from pathlib import Path
import os
import html


BASE_DIR = Path(__file__).resolve().parent.parent
OUTPUT_FILE = BASE_DIR / "info-card.svg"

USERNAME = "malibalaji95"

BACKGROUND = "#0d1117"
BORDER = "#30363d"
TEXT = "#c9d1d9"
MUTED = "#8b949e"
GREEN = "#39d353"
CYAN = "#58a6ff"


def make_info_card():
    rows = [
        ("USER", USERNAME, GREEN),
        ("ROLE", "Data Science & AI/ML", CYAN),
        ("FOCUS", "Machine Learning", GREEN),
        ("BACKEND", "Python | Node.js | SQL", CYAN),
        ("CLOUD", "AWS | Docker | GitHub Actions", GREEN),
        ("INTERESTS", "AI Systems | Data Engineering", CYAN),
    ]

    width = 480
    row_height = 35
    header_height = 65
    footer_height = 45

    height = header_height + len(rows) * row_height + footer_height

    svg = [
        (
            f'<svg xmlns="http://www.w3.org/2000/svg" '
            f'width="{width}" height="{height}" '
            f'viewBox="0 0 {width} {height}">'
        ),
        (
            f'<rect width="{width}" height="{height}" '
            f'rx="12" fill="{BACKGROUND}" '
            f'stroke="{BORDER}" stroke-width="1"/>'
        ),
    ]

    # Terminal title bar.
    for index, color in enumerate(["#ff5f56", "#ffbd2e", "#27c93f"]):
        svg.append(
            f'<circle cx="{20 + index * 18}" cy="20" '
            f'r="5" fill="{color}"/>'
        )

    svg.append(
        f'<text x="80" y="25" fill="{MUTED}" '
        'font-family="monospace" font-size="12">'
        f'{html.escape(USERNAME)}@github'
        '</text>'
    )

    svg.append(
        f'<text x="20" y="50" fill="{GREEN}" '
        'font-family="monospace" font-size="13">'
        '$ whoami'
        '</text>'
    )

    # Information rows.
    for index, (label, value, color) in enumerate(rows):
        y = header_height + index * row_height

        svg.append(
            f'<text x="22" y="{y + 18}" fill="{color}" '
            'font-family="monospace" font-size="12">'
            f'{html.escape(label)}'
            '</text>'
        )

        svg.append(
            f'<text x="125" y="{y + 18}" fill="{TEXT}" '
            'font-family="monospace" font-size="12">'
            f'{html.escape(value)}'
            '</text>'
        )

        svg.append(
            f'<line x1="20" y1="{y + 28}" '
            f'x2="{width - 20}" y2="{y + 28}" '
            f'stroke="{BORDER}" stroke-width="0.5"/>'
        )

        # Subtle line-by-line reveal.
        svg.append(
            f'<rect x="0" y="{y}" width="{width}" '
            f'height="{row_height}" fill="{BACKGROUND}">'
            '<animate attributeName="opacity" '
            'from="1" to="0" dur="0.5s" '
            f'begin="{index * 0.18:.2f}s" '
            'fill="freeze"/>'
            '</rect>'
        )

    footer_y = header_height + len(rows) * row_height + 25

    svg.append(
        f'<text x="22" y="{footer_y}" fill="{MUTED}" '
        'font-family="monospace" font-size="11">'
        'Status: Building intelligent systems'
        '</text>'
    )

    svg.append('</svg>')

    OUTPUT_FILE.write_text(
        "\n".join(svg),
        encoding="utf-8"
    )

    print(f"Information card generated: {OUTPUT_FILE}")


if __name__ == "__main__":
    make_info_card()
