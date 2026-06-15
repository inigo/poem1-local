#!/usr/bin/env python3
"""
Poem clock server that serves poems via HTTPS.

Configuration
-------------
Create a file named ``poem_server.conf`` in the same directory as this script
(i.e. alongside poem.py).  The file uses INI format with a [poem_server] section:

    [poem_server]
    token = <your poem.town API token>
    screen_id = <your screen ID>

See ``poem_server.conf.example`` for a ready-to-fill template.
The server refuses to start if the config file is absent or either value is missing.
"""

import configparser
from http.server import BaseHTTPRequestHandler, HTTPServer
from datetime import datetime
from pathlib import Path
import argparse
import json
import random
import ssl
import sys
import urllib.request

sys.path.insert(0, str(Path(__file__).parent.parent))
from datacreate.database import find_poems, find_poems_matching_any_tag

PREFIX = "/api/v1/clock"
POEM_TOWN_URL = "https://poem.town/api/v1/clock/compose"

_CONFIG_FILE = Path(__file__).parent / "poem_server.conf"

def _load_config() -> tuple[str, str]:
    if not _CONFIG_FILE.exists():
        sys.exit(
            f"Config file not found: {_CONFIG_FILE}\n"
            "Copy poem_server.conf.example to poem_server.conf and fill in your values."
        )
    cfg = configparser.ConfigParser()
    cfg.read(_CONFIG_FILE)
    try:
        token = cfg["poem_server"]["token"]
        screen_id = cfg["poem_server"]["screen_id"]
    except KeyError as exc:
        sys.exit(f"Missing required key in {_CONFIG_FILE}: {exc}")
    if not token or not screen_id:
        sys.exit(f"'token' and 'screen_id' must both be set in {_CONFIG_FILE}")
    return token, screen_id

POEM_TOWN_TOKEN, SCREEN_ID = _load_config()

active_tags: list[str] = []


class Handler(BaseHTTPRequestHandler):
    def do_POST(self):
        print(f"\n{self.command} {self.path} {self.request_version}")
        for k, v in self.headers.items():
            print(f"{k}: {v}")

        if self.path == f"{PREFIX}/status":
            self.send_json({
                "success": True,
                "device": {
                    "screenId": SCREEN_ID,
                    "buildId": "abc123",
                    "lastSeen": "2025-01-03T16:49:10Z",
                    "seen": 2,
                    "createdAt": "2025-01-03T12:00:00Z",
                    "isClaimed": True,
                },
            })

        elif self.path == f"{PREFIX}/compose":
            time24 = datetime.now().strftime("%H:%M")
            self.send_json(self._compose(time24))

    do_GET = do_POST

    def _compose(self, time24: str) -> dict:
        if active_tags:
            rows = find_poems_matching_any_tag(time24, active_tags)
            if rows:
                return self._format_local(random.choice(rows), time24)

        rows = find_poems(time_str=time24)
        if rows:
            return self._format_local(random.choice(rows), time24)

        return self._fetch_poem_town(time24)

    def _format_local(self, row, time24: str) -> dict:
        return {
            "poemId": str(row["id"]),
            "time24": time24,
            "poem": row["poem"],
            "debug": {"source": "local"},
        }

    def _fetch_poem_town(self, time24: str) -> dict:
        payload = json.dumps({"screenId": SCREEN_ID, "time24": time24}).encode("utf-8")
        req = urllib.request.Request(
            POEM_TOWN_URL,
            data=payload,
            headers={
                "Authorization": f"Bearer {POEM_TOWN_TOKEN}",
                "Content-Type": "application/json",
            },
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read())

    def send_json(self, payload):
        body = json.dumps(payload).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def main():
    global active_tags
    parser = argparse.ArgumentParser(description="Poem clock server")
    parser.add_argument("tags", nargs="*", help="Active condition tags (e.g. rainy windy)")
    args = parser.parse_args()
    active_tags = [t.strip().lower() for t in args.tags]
    if active_tags:
        print(f"Active tags: {active_tags}")

    server = HTTPServer(("0.0.0.0", 443), Handler)
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.load_cert_chain(certfile="cert.pem", keyfile="key.pem")
    server.socket = context.wrap_socket(server.socket, server_side=True)
    server.serve_forever()


if __name__ == "__main__":
    main()
