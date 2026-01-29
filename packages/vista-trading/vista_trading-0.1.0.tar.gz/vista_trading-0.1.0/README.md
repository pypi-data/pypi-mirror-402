# Vista Trading

AI-powered crypto trading terminal for Hyperliquid.

## Installation

```bash
pip install vista-trading
```

## Quick Start

```bash
vista
```

On first run, Vista will guide you through:
1. Creating an account (or logging in)
2. Connecting your Hyperliquid wallet
3. Setting up your trading preferences

## Features

- 🤖 **AI-Powered Analysis** - DeepSeek AI analyzes markets and makes trading decisions
- 💬 **Natural Language Trading** - Chat with Vista to execute trades
- 📊 **Live Market Data** - Real-time prices via WebSocket
- 📈 **Technical Analysis** - RSI, MACD, EMA, Bollinger Bands, and more
- 🔔 **Price Alerts** - Get notified when prices hit your targets
- 🛡️ **Risk Management** - Built-in stop-loss and take-profit
- 🐋 **Whale Tracking** - Monitor large trader activity

## Commands

Once in the terminal, you can:

```
> what's the price of BTC?
> analyze ETH for a potential long
> show my positions
> set alert BTC 100000
> long SOL 50 USD 5x
> close my ETH position
```

## Requirements

- Python 3.9+
- Hyperliquid account with API wallet

## Security

- Your API keys are stored locally in `~/.vista/`
- AI calls go through secure proxy (keys never exposed)
- Row-level security protects your data

## License

MIT

