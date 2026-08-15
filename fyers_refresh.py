import os
import hashlib
import requests
from dotenv import load_dotenv

load_dotenv()

# Read credentials from .env (or environment)
client_id = os.getenv("FYERS_CLIENT_ID")
secret_key = os.getenv("FYERS_CLIENT_SECRET")
refresh_token = os.getenv("FYERS_REFRESH_TOKEN")
pin = os.getenv("FYERS_PIN")

if not client_id or not secret_key or not refresh_token:
    print("Missing credentials. Please set FYERS_CLIENT_ID, FYERS_CLIENT_SECRET, and FYERS_REFRESH_TOKEN in your .env")
    raise SystemExit(2)

appIdHash = hashlib.sha256(f"{client_id}:{secret_key}".encode("utf-8")).hexdigest()
url = "https://api-t1.fyers.in/api/v3/validate-refresh-token"
payload = {
    "grant_type": "refresh_token",
    "appIdHash": appIdHash,
    "refresh_token": refresh_token,
    "pin": "mypin"
}

# POST request to get new access_token
resp = requests.post(url, json=payload)
try:
    response = resp.json()
except Exception:
    print("Invalid JSON response from token endpoint. Status:", resp.status_code)
    print(resp.text)
    raise

if response.get("s") == "ok":
    print("New Access Token:", response.get("access_token"))
else:
    print("Error refreshing token:", response)
