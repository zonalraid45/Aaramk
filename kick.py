import requests
import os
import sys
import time

def kick_member(token, team_id, username):
    # ✅ Correct API endpoint:
    url = f"https://lichess.org/api/team/{team_id}/kick/{username}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json"
    }
    response = requests.post(url, headers=headers)

    if response.status_code == 200:
        print(f"✅ Kicked {username} from {team_id}")
    elif response.status_code == 403:
        print(f"🚫 Token not authorized to manage {team_id}")
    elif response.status_code == 404:
        print(f"⚠️ User {username} not found in team {team_id}")
    else:
        print(f"❌ Failed to kick {username}: {response.status_code}\n{response.text}")

if __name__ == "__main__":
    token = os.getenv("BR")
    if not token:
        print("Error: Missing BR token environment variable.")
        sys.exit(1)

    if len(sys.argv) < 2:
        ]


