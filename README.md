# stockjournal
Journaling of Stock Trades

## Fyers trades fetcher

A small script to call the Fyers API and fetch trades for a specific date.

Files added:
- [fetch_trades.py](fetch_trades.py#L1-L999)
- [.env.example](.env.example)
- [requirements.txt](requirements.txt)

Quickstart

1. Install dependencies:

```bash
pip install -r requirements.txt
```

2. Set your access token (export or copy `.env.example` to `.env`):

Linux/macOS

```bash
export FYERS_ACCESS_TOKEN="your_token_here"
```

Windows (PowerShell)

```powershell
$env:FYERS_ACCESS_TOKEN = "your_token_here"
```

3. Run the script for a date (YYYY-MM-DD):

```bash
python fetch_trades.py --date 2026-08-14
```

Notes

Getting tokens automatically

1. Populate your `.env` (or copy `.env.example`) with `FYERS_CLIENT_ID` and `FYERS_CLIENT_SECRET` and set `FYERS_REDIRECT_URI` to the redirect URI you registered.

2. Run the OAuth helper which opens a browser, captures the authorization code, exchanges it for tokens, and writes them to `.env`:

```bash
python auth_fyers.py
```

3. After success, `FYERS_ACCESS_TOKEN` and `FYERS_REFRESH_TOKEN` will be written to `.env`. Then run the fetcher:

```bash
python fetch_trades.py --date 2026-08-14
```

If your registered redirect URI is not `http://localhost:8080/callback`, update `FYERS_REDIRECT_URI` accordingly and make sure your Developer Console entry matches the value exactly.

