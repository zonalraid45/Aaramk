#!/usr/bin/env python3
"""
Auto-join all *up-coming* Swiss tournaments of the Chess-Blasters-2 team.
Uses every repo secret named TOKEN1, TOKEN2, TOKEN3, … as a Lichess token.
"""

import os
import time
import json
import logging
import requests

TEAM_ID = "chess-blasters-2"
API_ROOT = "https://lichess.org/api"
HEADERS_NDJSON = {"Accept": "application/x-ndjson"}


def env_tokens(prefix: str = "TOKEN"):
    for k, v in os.environ.items():
        if k.startswith(prefix) and v:
            yield v


def get_upcoming_swiss() -> list[dict]:
    url = f"{API_ROOT}/team/{TEAM_ID}/swiss"
    res = requests.get(url, headers=HEADERS_NDJSON, timeout=15)
    res.raise_for_status()

    now_ms = time.time() * 1000
    swiss = []

    for line in res.iter_lines(decode_unicode=True):
        if not line:
            continue
        obj = json.loads(line)

        # --- NEW: robust start-time parsing ---------------------------------
        try:
            starts_at = int(obj.get("startsAt", 0))
        except (TypeError, ValueError):
            continue  # skip if startsAt missing or non-numeric
        # --------------------------------------------------------------------

        if starts_at > now_ms:
            swiss.append(obj)

    return swiss


def join(token: str, swiss_id: str):
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
    tournaments = get_upcoming_swiss()
    if not tournaments:
        logging.info("No upcoming Swiss tournaments to join.")
        return

    for t in tournaments:
        swiss_id = t["id"]
        name = t.get("name", "Unnamed")
        start = time.strftime("%Y-%m-%d %H:%M:%S",
                              time.localtime(int(t["startsAt"]) / 1000))
        logging.info("→ %s | %s | Starts: %s", swiss_id, name, start)
        for token in env_tokens():
            join(token, swiss_id)


if __name__ == "__main__":
    main()
