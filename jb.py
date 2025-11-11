#!/usr/bin/env python3
import os
import time
import json
import requests
from datetime import datetime, timezone

# ────────────────── CONFIG ──────────────────
TEAM_ID = os.environ.get("TEAM_ID", "chess-blasters-2")

TOKEN_NAMES = ["LICHESS_KEY", "LICHESS_KEYS", "T", "L"]
TOKENS = []
for name in TOKEN_NAMES:
    val = os.environ.get(name)
    if val:
        TOKENS.append(val.strip('"').strip("'"))

if not TOKENS:
    raise SystemExit("❌ No tokens found! Please export LICHESS_KEY, LICHESS_KEYS, T, W, or L")

API_ROOT = "https://lichess.org/api"

# ────────────────── HELPERS ──────────────────
def now_ms():
    return int(time.time() * 1000)

def get_username(token):
    try:
        r = requests.get(f"{API_ROOT}/account", headers={"Authorization": f"Bearer {token}"}, timeout=10)
        if r.status_code == 200:
            return r.json().get("username")
        else:
            print(f"[{token[:8]}] account fetch failed ({r.status_code}): {r.text}")
    except Exception as e:
        print(f"[{token[:8]}] account fetch error: {e}")
    return None

def get_upcoming_swisses(token, team_id):
    headers = {"Accept": "application/x-ndjson", "Authorization": f"Bearer {token}"}
    res = requests.get(f"{API_ROOT}/team/{team_id}/swiss", headers=headers, timeout=15)
    res.raise_for_status()

    swisses = []
    now = now_ms()
    for line in res.iter_lines(decode_unicode=True):
        if not line:
            continue
        try:
            obj = json.loads(line)
        except json.JSONDecodeError:
            continue
        starts = obj.get("startsAt")
        if not starts:
            continue
        try:
            start_ms = int(
                datetime.strptime(starts, "%Y-%m-%dT%H:%M:%SZ")
                .replace(tzinfo=timezone.utc)
                .timestamp() * 1000
            )
        except Exception:
            continue
        if start_ms > now:
            obj["_startsMs"] = start_ms
            swisses.append(obj)
    return sorted(swisses, key=lambda s: s["_startsMs"])

def withdraw(token, swiss_id, username):
    headers = {"Authorization": f"Bearer {token}"}
    try:
        r = requests.post(f"{API_ROOT}/swiss/{swiss_id}/withdraw", headers=headers, timeout=15)
        if r.status_code == 200:
            print(f"✅ [{username}] Withdraw OK {swiss_id}")
        elif "not joined" in r.text.lower():
            print(f"ℹ️ [{username}] Already not joined {swiss_id}")
        else:
            print(f"⚠️ [{username}] Withdraw failed {swiss_id} ({r.status_code}): {r.text}")
    except Exception as e:
        print(f"❌ [{username}] Withdraw error {swiss_id}: {e}")

# ────────────────── MAIN ──────────────────
print("──────────────────────────────")
print("🚀 Running Swiss auto-withdraw bot (always active)\n")

# Load usernames for all tokens
usernames = {}
for t in TOKENS:
    u = get_username(t)
    if u:
        usernames[t] = u

if not usernames:
    raise SystemExit("❌ No valid usernames fetched from tokens.")

print("Loaded accounts:")
for name in usernames.values():
    print("  -", name)

print("\nBot active. Monitoring upcoming Swiss tournaments...\n")

# ────────────────── LOOP ──────────────────
while True:
    for token, uname in usernames.items():
        try:
            swisses = get_upcoming_swisses(token, TEAM_ID)
        except Exception as e:
            print(f"[{uname}] ❌ Failed to fetch Swiss list: {e}")
            continue

        now = now_ms()
        if not swisses:
            continue

        for s in swisses:
            sid = s["id"]
            start = s["_startsMs"]
            mins_left = (start - now) / 60000

            # Withdraw one account at a time
            if 2.5 <= mins_left <= 3.5:
                print(f"[{uname}] Withdrawing from {sid} (starts in {mins_left:.2f} min)")
                withdraw(token, sid, uname)

            elif 1.5 <= mins_left <= 2.5:
                print(f"[{uname}] Retrying withdraw {sid} (starts in {mins_left:.2f} min)")
                withdraw(token, sid, uname)

        # brief pause between accounts to avoid API spam
        time.sleep(3)

    # active continuous checking
    time.sleep(15)
