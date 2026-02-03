"""
Minimal token server for testing the voice agent.
Returns a LiveKit access token that dispatches the "simple-agent" when the user joins.
Run: python token_server.py
Then GET http://localhost:8090/token?room=my-room&identity=user1
"""
import json
import os
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse

from dotenv import load_dotenv
from livekit import api

load_dotenv()
load_dotenv(".env.local")  # from lk app env -w after lk cloud auth

LIVEKIT_URL = os.getenv("LIVEKIT_URL", "wss://localhost:7880")
AGENT_NAME = "simple-agent"


def create_token(room: str, identity: str) -> tuple[str, str]:
    """Create a token that dispatches simple-agent when the user joins the room."""
    token = (
        api.AccessToken()
        .with_identity(identity)
        .with_grants(api.VideoGrants(room_join=True, room=room))
        .with_room_config(
            api.RoomConfiguration(
                agents=[api.RoomAgentDispatch(agent_name=AGENT_NAME)],
            ),
        )
        .to_jwt()
    )
    return token, LIVEKIT_URL


class TokenHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path != "/token":
            self.send_error(404)
            return
        params = parse_qs(parsed.query)
        room = (params.get("room") or ["my-room"])[0]
        identity = (params.get("identity") or ["user1"])[0]
        try:
            token, url = create_token(room, identity)
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(
                json.dumps({"token": token, "url": url}).encode("utf-8")
            )
        except Exception as e:
            self.send_response(500)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(
                json.dumps({"error": str(e)}).encode("utf-8")
            )

    def log_message(self, format, *args):
        print(f"[token_server] {args[0]}")


def main():
    port = int(os.getenv("PORT", "8090"))
    server = HTTPServer(("", port), TokenHandler)
    print(f"Token server: http://localhost:{port}/token?room=my-room&identity=user1")
    server.serve_forever()


if __name__ == "__main__":
    main()
