import json
import html
from datetime import date, timedelta
from pathlib import Path


USERNAME = "malibalaji95"

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_FILE = BASE_DIR / "data" / "contributions.json"
OUTPUT_FILE = BASE_DIR / "contrib-heatmap.svg"

BACKGROUND = "#0d1117"
TEXT = "#c9d1d9"
MUTED = "#8b949e"

PALETTE = [
    "#161b22",
    "#0e4429",
    "#006d32",
    "#26a641",
    "#39d353",
]


def load_data():
    if not DATA_FILE.exists():
        raise FileNotFoundError(
            "Contribution data not found. "
            "Run scripts/fetch_contributions.py first."
        )

    with open(DATA_FILE, "r", encoding="utf-8") as file:
        return json.load(file)


def level_for_day(day):
    level = day.get("level", 0)

    try:
        level = int(level)
    except (ValueError, TypeError):
        level = 0

    return max(0, min(4, level))


def generate_heatmap(data):
    days = data.get("days", [])
    stats = data.get("stats", {})

    # Display the latest 371 days (53 weeks).
    today = date.today()
    start_date = today - timedelta(days=370)

    # Align the first column to Sunday.
    start_date -= timedelta(days=(start_date.weekday() + 1) % 7)

    end_date = start_date + timedelta(days=370)

    day_lookup = {}

    for day in days:
        try:
            parsed_date = date.fromisoformat(day["date"])
            day_lookup[parsed_date] = day
        except (ValueError, KeyError, TypeError):
            continue

    cell_size = 11
    gap = 4
    step = cell_size + gap

    left = 44
    top = 52

    grid_width = 53 * step
    grid_height = 7 * step

    width = left + grid_width + 16
    height = top + grid_height + 84

    elements = []

    elements.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}" '
        f'role="img" aria-labelledby="title desc">'
    )

    elements.append("<title id=\"title\">GitHub contribution heatmap</title>")
    elements.append(
        "<desc id=\"desc\">Contribution activity for "
        f"{html.escape(USERNAME)} over approximately one year.</desc>"
    )

    elements.append(
        f'<rect width="{width}" height="{height}" '
        f'rx="12" fill="{BACKGROUND}"/>'
    )

    elements.append(
        f'<text x="20" y="27" fill="{TEXT}" '
        'font-family="monospace" font-size="15" font-weight="bold">'
        f'{html.escape(USERNAME)}@github:~ $ contributions'
        '</text>'
    )

    elements.append(
        f'<text x="20" y="44" fill="{MUTED}" '
        'font-family="monospace" font-size="10">'
        'Last 53 weeks'
        '</text>'
    )

    # Weekday labels.
    weekday_labels = [
        (1, "Mon"),
        (3, "Wed"),
        (5, "Fri"),
    ]

    for row, label in weekday_labels:
        y = top + row * step + 9

        elements.append(
            f'<text x="8" y="{y}" fill="{MUTED}" '
            'font-family="monospace" font-size="9">'
            f'{label}</text>'
        )

    # Month labels.
    previous_month = None

    for column in range(53):
        week_start = start_date + timedelta(days=column * 7)

        if week_start.month != previous_month:
            x = left + column * step

            elements.append(
                f'<text x="{x}" y="{top - 9}" fill="{MUTED}" '
                'font-family="monospace" font-size="9">'
                f'{week_start.strftime("%b")}</text>'
            )

            previous_month = week_start.month

    # Contribution cells.
    for column in range(53):
        for row in range(7):
            current_date = start_date + timedelta(
                days=column * 7 + row
            )

            if current_date > today or current_date < start_date:
                continue

            day = day_lookup.get(current_date, {"level": 0})
            level = level_for_day(day)

            x = left + column * step
            y = top + row * step

            delay = column * 0.012 + row * 0.035

            tooltip = (
                f'{current_date.isoformat()}: '
                f'level {level}'
            )

            elements.append(
                f'<rect x="{x}" y="{y}" '
                f'width="{cell_size}" height="{cell_size}" '
                'rx="3" '
                f'fill="{PALETTE[level]}" '
                f'data-date="{current_date.isoformat()}">'
                f'<title>{html.escape(tooltip)}</title>'
                '<animate attributeName="opacity" '
                'from="0" to="1" '
                'dur="0.45s" '
                f'begin="{delay:.3f}s" '
                'fill="freeze"/>'
                '</rect>'
            )

    # Legend.
    legend_y = top + grid_height + 23

    elements.append(
        f'<text x="{left}" y="{legend_y}" fill="{MUTED}" '
        'font-family="monospace" font-size="10">Less</text>'
    )

    legend_x = left + 33

    for index, color in enumerate(PALETTE):
        elements.append(
            f'<rect x="{legend_x + index * step}" '
            f'y="{legend_y - 10}" '
            f'width="{cell_size}" height="{cell_size}" '
            f'rx="3" fill="{color}"/>'
        )

    elements.append(
        f'<text x="{legend_x + len(PALETTE) * step + 3}" '
        f'y="{legend_y}" fill="{MUTED}" '
        'font-family="monospace" font-size="10">More</text>'
    )

    # Footer statistics.
    footer_y = legend_y + 28

    current_streak = stats.get("current_streak", 0)
    longest_streak = stats.get("longest_streak", 0)

    elements.append(
        f'<text x="{left}" y="{footer_y}" fill="{TEXT}" '
        'font-family="monospace" font-size="10">'
        f'Current streak: {current_streak} days'
        '</text>'
    )

    elements.append(
        f'<text x="{left + 180}" y="{footer_y}" fill="{TEXT}" '
        'font-family="monospace" font-size="10">'
        f'Longest streak: {longest_streak} days'
        '</text>'
    )

    elements.append("</svg>")

    OUTPUT_FILE.write_text(
        "\n".join(elements),
        encoding="utf-8"
    )

    print(f"Generated: {OUTPUT_FILE}")
    print(f"Contribution days loaded: {len(days)}")


if __name__ == "__main__":
    generate_heatmap(load_data())
