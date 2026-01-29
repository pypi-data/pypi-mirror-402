"""CCXT Generic Tool for Strands Agents

Goals:
- Expose *all* ccxt exchange methods via a single tool call (sync).
- Safe-by-default: no secrets in outputs, structured responses, helpful errors.
- Convenience helpers: list_exchanges, list_methods, multi_orderbook.

Usage examples:
- ccxt_generic(exchange='bybit', method='fetch_ticker', args='["BTC/USDT"]')
- ccxt_generic(exchange='binance', method='fetch_ohlcv', args='["BTC/USDT","1m",null,200]')
- ccxt_generic(exchange='bybit', method='create_order', args='["BTC/USDT","market","buy",0.001]', kwargs='{"price": null}')

Notes:
- Keep API keys in your agent runtime environment (shell/.zshrc/.env/secret manager).
- For authenticated calls, set env like:
  CCXT_EXCHANGE=bybit
  CCXT_API_KEY=...
  CCXT_SECRET=...
  CCXT_PASSWORD=... (optional)
  CCXT_UID=... (optional)
  CCXT_TOKEN=... (optional)
"""

from __future__ import annotations

import json
import asyncio
import os
import time
import traceback
from dataclasses import dataclass
from typing import Any, Dict, Optional

import ccxt
from strands import tool


SENSITIVE_KEYS = {
    "apiKey",
    "secret",
    "password",
    "uid",
    "token",
    "privateKey",
    "walletAddress",
    "mnemonic",
}


def _json_load_maybe(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, (dict, list, int, float, bool)):
        return value
    if isinstance(value, str):
        s = value.strip()
        if s == "":
            return None
        # allow raw strings that are not JSON
        if (s.startswith("{") and s.endswith("}")) or (s.startswith("[") and s.endswith("]")):
            return json.loads(s)
        return value
    return value


def _redact(obj: Any) -> Any:
    """Recursively redact secrets."""
    try:
        if isinstance(obj, dict):
            out = {}
            for k, v in obj.items():
                if str(k) in SENSITIVE_KEYS:
                    out[k] = "***"
                else:
                    out[k] = _redact(v)
            return out
        if isinstance(obj, list):
            return [_redact(x) for x in obj]
        return obj
    except Exception:
        return "***"


def _guess_default_type(exchange_id: str) -> Optional[str]:
    # conservative default: None (ccxt default), but allow override via env
    return os.getenv("CCXT_DEFAULT_TYPE") or None

def _normalize_exchange_id(exchange_id: str) -> str:
    return (exchange_id or "").strip().lower()


def _possible_secret_env_keys(prefix: str) -> list[str]:
    # common variants people use
    return [
        f"{prefix}_API_SECRET",
        f"{prefix}_API_SECRET_KEY",
        f"{prefix}_SECRET",
        f"{prefix}_SECRET_KEY",
    ]


def _env_get_first(keys: list[str]) -> Optional[str]:
    for k in keys:
        v = os.getenv(k)
        if v:
            return v
    return None


def _discover_exchange_from_env() -> tuple[Optional[str], list[str]]:
    """Infer exchange id from env vars.

    Candidate rule: we only consider PREFIX_API_KEY if a PREFIX secret variant also exists.
    Returns (exchange_id, candidates). If exactly one candidate -> exchange_id set.
    """
    candidates: set[str] = set()
    for k in os.environ.keys():
        if not k.endswith("_API_KEY"):
            continue
        prefix = k[:-8]  # strip _API_KEY
        if not prefix:
            continue
        if _env_get_first(_possible_secret_env_keys(prefix)):
            candidates.add(prefix.lower())
    out = sorted(candidates)
    if len(out) == 1:
        return out[0], out
    return None, out


def _resolve_credentials(exchange_id: str, user_config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Resolve credentials for CCXT.

    Priority:
      1) user_config explicit apiKey/secret/password/uid/token
      2) CCXT_API_KEY / CCXT_SECRET (exchange-agnostic)
      3) {EXCHANGE}_API_KEY + {EXCHANGE}_API_SECRET (plus common variants)
    """
    cfg: Dict[str, Any] = {}

    # 1) explicit in user_config
    if user_config:
        for k in ("apiKey", "secret", "password", "uid", "token"):
            v = user_config.get(k)
            if v:
                cfg[k] = v

    # 2) generic env
    if "apiKey" not in cfg:
        v = os.getenv("CCXT_API_KEY")
        if v:
            cfg["apiKey"] = v
    if "secret" not in cfg:
        v = os.getenv("CCXT_SECRET")
        if v:
            cfg["secret"] = v

    # 3) exchange-specific env
    prefix = exchange_id.upper()
    if "apiKey" not in cfg:
        v = os.getenv(f"{prefix}_API_KEY")
        if v:
            cfg["apiKey"] = v
    if "secret" not in cfg:
        v = _env_get_first(_possible_secret_env_keys(prefix))
        if v:
            cfg["secret"] = v

    # optional generic creds
    for env_k, cfg_k in (
        ("CCXT_PASSWORD", "password"),
        ("CCXT_UID", "uid"),
        ("CCXT_TOKEN", "token"),
    ):
        if cfg_k not in cfg:
            v = os.getenv(env_k)
            if v:
                cfg[cfg_k] = v

    return cfg



def _build_exchange(exchange_id: str, config: Optional[Dict[str, Any]] = None):
    exchange_id = _normalize_exchange_id(exchange_id)
    if not hasattr(ccxt, exchange_id):
        raise ValueError(f"Unknown exchange '{exchange_id}'. Try action='list_exchanges'.")

    cls = getattr(ccxt, exchange_id)

    cfg: Dict[str, Any] = {
        "enableRateLimit": True,
        "timeout": int(os.getenv("CCXT_TIMEOUT", "30000")),
    }

    # credentials from user config/env
    user_cfg = config if isinstance(config, dict) else None
    cfg.update(_resolve_credentials(exchange_id, user_cfg))

    default_type = _guess_default_type(exchange_id)
    if default_type:
        cfg.setdefault("options", {})
        cfg["options"].setdefault("defaultType", default_type)

    if config:
        # merge user config last (but secrets will be redacted in output)
        cfg.update(config)

    ex = cls(cfg)

    # optional sandbox
    if os.getenv("CCXT_SANDBOX", "false").lower() == "true":
        if hasattr(ex, "set_sandbox_mode"):
            ex.set_sandbox_mode(True)

    return ex


@dataclass
class CallResult:
    ok: bool
    exchange: str
    method: Optional[str]
    ms: int
    def __init__(self, ok: bool, exchange: str, method: Optional[str], ms: int, result: Any=None, error: Optional[str]=None, traceback: Optional[str]=None):
        self.ok=ok; self.exchange=exchange; self.method=method; self.ms=ms; self.result=result; self.error=error; self.traceback=traceback


def _call(ex, method: str, args: list, kwargs: dict) -> CallResult:
    t0 = time.time()
    try:
        if not hasattr(ex, method):
            # also accept camelCase names
            raise AttributeError(f"Exchange '{ex.id}' has no method '{method}'.")
        fn = getattr(ex, method)
        res = fn(*args, **kwargs)
        return CallResult(True, ex.id, method, int((time.time() - t0) * 1000), result=res)
    except Exception as e:
        return CallResult(
            False,
            ex.id,
            method,
            int((time.time() - t0) * 1000),
            error=f"{type(e).__name__}: {e}",
            traceback=traceback.format_exc(),
        )


@tool
def ccxt_generic(
    action: str = "call",
    exchange: str = None,
    method: str = None,
    args: str = None,
    kwargs: str = None,
    config: str = None,
) -> Dict[str, Any]:
    """Generic CCXT tool.

    Actions:
    - call: call any exchange method
    - list_exchanges: list supported exchanges
    - describe: describe exchange capabilities + markets (light)
    - list_methods: list callable methods on exchange instance

    Params:
    - exchange: ccxt exchange id (e.g., 'bybit', 'binance')
    - method: method name (snake_case, as in ccxt python)
    - args: JSON array string of positional args
    - kwargs: JSON object string of keyword args
    - config: JSON object string for exchange constructor overrides
    """

    try:
        if action == "list_exchanges":
            ids = sorted(ccxt.exchanges)
            return {
                "status": "success",
                "content": [
                    {
                        "text": json.dumps(
                            {"count": len(ids), "exchanges": ids[:500]}, indent=2
                        )
                    }
                ],
            }

        if action in ("call", "describe", "list_methods"):
            user_cfg = _json_load_maybe(config)
            exchange_id = _normalize_exchange_id(exchange or os.getenv("CCXT_EXCHANGE"))

            if not exchange_id:
                inferred, candidates = _discover_exchange_from_env()
                if inferred:
                    exchange_id = inferred
                else:
                    if candidates:
                        raise ValueError(
                            "exchange is required (or set CCXT_EXCHANGE). "
                            f"Detected multiple exchange key candidates in env: {candidates}. "
                            "Please pass exchange=... explicitly."
                        )
                    raise ValueError("exchange is required (or set CCXT_EXCHANGE env).")

            ex = _build_exchange(exchange_id, user_cfg)

            if action == "list_methods":
                # only public-callable methods
                methods = sorted(
                    [
                        m
                        for m in dir(ex)
                        if not m.startswith("_") and callable(getattr(ex, m, None))
                    ]
                )
                return {
                    "status": "success",
                    "content": [{"text": json.dumps({"exchange": ex.id, "methods": methods}, indent=2)}],
                }

            if action == "describe":
                # lightweight describe: capabilities + (optionally) markets
                info = {
                    "id": ex.id,
                    "name": getattr(ex, "name", None),
                    "rateLimit": getattr(ex, "rateLimit", None),
                    "has": getattr(ex, "has", None),
                    "timeframes": getattr(ex, "timeframes", None),
                    "urls": getattr(ex, "urls", None),
                }
                # Avoid huge market dumps by default
                if os.getenv("CCXT_DESCRIBE_INCLUDE_MARKETS", "false").lower() == "true":
                    try:
                        markets = ex.load_markets()
                        info["markets_count"] = len(markets)
                    except Exception as e:
                        info["markets_error"] = f"{type(e).__name__}: {e}"
                return {
                    "status": "success",
                    "content": [{"text": json.dumps(_redact(info), indent=2)}],
                }

            # action == call
            if not method:
                raise ValueError("method is required for action='call'.")

            parsed_args = _json_load_maybe(args)
            parsed_kwargs = _json_load_maybe(kwargs)
            if parsed_args is None:
                parsed_args = []
            if isinstance(parsed_args, str):
                # allow passing a raw string as single arg
                parsed_args = [parsed_args]
            if not isinstance(parsed_args, list):
                raise ValueError("args must be a JSON array string (e.g., '[""BTC/USDT""]')")
            if parsed_kwargs is None:
                parsed_kwargs = {}
            if not isinstance(parsed_kwargs, dict):
                raise ValueError("kwargs must be a JSON object string")

            r = _call(ex, method, parsed_args, parsed_kwargs)
            payload = {
                "ok": r.ok,
                "exchange": r.exchange,
                "method": r.method,
                "ms": r.ms,
            }
            if r.ok:
                payload["result"] = _redact(r.result)
                status = "success"
            else:
                payload["error"] = r.error
                payload["traceback"] = r.traceback
                status = "error"

            # best-effort close
            try:
                ex.close()
            except Exception:
                pass

            return {"status": status, "content": [{"text": json.dumps(payload, indent=2)[:12000]}]}

        return {
            "status": "error",
            "content": [
                {
                    "text": "Unknown action. Valid: call, list_exchanges, describe, list_methods"
                }
            ],
        }

    except Exception as e:
        return {
            "status": "error",
            "content": [{"text": f"{type(e).__name__}: {e}\n\n{traceback.format_exc()}"}],
        }


@tool
def ccxt_multi_exchange_orderbook(
    exchanges: str,
    symbol: str,
    limit: int = 10,
) -> Dict[str, Any]:
    """Fetch best bid/ask across multiple exchanges for a symbol.

    exchanges: JSON array string of exchange ids, e.g. '["binance","bybit","okx"]'
    """
    try:
        ex_ids = _json_load_maybe(exchanges)
        if not isinstance(ex_ids, list) or not ex_ids:
            raise ValueError("exchanges must be JSON array string of exchange ids")

        rows = []
        for ex_id in ex_ids:
            ex = _build_exchange(str(ex_id).strip(), None)
            r = _call(ex, "fetch_order_book", [symbol, limit], {})
            if r.ok:
                ob = r.result
                bid = ob.get("bids", [[None]])[0][0] if ob.get("bids") else None
                ask = ob.get("asks", [[None]])[0][0] if ob.get("asks") else None
                rows.append({"exchange": ex.id, "bid": bid, "ask": ask})
            else:
                rows.append({"exchange": ex.id, "error": r.error})
            try:
                ex.close()
            except Exception:
                pass

        # compute best
        best_bid = max([r["bid"] for r in rows if r.get("bid") is not None], default=None)
        best_ask = min([r["ask"] for r in rows if r.get("ask") is not None], default=None)
        best_bid_ex = next((r["exchange"] for r in rows if r.get("bid") == best_bid), None)
        best_ask_ex = next((r["exchange"] for r in rows if r.get("ask") == best_ask), None)

        out = {
            "symbol": symbol,
            "rows": rows,
            "best_bid": {"price": best_bid, "exchange": best_bid_ex},
            "best_ask": {"price": best_ask, "exchange": best_ask_ex},
        }
        return {"status": "success", "content": [{"text": json.dumps(out, indent=2)}]}

    except Exception as e:
        return {
            "status": "error",
            "content": [{"text": f"{type(e).__name__}: {e}\n\n{traceback.format_exc()}"}],
        }

# ---------------- CCXT PRO (optional) ----------------

def _import_ccxtpro():
    try:
        import ccxt.pro as ccxtpro  # type: ignore
        return ccxtpro
    except Exception as e:
        raise ImportError("ccxtpro is not installed. Install with: pip install ccxtpro") from e


async def _ccxtpro_watch_loop(ex, method: str, args_list: list, kwargs_dict: dict, max_messages: int, max_seconds: int):
    out = []
    t0 = time.time()
    for _ in range(max_messages):
        if max_seconds and (time.time() - t0) >= max_seconds:
            break
        if not hasattr(ex, method):
            raise AttributeError(f"Exchange '{ex.id}' has no method '{method}'")
        fn = getattr(ex, method)
        snap = await fn(*args_list, **kwargs_dict)
        out.append({"ts": int(time.time() * 1000), "data": _redact(snap)})
    return out


@tool
def ccxt_pro_watch(
    exchange: str = None,
    method: str = None,
    args: str = None,
    kwargs: str = None,
    config: str = None,
    max_messages: int = 5,
    max_seconds: int = 15,
) -> Dict[str, Any]:
    """Call ccxt.pro watch_* methods and return a bounded list of snapshots.

    Requires: pip install ccxtpro

    Example:
      ccxt_pro_watch(exchange="bybit", method="watch_ticker", args='["BTC/USDT"]', max_messages=3)
    """
    try:
        if not method:
            raise ValueError("method is required")
        exchange_id = (exchange or os.getenv("CCXT_EXCHANGE"))
        if not exchange_id:
            raise ValueError("exchange is required (or set CCXT_EXCHANGE)")

        ccxtpro = _import_ccxtpro()
        if not hasattr(ccxtpro, exchange_id):
            raise ValueError(f"Unknown exchange '{exchange_id}' in ccxt.pro")

        # build exchange (reuse env logic)
        cls = getattr(ccxtpro, exchange_id)
        cfg: Dict[str, Any] = {
            "enableRateLimit": True,
            "timeout": int(os.getenv("CCXT_TIMEOUT", "30000")),
        }
        api_key = os.getenv("CCXT_API_KEY")
        secret = os.getenv("CCXT_SECRET")
        if not api_key:
            api_key = os.getenv(f"{exchange_id.upper()}_API_KEY")
        if not secret:
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
        default_type = os.getenv("CCXT_DEFAULT_TYPE")
        if default_type:
            cfg.setdefault("options", {})
            cfg["options"].setdefault("defaultType", default_type)
        user_cfg = _json_load_maybe(config)
        if isinstance(user_cfg, dict):
            cfg.update(user_cfg)

        ex = cls(cfg)
        if os.getenv("CCXT_SANDBOX", "false").lower() == "true" and hasattr(ex, "set_sandbox_mode"):
            ex.set_sandbox_mode(True)

        parsed_args = _json_load_maybe(args)
        parsed_kwargs = _json_load_maybe(kwargs)
        if parsed_args is None:
            parsed_args = []
        if isinstance(parsed_args, str):
            parsed_args = [parsed_args]
        if not isinstance(parsed_args, list):
            raise ValueError("args must be JSON array string")
        if parsed_kwargs is None:
            parsed_kwargs = {}
        if not isinstance(parsed_kwargs, dict):
            raise ValueError("kwargs must be JSON object string")

        async def _run():
            try:
                snaps = await _ccxtpro_watch_loop(ex, method, parsed_args, parsed_kwargs, int(max_messages), int(max_seconds))
                return snaps
            finally:
                try:
                    await ex.close()
                except Exception:
                    pass

        snaps = asyncio.run(_run())

        payload = {
            "ok": True,
            "exchange": ex.id,
            "method": method,
            "count": len(snaps),
            "snapshots": snaps,
        }
        return {"status": "success", "content": [{"text": json.dumps(payload, indent=2)}]}

    except Exception as e:
        payload = {
            "ok": False,
            "exchange": exchange or os.getenv("CCXT_EXCHANGE"),
            "method": method,
            "error": f"{type(e).__name__}: {e}",
        }
        return {"status": "error", "content": [{"text": json.dumps(payload, indent=2)}]}
