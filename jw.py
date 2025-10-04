#!/usr/bin/env python3
import os
import time
import json
import logging
import requests
from datetime import datetime, timezone

TEAM_ID = os.environ.get("TEAM_ID", "chess-blasters-2")
TOKEN = os.environ.get("LICHESS_KEY")
if not TOKEN:
    raise ValueError("Environment variable LICHESS_KEY is not set!")
TOKEN = TOKEN.strip('"')

API_ROOT = "https://lichess.org/api"
HEADERS = {"Accept": "application/x-ndjson",
           "Authorization": f"Bearer {TOKEN}"}

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(message)s")


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
    return sorted(swisses, key=lambda s: s["_startsMs"])


def join(swiss_id):
    requests.post(f"{API_ROOT}/swiss/{swiss_id}/join", headers=HEADERS, timeout=15)
    logging.info(f"Joined Swiss: {swiss_id}")


def withdraw(swiss_id):
    requests.post(f"{API_ROOT}/swiss/{swiss_id}/withdraw", headers=HEADERS, timeout=15)
    logging.info(f"Withdrawn from Swiss: {swiss_id}")


def main():
    swisses = get_upcoming_swiss(TEAM_ID)
    now_ms = int(time.time() * 1000)

    for s in swisses:
        swiss_id = s["id"]
        join(swiss_id)

    for s in swisses:
        swiss_id = s["id"]
        start_ms = s["_startsMs"]
        sleep_sec = max((start_ms - now_ms) / 1000 - 8 * 60, 0)
        if sleep_sec > 0:
            time.sleep(sleep_sec)
        withdraw(swiss_id)
        now_ms = int(time.time() * 1000)


if __name__ == "__main__":
    main()
