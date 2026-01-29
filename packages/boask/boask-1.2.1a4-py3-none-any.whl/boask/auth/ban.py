from .users import USERS, verify_password, create_token
from .banlist import is_banned
from pathlib import Path
import urllib.parse
class Ban:
    @staticmethod
    def ban_user(handler):
        banlist_path = Path(__file__).parent / "banned_users.txt"
        if not banlist_path.exists():
            banlist_path.touch()
        if handler.command != "POST":
            handler.send_response(405)
            handler.end_headers()
            return b"Method Not Allowed"

        length = int(handler.headers.get("Content-Length", 0))
        body = handler.rfile.read(length).decode("utf-8")

        data = urllib.parse.parse_qs(body)
        username = data.get("username", [None])[0]
        password = data.get("password", [None])[0]

        if not username or not password:
            handler.send_response(400)
            handler.end_headers()
            return b"Missing credentials"

        if is_banned(username):
            handler.send_response(403)
            handler.end_headers()
            return b"User is banned"

        if username not in USERS:
            handler.send_response(401)
            handler.end_headers()
            return b"Invalid credentials"

        if not verify_password(password, USERS[username]):
            handler.send_response(401)
            handler.end_headers()
            return b"Invalid credentials"

        token = create_token(username)

        handler.send_response(200)
        handler.send_header("Content-Type", "application/json")
        handler.end_headers()

        return f'{{"token": "{token}"}}'.encode("utf-8")