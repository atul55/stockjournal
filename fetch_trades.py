#!/usr/bin/env python3
"""Fetch trades from Fyers API for a specific date.

Usage:
  python fetch_trades.py --date 2026-08-14

Requirements: set `FYERS_ACCESS_TOKEN` in environment or use --token.
"""
from __future__ import annotations

import argparse
import datetime
import json
import os
import sys
from typing import Any, Dict, List, Optional

import requests


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Fetch trades from Fyers API for a given date")
    p.add_argument("--date", required=True, help="Date in YYYY-MM-DD format to fetch trades for")
    p.add_argument("--base", default=os.environ.get("FYERS_API_BASE", "https://api.fyers.in"),
                   help="Fyers API base URL (env FYERS_API_BASE)")
    p.add_argument("--endpoint", default=os.environ.get("FYERS_TRADES_ENDPOINT", "/api/v2/orders"),
                   help="API endpoint path to fetch trades/orders (env FYERS_TRADES_ENDPOINT)")
    p.add_argument("--token", default=os.environ.get("FYERS_ACCESS_TOKEN"),
                   help="Fyers access token (env FYERS_ACCESS_TOKEN)")
    p.add_argument("--output", help="Write JSON output to file instead of stdout")
    return p.parse_args()


def iso_date_from_value(val: Any) -> Optional[datetime.date]:
    """Try to extract a date from common value types returned by APIs."""
    if val is None:
        return None
    # If it's an epoch timestamp (seconds or milliseconds)
    if isinstance(val, (int, float)):
        # Heuristic: if >1e12 treat as milliseconds
        ts = float(val) / 1000.0 if val > 1e12 else float(val)
        try:
            return datetime.datetime.fromtimestamp(ts).date()
        except Exception:
            return None
    # If it's a string, try common ISO formats
    if isinstance(val, str):
        for fmt in ("%Y-%m-%d", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S", "%d-%m-%Y"):
            try:
                return datetime.datetime.strptime(val.split("+")[0], fmt).date()
            except Exception:
                continue
        # Try to parse just the date substring
        try:
            return datetime.date.fromisoformat(val[:10])
        except Exception:
            return None
    return None


def extract_items(data: Any) -> List[Dict[str, Any]]:
    """Normalize response to a list of items to inspect for date fields."""
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        # Common wrappers
        for key in ("data", "items", "orders", "trades", "result"):
            if key in data and isinstance(data[key], list):
                return data[key]
        # If dict values are list-like, try to pick the first list
        for v in data.values():
            if isinstance(v, list):
                return v
    return []


def get_trades(base: str, endpoint: str, token: str, params: Optional[Dict[str, Any]] = None) -> Any:
    url = base.rstrip("/") + (endpoint if endpoint.startswith("/") else f"/{endpoint}")
    headers = {"Authorization": f"Bearer {token}", "Accept": "application/json"}
    resp = requests.get(url, headers=headers, params=params or {}, timeout=30)
    resp.raise_for_status()
    return resp.json()


def filter_by_date(items: List[Dict[str, Any]], target: datetime.date) -> List[Dict[str, Any]]:
    keys_to_check = ("trade_date", "date", "created_at", "timestamp", "time")
    out = []
    for it in items:
        found = None
        if not isinstance(it, dict):
            continue
        for k in keys_to_check:
            if k in it:
                d = iso_date_from_value(it[k])
                if d:
                    found = d
                    break
        # fallback: search all string/int fields
        if found is None:
            for v in it.values():
                d = iso_date_from_value(v)
                if d:
                    found = d
                    break
        if found == target:
            out.append(it)
    return out


def main() -> int:
    args = parse_args()
    if not args.token:
        print("Missing Fyers access token. Set FYERS_ACCESS_TOKEN or pass --token", file=sys.stderr)
        return 2
    try:
        target_date = datetime.datetime.strptime(args.date, "%Y-%m-%d").date()
    except Exception:
        print("Date must be in YYYY-MM-DD format", file=sys.stderr)
        return 2

    try:
        resp = get_trades(args.base, args.endpoint, args.token)
    except requests.HTTPError as e:
        print(f"HTTP error: {e}", file=sys.stderr)
        return 3
    except Exception as e:
        print(f"Error fetching trades: {e}", file=sys.stderr)
        return 3

    items = extract_items(resp)
    filtered = filter_by_date(items, target_date)

    out_json = json.dumps(filtered, indent=2, default=str)
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(out_json)
    else:
        print(out_json)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
