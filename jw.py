#!/usr/bin/env python3
import os
import time
import json
import logging
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

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

# ────────────────── Helpers ────────────────── #
def get_upcoming_swiss(team_id):
    """Fetch upcoming Swiss tournaments for the team."""
    url = f"{API_ROOT}/team/{team_id}/swiss"
    logging.info(f"Fetching upcoming Swiss tournaments for team: {team_id}")
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

    logging.info(f"Found {len(swisses)} upcoming Swiss tournaments.")
    for s in swisses:
        logging.info(f"- {s['id']} starts at {datetime.utcfromtimestamp(s['_startsMs']/1000).strftime('%Y-%m-%d %H:%M:%S UTC')}")

    return sorted(swisses, key=lambda s: s["_startsMs"])


def join(swiss_id):
    """Join a Swiss tournament."""
    try:
        res = requests.post(f"{API_ROOT}/swiss/{swiss_id}/join", headers=HEADERS, timeout=15)
        if res.status_code == 200:
            logging.info(f"✅ Joined Swiss: {swiss_id}")
        elif res.status_code == 400 and "already" in res.text:
            logging.info(f"ℹ️ Already joined Swiss: {swiss_id}")
        else:
            logging.warning(f"⚠️ Failed to join {swiss_id} | Status {res.status_code} | {res.text.strip()[:100]}")
    except requests.RequestException as e:
        logging.error(f"Join request failed for {swiss_id}: {e}")


def withdraw(swiss_id):
    """Withdraw from a Swiss tournament."""
    try:
        res = requests.post(f"{API_ROOT}/swiss/{swiss_id}/withdraw", headers=HEADERS, timeout=15)
        if res.status_code == 200:
            logging.info(f"🟡 Withdrawn from Swiss: {swiss_id}")
        elif res.status_code == 400 and "not joined" in res.text:
            logging.info(f"ℹ️ Already withdrawn or not joined: {swiss_id}")
        else:
            logging.warning(f"⚠️ Failed to withdraw {swiss_id} | Status {res.status_code} | {res.text.strip()[:100]}")
    except requests.RequestException as e:
        logging.error(f"Withdraw request failed for {swiss_id}: {e}")


# ────────────────── Main ────────────────── #
def main():
    logging.info("Starting Swiss join-withdraw automation...")
    swisses = get_upcoming_swiss(TEAM_ID)
    now_ms = int(time.time() * 1000)

    if not swisses:
        logging.info("No upcoming Swiss tournaments found. Exiting.")
        return

    # Step 1: Join all upcoming Swiss immediately
    for s in swisses:
        swiss_id = s["id"]
        logging.info(f"Attempting to join Swiss {swiss_id}...")
        join(swiss_id)
        time.sleep(2)  # small delay to avoid API spam

    # Step 2: Withdraw 3 minutes before each Swiss
    for s in swisses:
        swiss_id = s["id"]
        start_ms = s["_startsMs"]
        withdraw_time = datetime.utcfromtimestamp((start_ms - 3 * 60 * 1000) / 1000)
        sleep_sec = max((start_ms - now_ms) / 1000 - 3 * 60, 0)

        logging.info(f"Scheduled withdrawal for {swiss_id} at {withdraw_time.strftime('%Y-%m-%d %H:%M:%S UTC')} "
                     f"(in {int(sleep_sec)} seconds).")

        if sleep_sec > 0:
            time.sleep(sleep_sec)

        withdraw(swiss_id)
        now_ms = int(time.time() * 1000)

    logging.info("Automation completed successfully.")


if __name__ == "__main__":
    main()
