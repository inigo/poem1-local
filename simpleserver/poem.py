#!/usr/bin/env python3

from http.server import BaseHTTPRequestHandler, HTTPServer
from datetime import datetime
import json
import ssl

PREFIX = "/api/v1/clock"

class Handler(BaseHTTPRequestHandler):
    def do_POST(self):
        print(f"\n{self.command} {self.path} {self.request_version}")
        for k, v in self.headers.items():
            print(f"{k}: {v}")

        if self.path == f"{PREFIX}/status":
            self.send_json({
                "success": True,
                "device": {
                    "screenId": "64D12990A994",
                    "buildId": "abc123",
                    "lastSeen": "2025-01-03T16:49:10Z",
                    "seen": 2,
                    "createdAt": "2025-01-03T12:00:00Z",
                    "isClaimed": True,
                },
            })

        elif self.path == f"{PREFIX}/compose":
            time24 = datetime.now().strftime("%H:%M")
            self.send_json({
                "poemId": "123456",
                "time24": time24,
                "poem": f"The poem text / Two lines at {time24}",
                "screensaver": False,
                "debug": {},
            })

    do_GET = do_POST

    def send_json(self, payload):
        body = json.dumps(payload).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

server = HTTPServer(("0.0.0.0", 443), Handler)

context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
context.load_cert_chain(certfile="cert.pem", keyfile="key.pem")
server.socket = context.wrap_socket(server.socket, server_side=True)

server.serve_forever()
