import json
import os
import re
from datetime import date, timedelta
from pathlib import Path

import requests
from bs4 import BeautifulSoup


USERNAME = "malibalaji95"

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
OUTPUT_FILE = DATA_DIR / "contributions.json"

URL = f"https://github.com/users/{USERNAME}/contributions"


def fetch_contributions():
    print(f"Fetching contributions for {USERNAME}...")

    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; GitHubProfileArt/1.0)"
    }

    response = requests.get(
        URL,
        headers=headers,
        timeout=30
    )

    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    cells = soup.select("td.ContributionCalendar-day")

    if not cells:
        cells = soup.select("[data-date][data-level]")

    if not cells:
        raise RuntimeError(
            "No contribution cells found. "
            "GitHub may have changed its HTML or blocked the request."
        )

    days = []

    for cell in cells:
        contribution_date = cell.get("data-date")
        level = cell.get("data-level")

        if not contribution_date or level is None:
            continue

        try:
            day_date = date.fromisoformat(contribution_date)
            level = int(level)
        except (ValueError, TypeError):
            continue

        if not 0 <= level <= 4:
            continue

        # GitHub's public calendar does not always expose
        # an exact count for every day. Store only counts
        # that can be read reliably from the page.
        count = None

        label = cell.get("aria-label", "")
        match = re.search(r"(\d[\d,]*) contribution", label)

        if match:
            count = int(match.group(1).replace(",", ""))

        days.append({
            "date": day_date.isoformat(),
            "count": count,
            "level": level
        })

    if not days:
        raise RuntimeError(
            "The contribution page was loaded, "
            "but no valid dates were extracted."
        )

    days.sort(key=lambda item: item["date"])

    today = date.today()
    one_year_ago = today - timedelta(days=364)

    recent_days = [
        day for day in days
        if one_year_ago.isoformat() <= day["date"] <= today.isoformat()
    ]

    active_dates = {
        day["date"]
        for day in recent_days
        if day["level"] > 0
    }

    current_streak = 0
    streak_date = today

    if streak_date.isoformat() not in active_dates:
        streak_date -= timedelta(days=1)

    while streak_date.isoformat() in active_dates:
        current_streak += 1
        streak_date -= timedelta(days=1)

    longest_streak = 0
    running_streak = 0
    previous_date = None

    for day in recent_days:
        current_date = date.fromisoformat(day["date"])

        if day["level"] > 0:
            if (
                previous_date is not None
                and current_date == previous_date + timedelta(days=1)
            ):
                running_streak += 1
            else:
                running_streak = 1

            longest_streak = max(longest_streak, running_streak)
            previous_date = current_date
        else:
            running_streak = 0
            previous_date = None

    exact_counts = [
        day["count"]
        for day in recent_days
        if day["count"] is not None
    ]

    best_day = max(exact_counts) if exact_counts else None

    result = {
        "username": USERNAME,
        "updated_at": date.today().isoformat(),
        "days": days,
        "stats": {
            "days_recorded": len(days),
            "current_streak": current_streak,
            "longest_streak": longest_streak,
            "best_day": best_day
        }
    }

    DATA_DIR.mkdir(parents=True, exist_ok=True)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as file:
        json.dump(result, file, indent=2)

    print(f"Saved {len(days)} contribution days.")
    print(f"Output: {OUTPUT_FILE}")
    print(f"Current streak: {current_streak}")
    print(f"Longest streak: {longest_streak}")

    if best_day is None:
        print("Best day: unavailable")
    else:
        print(f"Best day: {best_day}")


if __name__ == "__main__":
    fetch_contributions()
