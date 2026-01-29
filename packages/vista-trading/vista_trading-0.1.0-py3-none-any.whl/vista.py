#!/usr/bin/env python3
"""
Vista - AI Trading Terminal

A Claude Code-style CLI for vibe trading. Natural language interface
for crypto trading on Hyperliquid.

Usage:
    vista                        # Interactive mode
    vista "what's BTC doing"     # Quick query
    vista login                  # Login to account
    vista logout                 # Logout
    vista config                 # Show current config
"""

import asyncio
import argparse
import logging
import os
import sys
from datetime import datetime
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field

from dotenv import load_dotenv
load_dotenv()

# Rich terminal UI (required)
try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
    from rich.text import Text
    from rich.progress import Progress, SpinnerColumn, TextColumn
    from rich.prompt import Prompt, Confirm
    from rich.markdown import Markdown
    RICH_AVAILABLE = True
except ImportError:
    print("Error: Vista requires the 'rich' library.")
    print("Install with: pip install rich")
    sys.exit(1)

# Setup logging (quiet by default)
logging.basicConfig(level=logging.WARNING, format='%(message)s')
logger = logging.getLogger(__name__)

# Console
console = Console()


@dataclass
class Tool:
    """Represents a tool Vista can use."""
    name: str
    description: str
    handler: Callable
    parameters: Dict[str, str] = field(default_factory=dict)
    requires_confirmation: bool = False


@dataclass
class Message:
    """A message in the conversation."""
    role: str  # 'user', 'assistant', 'system', 'tool_result'
    content: str
    timestamp: datetime = field(default_factory=datetime.utcnow)
    tool_calls: List[Dict] = field(default_factory=list)


class VistaCLI:
    """Interactive AI Trading Terminal."""

    def __init__(self):
        self.console = console
        self.conversation: List[Message] = []
        self.tools: Dict[str, Tool] = {}
        self.context: Dict[str, Any] = {}

        # Config (loaded from ~/.vista/)
        from src.vista_config import VistaConfig
        from src.vista_auth import VistaAuth
        self.config = VistaConfig.load()
        self.auth = VistaAuth()

        # Clients (lazy loaded)
        self._hl_client = None
        self._llm_service = None
        self._db = None

        # State
        self.running = False
        self.last_prices: Dict[str, float] = {}

        # Register tools
        self._register_tools()
        
    def _register_tools(self):
        """Register all available tools."""
        self.tools = {
            "get_price": Tool(
                name="get_price",
                description="Get current price for a cryptocurrency",
                handler=self._tool_get_price,
                parameters={"symbol": "Crypto symbol (BTC, ETH, SOL, etc.)"}
            ),
            "get_prices": Tool(
                name="get_prices",
                description="Get prices for all tracked symbols",
                handler=self._tool_get_prices,
            ),
            "get_positions": Tool(
                name="get_positions",
                description="Get current open positions and P&L",
                handler=self._tool_get_positions,
            ),
            "get_account": Tool(
                name="get_account",
                description="Get account balance and equity",
                handler=self._tool_get_account,
            ),
            "analyze_chart": Tool(
                name="analyze_chart",
                description="Run technical analysis on a symbol",
                handler=self._tool_analyze_chart,
                parameters={"symbol": "Symbol to analyze", "timeframe": "5m, 1h, or 1d"}
            ),
            "get_signals": Tool(
                name="get_signals",
                description="Get recent trading signals and their outcomes",
                handler=self._tool_get_signals,
            ),
            "place_order": Tool(
                name="place_order",
                description="Place a market order (REQUIRES CONFIRMATION)",
                handler=self._tool_place_order,
                parameters={"symbol": "Symbol", "side": "long or short", "size_usd": "Position size in USD"},
                requires_confirmation=True
            ),
            "close_position": Tool(
                name="close_position",
                description="Close an open position (REQUIRES CONFIRMATION)",
                handler=self._tool_close_position,
                parameters={"symbol": "Symbol to close"},
                requires_confirmation=True
            ),
            "generate_chart": Tool(
                name="generate_chart",
                description="Generate and save a chart image",
                handler=self._tool_generate_chart,
                parameters={"symbol": "Symbol", "timeframe": "5m or 1d"}
            ),
            # Dashboard
            "show_dashboard": Tool(
                name="show_dashboard",
                description="Launch full-screen trading dashboard with live charts, support/resistance, breakout analysis",
                handler=self._tool_show_dashboard,
                parameters={"symbol": "Symbol to display (BTC, ETH, SOL, etc.)"}
            ),
            # Market data tools
            "show_orderbook": Tool(
                name="show_orderbook",
                description="Show live orderbook with bid/ask depth visualization",
                handler=self._tool_show_orderbook,
                parameters={"symbol": "Symbol to show orderbook for"}
            ),
            "show_indicators": Tool(
                name="show_indicators",
                description="Show technical indicators: RSI, MACD, ATR, VWAP, moving averages",
                handler=self._tool_show_indicators,
                parameters={"symbol": "Symbol to analyze"}
            ),
            "run_backtest": Tool(
                name="run_backtest",
                description="Run a historical backtest on a strategy",
                handler=self._tool_run_backtest,
                parameters={"symbol": "Symbol", "strategy": "Strategy name (micro, scalp)", "start_date": "Start date YYYY-MM-DD", "end_date": "End date YYYY-MM-DD"}
            ),
            "toggle_paper_mode": Tool(
                name="toggle_paper_mode",
                description="Toggle paper trading mode (simulate trades without real money)",
                handler=self._tool_toggle_paper,
            ),
            "kill_switch": Tool(
                name="kill_switch",
                description="Emergency stop - halt all trading, close positions, or block certain trades",
                handler=self._tool_kill_switch,
                parameters={"action": "all (stop everything), longs (block longs), shorts (block shorts), off (resume)"}
            ),
            "bot_control": Tool(
                name="bot_control",
                description="Control the automated trading bot",
                handler=self._tool_bot_control,
                parameters={"action": "status, start, stop, restart"}
            ),
            "setup_bot": Tool(
                name="setup_bot",
                description="Configure and set up a new trading bot with custom settings",
                handler=self._tool_setup_bot,
            ),
        }

    # ==================== LAZY LOADING ====================

    @property
    def hl(self):
        """Lazy load Hyperliquid client using config."""
        if self._hl_client is None:
            from src.hyperliquid_client import HyperliquidClient
            self._hl_client = HyperliquidClient(
                private_key=self.config.hyperliquid_private_key,
                wallet_address=self.config.hyperliquid_wallet_address,
                testnet=self.config.hyperliquid_testnet
            )
        return self._hl_client

    @property
    def llm(self):
        """Lazy load LLM service using config (uses secure proxy)."""
        if self._llm_service is None:
            from src.llm_service import LLMService
            # Use proxy mode - DeepSeek key stays on server
            self._llm_service = LLMService(
                anthropic_api_key=self.config.anthropic_api_key or "dummy",
                deepseek_proxy_url=self.config.get_deepseek_proxy_url(),
                auth_token=self.auth.session.access_token
            )
        return self._llm_service

    @property
    def db(self):
        """Lazy load database."""
        if self._db is None:
            from src.database import get_db
            self._db = get_db()
        return self._db

    # ==================== TOOL IMPLEMENTATIONS ====================

    async def _tool_get_price(self, symbol: str) -> str:
        """Get price for a symbol."""
        price = self.hl.get_price(symbol.upper())
        if price:
            self.last_prices[symbol.upper()] = price
            return f"{symbol.upper()}: ${price:,.2f}"
        return f"Could not get price for {symbol}"

    async def _tool_get_prices(self) -> str:
        """Get all tracked prices."""
        from src.tickers import TRADING_TICKERS
        lines = []
        for sym in TRADING_TICKERS:
            price = self.hl.get_price(sym)
            if price:
                self.last_prices[sym] = price
                lines.append(f"  {sym}: ${price:,.2f}")
        return "Current Prices:\n" + "\n".join(lines)

    async def _tool_get_positions(self) -> str:
        """Get open positions."""
        state = self.hl.get_account_state()
        lines = ["Open Positions:"]
        has_pos = False
        for pos in state.get('positions', []):
            szi = float(pos.get('szi', 0) or 0)
            if szi != 0:
                has_pos = True
                coin = pos.get('coin', '?')
                entry = float(pos.get('entryPx', 0) or 0)
                current = self.hl.get_price(coin) or entry
                pnl_pct = ((current - entry) / entry * 100) if entry > 0 else 0
                if szi < 0:
                    pnl_pct = -pnl_pct
                unrealized = float(pos.get('unrealizedPnl', 0) or 0)
                side = "LONG" if szi > 0 else "SHORT"
                lines.append(f"  {coin}: {side} {abs(szi):.4f} @ ${entry:,.2f}")
                lines.append(f"    → ${current:,.2f} ({pnl_pct:+.2f}%) | P&L: ${unrealized:+.2f}")
        if not has_pos:
            lines.append("  No open positions")
        return "\n".join(lines)

    async def _tool_get_account(self) -> str:
        """Get account info."""
        state = self.hl.get_account_state()
        return f"""Account Summary:
  Equity: ${state['equity']:,.2f}
  Available: ${state['available_balance']:,.2f}
  Margin Used: ${state['equity'] - state['available_balance']:,.2f}"""

    async def _tool_analyze_chart(self, symbol: str, timeframe: str = "1h") -> str:
        """Run technical analysis."""
        from src.technical_analysis import detect_trendlines, calculate_support_resistance

        interval = {"5m": "5m", "1h": "1h", "1d": "1d", "daily": "1d"}.get(timeframe.lower(), "1h")
        limit = {"5m": 150, "1h": 100, "1d": 90}.get(interval, 100)

        candles = self.hl.get_candles(symbol.upper(), interval=interval, limit=limit)
        if not candles or len(candles) < 20:
            return f"Not enough data for {symbol} {timeframe}"

        trendlines = detect_trendlines(candles, lookback=50, min_touches=2)
        sr = calculate_support_resistance(candles, lookback=50)

        price = candles[-1]['close']
        signal = trendlines.get('signal', 'neutral')
        strength = trendlines.get('signal_strength', 0)
        trend = trendlines.get('trend_filter', 'unknown')
        valid = trendlines.get('signal_valid', True)

        supports = sr.get('supports', [])[:3]
        resistances = sr.get('resistances', [])[:3]

        lines = [
            f"📊 {symbol.upper()} {timeframe.upper()} Analysis:",
            f"  Price: ${price:,.2f}",
            f"  Trend: {trend.upper()}",
            f"  Signal: {signal} (strength: {strength:.0%})",
            f"  Valid: {'✅' if valid else '❌'} {trendlines.get('rejection_reason', '') or ''}",
            f"  Supports: {', '.join(f'${s:,.0f}' for s in supports)}",
            f"  Resistances: {', '.join(f'${r:,.0f}' for r in resistances)}",
        ]

        if trendlines.get('ascending_support'):
            asc = trendlines['ascending_support']
            lines.append(f"  📈 Ascending Support @ ${asc.get('current_price', 0):,.2f}")
        if trendlines.get('descending_resistance'):
            desc = trendlines['descending_resistance']
            lines.append(f"  📉 Descending Resistance @ ${desc.get('current_price', 0):,.2f}")

        return "\n".join(lines)

    async def _tool_get_signals(self) -> str:
        """Get recent signals and outcomes."""
        from datetime import timedelta
        cutoff = (datetime.utcnow() - timedelta(hours=24)).isoformat()

        with self.db._get_conn() as conn:
            signals = conn.execute('''
                SELECT symbol, direction, confidence, outcome_pct_1h, timestamp
                FROM chart_signals
                WHERE timestamp > ?
                ORDER BY timestamp DESC LIMIT 10
            ''', (cutoff,)).fetchall()

        if not signals:
            return "No recent signals"

        lines = ["Recent Signals (24h):"]
        for s in signals:
            outcome = s['outcome_pct_1h']
            emoji = "✅" if outcome and ((s['direction'] == 'bullish' and outcome > 0) or
                                         (s['direction'] == 'bearish' and outcome < 0)) else "❌" if outcome else "⏳"
            outcome_str = f"{outcome:+.2f}%" if outcome else "pending"
            lines.append(f"  {emoji} {s['symbol']} {s['direction']} ({s['confidence']:.0%}) → {outcome_str}")

        return "\n".join(lines)

    async def _tool_place_order(self, symbol: str, side: str, size_usd: float) -> str:
        """Place a market order."""
        import math

        symbol = symbol.upper()
        price = self.hl.get_price(symbol)
        if not price:
            return f"Could not get price for {symbol}"

        # Calculate size
        decimals_map = {"BTC": 5, "ETH": 4}
        decimals = decimals_map.get(symbol, 2)
        raw_size = float(size_usd) / price
        factor = 10 ** decimals
        size = math.ceil(raw_size * factor) / factor

        order_side = "buy" if side.lower() == "long" else "sell"

        result = self.hl.place_market_order(symbol, order_side, size)

        if result.get("success"):
            return f"✅ Order placed: {side.upper()} {size:.6f} {symbol} (~${size_usd})"
        else:
            return f"❌ Order failed: {result.get('error')}"

    async def _tool_close_position(self, symbol: str) -> str:
        """Close a position."""
        symbol = symbol.upper()
        result = self.hl.close_position(symbol)

        if result.get("success"):
            return f"✅ Closed {symbol} position"
        else:
            return f"❌ Close failed: {result.get('error')}"

    async def _tool_generate_chart(self, symbol: str, timeframe: str = "5m") -> str:
        """Launch live terminal chart."""
        symbol = symbol.upper()
        await self._run_live_chart(symbol, timeframe)
        return ""

    async def _run_live_chart(self, symbol: str, timeframe: str = "5m"):
        """Run live updating ASCII chart."""
        from rich.live import Live
        from rich.text import Text
        from datetime import datetime
        import asyncio

        interval = "1m"  # Use 1m for live updates

        self.console.print(f"\n[bold cyan]Live Chart: {symbol}[/] [dim](Press Ctrl+C to exit)[/]\n")

        try:
            with Live(self._build_chart_display(symbol, interval), refresh_per_second=1, console=self.console) as live:
                while True:
                    live.update(self._build_chart_display(symbol, interval))
                    await asyncio.sleep(2)  # Update every 2 seconds
        except KeyboardInterrupt:
            self.console.print("\n[dim]Chart closed[/]")

    def _build_chart_display(self, symbol: str, interval: str) -> Text:
        """Build the ASCII chart display."""
        from rich.text import Text
        from datetime import datetime

        # Get candles
        candles = self.hl.get_candles(symbol, interval=interval, limit=40)
        if not candles or len(candles) < 5:
            return Text(f"No data for {symbol}")

        closes = [c['close'] for c in candles]
        times = [datetime.fromtimestamp(c['time'] / 1000) for c in candles]

        # Chart dimensions
        height = 12
        width = min(len(closes), 50)

        # Sample if needed
        if len(closes) > width:
            step = len(closes) // width
            closes = closes[::step][:width]
            times = times[::step][:width]

        min_price = min(closes)
        max_price = max(closes)
        price_range = max_price - min_price
        if price_range == 0:
            price_range = max_price * 0.001  # 0.1% range if flat

        # Normalize prices to chart height
        normalized = [(p - min_price) / price_range * height for p in closes]

        # Build chart lines
        lines = []

        # Header
        current = closes[-1]
        change = ((closes[-1] - closes[0]) / closes[0] * 100) if closes[0] != 0 else 0
        change_sym = "▲" if change >= 0 else "▼"
        change_color = "green" if change >= 0 else "red"

        lines.append(f"  [bold cyan]{symbol}[/]  [bold white]${current:,.2f}[/]  [{change_color}]{change_sym} {abs(change):.2f}%[/]  [dim]{datetime.now().strftime('%H:%M:%S')}[/]")
        lines.append("")

        # Chart body with line drawing
        for row in range(height, -1, -1):
            # Y-axis label
            if row == height:
                line = f"[dim]{max_price:>10,.2f}[/] ┤"
            elif row == 0:
                line = f"[dim]{min_price:>10,.2f}[/] ┼"
            else:
                line = "            │"

            # Plot the line
            for i, val in enumerate(normalized):
                prev_val = normalized[i-1] if i > 0 else val

                # Determine what character to draw
                at_this_row = abs(val - row) < 0.5
                at_prev_row = abs(prev_val - row) < 0.5 if i > 0 else False
                above_line = val > row
                below_line = val < row

                if at_this_row:
                    if i == 0:
                        char = "─"
                    elif val > prev_val:
                        # Going up
                        if abs(prev_val - row) < 0.5:
                            char = "─"
                        else:
                            char = "┌" if row > prev_val else "─"
                    elif val < prev_val:
                        # Going down
                        if abs(prev_val - row) < 0.5:
                            char = "─"
                        else:
                            char = "└" if row < prev_val else "─"
                    else:
                        char = "─"

                    # Color based on direction
                    if i > 0 and closes[i] >= closes[i-1]:
                        line += f"[green]{char}[/]"
                    else:
                        line += f"[red]{char}[/]"
                elif i > 0 and ((prev_val > row > val) or (prev_val < row < val)):
                    # Vertical line connecting points
                    if closes[i] >= closes[i-1]:
                        line += f"[green]│[/]"
                    else:
                        line += f"[red]│[/]"
                else:
                    line += " "

            lines.append(line)

        # X-axis
        lines.append("            └" + "─" * len(closes))

        # Time labels
        if len(times) >= 4:
            time_line = "             "
            step = len(times) // 4
            for i in range(0, len(times), step):
                if i < len(times):
                    time_line += times[i].strftime("%H:%M").ljust(step)
            lines.append(f"[dim]{time_line}[/]")

        return Text.from_markup("\n".join(lines))

    # ==================== DASHBOARD TOOL HANDLER ====================

    async def _tool_show_dashboard(self, symbol: str = "BTC") -> str:
        """Launch the dashboard."""
        await self._run_dashboard(symbol.upper())
        return ""

    # ==================== MARKET DATA TOOL HANDLERS ====================

    async def _tool_show_orderbook(self, symbol: str) -> str:
        """Show orderbook."""
        return await self._show_orderbook(symbol.upper())

    async def _tool_show_indicators(self, symbol: str) -> str:
        """Show indicators."""
        return await self._show_indicators(symbol.upper())

    async def _tool_run_backtest(self, symbol: str, strategy: str = "micro", start_date: str = "2024-01-01", end_date: str = "2024-12-31") -> str:
        """Run backtest."""
        return await self._run_backtest(symbol.upper(), strategy, start_date, end_date)

    async def _tool_toggle_paper(self) -> str:
        """Toggle paper mode."""
        return self._toggle_paper_mode()

    async def _tool_kill_switch(self, action: str = "all") -> str:
        """Handle kill switch."""
        action = action.lower()
        if action == "off":
            # Turn off all kill switches
            self.kill_switches = {'all': False, 'longs': False, 'shorts': False}
            return "🟢 All kill switches [green]DEACTIVATED[/]. Trading resumed."
        return self._toggle_kill_switch(action)

    async def _tool_bot_control(self, action: str = "status") -> str:
        """Control trading bot."""
        action = action.lower()
        if action == "status":
            self._show_bot_status()
            return ""
        return await self._control_bot(action)

    async def _tool_setup_bot(self) -> str:
        """Launch interactive bot setup wizard."""
        await self._run_bot_setup()
        return ""

    async def _run_bot_setup(self):
        """Interactive bot configuration wizard."""
        from rich.prompt import Prompt, Confirm, IntPrompt, FloatPrompt
        from src.tickers import TRADING_TICKERS

        self.console.print()
        self.console.print("[bold cyan]🤖 Bot Setup Wizard[/]")
        self.console.print("[dim]Configure your automated trading bot[/]")
        self.console.print()

        # Strategy selection
        self.console.print("[bold]1. Choose Strategy[/]")
        self.console.print("   [cyan]micro[/]  - Quick scalps, small moves, high frequency")
        self.console.print("   [cyan]scalp[/]  - Short-term trades, 5-15 min holds")
        self.console.print("   [cyan]swing[/]  - Longer holds, bigger moves, lower frequency")
        self.console.print()

        strategy = Prompt.ask(
            "Strategy",
            choices=["micro", "scalp", "swing"],
            default=self.config.bot_strategy
        )

        # Symbol selection
        self.console.print()
        self.console.print("[bold]2. Select Trading Pairs[/]")
        self.console.print(f"   [dim]Available: {', '.join(TRADING_TICKERS[:10])}...[/]")
        self.console.print()

        symbols_input = Prompt.ask(
            "Symbols (comma-separated)",
            default=self.config.bot_symbols
        )
        symbols = [s.strip().upper() for s in symbols_input.split(",")]

        # Risk settings
        self.console.print()
        self.console.print("[bold]3. Risk Management[/]")
        self.console.print()

        position_size = FloatPrompt.ask(
            "Position size (USD per trade)",
            default=self.config.position_size_usd
        )

        max_leverage = FloatPrompt.ask(
            "Max leverage",
            default=self.config.bot_max_leverage
        )

        max_positions = IntPrompt.ask(
            "Max concurrent positions",
            default=self.config.bot_max_positions
        )

        stop_loss = FloatPrompt.ask(
            "Stop loss %",
            default=self.config.bot_stop_loss_pct
        )

        take_profit = FloatPrompt.ask(
            "Take profit %",
            default=self.config.bot_take_profit_pct
        )

        # Network
        self.console.print()
        self.console.print("[bold]4. Network[/]")
        testnet = Confirm.ask(
            "Use testnet? (paper money)",
            default=self.config.hyperliquid_testnet
        )

        # Summary
        self.console.print()
        self.console.print("[bold]📋 Bot Configuration Summary[/]")

        table = Table(border_style="dim")
        table.add_column("Setting", style="cyan")
        table.add_column("Value")

        table.add_row("Strategy", strategy)
        table.add_row("Symbols", ", ".join(symbols))
        table.add_row("Position Size", f"${position_size:.2f}")
        table.add_row("Max Leverage", f"{max_leverage}x")
        table.add_row("Max Positions", str(max_positions))
        table.add_row("Stop Loss", f"{stop_loss}%")
        table.add_row("Take Profit", f"{take_profit}%")
        table.add_row("Network", "Testnet" if testnet else "Mainnet")

        self.console.print(table)
        self.console.print()

        # Confirm
        if Confirm.ask("[bold]Save this configuration?[/]", default=True):
            # Save to config
            self.config.bot_strategy = strategy
            self.config.bot_symbols = ",".join(symbols)
            self.config.position_size_usd = position_size
            self.config.bot_max_leverage = max_leverage
            self.config.bot_max_positions = max_positions
            self.config.bot_stop_loss_pct = stop_loss
            self.config.bot_take_profit_pct = take_profit
            self.config.hyperliquid_testnet = testnet
            self.config.save()

            # Sync to cloud
            from src.vista_auth import VistaAuth
            auth = VistaAuth()
            await auth.sync_settings_to_cloud()

            self.console.print("[green]✓ Bot configuration saved and synced![/]")
            self.console.print()

            # Ask to start
            if Confirm.ask("Start the bot now?", default=False):
                await self._start_configured_bot()
        else:
            self.console.print("[dim]Setup cancelled[/]")

    async def _start_configured_bot(self):
        """Start the bot with saved configuration."""
        import subprocess
        import os

        # Build environment variables from config
        env = os.environ.copy()
        env["HYPERLIQUID_PRIVATE_KEY"] = self.config.hyperliquid_private_key
        env["HYPERLIQUID_WALLET_ADDRESS"] = self.config.hyperliquid_wallet_address
        env["HYPERLIQUID_TESTNET"] = "true" if self.config.hyperliquid_testnet else "false"
        # For the trading bot, we pass through DEEPSEEK_API_KEY from the environment
        # This should be set by the user who runs the bot server-side
        env["DEEPSEEK_API_KEY"] = os.getenv("DEEPSEEK_API_KEY", "")
        env["POSITION_SIZE_USD"] = str(self.config.position_size_usd)
        env["MAX_LEVERAGE"] = str(self.config.bot_max_leverage)
        env["TRADING_SYMBOLS"] = self.config.bot_symbols

        self.console.print("[cyan]🚀 Starting bot...[/]")

        # Start bot in background
        subprocess.Popen(
            ['python3', 'run.py'],
            env=env,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )

        self.console.print("[green]✓ Bot started in background[/]")
        self.console.print("[dim]Use 'bot status' to check, 'bot stop' to stop[/]")

    # ==================== AI CONVERSATION ====================

    def _build_system_prompt(self) -> str:
        """Build the system prompt for Vista."""
        tools_desc = "\n".join([
            f"- {name}: {tool.description}" +
            (f" (params: {tool.parameters})" if tool.parameters else "")
            for name, tool in self.tools.items()
        ])

        return f"""You are Vista, an AI crypto trading assistant for Hyperliquid perpetuals.
You understand natural language completely - users can talk to you however they want.

PERSONALITY:
- You're a knowledgeable trading buddy, not a robot
- Have real conversations - explain your thinking, share insights, give opinions
- Use trading language naturally (longs, shorts, leverage, liquidation, etc)
- When asked for analysis, go deep - explain the setup, risks, what you're seeing
- When asked simple questions, keep it natural but informative
- Use emojis naturally 📈 📉 🎯 ⚠️ 💰

CONVERSATION STYLE:
- If someone asks "what do you think about BTC?" - give a real opinion with reasoning
- If someone asks "should I long here?" - discuss the setup, risks, and your take
- If someone wants to chat about markets, engage naturally
- You can ask clarifying questions if needed
- Remember context from the conversation

REAL-TIME DATA:
You have LIVE market data injected below (prices, positions, account). Reference it naturally!

TOOLS:
{tools_desc}

To use a tool: [[TOOL:tool_name:param1=value1,param2=value2]]

NATURAL LANGUAGE UNDERSTANDING - Map user intent to tools:

DASHBOARD & VISUALIZATION:
- "show me the dashboard" / "open dashboard" / "trading terminal" / "full screen" → [[TOOL:show_dashboard:symbol=BTC]]
- "show dashboard for ETH" / "ETH dashboard" / "let me see ethereum" → [[TOOL:show_dashboard:symbol=ETH]]
- "what's the orderbook" / "show bids and asks" / "depth chart" / "liquidity" → [[TOOL:show_orderbook:symbol=BTC]]
- "SOL orderbook" / "orderbook for solana" → [[TOOL:show_orderbook:symbol=SOL]]
- "show me the indicators" / "RSI?" / "what's the MACD" / "technicals" → [[TOOL:show_indicators:symbol=BTC]]
- "ETH indicators" / "show me ETH RSI" → [[TOOL:show_indicators:symbol=ETH]]

ANALYSIS:
- "analyze BTC" / "what do you think of bitcoin" / "BTC setup?" → [[TOOL:analyze_chart:symbol=BTC,timeframe=1h]]
- "5 minute chart" / "short term ETH" → [[TOOL:analyze_chart:symbol=ETH,timeframe=5m]]
- "generate chart" / "save chart" / "chart image" → [[TOOL:generate_chart:symbol=BTC,timeframe=5m]]

TRADING:
- "go long BTC $100" / "buy bitcoin $100" / "long 100 bucks of BTC" → [[TOOL:place_order:symbol=BTC,side=long,size_usd=100]]
- "short ETH $50" / "sell ethereum" → [[TOOL:place_order:symbol=ETH,side=short,size_usd=50]]
- "close my BTC" / "exit bitcoin" / "get out of BTC" → [[TOOL:close_position:symbol=BTC]]
- "close everything" / "flatten" → Close all positions one by one

BACKTESTING & SIMULATION:
- "backtest BTC" / "test the strategy" / "how would micro do on BTC" → [[TOOL:run_backtest:symbol=BTC,strategy=micro]]
- "backtest SOL scalp from jan to june" → [[TOOL:run_backtest:symbol=SOL,strategy=scalp,start_date=2024-01-01,end_date=2024-06-30]]
- "paper trading" / "practice mode" / "simulate" / "demo mode" → [[TOOL:toggle_paper_mode]]

BOT SETUP & CONTROL:
- "set up a bot" / "configure bot" / "create a trading bot" / "I want to automate" → [[TOOL:setup_bot]]
- "help me set up automated trading" / "bot wizard" → [[TOOL:setup_bot]]
- "stop everything" / "emergency stop" / "kill it" / "halt trading" → [[TOOL:kill_switch:action=all]]
- "no more longs" / "block long positions" → [[TOOL:kill_switch:action=longs]]
- "no more shorts" / "block shorts" → [[TOOL:kill_switch:action=shorts]]
- "resume trading" / "turn off kill switch" / "start again" → [[TOOL:kill_switch:action=off]]
- "is the bot running" / "bot status" / "what's the bot doing" → [[TOOL:bot_control:action=status]]
- "start the bot" / "turn on bot" / "begin trading" → [[TOOL:bot_control:action=start]]
- "stop the bot" / "turn off bot" → [[TOOL:bot_control:action=stop]]

INFO:
- "what's BTC at" / "bitcoin price" → Answer from context (you have prices!)
- "my positions" / "what am I holding" / "exposure" → Answer from context
- "account" / "balance" / "how much do I have" → Answer from context
- "recent trades" / "signals" / "what happened" → [[TOOL:get_signals]]

RULES:
- Always confirm before executing trades
- Extract the symbol from context (if they say "ethereum" that's ETH)
- Default to BTC if no symbol specified
- Be helpful, not pedantic about syntax"""

    def _build_market_context(self) -> str:
        """Build real-time market context from WebSocket and SQLite."""
        from src.tickers import TRADING_TICKERS
        context_parts = []

        # 1. Live prices from WebSocket
        prices_lines = []
        for sym in TRADING_TICKERS[:10]:  # Top 10 tickers
            try:
                price = self.hl.get_price(sym)
                if price:
                    self.last_prices[sym] = price
                    # Get 24h change if available
                    prices_lines.append(f"  {sym}: ${price:,.2f}")
            except:
                pass

        if prices_lines:
            context_parts.append("📊 LIVE PRICES:\n" + "\n".join(prices_lines))

        # 2. Current positions
        try:
            state = self.hl.get_account_state()
            positions = state.get('positions', [])
            if positions:
                pos_lines = []
                for p in positions:
                    sym = p.get('symbol', '')
                    size = float(p.get('size', 0))
                    entry = float(p.get('entry_price', 0))
                    pnl = float(p.get('unrealized_pnl', 0))
                    side = "LONG" if size > 0 else "SHORT"
                    pos_lines.append(f"  {sym}: {side} {abs(size)} @ ${entry:,.2f} (PnL: ${pnl:+,.2f})")
                context_parts.append("📈 YOUR POSITIONS:\n" + "\n".join(pos_lines))
            else:
                context_parts.append("📈 POSITIONS: None open")

            # Account equity
            equity = float(state.get('equity', 0))
            available = float(state.get('available_balance', 0))
            context_parts.append(f"💰 ACCOUNT: ${equity:,.2f} equity, ${available:,.2f} available")
        except Exception as e:
            pass

        # 3. Recent trades from SQLite
        try:
            recent_trades = self.db.get_recent_trades(limit=5)
            if recent_trades:
                trade_lines = []
                for t in recent_trades:
                    trade_lines.append(f"  {t['timestamp'][:10]}: {t['symbol']} {t['side']} @ ${t['price']:,.2f} ({t['pnl']:+.2f})")
                context_parts.append("📜 RECENT TRADES:\n" + "\n".join(trade_lines))
        except:
            pass

        # 4. Market regime (if cached)
        # This gives the AI context about current market conditions

        return "\n\n".join(context_parts) if context_parts else ""

    async def _call_llm(self, user_message: str) -> str:
        """Call the LLM with conversation context and live market data."""
        # Build real-time market context
        market_context = self._build_market_context()

        # Build system prompt with injected market data
        system_prompt = self._build_system_prompt()
        if market_context:
            system_prompt += f"\n\n--- CURRENT MARKET STATE ---\n{market_context}\n--- END MARKET STATE ---"

        # Build messages
        messages = [{"role": "system", "content": system_prompt}]

        # Add recent conversation history (last 10 messages)
        for msg in self.conversation[-10:]:
            messages.append({"role": msg.role, "content": msg.content})

        # Add new user message
        messages.append({"role": "user", "content": user_message})

        # Call DeepSeek (cheap and fast)
        response = self.llm.deepseek_client.chat.completions.create(
            model="deepseek-chat",
            messages=messages,
            max_tokens=2000,  # Allow longer conversational responses
            temperature=0.7   # More natural/creative responses
        )

        return response.choices[0].message.content.strip()

    async def _process_response(self, response: str) -> str:
        """Process LLM response and execute any tool calls."""
        import re

        # Find tool calls in response
        tool_pattern = r'\[\[TOOL:(\w+)(?::([^\]]+))?\]\]'
        matches = re.findall(tool_pattern, response)

        if not matches:
            return response

        # Execute each tool call
        results = []
        for tool_name, params_str in matches:
            if tool_name not in self.tools:
                results.append(f"❌ Unknown tool: {tool_name}")
                continue

            tool = self.tools[tool_name]

            # Parse parameters
            params = {}
            if params_str:
                for param in params_str.split(','):
                    if '=' in param:
                        k, v = param.split('=', 1)
                        params[k.strip()] = v.strip()

            # Check confirmation for dangerous operations
            if tool.requires_confirmation:
                if RICH_AVAILABLE:
                    confirm = Prompt.ask(
                        f"⚠️  Execute {tool_name}({params})? [y/N]",
                        default="n"
                    )
                else:
                    confirm = input(f"⚠️  Execute {tool_name}({params})? [y/N]: ").strip().lower()

                if confirm.lower() != 'y':
                    results.append(f"❌ Cancelled: {tool_name}")
                    continue

            # Execute tool
            try:
                if RICH_AVAILABLE:
                    with Progress(
                        SpinnerColumn(),
                        TextColumn(f"[cyan]Running {tool_name}...[/]"),
                        console=self.console,
                        transient=True
                    ) as progress:
                        progress.add_task("", total=None)
                        result = await tool.handler(**params)
                else:
                    print(f"Running {tool_name}...")
                    result = await tool.handler(**params)

                results.append(result)
            except Exception as e:
                results.append(f"❌ Error in {tool_name}: {e}")

        # Remove tool calls from response and append results
        clean_response = re.sub(tool_pattern, '', response).strip()

        if clean_response and results:
            return clean_response + "\n\n" + "\n\n".join(results)
        elif results:
            return "\n\n".join(results)
        else:
            return clean_response

    # ==================== MAIN LOOP ====================

    def _print_welcome(self):
        """Print welcome message with gradient logo."""
        user_email = self.config.user_email or "trader"
        network = "testnet" if self.config.hyperliquid_testnet else "mainnet"

        # Two slanted bars \\ with cyan-to-orange gradient (Vista logo)
        self.console.print()
        self.console.print("[bright_cyan]                 ██╗      ██╗[/]")
        self.console.print("[cyan]                 ╚██╗    ██╔╝[/]")
        self.console.print("[blue]                  ╚██╗  ██╔╝[/]")
        self.console.print("[yellow]                   ╚██╗██╔╝[/]")
        self.console.print("[orange1]                    ╚███╔╝[/]")
        self.console.print("[dark_orange]                     ╚══╝[/]")
        self.console.print()
        self.console.print("[bold bright_cyan]              V I S T A[/]")
        self.console.print()
        self.console.print(f"[dim]            {user_email} • {network}[/]")
        self.console.print()
        self.console.print("[dim]  Talk naturally:[/] [cyan]\"what's BTC doing?\"[/]  [cyan]\"analyze ETH\"[/]  [cyan]\"go long SOL $50\"[/]")
        self.console.print("[dim]  Type[/] [white]help[/] [dim]for examples,[/] [white]quit[/] [dim]to exit[/]")
        self.console.print()

    def _print_help(self):
        """Print help message - showing natural language examples."""
        self.console.print(Panel(
            "[bold]Just talk naturally! Here are some things you can say:[/]\n",
            title="🔮 Vista understands you",
            border_style="cyan"
        ))

        # Examples by category
        examples = [
            ("📈 [green]Trading[/]", [
                '"go long BTC $100"',
                '"short ethereum fifty bucks"',
                '"close my solana"',
                '"what are my positions?"',
                '"how much do I have?"',
            ]),
            ("📊 [blue]Analysis[/]", [
                '"analyze bitcoin"',
                '"what do you think of ETH?"',
                '"show me the SOL indicators"',
                '"what\'s the RSI on BTC?"',
                '"generate a chart for AVAX"',
            ]),
            ("📖 [yellow]Market Data[/]", [
                '"show me the orderbook"',
                '"what\'s BTC trading at?"',
                '"SOL depth chart"',
                '"what are the bid/asks?"',
            ]),
            ("🖥️ [cyan]Dashboard[/]", [
                '"open the dashboard"',
                '"show me the trading terminal"',
                '"dashboard for ethereum"',
                '"full screen mode"',
            ]),
            ("🧪 [magenta]Testing[/]", [
                '"backtest the micro strategy"',
                '"how would scalp do on SOL?"',
                '"switch to paper trading"',
                '"practice mode"',
            ]),
            ("🤖 [red]Bot Control[/]", [
                '"is the bot running?"',
                '"start the bot"',
                '"stop everything"',
                '"emergency stop"',
                '"resume trading"',
            ]),
        ]

        for title, items in examples:
            self.console.print(f"\n{title}")
            for item in items:
                self.console.print(f"  [dim]•[/] [italic]{item}[/]")

        self.console.print("\n[dim]Type [white]quit[/] to exit, [white]config[/] for settings[/]")

    async def _handle_command(self, user_input: str) -> Optional[str]:
        """Handle direct commands, return None to pass to AI."""
        parts = user_input.lower().split()
        if not parts:
            return None

        cmd = parts[0]

        # Direct commands (bypass AI)
        if cmd in ['quit', 'exit', 'q']:
            self.running = False
            return "Goodbye! 👋"

        if cmd == 'help':
            self._print_help()
            return ""

        if cmd == 'prices':
            return await self._tool_get_prices()

        if cmd in ['positions', 'pos']:
            return await self._tool_get_positions()

        if cmd in ['account', 'bal', 'balance']:
            return await self._tool_get_account()

        if cmd == 'signals':
            return await self._tool_get_signals()

        if cmd == 'analyze' and len(parts) >= 2:
            sym = parts[1].upper()
            tf = parts[2] if len(parts) > 2 else "1h"
            return await self._tool_analyze_chart(sym, tf)

        if cmd == 'chart' and len(parts) >= 2:
            # Handle "chart of BTC" or "chart BTC"
            sym = parts[1].upper()
            if sym == "OF" and len(parts) >= 3:
                sym = parts[2].upper()
                tf = parts[3] if len(parts) > 3 else "5m"
            else:
                tf = parts[2] if len(parts) > 2 else "5m"
            return await self._tool_generate_chart(sym, tf)

        if cmd == 'long' and len(parts) >= 3:
            return await self._tool_place_order(parts[1], "long", float(parts[2]))

        if cmd == 'short' and len(parts) >= 3:
            return await self._tool_place_order(parts[1], "short", float(parts[2]))

        if cmd == 'close' and len(parts) >= 2:
            return await self._tool_close_position(parts[1])

        if cmd == 'config':
            return self._show_config()

        if cmd == 'logout':
            return self._logout()

        # Dashboard command - handle "dash btc", "dashboard btc", "btc dashboard", etc.
        if cmd in ['dash', 'dashboard']:
            sym = parts[1].upper() if len(parts) > 1 else "BTC"
            await self._run_dashboard(sym)
            return ""

        # Handle reversed order: "btc dashboard"
        if len(parts) >= 2 and parts[1] in ['dash', 'dashboard']:
            sym = parts[0].upper()
            await self._run_dashboard(sym)
            return ""

        # Market data commands
        if cmd == 'orderbook' and len(parts) >= 2:
            return await self._show_orderbook(parts[1].upper())

        if cmd == 'indicators' and len(parts) >= 2:
            return await self._show_indicators(parts[1].upper())

        if cmd == 'backtest':
            # backtest BTC micro 2024-01-01 2024-12-31
            if len(parts) < 3:
                return "Usage: backtest <symbol> <strategy> [start_date] [end_date]"
            sym = parts[1].upper()
            strategy = parts[2]
            start = parts[3] if len(parts) > 3 else "2024-01-01"
            end = parts[4] if len(parts) > 4 else "2024-12-31"
            return await self._run_backtest(sym, strategy, start, end)

        if cmd in ['paper', 'sim', 'simulate']:
            return self._toggle_paper_mode()

        if cmd == 'replay' and len(parts) >= 2:
            sym = parts[1].upper()
            date = parts[2] if len(parts) > 2 else None
            return await self._run_replay(sym, date)

        if cmd == 'kill':
            if len(parts) < 2:
                return self._toggle_kill_switch('all')
            return self._toggle_kill_switch(parts[1])

        if cmd == 'bot':
            if len(parts) < 2:
                return self._show_bot_status()
            if parts[1] == 'setup':
                await self._run_bot_setup()
                return ""
            return await self._control_bot(parts[1])

        if cmd == 'setup':
            await self._run_bot_setup()
            return ""

        # Stats command - show prediction analysis
        if cmd == 'stats':
            return await self._show_stats(parts[1] if len(parts) > 1 else None)

        # Not a direct command, pass to AI
        return None

    def _show_config(self) -> str:
        """Show current configuration."""
        from src.vista_config import VISTA_DIR

        table = Table(title="Configuration", border_style="dim")
        table.add_column("Setting", style="cyan")
        table.add_column("Value")

        table.add_row("User", self.config.user_email or "[dim]not set[/]")
        table.add_row("Wallet", self.config.hyperliquid_wallet_address[:10] + "..." if self.config.hyperliquid_wallet_address else "[dim]not set[/]")
        table.add_row("Network", "Testnet" if self.config.hyperliquid_testnet else "Mainnet")
        table.add_row("AI", "[green]✓ ready[/]")
        table.add_row("Config dir", str(VISTA_DIR))

        self.console.print(table)
        return ""

    def _logout(self) -> str:
        """Logout and clear session."""
        from src.vista_auth import VistaAuth
        auth = VistaAuth()
        auth.logout()
        self.running = False
        return "Logged out. Run [cyan]vista[/] to login again."

    # ==================== DASHBOARD ====================

    async def _run_dashboard(self, symbol: str):
        """Launch the Bloomberg-style live trading dashboard."""
        from src.vista_dashboard import VistaDashboard
        dashboard = VistaDashboard(hl_client=self.hl, llm=self.llm)
        await dashboard.run(symbol)

    # ==================== MARKET DATA COMMANDS ====================

    async def _show_orderbook(self, symbol: str) -> str:
        """Show orderbook for a symbol."""
        orderbook = self.hl.get_orderbook(symbol)
        if not orderbook:
            return f"Could not get orderbook for {symbol}"

        bids = orderbook.get('bids', [])[:8]
        asks = orderbook.get('asks', [])[:8]

        table = Table(title=f"📖 {symbol} Orderbook", box=None)
        table.add_column("Bid Size", justify="right", style="green")
        table.add_column("Bid", justify="right", style="green")
        table.add_column("Ask", justify="left", style="red")
        table.add_column("Ask Size", justify="left", style="red")

        for i in range(min(8, len(bids), len(asks))):
            bid_price, bid_size = bids[i] if i < len(bids) else (0, 0)
            ask_price, ask_size = asks[i] if i < len(asks) else (0, 0)
            table.add_row(f"{bid_size:.3f}", f"${bid_price:,.2f}", f"${ask_price:,.2f}", f"{ask_size:.3f}")

        self.console.print(table)
        return ""

    async def _show_indicators(self, symbol: str) -> str:
        """Show technical indicators for a symbol."""
        candles = self.hl.get_candles(symbol, interval="5m", limit=50)
        if not candles:
            return f"Could not get data for {symbol}"

        closes = [c['close'] for c in candles]

        # Simple RSI calculation
        rsi = self._calc_rsi(closes)

        # Simple EMA
        ema_9 = sum(closes[-9:]) / 9 if len(closes) >= 9 else closes[-1]
        ema_21 = sum(closes[-21:]) / 21 if len(closes) >= 21 else closes[-1]

        trend = "BULLISH" if ema_9 > ema_21 else "BEARISH"
        trend_color = "green" if ema_9 > ema_21 else "red"
        rsi_color = "green" if rsi < 30 else "red" if rsi > 70 else "yellow"

        table = Table(title=f"📊 {symbol} Indicators", box=None)
        table.add_column("Indicator", style="cyan")
        table.add_column("Value", justify="right")

        table.add_row("RSI(14)", f"[{rsi_color}]{rsi:.1f}[/]")
        table.add_row("EMA(9)", f"${ema_9:,.2f}")
        table.add_row("EMA(21)", f"${ema_21:,.2f}")
        table.add_row("Trend", f"[{trend_color}]{trend}[/]")
        table.add_row("Price", f"${closes[-1]:,.2f}")

        self.console.print(table)
        return ""

    def _calc_rsi(self, prices: list, period: int = 14) -> float:
        """Calculate RSI."""
        if len(prices) < period + 1:
            return 50.0
        gains, losses = [], []
        for i in range(1, len(prices)):
            diff = prices[i] - prices[i-1]
            gains.append(diff if diff > 0 else 0)
            losses.append(abs(diff) if diff < 0 else 0)
        avg_gain = sum(gains[-period:]) / period
        avg_loss = sum(losses[-period:]) / period
        if avg_loss == 0:
            return 100.0
        return 100 - (100 / (1 + avg_gain / avg_loss))

    async def _run_backtest(self, symbol: str, strategy: str, start: str, end: str) -> str:
        """Run a backtest."""
        return f"⚠️ Backtesting coming soon! Would test {strategy} on {symbol} from {start} to {end}"

    def _toggle_paper_mode(self) -> str:
        """Toggle paper trading mode."""
        self.paper_mode = not getattr(self, 'paper_mode', False)
        if self.paper_mode:
            return "📝 Paper trading mode [yellow]ENABLED[/]. Trades will be simulated."
        else:
            return "💰 Paper trading mode [green]DISABLED[/]. Trades will be REAL."

    async def _run_replay(self, symbol: str, date: str = None) -> str:
        """Run replay mode for a specific date."""
        if not date:
            return "Usage: replay <symbol> <date> (e.g., replay BTC 2024-12-01)"

        self.console.print(f"[cyan]Loading replay for {symbol} on {date}...[/]")
        # TODO: Implement full replay mode with historical candles
        return f"📼 Replay mode for {symbol} on {date} - Coming soon!"

    def _toggle_kill_switch(self, switch: str) -> str:
        """Toggle kill switches."""
        if not hasattr(self, 'kill_switches'):
            self.kill_switches = {'all': False, 'longs': False, 'shorts': False}

        if switch == 'all':
            self.kill_switches['all'] = not self.kill_switches['all']
            if self.kill_switches['all']:
                return "🔴 [red]KILL SWITCH ACTIVATED[/] - All trading halted!"
            return "🟢 [green]Kill switch deactivated[/] - Trading resumed."
        elif switch == 'longs':
            self.kill_switches['longs'] = not self.kill_switches['longs']
            status = "[red]BLOCKED[/]" if self.kill_switches['longs'] else "[green]allowed[/]"
            return f"Long positions: {status}"
        elif switch == 'shorts':
            self.kill_switches['shorts'] = not self.kill_switches['shorts']
            status = "[red]BLOCKED[/]" if self.kill_switches['shorts'] else "[green]allowed[/]"
            return f"Short positions: {status}"
        else:
            return "Kill switches: all, longs, shorts"

    def _show_bot_status(self) -> str:
        """Show trading bot status."""
        table = Table(title="🤖 Bot Status", border_style="cyan")
        table.add_column("Setting", style="cyan")
        table.add_column("Value")

        # Check if bot is running (look for process)
        import subprocess
        try:
            result = subprocess.run(['pgrep', '-f', 'run.py'], capture_output=True, text=True)
            bot_running = bool(result.stdout.strip())
        except:
            bot_running = False

        table.add_row("Status", "[green]RUNNING[/]" if bot_running else "[dim]stopped[/]")
        table.add_row("Mode", "[yellow]PAPER[/]" if getattr(self, 'paper_mode', False) else "[green]LIVE[/]")
        table.add_row("Kill All", "[red]ON[/]" if getattr(self, 'kill_switches', {}).get('all') else "[green]OFF[/]")

        self.console.print(table)
        self.console.print("\n[dim]Commands: bot start, bot stop, bot restart[/]")
        return ""

    async def _control_bot(self, action: str) -> str:
        """Control the trading bot."""
        import subprocess

        if action == 'start':
            subprocess.Popen(['python3', 'run.py'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return "🤖 Bot starting in background..."
        elif action == 'stop':
            subprocess.run(['pkill', '-f', 'run.py'], capture_output=True)
            return "🤖 Bot stopped."
        elif action == 'restart':
            subprocess.run(['pkill', '-f', 'run.py'], capture_output=True)
            await asyncio.sleep(1)
            subprocess.Popen(['python3', 'run.py'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return "🤖 Bot restarting..."
        else:
            return "Usage: bot [start|stop|restart]"

    async def _show_stats(self, subcommand: str = None) -> str:
        """Show prediction and trading statistics."""
        from src.database import Database
        from rich.table import Table

        db = Database()

        if subcommand == "errors" or subcommand == "analysis":
            # Show prediction error analysis
            analysis = db.analyze_prediction_errors(days=30)

            output = []
            output.append(f"[bold]📊 Prediction Error Analysis (30 days)[/]\n")
            output.append(f"Total Errors: [red]{analysis['total_errors']}[/]")
            output.append(f"Avg Error: [yellow]{analysis['avg_error_pct']:.2f}%[/]\n")

            if analysis["errors_by_trend"]:
                output.append("[bold]By Trend:[/]")
                for trend, data in analysis["errors_by_trend"].items():
                    output.append(f"  {trend}: {data['error_count']} errors ({data['pct_of_errors']:.0f}%)")

            if analysis["errors_by_volatility"]:
                output.append("\n[bold]By Volatility:[/]")
                for vol, data in analysis["errors_by_volatility"].items():
                    output.append(f"  {vol}: {data['error_count']} errors ({data['pct_of_errors']:.0f}%)")

            if analysis["common_failure_modes"]:
                output.append("\n[bold red]⚠️ Common Failure Modes:[/]")
                for mode in analysis["common_failure_modes"]:
                    output.append(f"  • {mode['description']}")
                    output.append(f"    [dim]→ {mode['recommendation']}[/]")

            if analysis["recommendations"]:
                output.append("\n[bold green]💡 Recommendations:[/]")
                for rec in analysis["recommendations"]:
                    output.append(f"  • {rec}")

            return "\n".join(output)

        # Default: show general stats
        stats = db.get_db_stats()

        table = Table(title="📊 Trading Bot Statistics", show_header=True)
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="white")

        table.add_row("Whale Events", str(stats.get("whale_events", 0)))
        table.add_row("Chart Signals", str(stats.get("chart_signals", 0)))
        table.add_row("S/R Events", str(stats.get("sr_events", 0)))
        table.add_row("Trade Signals", str(stats.get("trade_signals", 0)))
        table.add_row("Discord Alerts", str(stats.get("discord_alerts", 0)))
        table.add_row("Pending Outcomes", str(stats.get("pending_outcomes", 0)))

        if "predictions_total" in stats:
            table.add_row("─" * 15, "─" * 10)
            table.add_row("Predictions Total", str(stats.get("predictions_total", 0)))
            table.add_row("Predictions Pending", str(stats.get("predictions_pending", 0)))
            acc = stats.get("prediction_accuracy_pct", 0)
            acc_color = "green" if acc >= 60 else "yellow" if acc >= 50 else "red"
            table.add_row("Prediction Accuracy", f"[{acc_color}]{acc:.1f}%[/]")

        table.add_row("─" * 15, "─" * 10)
        table.add_row("DB Size", f"{stats.get('db_size_mb', 0):.2f} MB")

        self.console.print(table)
        self.console.print("\n[dim]Commands: stats errors (for prediction analysis)[/]")
        return ""

    async def run(self, initial_query: str = None):
        """Main REPL loop."""
        self._print_welcome()
        self.running = True

        # Connect to Hyperliquid
        with Progress(
            SpinnerColumn(),
            TextColumn("[cyan]Connecting...[/]"),
            console=self.console,
            transient=True
        ) as progress:
            progress.add_task("", total=None)
            connected = await self.hl.connect()

        if not connected:
            self.console.print("[red]Failed to connect to Hyperliquid[/]")
            return

        network = "Testnet" if self.config.hyperliquid_testnet else "Mainnet"
        self.console.print(f"[green]✓ Connected to {network}[/]\n")

        # Handle initial query if provided
        if initial_query:
            await self._process_input(initial_query)
            return

        # Main loop
        while self.running:
            try:
                user_input = Prompt.ask("\n[bold cyan]>[/]")
                if not user_input:
                    continue
                await self._process_input(user_input)

            except KeyboardInterrupt:
                self.console.print("\n\n[dim]Goodbye! 👋[/]")
                break
            except EOFError:
                break
            except Exception as e:
                self.console.print(f"[red]Error: {e}[/]")

    async def _process_input(self, user_input: str):
        """Process user input."""
        # Try direct command first
        result = await self._handle_command(user_input)

        if result is not None:
            if result:
                self._print_response(result)
            return

        # Pass to AI
        self.conversation.append(Message(role="user", content=user_input))

        with Progress(
            SpinnerColumn(),
            TextColumn("[dim]thinking...[/]"),
            console=self.console,
            transient=True
        ) as progress:
            progress.add_task("", total=None)
            response = await self._call_llm(user_input)
            response = await self._process_response(response)

        self.conversation.append(Message(role="assistant", content=response))
        self._print_response(response)

    def _print_response(self, response: str):
        """Print AI response with formatting."""
        # Check if response looks like structured data
        if any(response.startswith(c) for c in ['📊', '✅', '❌', 'Current', 'Account', 'Open', 'Recent', 'Logged']):
            # Structured output - use panel
            self.console.print(Panel(response, border_style="green"))
        else:
            # Regular conversational text
            self.console.print(f"\n[green]Vista:[/] {response}")


# ==================== CLI ENTRY POINT ====================

async def async_main():
    """Async main entry point."""
    from src.vista_config import VistaConfig
    from src.vista_setup import VistaSetup
    from src.vista_auth import VistaAuth

    parser = argparse.ArgumentParser(
        description="Vista - AI Trading Terminal",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  vista                        # Interactive mode
  vista "what's BTC doing"     # Quick query
  vista login                  # Force re-login
  vista logout                 # Logout
  vista config                 # Show config
"""
    )
    parser.add_argument("query", nargs="*", help="Query or command")
    parser.add_argument("--debug", action="store_true", help="Debug logging")

    args = parser.parse_args()

    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)

    # Handle special commands
    query = " ".join(args.query) if args.query else ""

    if query == "logout":
        auth = VistaAuth()
        auth.logout()
        console.print("[green]Logged out successfully[/]")
        return

    if query == "config":
        config = VistaConfig.load()
        console.print(f"[cyan]User:[/] {config.user_email or 'not logged in'}")
        console.print(f"[cyan]Wallet:[/] {config.hyperliquid_wallet_address[:20]}..." if config.hyperliquid_wallet_address else "[dim]not set[/]")
        console.print(f"[cyan]Network:[/] {'Testnet' if config.hyperliquid_testnet else 'Mainnet'}")
        console.print(f"[cyan]Config dir:[/] ~/.vista/")
        return

    # Run setup wizard if needed
    setup = VistaSetup(console)
    ready = await setup.run_if_needed()

    if not ready:
        console.print("[red]Setup incomplete. Run 'vista' again to continue.[/]")
        return

    # Create and run CLI
    vista = VistaCLI()

    # Handle login command (force re-setup)
    if query == "login":
        await setup.run_setup()
        return

    # Run with optional initial query
    initial_query = query if query else None
    await vista.run(initial_query)


def main():
    """Sync entry point."""
    asyncio.run(async_main())


if __name__ == "__main__":
    main()

