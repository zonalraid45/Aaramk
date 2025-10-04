import os
import requests
from datetime import datetime, timezone

LICHESS_API = "https://lichess.org/api"
TEAM_ID = os.environ.get("TEAM_ID", "chess-blasters-2")
TOKEN = os.environ["LICHESS_KEYS"]
headers = {"Authorization": f"Bearer {TOKEN}"}

def get_team_swisses(team_id):
    r = requests.get(f"{LICHESS_API}/team/{team_id}/swiss", headers=headers)
    r.raise_for_status()
    # Parse NDJSON (one JSON object per line)
    swisses = []
    for line in r.text.strip().split("\n"):
        if line:
            s = requests.models.json.loads(line)
            if not s.get("isFinished", True):
                swisses.append(s)
    return swisses

def join_tournament(swiss_id):
    requests.post(f"{LICHESS_API}/swiss/{swiss_id}/join", headers=headers)

def withdraw_tournament(swiss_id):
    requests.post(f"{LICHESS_API}/swiss/{swiss_id}/withdraw", headers=headers)

def main():
    now = datetime.now(timezone.utc)
    swisses = get_team_swisses(TEAM_ID)
    for s in swisses:
        swiss_id = s["id"]
        start_time = datetime.fromtimestamp(s["startsAt"] / 1000, tz=timezone.utc)
        mins_to_start = (start_time - now).total_seconds() / 60
        if mins_to_start > 8:
            join_tournament(swiss_id)
        elif 0 < mins_to_start <= 8:
            withdraw_tournament(swiss_id)

if __name__ == "__main__":
    main()
