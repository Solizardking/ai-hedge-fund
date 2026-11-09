#!/usr/bin/env python3
"""hedge-fund-backend — read-only HTTP API over the aihf v2 hedge_fund engine.

v1 scope (deliberate, fail-closed):
- Serves engine metadata and the state of deployed PAPER funds
  (~/.hedge-fund/paper/<name>/: fund.yaml, broker.json, control.json,
  ledger/*.json) exactly as the engine writes them.
- No mutation endpoints. The engine's brokers are SimBroker + PaperBroker
  only — there is no live-trading code path in this package at all.
- Data-dependent execution (paper tick / backtest) needs
  FINANCIAL_DATASETS_API_KEY (or the x402 wallet path) in the service env;
  until the owner sets it, /api/status reports data_configured=false and
  tick/backtest stay unimplemented rather than pretending to run.

Stdlib + PyYAML only, mirroring the sol-fund-web service pattern.
"""
from __future__ import annotations

import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse, unquote

import yaml

ENGINE_NAME = "aihf-hedge-fund"
ENGINE_VERSION = "2.7.1"  # pyproject.toml of the bundled hedge_fund package
MODE = "paper"

USER_DIR = Path(os.environ.get("HEDGE_FUND_HOME", Path.home() / ".hedge-fund"))
PAPER_DIR = USER_DIR / "paper"

KEY_ENVS = [
    "FINANCIAL_DATASETS_API_KEY",
    "ANTHROPIC_API_KEY",
    "OPENAI_API_KEY",
    "XAI_API_KEY",
    "DEEPSEEK_API_KEY",
    "GOOGLE_API_KEY",
]


def key_presence() -> dict:
    return {k: bool(os.environ.get(k)) for k in KEY_ENVS}


def fund_summary(fdir: Path) -> dict:
    out: dict = {"name": fdir.name}
    fy = fdir / "fund.yaml"
    if fy.exists():
        try:
            doc = yaml.safe_load(fy.read_text()) or {}
            out["universe"] = doc.get("universe", [])
            out["broker"] = doc.get("broker", "paper")
            out["created"] = doc.get("created")
            spec = doc.get("spec") or {}
            out["capital"] = spec.get("capital")
            out["strategies"] = [s.get("name") for s in (spec.get("strategies") or []) if isinstance(s, dict)]
        except Exception as e:  # surface, never hide a corrupt fund file
            out["fund_yaml_error"] = str(e)
    bj = fdir / "broker.json"
    if bj.exists():
        try:
            book = json.loads(bj.read_text())
            out["cash"] = book.get("cash")
            positions = book.get("positions") or book.get("shares") or {}
            out["positions"] = positions if isinstance(positions, dict) else {}
            out["position_count"] = len(positions) if isinstance(positions, dict) else 0
        except Exception as e:
            out["broker_error"] = str(e)
    cj = fdir / "control.json"
    halted = False
    if cj.exists():
        try:
            halted = bool(json.loads(cj.read_text()).get("halted"))
        except Exception:
            halted = False
    out["halted"] = halted
    ledger = fdir / "ledger"
    records = sorted(ledger.rglob("*.json")) if ledger.exists() else []
    # checkpoint.json files are state snapshots, not session records
    records = [r for r in records if r.name != "checkpoint.json"]
    out["sessions_recorded"] = len(records)
    out["last_session_file"] = records[-1].name if records else None
    return out


def list_funds() -> list:
    if not PAPER_DIR.exists():
        return []
    return [fund_summary(d) for d in sorted(PAPER_DIR.iterdir()) if d.is_dir()]


def engine_present() -> dict:
    pkg = Path(__file__).resolve().parent  # this module lives inside hedge_fund/
    py = list(pkg.rglob("*.py")) if pkg.exists() else []
    return {"bundled": pkg.exists(), "python_files": len(py)}


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, fmt, *args):  # keep stdout clean; Railway collects it anyway
        pass

    def _send(self, code: int, obj: dict):
        body = json.dumps(obj, indent=2, default=str).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        path = urlparse(self.path).path.rstrip("/") or "/"
        if path == "/healthz":
            return self._send(200, {"ok": True, "engine": ENGINE_NAME, "version": ENGINE_VERSION, "mode": MODE})
        if path == "/api/status":
            keys = key_presence()
            return self._send(200, {
                "engine": ENGINE_NAME,
                "version": ENGINE_VERSION,
                "mode": MODE,
                "engine_package": engine_present(),
                "paper_dir": str(PAPER_DIR),
                "funds": len(list_funds()),
                "keys_configured": keys,
                "data_configured": bool(keys.get("FINANCIAL_DATASETS_API_KEY")),
                "execution_endpoints": "disabled_in_v1_read_only",
            })
        if path == "/api/funds":
            return self._send(200, {"funds": list_funds()})
        if path.startswith("/api/funds/"):
            name = unquote(path[len("/api/funds/"):])
            if "/" in name or name in ("", ".", ".."):
                return self._send(400, {"error": "bad fund name"})
            fdir = PAPER_DIR / name
            if not fdir.is_dir():
                return self._send(404, {"error": "fund not found", "fund": name})
            return self._send(200, fund_summary(fdir))
        return self._send(404, {"error": "not found", "path": path})

    def do_POST(self):
        return self._send(501, {"error": "read_only_v1", "detail": "mutation endpoints arrive with the client phase"})

    do_PUT = do_POST
    do_DELETE = do_POST
    do_PATCH = do_POST


def main():
    port = int(os.environ.get("PORT", "8080"))
    PAPER_DIR.mkdir(parents=True, exist_ok=True)
    srv = ThreadingHTTPServer(("0.0.0.0", port), Handler)
    print(f"{ENGINE_NAME} backend listening on :{port} (mode={MODE}, paper_dir={PAPER_DIR})", flush=True)
    srv.serve_forever()


if __name__ == "__main__":
    main()
