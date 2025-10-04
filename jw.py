#!/usr/bin/env python3
import os
import time
import json
import requests
from datetime import datetime, timezone

TEAM_ID = os.environ.get("TEAM_ID", "chess-blasters-2")
TOKEN = os.environ["LICHESS_KEY"]
API_ROOT = "https://lichess.org/api"
HEADERS = {"Accept": "application/x-ndjson",
           "Authorization": f"Bearer {TOKEN}"}


def get_upcoming_swiss(team_id):
    url = f"{API_ROOT}/team/{team_id}/swiss"
    res = requests.get(url, headers=HEADERS, timeout=15)
    res.raise_for_status()
    swisses = []
    now_ms = int(time.time() * 1000)

    for line in res.iter_lines(decode_unicode=True):
        if not line:
            continue
        obj = json.loads(line)
        starts_ms = obj.get("startsAt")
        if not starts_ms:
            continue
        if isinstance(starts_ms, int):
            start_epoch = starts_ms
        else:
            try:
                start_epoch = int(datetime.strptime(starts_ms, "%Y-%m-%dT%H:%M:%SZ")
                                  .replace(tzinfo=timezone.utc).timestamp() * 1000)
            except ValueError:
                continue
        if start_epoch > now_ms:
            obj["_startsMs"] = start_epoch
            swisses.append(obj)
    return swisses


def join(swiss_id):
    requests.post(f"{API_ROOT}/swiss/{swiss_id}/join", headers=HEADERS, timeout=15)


def withdraw(swiss_id):
    requests.post(f"{API_ROOT}/swiss/{swiss_id}/withdraw", headers=HEADERS, timeout=15)


def main():
    swisses = get_upcoming_swiss(TEAM_ID)
    now_ms = int(time.time() * 1000)

    for s in swisses:
        swiss_id = s["id"]
        start_ms = s["_startsMs"]
        mins_to_start = (start_ms - now_ms) / 1000 / 60

        if mins_to_start > 8:
            join(swiss_id)
        elif 0 < mins_to_start <= 8:
            withdraw(swiss_id)


if __name__ == "__main__":
    main()
