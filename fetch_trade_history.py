#!/usr/bin/env python3
"""Fetch historical Fyers trades for a specific date."""
from __future__ import annotations

import argparse
import csv
import datetime
import os
import sys
from typing import Any, Dict, List

from dotenv import load_dotenv
from fyers_apiv3 import fyersModel

from fetch_trades import COLUMNS, extract_items, select_trade_columns

PAGE_SIZE = 100


def parse_args() -> argparse.Namespace:
    load_dotenv()
    parser = argparse.ArgumentParser(
        description="Fetch historical Fyers trades for a given date"
    )
    parser.add_argument("--date", required=True, help="Date in YYYY-MM-DD format")
    parser.add_argument("--debug", action="store_true",
                        help="Print request and response details to stderr")
    parser.add_argument("--client-id", default=os.environ.get("FYERS_CLIENT_ID"),
                        help="Fyers client ID (env FYERS_CLIENT_ID)")
    parser.add_argument("--token", default=os.environ.get("FYERS_ACCESS_TOKEN"),
                        help="Fyers access token (env FYERS_ACCESS_TOKEN)")
    return parser.parse_args()


def debug_print(enabled: bool, message: str) -> None:
    if enabled:
        print(f"DEBUG: {message}", file=sys.stderr)


def get_history(
    client_id: str, token: str, target_date: datetime.date, debug: bool = False
) -> List[Dict[str, Any]]:
    fyers = fyersModel.FyersModel(
        token=token,
        is_async=False,
        client_id=client_id,
        log_path="",
    )
    trades: List[Dict[str, Any]] = []
    page_no = 1

    while True:
        request = {
            "from_date": target_date.isoformat(),
            "to_date": target_date.isoformat(),
            "page_no": page_no,
            "page_size": PAGE_SIZE,
        }
        debug_print(debug, f"Requesting trade history page {page_no}: {request}")
        response = fyers.tradehistory(data=request)
        if not isinstance(response, dict):
            raise RuntimeError("Unexpected response from Fyers Trade History API")

        debug_print(
            debug,
            "Trade History response: "
            f"status={response.get('s')!r}, code={response.get('code')!r}, "
            f"message={response.get('message')!r}",
        )
        if response.get("s") == "error":
            code = response.get("code", "unknown")
            message = response.get("message", "Fyers API request failed")
            raise RuntimeError(f"Fyers API error ({code}): {message}")

        page_data = response.get("data")
        if not isinstance(page_data, list):
            raise RuntimeError(
                "Unexpected Fyers Trade History response: expected a 'data' list"
            )

        page_trades = extract_items(response)
        trades.extend(page_trades)
        debug_print(debug, f"Page {page_no} returned {len(page_trades)} trade(s)")

        if len(page_data) < PAGE_SIZE:
            break
        page_no += 1

    debug_print(debug, f"Fetched {len(trades)} historical trade(s)")
    return trades


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


def write_csv(items: List[Dict[str, Any]]) -> None:
    writer = csv.DictWriter(
        sys.stdout, fieldnames=COLUMNS, extrasaction="ignore", lineterminator="\n"
    )
    writer.writeheader()
    sorted_items = sorted(
        items,
        key=lambda item: (
            item.get("traded_qty", 0),
            str(item.get("symbol", "")).casefold(),
            order_time(item),
        ),
    )
    writer.writerows(select_trade_columns(item) for item in sorted_items)


def main() -> int:
    args = parse_args()
    if not args.client_id:
        print("Missing Fyers client ID. Set FYERS_CLIENT_ID or pass --client-id",
              file=sys.stderr)
        return 2
    if not args.token:
        print("Missing Fyers access token. Set FYERS_ACCESS_TOKEN or pass --token",
              file=sys.stderr)
        return 2
    try:
        target_date = datetime.datetime.strptime(args.date, "%Y-%m-%d").date()
    except ValueError:
        print("Date must be in YYYY-MM-DD format", file=sys.stderr)
        return 2

    try:
        trades = get_history(
            args.client_id, args.token, target_date, debug=args.debug
        )
    except Exception as error:
        print(f"Error fetching trade history: {error}", file=sys.stderr)
        return 3

    write_csv(trades)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
