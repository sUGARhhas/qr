import json
import os

VOLUNTEER_DATA_FILE = 'volunteer_data.json'
USER_IDS_FILE = 'user_ids.txt'

def load_volunteer_data():
    with open(VOLUNTEER_DATA_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def load_user_ids():
    if os.path.exists(USER_IDS_FILE):
        with open(USER_IDS_FILE, 'r') as f:
            return set(line.strip() for line in f)
    return set()

def save_user_ids(user_ids):
    with open(USER_IDS_FILE, 'w') as f:
        for user_id in sorted(user_ids):
            f.write(f"{user_id}\n") 