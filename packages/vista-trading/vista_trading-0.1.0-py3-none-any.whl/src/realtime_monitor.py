"""
Real-Time Price Monitor with Event-Driven AI Analysis

Streams prices via WebSocket and triggers AI analysis only when significant events occur:
- Breakouts (price breaks S/R levels)
- S/R touches (price approaches key levels)
- Volume spikes (unusual activity)
- Volatility expansions (sudden moves)

No third-party setup required - uses Hyperliquid's built-in WebSocket.
"""

import asyncio
import json
import logging
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass, field, asdict
from collections import deque
import websockets

from src.tickers import TRADING_TICKERS, format_price
from src.database import get_db

logger = logging.getLogger(__name__)


@dataclass
class PriceEvent:
    """Represents a significant price event that triggers analysis."""
    event_type: str  # "breakout", "sr_touch", "volume_spike", "volatility"
    symbol: str
    price: float
    timestamp: datetime
    details: Dict[str, Any] = field(default_factory=dict)
    severity: str = "medium"  # "low", "medium", "high", "critical"


@dataclass 
class SymbolState:
    """Tracks real-time state for a symbol."""
    symbol: str
    last_price: float = 0.0
    prices: deque = field(default_factory=lambda: deque(maxlen=1000))  # Last 1000 ticks
    volumes: deque = field(default_factory=lambda: deque(maxlen=100))  # Last 100 volume readings
    
    # Support/Resistance levels (updated periodically)
    support_levels: List[float] = field(default_factory=list)
    resistance_levels: List[float] = field(default_factory=list)
    
    # Volatility tracking
    high_1m: float = 0.0
    low_1m: float = float('inf')
    last_1m_reset: datetime = field(default_factory=datetime.utcnow)
    
    # Event cooldowns (prevent spam)
    last_sr_alert: datetime = field(default_factory=lambda: datetime.min)
    last_breakout_alert: datetime = field(default_factory=lambda: datetime.min)
    last_volatility_alert: datetime = field(default_factory=lambda: datetime.min)
    last_volume_alert: datetime = field(default_factory=lambda: datetime.min)


class LearningDataStore:
    """Persists market events (S/R exits, whale trades) for learning.

    Now uses SQLite database for efficient storage and querying.

    Tracks:
    - S/R breakout events with subsequent price movement (continuation vs reversal)
    - Whale position changes with price movement after

    This data helps the bot learn:
    - Which S/R levels are significant (hold vs break)
    - Whether to follow whale trades or fade them
    """

    def __init__(self):
        self.db = get_db()
        logger.info("📀 LearningDataStore using SQLite database")

    def record_sr_event(self, event: PriceEvent) -> None:
        """Record an S/R breakout event for learning."""
        if event.event_type != "breakout":
            return

        self.db.save_sr_event(
            symbol=event.symbol,
            price=event.price,
            level=event.details.get("level"),
            direction=event.details.get("direction"),
            break_pct=event.details.get("break_pct"),
            timestamp=event.timestamp.isoformat()
        )
        logger.info(f"📀 Recorded S/R event: {event.symbol} {event.details.get('direction')} @ {format_price(event.price)}")

    def record_whale_event(self, whale_data: Dict, action: str) -> None:
        """Record a whale position change for learning.

        Args:
            whale_data: Dict with whale, symbol, side, size, entry_price, etc.
            action: "opened" or "closed"
        """
        self.db.save_whale_event(
            whale=whale_data.get("whale"),
            symbol=whale_data.get("symbol"),
            action=action,
            side=whale_data.get("side"),
            size=whale_data.get("size"),
            entry_price=whale_data.get("entry_price"),
            leverage=whale_data.get("leverage"),
            notional_usd=whale_data.get("notional_usd")
        )
        logger.info(f"📀 Recorded whale event: {whale_data.get('whale')} {action} {whale_data.get('side')} {whale_data.get('symbol')}")

    def get_sr_stats(self, symbol: str = None) -> Dict:
        """Get statistics on S/R breakout outcomes from database."""
        stats = self.db.get_signal_accuracy_stats()
        return stats.get("sr_breakouts", {"total": 0, "continuation_rate": 0.5})

    def get_whale_stats(self, whale_name: str = None) -> Dict:
        """Get statistics on whale trade outcomes from database."""
        stats = self.db.get_signal_accuracy_stats()
        whale_stats = stats.get("whale_follow", {})
        return {
            "total": whale_stats.get("total", 0),
            "profitable_follows": whale_stats.get("profitable", 0),
            "follow_win_rate": whale_stats.get("accuracy", 0.5),
        }


class RealtimeMonitor:
    """
    Real-time price streaming with event detection.
    
    Connects to Hyperliquid WebSocket and detects:
    1. S/R level touches (within 0.2%)
    2. Breakouts (price crosses S/R with momentum)
    3. Volume spikes (3x average)
    4. Volatility expansions (>1% move in 1 minute)
    """
    
    # Hyperliquid WebSocket endpoints
    WS_MAINNET = "wss://api.hyperliquid.xyz/ws"
    WS_TESTNET = "wss://api.hyperliquid-testnet.xyz/ws"
    
    def __init__(
        self,
        symbols: List[str] = None,
        testnet: bool = True,
        on_event: Callable[[PriceEvent], None] = None
    ):
        self.symbols = symbols or TRADING_TICKERS
        self.testnet = testnet
        self.ws_url = self.WS_TESTNET if testnet else self.WS_MAINNET
        self.on_event = on_event  # Callback for events
        
        # State per symbol
        self.states: Dict[str, SymbolState] = {
            s: SymbolState(symbol=s) for s in self.symbols
        }
        
        # Connection state
        self.ws: Optional[websockets.WebSocketClientProtocol] = None
        self.is_running = False
        self.reconnect_delay = 1  # Seconds
        
        # Event detection thresholds
        self.sr_proximity_pct = 0.2     # Alert when within 0.2% of S/R
        self.breakout_confirm_pct = 0.1  # Confirm breakout after 0.1% beyond level
        self.volume_spike_mult = 3.0     # Volume > 3x average
        self.volatility_threshold_pct = 1.0  # 1% move in 1 minute
        
        # Cooldowns (prevent alert spam)
        self.sr_cooldown_seconds = 300      # 5 min between S/R alerts
        self.breakout_cooldown_seconds = 60  # 1 min between breakout alerts
        self.volatility_cooldown_seconds = 60
        self.volume_cooldown_seconds = 120
        
        # Statistics
        self.ticks_received = 0
        self.events_triggered = 0
        self.start_time: Optional[datetime] = None
        
        logger.info(f"RealtimeMonitor initialized for {self.symbols}")

    def set_sr_levels(self, symbol: str, supports: List[float], resistances: List[float]):
        """Update S/R levels for a symbol (call this from main bot)."""
        if symbol in self.states:
            self.states[symbol].support_levels = sorted(supports, reverse=True)
            self.states[symbol].resistance_levels = sorted(resistances)
            logger.debug(f"{symbol} S/R updated: S={supports}, R={resistances}")

    async def start(self):
        """Start the WebSocket connection and event loop."""
        self.is_running = True
        self.start_time = datetime.utcnow()
        logger.info(f"🔴 LIVE: Starting real-time monitor on {self.ws_url}")

        while self.is_running:
            try:
                await self._connect_and_stream()
            except Exception as e:
                logger.error(f"WebSocket error: {e}")
                if self.is_running:
                    logger.info(f"Reconnecting in {self.reconnect_delay}s...")
                    await asyncio.sleep(self.reconnect_delay)
                    self.reconnect_delay = min(self.reconnect_delay * 2, 30)

    async def stop(self):
        """Stop the monitor."""
        self.is_running = False
        if self.ws:
            await self.ws.close()
        logger.info(f"Monitor stopped. Ticks: {self.ticks_received}, Events: {self.events_triggered}")

    async def _connect_and_stream(self):
        """Connect to WebSocket and stream prices."""
        async with websockets.connect(self.ws_url) as ws:
            self.ws = ws
            self.reconnect_delay = 1  # Reset on successful connect
            logger.info("✅ WebSocket connected")

            # Subscribe to all symbols
            for symbol in self.symbols:
                subscribe_msg = {
                    "method": "subscribe",
                    "subscription": {"type": "allMids"}
                }
                await ws.send(json.dumps(subscribe_msg))

            logger.info(f"📡 Subscribed to price feeds: {self.symbols}")

            # Process incoming messages
            async for message in ws:
                if not self.is_running:
                    break
                await self._handle_message(message)

    async def _handle_message(self, message: str):
        """Handle incoming WebSocket message."""
        try:
            data = json.loads(message)

            # Handle allMids updates (price updates for all symbols)
            if data.get("channel") == "allMids":
                mids = data.get("data", {}).get("mids", {})
                for symbol in self.symbols:
                    if symbol in mids:
                        price = float(mids[symbol])
                        await self._process_price(symbol, price)

        except json.JSONDecodeError:
            logger.warning(f"Invalid JSON: {message[:100]}")
        except Exception as e:
            logger.error(f"Error handling message: {e}")

    async def _process_price(self, symbol: str, price: float):
        """Process a new price tick and check for events."""
        state = self.states[symbol]
        now = datetime.utcnow()
        self.ticks_received += 1

        # Update state
        old_price = state.last_price
        state.last_price = price
        state.prices.append((now, price))

        # Update 1-minute high/low
        if (now - state.last_1m_reset).total_seconds() > 60:
            state.high_1m = price
            state.low_1m = price
            state.last_1m_reset = now
        else:
            state.high_1m = max(state.high_1m, price)
            state.low_1m = min(state.low_1m, price)

        # Skip event detection on first tick
        if old_price == 0:
            return

        # === EVENT DETECTION ===

        # 1. S/R Level Touch
        await self._check_sr_touch(state, price, now)

        # 2. Breakout Detection
        await self._check_breakout(state, price, old_price, now)

        # 3. Volatility Spike
        await self._check_volatility(state, price, now)

    async def _check_sr_touch(self, state: SymbolState, price: float, now: datetime):
        """Check if price is touching S/R levels."""
        if (now - state.last_sr_alert).total_seconds() < self.sr_cooldown_seconds:
            return

        # Check supports
        for support in state.support_levels:
            distance_pct = abs(price - support) / support * 100
            if distance_pct <= self.sr_proximity_pct:
                event = PriceEvent(
                    event_type="sr_touch",
                    symbol=state.symbol,
                    price=price,
                    timestamp=now,
                    details={"level": support, "type": "support", "distance_pct": distance_pct},
                    severity="high" if distance_pct < 0.1 else "medium"
                )
                await self._trigger_event(event)
                state.last_sr_alert = now
                return

        # Check resistances
        for resistance in state.resistance_levels:
            distance_pct = abs(price - resistance) / resistance * 100
            if distance_pct <= self.sr_proximity_pct:
                event = PriceEvent(
                    event_type="sr_touch",
                    symbol=state.symbol,
                    price=price,
                    timestamp=now,
                    details={"level": resistance, "type": "resistance", "distance_pct": distance_pct},
                    severity="high" if distance_pct < 0.1 else "medium"
                )
                await self._trigger_event(event)
                state.last_sr_alert = now
                return

    async def _check_breakout(self, state: SymbolState, price: float, old_price: float, now: datetime):
        """Check for breakouts through S/R levels."""
        if (now - state.last_breakout_alert).total_seconds() < self.breakout_cooldown_seconds:
            return

        # Breakout above resistance
        for resistance in state.resistance_levels:
            if old_price < resistance and price > resistance * (1 + self.breakout_confirm_pct / 100):
                event = PriceEvent(
                    event_type="breakout",
                    symbol=state.symbol,
                    price=price,
                    timestamp=now,
                    details={
                        "level": resistance,
                        "direction": "bullish",
                        "break_pct": (price - resistance) / resistance * 100
                    },
                    severity="critical"
                )
                await self._trigger_event(event)
                state.last_breakout_alert = now
                return

        # Breakdown below support
        for support in state.support_levels:
            if old_price > support and price < support * (1 - self.breakout_confirm_pct / 100):
                event = PriceEvent(
                    event_type="breakout",
                    symbol=state.symbol,
                    price=price,
                    timestamp=now,
                    details={
                        "level": support,
                        "direction": "bearish",
                        "break_pct": (support - price) / support * 100
                    },
                    severity="critical"
                )
                await self._trigger_event(event)
                state.last_breakout_alert = now
                return

    async def _check_volatility(self, state: SymbolState, price: float, now: datetime):
        """Check for volatility spikes."""
        if (now - state.last_volatility_alert).total_seconds() < self.volatility_cooldown_seconds:
            return

        # Calculate 1-minute range
        range_pct = (state.high_1m - state.low_1m) / state.low_1m * 100 if state.low_1m > 0 else 0

        if range_pct >= self.volatility_threshold_pct:
            direction = "up" if price > (state.high_1m + state.low_1m) / 2 else "down"
            event = PriceEvent(
                event_type="volatility",
                symbol=state.symbol,
                price=price,
                timestamp=now,
                details={
                    "range_pct": round(range_pct, 2),
                    "high_1m": state.high_1m,
                    "low_1m": state.low_1m,
                    "direction": direction
                },
                severity="high" if range_pct > 2.0 else "medium"
            )
            await self._trigger_event(event)
            state.last_volatility_alert = now

    async def _trigger_event(self, event: PriceEvent):
        """Trigger an event - log and call callback."""
        self.events_triggered += 1

        # Log with severity-appropriate emoji
        emoji = {
            "sr_touch": "📍",
            "breakout": "🚀" if event.details.get("direction") == "bullish" else "💥",
            "volatility": "⚡",
            "volume_spike": "📊"
        }.get(event.event_type, "🔔")

        severity_color = {
            "low": "",
            "medium": "🟡",
            "high": "🟠",
            "critical": "🔴"
        }.get(event.severity, "")

        logger.info(
            f"{emoji} {severity_color} [{event.symbol}] {event.event_type.upper()}: "
            f"${event.price:,.2f} | {event.details}"
        )

        # Call the callback (this triggers AI analysis)
        if self.on_event:
            try:
                if asyncio.iscoroutinefunction(self.on_event):
                    await self.on_event(event)
                else:
                    self.on_event(event)
            except Exception as e:
                logger.error(f"Event callback error: {e}")

    def get_stats(self) -> Dict[str, Any]:
        """Get monitoring statistics."""
        uptime = (datetime.utcnow() - self.start_time).total_seconds() if self.start_time else 0
        return {
            "uptime_seconds": uptime,
            "ticks_received": self.ticks_received,
            "events_triggered": self.events_triggered,
            "ticks_per_second": self.ticks_received / uptime if uptime > 0 else 0,
            "symbols": self.symbols,
            "current_prices": {s: self.states[s].last_price for s in self.symbols}
        }


class EventDrivenAnalyzer:
    """
    Connects RealtimeMonitor to AI analysis.

    Only triggers expensive AI calls when significant events occur.
    This saves ~95% of analysis costs compared to polling.
    """

    def __init__(
        self,
        chart_analyzer,  # ChartAnalyzer instance
        llm_service,     # LLMService instance
        hl_client,       # HyperliquidClient for getting candles
        discord=None,    # Optional Discord notifier
        signal_learner=None  # Optional signal learner for training from charts
    ):
        self.chart_analyzer = chart_analyzer
        self.llm_service = llm_service
        self.hl_client = hl_client
        self.discord = discord
        self.signal_learner = signal_learner  # For learning from chart signals

        # Track recent analyses to prevent spam
        self.last_analysis: Dict[str, datetime] = {}
        self.analysis_cooldown_seconds = 60  # Min 1 minute between analyses

        # Analysis results cache
        self.cached_analyses: Dict[str, Dict] = {}

        # Learning data persistence
        self.learning_store = LearningDataStore()

        # Chart scheduler for periodic chart generation
        self.chart_scheduler = None
        self._chart_scheduler_task = None

        logger.info("EventDrivenAnalyzer initialized")

    async def start_chart_scheduler(self):
        """Start the chart scheduler for periodic chart generation."""
        try:
            from src.chart_scheduler import ChartScheduler

            logger.info("📊 Initializing chart scheduler...")
            self.chart_scheduler = ChartScheduler(
                hl_client=self.hl_client,
                discord_notifier=self.discord,
                llm_service=self.llm_service,
                signal_learner=self.signal_learner  # Pass signal learner for training
            )

            # Start scheduler as background task
            self._chart_scheduler_task = asyncio.create_task(
                self.chart_scheduler.run_scheduler()
            )
            logger.info("📊 Chart scheduler started (30m intervals for 5m charts, 24h for daily)")

        except Exception as e:
            logger.error(f"Failed to start chart scheduler: {e}", exc_info=True)

    async def stop_chart_scheduler(self):
        """Stop the chart scheduler."""
        if self._chart_scheduler_task:
            self._chart_scheduler_task.cancel()
            try:
                await self._chart_scheduler_task
            except asyncio.CancelledError:
                pass
            logger.info("Chart scheduler stopped")

    async def handle_event(self, event: PriceEvent):
        """Handle a price event - decide if AI analysis is needed."""
        symbol = event.symbol
        now = datetime.utcnow()

        # Record S/R breakouts for learning (even if cooldown active)
        if event.event_type == "breakout":
            self.learning_store.record_sr_event(event)

        # Check cooldown
        last = self.last_analysis.get(symbol, datetime.min)
        if (now - last).total_seconds() < self.analysis_cooldown_seconds:
            logger.debug(f"Skipping {symbol} analysis (cooldown)")
            return

        # Determine analysis depth based on event severity
        if event.severity == "critical":
            # CRITICAL: Full deep analysis
            analysis = await self._deep_analysis(symbol, event)
        elif event.severity == "high":
            # HIGH: Quick chart analysis
            analysis = await self._quick_analysis(symbol, event)
        else:
            # MEDIUM/LOW: Just log, no AI call
            logger.info(f"📝 {symbol} event logged (no AI trigger): {event.event_type}")
            return

        self.last_analysis[symbol] = now
        self.cached_analyses[symbol] = analysis

        # Send to Discord if critical
        if event.severity == "critical" and self.discord:
            await self._notify_discord(event, analysis)

    async def _quick_analysis(self, symbol: str, event: PriceEvent) -> Dict:
        """Quick chart analysis using DeepSeek (cheap, ~$0.0003)."""
        try:
            logger.info(f"⚡ Quick analysis triggered for {symbol}")

            # Get recent candles (5m timeframe for speed)
            candles = self.hl_client.get_candles(symbol, interval="5m", limit=50)

            if not candles or len(candles) < 20:
                return {"error": "Insufficient candle data"}

            # Use DeepSeek text analysis (cheap)
            analysis = self.chart_analyzer.analyze_chart_with_deepseek(
                candles, symbol, "5m"
            )

            analysis["event"] = event.event_type
            analysis["event_details"] = event.details
            analysis["timestamp"] = datetime.utcnow().isoformat()

            logger.info(
                f"📊 {symbol} Quick Analysis: {analysis.get('trend_direction', 'unknown')} "
                f"(strength: {analysis.get('trend_strength', 0)}/10)"
            )

            return analysis

        except Exception as e:
            logger.error(f"Quick analysis failed: {e}")
            return {"error": str(e)}

    async def _deep_analysis(self, symbol: str, event: PriceEvent) -> Dict:
        """Deep analysis for critical events (uses more AI)."""
        try:
            logger.info(f"🔬 Deep analysis triggered for {symbol} ({event.event_type})")

            # Get candles for multiple timeframes
            candles_5m = self.hl_client.get_candles(symbol, interval="5m", limit=100)
            candles_1h = self.hl_client.get_candles(symbol, interval="1h", limit=50)

            # Quick analysis on 5m
            analysis_5m = self.chart_analyzer.analyze_chart_with_deepseek(
                candles_5m, symbol, "5m"
            ) if candles_5m else {}

            # Trend analysis on 1h
            analysis_1h = self.chart_analyzer.analyze_chart_with_deepseek(
                candles_1h, symbol, "1h"
            ) if candles_1h else {}

            # Combine analyses
            combined = {
                "symbol": symbol,
                "event": event.event_type,
                "event_details": event.details,
                "price": event.price,
                "timestamp": datetime.utcnow().isoformat(),
                "analysis_5m": analysis_5m,
                "analysis_1h": analysis_1h,
                "trend_5m": analysis_5m.get("trend_direction", "unknown"),
                "trend_1h": analysis_1h.get("trend_direction", "unknown"),
                "strength_5m": analysis_5m.get("trend_strength", 0),
                "strength_1h": analysis_1h.get("trend_strength", 0),
            }

            # Determine overall signal
            if event.event_type == "breakout":
                direction = event.details.get("direction", "")
                if direction == "bullish" and analysis_5m.get("trend_direction") == "bullish":
                    combined["signal"] = "STRONG_LONG"
                elif direction == "bearish" and analysis_5m.get("trend_direction") == "bearish":
                    combined["signal"] = "STRONG_SHORT"
                else:
                    combined["signal"] = "CAUTION"  # Breakout but trend doesn't confirm

            logger.info(
                f"🎯 {symbol} Deep Analysis: {combined.get('signal', 'N/A')} | "
                f"5m: {combined['trend_5m']} | 1h: {combined['trend_1h']}"
            )

            return combined

        except Exception as e:
            logger.error(f"Deep analysis failed: {e}")
            return {"error": str(e)}

    async def _notify_discord(self, event: PriceEvent, analysis: Dict):
        """Send critical event notification to Discord → ticker-specific channel."""
        if not self.discord:
            return

        try:
            symbol = event.symbol
            level = event.details.get("level", 0)
            direction = event.details.get("direction", "")

            # Use dedicated breakout alert method (goes to ticker channel)
            if event.event_type == "breakout":
                breakout_type = "breaking_resistance" if direction == "bullish" else "breaking_support"
                confidence = 0.8 if analysis.get("signal", "").startswith("STRONG") else 0.5

                await self.discord.send_breakout_alert(
                    symbol=symbol,
                    breakout_type=breakout_type,
                    price=event.price,
                    level=level,
                    confidence=confidence
                )
            elif event.event_type == "sr_touch":
                level_type = event.details.get("type", "support")
                await self.discord.send_sr_alert(
                    symbol=symbol,
                    level_type=level_type,
                    price=event.price,
                    level=level
                )
            else:
                # Generic alert for other event types
                emoji = "🚀" if direction == "bullish" else "💥"
                signal = analysis.get("signal", "REVIEW")
                message = (
                    f"{emoji} **{event.event_type.upper()}** ${symbol}\n"
                    f"Price: ${event.price:,.2f}\n"
                    f"Signal: **{signal}**"
                )
                await self.discord.send_alert(message)

        except Exception as e:
            logger.error(f"Discord notification failed: {e}")

