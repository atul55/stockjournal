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
- The script uses `FYERS_API_BASE` and `FYERS_TRADES_ENDPOINT` environment variables when provided.
- If the API response wraps items, the script will try common keys like `data`, `items`, `orders`, or `trades`.
- The script filters returned items by detecting common date fields such as `trade_date`, `date`, `timestamp`.

