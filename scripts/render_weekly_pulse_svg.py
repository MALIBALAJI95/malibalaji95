import json
import math
from pathlib import Path
from datetime import datetime
from xml.sax.saxutils import escape

BASE_DIR = Path(__file__).resolve().parent.parent
INPUT_FILE = BASE_DIR / "data" / "contributions.json"
OUTPUT_FILE = BASE_DIR / "contrib-round-year.svg"

WIDTH = 1000
HEIGHT = 760

CX = 360
CY = 390

INNER_RADIUS = 115
OUTER_RADIUS = 290

BACKGROUND = "#ffffff"
TEXT = "#171717"
MUTED = "#777777"

COLORS = [
    "#e5e7eb",
    "#c0f2ca",
    "#83dfa0",
    "#40c463",
    "#216e39",
]


def load_data():
    with INPUT_FILE.open("r", encoding="utf-8") as file:
        return json.load(file)


def parse_days(data):
    parsed = []

    for item in data.get("days", []):
        date_text = item.get("date")

        if not date_text:
            continue

        raw_count = item.get("count")

        try:
            count = int(raw_count) if raw_count is not None else 0
        except (TypeError, ValueError):
            count = 0

        parsed.append({
            "date": datetime.strptime(date_text, "%Y-%m-%d"),
            "count": max(0, count),
        })

    parsed.sort(key=lambda item: item["date"])

    return parsed[-365:]


def polar_point(radius, angle):
    x = CX + radius * math.cos(angle)
    y = CY + radius * math.sin(angle)

    return x, y


def color_for_count(count, max_count):
    if count <= 0:
        return COLORS[0]

    ratio = count / max_count

    if ratio <= 0.25:
        return COLORS[1]
    elif ratio <= 0.5:
        return COLORS[2]
    elif ratio <= 0.75:
        return COLORS[3]

    return COLORS[4]


def render(days):
    if not days:
        raise ValueError("No contribution days found.")

    max_count = max(day["count"] for day in days)
    max_count = max(max_count, 1)

    total = sum(day["count"] for day in days)

    best_day = max(days, key=lambda item: item["count"])

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
          font-size="38"
          fill="{TEXT}">
        Round the year
    </text>

    <text x="60" y="95"
          font-family="monospace"
          font-size="12"
          fill="{MUTED}">
        YOUR CONTRIBUTIONS, WRAPPED INTO A CIRCLE
    </text>
    """)

    # One circular ring for each weekday.
    ring_count = 7

    # Divide the year into angular slots.
    slot_angle = (2 * math.pi) / len(days)

    # Add a slight gap between contribution cells.
    gap = 0.008

    # Draw rings from inside to outside.
    for ring in range(ring_count):
        radius = INNER_RADIUS + ring * 25

        for index, day in enumerate(days):
            angle = -math.pi / 2 + index * slot_angle

            start_angle = angle + gap
            end_angle = angle + slot_angle - gap

            # A small arc-shaped cell.
            p1 = polar_point(radius, start_angle)
            p2 = polar_point(radius + 21, start_angle)
            p3 = polar_point(radius + 21, end_angle)
            p4 = polar_point(radius, end_angle)

            points = " ".join(
                f"{x:.2f},{y:.2f}"
                for x, y in [p1, p2, p3, p4]
            )

            fill = color_for_count(day["count"], max_count)

            delay = index * 0.004 + ring * 0.04

            svg.append(f"""
            <polygon points="{points}"
                     fill="{fill}"
                     stroke="#ffffff"
                     stroke-width="1">
                <title>
                    {day["date"].strftime("%d %b %Y")}:
                    {day["count"]} contributions
                </title>

                <animate
                    attributeName="opacity"
                    from="0"
                    to="1"
                    begin="{delay:.3f}s"
                    dur="0.6s"
                    fill="freeze"/>
            </polygon>
            """)

    # Month labels around the circle.
    month_positions = {}

    for index, day in enumerate(days):
        month_key = day["date"].strftime("%b")

        if month_key not in month_positions:
            angle = -math.pi / 2 + index * slot_angle
            month_positions[month_key] = angle

    for month, angle in month_positions.items():
        label_radius = OUTER_RADIUS + 35

        x, y = polar_point(label_radius, angle)

        svg.append(f"""
        <text x="{x:.2f}" y="{y:.2f}"
              text-anchor="middle"
              dominant-baseline="middle"
              font-family="monospace"
              font-size="11"
              fill="{MUTED}">
            {escape(month.upper())}
        </text>
        """)

    # Center circle.
    svg.append(f"""
    <circle cx="{CX}" cy="{CY}" r="{INNER_RADIUS - 10}"
            fill="#ffffff"/>

    <text x="{CX}" y="{CY - 12}"
          text-anchor="middle"
          font-family="Georgia, serif"
          font-size="42"
          fill="{TEXT}">
        {total:,}
    </text>

    <text x="{CX}" y="{CY + 20}"
          text-anchor="middle"
          font-family="monospace"
          font-size="11"
          fill="{MUTED}">
        CONTRIBUTIONS
    </text>
    """)

    # Statistics on the right.
    svg.append(f"""
    <text x="710" y="335"
          font-family="Georgia, serif"
          font-size="48"
          fill="{TEXT}">
        {total:,}
    </text>

    <text x="710" y="365"
          font-family="monospace"
          font-size="12"
          fill="{MUTED}">
        CONTRIBUTIONS
    </text>

    <text x="710" y="425"
          font-family="Georgia, serif"
          font-size="30"
          fill="{TEXT}">
        {best_day["count"]}
    </text>

    <text x="710" y="450"
          font-family="monospace"
          font-size="12"
          fill="{MUTED}">
        BEST DAY
    </text>

    <text x="710" y="490"
          font-family="monospace"
          font-size="12"
          fill="{MUTED}">
        {best_day["date"].strftime("%d %b %Y")}
    </text>
    """)

    # Legend.
    svg.append(f"""
    <text x="60" y="710"
          font-family="monospace"
          font-size="12"
          fill="{MUTED}">
        LESS
    </text>
    """)

    for i, color in enumerate(COLORS):
        x = 110 + i * 28

        svg.append(
            f'<rect x="{x}" y="695" width="20" height="20" '
            f'rx="3" fill="{color}"/>'
        )

    svg.append(f"""
    <text x="265" y="710"
          font-family="monospace"
          font-size="12"
          fill="{MUTED}">
        MORE
    </text>
    """)

    svg.append("</svg>")

    OUTPUT_FILE.write_text(
        "\n".join(svg),
        encoding="utf-8"
    )

    print(f"Created: {OUTPUT_FILE}")
    print(f"Total contributions: {total:,}")


def main():
    data = load_data()
    days = parse_days(data)
    render(days)


if __name__ == "__main__":
    main()
