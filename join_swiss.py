#!/usr/bin/env python3
"""
Auto-join all *upcoming* Swiss tournaments of the Chess-Blasters-2 team
using all tokens defined as secrets: TOKEN1, TOKEN2, TOKEN3, etc.
"""

import os
import time
import logging
import requests

TEAM_ID = "chess-blasters-2"
API_ROOT = "https://lichess.org/api"
HEADERS_JSON = {"Accept": "application/json"}

def env_tokens(prefix: str = "TOKEN"):
    """Yield every env var starting with TOKEN that has a non-empty value."""
    for key, value in os.environ.items():
        if key.startswith(prefix) and value:
            yield value

def get_upcoming_swiss() -> list[dict]:
    """Return all Swiss tournaments of the team that haven't started yet."""
    url = f"{API_ROOT}/team/{TEAM_ID}/swiss"
    res = requests.get(url, headers=HEADERS_JSON, timeout=15)
    res.raise_for_status()
    swiss = res.json()  # list of tournaments
    now_ms = time.time() * 1000
    return [s for s in swiss if s.get("startsAt", 0) > now_ms]

def join(token: str, swiss_id: str):
    """Send POST request to join a Swiss tournament using a token."""
    url = f"{API_ROOT}/swiss/{swiss_id}/join"
    headers = {
        "Authorization": f"Bearer {token}"
    }
    res = requests.post(url, headers=headers, timeout=15)
    if res.status_code == 200:
        logging.info("✔ Joined %s successfully", swiss_id)
    elif res.status_code == 400 and "already" in res.text:
        logging.info("• Already joined %s", swiss_id)
    else:
        logging.warning("✖ Failed to join %s → %d %s", swiss_id, res.status_code, res.text.strip())

def main():
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    tournaments = get_upcoming_swiss()
    if not tournaments:
        logging.info("No upcoming Swiss tournaments to join.")
        return

    for t in tournaments:
        swiss_id = t["id"]
        name = t.get("name", "Unnamed")
        start = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(t["startsAt"] / 1000))
        logging.info("→ Swiss ID: %s | Name: %s | Starts at: %s", swiss_id, name, start)
        for token in env_tokens():
            join(token, swiss_id)

if __name__ == "__main__":
    main()
