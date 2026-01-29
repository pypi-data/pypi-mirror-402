"""CCXT Pro (WebSocket) tool for Strands Agents.

Requires: pip install ccxtpro

Exposes:
- ccxt_pro_watch(exchange, method, args, kwargs, config, max_messages, max_seconds)
"""

from __future__ import annotations

import asyncio
import json
import os
import time
from typing import Any, Dict, List, Optional

from strands import tool


def _redact(obj: Any) -> Any:
    if isinstance(obj, dict):
        out = {}
        for k, v in obj.items():
            lk = str(k).lower()
            if any(s in lk for s in ["secret", "apikey", "api_key", "password", "token", "uid"]):
                out[k] = "***"
            else:
                out[k] = _redact(v)
        return out
    if isinstance(obj, list):
        return [_redact(x) for x in obj]
    return obj


def _json_loads_maybe(s: Optional[str], default: Any) -> Any:
    if s is None:
        return default
    if isinstance(s, (dict, list)):
        return s
    s = str(s).strip()
    if not s:
        return default
    return json.loads(s)


def _make_config(config: Dict[str, Any]) -> Dict[str, Any]:
    # Env defaults
    cfg = {
        "enableRateLimit": True,
        "timeout": int(os.getenv("CCXT_TIMEOUT", "30000")),
    }
    default_type = os.getenv("CCXT_DEFAULT_TYPE")
    if default_type:
        cfg["options"] = {"defaultType": default_type}

    # Auth
    api_key = os.getenv("CCXT_API_KEY")
    secret = os.getenv("CCXT_SECRET")
    if not api_key and exchange_id:
        api_key = os.getenv(f"{exchange_id.upper()}_API_KEY")
    if not secret and exchange_id:
        secret = os.getenv(f"{exchange_id.upper()}_API_SECRET")
    password = os.getenv("CCXT_PASSWORD")
    uid = os.getenv("CCXT_UID")
    token = os.getenv("CCXT_TOKEN")
    if api_key:
        cfg["apiKey"] = api_key
    if secret:
        cfg["secret"] = secret
    if password:
        cfg["password"] = password
    if uid:
        cfg["uid"] = uid
    if token:
        cfg["token"] = token

    # Merge caller config last
    cfg.update(config or {})
    return cfg


@tool
def ccxt_pro_watch(
    exchange: str | None = None,
    method: str | None = None,
    args: str | None = None,
    kwargs: str | None = None,
    config: str | None = None,
    max_messages: int = 5,
    max_seconds: int = 15,
) -> Dict[str, Any]:
    """Call ccxt.pro watch_* methods and return bounded snapshots.

    Params:
      - exchange: e.g. "bybit" (default from CCXT_EXCHANGE)
      - method: e.g. "watch_ticker", "watch_trades"
      - args: JSON array string
      - kwargs: JSON object string
      - config: JSON object string -> passed into exchange constructor
    """
    ex_id = exchange or os.getenv("CCXT_EXCHANGE")
    if not ex_id:
        return {"status": "error", "content": [{"text": "exchange required (or set CCXT_EXCHANGE)"}]}
    if not method:
        return {"status": "error", "content": [{"text": "method required"}]}

    try:
        import ccxt.pro as ccxtpro  # type: ignore
    except Exception as e:
        return {
            "status": "error",
            "content": [{"text": f"ccxtpro not installed/importable: {e}. Install with: pip install ccxtpro"}],
        }

    cfg = _make_config(_json_loads_maybe(config, {}))
    sandbox = os.getenv("CCXT_SANDBOX", "false").lower() == "true"

    a = _json_loads_maybe(args, [])
    k = _json_loads_maybe(kwargs, {})

    async def _run() -> Dict[str, Any]:
        if not hasattr(ccxtpro, ex_id):
            return {"ok": False, "error": f"Unknown exchange: {ex_id}"}
        ex_cls = getattr(ccxtpro, ex_id)
        ex = ex_cls(cfg)
        try:
            if sandbox and hasattr(ex, "set_sandbox_mode"):
                ex.set_sandbox_mode(True)

            if not hasattr(ex, method):
                return {"ok": False, "error": f"Exchange has no method: {method}"}
            fn = getattr(ex, method)

            out: List[Any] = []
            started = time.time()
            for _ in range(max_messages):
                if time.time() - started > max_seconds:
                    break
                msg = await fn(*a, **k)
                out.append(_redact(msg))

            return {"ok": True, "exchange": ex_id, "method": method, "messages": out}
        finally:
            try:
                await ex.close()
            except Exception:
                pass

    try:
        res = asyncio.run(_run())
        if not res.get("ok"):
            return {"status": "error", "content": [{"text": json.dumps(res, ensure_ascii=False, indent=2)}]}
        return {"status": "success", "content": [{"text": json.dumps(res, ensure_ascii=False, indent=2)}]}
    except Exception as e:
        return {"status": "error", "content": [{"text": f"Error: {e}"}]}
