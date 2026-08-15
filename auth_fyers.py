#!/usr/bin/env python3
"""OAuth helper to obtain Fyers access and refresh tokens.

Usage:
  python auth_fyers.py

It will open the authorization URL in your browser and run a local HTTP server
to capture the authorization code, exchange it for tokens, and write them to
the local `.env` file.
"""
from __future__ import annotations

import http.server
import json
import os
import socketserver
import threading
import time
import urllib.parse
import webbrowser
from typing import Dict, Optional

import requests
from dotenv import load_dotenv


DEFAULT_PORT = 8080
DEFAULT_PATH = "/callback"
FYERS_BASE = os.environ.get("FYERS_API_BASE", "https://api.fyers.in")


def load_config() -> Dict[str, Optional[str]]:
    load_dotenv()
    return {
        "client_id": os.environ.get("FYERS_CLIENT_ID"),
        "client_secret": os.environ.get("FYERS_CLIENT_SECRET"),
        "redirect_uri": os.environ.get("FYERS_REDIRECT_URI", f"http://localhost:{DEFAULT_PORT}{DEFAULT_PATH}"),
        "env_path": os.path.join(os.getcwd(), ".env"),
    }


def update_env_file(path: str, kv: Dict[str, str]) -> None:
    lines = []
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            lines = f.read().splitlines()
    out = []
    keys = set(kv.keys())
    for line in lines:
        if not line or line.strip().startswith("#") or "=" not in line:
            out.append(line)
            continue
        k, _, v = line.partition("=")
        if k in kv:
            out.append(f"{k}={kv[k]}")
            keys.discard(k)
        else:
            out.append(line)
    for k in keys:
        out.append(f"{k}={kv[k]}")
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(out) + "\n")


class CallbackHandler(http.server.BaseHTTPRequestHandler):
    server_version = "FyersAuth/0.1"

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        q = urllib.parse.parse_qs(parsed.query)
        code = q.get("code", [None])[0]
        state = q.get("state", [None])[0]
        self.server.auth_code = code
        # Respond to browser
        self.send_response(200)
        self.send_header("Content-Type", "text/html")
        self.end_headers()
        if code:
            self.wfile.write(b"<html><body><h1>Authorization received</h1><p>You can close this window.</p></body></html>")
        else:
            self.wfile.write(b"<html><body><h1>Missing code</h1><p>Check the query parameters.</p></body></html>")

    def log_message(self, format, *args):
        # Silence default logging
        return


def run_local_server(port: int) -> socketserver.TCPServer:
    handler = CallbackHandler
    httpd = socketserver.TCPServer(("", port), handler)
    # attach a place to store the code
    httpd.auth_code = None
    return httpd


def build_authorize_url(client_id: str, redirect_uri: str) -> str:
    params = {
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "state": "state",
    }
    # Use urlencode to properly encode values, but some environments expect
    # the redirect_uri to be exact as-registered. Keep the value encoded
    # while still making it easy to debug if a mismatch occurs.
    return f"{FYERS_BASE.rstrip('/')}/api/v2/authorize?{urllib.parse.urlencode(params)}"


def exchange_code_for_tokens(code: str, client_id: str, client_secret: str, redirect_uri: str) -> Dict[str, str]:
    url = f"{FYERS_BASE.rstrip('/')}/api/v2/token"
    data = {
        "grant_type": "authorization_code",
        "code": code,
        "client_id": client_id,
        "client_secret": client_secret,
        "redirect_uri": redirect_uri,
    }
    # Try form-encoded first (typical)
    headers = {"Content-Type": "application/x-www-form-urlencoded", "Accept": "application/json"}
    try:
        print("Attempting token exchange (form-encoded)...")
        print("Request URL:", url)
        print("Request data:", data)
        resp = requests.post(url, data=data, headers=headers, timeout=30)
        resp.raise_for_status()
        return resp.json()
    except Exception as ex_form:
        print("Form-encoded token exchange failed:", ex_form)
        try:
            print("Status:", resp.status_code)
            print("Response body:", resp.text)
        except Exception:
            pass

    # Fallback: try JSON body
    try:
        print("Attempting token exchange (JSON body)...")
        headers_json = {"Content-Type": "application/json", "Accept": "application/json"}
        resp2 = requests.post(url, json=data, headers=headers_json, timeout=30)
        resp2.raise_for_status()
        return resp2.json()
    except Exception as ex_json:
        print("JSON token exchange failed:", ex_json)
        try:
            print("Status:", resp2.status_code)
            print("Response body:", resp2.text)
        except Exception:
            pass

    # Fallback: try Basic Auth with grant params in body
    try:
        print("Attempting token exchange (Basic Auth fallback)...")
        from requests.auth import HTTPBasicAuth

        body = {"grant_type": "authorization_code", "code": code, "redirect_uri": redirect_uri}
        resp3 = requests.post(url, data=body, auth=HTTPBasicAuth(client_id, client_secret), headers={"Accept": "application/json"}, timeout=30)
        resp3.raise_for_status()
        return resp3.json()
    except Exception as ex_auth:
        print("Basic Auth token exchange failed:", ex_auth)
        try:
            print("Status:", resp3.status_code)
            print("Response body:", resp3.text)
        except Exception:
            pass

    # All attempts failed; raise the last error
    raise RuntimeError("All token exchange attempts failed; see printed output for details")


def main() -> int:
    cfg = load_config()
    client_id = cfg.get("client_id")
    client_secret = cfg.get("client_secret")
    redirect_uri = cfg.get("redirect_uri")
    env_path = cfg.get("env_path")

    if not client_id or not client_secret:
        print("Please set FYERS_CLIENT_ID and FYERS_CLIENT_SECRET in your .env before running.")
        return 2

    parsed = urllib.parse.urlparse(redirect_uri)
    port = parsed.port or DEFAULT_PORT

    auth_url = build_authorize_url(client_id, redirect_uri)
    print("Opening browser for authorization. If it fails, open this URL manually:")
    print(auth_url)

    httpd = run_local_server(port)
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()

    try:
        webbrowser.open(auth_url)
    except Exception:
        pass

    print("Waiting for authorization callback on local server...")
    # wait up to 300 seconds
    timeout = 300
    start = time.time()
    while time.time() - start < timeout and httpd.auth_code is None:
        time.sleep(0.5)

    code = httpd.auth_code
    httpd.shutdown()

    if not code:
        print("Did not receive authorization code via local callback.")
        print("If your redirect URI uses HTTPS or a different host/port, the local server may not be reachable.")
        print("You can paste the full redirect URL you were sent after authorizing (the browser address bar).")
        try:
            redirect_input = input("Paste full redirect URL (or just the 'code' value), or press Enter to abort: ").strip()
        except Exception:
            redirect_input = ""
        if not redirect_input:
            print("No input provided. Aborting.")
            return 3
        # Extract code from pasted URL or raw code
        if "code=" in redirect_input:
            q = urllib.parse.urlparse(redirect_input).query
            params = urllib.parse.parse_qs(q)
            code = params.get("code", [None])[0]
        else:
            code = redirect_input
        if not code:
            print("Could not extract code from input. Aborting.")
            return 3

    print("Exchanging code for tokens...")
    try:
        token_resp = exchange_code_for_tokens(code, client_id, client_secret, redirect_uri)
    except Exception as e:
        print(f"Token exchange failed: {e}")
        return 4

    # Save relevant keys to .env
    kv = {}
    for k in ("access_token", "refresh_token", "expires_in", "token_type"):
        if k in token_resp:
            kv_key = "FYERS_" + k.upper()
            kv[kv_key] = str(token_resp[k])

    # Also store client id/secret and redirect_uri if not present
    kv.setdefault("FYERS_CLIENT_ID", client_id)
    kv.setdefault("FYERS_CLIENT_SECRET", client_secret)
    kv.setdefault("FYERS_REDIRECT_URI", redirect_uri)

    update_env_file(env_path, kv)
    print(f"Tokens stored to {env_path}")
    print("Done.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
