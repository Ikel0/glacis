from __future__ import annotations

import json
import os
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from .contract import ContractError, validate
from .decision import assess
from .store import overview, save

ROOT = Path(__file__).resolve().parents[2]
WEB = ROOT / "web"


def weather_context() -> dict:
    url = "https://api.open-meteo.com/v1/forecast?latitude=48.8566&longitude=2.3522&current=temperature_2m,relative_humidity_2m&timezone=Europe%2FParis"
    try:
        request = Request(url, headers={"User-Agent": "Ikel-Glacis/1.0 (+https://github.com/Ikel0/glacis)"})
        with urlopen(request, timeout=5) as response:
            payload = json.load(response)
        current = payload.get("current", {})
        return {"live": True, "source": "Open-Meteo · Paris", "temperature_c": current.get("temperature_2m"), "humidity": current.get("relative_humidity_2m"), "observed_at": current.get("time")}
    except Exception:
        return {"live": False, "source": "Open-Meteo · Paris", "message": "Contexte météo indisponible."}


def ingest(reading: dict) -> dict:
    valid = validate(reading)
    result = assess(valid)
    return {"reading_id": valid["reading_id"], "inserted": save(valid, result), "decision": result}


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(WEB), **kwargs)

    def send_json(self, status: int, payload: dict) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):  # noqa: N802
        path = urlparse(self.path).path
        if path == "/health":
            return self.send_json(HTTPStatus.OK, {"status": "ok", "service": "glacis"})
        if path == "/api/overview":
            return self.send_json(HTTPStatus.OK, overview())
        if path == "/api/weather-context":
            return self.send_json(HTTPStatus.OK, weather_context())
        if path == "/":
            self.path = "/index.html"
        return super().do_GET()

    def do_POST(self):  # noqa: N802
        path = urlparse(self.path).path
        if path == "/api/demo":
            events = [json.loads(line) for line in (ROOT / "data" / "demo_readings.jsonl").read_text().splitlines()]
            values = [ingest(event) for event in events]
            return self.send_json(HTTPStatus.CREATED, {"inserted": sum(value["inserted"] for value in values)})
        if path != "/api/readings":
            return self.send_json(HTTPStatus.NOT_FOUND, {"error": "unknown endpoint"})
        try:
            length = int(self.headers.get("Content-Length", "0"))
            return self.send_json(HTTPStatus.CREATED, ingest(json.loads(self.rfile.read(length))))
        except json.JSONDecodeError:
            return self.send_json(HTTPStatus.BAD_REQUEST, {"error": "body must be JSON"})
        except ContractError as exc:
            return self.send_json(HTTPStatus.UNPROCESSABLE_ENTITY, {"error": str(exc)})

    def log_message(self, fmt, *args):
        return


def main() -> None:
    port = int(os.getenv("PORT", "8090"))
    print(f"Glacis running on http://localhost:{port}")
    ThreadingHTTPServer(("0.0.0.0", port), Handler).serve_forever()


if __name__ == "__main__":
    main()
