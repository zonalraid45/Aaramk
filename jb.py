#!/usr/bin/env python3
import os
import time
import json
import requests
from datetime import datetime, timezone

TEAM_ID = os.environ.get("TEAM_ID", "chess-blasters-2")

# ───────────── Tokens ─────────────
TOKEN1 = os.environ.get("LICHESS_KEY")
TOKEN2 = os.environ.get("LICHESS_KEYS")
TOKEN_T = os.environ.get("T")
TOKEN_L = os.environ.get("L")

TOKENS = [t.strip('"').strip("'") for t in [TOKEN1, TOKEN2, TOKEN_T, TOKEN_L] if t]
if not TOKENS:
    raise ValueError("No tokens found (LICHESS_KEY, LICHESS_KEYS, T, L)")

API_ROOT = "https://lichess.org/api"

# ───────────── Helpers ─────────────
def get_username(token):
    try:
        res = requests.get(f"{API_ROOT}/account",
                           headers={"Authorization": f"Bearer {token}"}, timeout=10)
        if res.status_code == 200:
            return res.json().get("username", "UnknownUser")
    except Exception:
        pass
    return "UnknownUser"

def get_team_swisses(token):
    """Return list of future swisses for the team."""
    try:
        r = requests.get(f"{API_ROOT}/team/{TEAM_ID}/swiss",
                         headers={"Accept": "application/x-ndjson",
                                  "Authorization": f"Bearer {token}"}, timeout=15)
        r.raise_for_status()
    except Exception:
        return []

    now = int(time.time() * 1000)
    items = []
    for line in r.iter_lines(decode_unicode=True):
        if not line:
            continue
        try:
            obj = json.loads(line)
        except json.JSONDecodeError:
            continue
        starts = obj.get("startsAt")
        if not starts:
            continue
        if not isinstance(starts, int):
            try:
                starts = int(datetime.strptime(starts, "%Y-%m-%dT%H:%M:%SZ")
                             .replace(tzinfo=timezone.utc).timestamp() * 1000)
            except ValueError:
                continue
        if starts > now:
            obj["_startsMs"] = starts
            items.append(obj)
    return sorted(items, key=lambda x: x["_startsMs"])

def withdraw(token, swiss_id):
    """Try to withdraw; return True if done or already withdrawn."""
    try:
        r = requests.post(f"{API_ROOT}/swiss/{swiss_id}/withdraw",
                          headers={"Authorization": f"Bearer {token}"}, timeout=10)
        if r.status_code == 200:
            print(f"✅  Withdraw OK  {swiss_id}")
            return True
        if r.status_code == 400 and "not joined" in r.text:
            print(f"⚠️  Already withdrawn  {swiss_id}")
            return True
        print(f"❌  Withdraw fail {swiss_id}: {r.status_code} {r.text[:80]}")
    except Exception as e:
        print(f"❗ Withdraw error {swiss_id}: {e}")
    return False

# ───────────── Main Loop ─────────────
def main():
    usernames = {t: get_username(t) for t in TOKENS}
    print("🚀 Running Swiss auto-withdraw bot (always active)\n")
    handled = {}   # swiss_id -> {"time": last_attempt_ms, "retried": bool}

    while True:
        now = int(time.time() * 1000)
        for token in TOKENS:
            uname = usernames[token]
            swisses = get_team_swisses(token)
            if not swisses:
                continue
            for s in swisses:
                sid = s["id"]
                start = s["_startsMs"]
                mins_left = (start - now) / 60000.0

                if mins_left <= 0:
                    continue  # started already
                # T−3: withdraw; T−2: retry once
                if 2.9 <= mins_left <= 3.1 and sid not in handled:
                    print(f"[{uname}] Withdrawing from {sid} (starts in {mins_left:.2f} m)")
                    ok = withdraw(token, sid)
                    handled[sid] = {"time": now, "retried": False, "ok": ok}

                elif 1.9 <= mins_left <= 2.1 and sid in handled and not handled[sid]["retried"]:
                    if not handled[sid]["ok"]:
                        print(f"[{uname}] Retry withdrawal for {sid} (starts in {mins_left:.2f} m)")
                        withdraw(token, sid)
                    handled[sid]["retried"] = True

        # short pause just to avoid hammering API too hard
        time.sleep(5)

if __name__ == "__main__":
    main()
