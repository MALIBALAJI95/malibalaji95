import json
from pathlib import Path
from datetime import datetime
from xml.sax.saxutils import escape


BASE_DIR = Path(__file__).resolve().parent.parent

INPUT_FILE = BASE_DIR / "data" / "contributions.json"
OUTPUT_FILE = BASE_DIR / "weekly-pulse.svg"

BACKGROUND = "#0d1117"
FOREGROUND = "#c9d1d9"
GREEN = "#30a14e"
GRID = "#21262d"

WIDTH = 1000
HEIGHT = 390

LEFT = 70
RIGHT = 30
TOP = 65
BOTTOM = 75

BAR_COLOR = "#30a14e"
MAX_BAR_COLOR = "#9be9a8"


def load_data():
    if not INPUT_FILE.exists():
        raise FileNotFoundError(
            f"Contribution data not found: {INPUT_FILE}"
        )

    with INPUT_FILE.open("r", encoding="utf-8") as file:
        return json.load(file)


def parse_days(data):
    days = data.get("days", [])

    parsed = []

    for item in days:
        date_text = item.get("date")
        count = int(item.get("count", 0))

        if not date_text:
            continue

        date = datetime.strptime(date_text, "%Y-%m-%d")

        parsed.append({
            "date": date,
            "count": max(0, count)
        })

    parsed.sort(key=lambda item: item["date"])

    return parsed


def group_by_week(days):
    weeks = []

    for day in days:
        # Monday-based week index.
        week_key = day["date"].isocalendar()[:2]

        if not weeks or weeks[-1]["key"] != week_key:
            weeks.append({
                "key": week_key,
                "days": [],
                "total": 0
            })

        weeks[-1]["days"].append(day)
        weeks[-1]["total"] += day["count"]

    return weeks


def render_svg(weeks):
    if not weeks:
        raise ValueError("No contribution weeks found.")

    chart_width = WIDTH - LEFT - RIGHT
    chart_height = HEIGHT - TOP - BOTTOM

    max_total = max(week["total"] for week in weeks)
    max_total = max(max_total, 1)

    slot_width = chart_width / len(weeks)
    bar_width = max(2, slot_width * 0.62)

    svg = []

    svg.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'width="{WIDTH}" height="{HEIGHT}" '
        f'viewBox="0 0 {WIDTH} {HEIGHT}">'
    )

    svg.append(
        f'<rect width="{WIDTH}" height="{HEIGHT}" '
        f'rx="14" fill="{BACKGROUND}"/>'
    )

    # Heading
    svg.append(
        f'<text x="{LEFT}" y="32" '
        f'fill="{FOREGROUND}" '
        f'font-family="monospace" font-size="20" '
        f'font-weight="bold">'
        'CONTRIBUTIONS / WEEK'
        '</text>'
    )

    svg.append(
        f'<text x="{WIDTH - RIGHT}" y="32" '
        f'text-anchor="end" '
        f'fill="#8b949e" '
        f'font-family="monospace" font-size="12">'
        f'{len(weeks)} WEEKS'
        '</text>'
    )

    # Horizontal chart lines
    for i in range(5):
        y = TOP + chart_height * i / 4

        svg.append(
            f'<line x1="{LEFT}" y1="{y:.2f}" '
            f'x2="{WIDTH - RIGHT}" y2="{y:.2f}" '
            f'stroke="{GRID}" stroke-width="1"/>'
        )

    # Bars
    for index, week in enumerate(weeks):
        total = week["total"]

        bar_height = (total / max_total) * chart_height

        x = LEFT + index * slot_width + (
            slot_width - bar_width
        ) / 2

        y = TOP + chart_height - bar_height

        delay = index * 0.035

        fill = MAX_BAR_COLOR if total == max_total else BAR_COLOR

        svg.append(
            f'<rect x="{x:.2f}" '
            f'y="{TOP + chart_height:.2f}" '
            f'width="{bar_width:.2f}" '
            f'height="0" rx="2" fill="{fill}">'
            f'<title>Week {index + 1}: '
            f'{total} contributions</title>'
            f'<animate attributeName="y" '
            f'from="{TOP + chart_height:.2f}" '
            f'to="{y:.2f}" '
            f'begin="{delay:.3f}s" '
            f'dur="0.65s" '
            f'fill="freeze" '
            f'calcMode="spline" '
            f'keySplines="0.22 1 0.36 1"/>'
            f'<animate attributeName="height" '
            f'from="0" to="{bar_height:.2f}" '
            f'begin="{delay:.3f}s" '
            f'dur="0.65s" '
            f'fill="freeze" '
            f'calcMode="spline" '
            f'keySplines="0.22 1 0.36 1"/>'
            '</rect>'
        )

        # Label every fourth week
        if index % 4 == 0 or index == len(weeks) - 1:
            label_date = week["days"][0]["date"]
            label = label_date.strftime("%b %d")

            svg.append(
                f'<text x="{x + bar_width / 2:.2f}" '
                f'y="{HEIGHT - 35}" '
                f'text-anchor="middle" '
                f'fill="#8b949e" '
                f'font-family="monospace" '
                f'font-size="10">'
                f'{escape(label)}'
                '</text>'
            )

    # Total contributions
    total_contributions = sum(
        day["count"]
        for week in weeks
        for day in week["days"]
    )

    svg.append(
        f'<text x="{LEFT}" y="{HEIGHT - 12}" '
        f'fill="{FOREGROUND}" '
        f'font-family="monospace" font-size="12">'
        f'TOTAL CONTRIBUTIONS: {total_contributions:,}'
        '</text>'
    )

    svg.append("</svg>")

    OUTPUT_FILE.write_text(
        "\n".join(svg),
        encoding="utf-8"
    )

    print(f"Weekly pulse created: {OUTPUT_FILE}")


def main():
    data = load_data()
    days = parse_days(data)
    weeks = group_by_week(days)
    render_svg(weeks)


if __name__ == "__main__":
    main()
