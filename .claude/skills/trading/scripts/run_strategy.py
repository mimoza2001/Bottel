#!/usr/bin/env python3
"""
Trading strategy runner.
Usage: python run_strategy.py --exchange binance --symbol BTC/USDT --timeframe 1h
"""
import argparse
import ccxt
import pandas as pd
import os
import sys
from dotenv import load_dotenv

load_dotenv()


def parse_args():
    p = argparse.ArgumentParser(description='Run a trading strategy')
    p.add_argument('--exchange', default='binance', help='CCXT exchange id')
    p.add_argument('--symbol', default='BTC/USDT', help='Trading pair')
    p.add_argument('--timeframe', default='1h', help='Candle timeframe')
    p.add_argument('--limit', type=int, default=200, help='Number of candles')
    p.add_argument('--dry-run', action='store_true', help='Print signal only, no orders')
    return p.parse_args()


def build_exchange(exchange_id: str) -> ccxt.Exchange:
    cls = getattr(ccxt, exchange_id)
    ex = cls({
        'apiKey': os.getenv('EXCHANGE_API_KEY'),
        'secret': os.getenv('EXCHANGE_SECRET'),
        'passphrase': os.getenv('EXCHANGE_PASSPHRASE', ''),
        'enableRateLimit': True,
    })
    ex.set_sandbox_mode(True)  # SAFETY: always sandbox by default
    return ex


def fetch_ohlcv(ex: ccxt.Exchange, symbol: str, tf: str, limit: int) -> pd.DataFrame:
    raw = ex.fetch_ohlcv(symbol, tf, limit=limit)
    df = pd.DataFrame(raw, columns=['ts', 'open', 'high', 'low', 'close', 'volume'])
    df['ts'] = pd.to_datetime(df['ts'], unit='ms')
    return df.set_index('ts')


def sma_crossover_signal(df: pd.DataFrame) -> int:
    """Returns 1=buy, -1=sell, 0=flat"""
    df = df.copy()
    df['sma20'] = df['close'].rolling(20).mean()
    df['sma50'] = df['close'].rolling(50).mean()
    last = df.iloc[-1]
    if last['sma20'] > last['sma50']:
        return 1
    if last['sma20'] < last['sma50']:
        return -1
    return 0


def main():
    args = parse_args()
    ex = build_exchange(args.exchange)

    print(f'Fetching {args.symbol} {args.timeframe} candles from {args.exchange}...')
    df = fetch_ohlcv(ex, args.symbol, args.timeframe, args.limit)

    signal = sma_crossover_signal(df)
    labels = {1: 'BUY', -1: 'SELL', 0: 'FLAT'}
    print(f'Signal: {labels[signal]}')
    print(f'Last close: {df["close"].iloc[-1]}')

    if args.dry_run or signal == 0:
        print('Dry run — no order placed.')
        return

    amount = float(os.getenv('TRADE_AMOUNT', '0.001'))
    try:
        if signal == 1:
            order = ex.create_market_buy_order(args.symbol, amount)
        else:
            order = ex.create_market_sell_order(args.symbol, amount)
        print(f'Order placed: {order}')
    except Exception as e:
        print(f'Order failed: {e}', file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
