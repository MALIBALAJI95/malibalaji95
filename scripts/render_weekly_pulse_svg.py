import json
import math
from pathlib import Path
from datetime import datetime, date, timedelta
from xml.sax.saxutils import escape

BASE_DIR = Path(__file__).resolve().parent.parent
INPUT_FILE = BASE_DIR / "data" / "contributions.json"
OUTPUT_FILE = BASE_DIR / "contrib-round-year.svg"

WIDTH = 1100
HEIGHT = 760

CX = 390
CY = 385

INNER_RADIUS = 115
CELL_SIZE = 19
CELL_GAP = 3

BACKGROUND = "#ffffff"
TEXT = "#171717"
MUTED = "#777777"

COLORS = [
    "#ebedf0",
    "#9be9a8",
    "#40c463",
    "#30a14e",
    "#216e39",
]


def load_data():
    with INPUT_FILE.open("r", encoding="utf-8") as file:
        return json.load(file)


def parse_days(data):
    parsed = {}

    for item in data.get("days", []):
        date_text = item.get("date")

        if not date_text:
            continue

        try:
            day_date = datetime.strptime(
                date_text, "%Y-%m-%d"
            ).date()
        except ValueError:
            continue

        # Your actual JSON uses level, not count.
        raw_level = item.get("level", 0)

        try:
            level = int(raw_level) if raw_level is not None else 0
        except (TypeError, ValueError):
            level = 0

        level = max(0, min(4, level))

        parsed[day_date] = {
            "date": day_date,
            "level": level,
        }

    return parsed


def get_calendar_days(days):
    if not days:
        raise ValueError("No contribution days found.")

    last_date = max(days.keys())

    # Show a full year ending at the latest date in the JSON.
    first_date = last_date - timedelta(days=364)

    # Align start to Sunday so the calendar starts at a full week.
    first_date -= timedelta(days=(first_date.weekday() + 1) % 7)

    calendar_days = []
    current = first_date

    while current <= last_date:
        calendar_days.append(
            days.get(
                current,
                {
                    "date": current,
                    "level": 0,
                }
            )
        )

        current += timedelta(days=1)

    return calendar_days


def polar_point(radius, angle):
    x = CX + radius * math.cos(angle)
    y = CY + radius * math.sin(angle)
    return x, y


def render(days):
    calendar_days = get_calendar_days(days)

    # Use 7 rings for weekdays and 53 angular positions for weeks.
    total_weeks = math.ceil(len(calendar_days) / 7)

    outer_radius = (
        INNER_RADIUS
        + total_weeks * (CELL_SIZE + CELL_GAP)
    )

    svg = []

    svg.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'width="{WIDTH}" height="{HEIGHT}" '
        f'viewBox="0 0 {WIDTH} {HEIGHT}">'
    )

    svg.append(
        f'<rect width="{WIDTH}" height="{HEIGHT}" '
        f'fill="{BACKGROUND}"/>'
    )

    svg.append(f"""
    <text x="60" y="65"
          font-family="Georgia, serif"
          font-size="40"
          fill="{TEXT}">
        Round the year
    </text>

    <text x="62" y="96"
          font-family="monospace"
          font-size="13"
          fill="{MUTED}">
        EVERY DAY, A CELL IN MY YEAR
    </text>
    """)

    # Draw each day as a cell:
    # angle = week of year
    # radius = weekday
    for index, day in enumerate(calendar_days):
        day_date = day["date"]
        level = day["level"]

        # Sunday = 0 ... Saturday = 6
        weekday = (day_date.weekday() + 1) % 7

        week_index = index // 7

        angle = (
            -math.pi / 2
            + (week_index / total_weeks) * 2 * math.pi
        )

        radius = (
            INNER_RADIUS
            + weekday * (CELL_SIZE + CELL_GAP)
        )

        angle_width = (
            (CELL_SIZE / max(radius, 1))
            * 0.85
        )

        start_angle = angle - angle_width / 2
        end_angle = angle + angle_width / 2

        r1 = radius
        r2 = radius + CELL_SIZE

        p1 = polar_point(r1, start_angle)
        p2 = polar_point(r2, start_angle)
        p3 = polar_point(r2, end_angle)
        p4 = polar_point(r1, end_angle)

        points = " ".join(
            f"{x:.2f},{y:.2f}"
            for x, y in [p1, p2, p3, p4]
        )

        fill = COLORS[level]

        # Animate each cell appearing in sequence.
        delay = index * 0.002

        svg.append(f"""
        <polygon points="{points}"
                 fill="{fill}"
                 stroke="#ffffff"
                 stroke-width="1"
                 opacity="0">
            <title>
                {day_date.strftime("%d %b %Y")}:
                contribution level {level}
            </title>

            <animate
                attributeName="opacity"
                from="0"
                to="1"
                begin="{delay:.3f}s"
                dur="0.35s"
                fill="freeze"/>
        </polygon>
        """)

    # Month labels positioned around the ring.
    month_positions = {}

    for index, day in enumerate(calendar_days):
        day_date = day["date"]
        month_key = (day_date.year, day_date.month)

        if month_key not in month_positions:
            week_index = index // 7

            angle = (
                -math.pi / 2
                + (week_index / total_weeks) * 2 * math.pi
            )

            month_positions[month_key] = (
                day_date.strftime("%b").upper(),
                angle,
            )

    for month, angle in month_positions.values():
        label_radius = outer_radius + 28
        x, y = polar_point(label_radius, angle)

        svg.append(f"""
        <text x="{x:.2f}" y="{y:.2f}"
              text-anchor="middle"
              dominant-baseline="middle"
              font-family="monospace"
              font-size="11"
              fill="{MUTED}">
            {escape(month)}
        </text>
        """)

    # Center circle and title.
    svg.append(f"""
    <circle cx="{CX}" cy="{CY}" r="{INNER_RADIUS - 8}"
            fill="#ffffff"/>

    <text x="{CX}" y="{CY - 12}"
          text-anchor="middle"
          font-family="Georgia, serif"
          font-size="34"
          fill="{TEXT}">
        {len(calendar_days)}d
    </text>

    <text x="{CX}" y="{CY + 18}"
          text-anchor="middle"
          font-family="monospace"
          font-size="11"
          fill="{MUTED}">
        CONTRIBUTIONS
    </text>
    """)

    # Legend.
    svg.append(f"""
    <text x="60" y="700"
          font-family="monospace"
          font-size="12"
          fill="{MUTED}">
        LESS
    </text>
    """)

    for index, color in enumerate(COLORS):
        x = 110 + index * 28

        svg.append(
            f'<rect x="{x}" y="685" '
            f'width="20" height="20" '
            f'rx="3" fill="{color}"/>'
        )

    svg.append(f"""
    <text x="265" y="700"
          font-family="monospace"
          font-size="12"
          fill="{MUTED}">
        MORE
    </text>

    <text x="720" y="350"
          font-family="Georgia, serif"
          font-size="48"
          fill="{TEXT}">
        {sum(1 for d in calendar_days if d["level"] > 0)}
    </text>

    <text x="720" y="380"
          font-family="monospace"
          font-size="12"
          fill="{MUTED}">
        ACTIVE DAYS
    </text>

    <text x="720" y="445"
          font-family="Georgia, serif"
          font-size="30"
          fill="{TEXT}">
        {max(d["level"] for d in calendar_days)}
    </text>

    <text x="720" y="470"
          font-family="monospace"
          font-size="12"
          fill="{MUTED}">
        MAX LEVEL
    </text>
    """)

    svg.append("</svg>")

    OUTPUT_FILE.write_text(
        "\n".join(svg),
        encoding="utf-8"
    )

    print(f"Created: {OUTPUT_FILE}")
    print(f"Contribution days: {len(calendar_days)}")
    print(f"Active days: {sum(1 for d in calendar_days if d['level'] > 0)}")


def main():
    data = load_data()
    days = parse_days(data)
    render(days)


if __name__ == "__main__":
    main()
