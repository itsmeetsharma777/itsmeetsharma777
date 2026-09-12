"""Generate a compact, full-width LeetCode SVG card for a GitHub profile README."""
import html
import json
import os
from pathlib import Path

import requests

USERNAME = os.environ.get("LEETCODE_USERNAME", "itsmeetsharma")
OUT = Path(os.environ.get("OUTPUT", "assets/leetcode-card.svg"))
OUT.parent.mkdir(parents=True, exist_ok=True)

FALLBACK = {
    "ranking": 1624381,
    "all": 103,
    "easy": 80,
    "medium": 21,
    "hard": 2,
    "total_easy": 963,
    "total_medium": 2111,
    "total_hard": 973,
    "languages": [("C++", 101), ("JavaScript", 1), ("Pandas", 1)],
}

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
    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; MeetSharmaProfile/1.0)",
        "Referer": "https://leetcode.com/",
        "Content-Type": "application/json",
    }
    response = requests.post(
        "https://leetcode.com/graphql",
        json={"query": QUERY, "variables": {"username": USERNAME}},
        headers=headers,
        timeout=30,
    )
    response.raise_for_status()
    payload = response.json()
    data = payload.get("data", {})
    user = data.get("matchedUser")
    if not user:
        raise RuntimeError("LeetCode user was not found")

    totals = {x["difficulty"]: int(x["count"]) for x in data.get("allQuestionsCount", [])}
    solved = {x["difficulty"]: int(x["count"]) for x in user.get("submitStats", {}).get("acSubmissionNum", [])}
    langs = sorted(
        [(x.get("languageName", ""), int(x.get("problemsSolved", 0))) for x in user.get("languageProblemCount", [])],
        key=lambda x: x[1],
        reverse=True,
    )[:3]
    return {
        "ranking": int(user.get("profile", {}).get("ranking") or FALLBACK["ranking"]),
        "all": solved.get("All", FALLBACK["all"]),
        "easy": solved.get("Easy", FALLBACK["easy"]),
        "medium": solved.get("Medium", FALLBACK["medium"]),
        "hard": solved.get("Hard", FALLBACK["hard"]),
        "total_easy": totals.get("Easy", FALLBACK["total_easy"]),
        "total_medium": totals.get("Medium", FALLBACK["total_medium"]),
        "total_hard": totals.get("Hard", FALLBACK["total_hard"]),
        "languages": langs or FALLBACK["languages"],
    }


def esc(value):
    return html.escape(str(value))


def bar(x, y, width, solved, total, color, label, fraction_text):
    pct = 0 if total <= 0 else min(1, solved / total)
    fill_w = max(4, width * pct) if solved else 0
    return f"""
    <text x="{x}" y="{y}" class="label">{esc(label)}</text>
    <text x="{x + width}" y="{y}" text-anchor="end" class="value">{esc(fraction_text)}</text>
    <rect x="{x}" y="{y + 12}" width="{width}" height="7" rx="3.5" class="track"/>
    <rect x="{x}" y="{y + 12}" width="{fill_w:.1f}" height="7" rx="3.5" fill="{color}"/>
    """


def render(s):
    W, H = 1200, 220
    orange = "#FFA116"
    green = "#45B84A"
    yellow = "#F5B94C"
    red = "#EF6A67"
    bg = "#0D0718"
    border = "#7C3AED"
    text = "#F4ECFF"
    muted = "#B9A9CF"

    langs = " · ".join(f"{name} {count}" for name, count in s["languages"])
    rank = f"#{s['ranking']:,}"

    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="100%" height="220" viewBox="0 0 {W} {H}">
  <defs>
    <linearGradient id="lcAccent" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0" stop-color="#A855F7"/>
      <stop offset="1" stop-color="#EC4899"/>
    </linearGradient>
    <style>
      .title {{ font: 700 28px -apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif; fill: {text}; }}
      .rank {{ font: 700 26px -apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif; fill: #C084FC; }}
      .label {{ font: 700 16px -apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif; fill: {text}; }}
      .value {{ font: 600 15px -apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif; fill: {muted}; }}
      .small {{ font: 500 13px -apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif; fill: {muted}; }}
      .track {{ fill: #2A2036; }}
    </style>
  </defs>
  <rect x="1" y="1" width="1198" height="218" rx="14" fill="{bg}" stroke="{border}" stroke-width="2"/>

  <!-- LeetCode mark -->
  <g transform="translate(34 43)">
    <path d="M0 28 L25 2 L44 21 L25 40 L10 25" fill="none" stroke="#F2F2F2" stroke-width="8" stroke-linecap="round" stroke-linejoin="round"/>
    <path d="M31 17 L47 8" stroke="{orange}" stroke-width="8" stroke-linecap="round"/>
    <path d="M29 31 L50 31" stroke="#A7A7A7" stroke-width="8" stroke-linecap="round"/>
  </g>
  <text x="105" y="63" class="title">{esc(USERNAME)}</text>
  <text x="1160" y="62" text-anchor="end" class="rank">{rank}</text>
  <text x="105" y="87" class="small">LeetCode · Problem Solving · DSA</text>

  <g transform="translate(48 112)">
    {bar(0, 0, 330, s['easy'], s['total_easy'], green, 'Easy', f"{s['easy']} / {s['total_easy']}")}
    {bar(390, 0, 330, s['medium'], s['total_medium'], yellow, 'Medium', f"{s['medium']} / {s['total_medium']}")}
    {bar(780, 0, 330, s['hard'], s['total_hard'], red, 'Hard', f"{s['hard']} / {s['total_hard']}")}
  </g>

  <text x="48" y="202" class="small">{s['all']} problems solved</text>
  <text x="1152" y="202" text-anchor="end" class="small">{esc(langs)}</text>
  <rect x="48" y="96" width="1104" height="2" rx="1" fill="url(#lcAccent)" opacity="0.55"/>
</svg>'''
    return svg


try:
    stats = fetch_stats()
    print("Fetched live LeetCode stats")
except Exception as exc:
    stats = FALLBACK
    print(f"Live LeetCode fetch failed; using last-known fallback values: {exc}")

OUT.write_text(render(stats), encoding="utf-8")
print(f"Wrote {OUT}")
