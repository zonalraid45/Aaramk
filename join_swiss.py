#!/usr/bin/env python3
"""
Auto-join every *up-coming* Swiss tournament created by the Chess-Blasters-2 team.

・Reads any repo secret whose name starts with TOKEN (TOKEN1, TOKEN2, TOKEN3…).
・Uses the first token both to list tournaments (GET) and to join them (POST).
"""

import os
import time
import json
import logging
import requests
from itertools import islice

TEAM_ID = "chess-blasters-2"
API_ROOT = "https://lichess.org/api"
HEADERS_NDJSON = {"Accept": "application/x-ndjson"}


# --------------------------------------------------------------------------- #
#  helpers
# --------------------------------------------------------------------------- #

def env_tokens(prefix: str = "TOKEN"):
    """Yield every non-empty env var whose name starts with TOKEN."""
    for k, v in os.environ.items():
        if k.startswith(prefix) and v:
            yield v


def get_upcoming_swiss(tokens) -> list[dict]:
    """
    Return Swiss tournaments that haven’t started yet.

    We authenticate the request with the first token (if any) so that
    invite-only events are visible in the API response.
    """
    url = f"{API_ROOT}/team/{TEAM_ID}/swiss"
    headers = dict(HEADERS_NDJSON)
    first = next(tokens, None)
    if first:                              # add auth only if we actually have one
        headers["Authorization"] = f"Bearer {first}"
        # put the token back for later JOIN calls
        tokens = (t for t in ([first] + list(tokens)))

    res = requests.get(url, headers=headers, timeout=15)
    res.raise_for_status()

    now_ms = time.time() * 1000
    swiss, raw = [], []

    for line in res.iter_lines(decode_unicode=True):
        if not line:
            continue
        obj = json.loads(line)
        raw.append(obj)
        try:
            starts_at = int(obj.get("startsAt", 0))
        except (TypeError, ValueError):
            continue
        if starts_at > now_ms:
            swiss.append(obj)

    # ----------------------------- DEBUG ----------------------------------- #
    logging.info("Total Swiss tournaments fetched: %d", len(raw))
    if not swiss:
        logging.info("No future Swiss returned. First few raw entries:")
        for o in islice(raw, 0, 5):
            logging.info("  %s | startsAt=%s", o.get("id"), o.get("startsAt"))
    # ---------------------------------------------------------------------- #

    return swiss, tokens


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


# --------------------------------------------------------------------------- #
#  main
# --------------------------------------------------------------------------- #

def main():
    logging.basicConfig(level=logging.INFO, format="%(message)s")

    all_tokens = list(env_tokens())
    if not all_tokens:
        logging.error("No TOKEN* secrets found — nothing to do.")
        return

    upcoming, tokens_for_use = get_upcoming_swiss(iter(all_tokens))
    if not upcoming:
        logging.info("No upcoming Swiss tournaments to join.")
        return

    for t in upcoming:
        swiss_id = t["id"]
        name = t.get("name", "Unnamed")
        start = time.strftime("%Y-%m-%d %H:%M:%S",
                              time.localtime(int(t["startsAt"]) / 1000))
        logging.info("→ %s | %s | Starts: %s", swiss_id, name, start)

        for token in tokens_for_use:
            join(token, swiss_id)


if __name__ == "__main__":
    main()
