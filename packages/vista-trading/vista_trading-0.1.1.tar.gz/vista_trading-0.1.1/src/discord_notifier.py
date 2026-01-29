"""
Discord Notifier - Multi-channel market analysis bot.

CHANNEL STRUCTURE:
- #btc-signals    → BTC-specific trading signals
- #eth-signals    → ETH-specific trading signals
- #alpha-calls    → AI trade setups with @everyone alerts
- #liquidations   → Liquidation alerts
- #whales         → Whale activity alerts
- #assistant      → User chat with AI (NO account/trade data)

SECURITY:
- NEVER sends account balances, position sizes, or trade details
- #assistant channel has NO access to trading bot data
- Only public market data is shared
"""

import asyncio
import logging
from typing import Dict, Any, Optional
from datetime import datetime
from dataclasses import dataclass, field

from src.tickers import TRADING_TICKERS, format_price
from src.database import get_db

logger = logging.getLogger(__name__)

try:
    import discord
    from discord.ext import commands
    DISCORD_AVAILABLE = True
except ImportError:
    DISCORD_AVAILABLE = False
    logger.warning("discord.py not installed. Run: pip install discord.py")


@dataclass
class DiscordChannels:
    """Discord channel IDs for different message types.

    Signal channels are stored in a dict keyed by ticker symbol.
    All tickers from TRADING_TICKERS use the same dynamic lookup.

    To add a new ticker:
    1. Add to TRADING_TICKERS in src/tickers.py
    2. Add DISCORD_CHANNEL_{SYMBOL}_SIGNALS to .env
    """
    # Per-ticker signal channels: {"BTC": 123456, "ETH": 789012, ...}
    # Populated dynamically from env vars for all TRADING_TICKERS
    signal_channels: Dict[str, int] = field(default_factory=dict)

    # Special channels
    alpha_calls: Optional[int] = None  # Trade setups with @everyone
    liquidations: Optional[int] = None
    whales: Optional[int] = None
    assistant: Optional[int] = None
    default: Optional[int] = None  # Fallback channel

    def get_signal_channel(self, symbol: str) -> Optional[int]:
        """Get signal channel for a symbol."""
        return self.signal_channels.get(symbol.upper()) or self.default

    @classmethod
    def from_env(cls, env_getter) -> "DiscordChannels":
        """Create DiscordChannels from environment variables.

        Args:
            env_getter: Function that takes env var name and returns value (e.g., os.getenv)

        Returns:
            DiscordChannels with all channels populated from env
        """
        def parse_channel(key: str) -> Optional[int]:
            val = env_getter(key, "")
            if val:
                val = val.strip()
            return int(val) if val else None

        # Load signal channels for ALL trading tickers dynamically
        signal_channels = {}
        for ticker in TRADING_TICKERS:
            channel_id = parse_channel(f"DISCORD_CHANNEL_{ticker}_SIGNALS")
            if channel_id:
                signal_channels[ticker] = channel_id

        return cls(
            signal_channels=signal_channels,
            alpha_calls=parse_channel("DISCORD_CHANNEL_ALPHA_CALLS"),
            liquidations=parse_channel("DISCORD_CHANNEL_LIQUIDATIONS"),
            whales=parse_channel("DISCORD_CHANNEL_WHALES"),
            assistant=parse_channel("DISCORD_CHANNEL_ASSISTANT"),
            default=parse_channel("DISCORD_CHANNEL_ID"),
        )


class DiscordNotifier:
    """Multi-channel Discord bot for market analysis."""

    def __init__(self, bot_token: str, channel_id: int = None, channels: DiscordChannels = None):
        """Initialize Discord notifier.

        Args:
            bot_token: Discord bot token
            channel_id: Default channel ID (legacy support)
            channels: DiscordChannels dataclass with all channel IDs
        """
        self.bot_token = bot_token
        self.channels = channels or DiscordChannels(default=channel_id)
        if channel_id and not self.channels.default:
            self.channels.default = channel_id

        self.client: Optional[discord.Client] = None
        self.is_ready = False
        self._message_queue: list = []
        self._llm_service = None  # Will be set for assistant channel

        if not DISCORD_AVAILABLE:
            logger.error("Discord not available - install discord.py")
            return

    def set_llm_service(self, llm_service):
        """Set LLM service for assistant channel responses."""
        self._llm_service = llm_service

    async def connect(self) -> bool:
        """Connect to Discord with message handling.

        NOTE: If using assistant channel, enable "Message Content Intent" in Discord Developer Portal:
        https://discord.com/developers/applications/ → Your Bot → Bot → Privileged Gateway Intents
        """
        if not DISCORD_AVAILABLE:
            return False

        try:
            intents = discord.Intents.default()
            # Only request message_content if assistant channel is configured
            # This requires enabling "Message Content Intent" in Discord Developer Portal
            if self.channels.assistant:
                intents.message_content = True
            self.client = discord.Client(intents=intents)

            @self.client.event
            async def on_ready():
                logger.info(f"Discord bot connected as {self.client.user}")
                self.is_ready = True
                # Send any queued messages
                for channel_id, msg in self._message_queue:
                    await self._send_to_channel(channel_id, msg)
                self._message_queue.clear()

            @self.client.event
            async def on_message(message):
                # Ignore own messages
                if message.author == self.client.user:
                    return

                # Handle assistant channel messages
                if self.channels.assistant and message.channel.id == self.channels.assistant:
                    await self._handle_assistant_message(message)

            # Start bot in background
            asyncio.create_task(self.client.start(self.bot_token))

            # Wait for ready (max 10 seconds)
            for _ in range(20):
                if self.is_ready:
                    return True
                await asyncio.sleep(0.5)

            logger.warning("Discord connection timed out - check bot token and intents")
            return False

        except discord.errors.PrivilegedIntentsRequired:
            logger.error(
                "Discord requires 'Message Content Intent' for assistant channel. "
                "Enable it at: https://discord.com/developers/applications/ → Bot → Privileged Gateway Intents"
            )
            return False
        except Exception as e:
            logger.error(f"Failed to connect to Discord: {e}")
            return False

    async def _handle_assistant_message(self, message):
        """Handle messages in #assistant channel - AI chat with NO trading data."""
        if not self._llm_service:
            await message.channel.send("🤖 AI assistant not configured.")
            return

        user_msg = message.content.strip()
        if not user_msg:
            return

        # Block any attempts to get trading/account info
        blocked_keywords = ['balance', 'position', 'trade', 'pnl', 'profit', 'loss',
                          'account', 'wallet', 'equity', 'margin', 'order']
        if any(kw in user_msg.lower() for kw in blocked_keywords):
            await message.channel.send(
                "🚫 I can't share trading account information. "
                "Ask me about market analysis, technical indicators, or trading concepts instead!"
            )
            return

        try:
            # Show typing indicator
            async with message.channel.typing():
                # Use LLM for general market/trading education
                response = await self._get_assistant_response(user_msg)

                # Split long responses
                if len(response) > 2000:
                    for i in range(0, len(response), 2000):
                        await message.channel.send(response[i:i+2000])
                else:
                    await message.channel.send(response)
        except Exception as e:
            logger.error(f"Assistant error: {e}")
            await message.channel.send("🤖 Sorry, I encountered an error. Try again!")

    async def _get_assistant_response(self, question: str) -> str:
        """Get AI response for assistant channel - educational only."""
        prompt = f"""You are a helpful crypto trading assistant. Answer the user's question about:
- Technical analysis concepts
- Market indicators (RSI, MACD, etc.)
- Trading strategies and concepts
- Crypto market education

IMPORTANT: You do NOT have access to any live trading data, account balances,
positions, or real-time prices. If asked about these, politely explain you
can only discuss educational concepts.

User question: {question}

Provide a helpful, concise response (under 500 words):"""

        try:
            if hasattr(self._llm_service, 'generate_response'):
                response = await self._llm_service.generate_response(prompt)
            else:
                response = "I can help explain trading concepts. What would you like to learn about?"
            return f"🤖 {response}"
        except Exception as e:
            logger.error(f"LLM error: {e}")
            return "🤖 I'm having trouble thinking right now. Try asking again!"

    def _get_channel_for_symbol(self, symbol: str) -> Optional[int]:
        """Get the appropriate signal channel for a symbol."""
        return self.channels.get_signal_channel(symbol)

    async def _send_to_channel(self, channel_id: int, content: str) -> bool:
        """Send a message to a specific channel."""
        if not self.client or not self.is_ready:
            return False

        if not channel_id:
            channel_id = self.channels.default

        if not channel_id:
            logger.warning("No channel ID configured")
            return False

        try:
            channel = self.client.get_channel(channel_id)
            if not channel:
                channel = await self.client.fetch_channel(channel_id)

            if channel:
                await channel.send(content)
                return True
            else:
                logger.error(f"Channel {channel_id} not found")
                return False
        except Exception as e:
            logger.error(f"Failed to send Discord message: {e}")
            return False

    async def _queue_or_send(self, channel_id: int, content: str) -> bool:
        """Queue message if not ready, otherwise send immediately."""
        if self.is_ready:
            return await self._send_to_channel(channel_id, content)
        else:
            self._message_queue.append((channel_id, content))
            return True

    # Legacy support
    async def _send_message(self, content: str) -> bool:
        """Send a message to the default channel (legacy)."""
        return await self._send_to_channel(self.channels.default, content)

    async def send_bot_status(self, message: str) -> bool:
        """Send bot status message (startup, shutdown, errors) - to default channel."""
        return await self._queue_or_send(self.channels.default, message)

    async def send_market_analysis(self, symbol: str, analysis: Dict[str, Any]) -> bool:
        """Send market analysis update → symbol-specific channel.

        Args:
            symbol: Trading symbol (e.g., "BTC", "ETH")
            analysis: Dict containing market analysis data
        """
        channel_id = self._get_channel_for_symbol(symbol)

        # Build message - ONLY market data, no account info
        lines = [
            f"📊 **{symbol} Market Analysis** - {datetime.utcnow().strftime('%H:%M UTC')}",
            ""
        ]

        # Price levels
        price = analysis.get("price", 0)
        if price:
            lines.append(f"💰 **Price:** ${price:,.2f}")

        # Support/Resistance
        support = analysis.get("support") or analysis.get("nearest_support")
        resistance = analysis.get("resistance") or analysis.get("nearest_resistance")
        if support or resistance:
            lines.append("")
            lines.append("📍 **Key Levels:**")
            if support:
                lines.append(f"  • Support: ${support:,.2f}")
            if resistance:
                lines.append(f"  • Resistance: ${resistance:,.2f}")

        # Visual levels from chart
        visual_support = analysis.get("visual_support")
        visual_resistance = analysis.get("visual_resistance")
        if visual_support or visual_resistance:
            lines.append("")
            lines.append("🎯 **Chart Levels:**")
            if visual_support:
                lines.append(f"  • Visual Support: ${visual_support:,.2f}")
            if visual_resistance:
                lines.append(f"  • Visual Resistance: ${visual_resistance:,.2f}")

        # Trend
        trend = analysis.get("trend") or analysis.get("ema_macro_signal")
        if trend:
            emoji = "🟢" if trend == "bullish" else "🔴" if trend == "bearish" else "⚪"
            lines.append(f"\n📈 **Trend:** {emoji} {trend.upper()}")

        message = "\n".join(lines)
        return await self._queue_or_send(channel_id, message)

    async def send_whale_activity(self, symbol: str, whale_data: Dict[str, Any]) -> bool:
        """Send whale order activity alert → #whales channel.

        Args:
            symbol: Trading symbol
            whale_data: Dict containing whale order info
        """
        channel_id = self.channels.whales or self.channels.default

        large_bids = whale_data.get("large_bids", [])
        large_asks = whale_data.get("large_asks", [])
        bid_depth = whale_data.get("bid_depth_usd", 0)
        ask_depth = whale_data.get("ask_depth_usd", 0)

        # Determine bias
        ratio = bid_depth / ask_depth if ask_depth > 0 else 1
        if ratio > 1.3:
            bias = "buyers stacking"
        elif ratio < 0.7:
            bias = "sellers stacking"
        else:
            bias = "balanced"

        # Build tweet-style message
        if large_bids and not large_asks:
            top_bid = large_bids[0]
            message = f"🐋 ${symbol} whale bid ${top_bid.get('size_usd', 0)/1000:.0f}K @ {format_price(top_bid.get('price', 0))} — {bias}"
        elif large_asks and not large_bids:
            top_ask = large_asks[0]
            message = f"🐋 ${symbol} whale ask ${top_ask.get('size_usd', 0)/1000:.0f}K @ {format_price(top_ask.get('price', 0))} — {bias}"
        else:
            message = f"🐋 ${symbol} whale walls detected — {bias} (bid/ask {ratio:.1f}x)"

        return await self._queue_or_send(channel_id, message)

    async def send_whale_position_alert(self, position_data: Dict[str, Any], action: str = "opened") -> bool:
        """Send alert when a tracked whale opens/closes a position → #whales channel.

        Args:
            position_data: Dict with whale name, symbol, side, size, entry_price, leverage
            action: "opened" or "closed"
        """
        channel_id = self.channels.whales or self.channels.default

        whale_name = position_data.get("whale", "Unknown Whale")
        symbol = position_data.get("symbol", "?")
        side = position_data.get("side", "unknown").upper()
        size = abs(position_data.get("size", 0))
        entry_price = position_data.get("entry_price", 0)
        leverage = position_data.get("leverage", 1)
        pnl = position_data.get("unrealized_pnl", 0)

        # Calculate notional value
        notional = size * entry_price if entry_price else 0

        # Build tweet-style message
        if action == "opened":
            side_emoji = "🟢" if side == "LONG" else "🔴"
            message = f"🐋 {whale_name} {side_emoji}{side} ${symbol} — {size:.4f} @ {format_price(entry_price)} ({leverage}x) = ${notional/1000:.0f}K"
        else:  # closed
            result_emoji = "✅" if pnl > 0 else "❌" if pnl < 0 else "⚪"
            pnl_str = f"${pnl:+,.0f}" if pnl != 0 else "flat"
            message = f"🐋 {whale_name} closed {side} ${symbol} — {result_emoji} {pnl_str}"

        return await self._queue_or_send(channel_id, message)

    async def send_whale_consensus(self, symbol: str, longs: int, shorts: int) -> bool:
        """Send whale consensus update → #whales channel.

        Args:
            symbol: Trading symbol
            longs: Number of whales long
            shorts: Number of whales short
        """
        channel_id = self.channels.whales or self.channels.default
        total = longs + shorts
        if total == 0:
            return False

        if longs > shorts:
            bias = f"{longs} whales LONG vs {shorts} short"
            emoji = "🟢"
        elif shorts > longs:
            bias = f"{shorts} whales SHORT vs {longs} long"
            emoji = "🔴"
        else:
            bias = f"split {longs}-{shorts}"
            emoji = "⚪"

        message = f"🐋 ${symbol} whale consensus: {emoji} {bias}"
        return await self._queue_or_send(channel_id, message)

    async def send_trade_setup(self, symbol: str, setup: Dict[str, Any]) -> bool:
        """Send potential trade setup alert → symbol-specific channel.

        Args:
            symbol: Trading symbol
            setup: Dict containing setup details (NO position sizes or account data)
        """
        channel_id = self._get_channel_for_symbol(symbol)

        action = setup.get("action", "").upper()
        confidence = setup.get("confidence", 0)
        entry_zone = setup.get("entry_zone", 0)
        reasoning = setup.get("reasoning", "")

        emoji = "🟢" if action == "LONG" else "🔴"

        # Get first signal reason, keep it short
        short_reason = reasoning.split(".")[0][:60] if reasoning else ""

        message = f"{emoji} ${symbol} {action} setup {confidence:.0%} @ {format_price(entry_zone)} — {short_reason}"
        return await self._queue_or_send(channel_id, message)

    async def send_trend_update(self, symbol: str, trend_data: Dict[str, Any]) -> bool:
        """Send trend flip alert → symbol-specific channel.

        Args:
            symbol: Trading symbol
            trend_data: Dict containing trend analysis
        """
        channel_id = self._get_channel_for_symbol(symbol)

        trend_4h = trend_data.get("trend_4h") or trend_data.get("ema_macro_signal", "")
        prev_trend = trend_data.get("previous_trend", "")
        rsi = trend_data.get("rsi", 50)

        emoji = "🟢" if "bull" in trend_4h.lower() else "🔴"
        rsi_note = " (oversold)" if rsi < 30 else " (overbought)" if rsi > 70 else ""

        message = f"📈 ${symbol} trend flipped {prev_trend} → {trend_4h.upper()}{rsi_note}"
        return await self._queue_or_send(channel_id, message)

    async def send_trade_executed(self, symbol: str, trade_data: Dict[str, Any]) -> bool:
        """Send notification when a trade is EXECUTED → symbol-specific channel.

        Args:
            symbol: Trading symbol
            trade_data: Dict with side, entry_price, stop_loss, take_profit, confidence, reasoning
        """
        channel_id = self._get_channel_for_symbol(symbol)

        side = trade_data.get("side", "").upper()
        entry_price = trade_data.get("entry_price", 0)
        stop_loss = trade_data.get("stop_loss", 0)
        take_profit = trade_data.get("take_profit", 0)
        confidence = trade_data.get("confidence", 0)

        emoji = "🟢" if side == "LONG" else "🔴"
        sl_dist = abs(entry_price - stop_loss) / entry_price * 100 if entry_price else 0
        tp_dist = abs(take_profit - entry_price) / entry_price * 100 if entry_price else 0

        message = f"{emoji} ${symbol} {side} @ {format_price(entry_price)} | SL {sl_dist:.1f}% | TP {tp_dist:.1f}% | {confidence:.0%} conf"

        # Save to database
        try:
            db = get_db()
            db.save_discord_alert(
                alert_type="trade_executed",
                channel=f"{symbol.lower()}_signals",
                symbol=symbol,
                direction=side.lower(),
                entry_price=entry_price,
                stop_loss=stop_loss,
                take_profit=take_profit,
                confidence=confidence,
                reasoning=trade_data.get("reasoning"),
                metadata={"sl_dist_pct": sl_dist, "tp_dist_pct": tp_dist}
            )
        except Exception as e:
            logger.warning(f"Failed to save trade_executed to DB: {e}")

        return await self._queue_or_send(channel_id, message)

    async def send_trade_closed(self, symbol: str, trade_data: Dict[str, Any]) -> bool:
        """Send notification when a trade is CLOSED → symbol-specific channel.

        Args:
            symbol: Trading symbol
            trade_data: Dict with side, entry_price, exit_price, pnl_pct, exit_reason
        """
        channel_id = self._get_channel_for_symbol(symbol)

        side = trade_data.get("side", "").upper()
        pnl_pct = trade_data.get("pnl_pct", 0)
        pnl_usd = trade_data.get("pnl_usd", 0)
        exit_reason = trade_data.get("exit_reason", "unknown").replace("_", " ")

        result_emoji = "✅" if pnl_pct > 0 else "❌"
        side_emoji = "🟢" if side == "LONG" else "🔴"

        message = f"{result_emoji} ${symbol} {side_emoji}{side} closed {pnl_pct:+.1f}% — {exit_reason}"

        # Save to database
        try:
            db = get_db()
            db.save_discord_alert(
                alert_type="trade_closed",
                channel=f"{symbol.lower()}_signals",
                symbol=symbol,
                direction=side.lower(),
                entry_price=trade_data.get("entry_price"),
                pnl_pct=pnl_pct,
                pnl_usd=pnl_usd,
                metadata={"exit_reason": exit_reason, "exit_price": trade_data.get("exit_price")}
            )
        except Exception as e:
            logger.warning(f"Failed to save trade_closed to DB: {e}")

        return await self._queue_or_send(channel_id, message)

    async def send_ai_market_summary(self, symbol: str, summary: str) -> bool:
        """Send AI-generated market summary → symbol channel.

        Args:
            symbol: Trading symbol
            summary: Short AI-generated trend summary (1-2 sentences)
        """
        channel_id = self._get_channel_for_symbol(symbol)

        # Truncate to tweet length
        summary = summary[:200] if len(summary) > 200 else summary
        message = f"🤖 ${symbol} — {summary}"
        return await self._queue_or_send(channel_id, message)

    async def send_ai_reasoning(self, symbol: str, reasoning: str, decision: str) -> bool:
        """Send AI reasoning/thought process → symbol channel.

        Args:
            symbol: Trading symbol
            reasoning: AI's analysis reasoning
            decision: The final decision made
        """
        channel_id = self._get_channel_for_symbol(symbol)

        # Truncate reasoning if too long
        if len(reasoning) > 1500:
            reasoning = reasoning[:1500] + "..."

        message = f"🧠 **{symbol} AI Analysis**\n{reasoning}\n\n**Decision:** {decision}"

        # Save to database
        try:
            db = get_db()
            db.save_discord_alert(
                alert_type="ai_reasoning",
                channel=f"{symbol.lower()}_signals",
                symbol=symbol,
                reasoning=reasoning[:2000],
                metadata={"decision": decision}
            )
        except Exception as e:
            logger.warning(f"Failed to save ai_reasoning to DB: {e}")

        return await self._queue_or_send(channel_id, message)

    async def send_alpha_call(self, symbol: str, direction: str, entry: float,
                              stop_loss: float, target: float, reasoning: str,
                              confidence: float = 0.0) -> bool:
        """Send alpha call with @everyone to #alpha-calls channel.

        Args:
            symbol: Trading symbol
            direction: LONG or SHORT
            entry: Entry price zone
            stop_loss: Stop loss price
            target: Target price
            reasoning: Why this trade setup looks good
            confidence: Confidence level (0-1)
        """
        channel_id = self.channels.alpha_calls or self.channels.default
        if not channel_id:
            return False

        # Calculate R:R
        if direction.upper() == "LONG":
            risk = entry - stop_loss
            reward = target - entry
        else:
            risk = stop_loss - entry
            reward = entry - target

        rr_ratio = reward / risk if risk > 0 else 0

        emoji = "🟢" if direction.upper() == "LONG" else "🔴"
        conf_str = f" ({confidence:.0%} conf)" if confidence > 0 else ""

        message = f"""@everyone

{emoji} **ALPHA CALL: {direction.upper()} ${symbol}**{conf_str}

📍 **Entry Zone:** ${entry:,.2f}
🛑 **Stop Loss:** ${stop_loss:,.2f}
🎯 **Target:** ${target:,.2f}
📊 **R:R Ratio:** {rr_ratio:.1f}:1

💡 **Setup:** {reasoning[:500]}

⚠️ *Not financial advice. DYOR. Manage your risk.*
"""
        # Save to database
        try:
            db = get_db()
            db.save_discord_alert(
                alert_type="alpha_call",
                channel="alpha_calls",
                symbol=symbol,
                direction=direction.lower(),
                entry_price=entry,
                stop_loss=stop_loss,
                take_profit=target,
                confidence=confidence,
                reasoning=reasoning[:1000],
                metadata={"rr_ratio": rr_ratio}
            )
        except Exception as e:
            logger.warning(f"Failed to save alpha_call to DB: {e}")

        return await self._queue_or_send(channel_id, message)

    async def send_liquidation_alert(self, symbol: str, liquidation_data: Dict[str, Any]) -> bool:
        """Send liquidation alert → #liquidations channel.

        Args:
            symbol: Trading symbol
            liquidation_data: Dict with side, price, size_usd, etc.
        """
        channel_id = self.channels.liquidations or self.channels.default

        side = liquidation_data.get("side", "").upper()
        price = liquidation_data.get("price", 0)
        size_usd = liquidation_data.get("size_usd", 0)

        emoji = "💀" if size_usd > 1_000_000 else "⚠️"
        side_emoji = "🟢" if side == "LONG" else "🔴"

        if size_usd >= 1_000_000:
            size_str = f"${size_usd/1_000_000:.1f}M"
        else:
            size_str = f"${size_usd/1_000:.0f}K"

        message = f"{emoji} ${symbol} {side_emoji}{side} liquidated {size_str} @ {format_price(price)}"

        # Save to database
        try:
            db = get_db()
            db.save_discord_alert(
                alert_type="liquidation",
                channel="liquidations",
                symbol=symbol,
                direction=side.lower(),
                entry_price=price,
                liquidation_size=size_usd,
                metadata=liquidation_data
            )
        except Exception as e:
            logger.warning(f"Failed to save liquidation to DB: {e}")

        return await self._queue_or_send(channel_id, message)

    async def send_full_technical_analysis(self, symbol: str, market_data: Dict[str, Any]) -> bool:
        """Send comprehensive technical analysis → symbol-specific channel.

        Args:
            symbol: Trading symbol
            market_data: Full market data dict with all indicators
        """
        channel_id = self._get_channel_for_symbol(symbol)
        price = market_data.get("price", 0)

        # === BUILD HEADER ===
        lines = [
            f"📊 **${symbol} FULL ANALYSIS** — {datetime.utcnow().strftime('%H:%M UTC')}",
            f"💰 Price: **{format_price(price)}**",
            ""
        ]

        # === MULTI-TIMEFRAME TRENDS ===
        lines.append("📈 **TRENDS**")
        trend_5m = market_data.get("ema_micro_signal", "—")
        trend_1h = market_data.get("ema_mid_signal", "—")
        trend_4h = market_data.get("ema_macro_signal", "—")

        def trend_emoji(t):
            return "🟢" if t == "bullish" else "🔴" if t == "bearish" else "⚪"

        lines.append(f"  5m: {trend_emoji(trend_5m)} {trend_5m} | 1h: {trend_emoji(trend_1h)} {trend_1h} | 4h: {trend_emoji(trend_4h)} {trend_4h}")

        # === KEY INDICATORS ===
        lines.append("")
        lines.append("📉 **INDICATORS**")

        rsi = market_data.get("rsi", 50)
        rsi_emoji = "🔴" if rsi > 70 else "🟢" if rsi < 30 else "⚪"
        lines.append(f"  RSI: {rsi_emoji} {rsi:.0f}")

        # MACD
        macd = market_data.get("macd", {})
        if isinstance(macd, dict):
            macd_val = macd.get("macd", 0)
            macd_signal = macd.get("signal", 0)
            macd_hist = macd.get("histogram", 0)
            macd_cross = "🟢 bullish" if macd_val > macd_signal else "🔴 bearish"
            lines.append(f"  MACD: {macd_cross} (hist: {macd_hist:+.0f})")

        # ADX (trend strength)
        adx = market_data.get("adx", {})
        if isinstance(adx, dict):
            adx_val = adx.get("adx", 0)
            plus_di = adx.get("plus_di", 0)
            minus_di = adx.get("minus_di", 0)
            if adx_val:
                strength = "STRONG" if adx_val > 25 else "WEAK"
                direction = "🟢" if plus_di > minus_di else "🔴"
                lines.append(f"  ADX: {adx_val:.0f} ({strength}) {direction} +DI:{plus_di:.0f} -DI:{minus_di:.0f}")

        # Bollinger Bands
        bb = market_data.get("bollinger_bands", {})
        if isinstance(bb, dict) and bb.get("upper"):
            bb_upper = bb.get("upper", 0)
            bb_lower = bb.get("lower", 0)
            bb_width = bb.get("width", 0)
            bb_pos = "upper" if price > bb_upper * 0.99 else "lower" if price < bb_lower * 1.01 else "middle"
            lines.append(f"  BB: {format_price(bb_lower)} - {format_price(bb_upper)} (width: {bb_width:.2%}, at {bb_pos})")

        # ATR (volatility)
        atr = market_data.get("atr", 0)
        atr_pct = market_data.get("atr_pct", 0)
        if atr:
            lines.append(f"  ATR: {format_price(atr)} ({atr_pct:.2%} volatility)")

        # === SUPPORT/RESISTANCE ===
        lines.append("")
        lines.append("📍 **LEVELS**")
        support = market_data.get("nearest_support", 0)
        resistance = market_data.get("nearest_resistance", 0)
        sr_signal = market_data.get("sr_signal", "mid_range")

        if support:
            dist_sup = (price - support) / price * 100
            lines.append(f"  Support: {format_price(support)} ({dist_sup:.1f}% below)")
        if resistance:
            dist_res = (resistance - price) / price * 100
            lines.append(f"  Resistance: {format_price(resistance)} ({dist_res:.1f}% above)")
        lines.append(f"  Position: {sr_signal.replace('_', ' ')}")

        # === ORDERBOOK / LIQUIDITY ===
        orderbook = market_data.get("orderbook_analysis", {})
        if orderbook:
            lines.append("")
            lines.append("📚 **ORDERBOOK**")
            imbalance = orderbook.get("imbalance", 0)
            bid_depth = orderbook.get("bid_depth_usd", 0)
            ask_depth = orderbook.get("ask_depth_usd", 0)
            bias = "🟢 bid heavy" if imbalance > 0.2 else "🔴 ask heavy" if imbalance < -0.2 else "⚪ balanced"
            lines.append(f"  {bias} | Bids: ${bid_depth/1e6:.1f}M | Asks: ${ask_depth/1e6:.1f}M")

        # === FUNDING RATE ===
        funding = market_data.get("funding_rate", 0)
        if funding:
            lines.append("")
            funding_emoji = "🔴" if funding > 0.01 else "🟢" if funding < -0.01 else "⚪"
            funding_note = "(longs pay)" if funding > 0 else "(shorts pay)" if funding < 0 else ""
            lines.append(f"💸 Funding: {funding_emoji} {funding:.4%} {funding_note}")

        # === REGIME ===
        regime = market_data.get("adaptive_regime") or market_data.get("intel_regime", "")
        if regime:
            lines.append("")
            regime_emoji = {"trend_up": "🟢📈", "trend_down": "🔴📉", "range": "⚪↔️",
                          "compression": "🔶🔄", "expansion": "🟡💥", "exhaustion": "⚠️"}.get(regime, "❓")
            lines.append(f"🎯 Regime: {regime_emoji} **{regime.upper()}**")

        # === PATTERNS DETECTED ===
        patterns = market_data.get("candle_patterns", {})
        if patterns and patterns.get("pattern"):
            lines.append("")
            lines.append(f"🕯️ Pattern: **{patterns.get('pattern')}** ({patterns.get('bias', 'neutral')})")

        message = "\n".join(lines)
        return await self._queue_or_send(channel_id, message)

    async def send_sr_alert(self, symbol: str, level_type: str, price: float, level: float) -> bool:
        """Send S/R level approach alert → symbol-specific channel.

        Args:
            symbol: Trading symbol
            level_type: "support" or "resistance"
            price: Current price
            level: S/R level price
        """
        channel_id = self._get_channel_for_symbol(symbol)

        dist_pct = abs(price - level) / level * 100 if level else 0
        emoji = "🟢" if level_type == "support" else "🔴"
        action = "bouncing off" if dist_pct < 0.2 else "approaching"

        message = f"{emoji} ${symbol} {action} {level_type} {format_price(level)} ({dist_pct:.1f}% away)"
        return await self._queue_or_send(channel_id, message)

    async def send_breakout_alert(self, symbol: str, breakout_type: str, price: float,
                                   level: float, confidence: float) -> bool:
        """Send breakout alert → symbol-specific channel.

        Args:
            symbol: Trading symbol
            breakout_type: "breaking_support" or "breaking_resistance"
            price: Current price
            level: The S/R level being broken
            confidence: Breakout confidence (0-1)
        """
        channel_id = self._get_channel_for_symbol(symbol)

        if breakout_type == "breaking_resistance":
            emoji = "🚀"
            direction = "BULLISH BREAKOUT"
            action = "breaking above"
            implication = "→ Continuation higher likely"
        else:
            emoji = "💥"
            direction = "BEARISH BREAKDOWN"
            action = "breaking below"
            implication = "→ Continuation lower likely"

        pct_through = abs(price - level) / level * 100 if level else 0
        conf_str = f"{confidence:.0%}" if confidence > 0 else "confirming"

        message = f"""{emoji} **{symbol} {direction}** {emoji}
${symbol} {action} {format_price(level)} (now {format_price(price)}, {pct_through:.2f}% through)
Confidence: {conf_str}
{implication}"""

        return await self._queue_or_send(channel_id, message)

    async def send_trend_alignment_alert(self, symbol: str, alignment_data: Dict[str, Any]) -> bool:
        """Send alert when all timeframes align → symbol-specific channel.

        Args:
            symbol: Trading symbol
            alignment_data: Dict with trend alignment info
        """
        channel_id = self._get_channel_for_symbol(symbol)

        direction = alignment_data.get("direction", "neutral")
        alignment_pct = alignment_data.get("alignment_pct", 0)
        bullish_count = alignment_data.get("bullish_count", 0)
        bearish_count = alignment_data.get("bearish_count", 0)

        if direction == "bullish" and alignment_pct >= 70:
            emoji = "🟢🟢🟢"
            msg = f"BULLISH ALIGNMENT ({bullish_count}/7 TFs bullish)"
        elif direction == "bearish" and alignment_pct >= 70:
            emoji = "🔴🔴🔴"
            msg = f"BEARISH ALIGNMENT ({bearish_count}/7 TFs bearish)"
        else:
            return False  # Don't alert for weak alignment

        message = f"""{emoji} **{symbol} MULTI-TIMEFRAME {msg}** {emoji}
All major timeframes aligned → High conviction setup
1D/4H/1H/30m/15m/5m/1m trends pointing same direction"""

        return await self._queue_or_send(channel_id, message)

    async def send_pattern_alert(self, symbol: str, pattern: Dict[str, Any]) -> bool:
        """Send chart pattern alert → symbol-specific channel.

        Args:
            symbol: Trading symbol
            pattern: Pattern dict with name, direction, score, entry, target, stop, etc.
        """
        channel_id = self._get_channel_for_symbol(symbol)

        emoji = "🟢" if pattern.get("direction") == "bullish" else "🔴"
        type_emoji = {
            "continuation_bull": "📈",
            "continuation_bear": "📉",
            "reversal_bull": "🔄",
            "reversal_bear": "🔄",
            "breakout": "💥",
            "liquidity": "🎯"
        }.get(pattern.get("type", ""), "📊")

        name = pattern.get("name", "Pattern")
        score = pattern.get("score", 0)
        tf = pattern.get("timeframe", "")
        entry = pattern.get("entry", 0)
        target = pattern.get("target", 0)
        stop = pattern.get("stop", 0)
        rr = pattern.get("risk_reward", 0)

        # Build badges
        badges = []
        if pattern.get("volume_confirmed"):
            badges.append("📊")
        if pattern.get("trend_aligned"):
            badges.append("📐")
        if pattern.get("htf_support"):
            badges.append("🔝")
        badges_str = "".join(badges)

        # Build message
        message = f"{emoji} ${symbol} {type_emoji}{name} ({tf}) {badges_str}\n"
        message += f"Score: {score}/100 | R:R {rr:.1f}:1\n"
        message += f"Entry ${entry:,.0f} → ${target:,.0f} (SL ${stop:,.0f})"

        # Get first signal reason
        signals = pattern.get("signals", [])
        if signals:
            message += f"\n{signals[0]}"

        return await self._queue_or_send(channel_id, message)

    async def send_pattern_summary(self, symbol: str, patterns: list) -> bool:
        """Send summary of detected patterns → symbol-specific channel.

        Args:
            symbol: Trading symbol
            patterns: List of pattern dicts sorted by score
        """
        if not patterns:
            return False

        channel_id = self._get_channel_for_symbol(symbol)

        # Count by direction
        bullish = sum(1 for p in patterns if p.get("direction") == "bullish")
        bearish = sum(1 for p in patterns if p.get("direction") == "bearish")

        # Best pattern
        best = patterns[0]
        emoji = "🟢" if best.get("direction") == "bullish" else "🔴"

        message = f"📊 **${symbol} Pattern Scan** — {len(patterns)} setups\n"
        message += f"🟢{bullish} 🔴{bearish}\n"
        message += f"{emoji} Best: **{best['name']}** ({best['timeframe']}) — {best['score']}/100"

        if len(patterns) > 1:
            message += "\n"
            for p in patterns[1:3]:
                e = "🟢" if p.get("direction") == "bullish" else "🔴"
                message += f"\n{e} {p['name']} ({p['timeframe']}) {p['score']}/100"

        return await self._queue_or_send(channel_id, message)

    async def send_liquidity_alert(self, symbol: str, pattern: Dict[str, Any]) -> bool:
        """Send high-priority liquidity/smart money alert → alpha channel.

        These are the highest-quality setups (liquidity sweeps, order blocks, FVGs).
        Goes to #alpha-calls for visibility.
        """
        channel_id = self.channels.alpha_calls
        if not channel_id:
            return False

        emoji = "🟢" if pattern.get("direction") == "bullish" else "🔴"
        name = pattern.get("name", "Liquidity Setup")
        score = pattern.get("score", 0)
        entry = pattern.get("entry", 0)
        target = pattern.get("target", 0)
        stop = pattern.get("stop", 0)
        rr = pattern.get("risk_reward", 0)

        signals = pattern.get("signals", [])
        signal_text = " • ".join(signals[:2]) if signals else ""

        message = f"🎯 **SMART MONEY ALERT** 🎯\n"
        message += f"{emoji} ${symbol} — **{name}**\n"
        message += f"Score: {score}/100 | R:R {rr:.1f}:1\n"
        message += f"Entry: ${entry:,.0f} → Target: ${target:,.0f}\n"
        message += f"Stop: ${stop:,.0f}\n"
        if signal_text:
            message += f"_{signal_text}_"

        return await self._queue_or_send(channel_id, message)

    async def disconnect(self):
        """Disconnect from Discord."""
        if self.client:
            await self.client.close()
            self.is_ready = False

