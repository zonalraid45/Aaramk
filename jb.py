#!/usr/bin/env python3
import os
import time
import json
import requests
from datetime import datetime, timezone

# ────────────────── Configuration ──────────────────
TEAM_ID = os.environ.get("TEAM_ID", "chess-blasters-2")

# Fetch all possible token sources
TOKEN1 = os.environ.get("LICHESS_KEY")
TOKEN2 = os.environ.get("LICHESS_KEYS")
TOKEN_T = os.environ.get("T")
TOKEN_L = os.environ.get("L")

if not any([TOKEN1, TOKEN2, TOKEN_T, TOKEN_L]):
    raise ValueError("No Lichess API tokens found! Set one of: LICHESS_KEY, LICHESS_KEYS, T, or L.")

# Strip quotes if present
def clean_token(token):
    return token.strip('"').strip("'") if token else None

TOKENS = [clean_token(t) for t in [TOKEN1, TOKEN2, TOKEN_T, TOKEN_L] if t]

API_ROOT = "https://lichess.org/api"

# ────────────────── Helpers ──────────────────
def get_upcoming_swiss(token, team_id):
    """Fetch upcoming Swiss tournaments for the team using a specific token."""
    headers = {
        "Accept": "application/x-ndjson",
        "Authorization": f"Bearer {token}"
    }
    url = f"{API_ROOT}/team/{team_id}/swiss"
    res = requests.get(url, headers=headers, timeout=15)
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
                    .replace(tzinfo=timezone.utc)
                    .timestamp() * 1000
                )
            except ValueError:
                continue

        if start_epoch > now_ms:
            obj["_startsMs"] = start_epoch
            swisses.append(obj)

    return sorted(swisses, key=lambda s: s["_startsMs"])

def withdraw(token, swiss_id):
    """Withdraw from a Swiss tournament using a specific token."""
    headers = {
        "Accept": "application/x-ndjson",
        "Authorization": f"Bearer {token}"
    }
    try:
        res = requests.post(f"{API_ROOT}/swiss/{swiss_id}/withdraw", headers=headers, timeout=15)
        if res.status_code == 200:
            print(f"✅ Withdrawn successfully from Swiss: {swiss_id}")
        elif res.status_code == 400 and "not joined" in res.text:
            print(f"⚠️ Already withdrawn or not joined: {swiss_id}")
        else:
            print(f"❌ Failed to withdraw {swiss_id} | Status {res.status_code}")
    except requests.RequestException as e:
        print(f"❗ Withdraw request failed for {swiss_id}: {e}")

# ────────────────── Main ──────────────────
def main():
    for token in TOKENS:
        print(f"\n=== Using token: {token[:8]}*** ===")
        try:
            swisses = get_upcoming_swiss(token, TEAM_ID)
        except requests.RequestException as e:
            print(f"Failed to fetch Swiss list with token {token[:8]}***: {e}")
            continue

        now_ms = int(time.time() * 1000)
        if not swisses:
            print("No upcoming Swiss tournaments found. Skipping this token.")
            continue

        for s in swisses:
            swiss_id = s["id"]
            start_ms = s["_startsMs"]
            sleep_sec = max((start_ms - now_ms) / 1000 - 3 * 60, 0)

            print(f"Will withdraw from {swiss_id} in {int(sleep_sec)} seconds.")
            if sleep_sec > 0:
                time.sleep(sleep_sec)

            withdraw(token, swiss_id)
            now_ms = int(time.time() * 1000)

if __name__ == "__main__":
    main()
