# CCXT Tools (for Strands Agents)

A community tool package that exposes **CCXT** (and optional **CCXT Pro**) to Strands Agents via `@tool` wrappers.

- Generic method calling: `fetch_*`, `create_order`, `cancel_order`, etc.
- Optional real-time WebSocket streaming via `ccxt.pro` (`watch_*`).

## Install

```bash
pip install ccxt-tool-strands
```

## Usage in a Strands Agent

```python
from strands import Agent

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

Set environment variables in the **agent runtime** (shell, `.zshrc`, `.env`, secret manager):

```bash
export CCXT_EXCHANGE=bybit   # or binance, okx, coinbase, ...
export CCXT_API_KEY=...
export CCXT_SECRET=...

# optional (only if your exchange requires them)
export CCXT_PASSWORD=...
export CCXT_UID=...
export CCXT_TOKEN=...
export CCXT_DEFAULT_TYPE=swap   # or spot
export CCXT_SANDBOX=false
```

Then you can omit `exchange=` and call authenticated methods:

```python
agent.tool.ccxt_generic(action="call", method="fetch_balance")
```

## Notes

- Keep API keys **out of code** and **out of git**.
- CCXT `enableRateLimit=True` is enabled by default in the tool.

## Links

- CCXT: https://github.com/ccxt/ccxt
- Strands community tools: https://strandsagents.com/latest/documentation/docs/community/tools
