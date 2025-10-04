#!/usr/bin/env python3
import os
import time
import json
import requests
from datetime import datetime, timezone

# ────────────────── Configuration ────────────────── #
TEAM_ID = os.environ.get("TEAM_ID", "chess-blasters-2")
TOKEN = os.environ.get("LICHESS_KEY")
if not TOKEN:
    raise ValueError("Environment variable LICHESS_KEY is not set!")
TOKEN = TOKEN.strip('"')

API_ROOT = "https://lichess.org/api"
HEADERS = {
    "Accept": "application/x-ndjson",
    "Authorization": f"Bearer {TOKEN}"
}

# ────────────────── Helpers ────────────────── #
def get_upcoming_swiss(team_id):
    """Fetch upcoming Swiss tournaments for the team."""
    url = f"{API_ROOT}/team/{team_id}/swiss"
    res = requests.get(url, headers=HEADERS, timeout=15)
    res.raise_for_status()

    swisses = []
    now_ms = int(time.time() * 1000)

    for line in res.iter_lines(decode_unicode=True):
        if not line:
            continue
        try:
            obj = json.loads(line)
        except json.JSONDecodeError:
            continue

        starts_ms = obj.get("startsAt")
        if not starts_ms:
            continue
        if isinstance(starts_ms, int):
            start_epoch = starts_ms
        else:
            try:
                start_epoch = int(
                    datetime.strptime(starts_ms, "%Y-%m-%dT%H:%M:%SZ")
                    .replace(tzinfo=timezone.utc).timestamp() * 1000
                )
            except ValueError:
                continue

        if start_epoch > now_ms:
            obj["_startsMs"] = start_epoch
            swisses.append(obj)

    # Print tournament list with start time
    print(f"Found {len(swisses)} upcoming Swiss tournaments:")
    for s in swisses:
        start_time = datetime.utcfromtimestamp(s["_startsMs"]/1000)
        print(f"- {s['id']} | Starts at: {start_time.strftime('%Y-%m-%d %H:%M:%S UTC')}")

    return sorted(swisses, key=lambda s: s["_startsMs"])


def withdraw(swiss_id):
    """Withdraw from a Swiss tournament."""
    try:
        res = requests.post(f"{API_ROOT}/swiss/{swiss_id}/withdraw", headers=HEADERS, timeout=15)
        if res.status_code == 200:
            print(f"Withdraw successfully from Swiss: {swiss_id}")
        elif res.status_code == 400 and "not joined" in res.text:
            print(f"Already withdrawn or not joined: {swiss_id}")
        else:
            print(f"Failed to withdraw {swiss_id} | Status {res.status_code}")
    except requests.RequestException as e:
        print(f"Withdraw request failed for {swiss_id}: {e}")


# ────────────────── Main ────────────────── #
def main():
    swisses = get_upcoming_swiss(TEAM_ID)
    now_ms = int(time.time() * 1000)

    if not swisses:
        print("No upcoming Swiss tournaments found. Exiting.")
        return

    # Withdraw 3 minutes before each Swiss
    for s in swisses:
        swiss_id = s["id"]
        start_ms = s["_startsMs"]
        sleep_sec = max((start_ms - now_ms) / 1000 - 3 * 60, 0)

        print(f"Will withdraw from {swiss_id} in {int(sleep_sec)} seconds.")

        if sleep_sec > 0:
            time.sleep(sleep_sec)

        withdraw(swiss_id)
        now_ms = int(time.time() * 1000)


if __name__ == "__main__":
    main()
