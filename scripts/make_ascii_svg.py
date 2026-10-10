from pathlib import Path
from xml.sax.saxutils import escape

from PIL import Image, ImageOps, ImageEnhance


BASE_DIR = Path(__file__).resolve().parent.parent

INPUT_FILE = BASE_DIR / "assets" / "source-prepped.png"
OUTPUT_FILE = BASE_DIR / "avi-ascii.svg"

# Dense characters represent dark pixels.
# Spaces represent bright pixels.
RAMP = " .,:;irsXA253hMHGS#9B&@"

COLUMNS = 120
FONT_SIZE = 8
LINE_HEIGHT = 10

BACKGROUND = "#0d1117"
FOREGROUND = "#39d353"


def brightness_to_character(value):
    """
    Convert brightness into an ASCII character.

    Dark pixels use dense characters.
    Bright pixels use spaces.
    """
    value = max(0, min(255, int(value)))

    index = round(
        (255 - value) / 255 * (len(RAMP) - 1)
    )

    return RAMP[index]


def make_ascii_svg():
    if not INPUT_FILE.exists():
        raise FileNotFoundError(
            f"Prepared photo not found: {INPUT_FILE}\n"
            "Run scripts/prep_photo.py first."
        )

    # Load the prepared portrait.
    image = Image.open(INPUT_FILE).convert("L")

    # Improve contrast so the subject is easier to distinguish.
    image = ImageOps.autocontrast(image)
    image = ImageEnhance.Contrast(image).enhance(1.5)

    # Account for the width of monospace characters.
    rows = max(
        1,
        round(image.height / image.width * COLUMNS * 0.5)
    )

    image = image.resize(
        (COLUMNS, rows),
        Image.Resampling.LANCZOS
    )

    pixels = image.load()

    width = COLUMNS * FONT_SIZE + 20
    height = rows * LINE_HEIGHT + 40

    svg = [
        (
            '<svg xmlns="http://www.w3.org/2000/svg" '
            f'width="{width}" height="{height}" '
            f'viewBox="0 0 {width} {height}">'
        ),

        (
            f'<rect width="{width}" height="{height}" '
            f'rx="12" fill="{BACKGROUND}"/>'
        ),

        (
            '<text x="16" y="22" '
            'font-family="monospace" font-size="11" '
            'fill="#8b949e">'
            'balaji@mali:~$ portrait --ascii'
            '</text>'
        ),
    ]

    # Build a visible, static portrait.
    # Animation is deliberately omitted until the image works.
    for row in range(rows):
        text = "".join(
            brightness_to_character(pixels[column, row])
            for column in range(COLUMNS)
        )

        y = 38 + row * LINE_HEIGHT

        svg.append(
            f'<text x="10" y="{y}" '
            f'fill="{FOREGROUND}" '
            f'font-family="monospace" '
            f'font-size="{FONT_SIZE}" '
            f'font-weight="bold" '
            'xml:space="preserve">'
            f'{escape(text)}'
            '</text>'
        )

    svg.append("</svg>")

    OUTPUT_FILE.write_text(
        "\n".join(svg),
        encoding="utf-8"
    )

    # Validate the output.
    generated = OUTPUT_FILE.read_text(encoding="utf-8")

    if "<svg" not in generated or "</svg>" not in generated:
        raise RuntimeError("Generated SVG is invalid.")

    if len(generated) < 1000:
        raise RuntimeError("Generated SVG appears unexpectedly small.")

    print(f"ASCII portrait generated: {OUTPUT_FILE}")
    print(f"Dimensions: {width} x {height}")
    print(f"ASCII rows: {rows}")
    print(f"File size: {OUTPUT_FILE.stat().st_size} bytes")


if __name__ == "__main__":
    make_ascii_svg()
