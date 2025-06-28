#!/usr/bin/env python3
"""
Auto-join every *up-coming* Swiss tournament created by the Chess-Blasters-2 team.
Uses every repo secret named TOKEN1, TOKEN2, TOKEN3, … as a Lichess token.
"""

import os
import time
import json
import logging
import requests
from datetime import datetime, timezone
from typing import Iterator, List, Dict

TEAM_ID = "chess-blasters-2"
API_ROOT = "https://lichess.org/api"
HEADERS_NDJSON = {"Accept": "application/x-ndjson"}


# ───────────────────────── helpers ───────────────────────── #

def env_tokens(prefix: str = "TOKEN") -> Iterator[str]:
    """Yield each non-empty env var whose name starts with TOKEN."""
    for k, v in os.environ.items():
        if k.startswith(prefix) and v:
            yield v


def iso_to_epoch_ms(iso_str: str) -> int:
    """Convert '2025-11-07T18:30:00Z' →  int milliseconds since epoch."""
    dt = datetime.strptime(iso_str, "%Y-%m-%dT%H:%M:%SZ")
    return int(dt.replace(tzinfo=timezone.utc).timestamp() * 1000)


def get_upcoming_swiss(tokens: List[str]) -> List[Dict]:
    """Return Swiss events whose start time is still in the future."""
    url = f"{API_ROOT}/team/{TEAM_ID}/swiss"

    headers = dict(HEADERS_NDJSON)
    if tokens:                                    # authenticate the GET
        headers["Authorization"] = f"Bearer {tokens[0]}"

    res = requests.get(url, headers=headers, timeout=15)
    res.raise_for_status()

    now_ms = int(time.time() * 1000)
    upcoming = []

    for line in res.iter_lines(decode_unicode=True):
        if not line:
            continue
        obj = json.loads(line)
        iso_start = obj.get("startsAt")
        if not iso_start:
            continue
        try:
            starts_ms = iso_to_epoch_ms(iso_start)
        except ValueError:
            logging.warning("Unparsable startsAt: %s", iso_start)
            continue

        if starts_ms > now_ms:
            obj["_startsMs"] = starts_ms      # cache parsed value for later
            upcoming.append(obj)

    return upcoming


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
        logging.warning("✖ %s → %d %s",
                        swiss_id, res.status_code, res.text.strip()[:120])


# ───────────────────────── main ───────────────────────── #

def main():
    logging.basicConfig(level=logging.INFO, format="%(message)s")

    tokens = list(env_tokens())
    if not tokens:
        logging.error("No TOKEN* secrets found — nothing to do.")
        return

    swiss_events = get_upcoming_swiss(tokens)
    if not swiss_events:
        logging.info("No upcoming Swiss tournaments to join.")
        return

    for t in swiss_events:
        swiss_id = t["id"]
        name = t.get("name", "Unnamed")
        start_iso = t["startsAt"]
        logging.info("→ %s | %s | Starts: %s", swiss_id, name, start_iso)

        for token in tokens:
            join(token, swiss_id)


if __name__ == "__main__":
    main()
