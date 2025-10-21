import requests
import os
import sys

def send_private_message(token, username, message):
    url = f"https://lichess.org/inbox/{username}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/x-www-form-urlencoded"
    }
    data = {"text": message}
    response = requests.post(url, headers=headers, data=data)

    if response.status_code == 200:
        print(f"✅ Message sent to {username}")
    else:
        print(f"❌ Failed to send message: {response.status_code} {response.text}")

if __name__ == "__main__":
    token = os.getenv("BR")
    if not token:
        print("Error: Lichess token not found in environment variable 'BR'")
        sys.exit(1)

    if len(sys.argv) < 2:
        print("Usage: python send_message.py <player_name>")
        sys.exit(1)

    username = sys.argv[1]

    with open("msg.txt", "r", encoding="utf-8") as f:
        message = f.read().strip()

    send_private_message(token, username, message)
