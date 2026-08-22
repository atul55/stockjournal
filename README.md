# stockjournal

Journaling of Stock Trades

## Project overview

This repository contains helpers for authenticating with the Fyers API, calling Fyers APIs, and fetching trades for a given date.

Key files

- [fyers_auth.py](fyers_auth.py): generate the Fyers access and refresh tokens through the OAuth flow and update `.env`.
- [fyers_apis.py](fyers_apis.py): examples of Fyers user, transaction, order, position, and data API calls.
- [fyers_refresh.py](fyers_refresh.py): request a new access token with an existing refresh token.
- [fetch_trades.py](fetch_trades.py): fetch historical trades and filter them by date.
- [requirements.txt](requirements.txt): Python dependencies.

## Setup

Install the dependencies:

```bash
pip install -r requirements.txt
```

Create a `.env` file in the project directory with the values registered in the Fyers Developer Console:

```dotenv
FYERS_CLIENT_ID=your_client_id
FYERS_CLIENT_SECRET=your_client_secret
FYERS_REDIRECT_URI=http://localhost/callback
FYERS_ACCESS_TOKEN=
FYERS_REFRESH_TOKEN=
```

`FYERS_REDIRECT_URI` must exactly match the registered redirect URI, including the scheme, host, port, and path. The token entries should be present because `fyers_auth.py` updates their existing lines.

## Generate tokens

Use `fyers_auth.py` whenever a new authorization code and token pair is required:

```bash
python fyers_auth.py
```

The script opens the Fyers authorization page, listens for the `/callback` request, exchanges the authorization code, and writes `FYERS_ACCESS_TOKEN` and `FYERS_REFRESH_TOKEN` to `.env`. Use `--debug` for verbose token-exchange diagnostics.

## Fetch trades

After generating a token, fetch trades or orders for a date:

```bash
python fetch_trades.py --date 2026-08-14
```

The script reads `FYERS_ACCESS_TOKEN` from `.env` or the environment. You can also provide a token explicitly:

```bash
python fetch_trades.py --date 2026-08-14 --token your_access_token
```

The script uses the Fyers SDK `tradehistory` API with the requested date as both `from_date` and `to_date`, then filters the returned records locally as a safeguard. Override the client ID with `--client-id` when needed.

The output is a table with these columns:

```text
symbol | orderDateTime | trade_price | traded_qty
```

Rows are sorted by `traded_qty`, then `symbol`, then `orderDateTime`.

Use `--output trades.txt` to write the table to a file.

## Other scripts

Run [fyers_apis.py](fyers_apis.py) after a token has been generated to exercise the SDK examples. Review its sample order payloads before enabling order-placement calls. [fyers_refresh.py](fyers_refresh.py) is available for refresh-token based access-token renewal.

## Security notes

- Never commit `.env` to git; it is ignored by this repository.
- Treat `FYERS_CLIENT_SECRET`, `FYERS_ACCESS_TOKEN`, and `FYERS_REFRESH_TOKEN` as sensitive secrets.

## Troubleshooting

- If Fyers returns `Invalid Request, please provide valid method`, verify that `FYERS_REDIRECT_URI` exactly matches the value registered in the Fyers Developer Console.
- If the callback server cannot start, check that the redirect URI port is available and that the script has permission to bind to it.
- Run `python fyers_auth.py --debug` to print token-exchange diagnostics.

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