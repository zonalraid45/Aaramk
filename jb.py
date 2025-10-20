#!/usr/bin/env python3
import os
import time
import json
import requests
from datetime import datetime, timezone

TEAM_ID = os.environ.get("TEAM_ID", "chess-blasters-2")

# ────────────────── Tokens ──────────────────
TOKEN1 = os.environ.get("LICHESS_KEY")
TOKEN2 = os.environ.get("LICHESS_KEYS")
TOKEN_T = os.environ.get("T")
TOKEN_L = os.environ.get("L")

TOKENS = [t.strip('"').strip("'") for t in [TOKEN1, TOKEN2, TOKEN_T, TOKEN_L] if t]
if not TOKENS:
    raise ValueError("No tokens found (LICHESS_KEY, LICHESS_KEYS, T, L)")

API_ROOT = "https://lichess.org/api"

# ────────────────── Helpers ──────────────────
def get_account_name(token):
    """Get Lichess username for this token."""
    headers = {"Authorization": f"Bearer {token}"}
    try:
        res = requests.get(f"{API_ROOT}/account", headers=headers, timeout=10)
        if res.status_code == 200:
            return res.json().get("username", "UnknownUser")
    except Exception:
        pass
    return "UnknownUser"

def get_upcoming_swiss(token, team_id):
    """Fetch upcoming Swiss tournaments for the team."""
    headers = {"Accept": "application/x-ndjson", "Authorization": f"Bearer {token}"}
    url = f"{API_ROOT}/team/{team_id}/swiss"
    try:
        res = requests.get(url, headers=headers, timeout=15)
        res.raise_for_status()
    except requests.RequestException:
        return []

    now_ms = int(time.time() * 1000)
    swisses = []
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
        if not isinstance(starts_ms, int):
            try:
                starts_ms = int(datetime.strptime(starts_ms, "%Y-%m-%dT%H:%M:%SZ")
                                .replace(tzinfo=timezone.utc).timestamp() * 1000)
            except ValueError:
                continue
        if starts_ms > now_ms:
            obj["_startsMs"] = starts_ms
            swisses.append(obj)
    return sorted(swisses, key=lambda s: s["_startsMs"])

def withdraw(token, swiss_id):
    """Withdraw from a Swiss tournament."""
    headers = {"Accept": "application/x-ndjson", "Authorization": f"Bearer {token}"}
    try:
        res = requests.post(f"{API_ROOT}/swiss/{swiss_id}/withdraw", headers=headers, timeout=15)
        if res.status_code == 200:
            print(f"✅ Withdrawn successfully from {swiss_id}")
            return True
        elif res.status_code == 400 and "not joined" in res.text:
            print(f"⚠️ Already withdrawn or not joined: {swiss_id}")
            return True
        else:
            print(f"❌ Withdraw failed {swiss_id}: {res.status_code}")
    except requests.RequestException as e:
        print(f"❗ Withdraw request error for {swiss_id}: {e}")
    return False

# ────────────────── Main ──────────────────
def main():
    last_processed = {}  # store last processed Swiss IDs to avoid repeating
    usernames = {}

    # Preload usernames once
    for token in TOKENS:
        usernames[token] = get_account_name(token)
        print(f"✅ Loaded account: {usernames[token]}")

    print("\n🚀 Running infinite Swiss monitor...\n")

    while True:
        for token in TOKENS:
            username = usernames.get(token, "UnknownUser")
            print(f"\n=== Checking for {username} ===")

            swisses = get_upcoming_swiss(token, TEAM_ID)
            if not swisses:
                print("No upcoming Swiss tournaments.")
                continue

            now_ms = int(time.time() * 1000)
            for s in swisses:
                swiss_id = s["id"]
                start_ms = s["_startsMs"]
                mins_left = (start_ms - now_ms) / 60000

                if swiss_id in last_processed and (time.time() - last_processed[swiss_id]) < 7200:
                    continue  # skip if processed recently

                if mins_left <= 3 and mins_left > 0:
                    print(f"⏰ {username}: Withdrawing from {swiss_id} (starts in {mins_left:.1f}m)")
                    success = withdraw(token, swiss_id)
                    last_processed[swiss_id] = time.time()

                    print("⏳ Waiting 1 minute before retry check...")
                    time.sleep(60)

                    if not success:
                        print(f"🔁 Retrying withdrawal for {swiss_id}...")
                        withdraw(token, swiss_id)
                    else:
                        print(f"✅ Verified withdrawn for {swiss_id}")

        print("\n🕒 Sleeping 5 minutes before next check...\n")
        time.sleep(300)  # sleep 5 minutes before checking again

if __name__ == "__main__":
    main()
