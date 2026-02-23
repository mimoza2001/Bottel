# CCXT API Quick Reference

Load this file only when you need detailed CCXT API details beyond what SKILL.md covers.

## Exchange IDs (most common)
`binance`, `bybit`, `okx`, `kraken`, `coinbase`, `kucoin`, `gateio`, `huobi`, `bitfinex`

## Market Types
- `spot` — buy/sell crypto directly
- `future` / `swap` — perpetual or dated futures (requires margin)
- `margin` — spot margin trading

Set via: `exchange.options['defaultType'] = 'future'`

## Timeframes
`1m`, `5m`, `15m`, `30m`, `1h`, `4h`, `1d`, `1w`

## Error Classes
```python
ccxt.NetworkError        # connectivity issues — retry
ccxt.ExchangeError       # exchange returned an error
ccxt.InvalidOrder        # bad order params
ccxt.InsufficientFunds   # not enough balance
ccxt.RateLimitExceeded   # too many requests
ccxt.AuthenticationError # bad API key / secret
```

## Async Usage (for high-frequency / multiple exchanges)
```python
import ccxt.async_support as ccxt_async
import asyncio

async def main():
    ex = ccxt_async.binance({'enableRateLimit': True})
    ticker = await ex.fetch_ticker('ETH/USDT')
    await ex.close()
    return ticker

asyncio.run(main())
```

## WebSocket Streams (ccxt.pro)
```python
import ccxt.pro as ccxtpro
import asyncio

async def stream():
    ex = ccxtpro.binance()
    while True:
        ticker = await ex.watch_ticker('BTC/USDT')
        print(ticker['last'])

asyncio.run(stream())
```

## Pagination for Historical Data
```python
since = exchange.parse8601('2024-01-01T00:00:00Z')
all_candles = []
while True:
    candles = exchange.fetch_ohlcv('BTC/USDT', '1d', since=since, limit=1000)
    if not candles:
        break
    all_candles += candles
    since = candles[-1][0] + 1
```
