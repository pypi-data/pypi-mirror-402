# ccxt-tool-strands

CCXT + (optional) CCXT Pro tools for Strands/DevDuck.

This repo ships Strands `@tool` wrappers that let your agent call **any** CCXT exchange method (`fetch_*`, `create_order`, etc.) via a single tool entrypoint.

## What’s inside

- `tools/ccxt_generic.py`
  - `ccxt_generic(...)` — call *any* ccxt exchange method (sync)
  - `ccxt_multi_exchange_orderbook(...)` — compare best bid/ask across exchanges
  - `ccxt_pro_watch(...)` — call ccxt.pro `watch_*` methods (optional)

## Install

### Base (CCXT)

```bash
pip install ccxt-tool-strands
```

This installs:
- `ccxt`
- `strands-agents` (provides the `strands` Python module)

### Optional: CCXT Pro (WebSocket / `watch_*`)

CCXT Pro (real-time WebSocket `watch_*`) is shipped as a separate distribution by CCXT and is not reliably installable from public PyPI.

This tool will try to import `ccxt.pro` (recommended). If you have CCXT Pro installed in your environment, `ccxt_pro_watch(...)` works. Otherwise it returns a clear ImportError message.

See CCXT Pro docs: https://github.com/ccxt/ccxt/wiki/ccxt.pro.manual


## Using with DevDuck / Strands

Assuming your agent loads tools from `./tools` (DevDuck default when `DEVDUCK_LOAD_TOOLS_FROM_DIR=true`).

### Public calls

```python
ccxt_generic(action="call", exchange="bybit", method="fetch_ticker", args='["BTC/USDT"]')
ccxt_generic(action="call", exchange="bybit", method="fetch_ohlcv", args='["BTC/USDT","1m",null,200]')
ccxt_generic(action="list_methods", exchange="bybit")
```

### Authenticated calls (server-side env)

Set environment variables:

```bash
export CCXT_EXCHANGE=bybit
export CCXT_API_KEY=...
export CCXT_SECRET=...
# optional
export CCXT_PASSWORD=...
export CCXT_UID=...
export CCXT_TOKEN=...
export CCXT_DEFAULT_TYPE=swap   # or spot
export CCXT_SANDBOX=true        # optional
```

Then:

```python
ccxt_generic(action="call", method="fetch_balance")
```

### CCXT Pro watch example

```python
ccxt_pro_watch(
  exchange="bybit",
  method="watch_ticker",
  args='["BTC/USDT"]',
  max_messages=3,
  max_seconds=15,
)
```

## Notes

- Outputs redact common secret fields.
- `enableRateLimit=True` by default.
- Browser-side API keys are unsafe; keep keys server-side.
