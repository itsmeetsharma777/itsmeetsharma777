"""Refresh the live statistics inside the purple LeetCode SVG card."""

import html
import re
import os
from pathlib import Path

import requests

USERNAME = os.environ.get("LEETCODE_USERNAME", "itsmeetsharma")
OUT = Path(os.environ.get("OUTPUT", "assets/leetcode-card-v3.svg"))

QUERY = """
query userStats($username: String!) {
  allQuestionsCount { difficulty count }
  matchedUser(username: $username) {
    profile { ranking }
    submitStats { acSubmissionNum { difficulty count } }
    languageProblemCount { languageName problemsSolved }
  }
}
"""


def fetch_stats():
    response = requests.post(
        "https://leetcode.com/graphql",
        json={"query": QUERY, "variables": {"username": USERNAME}},
        headers={
            "User-Agent": "Mozilla/5.0 (compatible; MeetSharmaProfile/1.0)",
            "Referer": "https://leetcode.com/",
            "Content-Type": "application/json",
        },
        timeout=30,
    )
    response.raise_for_status()

    payload = response.json()
    data = payload.get("data", {})
    user = data.get("matchedUser")
    if not user:
        raise RuntimeError("LeetCode user was not found")

    totals = {
        item["difficulty"]: int(item["count"])
        for item in data.get("allQuestionsCount", [])
    }
    solved = {
        item["difficulty"]: int(item["count"])
        for item in user.get("submitStats", {}).get("acSubmissionNum", [])
    }

    languages = sorted(
        [
            (
                item.get("languageName", ""),
                int(item.get("problemsSolved", 0)),
            )
            for item in user.get("languageProblemCount", [])
        ],
        key=lambda item: item[1],
        reverse=True,
    )

    return {
        "ranking": int(user.get("profile", {}).get("ranking") or 0),
        "all": solved.get("All", 0),
        "easy": solved.get("Easy", 0),
        "medium": solved.get("Medium", 0),
        "hard": solved.get("Hard", 0),
        "total_easy": totals.get("Easy", 0),
        "total_medium": totals.get("Medium", 0),
        "total_hard": totals.get("Hard", 0),
        "languages": languages[:3],
    }


def replace_once(text, pattern, replacement):
    updated, count = re.subn(pattern, replacement, text, count=1)
    if count != 1:
        raise RuntimeError(f"Could not find card field: {pattern}")
    return updated


def refresh_card(card, stats):
    # Header
    card = replace_once(
        card,
        r'(<text x="1155" y="65" text-anchor="end" class="rank">)#.*?(</text>)',
        rf'\1#{stats["ranking"]:,}\2',
    )

    # Difficulty totals and solved percentages.
    values = [
        ("Easy", stats["easy"], stats["total_easy"], 62, 372),
        ("Medium", stats["medium"], stats["total_medium"], 445, 755),
        ("Hard", stats["hard"], stats["total_hard"], 828, 1138),
    ]

    for label, solved, total, x, right_x in values:
        pct = (solved / total * 100) if total else 0
        card = replace_once(
            card,
            rf'(<text x="{right_x}" y="153" text-anchor="end" class="value">).*?(</text>)',
            rf'\1{solved} / {total}\2',
        )
        card = replace_once(
            card,
            rf'(<text x="{x}" y="179" class="pct">).*?(</text>)',
            rf'\1{pct:.2f}% solved\2',
        )

    # Overall solved count.
    card = replace_once(
        card,
        r'(<text x="62" y="306" class="stat">)\d+(</text>)',
        rf'\1{stats["all"]}\2',
    )

    # Language breakdown.
    lang_values = stats["languages"] + [("", 0)] * 3
    positions = [
        ("C++", 350, 392),
        ("JavaScript", 470, 568),
        ("Pandas", 625, 690),
    ]

    for index, (default_name, name_x, value_x) in enumerate(positions):
        name, count = lang_values[index]
        if not name:
            name, count = default_name, 0

        card = replace_once(
            card,
            rf'(<text x="{name_x}" y="306" class="muted">).*?(</text>)',
            rf'\1{html.escape(name)}\2',
        )
        card = replace_once(
            card,
            rf'(<text x="{value_x}" y="306" class="chip">).*?(</text>)',
            rf'\1{count}\2',
        )

    return card


def main():
    if not OUT.exists():
        raise RuntimeError(f"Card not found: {OUT}")

    card = OUT.read_text(encoding="utf-8")
    stats = fetch_stats()
    updated = refresh_card(card, stats)

    if updated != card:
        OUT.write_text(updated, encoding="utf-8")
        print(
            f"Updated LeetCode card: {stats['all']} solved, "
            f"Easy {stats['easy']}, Medium {stats['medium']}, Hard {stats['hard']}, "
            f"rank #{stats['ranking']:,}"
        )
    else:
        print("LeetCode card is already up to date.")


if __name__ == "__main__":
    main()
