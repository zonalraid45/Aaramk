#!/usr/bin/env python3
"""
Auto-join all *up-coming* Swiss tournaments of the Chess-Blasters-2 team
using any repo secrets named TOKEN1, TOKEN2, TOKEN3, … (add more as needed).
"""

import os
import time
import json
import logging
import requests

TEAM_ID = "chess-blasters-2"
API_ROOT = "https://lichess.org/api"

# Ask explicitly for NDJSON so we can parse line-by-line
HEADERS_NDJSON = {"Accept": "application/x-ndjson"}


def env_tokens(prefix: str = "TOKEN"):
    """Yield every non-empty env var whose name starts with TOKEN."""
    for k, v in os.environ.items():
        if k.startswith(prefix) and v:
            yield v


def get_upcoming_swiss() -> list[dict]:
    """
    Return a list of Swiss-tournament objects that haven’t started yet.
    /team/{id}/swiss streams NDJSON, so we read it line-by-line.
    """
    url = f"{API_ROOT}/team/{TEAM_ID}/swiss"
    res = requests.get(url, headers=HEADERS_NDJSON, timeout=15)
    res.raise_for_status()

    now_ms = time.time() * 1000
    tournaments: list[dict] = []

    for line in res.iter_lines(decode_unicode=True):
        if not line:
            continue                    # skip blank lines
        obj = json.loads(line)
        if obj.get("startsAt", 0) > now_ms:
            tournaments.append(obj)

    return tournaments


def join(token: str, swiss_id: str):
    """Send POST request to join a Swiss tournament with a given token."""
    url = f"{API_ROOT}/swiss/{swiss_id}/join"
    res = requests.post(url,
                        headers={"Authorization": f"Bearer {token}"},
                        timeout=15)
    if res.status_code == 200:
        logging.info("✔ Joined %s", swiss_id)
    elif res.status_code == 400 and "already" in res.text:
        logging.info("• Already joined %s", swiss_id)
    else:
        logging.warning("✖ %s → %d %s", swiss_id,
                        res.status_code, res.text.strip()[:200])


def main():
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    swiss_list = get_upcoming_swiss()

    if not swiss_list:
        logging.info("No upcoming Swiss tournaments to join.")
        return

    for t in swiss_list:
        swiss_id = t["id"]
        name = t.get("name", "Unnamed")
        start = time.strftime("%Y-%m-%d %H:%M:%S",
                              time.localtime(t["startsAt"] / 1000))
        logging.info("→ Swiss ID: %s | Name: %s | Starts at: %s",
                     swiss_id, name, start)
        for token in env_tokens():
            join(token, swiss_id)


if __name__ == "__main__":
    main()
