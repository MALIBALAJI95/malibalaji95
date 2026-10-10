from pathlib import Path
from xml.sax.saxutils import escape

from PIL import Image


BASE_DIR = Path(__file__).resolve().parent.parent

INPUT_FILE = BASE_DIR / "assets" / "source-prepped.png"
OUTPUT_FILE = BASE_DIR / "avi-ascii.svg"

RAMP = " .`:-=+*cs#%@"

COLUMNS = 90
FONT_SIZE = 8
LINE_HEIGHT = 10

BACKGROUND = "#0d1117"
FOREGROUND = "#c9d1d9"


def brightness_to_character(value):
    index = int(value / 255 * (len(RAMP) - 1))
    return RAMP[index]


def make_ascii_svg():
    if not INPUT_FILE.exists():
        raise FileNotFoundError(
            "Prepared photo not found. "
            "Run scripts/prep_photo.py first."
        )

    image = Image.open(INPUT_FILE).convert("L")

    rows = max(
        1,
        round(image.height / image.width * COLUMNS * 0.5)
    )

    image = image.resize((COLUMNS, rows))

    pixels = image.load()

    width = COLUMNS * FONT_SIZE
    height = rows * LINE_HEIGHT + 20

    svg = [
        (
            f'<svg xmlns="http://www.w3.org/2000/svg" '
            f'width="{width}" height="{height}" '
            f'viewBox="0 0 {width} {height}">'
        ),
        (
            f'<rect width="{width}" height="{height}" '
            f'rx="8" fill="{BACKGROUND}"/>'
        ),
    ]

    for row in range(rows):
        text = "".join(
            brightness_to_character(pixels[column, row])
            for column in range(COLUMNS)
        )

        # The original leading spaces are intentional.
        # XML text content preserves spaces in SVG text.
        escaped_text = escape(text)

        y = 15 + row * LINE_HEIGHT

        # Each row reveals from left to right.
        svg.append(
            f'<clipPath id="clip{row}">'
            f'<rect x="0" y="0" width="0" height="{LINE_HEIGHT}">'
            '<animate attributeName="width" '
            f'from="0" to="{width}" '
            'dur="1.1s" '
            f'begin="{row * 0.045:.3f}s" '
            'fill="freeze"/>'
            '</rect>'
            '</clipPath>'
        )

        svg.append(
            f'<text x="5" y="{y}" '
            f'fill="{FOREGROUND}" '
            f'font-family="monospace" '
            f'font-size="{FONT_SIZE}" '
            'xml:space="preserve" '
            f'clip-path="url(#clip{row})">'
            f'{escaped_text}'
            '</text>'
        )

    svg.append("</svg>")

    OUTPUT_FILE.write_text(
        "\n".join(svg),
        encoding="utf-8"
    )

    print(f"ASCII portrait created: {OUTPUT_FILE}")


if __name__ == "__main__":
    make_ascii_svg()
