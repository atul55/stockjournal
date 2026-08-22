"""Local HTTP API for loading Fyers trades into Excel or another client."""
from __future__ import annotations

import datetime
import csv
import io
import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse
from typing import Any, Dict, List

from dotenv import load_dotenv

from fetch_trades import extract_items, filter_by_date, get_trades, sort_items

load_dotenv()

COLUMNS = ("symbol", "orderDateTime", "trade_price", "traded_qty")


def select_columns(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return [
        {column: item.get(column, "") for column in COLUMNS}
        for item in sort_items(items)
    ]


class TradesRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        request = urlparse(self.path)
        if request.path == "/health":
            self.send_json({"status": "ok"})
            return
        if request.path != "/trades":
            self.send_json({"detail": "Not found"}, status=404)
            return

        date_values = parse_qs(request.query).get("date", [])
        if not date_values:
            self.send_json({"detail": "The date query parameter is required"}, status=400)
            return
        try:
            target_date = datetime.date.fromisoformat(date_values[0])
        except ValueError:
            self.send_json({"detail": "date must use YYYY-MM-DD format"}, status=400)
            return

        client_id = os.getenv("FYERS_CLIENT_ID")
        token = os.getenv("FYERS_ACCESS_TOKEN")
        if not client_id or not token:
            self.send_json({"detail": "FYERS_CLIENT_ID and FYERS_ACCESS_TOKEN must be set"}, status=500)
            return

        try:
            response = get_trades(client_id, token, target_date)
            items = filter_by_date(extract_items(response), target_date)
            self.send_csv(select_columns(items))
        except Exception as error:
            self.send_json({"detail": str(error)}, status=502)

    def send_json(self, payload: Any, status: int = 200) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def send_csv(self, items: List[Dict[str, Any]], status: int = 200) -> None:
        output = io.StringIO(newline="")
        writer = csv.DictWriter(output, fieldnames=COLUMNS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(items)
        body = output.getvalue().encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/csv; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format: str, *args: Any) -> None:
        return


if __name__ == "__main__":
    server = ThreadingHTTPServer(("127.0.0.1", 8000), TradesRequestHandler)
    print("Stockjournal API running at http://127.0.0.1:8000")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
