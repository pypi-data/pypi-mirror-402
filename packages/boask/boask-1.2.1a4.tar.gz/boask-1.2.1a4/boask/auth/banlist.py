# banlist.py
from pathlib import Path

BANLIST_FILE = Path(__file__).parent / "banned_users.txt"

def load_banned_users() -> set:
    """Load banned usernames from the banlist file."""
    if not BANLIST_FILE.exists():
        return set()
    with open(BANLIST_FILE, "r", encoding="utf-8") as f:
        return set(line.strip() for line in f if line.strip())

def is_banned(username: str) -> bool:
    """Check if a username is banned."""
    banned_users = load_banned_users()
    return username in banned_users

def ban_user(username: str) -> None:
    """Add a username to the banlist file."""
    banned_users = load_banned_users()
    if username not in banned_users:
        with open(BANLIST_FILE, "a", encoding="utf-8") as f:
            f.write(username + "\n")
