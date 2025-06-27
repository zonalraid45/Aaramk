#!/usr/bin/env python3 """ Grand Chess Championship scheduler (48 Swiss events)

Starts at 00:00 IST (next midnight), one every 30 minutes until 23:30 IST

7 rounds each; automatic round spacing (interval omitted)

Time controls follow the 12‑item pattern (10+0, 7+2, 3+2, 3+0, 5+0, 10+5, 10+0, 7+2, 3+2, 3+0, 5+0, 3+1) repeated four times


Run this script any time before tournament day; it calculates UTC start times. """ import os import pathlib import datetime as dt from zoneinfo import ZoneInfo import requests

——— Settings ———

TOKEN = os.environ["LICHESS_KEY"].strip('"') TEAM  = "testingsgirl"          # Change as needed ROUNDS = 7                      # rounds per tournament GAP_MIN = 30                    # minutes between successive tournaments

Time‑control pattern: (initial seconds, increment seconds)

_PATTERN = [ (600, 0), (420, 2), (180, 2), (180, 0), (300, 0), (600, 5), (600, 0), (420, 2), (180, 2), (180, 0), (300, 0), (180, 1), ] TIME_CONTROLS = _PATTERN * 4    # 48 tournaments total

HEADERS = {"Authorization": f"Bearer {TOKEN}"} URL     = f"https://lichess.org/api/swiss/new/{TEAM}"

——— Long description ———

DESC_FILE = pathlib.Path(file).with_name("description.txt") try: LONG_DESC = DESC_FILE.read_text(encoding="utf-8").strip() except FileNotFoundError: raise SystemExit("❌ description.txt not found!")

——— Helpers ———

def next_midnight_ist() -> dt.datetime: """Return the next 00:00 in Asia/Kolkata as an aware datetime.""" ist = ZoneInfo("Asia/Kolkata") now = dt.datetime.now(ist) midnight = now.replace(hour=0, minute=0, second=0, microsecond=0) if now >= midnight: midnight += dt.timedelta(days=1) return midnight

def create_one(idx: int, start_utc: dt.datetime, limit: int, increment: int) -> None: payload = { "name": "Grand Chess Championship", "clock.limit":     limit, "clock.increment": increment, "startsAt":        start_utc.strftime("%Y-%m-%dT%H:%M:%SZ"), "nbRounds":        ROUNDS, "variant":         "standard", "rated":           "true", "description":     LONG_DESC, } r = requests.post(URL, headers=HEADERS, data=payload) if r.status_code == 200: print(f"✅ Tmt #{idx+1} created:", r.json().get("url")) else: print(f"❌ Tmt #{idx+1} error", r.status_code, r.text)

——— Main ———

if name == "main": first_start_ist = next_midnight_ist() first_start_utc = first_start_ist.astimezone(dt.timezone.utc)

for i, (limit, inc) in enumerate(TIME_CONTROLS):
    start_time = first_start_utc + dt.timedelta(minutes=i * GAP_MIN)
    create_one(i, start_time, limit, inc)

