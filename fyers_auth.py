from fyers_apiv3 import fyersModel
import webbrowser
import http.server
import time
import requests
import threading
import socketserver
import os
from dotenv import load_dotenv
import urllib
from typing import Dict, Any, Optional
import base64
import json
import datetime
import argparse
import sys

# Toggle verbose debug printing. Set in `main()` from env or CLI.
DEBUG = False

def debug_print(*args, **kwargs):
    if DEBUG:
        print(*args, **kwargs)

DEFAULT_PORT = 80
DEFAULT_PATH = "/callback"
FYERS_BASE = os.environ.get("FYERS_API_BASE", "https://api.fyers.in")

class CallbackHandler(http.server.BaseHTTPRequestHandler):
    server_version = "FyersAuth/0.1"

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        q = urllib.parse.parse_qs(parsed.query)
        # Always log the raw incoming request path so callbacks are visible
        print("Callback received:", self.path)

        # Ignore non-callback paths (favicon -> short no-content response)
        if parsed.path != DEFAULT_PATH:
            if parsed.path == "/favicon.ico":
                print("favicon Callback received. Ignoring", parsed.path)
                self.send_response(204)
                self.end_headers()
            else:
                print("Invalid Callback received. Ignoring", parsed.path)
                self.send_response(404)
                self.send_header("Content-Type", "text/html")
                self.end_headers()
                self.wfile.write(b"<html><body><h1>Not found</h1></body></html>")
            return

        code = q.get("auth_code", [None])[0]
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

def update_env_file(access_token: str, refresh_token: str, path: str) -> None:
    lines = []
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            lines = f.read().splitlines()
    out = []
    for line in lines:
        if not line or line.strip().startswith("#") or "=" not in line:
            out.append(line)
            continue
        k, _, v = line.partition("=")
        if k == "FYERS_ACCESS_TOKEN":
            out.append(f"{k}={access_token}")
        elif k == "FYERS_REFRESH_TOKEN":
            out.append(f"{k}={refresh_token}")
        else:
            out.append(line)
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(out) + "\n")

def run_local_server(port: int) -> socketserver.TCPServer:
    handler = CallbackHandler
    httpd = socketserver.TCPServer(("", port), handler)
    # attach a place to store the code
    httpd.auth_code = None
    return httpd


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
        debug_print("Attempting token exchange (form-encoded)...")
        debug_print("Request URL:", url)
        debug_print("Request data:", data)
        resp = requests.post(url, data=data, headers=headers, timeout=30)
        resp.raise_for_status()
        return resp.json()
    except Exception as ex_form:
        debug_print("Form-encoded token exchange failed:", ex_form)
        try:
            debug_print("Status:", resp.status_code)
            debug_print("Response body:", resp.text)
        except Exception:
            pass

    # Fallback: try JSON body
    try:
        debug_print("Attempting token exchange (JSON body)...")
        headers_json = {"Content-Type": "application/json", "Accept": "application/json"}
        resp2 = requests.post(url, json=data, headers=headers_json, timeout=30)
        resp2.raise_for_status()
        return resp2.json()
    except Exception as ex_json:
        debug_print("JSON token exchange failed:", ex_json)
        try:
            debug_print("Status:", resp2.status_code)
            debug_print("Response body:", resp2.text)
        except Exception:
            pass

    # Fallback: try Basic Auth with grant params in body
    try:
        debug_print("Attempting token exchange (Basic Auth fallback)...")
        from requests.auth import HTTPBasicAuth

        body = {"grant_type": "authorization_code", "code": code, "redirect_uri": redirect_uri}
        resp3 = requests.post(url, data=body, auth=HTTPBasicAuth(client_id, client_secret), headers={"Accept": "application/json"}, timeout=30)
        resp3.raise_for_status()
        return resp3.json()
    except Exception as ex_auth:
        debug_print("Basic Auth token exchange failed:", ex_auth)
        try:
            debug_print("Status:", resp3.status_code)
            debug_print("Response body:", resp3.text)
        except Exception:
            pass

    # All attempts failed; raise the last error
    raise RuntimeError("All token exchange attempts failed; see printed output for details")


def _decode_access_token_expiry(access_token: str) -> Optional[datetime.datetime]:
    """Decode JWT-like access token and return expiry as an aware datetime in IST.

    Returns None if the token doesn't contain an `exp` claim or cannot be decoded.
    """
    if not access_token or "." not in access_token:
        return None
    try:
        parts = access_token.split(".")
        payload_b64 = parts[1]
        # Add padding if necessary
        padding = "=" * (-len(payload_b64) % 4)
        payload_b64_padded = payload_b64 + padding
        payload_bytes = base64.urlsafe_b64decode(payload_b64_padded)
        payload = json.loads(payload_bytes.decode("utf-8"))
        exp = payload.get("exp")
        if exp is None:
            return None
        exp_int = int(exp)
        dt_utc = datetime.datetime.fromtimestamp(exp_int, tz=datetime.timezone.utc)
        ist = datetime.timezone(datetime.timedelta(hours=5, minutes=30), name="IST")
        return dt_utc.astimezone(ist)
    except Exception:
        return None


def main() -> None:
    """Generate an authcode URL and open it in the browser.

    Reads credentials from environment variables (or `.env` via python-dotenv):
      - FYERS_CLIENT_ID
      - FYERS_CLIENT_SECRET
      - FYERS_REDIRECT_URI
    """
    load_dotenv()
    # CLI arg parsing for debug mode
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--debug", action="store_true", help="Enable debug/verbose output")
    # parse known args only to avoid interfering with other callers
    args, _ = parser.parse_known_args()
    # Global DEBUG can also be enabled via FYERS_DEBUG env var (1/true/yes)
    global DEBUG
    env_debug = os.getenv("FYERS_DEBUG", "").lower() in ("1", "true", "yes")
    DEBUG = bool(args.debug) or env_debug

    # Read credentials from environment
    redirect_uri = os.getenv("FYERS_REDIRECT_URI", "https://localhost")
    client_id = os.getenv("FYERS_CLIENT_ID")
    secret_key = os.getenv("FYERS_CLIENT_SECRET")
    env_path = os.path.join(os.getcwd(), ".env")
    debug_print(f"Loaded .env from {env_path} (if it exists)")

    if not client_id or not secret_key:
        print("Please set FYERS_CLIENT_ID and FYERS_CLIENT_SECRET in your .env or environment.")
        return

    parsed = urllib.parse.urlparse(redirect_uri)

    port = parsed.port or DEFAULT_PORT

    grant_type = "authorization_code"
    response_type = "code"
    state = "sample"

    # Connect to the sessionModel object here with the required input parameters
    appSession = fyersModel.SessionModel(
        client_id=client_id,
        redirect_uri=redirect_uri,
        response_type=response_type,
        state=state,
        secret_key=secret_key,
        grant_type=grant_type,
    )

    # Make a request to generate_authcode object; this will return a login url
    generateTokenUrl = appSession.generate_authcode()


    debug_print(f"Starting local server on port {port} to receive the authorization code...")
    httpd = run_local_server(port)
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()

    # Print and open the URL in the default browser
    # Show the URL so the user can open it even when not in debug mode
    print(generateTokenUrl)
    try:
        webbrowser.open(generateTokenUrl, new=1)
    except Exception:
        print("Failed to open browser automatically. Paste the URL into your browser to continue.")

    debug_print("Waiting for authorization callback on local server...")
    # wait up to 300 seconds
    timeout = 300
    start = time.time()
    while time.time() - start < timeout and httpd.auth_code is None:
        time.sleep(0.5)

    code = httpd.auth_code
    debug_print(f"Received authorization code: {code}")
    httpd.shutdown()

    appSession.set_token(code)
    response = appSession.generate_token()

    # There can be two cases: successful token response or an error response.
    try:
        debug_print("Response:", response)
        access_token = response["access_token"]
        refresh_token = response["refresh_token"]
        debug_print("Access Token:", access_token)
        debug_print("Refresh Token:", refresh_token)

        # Persist tokens to .env
        update_env_file(access_token, refresh_token, env_path)

        # Try to decode access token expiry from token payload (JWT-like)
        expiry_dt = _decode_access_token_expiry(access_token)
        print(f"Access token expiry (IST): {expiry_dt.strftime('%Y-%m-%d %H:%M:%S %Z')}")

    except Exception as e:
        # Always print errors so failures are visible even when not debugging
        print(e, response)

if __name__ == "__main__":
    main()
