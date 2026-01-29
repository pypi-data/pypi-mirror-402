# CCXT Tools (for Strands Agents)

A community tool package that exposes **CCXT** (and optional **CCXT Pro**) to Strands Agents via `@tool` wrappers.

- Generic method calling: `fetch_*`, `create_order`, `cancel_order`, etc.
- Optional real-time WebSocket streaming via `ccxt.pro` (`watch_*`).

## Install

```bash
pip install ccxt-tool-strands
```

### Optional: CCXT Pro

CCXT Pro is distributed separately by CCXT.

If you have it available in your environment, `ccxt_pro_watch(...)` will work.
If not, the tool returns a clear ImportError message.

## Tools

- `ccxt_generic(...)`
  - Call **any** CCXT exchange method.
- `ccxt_multi_exchange_orderbook(...)`
  - Compare best bid/ask across multiple exchanges.
- `ccxt_pro_watch(...)`
  - Call `ccxt.pro` `watch_*` methods (bounded snapshots).

## Usage in a Strands Agent

```python
from strands import Agent

# import tools from the installed package
from ccxt_tool_strands.ccxt_generic import ccxt_generic, ccxt_multi_exchange_orderbook
from ccxt_tool_strands.ccxt_pro import ccxt_pro_watch

agent = Agent(
    model="...",
    tools=[ccxt_generic, ccxt_multi_exchange_orderbook, ccxt_pro_watch],
)

# public market data
agent.tool.ccxt_generic(action="call", exchange="bybit", method="fetch_ticker", args='["BTC/USDT"]')
agent.tool.ccxt_generic(action="call", exchange="bybit", method="fetch_ohlcv", args='["BTC/USDT","1m",null,200]')

# multi-exchange best bid/ask
agent.tool.ccxt_multi_exchange_orderbook(exchanges='["binance","bybit","okx"]', symbol="BTC/USDT")
```

## Authentication (recommended: server-side)
### Which env var names should I use?

This package reads credentials **from environment variables** and passes them into CCXT.

- Primary (recommended, exchange-agnostic): `CCXT_API_KEY` / `CCXT_SECRET`
- Exchange selection: `CCXT_EXCHANGE` (e.g. `bybit`, `binance`, `okx`)

This means: **even if you switch exchanges, you keep using the same env var names** (`CCXT_API_KEY`, `CCXT_SECRET`). You only change `CCXT_EXCHANGE`.

If you already have exchange-specific variables in your shell (e.g. `BYBIT_API_KEY`), you can either:
1) Duplicate them into `CCXT_API_KEY`/`CCXT_SECRET` (simplest), or
2) Set small aliases in your shell:

```bash
export CCXT_API_KEY="$BYBIT_API_KEY"
export CCXT_SECRET="$BYBIT_API_SECRET"
export CCXT_EXCHANGE=bybit
```



Set environment variables in the agent runtime:

```bash
export CCXT_EXCHANGE=bybit
# Generic (exchange-agnostic) env vars used by ccxt-tool-strands
export CCXT_API_KEY=...
export CCXT_SECRET=...

# Optional convenience aliases (tool will also accept these)
# export BYBIT_API_KEY=...
# export BYBIT_API_SECRET=...
# export BINANCE_API_KEY=...
# export BINANCE_API_SECRET=...
# optional
export CCXT_PASSWORD=...
export CCXT_UID=...
export CCXT_TOKEN=...
export CCXT_DEFAULT_TYPE=swap   # or spot
export CCXT_SANDBOX=true        # optional
```

Then you can omit `exchange=` and call authenticated methods:

```python
agent.tool.ccxt_generic(action="call", method="fetch_balance")
```

## Notes

- **Secrets**: do not put API keys in client-side apps; keep them in the agent/server environment.
- **Rate limits**: CCXT `enableRateLimit=True` is enabled by default in the tool.

## Links

- CCXT: https://github.com/ccxt/ccxt
- Strands community tools: https://strandsagents.com/latest/documentation/docs/community/tools


<!-- auto-publish test: 2026-01-17T18:15:05.148445Z -->
