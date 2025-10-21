import requests
import os
import sys
import time

def kick_member(token, team_id, username):
    url = f"https://lichess.org/team/{team_id}/kick/{username}"
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.post(url, headers=headers)
    
    if response.status_code == 200:
        print(f"✅ Kicked {username} from team {team_id}")
    else:
        print(f"❌ Failed to kick {username}: {response.status_code} {response.text}")

if __name__ == "__main__":
    token = os.getenv("BR")
    if not token:
        print("Error: Lichess token not found in 'BR'")
        sys.exit(1)

    if len(sys.argv) < 2:
        print("Usage: python kick_members.py <team_id>")
        sys.exit(1)

    team_id = sys.argv[1]

    try:
        with open("kick.txt", "r", encoding="utf-8") as f:
            members = [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        print("kick.txt not found.")
        sys.exit(1)

    if not members:
        print("No usernames found in kick.txt.")
        sys.exit(0)

    for username in members:
        kick_member(token, team_id, username)
        time.sleep(1)  # polite delay to avoid rate limit
