# Trading Skills Suite

A comprehensive set of AI-powered trading analysis skills for market analysis, strategy backtesting, and portfolio management.

## Available Commands

- `/trading-analysis` — Real-time market analysis with technical + fundamental signals
- `/backtest-strategy` — Backtest a trading strategy against historical data
- `/portfolio-check` — Assess current portfolio risk, exposure, and rebalancing needs
- `/sector-analyst` — Deep sector rotation and relative strength analysis
- `/options-advisor` — Options strategy selection and risk/reward profiling
- `/macro-regime` — Macro regime detection (risk-on vs risk-off, inflation, rates)

## Setup

Install dependencies:
```bash
pip install yfinance pandas ta-lib alpaca-trade-api requests python-dotenv
```

Required environment variables in `.env`:
```
ALPACA_API_KEY=your_key
ALPACA_SECRET_KEY=your_secret
ALPACA_BASE_URL=https://paper-api.alpaca.markets   # use live URL for real trading
ALPHA_VANTAGE_API_KEY=your_key
POLYGON_API_KEY=your_key
```

## Sources

Based on [tradermonty/claude-trading-skills](https://github.com/tradermonty/claude-trading-skills) and [quant-sentiment-ai/claude-equity-research](https://github.com/quant-sentiment-ai/claude-equity-research).

> **Disclaimer:** All trading skills are for educational and research purposes only. Nothing here constitutes financial advice.
