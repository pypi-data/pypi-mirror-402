"""
Vista Trading Terminal - Bloomberg-style Live Dashboard

A professional-grade trading terminal with:
- Real-time candlestick charts (py-candlestick-chart)
- Full technical indicators panel
- AI-powered market insights
- Quick function keys

Press Q to quit, C to chat, T to change timeframe.
"""
import time
import asyncio
import sys
import select
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field

from rich.console import Console, Group
from rich.live import Live
from rich.panel import Panel
from rich.layout import Layout
from rich.table import Table
from rich.text import Text
from rich.style import Style

# py-candlestick-chart library
try:
    from candlestick_chart import Candle, Chart
    from candlestick_chart.utils import fnum
    HAS_CHART_LIB = True
except ImportError:
    HAS_CHART_LIB = False
    Candle = Chart = fnum = None


@dataclass
class Indicators:
    """Technical indicators container."""
    # Price
    price: float = 0.0
    change_24h: float = 0.0
    # Momentum
    rsi: float = 50.0
    macd: float = 0.0
    macd_signal: float = 0.0
    macd_hist: float = 0.0
    stoch_k: float = 50.0
    stoch_d: float = 50.0
    # Trend
    ema_9: float = 0.0
    ema_21: float = 0.0
    ema_50: float = 0.0
    adx: float = 0.0
    trend: str = "NEUTRAL"
    # Volatility
    bb_upper: float = 0.0
    bb_middle: float = 0.0
    bb_lower: float = 0.0
    atr: float = 0.0
    atr_pct: float = 0.0
    # Volume
    vwap: float = 0.0
    volume: float = 0.0
    vol_avg: float = 0.0
    vol_ratio: float = 1.0
    cvd: float = 0.0
    # Levels
    support: float = 0.0
    resistance: float = 0.0
    pivot: float = 0.0


@dataclass
class DashboardState:
    """Dashboard state container."""
    symbol: str = "BTC"
    interval: str = "5m"
    candles: List[Dict] = field(default_factory=list)
    indicators: Indicators = field(default_factory=Indicators)
    last_update: str = ""
    status: str = "CONNECTING..."
    # Order entry
    order_input: str = ""
    order_side: str = ""  # "LONG" or "SHORT"
    # AI
    ai_thinking: bool = False
    ai_analysis: str = ""
    bot_running: bool = False


class VistaDashboard:
    """Bloomberg-style Trading Terminal."""

    # Available timeframes
    TIMEFRAMES = ["1m", "5m", "15m", "30m", "1h", "4h", "1d"]

    # Colors - Bloomberg aesthetic
    COLORS = {
        "bull": Style(color="bright_green"),
        "bear": Style(color="red"),
        "neutral": Style(color="yellow"),
        "header": Style(color="bright_cyan", bold=True),
        "label": Style(color="bright_white", dim=True),
        "value": Style(color="bright_white"),
        "positive": Style(color="bright_green"),
        "negative": Style(color="red"),
        "warning": Style(color="yellow"),
        "key": Style(color="black", bgcolor="yellow", bold=True),
    }

    def __init__(self, hl_client=None, llm=None):
        """Initialize the Vista Trading Terminal."""
        self.hl = hl_client
        self.llm = llm
        self.state = DashboardState()
        self.console = Console()
        self.running = False
        self._live = None
        self._tf_index = 1  # Default to 5m

        # Multi-ticker watchlist
        from src.tickers import TRADING_TICKERS
        self.watchlist_tickers = TRADING_TICKERS  # BTC, ETH, SOL, ZEC, SUI, XRP, ADA
        self.watchlist_data: Dict[str, Dict] = {}  # {symbol: {price, change, rsi, trend}}

    def _calculate_indicators(self, candles: List[Dict]) -> Indicators:
        """Calculate all technical indicators from candle data."""
        if not candles or len(candles) < 50:
            return Indicators()

        from src.technical_analysis import (
            calculate_rsi, calculate_ema, calculate_macd,
            calculate_bollinger_bands, calculate_atr,
            calculate_support_resistance, calculate_vwap,
            calculate_adx
        )

        ind = Indicators()
        price = candles[-1]["close"]
        ind.price = price

        # 24h change
        if len(candles) >= 288:  # 5m candles in 24h
            old_price = candles[-288]["close"]
            ind.change_24h = ((price - old_price) / old_price * 100) if old_price else 0

        # RSI
        rsi = calculate_rsi(candles, period=14)
        ind.rsi = rsi if rsi else 50.0

        # MACD
        macd = calculate_macd(candles, fast=12, slow=26, signal=9)
        ind.macd = macd.get("macd_line", 0) or 0
        ind.macd_signal = macd.get("signal_line", 0) or 0
        ind.macd_hist = macd.get("histogram", 0) or 0

        # EMAs
        ind.ema_9 = calculate_ema(candles, 9) or price
        ind.ema_21 = calculate_ema(candles, 21) or price
        ind.ema_50 = calculate_ema(candles, 50) or price

        # Trend direction
        if ind.ema_9 > ind.ema_21 > ind.ema_50:
            ind.trend = "BULLISH"
        elif ind.ema_9 < ind.ema_21 < ind.ema_50:
            ind.trend = "BEARISH"
        else:
            ind.trend = "NEUTRAL"

        # ADX
        adx_data = calculate_adx(candles, period=14) if len(candles) >= 30 else {}
        ind.adx = adx_data.get("adx", 0) or 0

        # Bollinger Bands
        bb = calculate_bollinger_bands(candles, period=20, std_dev=2.0)
        ind.bb_upper = bb.get("upper", price) or price
        ind.bb_middle = bb.get("middle", price) or price
        ind.bb_lower = bb.get("lower", price) or price

        # ATR
        atr = calculate_atr(candles, period=14)
        ind.atr = atr if atr else 0
        ind.atr_pct = (atr / price * 100) if atr and price else 0

        # VWAP
        vwap_data = calculate_vwap(candles)
        ind.vwap = vwap_data.get("vwap", price) or price

        # Volume
        volumes = [c.get("volume", 0) for c in candles[-20:]]
        ind.vol_avg = sum(volumes) / len(volumes) if volumes else 0
        ind.volume = candles[-1].get("volume", 0)
        ind.vol_ratio = (ind.volume / ind.vol_avg) if ind.vol_avg > 0 else 1.0

        # Support/Resistance
        sr = calculate_support_resistance(candles, lookback=50)
        ind.support = sr.get("support", price * 0.98) or price * 0.98
        ind.resistance = sr.get("resistance", price * 1.02) or price * 1.02
        ind.pivot = (ind.support + ind.resistance) / 2

        return ind

    def _make_chart(self, width: int, height: int):
        """Create candlestick chart using py-candlestick-chart library."""
        if not self.state.candles:
            return Text("Waiting for data...", style="dim")

        candles = self.state.candles[-100:]

        if HAS_CHART_LIB:
            # Convert to library format
            chart_candles = [
                Candle(
                    open=c["open"], high=c["high"],
                    low=c["low"], close=c["close"],
                    volume=c.get("volume", 0)
                ) for c in candles
            ]

            chart = Chart(chart_candles, title=f"{self.state.symbol} {self.state.interval}")
            chart.set_name(f"{self.state.symbol}/USD")

            # Bloomberg-style colors
            chart.set_bull_color(0, 255, 136)   # Bright green
            chart.set_bear_color(255, 82, 82)  # Bright red

            # Labels
            chart.set_label("highest", "HIGH")
            chart.set_label("lowest", "LOW")
            chart.set_label("average", "")
            chart.set_label("volume", "")
            chart.set_volume_pane_enabled(False)

            # Size
            chart.update_size(width, height)

            # S/R highlights
            ind = self.state.indicators
            if ind.support > 0:
                chart.set_highlight(fnum(ind.support), (0, 255, 0))
            if ind.resistance > 0:
                chart.set_highlight(fnum(ind.resistance), (255, 0, 0))

            return chart

        # Fallback: simple text chart
        return self._make_fallback_chart(candles, width, height)

    def _make_fallback_chart(self, candles: List[Dict], width: int, height: int) -> str:
        """Fallback ASCII candlestick chart with S/R levels."""
        if not candles:
            return "No data"

        ind = self.state.indicators

        # Calculate price range - include S/R levels
        highs = [c["high"] for c in candles]
        lows = [c["low"] for c in candles]
        price_max = max(max(highs), ind.resistance) if ind.resistance > 0 else max(highs)
        price_min = min(min(lows), ind.support) if ind.support > 0 else min(lows)
        price_range = price_max - price_min or price_max * 0.01

        # Scale function
        def scale(p):
            return min(height - 1, max(0, int((price_max - p) / price_range * (height - 1))))

        # Build chart
        chart_width = width - 12  # Reserve space for price labels
        max_candles = min(len(candles), chart_width // 2)
        candles = candles[-max_candles:]

        lines = []
        current = candles[-1]["close"]
        change = ((current - candles[0]["open"]) / candles[0]["open"] * 100) if candles[0]["open"] else 0
        change_color = "green" if change >= 0 else "red"

        lines.append(f"[bold]{self.state.symbol}/USD[/] ${current:,.2f} [{change_color}]{'+' if change >= 0 else ''}{change:.2f}%[/]")
        lines.append("")

        # Price grid with S/R lines
        grid = [[" "] * (len(candles) * 2) for _ in range(height)]

        # Calculate S/R row positions
        res_row = scale(ind.resistance) if ind.resistance > 0 else -1
        sup_row = scale(ind.support) if ind.support > 0 else -1
        pivot_row = scale(ind.pivot) if ind.pivot > 0 else -1

        # Draw candles
        for i, c in enumerate(candles):
            x = i * 2
            bull = c["close"] >= c["open"]
            y_h, y_l = scale(c["high"]), scale(c["low"])
            y_o, y_c = scale(c["open"]), scale(c["close"])
            y_top, y_bot = min(y_o, y_c), max(y_o, y_c)

            col = "green" if bull else "red"
            for y in range(y_h, y_l + 1):
                if y_top <= y <= y_bot:
                    grid[y][x] = f"[{col}]█[/]"
                else:
                    grid[y][x] = f"[{col}]│[/]"

        # Build output with S/R labels on right
        for row_idx, row in enumerate(grid):
            row_str = "".join(row)

            # Add S/R labels on right side
            if row_idx == res_row:
                row_str += f" [red]━━ R ${ind.resistance:,.0f}[/]"
            elif row_idx == sup_row:
                row_str += f" [green]━━ S ${ind.support:,.0f}[/]"
            elif row_idx == pivot_row:
                row_str += f" [yellow]-- P ${ind.pivot:,.0f}[/]"

            lines.append(row_str)

        return "\n".join(lines)


    def _make_indicators_panel(self) -> Text:
        """Create the full indicators panel - Bloomberg style."""
        ind = self.state.indicators
        lines = []

        def val_color(val, threshold_low=30, threshold_high=70):
            if val < threshold_low:
                return "red"
            elif val > threshold_high:
                return "green"
            return "yellow"

        def trend_icon(val, ref=0):
            return "▲" if val > ref else "▼" if val < ref else "─"

        # ═══════════════ MOMENTUM ═══════════════
        lines.append("[bold cyan]━━━ MOMENTUM ━━━[/]")
        rsi_col = val_color(ind.rsi)
        lines.append(f"[dim]RSI(14):[/]    [{rsi_col}]{ind.rsi:>6.1f}[/] {'◐' if 40 < ind.rsi < 60 else '●' if ind.rsi > 50 else '○'}")

        macd_col = "green" if ind.macd_hist > 0 else "red"
        macd_trend = "BULLISH" if ind.macd > ind.macd_signal else "BEARISH"
        lines.append(f"[dim]MACD:[/]      [{macd_col}]{ind.macd:>+7.1f}[/] {trend_icon(ind.macd_hist)} {macd_trend}")
        lines.append(f"[dim]Signal:[/]    [{macd_col}]{ind.macd_signal:>+7.1f}[/]")
        lines.append(f"[dim]Histogram:[/] [{macd_col}]{ind.macd_hist:>+7.2f}[/]")
        lines.append("")

        # ═══════════════ TREND ═══════════════
        lines.append("[bold cyan]━━━ TREND ━━━[/]")
        trend_col = "green" if ind.trend == "BULLISH" else "red" if ind.trend == "BEARISH" else "yellow"
        lines.append(f"[dim]Trend:[/]     [{trend_col}]{ind.trend:>10}[/]")

        # EMAs with color based on price position
        price = ind.price
        ema9_col = "green" if price > ind.ema_9 else "red"
        ema21_col = "green" if price > ind.ema_21 else "red"
        ema50_col = "green" if price > ind.ema_50 else "red"

        lines.append(f"[dim]EMA(9):[/]    [{ema9_col}]{ind.ema_9:>10,.2f}[/]")
        lines.append(f"[dim]EMA(21):[/]   [{ema21_col}]{ind.ema_21:>10,.2f}[/]")
        lines.append(f"[dim]EMA(50):[/]   [{ema50_col}]{ind.ema_50:>10,.2f}[/]")

        # ADX
        adx_col = "green" if ind.adx > 25 else "yellow" if ind.adx > 20 else "dim"
        adx_str = "STRONG" if ind.adx > 25 else "WEAK" if ind.adx < 20 else "MODERATE"
        lines.append(f"[dim]ADX(14):[/]   [{adx_col}]{ind.adx:>6.1f}[/] {adx_str}")
        lines.append("")

        # ═══════════════ VOLATILITY ═══════════════
        lines.append("[bold cyan]━━━ VOLATILITY ━━━[/]")

        # BB position
        bb_range = ind.bb_upper - ind.bb_lower
        bb_pos = ((price - ind.bb_lower) / bb_range * 100) if bb_range > 0 else 50
        bb_col = "red" if bb_pos > 80 else "green" if bb_pos < 20 else "yellow"

        lines.append(f"[dim]BB Upper:[/]  [red]{ind.bb_upper:>10,.2f}[/]")
        lines.append(f"[dim]BB Middle:[/] [yellow]{ind.bb_middle:>10,.2f}[/]")
        lines.append(f"[dim]BB Lower:[/]  [green]{ind.bb_lower:>10,.2f}[/]")
        lines.append(f"[dim]BB Pos:[/]    [{bb_col}]{bb_pos:>6.1f}%[/]")

        atr_col = "red" if ind.atr_pct > 1.5 else "green" if ind.atr_pct < 0.5 else "yellow"
        lines.append(f"[dim]ATR(14):[/]   [{atr_col}]{ind.atr:>8,.2f}[/] ({ind.atr_pct:.2f}%)")
        lines.append("")

        # ═══════════════ VOLUME ═══════════════
        lines.append("[bold cyan]━━━ VOLUME ━━━[/]")

        vwap_col = "green" if price > ind.vwap else "red"
        lines.append(f"[dim]VWAP:[/]      [{vwap_col}]{ind.vwap:>10,.2f}[/]")

        vol_col = "green" if ind.vol_ratio > 1.2 else "red" if ind.vol_ratio < 0.8 else "yellow"
        lines.append(f"[dim]Volume:[/]    [{vol_col}]{ind.volume:>10,.0f}[/]")
        lines.append(f"[dim]Vol Avg:[/]   [dim]{ind.vol_avg:>10,.0f}[/]")
        lines.append(f"[dim]Vol Ratio:[/] [{vol_col}]{ind.vol_ratio:>6.2f}x[/]")
        lines.append("")

        # ═══════════════ LEVELS ═══════════════
        lines.append("[bold cyan]━━━ LEVELS ━━━[/]")
        lines.append(f"[dim]Resistance:[/][red]{ind.resistance:>10,.2f}[/]")
        lines.append(f"[dim]Pivot:[/]     [yellow]{ind.pivot:>10,.2f}[/]")
        lines.append(f"[dim]Support:[/]   [green]{ind.support:>10,.2f}[/]")

        # Distance from levels
        dist_r = ((ind.resistance - price) / price * 100) if price > 0 else 0
        dist_s = ((price - ind.support) / price * 100) if price > 0 else 0
        lines.append(f"[dim]To Res:[/]    [red]+{dist_r:.2f}%[/]")
        lines.append(f"[dim]To Sup:[/]    [green]-{dist_s:.2f}%[/]")

        return Text.from_markup("\n".join(lines))


    def _make_function_keys(self) -> Text:
        """Create the bottom function keys bar with trading buttons."""
        parts = []

        # Trading buttons - highlighted based on selection
        long_style = "black on bright_green bold" if self.state.order_side == "LONG" else "white on green"
        short_style = "black on bright_red bold" if self.state.order_side == "SHORT" else "white on red"

        parts.append(f"[{long_style}] L LONG [/]")
        parts.append(f"[{short_style}] S SHORT [/]")
        parts.append("  ")

        # AI buttons
        bot_style = "black on bright_cyan bold" if self.state.bot_running else "white on blue"
        bot_label = "🤖 STOP" if self.state.bot_running else "🤖 BOT"
        ask_style = "white on magenta"

        parts.append(f"[{bot_style}] B {bot_label} [/]")
        parts.append(f"[{ask_style}] A 💬 ASK AI [/]")
        parts.append("  ")

        # Standard keys
        keys = [
            ("[1-7]", "Sym"),
            ("[T]", "TF"),
            ("[R]", "Refresh"),
            ("[Q]", "Quit"),
        ]

        for key, label in keys:
            parts.append(f"[black on yellow bold]{key}[/][white]{label}[/]")

        return Text.from_markup("  ".join(parts))

    def _make_order_input(self) -> Text:
        """Create the order input bar with AI analysis."""
        # AI thinking status
        if self.state.ai_thinking:
            return Text.from_markup("[bright_magenta]🧠 AI analyzing market...[blink]...[/][/]")

        # Show AI analysis if available
        if self.state.ai_analysis and not self.state.order_side:
            return Text.from_markup(f"[bright_cyan]🤖 {self.state.ai_analysis}[/]")

        # Bot running status
        if self.state.bot_running and not self.state.order_side:
            return Text.from_markup("[bright_cyan]🤖 AI Trading Bot ACTIVE[/] [dim]- Press [B] to stop[/]")

        if not self.state.order_side:
            return Text.from_markup("[dim]Press [L] Long  [S] Short  [B] Bot  [A] AI Think[/]")

        ind = self.state.indicators
        side_col = "green" if self.state.order_side == "LONG" else "red"
        side_icon = "📈" if self.state.order_side == "LONG" else "📉"

        # Build order preview
        order_text = f"{side_icon} [{side_col} bold]{self.state.order_side}[/] {self.state.symbol}/USD @ ${ind.price:,.2f}"

        if self.state.order_input:
            order_text += f"  [white]Size: {self.state.order_input}[/]"
            order_text += " [dim](Enter to confirm, ESC to cancel)[/]"
        else:
            order_text += "  [yellow]Enter size (e.g. 0.01 or $100):[/] [blink]_[/]"

        return Text.from_markup(order_text)

    def _make_header(self) -> Text:
        """Create the header bar with price info."""
        ind = self.state.indicators
        ts = datetime.now().strftime("%H:%M:%S")

        change_col = "green" if ind.change_24h >= 0 else "red"
        change_sym = "▲" if ind.change_24h >= 0 else "▼"

        header = f"[bold cyan]📈 {self.state.symbol}/USD[/]  "
        header += f"[bold white]${ind.price:,.2f}[/]  "
        header += f"[{change_col}]{change_sym} {abs(ind.change_24h):.2f}%[/]  "
        header += f"[dim]│[/]  "
        header += f"[yellow]{self.state.interval}[/]  "
        header += f"[dim]│[/]  "
        header += f"[dim]{ts}[/]  "
        header += f"[dim]│[/]  "
        header += f"[green]{self.state.status}[/]"

        return Text.from_markup(header)

    def _make_watchlist_panel(self) -> Table:
        """Create the multi-ticker watchlist panel."""
        from src.tickers import format_price

        table = Table(box=None, show_header=True, header_style="bold cyan", padding=(0, 1))
        table.add_column("#", style="dim", width=2)
        table.add_column("SYM", style="bold", width=4)
        table.add_column("PRICE", justify="right", width=10)
        table.add_column("CHG", justify="right", width=7)
        table.add_column("RSI", justify="right", width=4)
        table.add_column("", width=4)  # Trend indicator

        for i, symbol in enumerate(self.watchlist_tickers, 1):
            data = self.watchlist_data.get(symbol, {})
            price = data.get("price", 0)
            change = data.get("change", 0)
            rsi = data.get("rsi", 50)
            trend = data.get("trend", "NEUT")

            # Highlight current symbol
            sym_style = "bold yellow" if symbol == self.state.symbol else "white"

            # Price formatting
            price_str = format_price(price) if price > 0 else "-"

            # Change color
            if change > 0:
                chg_str = f"[green]+{change:.1f}%[/]"
            elif change < 0:
                chg_str = f"[red]{change:.1f}%[/]"
            else:
                chg_str = "[dim]0.0%[/]"

            # RSI color
            if rsi < 30:
                rsi_str = f"[green]{rsi:.0f}[/]"
            elif rsi > 70:
                rsi_str = f"[red]{rsi:.0f}[/]"
            else:
                rsi_str = f"[yellow]{rsi:.0f}[/]"

            # Trend indicator
            if trend == "BULL":
                trend_str = "[green]▲ BUL[/]"
            elif trend == "BEAR":
                trend_str = "[red]▼ BER[/]"
            else:
                trend_str = "[yellow]▬ NEU[/]"

            table.add_row(
                f"[dim]{i}[/]",
                f"[{sym_style}]{symbol}[/]",
                price_str,
                chg_str,
                rsi_str,
                trend_str
            )

        return table

    def _make_layout(self) -> Layout:
        """Create the full Bloomberg-style dashboard layout."""
        layout = Layout()

        # Main structure: header, body, order_bar, footer
        layout.split_column(
            Layout(name="header", size=3),
            Layout(name="body", ratio=1),
            Layout(name="order_bar", size=3),
            Layout(name="footer", size=3)
        )

        # Body: watchlist (left) + chart (center) + indicators (right)
        layout["body"].split_row(
            Layout(name="watchlist", size=38),  # Fixed width watchlist
            Layout(name="chart", ratio=2),
            Layout(name="indicators", ratio=1)
        )

        # Calculate chart dimensions
        term_w = self.console.size.width
        term_h = self.console.size.height
        chart_w = max(40, (term_w - 38) * 2 // 3 - 4)  # Account for watchlist
        chart_h = max(15, term_h - 13)

        # Header
        layout["header"].update(Panel(
            self._make_header(),
            border_style="cyan",
            padding=(0, 1)
        ))

        # Watchlist panel
        layout["watchlist"].update(Panel(
            self._make_watchlist_panel(),
            title="[bold cyan]WATCHLIST[/] [dim](1-7)[/]",
            border_style="bright_cyan"
        ))

        # Chart panel
        chart_content = self._make_chart(chart_w, chart_h)
        layout["chart"].update(Panel(
            chart_content,
            title=f"[bold cyan]{self.state.symbol} {self.state.interval}[/]",
            border_style="bright_cyan"
        ))

        # Indicators panel
        layout["indicators"].update(Panel(
            self._make_indicators_panel(),
            title="[bold cyan]INDICATORS[/]",
            border_style="bright_cyan"
        ))

        # Order input bar
        order_border = "green" if self.state.order_side == "LONG" else "red" if self.state.order_side == "SHORT" else "dim"
        layout["order_bar"].update(Panel(
            self._make_order_input(),
            title="[bold]ORDER ENTRY[/]" if self.state.order_side else None,
            border_style=order_border
        ))

        # Function keys footer
        layout["footer"].update(Panel(
            self._make_function_keys(),
            border_style="dim"
        ))

        return layout

    def _fetch_data(self):
        """Fetch market data and calculate indicators."""
        if not self.hl:
            self.state.status = "NO CLIENT"
            return

        try:
            self.state.status = "FETCHING..."
            candles = self.hl.get_candles(
                self.state.symbol,
                self.state.interval,
                200
            )

            if candles:
                self.state.candles = candles
                self.state.indicators = self._calculate_indicators(candles)
                self.state.status = "LIVE"
                self.state.last_update = datetime.now().strftime("%H:%M:%S")
            else:
                self.state.status = "NO DATA"

        except Exception as e:
            self.state.status = f"ERROR: {str(e)[:20]}"

    def _fetch_watchlist(self):
        """Fetch data for all watchlist tickers (lightweight)."""
        if not self.hl:
            return

        from src.technical_analysis import calculate_rsi

        for symbol in self.watchlist_tickers:
            try:
                # Get 5m candles for quick RSI calc
                candles = self.hl.get_candles(symbol, "5m", 50)
                if not candles or len(candles) < 20:
                    continue

                price = candles[-1]["close"]

                # Calculate 24h change (if we have enough data)
                change_24h = 0.0
                if len(candles) >= 48:  # ~4 hours of 5m candles
                    old_price = candles[-48]["close"]
                    change_24h = ((price - old_price) / old_price * 100) if old_price else 0

                # RSI
                rsi = calculate_rsi(candles, period=14) or 50.0

                # Trend based on short EMAs
                closes = [c["close"] for c in candles]
                ema_9 = sum(closes[-9:]) / 9 if len(closes) >= 9 else price
                ema_21 = sum(closes[-21:]) / 21 if len(closes) >= 21 else price

                if ema_9 > ema_21 * 1.001:
                    trend = "BULL"
                elif ema_9 < ema_21 * 0.999:
                    trend = "BEAR"
                else:
                    trend = "NEUT"

                self.watchlist_data[symbol] = {
                    "price": price,
                    "change": change_24h,
                    "rsi": rsi,
                    "trend": trend
                }
            except Exception:
                pass  # Skip failed tickers silently

    def _cycle_timeframe(self):
        """Cycle to next timeframe."""
        self._tf_index = (self._tf_index + 1) % len(self.TIMEFRAMES)
        self.state.interval = self.TIMEFRAMES[self._tf_index]
        self._fetch_data()

    def _get_learning_context(self, symbol: str) -> str:
        """Build comprehensive learning context from database for AI decisions."""
        from src.database import get_db
        import json

        try:
            db = get_db()
            context_parts = []

            # 1. HISTORICAL TRADE PERFORMANCE
            trades = db.get_completed_trades(symbol=symbol, limit=20)
            if trades:
                wins = [t for t in trades if t.get("pnl_usd", 0) > 0]
                losses = [t for t in trades if t.get("pnl_usd", 0) <= 0]
                total_pnl = sum(t.get("pnl_usd", 0) for t in trades)
                win_rate = len(wins) / len(trades) * 100 if trades else 0

                context_parts.append(f"""=== YOUR {symbol} TRADE HISTORY ===
Last {len(trades)} trades: {len(wins)} wins, {len(losses)} losses ({win_rate:.0f}% win rate)
Total P&L: ${total_pnl:+.2f}""")

                # Show last 5 trades with conditions
                trade_details = []
                for t in trades[:5]:
                    side = t.get("side", "?").upper()
                    pnl = t.get("pnl_usd", 0)
                    emoji = "✅" if pnl > 0 else "❌"
                    conditions = t.get("entry_conditions", {})
                    if isinstance(conditions, str):
                        try:
                            conditions = json.loads(conditions)
                        except:
                            conditions = {}

                    cond_str = ""
                    if conditions and conditions.get("trend"):
                        rsi = conditions.get("rsi")
                        trend = conditions.get("trend", "?")
                        rsi_str = f"{rsi:.0f}" if isinstance(rsi, (int, float)) else str(rsi) if rsi else "?"
                        cond_str = f" [RSI:{rsi_str}, {trend}]"

                    trade_details.append(f"  {emoji} {side}: ${pnl:+.2f}{cond_str}")

                context_parts.append("Recent:\n" + "\n".join(trade_details))

                # Analyze loss patterns
                loss_in_bullish = sum(1 for t in losses[:10]
                    if t.get("side") == "short" and
                    (json.loads(t.get("entry_conditions", "{}")) if isinstance(t.get("entry_conditions"), str) else t.get("entry_conditions", {})).get("trend") == "BULLISH")
                loss_in_bearish = sum(1 for t in losses[:10]
                    if t.get("side") == "long" and
                    (json.loads(t.get("entry_conditions", "{}")) if isinstance(t.get("entry_conditions"), str) else t.get("entry_conditions", {})).get("trend") == "BEARISH")

                if loss_in_bullish > 1:
                    context_parts.append(f"⚠️ WARNING: {loss_in_bullish} losses from shorting in BULLISH trend!")
                if loss_in_bearish > 1:
                    context_parts.append(f"⚠️ WARNING: {loss_in_bearish} losses from longing in BEARISH trend!")

            # 2. ALPHA CALL PERFORMANCE (with outcomes!)
            try:
                alpha_perf = db.get_alpha_call_performance(symbol=symbol, limit=20)
                if alpha_perf.get("total", 0) >= 3:
                    wr = alpha_perf.get("win_rate", 0)
                    wins = alpha_perf.get("wins", 0)
                    losses = alpha_perf.get("losses", 0)
                    context_parts.append(f"\n=== ALPHA CALL TRACK RECORD ({symbol}) ===")
                    context_parts.append(f"  {wins}W/{losses}L ({wr:.0f}% win rate)")

                    # Show insights (which patterns work/fail)
                    for insight in alpha_perf.get("insights", [])[:3]:
                        context_parts.append(f"  {insight}")
            except:
                pass

            # 3. PENDING ALPHA CALLS (active signals)
            try:
                pending = db.get_pending_alpha_calls(symbol=symbol, max_age_hours=12)
                if pending:
                    context_parts.append(f"\n=== ACTIVE ALPHA CALLS ===")
                    for call in pending[:2]:
                        direction = call.get("direction", "?").upper()
                        entry = call.get("entry_price") or 0
                        tp = call.get("take_profit") or 0
                        sl = call.get("stop_loss") or 0
                        context_parts.append(f"  {direction} @ ${entry:,.2f} (TP: ${tp:,.2f}, SL: ${sl:,.2f})")
            except:
                pass

            # 4. WHALE ACTIVITY
            whale_events = db.get_whale_events(symbol=symbol, limit=5)
            big_whales = [w for w in whale_events if (w.get("notional_usd") or 0) > 50000][:3]
            if big_whales:
                context_parts.append(f"\n=== WHALE ACTIVITY ===")
                for w in big_whales:
                    side = w.get("side", "?").upper()
                    size = w.get("notional_usd") or 0
                    context_parts.append(f"  {side} ${size:,.0f}")

            # 5. OVERALL STATS
            all_trades = db.get_completed_trades(limit=100)
            if all_trades:
                overall_pnl = sum(t.get("pnl_usd", 0) for t in all_trades)
                overall_wins = len([t for t in all_trades if t.get("pnl_usd", 0) > 0])
                overall_total = len(all_trades)
                context_parts.append(f"\n=== OVERALL: {overall_wins}/{overall_total} wins, ${overall_pnl:+.2f} ===")

            return "\n".join(context_parts) if context_parts else ""

        except Exception as e:
            return f"(DB error: {str(e)[:20]})"

    async def _ai_think(self):
        """AI analyzes current market with full database learning context."""
        if not self.llm:
            self.state.ai_analysis = "No AI client configured"
            return

        self.state.ai_thinking = True
        try:
            ind = self.state.indicators

            # Get current position if any
            position_info = ""
            if self.hl:
                try:
                    pos = self.hl.get_position(self.state.symbol)
                    if pos and float(pos.get("szi", 0)) != 0:
                        pos_size = float(pos.get("szi", 0))
                        pos_side = "LONG" if pos_size > 0 else "SHORT"
                        entry = float(pos.get("entryPx", 0))
                        pnl = float(pos.get("unrealizedPnl", 0))
                        position_info = f"\nCURRENT POSITION: {pos_side} {abs(pos_size)} @ ${entry:,.2f} (PnL: ${pnl:+,.2f})"
                except:
                    pass

            # Get learning context from database
            learning_context = self._get_learning_context(self.state.symbol)

            # Build comprehensive market context with learning
            context = f"""You are my trading AI. Use your PAST PERFORMANCE to make better decisions.

{learning_context}

=== CURRENT {self.state.symbol} MARKET ===
PRICE: ${ind.price:,.2f} (24h: {ind.change_24h:+.2f}%){position_info}

MOMENTUM: RSI {ind.rsi:.1f} | MACD Hist {ind.macd_hist:+.2f}
TREND: {ind.trend} | ADX {ind.adx:.1f} | Price {'>' if ind.price > ind.vwap else '<'} VWAP
LEVELS: Support ${ind.support:,.0f} | Resistance ${ind.resistance:,.0f}

RULES:
1. DON'T repeat your losing patterns shown above
2. If you lost shorting BULLISH trends - don't short BULLISH
3. If you lost longing BEARISH trends - don't long BEARISH
4. Consider Discord calls and whale activity
5. WAIT if conditions match your loss patterns

Decision: [LONG/SHORT/WAIT] @ $price, SL: $, TP: $ - reason"""

            response = await asyncio.to_thread(
                self.llm.deepseek_client.chat.completions.create,
                model="deepseek-chat",
                messages=[
                    {"role": "system", "content": "You're a disciplined trader that LEARNS from mistakes. Check your loss history before deciding. If similar conditions caused losses, say WAIT."},
                    {"role": "user", "content": context}
                ],
                max_tokens=120,
                temperature=0.3
            )

            self.state.ai_analysis = response.choices[0].message.content.strip()

        except Exception as e:
            self.state.ai_analysis = f"AI Error: {str(e)[:30]}"
        finally:
            self.state.ai_thinking = False

    async def _prompt_bot_size(self) -> float:
        """Prompt user for USDC per position."""
        from rich.prompt import FloatPrompt, Confirm
        from rich.panel import Panel

        self.console.print()
        self.console.print(Panel(
            "[bold cyan]🤖 AI Trading Bot[/]\n\n"
            "The bot will analyze markets and execute trades automatically.\n"
            "Set how much USDC to risk per position.",
            border_style="cyan"
        ))

        try:
            size = FloatPrompt.ask(
                "\n[cyan]USDC per position[/]",
                default=10.0
            )

            if size <= 0:
                self.console.print("[red]Invalid size. Cancelled.[/]")
                return 0

            confirm = Confirm.ask(
                f"[yellow]Start bot with ${size:.2f} per position?[/]",
                default=True
            )

            if confirm:
                self.console.print(f"[green]✓ Bot starting with ${size:.2f}/position[/]")
                return size
            else:
                self.console.print("[dim]Cancelled[/]")
                return 0

        except (KeyboardInterrupt, EOFError):
            return 0

    async def _run_ai_bot(self, position_size_usd: float = 10.0):
        """Run AI trading bot - executes trades on Hyperliquid.

        Args:
            position_size_usd: USDC amount per position
        """
        from datetime import datetime
        from src.database import get_db

        self.state.status = f"BOT: Starting (${position_size_usd}/pos)..."

        # Track open positions for recording
        bot_positions = {}  # symbol -> {entry_price, entry_time, side, size, conditions}

        while self.state.bot_running and self.running:
            try:
                # Refresh market data
                self._fetch_data()

                # Get AI recommendation
                await self._ai_think()

                analysis = self.state.ai_analysis.upper()
                ind = self.state.indicators

                # Check current position
                current_pos = None
                pos = None
                if self.hl:
                    try:
                        pos = self.hl.get_position(self.state.symbol)
                        if pos and float(pos.get("szi", 0)) != 0:
                            current_pos = "LONG" if float(pos.get("szi", 0)) > 0 else "SHORT"
                    except:
                        pass

                # Calculate size from USD amount
                size = position_size_usd / ind.price if ind.price > 0 else 0.001
                size = max(0.001, size)  # Minimum size

                # Capture entry conditions for learning
                entry_conditions = {
                    "rsi": ind.rsi,
                    "macd": ind.macd,
                    "macd_signal": ind.macd_signal,
                    "trend": ind.trend,
                    "bb_upper": ind.bb_upper,
                    "bb_lower": ind.bb_lower,
                    "atr_pct": ind.atr_pct,
                    "vwap": ind.vwap,
                    "volume_ratio": ind.vol_ratio,
                    "support": ind.support,
                    "resistance": ind.resistance,
                    "ai_analysis": self.state.ai_analysis[:200],
                }

                # ═══════════════════════════════════════════════════════════════
                # TREND CONFIRMATION FILTERS - Prevent counter-trend trades
                # ═══════════════════════════════════════════════════════════════

                # Check if trend is strong enough (ADX > 20 = trending market)
                trend_strength = ind.adx > 20

                # Bullish confirmation: EMA alignment + MACD + VWAP
                bullish_trend = (
                    ind.trend == "BULLISH" and           # EMA9 > EMA21 > EMA50
                    ind.macd_hist > 0 and                # MACD histogram positive
                    ind.price > ind.vwap                 # Price above VWAP
                )

                # Bearish confirmation: EMA alignment + MACD + VWAP
                bearish_trend = (
                    ind.trend == "BEARISH" and           # EMA9 < EMA21 < EMA50
                    ind.macd_hist < 0 and                # MACD histogram negative
                    ind.price < ind.vwap                 # Price below VWAP
                )

                # RSI extremes can override trend (mean reversion)
                rsi_oversold = ind.rsi < 25              # Very oversold = potential long
                rsi_overbought = ind.rsi > 75           # Very overbought = potential short

                # Allow LONG if: bullish trend confirmed OR extreme oversold
                long_confirmed = bullish_trend or (rsi_oversold and trend_strength)

                # Allow SHORT if: bearish trend confirmed OR extreme overbought
                short_confirmed = bearish_trend or (rsi_overbought and trend_strength)

                # Execute based on AI signal + TREND CONFIRMATION
                if "LONG" in analysis and "WAIT" not in analysis:
                    if current_pos == "SHORT":
                        # Close short first - record the trade
                        self.state.status = "BOT: Closing SHORT..."
                        exit_price = ind.price
                        self.hl.place_market_order(self.state.symbol, "buy", abs(float(pos.get("szi", 0))), reduce_only=True)

                        # Record closed trade to database
                        if self.state.symbol in bot_positions:
                            self._record_bot_trade(bot_positions[self.state.symbol], exit_price, "signal_flip")
                            del bot_positions[self.state.symbol]
                        await asyncio.sleep(1)

                    if current_pos != "LONG":
                        # ═══ TREND CONFIRMATION CHECK ═══
                        if not long_confirmed:
                            self.state.status = f"BOT: LONG blocked (trend:{ind.trend[:4]} MACD:{ind.macd_hist:+.1f})"
                            await asyncio.sleep(30)
                            continue

                        self.state.status = f"BOT: LONG {size:.4f}..."
                        result = self.hl.place_market_order(
                            symbol=self.state.symbol,
                            side="buy",
                            size=size,
                            reduce_only=False
                        )
                        if result and result.get("success"):
                            self.state.status = f"BOT: LONG ✓ {size:.4f} (trend confirmed)"
                            # Track entry for later recording
                            bot_positions[self.state.symbol] = {
                                "entry_price": ind.price,
                                "entry_time": datetime.utcnow(),
                                "side": "long",
                                "size": size,
                                "conditions": entry_conditions,
                            }
                        else:
                            err = result.get("error", "Unknown") if result else "Failed"
                            self.state.status = f"BOT: LONG ✗ {str(err)[:10]}"
                        await asyncio.sleep(60)  # Wait after trade
                    else:
                        self.state.status = "BOT: Already LONG"

                elif "SHORT" in analysis and "WAIT" not in analysis:
                    if current_pos == "LONG":
                        # Close long first - record the trade
                        self.state.status = "BOT: Closing LONG..."
                        exit_price = ind.price
                        self.hl.place_market_order(self.state.symbol, "sell", abs(float(pos.get("szi", 0))), reduce_only=True)

                        # Record closed trade to database
                        if self.state.symbol in bot_positions:
                            self._record_bot_trade(bot_positions[self.state.symbol], exit_price, "signal_flip")
                            del bot_positions[self.state.symbol]
                        await asyncio.sleep(1)

                    if current_pos != "SHORT":
                        # ═══ TREND CONFIRMATION CHECK ═══
                        if not short_confirmed:
                            self.state.status = f"BOT: SHORT blocked (trend:{ind.trend[:4]} MACD:{ind.macd_hist:+.1f})"
                            await asyncio.sleep(30)
                            continue

                        self.state.status = f"BOT: SHORT {size:.4f}..."
                        result = self.hl.place_market_order(
                            symbol=self.state.symbol,
                            side="sell",
                            size=size,
                            reduce_only=False
                        )
                        if result and result.get("success"):
                            self.state.status = f"BOT: SHORT ✓ {size:.4f} (trend confirmed)"
                            # Track entry for later recording
                            bot_positions[self.state.symbol] = {
                                "entry_price": ind.price,
                                "entry_time": datetime.utcnow(),
                                "side": "short",
                                "size": size,
                                "conditions": entry_conditions,
                            }
                        else:
                            err = result.get("error", "Unknown") if result else "Failed"
                            self.state.status = f"BOT: SHORT ✗ {str(err)[:10]}"
                        await asyncio.sleep(60)
                    else:
                        self.state.status = "BOT: Already SHORT"
                else:
                    self.state.status = "BOT: Scanning..."

                # Check every 30 seconds
                await asyncio.sleep(30)

            except Exception as e:
                self.state.status = f"BOT ERR: {str(e)[:15]}"
                await asyncio.sleep(10)

        self.state.status = "BOT: Stopped"

    def _record_bot_trade(self, position: dict, exit_price: float, exit_reason: str):
        """Record a completed bot trade to the database for learning."""
        from datetime import datetime
        from src.database import get_db
        import json

        try:
            db = get_db()
            entry_price = position["entry_price"]
            side = position["side"]
            size = position["size"]
            entry_time = position["entry_time"]
            conditions = position.get("conditions", {})

            # Calculate PnL
            if side == "long":
                pnl_pct = ((exit_price - entry_price) / entry_price) * 100
            else:
                pnl_pct = ((entry_price - exit_price) / entry_price) * 100

            pnl_usd = size * entry_price * (pnl_pct / 100)

            # Save to completed_trades table
            db.save_completed_trade(
                symbol=self.state.symbol,
                side=side,
                entry_price=entry_price,
                exit_price=exit_price,
                size=size,
                entry_time=entry_time.isoformat(),
                exit_time=datetime.utcnow().isoformat(),
                pnl_pct=pnl_pct,
                pnl_usd=pnl_usd,
                exit_reason=exit_reason,
                entry_conditions=conditions
            )

            emoji = "✅" if pnl_usd > 0 else "❌"
            self.state.status = f"BOT: {emoji} {side.upper()} closed ${pnl_usd:+.2f}"

        except Exception as e:
            # Don't crash bot if recording fails
            pass

    async def _submit_order(self):
        """Submit the order from the input bar to Hyperliquid."""
        if not self.state.order_input or not self.state.order_side:
            return

        if not self.hl:
            self.state.status = "NO HL CLIENT"
            return

        try:
            ind = self.state.indicators
            size_str = self.state.order_input

            # Parse size - handle $ prefix for USD amount
            if size_str.startswith('$'):
                usd_amount = float(size_str[1:])
                size = usd_amount / ind.price if ind.price > 0 else 0
            else:
                size = float(size_str)

            if size <= 0:
                self.state.status = "INVALID SIZE"
                return

            # Determine side
            side = "buy" if self.state.order_side == "LONG" else "sell"

            self.state.status = f"PLACING {self.state.order_side} {size:.4f}..."

            # Place market order on Hyperliquid
            result = self.hl.place_market_order(
                symbol=self.state.symbol,
                side=side,
                size=size,
                reduce_only=False
            )

            if result and result.get("success"):
                filled_size = result.get("filled_size", size)
                avg_price = result.get("avg_price", ind.price)
                self.state.status = f"{self.state.order_side} ✓ {filled_size:.4f} @ ${avg_price:,.2f}"
            else:
                error = result.get("error", "Unknown") if result else "Failed"
                self.state.status = f"FAILED: {str(error)[:20]}"

        except Exception as e:
            self.state.status = f"ERROR: {str(e)[:20]}"
        finally:
            # Clear order entry
            self.state.order_side = ""
            self.state.order_input = ""

    async def run(self, symbol: str = "BTC"):
        """Run the live trading dashboard."""
        self.state.symbol = symbol.upper()
        self.running = True

        if not self.hl:
            self.console.print("[red]Error: No Hyperliquid client![/]")
            return

        self.console.clear()
        self._fetch_data()
        self._fetch_watchlist()  # Load all tickers data

        # Setup non-blocking input
        import termios
        import tty
        old_settings = termios.tcgetattr(sys.stdin)

        try:
            tty.setcbreak(sys.stdin.fileno())

            with Live(self._make_layout(), console=self.console, refresh_per_second=2, screen=True) as live:
                self._live = live
                last_fetch = time.time()

                while self.running:
                    # Non-blocking keyboard input
                    if select.select([sys.stdin], [], [], 0)[0]:
                        key = sys.stdin.read(1)

                        # Check for escape key (ESC = \x1b)
                        if key == '\x1b':
                            # Clear order entry
                            self.state.order_side = ""
                            self.state.order_input = ""
                            continue

                        key_lower = key.lower()

                        # If in order entry mode, handle input
                        if self.state.order_side:
                            if key == '\n' or key == '\r':
                                # Submit order
                                if self.state.order_input:
                                    await self._submit_order()
                            elif key == '\x7f' or key == '\b':
                                # Backspace
                                self.state.order_input = self.state.order_input[:-1]
                            elif key.isdigit() or key in '.$':
                                # Add to input (numbers, decimal, dollar sign)
                                self.state.order_input += key
                            continue

                        # Normal mode keys
                        if key_lower == 'q':
                            self.running = False
                            break
                        elif key_lower == 'l':
                            # Long button
                            self.state.order_side = "LONG"
                            self.state.order_input = ""
                            self.state.ai_analysis = ""
                        elif key_lower == 's':
                            # Short button
                            self.state.order_side = "SHORT"
                            self.state.order_input = ""
                            self.state.ai_analysis = ""
                        elif key_lower == 'b':
                            # Toggle AI trading bot - prompt for size if starting
                            if not self.state.bot_running:
                                # Stop live to get user input
                                live.stop()
                                termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)
                                position_size = await self._prompt_bot_size()
                                self.console.clear()
                                tty.setcbreak(sys.stdin.fileno())
                                live.start()

                                if position_size:
                                    self.state.bot_running = True
                                    self.state.status = f"BOT STARTED (${position_size}/pos)"
                                    asyncio.create_task(self._run_ai_bot(position_size))
                            else:
                                self.state.bot_running = False
                                self.state.status = "BOT STOPPED"
                        elif key_lower == 'a':
                            # Ask AI - open chat
                            live.stop()
                            termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)
                            await self._chat_mode()
                            self.console.clear()
                            tty.setcbreak(sys.stdin.fileno())
                            live.start()
                        elif key_lower == 't':
                            self._cycle_timeframe()
                        elif key_lower == 'r':
                            self._fetch_data()
                            self._fetch_watchlist()
                        elif key_lower == 'c' and self.llm:
                            # Chat mode
                            live.stop()
                            termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)
                            await self._chat_mode()
                            self.console.clear()
                            tty.setcbreak(sys.stdin.fileno())
                            live.start()
                        elif key in '1234567':
                            # Quick switch to ticker 1-7
                            idx = int(key) - 1
                            if idx < len(self.watchlist_tickers):
                                self.state.symbol = self.watchlist_tickers[idx]
                                self._fetch_data()

                    # Auto-refresh every 5 seconds
                    if time.time() - last_fetch > 5:
                        self._fetch_data()
                        self._fetch_watchlist()
                        last_fetch = time.time()

                    live.update(self._make_layout())
                    await asyncio.sleep(0.1)

        except KeyboardInterrupt:
            self.running = False
        finally:
            termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)
            self._live = None

    async def _chat_mode(self):
        """Interactive AI chat about current market."""
        from rich.prompt import Prompt

        self.console.print("\n[bold cyan]💬 AI Chat Mode[/] (type 'exit' to return)\n")

        while True:
            try:
                question = Prompt.ask("[cyan]You[/]")
                if question.lower() in ['exit', 'quit', 'q', '']:
                    break

                self.console.print("[dim]Thinking...[/]")

                # Build context
                ind = self.state.indicators
                context = f"""Current {self.state.symbol} Market:
- Price: ${ind.price:,.2f}
- RSI: {ind.rsi:.1f}
- MACD: {ind.macd:.2f} (Signal: {ind.macd_signal:.2f})
- Trend: {ind.trend}
- Support: ${ind.support:,.2f}
- Resistance: ${ind.resistance:,.2f}
- ATR: {ind.atr_pct:.2f}%

User question: {question}"""

                response = self.llm.deepseek_client.chat.completions.create(
                    model="deepseek-chat",
                    messages=[
                        {"role": "system", "content": "You're a crypto trading assistant. Be concise (2-3 sentences). Use the data provided."},
                        {"role": "user", "content": context}
                    ],
                    max_tokens=150,
                    temperature=0.7
                )

                self.console.print(f"[green]AI:[/] {response.choices[0].message.content.strip()}\n")

            except KeyboardInterrupt:
                break
            except Exception as e:
                self.console.print(f"[red]Error: {e}[/]\n")
