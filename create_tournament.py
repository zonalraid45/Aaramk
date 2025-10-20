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
TEAM    = "chess-blasters-2"
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
SCHEDULE = [
    #  time ,      title,      min, inc
    ("00:00", "Cash Tournament Qualifier",    10,  0),
    ("00:30", "Cash Tournament Qualifier",     7,  2),
    ("01:00", "Cash Tournament Qualifier",     3,  2),
    ("01:30", "Cash Tournament Qualifier",     3,  0),
    ("02:00", "Cash Tournament Qualifier",     5,  0),
    ("02:30", "Cash Tournament Qualifier",    10,  5),
    ("03:00", "Cash Tournament Qualifier",    10,  0),
    ("03:30", "Cash Tournament Qualifier",     7,  2),
    ("04:00", "Cash Tournament Qualifier",     3,  2),
    ("04:30", "Cash Tournament Qualifier",     3,  0),
    ("05:00", "Cash Tournament Qualifier",     5,  0),
    ("05:30", "Cash Tournament Qualifier",     3,  1),
    ("06:00", "Cash Tournament Qualifier",    10,  0),
    ("06:30", "Cash Tournament Qualifier",     7,  2),
    ("07:00", "Cash Tournament Qualifier",     3,  2),
    ("07:30", "Cash Tournament Qualifier",     3,  0),
    ("08:00", "Cash Tournament Qualifier",     5,  0),
    ("08:30", "Cash Tournament Qualifier",    10,  5),
    ("09:00", "Cash Tournament Qualifier",    10,  0),
    ("09:30", "Cash Tournament Qualifier",     7,  2),
    ("10:00", "Cash Tournament Qualifier",     3,  2),
    ("10:30", "Cash Tournament Qualifier",     3,  0),
    ("11:00", "Cash Tournament Qualifier",     5,  0),
    ("11:30", "Cash Tournament Qualifier",     3,  0),
    ("12:00", "Cash Tournament Qualifier",     3,  1),
    ("12:30", "Cash Tournament Qualifier",    10,  0),
    ("13:00", "Cash Tournament Qualifier",     7,  2),
    ("13:30", "Cash Tournament Qualifier",     3,  2),
    ("14:00", "Cash Tournament Qualifier",     3,  0),
    ("14:30", "Cash Tournament Qualifier",     5,  0),
    ("15:00", "Cash Tournament Qualifier",    10,  5),
    ("15:30", "Cash Tournament Qualifier",    10,  0),
    ("16:00", "Cash Tournament Qualifier",     7,  2),
    ("16:30", "Cash Tournament Qualifier",     3,  2),
    ("17:00", "Cash Tournament Qualifier",     3,  0),
    ("17:30", "Cash Tournament Qualifier",     5,  0),
    ("18:00", "Cash Tournament Qualifier",     3,  1),
    ("18:30", "Cash Tournament Qualifier",    10,  0),
    ("19:00", "Cash Tournament Qualifier",     7,  2),
    ("19:30", "Cash Tournament Qualifier",     3,  2),
    ("20:00", "Cash Tournament Qualifier",     3,  0),
    ("20:30", "Cash Tournament Qualifier",     5,  0),
    ("21:00", "Cash Tournament Qualifier",    10,  5),
    ("21:30", "Cash Tournament Qualifier",    10,  0),
    ("22:00", "Cash Tournament Qualifier",     7,  2),
    ("22:30", "Cash Tournament Qualifier",     3,  2),
    ("23:00", "Cash Tournament Qualifier",     3,  1),
    ("23:30", "Cash Tournament Qualifier",     5,  0),
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
