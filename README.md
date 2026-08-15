# stockjournal
Journaling of Stock Trades

## Project overview

This repository contains small helpers to authenticate with the Fyers API and to fetch trades for a given date.

Key files

- [fetch_trades.py](fetch_trades.py#L1-L999): fetch trades (or orders) from Fyers and filter by date.
- [auth_fyers.py](auth_fyers.py#L1-L999): local OAuth helper — opens the authorize URL, captures the code, exchanges for tokens, and writes to `.env`.
- [fyers1.py](fyers1.py#L1-L200), [fyers2.py](fyers2.py#L1-L200), [fyers3.py](fyers3.py#L1-L200): example scripts showing how to use the Fyers SDK. They read credentials from environment variables when present.
- [.env.example](.env.example#L1-L20): sample environment variables to copy into `.env`.
- [requirements.txt](requirements.txt): Python dependencies.

Quickstart

1. Install dependencies:

```bash
pip install -r requirements.txt
```

2. Create a `.env` file by copying `.env.example` and fill in values:

```bash
copy .env.example .env  # Windows PowerShell
```

Edit `.env` and set at minimum:

- `FYERS_CLIENT_ID`
- `FYERS_CLIENT_SECRET`
- `FYERS_REDIRECT_URI` (must match the redirect URI registered in the Fyers Developer Console)

3. Obtain tokens (recommended):

```bash
python auth_fyers.py
```

The helper will open the authorization URL in your browser. If your local server cannot receive the callback you can paste the redirect URL when prompted. On success the helper writes `FYERS_ACCESS_TOKEN` and `FYERS_REFRESH_TOKEN` to `.env`.

4. Fetch trades for a date:

```bash
python fetch_trades.py --date 2026-08-14
```

Example: use the SDK directly

After you have an access token in `.env` you can run the example scripts (they read credentials from environment):

```bash
python fyers3.py
```

Security notes

- Never commit your `.env` to git. This repository includes a `.gitignore` that ignores `.env`.
- Treat `FYERS_CLIENT_SECRET`, `FYERS_ACCESS_TOKEN`, and `FYERS_REFRESH_TOKEN` as sensitive secrets.

Debugging tips

- If you see the 500 error `{"s":"error","code":500,"message":"Invalid Request, please provide valid method"}` in the browser, check that your authorize URL's `redirect_uri` exactly matches the registered redirect URI (scheme, host, port, and path). For local testing prefer `http://localhost:8080/callback`.
- If token exchange fails, run `python auth_fyers.py` and paste the printed token-endpoint response here for diagnosis.

PowerShell: decode JWT helper

Paste this into PowerShell to inspect JWT header/payload:

```powershell
function Decode-JWT {
     param([string]$Token)
     $Parts = $Token.Split('.')
     if ($Parts.Length -lt 2) { Write-Error "Invalid JWT format"; return }
     foreach ($Section in @('HEADER', 'PAYLOAD')) {
         $Idx = if ($Section -eq 'HEADER') { 0 } else { 1 }
         $Base64 = $Parts[$Idx].Replace('-','+').Replace('_','/')
         $Base64 = $Base64.PadRight($Base64.Length + (4 - $Base64.Length % 4) % 4, '=')
         Write-Host "--- $Section ---" -ForegroundColor Cyan
         [System.Text.Encoding]::UTF8.GetString([System.Convert]::FromBase64String($Base64)) | ConvertFrom-Json | Format-List
     }
}

# Usage: Decode-JWT $env:FYERS_ACCESS_TOKEN
```