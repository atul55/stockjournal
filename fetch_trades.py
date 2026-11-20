#!/usr/bin/env python3
"""Fetch trades from Fyers API for a specific date.

Usage:
  python fetch_trades.py --date 2026-08-14

Requirements: set `FYERS_CLIENT_ID` and `FYERS_ACCESS_TOKEN` in `.env` or use the command-line options.
"""
from __future__ import annotations

import argparse
import calendar
import csv
import datetime
import os
import re
import sys
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv
from fyers_apiv3 import fyersModel

COLUMNS = (
    "option_contract",
    "side",
    "trade_price",
    "",
    "orderDateTime",
    "",
    "",
    "",
    "traded_qty",
    "symbol",
)
OPTION_SYMBOL_RE = re.compile(
    r"^(?P<underlying>[A-Z]+?)(?P<year>\d{2})"
    r"(?P<month>1[0-2]|0?[1-9]|[OND])"
    r"(?P<day>0[1-9]|[12]\d|3[01])"
    r"(?P<strike>\d{4,})(?P<right>CE|PE)$"
)
MONTH_PATTERN = r"(?:JAN|FEB|MAR|APR|MAY|JUN|JUL|AUG|SEP|OCT|NOV|DEC)"
MONTHLY_OPTION_SYMBOL_RE = re.compile(
    rf"^(?P<underlying>[A-Z][A-Z0-9]*?)(?P<year>\d{{2}})"
    rf"(?P<month>{MONTH_PATTERN})(?P<strike>\d+)(?P<right>CE|PE)$"
)
FUTURE_SYMBOL_RE = re.compile(
    rf"^(?P<underlying>[A-Z][A-Z0-9]*?)(?P<year>\d{{2}})"
    rf"(?P<month>{MONTH_PATTERN})FUT$"
)


def parse_args() -> argparse.Namespace:
    load_dotenv()
    p = argparse.ArgumentParser(description="Fetch trades from Fyers API for a given date")
    p.add_argument("--date", required=True, help="Date in YYYY-MM-DD format to fetch trades for")
    p.add_argument("--debug", action="store_true",
                   help="Print the Fyers response and filtering details to stderr")
    p.add_argument("--client-id", default=os.environ.get("FYERS_CLIENT_ID"),
                   help="Fyers client ID (env FYERS_CLIENT_ID)")
    p.add_argument("--token", default=os.environ.get("FYERS_ACCESS_TOKEN"),
                   help="Fyers access token (env FYERS_ACCESS_TOKEN)")
    return p.parse_args()


def debug_print(enabled: bool, message: str) -> None:
    if enabled:
        print(f"DEBUG: {message}", file=sys.stderr)


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
    def normalize(items: List[Any]) -> List[Dict[str, Any]]:
        normalized = []
        for item in items:
            if not isinstance(item, dict):
                continue
            item = dict(item)
            item.setdefault("trade_price", item.get("tradePrice", ""))
            item.setdefault("traded_qty", item.get("tradedQty", ""))
            normalized.append(item)
        return normalized

    if isinstance(data, list):
        return normalize(data)
    if isinstance(data, dict):
        # Common wrappers
        for key in ("data", "items", "orders", "trades", "tradeBook", "tradeHistory", "result"):
            if key in data and isinstance(data[key], list):
                return normalize(data[key])
        # If dict values are list-like, try to pick the first list
        for v in data.values():
            if isinstance(v, list):
                return normalize(v)
    return []


def format_option_contract(symbol: Any) -> str:
    """Convert a Fyers option or future symbol to a readable contract description."""
    if not isinstance(symbol, str):
        return ""
    symbol_name = symbol.rsplit(":", 1)[-1].upper()

    match = MONTHLY_OPTION_SYMBOL_RE.fullmatch(symbol_name)
    if match:
        option_type = "CALL" if match.group("right") == "CE" else "PUT"
        return (
            f"{match.group('underlying')} {match.group('year')} "
            f"{match.group('month')} {match.group('strike')} {option_type}"
        )

    match = FUTURE_SYMBOL_RE.fullmatch(symbol_name)
    if match:
        return (
            f"{match.group('underlying')} {match.group('year')} "
            f"{match.group('month')} FUT"
        )

    match = OPTION_SYMBOL_RE.fullmatch(symbol_name)
    if not match:
        return ""

    month_value = match.group("month")
    month = {"O": 10, "N": 11, "D": 12}.get(month_value)
    if month is None:
        month = int(month_value)
    day = int(match.group("day"))
    try:
        datetime.date(2000, month, day)
    except ValueError:
        return ""

    month_name = calendar.month_abbr[month].upper()
    option_type = "CALL" if match.group("right") == "CE" else "PUT"
    return (
        f"{match.group('underlying')} {day} {month_name} "
        f"{match.group('strike')} {option_type}"
    )


def format_trade_side(side: Any) -> str:
    """Convert Fyers' numeric trade side to a readable label."""
    if side is None:
        return ""
    if isinstance(side, bool):
        return str(side)
    if side == 1:
        return "BUY"
    if side == -1:
        return "SELL"
    if isinstance(side, str):
        normalized = side.strip().casefold()
        if normalized in ("buy", "b"):
            return "BUY"
        if normalized in ("sell", "s"):
            return "SELL"
        if normalized == "1":
            return "BUY"
        if normalized == "-1":
            return "SELL"
    return str(side)


def select_trade_columns(item: Dict[str, Any]) -> Dict[str, Any]:
    return {
        column: (
            format_option_contract(item.get("symbol", ""))
            if column == "option_contract"
            else format_trade_side(item.get("side"))
            if column == "side"
            else item.get(column, "")
        )
        for column in COLUMNS
    }


def get_trades(
    client_id: str, token: str, target_date: datetime.date, debug: bool = False
) -> Any:
    fyers = fyersModel.FyersModel(
        token=token,
        is_async=False,
        client_id=client_id,
        log_path="",
    )
    response = fyers.tradebook()
    debug_print(debug, f"Fyers tradebook response: {response!r}")
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


def order_time(item: Dict[str, Any]) -> datetime.datetime:
    value = item.get("orderDateTime")
    if isinstance(value, (int, float)):
        timestamp = value / 1000 if value > 1e12 else value
        try:
            return datetime.datetime.fromtimestamp(timestamp)
        except (OverflowError, OSError, ValueError):
            return datetime.datetime.max
    if isinstance(value, str):
        for date_format in (
            "%d-%b-%Y %H:%M:%S",
            "%d-%m-%Y %H:%M:%S",
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%d %H:%M:%S",
        ):
            try:
                return datetime.datetime.strptime(value, date_format)
            except ValueError:
                continue
    return datetime.datetime.max


def sort_items(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Sort trades chronologically by order time."""
    return sorted(items, key=order_time)


def write_csv(items: List[Dict[str, Any]]) -> None:
    writer = csv.DictWriter(sys.stdout, fieldnames=COLUMNS, extrasaction="ignore",
                            lineterminator="\n")
    writer.writeheader()
    writer.writerows(select_trade_columns(item) for item in sort_items(items))


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
        debug_print(args.debug, f"Fetching trades for {target_date.isoformat()}")
        resp = get_trades(args.client_id, args.token, target_date, debug=args.debug)
    except Exception as e:
        print(f"Error fetching trades: {e}", file=sys.stderr)
        return 3

    items = extract_items(resp)
    debug_print(args.debug, f"Normalized {len(items)} trade item(s)")
    filtered = filter_by_date(items, target_date)
    debug_print(args.debug, f"{len(filtered)} item(s) matched {target_date.isoformat()}")

    write_csv(filtered)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
