import requests, os, time

TEAM_ID = "chess-blasters-2"
L_TOKEN = os.getenv("L_TOKEN")
T_TOKEN = os.getenv("T_TOKEN")

# your Lichess usernames (for identifying joins)
L_USERNAME = "raja1544"
T_USERNAME = "unrealboy9000"

def get_swiss_list():
    """Get all Swiss tournaments of the team that are created or started."""
    url = f"https://lichess.org/api/team/{TEAM_ID}/swiss"
    r = requests.get(url)
    if r.ok:
        data = r.json()
        return [s['id'] for s in data if s.get('status') in ['created', 'started']]
    print("Error fetching Swiss list:", r.status_code)
    return []

def get_players_text(swiss_id, token):
    """Get all players in a Swiss as plain text."""
    url = f"https://lichess.org/api/swiss/{swiss_id}/players"
    headers = {"Authorization": f"Bearer {token}"}
    r = requests.get(url, headers=headers)
    return r.text.lower() if r.ok else ""

def join_swiss(swiss_id, token):
    """Make account join a Swiss."""
    url = f"https://lichess.org/api/swiss/{swiss_id}/join"
    headers = {"Authorization": f"Bearer {token}"}
    r = requests.post(url, headers=headers)
    print(f"[{time.strftime('%H:%M:%S')}] Tried to join {swiss_id}: {r.status_code}")

def loop_check():
    """Continuously check every minute if L joined a Swiss, then auto join with T."""
    while True:
        swisses = get_swiss_list()
        if not swisses:
            print(f"[{time.strftime('%H:%M:%S')}] No Swiss found.")
        for sid in swisses:
            players_L = get_players_text(sid, L_TOKEN)
            if L_USERNAME in players_L:
                players_T = get_players_text(sid, T_TOKEN)
                if T_USERNAME not in players_T:
                    print(f"[+] {L_USERNAME} joined {sid}, {T_USERNAME} not joined — joining now.")
                    join_swiss(sid, T_TOKEN)
                else:
                    print(f"[=] Both already joined {sid}")
            else:
                print(f"[-] {L_USERNAME} not in {sid}")
        time.sleep(60)  # check every minute

if __name__ == "__main__":
    loop_check()
