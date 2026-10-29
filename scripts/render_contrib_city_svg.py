import json
import math
from pathlib import Path
from datetime import datetime
from xml.sax.saxutils import escape

BASE_DIR = Path(__file__).resolve().parent.parent

INPUT_FILE = BASE_DIR / "data" / "contributions.json"
OUTPUT_FILE = BASE_DIR / "contrib-city.svg"

WIDTH = 1200
HEIGHT = 720

BACKGROUND = "#f7f8f7"
TEXT = "#171717"
MUTED = "#777777"

GREEN_LIGHT = "#9be9a8"
GREEN_MID = "#40c463"
GREEN_DARK = "#216e39"

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
            "count": max(0, count)
        })

    parsed.sort(key=lambda item: item["date"])

    # Keep the latest 365 days.
    return parsed[-365:]


def project(x, y, z):
    """
    Convert 3D coordinates to an isometric 2D position.
    """
    screen_x = 600 + (x - y) * 1.15
    screen_y = 450 + (x + y) * 0.48 - z

    return screen_x, screen_y


def polygon(points, fill, opacity=1):
    points_string = " ".join(
        f"{x:.2f},{y:.2f}" for x, y in points
    )

    return (
        f'<polygon points="{points_string}" '
        f'fill="{fill}" opacity="{opacity}"/>'
    )


def building(x, y, height, index, max_height):
    """
    Create one isometric building with three visible faces.
    """
    base_x = x * 18
    base_y = y * 18

    h = max(5, height)

    # Front-left face
    front_left = [
        project(base_x, base_y, 0),
        project(base_x + 14, base_y, 0),
        project(base_x + 14, base_y, h),
        project(base_x, base_y, h)
    ]

    # Front-right face
    front_right = [
        project(base_x + 14, base_y, 0),
        project(base_x + 14, base_y + 14, 0),
        project(base_x + 14, base_y + 14, h),
        project(base_x + 14, base_y, h)
    ]

    # Top face
    top = [
        project(base_x, base_y, h),
        project(base_x + 14, base_y, h),
        project(base_x + 14, base_y + 14, h),
        project(base_x, base_y + 14, h)
    ]

    ratio = h / max_height if max_height else 0

    if ratio > 0.75:
        front_color = GREEN_DARK
        side_color = "#165c30"
        top_color = "#73d68b"
    elif ratio > 0.4:
        front_color = GREEN_MID
        side_color = "#2d9d50"
        top_color = "#83dfa0"
    else:
        front_color = GREEN_LIGHT
        side_color = "#7bcf91"
        top_color = "#c0f2ca"

    delay = index * 0.012

    return f"""
    <g>
        <title>{escape(str(height))} contributions</title>

        {polygon(front_left, front_color)}
        {polygon(front_right, side_color)}
        {polygon(top, top_color)}

        <animateTransform
            attributeName="transform"
            type="translate"
            values="0 35; 0 0"
            begin="{delay:.3f}s"
            dur="0.8s"
            fill="freeze"
            calcMode="spline"
            keySplines="0.22 1 0.36 1"
        />
    </g>
    """


def render(days):
    if not days:
        raise ValueError("No contribution days found.")

    max_count = max(day["count"] for day in days)
    max_count = max(max_count, 1)

    # Create a 13 x 28 city grid.
    columns = 28
    rows = 13

    city_days = days[-(columns * rows):]

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
    <text x="65" y="75"
          font-family="Georgia, serif"
          font-size="42"
          fill="{TEXT}">
        My GitHub Contribution City
    </text>

    <text x="68" y="112"
          font-family="monospace"
          font-size="14"
          fill="{MUTED}">
        EVERY DAY BUILDS SOMETHING
    </text>
    """)

    # Ground plane
    ground = [
        project(0, 0, 0),
        project(columns * 18, 0, 0),
        project(columns * 18, rows * 18, 0),
        project(0, rows * 18, 0)
    ]

    svg.append(polygon(ground, "#eeeeee"))

    # Draw buildings from back to front.
    max_building_height = 150

    for index, day in enumerate(city_days):
        row = index // columns
        col = index % columns

        count = day["count"]

        height = 5 + (
            count / max_count
        ) * max_building_height

        svg.append(
            building(
                col,
                row,
                height,
                index,
                max_building_height + 5
            )
        )

    total = sum(day["count"] for day in days)

    best_day = max(days, key=lambda item: item["count"])

    svg.append(f"""
    <text x="65" y="650"
          font-family="monospace"
          font-size="17"
          fill="{TEXT}">
        TOTAL CONTRIBUTIONS: {total:,}
    </text>

    <text x="65" y="680"
          font-family="monospace"
          font-size="13"
          fill="{MUTED}">
        BEST DAY: {best_day["date"].strftime("%d %b %Y")}
        — {best_day["count"]} contributions
    </text>
    """)

    svg.append("</svg>")

    OUTPUT_FILE.write_text(
        "\n".join(svg),
        encoding="utf-8"
    )

    print(f"Created: {OUTPUT_FILE}")
    print(f"Contribution days: {len(days)}")
    print(f"Total contributions: {total:,}")


def main():
    data = load_data()
    days = parse_days(data)
    render(days)


if __name__ == "__main__":
    main()
