#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import datetime as dt
import pathlib
import requests
from zoneinfo import ZoneInfo

TOKEN = os.environ["LICHESS_KEY"].strip('"')
TEAM = "online-world-chess-lovers"
ROUNDS = 7
IST = ZoneInfo("Asia/Kolkata")
DELAY_DAYS = 4

headers = {"Authorization": f"Bearer {TOKEN}"}
URL = f"https://lichess.org/api/swiss/new/{TEAM}"

DESC_FILE = pathlib.Path(__file__).with_name("description.txt")
try:
    LONG_DESC = DESC_FILE.read_text(encoding="utf-8").strip()
except FileNotFoundError:
    raise SystemExit("❌ description.txt not found!")

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

def scheduled_time_utc(time_str: str) -> dt.datetime:
    hh, mm = map(int, time_str.split(":"))
    now_ist = dt.datetime.now(IST)
    target_date = (now_ist + dt.timedelta(days=DELAY_DAYS)).date()
    start_ist = dt.datetime.combine(
        target_date,
        dt.time(hh, mm),
        tzinfo=IST
    )
    return start_ist.astimezone(dt.timezone.utc)

def create_tmt(name: str, minutes: int, inc: int, start_utc: dt.datetime) -> None:
    payload = {
        "name": name[:30],
        "clock.limit": minutes * 60,
        "clock.increment": inc,
        "startsAt": start_utc.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "nbRounds": ROUNDS,
        "variant": "standard",
        "rated": "true",
        "description": LONG_DESC,
        "conditions.playYourGames": "true",
    }

    r = requests.post(URL, headers=headers, data=payload, timeout=15)

    if r.status_code == 200:
        print(f"✅ {name:<25} → {r.json().get('url')}")
    else:
        print(f"❌ {name:<25} ({r.status_code}) {r.text[:120]}")

if __name__ == "__main__":
    for time_str, title, mins, inc in SCHEDULE:
        start = scheduled_time_utc(time_str)
        create_tmt(title, mins, inc, start)
