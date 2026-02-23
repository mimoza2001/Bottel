# Technical Indicator Recipes

Load this file when the user asks for technical analysis indicators.

## Using the `ta` library

```bash
pip install ta
```

```python
import ta

# RSI
df['rsi'] = ta.momentum.RSIIndicator(df['close'], window=14).rsi()

# MACD
macd = ta.trend.MACD(df['close'])
df['macd'] = macd.macd()
df['macd_signal'] = macd.macd_signal()
df['macd_diff'] = macd.macd_diff()

# Bollinger Bands
bb = ta.volatility.BollingerBands(df['close'], window=20, window_dev=2)
df['bb_upper'] = bb.bollinger_hband()
df['bb_mid']   = bb.bollinger_mavg()
df['bb_lower'] = bb.bollinger_lband()

# EMA
df['ema20'] = ta.trend.EMAIndicator(df['close'], window=20).ema_indicator()

# ATR (for stop-loss sizing)
df['atr'] = ta.volatility.AverageTrueRange(df['high'], df['low'], df['close']).average_true_range()
```

## Pure pandas / numpy (no extra deps)

```python
# SMA
df['sma20'] = df['close'].rolling(20).mean()

# EMA
df['ema20'] = df['close'].ewm(span=20, adjust=False).mean()

# Percent change
df['pct'] = df['close'].pct_change()

# Volatility (rolling std dev)
df['vol'] = df['close'].pct_change().rolling(20).std()
```

## Signal Generation Pattern

```python
def generate_signals(df):
    df = df.copy()
    df['rsi'] = ta.momentum.RSIIndicator(df['close']).rsi()
    df['signal'] = 0
    df.loc[df['rsi'] < 30, 'signal'] = 1   # oversold → buy
    df.loc[df['rsi'] > 70, 'signal'] = -1  # overbought → sell
    return df
```
