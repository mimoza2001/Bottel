---
name: trading
description: >
  Crypto and stock trading automation. Use this skill when the user wants to:
  connect to crypto exchanges, fetch market data (OHLCV, order books, tickers),
  place or cancel orders, manage positions, run trading strategies, implement
  technical indicators, backtest strategies, or monitor portfolio PnL.
  Supports CCXT for 100+ exchanges (Binance, Bybit, Coinbase, Kraken, OKX, etc.)
  and yfinance for stock market data.
tools:
  - Bash
  - Read
  - Write
  - Edit
---

# Trading Skill

You are a professional algorithmic trading engineer. When invoked, help the user
build, run, and monitor trading bots and strategies.

## Setup & Dependencies

Before running any trading code, ensure dependencies are installed:

```bash
pip install ccxt python-dotenv pandas numpy ta websockets aiohttp
pip install yfinance  # for stock/ETF market data
```

Store API keys in a `.env` file (NEVER hard-code them):
```
EXCHANGE_API_KEY=your_key
EXCHANGE_SECRET=your_secret
EXCHANGE_PASSPHRASE=your_passphrase   # OKX, Coinbase only
```

## Exchange Connection Pattern

```python
import ccxt, os
from dotenv import load_dotenv

load_dotenv()

exchange = ccxt.binance({           # swap for bybit, okx, kraken, coinbase, etc.
    'apiKey': os.getenv('EXCHANGE_API_KEY'),
    'secret': os.getenv('EXCHANGE_SECRET'),
    'enableRateLimit': True,        # REQUIRED – respects exchange rate limits
    'options': {'defaultType': 'future'},  # 'spot' | 'future' | 'margin'
})
```

## Core Operations

### Market Data
```python
# Ticker (last price, bid, ask, volume)
ticker = exchange.fetch_ticker('BTC/USDT')

# OHLCV candles
ohlcv = exchange.fetch_ohlcv('BTC/USDT', timeframe='1h', limit=200)
# returns: [[timestamp, open, high, low, close, volume], ...]

# Order book
book = exchange.fetch_order_book('BTC/USDT', limit=20)
```

### Order Placement
```python
# Market order
order = exchange.create_market_buy_order('BTC/USDT', amount=0.001)
order = exchange.create_market_sell_order('BTC/USDT', amount=0.001)

# Limit order
order = exchange.create_limit_buy_order('BTC/USDT', amount=0.001, price=60000)

# Stop-loss (exchange-dependent, use params dict)
order = exchange.create_order('BTC/USDT', 'stop_market', 'sell', 0.001,
                               params={'stopPrice': 58000})
```

### Portfolio & Positions
```python
balance   = exchange.fetch_balance()
positions = exchange.fetch_positions(['BTC/USDT'])
orders    = exchange.fetch_open_orders('BTC/USDT')
exchange.cancel_order(order_id, 'BTC/USDT')
```

## Strategy Template

```python
import ccxt, pandas as pd, os
from dotenv import load_dotenv

load_dotenv()
exchange = ccxt.binance({'apiKey': os.getenv('EXCHANGE_API_KEY'),
                          'secret': os.getenv('EXCHANGE_SECRET'),
                          'enableRateLimit': True})

def get_df(symbol='BTC/USDT', tf='1h', limit=200):
    raw = exchange.fetch_ohlcv(symbol, tf, limit=limit)
    df = pd.DataFrame(raw, columns=['ts','open','high','low','close','volume'])
    df['ts'] = pd.to_datetime(df['ts'], unit='ms')
    return df.set_index('ts')

def sma_crossover(df):
    df['sma20'] = df['close'].rolling(20).mean()
    df['sma50'] = df['close'].rolling(50).mean()
    df['signal'] = 0
    df.loc[df['sma20'] > df['sma50'], 'signal'] = 1   # long
    df.loc[df['sma20'] < df['sma50'], 'signal'] = -1  # short
    return df

df = get_df()
df = sma_crossover(df)
latest_signal = df['signal'].iloc[-1]
print('Signal:', 'BUY' if latest_signal == 1 else 'SELL' if latest_signal == -1 else 'FLAT')
```

## Risk Management Rules

Always apply these rules before placing any live order:

1. **Position sizing**: never risk more than 1-2% of portfolio per trade.
2. **Stop-loss**: always define a stop-loss at order creation time.
3. **Sandbox first**: use exchange testnet/sandbox environment before going live.
   ```python
   exchange.set_sandbox_mode(True)   # Binance Testnet
   ```
4. **Rate limits**: always set `enableRateLimit: True`.
5. **Error handling**: wrap order calls in try/except and log all exceptions.

## Telegram Notification Integration

Since this project is a Telegram bot, send trade alerts via the bot:

```python
import requests

def notify(msg: str, token: str, chat_id: str):
    url = f'https://api.telegram.org/bot{token}/sendMessage'
    requests.post(url, json={'chat_id': chat_id, 'text': msg, 'parse_mode': 'Markdown'})

notify(f'*BTC/USDT* signal: *{latest_signal}*', token, chat_id)
```

## References

- `references/ccxt-api.md` — full CCXT API reference (load on demand)
- `references/indicators.md` — technical indicator recipes
- https://docs.ccxt.com
