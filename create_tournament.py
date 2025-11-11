#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Create a full day of Swiss tournaments according to the timetable
supplied by Utsa.  All times are interpreted
"""
import os, datetime as dt, pathlib, requests
from zoneinfo import ZoneInfo   # Python ≥3.9

# ─────────────── Settings ───────────────
TOKEN   = os.environ["LICHESS_KEY"].strip('"')
TEAM    = "online-world-chess-lovers"
ROUNDS  = 7
IST     = ZoneInfo("Asia/Kolkata")

headers = {"Authorization": f"Bearer {TOKEN}"}
URL     = f"https://lichess.org/api/swiss/new/{TEAM}"

# ---------- read long description once ----------
DESC_FILE = pathlib.Path(__file__).with_name("description.txt")
try:
    LONG_DESC = DESC_FILE.read_text(encoding="utf-8").strip()
except FileNotFoundError:
    raise SystemExit("❌ description.txt not found!")

# ─────────────── Timetable ───────────────
# ─────────────── Timetable ───────────────
SCHEDULE = [
    ("00:20", "Cash Tournament Qualifier", 10, 0),
    ("01:20", "Cash Tournament Qualifier", 3, 2),
    ("02:20", "Cash Tournament Qualifier", 5, 0),
    ("03:20", "Cash Tournament Qualifier", 7, 2),
    ("04:20", "Cash Tournament Qualifier", 3, 0),
    ("05:20", "Cash Tournament Qualifier", 5, 2),
    ("06:20", "Cash Tournament Qualifier", 10, 0),
    ("07:20", "Cash Tournament Qualifier", 5, 2),
    ("08:20", "Cash Tournament Qualifier", 3, 0),
    ("09:20", "Cash Tournament Qualifier", 10, 0),
    ("10:20", "Cash Tournament Qualifier", 3, 2),
    ("11:20", "Cash Tournament Qualifier", 5, 0),
    ("12:20", "Cash Tournament Qualifier", 7, 2),
    ("13:20", "Cash Tournament Qualifier", 3, 0),
    ("14:20", "Cash Tournament Qualifier", 5, 2),
    ("15:20", "Cash Tournament Qualifier", 10, 5),
    ("16:20", "Cash Tournament Qualifier", 5, 0),
    ("17:20", "Cash Tournament Qualifier", 3, 0),
    ("18:20", "Cash Tournament Qualifier", 5, 2),
    ("19:20", "Cash Tournament Qualifier", 10, 0),
    ("20:20", "Cash Tournament Qualifier", 7, 2),
    ("21:20", "Cash Tournament Qualifier", 3, 2),
    ("22:20", "Cash Tournament Qualifier", 5, 0),
    ("23:20", "Cash Tournament Qualifier", 3, 0),
]

# ─────────────── Helper ───────────────
def next_occurrence(time_str: str) -> dt.datetime:
    """Return the next datetime (≥ now + 5 min) for HH:MM in IST."""
    hh, mm = map(int, time_str.split(":"))
    today   = dt.date.today()
    now_ist = dt.datetime.now(IST)
    cand    = dt.datetime.combine(today, dt.time(hh, mm), tzinfo=IST)
    if cand < now_ist + dt.timedelta(minutes=5):
        cand += dt.timedelta(days=1)
    return cand.astimezone(dt.timezone.utc)   # convert to UTC

def create_tmt(idx: int, name: str, minutes: int, inc: int, start_utc: dt.datetime) -> None:
    payload = {
        "name":                    f"{name}"[:30],
        "clock.limit":             minutes * 60,
        "clock.increment":         inc,
        "startsAt":                start_utc.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "nbRounds":                ROUNDS,
        # No explicit interval -> Lichess chooses automatic
        "variant":                 "standard",
        "rated":                   "true",
        "description":             LONG_DESC,
        "conditions.playYourGames": "true",  # Enforce must-play condition
    }
    r = requests.post(URL, headers=headers, data=payload, timeout=15)
    if r.status_code == 200:
        print(f"✅  {payload['name']:<25} → {r.json().get('url')}")
    else:
        print(f"❌  {payload['name']:<25} ({r.status_code}) {r.text[:120]}")

# ─────────────── Main ───────────────
if __name__ == "__main__":
    for idx, (t, title, mins, inc) in enumerate(SCHEDULE):
        start = next_occurrence(t)
        create_tmt(idx, title, mins, inc, start)
