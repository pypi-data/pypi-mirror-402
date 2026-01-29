import json
from pathlib import Path
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
import datetime
import secrets

USERS_FILE = Path("users.json")
BANLIST_FILE = Path("banned_users.txt")
SECRET_FILE = Path("secret.key")

if SECRET_FILE.exists():
    SECRET_KEY = SECRET_FILE.read_text().strip()
else:
    SECRET_KEY = secrets.token_hex(32)
    SECRET_FILE.write_text(SECRET_KEY)

def load_users():
    if not USERS_FILE.exists():
        return {}
    with open(USERS_FILE, "r") as f:
        return json.load(f)

def save_users(users):
    with open(USERS_FILE, "w") as f:
        json.dump(users, f)

def load_banlist():
    if not BANLIST_FILE.exists():
        BANLIST_FILE.touch()
        return set()
    with open(BANLIST_FILE, "r") as f:
        return set(line.strip() for line in f if line.strip())

def ban_user(username):
    banned = load_banlist()
    if username not in banned:
        with open(BANLIST_FILE, "a") as f:
            f.write(username + "\n")

def register_user(username, password, role="user"):
    users = load_users()
    if username in users:
        return False
    users[username] = {
        "password": generate_password_hash(password),
        "role": role
    }
    save_users(users)
    return True

def verify_password(username, password):
    users = load_users()
    if username not in users:
        return False
    return check_password_hash(users[username]["password"], password)

def create_token(username, expire_minutes=60):
    payload = {
        "sub": username,
        "exp": datetime.datetime.utcnow() + datetime.timedelta(minutes=expire_minutes)
    }
    return jwt.encode(payload, SECRET_KEY, algorithm="HS256")

def verify_token(token):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return payload["sub"]
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None
