#!/usr/bin/env python3
"""Fetch trades from Fyers API for a specific date.

Usage:
  python fetch_trades.py --date 2026-08-14

Requirements: set `FYERS_CLIENT_ID` and `FYERS_ACCESS_TOKEN` in `.env` or use the command-line options.
"""
from __future__ import annotations

import argparse
import csv
import datetime
import os
import sys
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv
from fyers_apiv3 import fyersModel


def parse_args() -> argparse.Namespace:
    load_dotenv()
    p = argparse.ArgumentParser(description="Fetch trades from Fyers API for a given date")
    p.add_argument("--date", required=True, help="Date in YYYY-MM-DD format to fetch trades for")
    p.add_argument("--client-id", default=os.environ.get("FYERS_CLIENT_ID"),
                   help="Fyers client ID (env FYERS_CLIENT_ID)")
    p.add_argument("--token", default=os.environ.get("FYERS_ACCESS_TOKEN"),
                   help="Fyers access token (env FYERS_ACCESS_TOKEN)")
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
        for fmt in ("%Y-%m-%d", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S",
                "%d-%m-%Y", "%d-%b-%Y %H:%M:%S"):
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
        for key in ("data", "items", "orders", "trades", "tradeBook", "tradeHistory", "result"):
            if key in data and isinstance(data[key], list):
                return data[key]
        # If dict values are list-like, try to pick the first list
        for v in data.values():
            if isinstance(v, list):
                return v
    return []


def get_trades(client_id: str, token: str, target_date: datetime.date) -> Any:
    fyers = fyersModel.FyersModel(
        token=token,
        is_async=False,
        client_id=client_id,
        log_path="",
    )
    response = fyers.tradehistory({
        "symbol": "",
        "from_date": target_date.isoformat(),
        "to_date": target_date.isoformat(),
        "page_no": 1,
        "page_size": 100,
        "segment_type": "0",
        "exchange_type": "0",
    })
    if isinstance(response, dict) and response.get("s") == "error":
        code = response.get("code", "unknown")
        message = response.get("message", "Fyers API request failed")
        raise RuntimeError(f"Fyers API error ({code}): {message}")
    return response


def filter_by_date(items: List[Dict[str, Any]], target: datetime.date) -> List[Dict[str, Any]]:
    keys_to_check = ("trade_date", "date", "created_at", "timestamp", "time", "orderDateTime")
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


def sort_items(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Sort trades by quantity, symbol, and order time."""
    return sorted(
        items,
        key=lambda item: (
            item.get("traded_qty", 0),
            str(item.get("symbol", "")).casefold(),
            datetime.datetime.strptime(
                str(item.get("orderDateTime", "")), "%d-%b-%Y %H:%M:%S"
            ) if item.get("orderDateTime") else datetime.datetime.max,
        ),
    )


def write_csv(items: List[Dict[str, Any]]) -> None:
    columns = ("symbol", "orderDateTime", "trade_price", "traded_qty")
    writer = csv.DictWriter(sys.stdout, fieldnames=columns, extrasaction="ignore",
                            lineterminator="\n")
    writer.writeheader()
    writer.writerows({column: item.get(column, "") for column in columns}
                     for item in sort_items(items))


def main() -> int:
    args = parse_args()
    if not args.client_id:
        print("Missing Fyers client ID. Set FYERS_CLIENT_ID or pass --client-id", file=sys.stderr)
        return 2
    if not args.token:
        print("Missing Fyers access token. Set FYERS_ACCESS_TOKEN or pass --token", file=sys.stderr)
        return 2
    try:
        target_date = datetime.datetime.strptime(args.date, "%Y-%m-%d").date()
    except Exception:
        print("Date must be in YYYY-MM-DD format", file=sys.stderr)
        return 2

    try:
        resp = get_trades(args.client_id, args.token, target_date)
    except Exception as e:
        print(f"Error fetching trades: {e}", file=sys.stderr)
        return 3

    items = extract_items(resp)
    filtered = filter_by_date(items, target_date)

    write_csv(filtered)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
