#!/usr/bin/env python3
"""Functional POC web server (Python standard library only).

Serves a simple login experience backed by SQLite, with real enforcement and a
real audit log:
  * sign in as a hypothetical attorney -> see only your documents
  * try to open another matter's document -> denied and recorded
  * sign in as admin -> see which users accessed which files

Run:
    python3 poc/seed.py
    python3 poc/server.py            # http://localhost:8000
"""
import json
import pathlib
import secrets
import sqlite3
import urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import access

ROOT = pathlib.Path(__file__).resolve().parent
DB_PATH = ROOT / "db" / "poc.db"
WEB = ROOT / "web"
SESSIONS = {}


class Handler(BaseHTTPRequestHandler):
    server_version = "SnowCompliancePOC/0.1"

    def log_message(self, *a):
        pass

    def _send(self, code, body, ctype="application/json"):
        data = body if isinstance(body, bytes) else json.dumps(body).encode()
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(data)

    def _user(self):
        auth = self.headers.get("Authorization", "")
        token = auth[7:] if auth.startswith("Bearer ") else None
        return SESSIONS.get(token)

    def _read_json(self):
        n = int(self.headers.get("Content-Length", 0))
        return json.loads(self.rfile.read(n) or b"{}")

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        qs = urllib.parse.parse_qs(parsed.query)
        if path in ("/", "/index.html"):
            return self._serve_file(WEB / "index.html")
        if path in ("/app.js", "/styles.css"):
            return self._serve_file(WEB / path.lstrip("/"))
        if path == "/api/documents":
            user = self._user()
            if not user:
                return self._send(401, {"error": "not authenticated"})
            con = access.connect(DB_PATH)
            try:
                return self._send(200, {"documents": access.list_documents(con, user)})
            finally:
                con.close()
        if path == "/api/document":
            user = self._user()
            if not user:
                return self._send(401, {"error": "not authenticated"})
            con = access.connect(DB_PATH)
            try:
                doc = access.get_document(con, user, qs.get("id", [""])[0])
                return self._send(200, doc)
            except access.Denied as e:
                return self._send(403, {"error": str(e)})
            finally:
                con.close()
        if path == "/api/audit":
            user = self._user()
            if not user:
                return self._send(401, {"error": "not authenticated"})
            con = access.connect(DB_PATH)
            try:
                return self._send(200, {"audit": access.get_audit(con, user)})
            except access.Denied as e:
                return self._send(403, {"error": str(e)})
            finally:
                con.close()
        return self._send(404, {"error": "not found"})

    def do_POST(self):
        path = urllib.parse.urlparse(self.path).path
        if path == "/api/login":
            body = self._read_json()
            con = access.connect(DB_PATH)
            try:
                user = access.authenticate(con, body.get("username", ""), body.get("password", ""))
            finally:
                con.close()
            if not user:
                return self._send(401, {"error": "invalid credentials"})
            token = secrets.token_urlsafe(24)
            SESSIONS[token] = user
            return self._send(200, {"token": token, "user": user})
        if path == "/api/logout":
            auth = self.headers.get("Authorization", "")
            SESSIONS.pop(auth[7:] if auth.startswith("Bearer ") else None, None)
            return self._send(200, {"ok": True})
        return self._send(404, {"error": "not found"})

    def _serve_file(self, p: pathlib.Path):
        if not p.exists():
            return self._send(404, {"error": "not found"})
        ctype = "text/html" if p.suffix == ".html" else "text/javascript" if p.suffix == ".js" else "text/css"
        self._send(200, p.read_bytes(), ctype)


def main():
    if not DB_PATH.exists():
        raise SystemExit("poc.db missing; run: python3 poc/seed.py")
    httpd = ThreadingHTTPServer(("127.0.0.1", 8000), Handler)
    print("POC server running at http://localhost:8000  (users: alice, bob, carol, admin / password: demo)")
    httpd.serve_forever()


if __name__ == "__main__":
    main()
