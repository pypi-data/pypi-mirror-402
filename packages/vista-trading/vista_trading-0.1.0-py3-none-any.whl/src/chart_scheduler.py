#!/usr/bin/env python3
"""Scheduled chart generation with AI analysis for Discord."""

import asyncio
import os
import logging
from io import BytesIO
from datetime import datetime
from typing import Dict, List, Optional, Any

from src.tickers import TRADING_TICKERS, format_price
from src.database import get_db

logger = logging.getLogger(__name__)

# Use centralized ticker list
TICKERS = TRADING_TICKERS
DEFAULT_TICKERS = TRADING_TICKERS


def calc_ema_series(closes: List[float], period: int) -> List[float]:
    """Calculate EMA for entire series."""
    emas = []
    multiplier = 2 / (period + 1)
    ema = sum(closes[:period]) / period if len(closes) >= period else closes[0]
    for i, price in enumerate(closes):
        if i < period:
            emas.append(sum(closes[:i+1]) / (i+1))
        else:
            ema = (price * multiplier) + (ema * (1 - multiplier))
            emas.append(ema)
    return emas


def calculate_trend_context(candles: List[Dict], patterns: List[Dict] = None) -> Dict[str, Any]:
    """Calculate comprehensive trend context for learning and filtering.

    Returns:
        Dict with trend_direction, trend_strength, ema_position, rsi_value,
        macd_histogram, patterns_detected, volume_trend, volatility_regime
    """
    from src.technical_analysis import calculate_rsi, calculate_macd, calculate_adx

    if not candles or len(candles) < 21:
        return {
            "trend_direction": None,
            "trend_strength": None,
            "ema_position": None,
            "rsi_value": None,
            "macd_histogram": None,
            "patterns_detected": [],
            "volume_trend": None,
            "volatility_regime": None
        }

    closes = [c['close'] for c in candles]
    price = closes[-1]

    # === EMA Position ===
    ema21 = calc_ema_series(closes, 21)[-1]
    ema50 = calc_ema_series(closes, 50)[-1] if len(closes) >= 50 else ema21

    ema_pct_diff = ((price - ema21) / ema21) * 100
    if ema_pct_diff > 1.0:
        ema_position = "above_ema"
    elif ema_pct_diff < -1.0:
        ema_position = "below_ema"
    else:
        ema_position = "at_ema"

    # === RSI ===
    rsi = calculate_rsi(candles, period=14)

    # === MACD ===
    macd_data = calculate_macd(candles)
    macd_histogram = macd_data.get("histogram")

    # === ADX for trend direction and strength ===
    adx_data = calculate_adx(candles, period=14)
    adx_value = adx_data.get("adx")
    trend_direction = adx_data.get("trend_direction", "neutral")

    # Convert ADX to trend strength (0-100 scale)
    if adx_value is not None:
        trend_strength = min(100, adx_value * 2.5)  # ADX 40 = strength 100
    else:
        trend_strength = None

    # === Volume Trend ===
    volumes = [c.get('volume', c.get('v', 0)) for c in candles]
    if len(volumes) >= 20:
        avg_vol_20 = sum(volumes[-20:]) / 20
        recent_vol = sum(volumes[-5:]) / 5
        vol_ratio = recent_vol / avg_vol_20 if avg_vol_20 > 0 else 1.0

        if vol_ratio > 1.5:
            volume_trend = "increasing"
        elif vol_ratio < 0.6:
            volume_trend = "decreasing"
        else:
            volume_trend = "stable"
    else:
        volume_trend = None

    # === Volatility Regime ===
    # Use ATR as % of price
    if len(candles) >= 14:
        tr_list = []
        for i in range(1, len(candles)):
            high = candles[i].get('high', candles[i].get('h', 0))
            low = candles[i].get('low', candles[i].get('l', 0))
            prev_close = candles[i-1]['close']
            tr = max(high - low, abs(high - prev_close), abs(low - prev_close))
            tr_list.append(tr)

        atr = sum(tr_list[-14:]) / 14
        atr_pct = (atr / price) * 100

        if atr_pct > 3.0:
            volatility_regime = "high"
        elif atr_pct < 1.0:
            volatility_regime = "low"
        else:
            volatility_regime = "normal"
    else:
        volatility_regime = None

    # === Patterns ===
    patterns_detected = []
    if patterns:
        for p in patterns:
            if isinstance(p, dict):
                patterns_detected.append(p.get("pattern", p.get("name", str(p))))
            else:
                patterns_detected.append(str(p))

    return {
        "trend_direction": trend_direction,
        "trend_strength": trend_strength,
        "ema_position": ema_position,
        "rsi_value": rsi,
        "macd_histogram": macd_histogram,
        "patterns_detected": patterns_detected[:5],  # Top 5 patterns
        "volume_trend": volume_trend,
        "volatility_regime": volatility_regime
    }


class ChartScheduler:
    """Generates and posts charts on schedule."""

    def __init__(self, hl_client, discord_notifier, llm_service=None, signal_learner=None, symbols: List[str] = None):
        self.hl = hl_client
        self.discord = discord_notifier
        self.llm = llm_service
        self.signal_learner = signal_learner  # For learning from chart signals
        self.symbols = symbols or DEFAULT_TICKERS  # Use passed symbols or default
        self.last_30m_run = None
        self.last_daily_run = None
        self.last_vista_run = None  # Track last Vista AI analysis
        self.db = get_db()  # Initialize database connection
        logger.info(f"📊 ChartScheduler initialized for symbols: {self.symbols}")
    
    async def generate_chart_image(self, candles: List[Dict], symbol: str,
                                    timeframe: str, trendlines: Dict, sr: Dict,
                                    lookback: int = 50, prediction: Dict = None) -> bytes:
        """Generate chart image with trendlines and S/R.

        Args:
            candles: List of candle data
            symbol: Trading symbol
            timeframe: Chart timeframe string
            trendlines: Trendline detection results
            sr: Support/resistance data
            lookback: Lookback period used for trendline detection (must match!)
            prediction: Optional price prediction dict with 'predicted_price' for white dot
        """
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        import matplotlib.dates as mdates
        from datetime import timedelta

        closes = [c['close'] for c in candles]
        highs = [c['high'] for c in candles]
        lows = [c['low'] for c in candles]
        opens = [c['open'] for c in candles]
        dates = [datetime.fromtimestamp(c['timestamp']/1000) for c in candles]

        ema9 = calc_ema_series(closes, 9)
        ema21 = calc_ema_series(closes, 21)

        # Create figure
        fig, ax1 = plt.subplots(1, 1, figsize=(14, 8))
        fig.patch.set_facecolor('#1a1a2e')
        ax1.set_facecolor('#1a1a2e')

        # Candlesticks
        for i, (d, o, h, l, c) in enumerate(zip(dates, opens, highs, lows, closes)):
            color = '#00ff88' if c >= o else '#ff4466'
            ax1.plot([d, d], [l, h], color=color, linewidth=0.8)
            ax1.plot([d, d], [o, c], color=color, linewidth=2.5 if timeframe == "5m" else 4)

        # EMAs
        ax1.plot(dates, ema9, color='#00aaff', linewidth=1.2, alpha=0.8, label='EMA 9')
        ax1.plot(dates, ema21, color='#ffaa00', linewidth=1.2, alpha=0.8, label='EMA 21')

        # Horizontal S/R
        for s in sr.get('supports', [])[:3]:
            ax1.axhline(y=s, color='#00ff88', linestyle='--', alpha=0.6, linewidth=1.5)
            ax1.text(dates[-1], s, f'  S {format_price(s)}', color='#00ff88', fontsize=9, va='center')

        for r in sr.get('resistances', [])[:3]:
            ax1.axhline(y=r, color='#ff4466', linestyle='--', alpha=0.6, linewidth=1.5)
            ax1.text(dates[-1], r, f'  R {format_price(r)}', color='#ff4466', fontsize=9, va='center')

        # Diagonal trendlines - use the lookback that was used for detection
        offset = max(0, len(candles) - lookback)

        asc = trendlines.get('ascending_support')
        if asc and asc.get('start_idx') is not None:
            start_idx_full = offset + asc['start_idx']
            slope = asc['slope']
            start_price = asc['start_price']
            start_idx_lookback = asc['start_idx']

            # Calculate line prices for full candle array
            line_prices = []
            for i in range(len(candles)):
                if i < start_idx_full:
                    line_prices.append(None)
                else:
                    # Calculate relative to lookback window
                    lookback_i = i - offset
                    price_at_i = start_price + slope * (lookback_i - start_idx_lookback)
                    line_prices.append(price_at_i)

            ax1.plot(dates, line_prices, color='#00ff88', linewidth=2.5,
                    label=f'Asc Support {format_price(asc.get("current_price", 0))}')

        desc = trendlines.get('descending_resistance')
        if desc and desc.get('start_idx') is not None:
            start_idx_full = offset + desc['start_idx']
            slope = desc['slope']
            start_price = desc['start_price']
            start_idx_lookback = desc['start_idx']

            line_prices = []
            for i in range(len(candles)):
                if i < start_idx_full:
                    line_prices.append(None)
                else:
                    lookback_i = i - offset
                    price_at_i = start_price + slope * (lookback_i - start_idx_lookback)
                    line_prices.append(price_at_i)

            ax1.plot(dates, line_prices, color='#ff4466', linewidth=2.5,
                    label=f'Desc Resist {format_price(desc.get("current_price", 0))}')

        # 🎯 PREDICTION DOT - White dot showing predicted price 5 candles ahead
        if prediction and prediction.get('predicted_price'):
            pred_price = prediction['predicted_price']
            pred_direction = prediction.get('predicted_direction', 'neutral')
            pred_confidence = prediction.get('confidence', 0)

            # Calculate future date (5 candles ahead)
            if len(dates) >= 2:
                # Estimate candle interval from last two dates
                candle_interval = dates[-1] - dates[-2]
                future_date = dates[-1] + (candle_interval * 5)
            else:
                future_date = dates[-1] + (timedelta(minutes=25) if timeframe == "5m" else timedelta(days=5))

            # Draw the prediction dot (white with glow effect)
            ax1.scatter([future_date], [pred_price], c='white', s=150, zorder=10,
                       edgecolors='#00aaff' if pred_direction == 'up' else '#ff4466' if pred_direction == 'down' else 'gray',
                       linewidths=3, alpha=0.9)

            # Add connecting line from current price to prediction
            ax1.plot([dates[-1], future_date], [closes[-1], pred_price],
                    color='white', linestyle=':', linewidth=1.5, alpha=0.6)

            # Label the prediction
            direction_emoji = "↑" if pred_direction == "up" else "↓" if pred_direction == "down" else "→"
            conf_pct = int(pred_confidence * 100)
            ax1.annotate(f'{direction_emoji} {format_price(pred_price)}\n({conf_pct}% conf)',
                        xy=(future_date, pred_price),
                        xytext=(10, 10), textcoords='offset points',
                        color='white', fontsize=9, fontweight='bold',
                        bbox=dict(boxstyle='round,pad=0.3', facecolor='#2a2a3e', edgecolor='white', alpha=0.8))

        # Title - determine emoji based on expected price direction
        signal = trendlines.get('signal', 'neutral')
        price = closes[-1]
        # "breaking_resistance" = bullish breakout, "breaking_support" = bearish breakdown
        if signal == "breaking_resistance":
            trend_emoji = "🚀"  # Bullish breakout
        elif signal == "breaking_support":
            trend_emoji = "💥"  # Bearish breakdown
        elif "support" in signal or "bullish" in signal:
            trend_emoji = "📈"  # At support, expecting bounce up
        elif "resistance" in signal or "bearish" in signal:
            trend_emoji = "📉"  # At resistance, expecting rejection down
        else:
            trend_emoji = "➡️"
        ax1.set_title(f'{symbol}/USD {timeframe} {trend_emoji} {signal.upper()}\nPrice: {format_price(price)}',
                      color='white', fontsize=14, fontweight='bold')
        ax1.legend(loc='upper left', facecolor='#2a2a3e', labelcolor='white', fontsize=9)
        ax1.tick_params(colors='white')
        ax1.grid(True, alpha=0.2)
        ax1.set_ylabel('Price', color='white')
        
        # Format x-axis
        if timeframe == "5m":
            ax1.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
        else:
            ax1.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d'))
        plt.xticks(rotation=45)
        plt.tight_layout()
        
        # Save to bytes
        buf = BytesIO()
        plt.savefig(buf, format='png', facecolor='#1a1a2e', dpi=120)
        buf.seek(0)
        img_bytes = buf.read()
        plt.close(fig)

        return img_bytes

    def _generate_quick_analysis(self, symbol: str, candles: List[Dict],
                                  trendlines: Dict, sr: Dict, timeframe: str) -> str:
        """Generate quick text analysis of the chart."""
        closes = [c['close'] for c in candles]
        price = closes[-1]

        # Calculate key metrics
        high_24h = max(c['high'] for c in candles[-48:]) if timeframe == "5m" else max(c['high'] for c in candles[-1:])
        low_24h = min(c['low'] for c in candles[-48:]) if timeframe == "5m" else min(c['low'] for c in candles[-1:])

        # EMAs
        ema9 = calc_ema_series(closes, 9)[-1]
        ema21 = calc_ema_series(closes, 21)[-1]
        ema_trend = "bullish" if ema9 > ema21 else "bearish"

        # Price position
        supports = sr.get('supports', [])
        resistances = sr.get('resistances', [])
        nearest_support = supports[0] if supports else price * 0.98
        nearest_resistance = resistances[0] if resistances else price * 1.02

        dist_to_support = (price - nearest_support) / price * 100
        dist_to_resistance = (nearest_resistance - price) / price * 100

        # Trendline signal
        signal = trendlines.get('signal', 'neutral')

        # Build analysis
        lines = []

        # Trend assessment
        if ema_trend == "bullish" and "support" in signal:
            lines.append(f"**Trend:** 📈 Bullish - EMA9 > EMA21, holding support")
        elif ema_trend == "bearish" and "resistance" in signal:
            lines.append(f"**Trend:** 📉 Bearish - EMA9 < EMA21, at resistance")
        elif ema_trend == "bullish":
            lines.append(f"**Trend:** 📈 Bullish bias - EMA9 > EMA21")
        else:
            lines.append(f"**Trend:** 📉 Bearish bias - EMA9 < EMA21")

        # Key levels
        lines.append(f"**Support:** {format_price(nearest_support)} ({dist_to_support:.1f}% away)")
        lines.append(f"**Resistance:** {format_price(nearest_resistance)} ({dist_to_resistance:.1f}% away)")

        # Expectation
        if "breaking_resistance" in signal:
            lines.append(f"⚡ **Expect:** Breakout in progress - watching for continuation to {format_price(nearest_resistance * 1.02)}")
        elif "breaking_support" in signal:
            lines.append(f"⚡ **Expect:** Breakdown in progress - watching for drop to {format_price(nearest_support * 0.98)}")
        elif dist_to_support < 1.0:
            lines.append(f"⚠️ **Expect:** Testing support - bounce or breakdown imminent")
        elif dist_to_resistance < 1.0:
            lines.append(f"⚠️ **Expect:** Testing resistance - rejection or breakout imminent")
        elif ema_trend == "bullish":
            lines.append(f"📊 **Expect:** Continuation toward {format_price(nearest_resistance)} resistance")
        else:
            lines.append(f"📊 **Expect:** Continuation toward {format_price(nearest_support)} support")

        return "\n".join(lines)

    def _generate_daily_analysis(self, symbol: str, candles: List[Dict],
                                  trendlines: Dict, sr: Dict) -> str:
        """Generate analysis for what to expect in next 24hr candle."""
        closes = [c['close'] for c in candles]
        price = closes[-1]

        # Recent price action
        if len(candles) >= 7:
            week_change = (price - candles[-7]['close']) / candles[-7]['close'] * 100
        else:
            week_change = 0

        day_high = candles[-1]['high']
        day_low = candles[-1]['low']
        day_range = (day_high - day_low) / day_low * 100

        # EMAs
        ema9 = calc_ema_series(closes, 9)[-1]
        ema21 = calc_ema_series(closes, 21)[-1]

        supports = sr.get('supports', [])
        resistances = sr.get('resistances', [])
        nearest_support = supports[0] if supports else price * 0.95
        nearest_resistance = resistances[0] if resistances else price * 1.05

        lines = []
        lines.append(f"**📅 Daily Analysis for {symbol}**")
        lines.append(f"Current: {format_price(price)} | 7d: {week_change:+.1f}%")
        lines.append("")

        # Trend
        if ema9 > ema21:
            lines.append("📈 **Daily Trend:** Bullish (EMA9 > EMA21)")
        else:
            lines.append("📉 **Daily Trend:** Bearish (EMA9 < EMA21)")

        # Key levels
        lines.append(f"🟢 **Key Support:** {format_price(nearest_support)}")
        lines.append(f"🔴 **Key Resistance:** {format_price(nearest_resistance)}")
        lines.append("")

        # 24hr expectation
        lines.append("**🔮 Next 24hr Expectation:**")

        signal = trendlines.get('signal', 'neutral')

        if "breaking" in signal:
            if "resistance" in signal:
                lines.append(f"• Breakout confirmed - target {format_price(nearest_resistance * 1.03)}")
                lines.append(f"• Invalidation below {format_price(price * 0.98)}")
            else:
                lines.append(f"• Breakdown confirmed - target {format_price(nearest_support * 0.97)}")
                lines.append(f"• Invalidation above {format_price(price * 1.02)}")
        elif week_change > 5:
            lines.append("• Strong momentum - expect continuation but watch for pullback")
            lines.append(f"• Likely range: {format_price(price * 0.97)} - {format_price(price * 1.03)}")
        elif week_change < -5:
            lines.append("• Weak momentum - expect bounce attempt or continued selling")
            lines.append(f"• Likely range: {format_price(price * 0.95)} - {format_price(price * 1.02)}")
        else:
            lines.append("• Consolidation expected - range-bound action likely")
            lines.append(f"• Likely range: {format_price(nearest_support)} - {format_price(nearest_resistance)}")

        return "\n".join(lines)

    async def generate_5m_charts(self) -> None:
        """Generate 5m charts for all tickers with analysis."""
        from src.technical_analysis import detect_trendlines, calculate_support_resistance
        from src.pattern_detector import PatternDetector, PricePredictor
        import discord

        logger.info(f"📊 Generating 5m charts for ALL {len(TICKERS)} tickers: {TICKERS}")
        success_count = 0
        failed_tickers = []

        # Initialize predictor for price predictions
        predictor = PricePredictor()

        for symbol in TICKERS:
            logger.info(f"📊 Processing {symbol} 5m chart...")
            try:
                # Get candles
                candles = self.hl.get_candles(symbol, interval="5m", limit=150)
                if not candles or len(candles) < 50:
                    logger.warning(f"Not enough candles for {symbol}")
                    continue

                # Analysis - use lookback=50 for 5m charts with looser tolerance for intraday
                short_lookback = 50
                # 5m charts: 1% tolerance (more volatile), 0.01% min slope (allow flatter trendlines)
                trendlines = detect_trendlines(candles, lookback=short_lookback, min_touches=2,
                                               tolerance_pct=0.01, min_slope_pct=0.01)
                sr = calculate_support_resistance(candles, lookback=short_lookback)

                # Debug: Log trendline detection results
                asc = trendlines.get('ascending_support')
                desc = trendlines.get('descending_resistance')
                swing_lows = trendlines.get('swing_lows_count', 0)
                swing_highs = trendlines.get('swing_highs_count', 0)
                logger.info(f"📊 {symbol} 5m: {swing_lows} swing lows, {swing_highs} swing highs | ASC={asc is not None} DESC={desc is not None}")
                if asc:
                    logger.info(f"   ✅ ASC Support: ${asc.get('current_price'):,.2f}, touches={asc.get('touches')}, slope={asc.get('slope_pct_per_candle')}%/candle")
                if desc:
                    logger.info(f"   ✅ DESC Resist: ${desc.get('current_price'):,.2f}, touches={desc.get('touches')}, slope={desc.get('slope_pct_per_candle')}%/candle")
                if not asc and not desc:
                    logger.info(f"   ⚠️ No trendlines detected - need more swing points or better alignment")

                # 🎯 PRICE PREDICTION - predict where price will be 5 candles ahead
                prediction = None
                prediction_dict = None
                trend_ctx = {}  # Will be populated with trend context for learning
                try:
                    # Get patterns for prediction context
                    pattern_detector = PatternDetector()
                    candles_15m = self.hl.get_candles(symbol, interval="15m", limit=100)
                    candles_1h = self.hl.get_candles(symbol, interval="1h", limit=100)

                    patterns = pattern_detector.get_alert_patterns(
                        candles_5m=candles,
                        candles_15m=candles_15m or [],
                        candles_1h=candles_1h or [],
                        min_score=50
                    )

                    # 📊 Calculate trend context for learning
                    trend_ctx = calculate_trend_context(candles, patterns)

                    prediction = predictor.predict_price_5_candles(
                        symbol=symbol,
                        candles=candles,
                        timeframe="5m",
                        patterns=patterns
                    )
                    prediction_dict = prediction.to_dict()

                    logger.info(f"🎯 {symbol} 5m Prediction: ${prediction.predicted_price:,.2f} ({prediction.predicted_direction}) conf={prediction.confidence:.0%}")
                    logger.debug(f"📊 {symbol} trend context: dir={trend_ctx['trend_direction']}, strength={trend_ctx['trend_strength']}, ema={trend_ctx['ema_position']}")

                    # Save prediction to database with trend context
                    db = get_db()
                    db.save_prediction(
                        symbol=symbol,
                        timeframe="5m",
                        current_price=prediction.current_price,
                        predicted_price=prediction.predicted_price,
                        predicted_direction=prediction.predicted_direction,
                        confidence=prediction.confidence,
                        predicted_pct_change=prediction.predicted_pct_change,
                        reasoning=prediction.reasoning,
                        patterns_used=prediction.patterns_used,
                        # Trend context for learning
                        trend_direction=trend_ctx.get("trend_direction"),
                        trend_strength=trend_ctx.get("trend_strength"),
                        ema_position=trend_ctx.get("ema_position"),
                        rsi_value=trend_ctx.get("rsi_value"),
                        macd_histogram=trend_ctx.get("macd_histogram"),
                        volatility_regime=trend_ctx.get("volatility_regime")
                    )
                except Exception as pe:
                    logger.warning(f"Prediction failed for {symbol}: {pe}")
                    trend_ctx = calculate_trend_context(candles)  # Still calc for signal save

                # Generate chart - pass same lookback used for detection + prediction
                img_bytes = await self.generate_chart_image(
                    candles, symbol, "5m", trendlines, sr, lookback=short_lookback,
                    prediction=prediction_dict
                )

                # Generate analysis
                analysis = self._generate_quick_analysis(symbol, candles, trendlines, sr, "5m")

                # Build message
                price = candles[-1]['close']
                signal = trendlines.get('signal', 'neutral')
                # Determine emoji - "breaking" reverses the meaning!
                if signal == "breaking_resistance":
                    trend_emoji = "🚀"  # Bullish breakout
                elif signal == "breaking_support":
                    trend_emoji = "💥"  # Bearish breakdown
                elif "support" in signal or "bullish" in signal:
                    trend_emoji = "📈"  # At support, expecting bounce up
                elif "resistance" in signal or "bearish" in signal:
                    trend_emoji = "📉"  # At resistance, expecting rejection down
                else:
                    trend_emoji = "➡️"

                msg = f"{trend_emoji} **{symbol} 5m Update** ({datetime.now().strftime('%H:%M UTC')})\n"
                msg += f"Price: **{format_price(price)}**\n\n"
                msg += analysis

                # Send to ticker channel
                await self._send_chart_to_channel(symbol, msg, img_bytes, f"{symbol.lower()}_5m.png")

                # Determine direction - IMPORTANT: "breaking" reverses the meaning!
                # - "breaking_support" = price falling BELOW support = BEARISH
                # - "breaking_resistance" = price rising ABOVE resistance = BULLISH
                asc = trendlines.get('ascending_support', {})
                desc = trendlines.get('descending_resistance', {})
                if signal == 'breaking_resistance':
                    direction = 'bullish'  # Breaking ABOVE resistance = bullish breakout
                elif signal == 'breaking_support':
                    direction = 'bearish'  # Breaking BELOW support = bearish breakdown
                elif 'support' in signal or 'bullish' in signal.lower():
                    direction = 'bullish'  # At/testing support = expecting bounce up
                elif 'resistance' in signal or 'bearish' in signal.lower():
                    direction = 'bearish'  # At/testing resistance = expecting rejection down
                else:
                    direction = 'neutral'

                # Check if signal passes all validation filters
                signal_valid = trendlines.get('signal_valid', True)
                signal_strength = trendlines.get('signal_strength', 0.5)
                trend_filter = trendlines.get('trend_filter', 'unknown')
                rejection_reason = trendlines.get('rejection_reason')

                # 📚 APPLY LEARNING ADJUSTMENT to confidence
                # This adjusts confidence based on historical signal accuracy
                learning_adjustment = 1.0
                if self.signal_learner and signal != 'neutral':
                    try:
                        has_trendline = asc.get('current_price') or desc.get('current_price')
                        learning_adjustment = self.signal_learner.get_confidence_adjustment(
                            symbol=symbol,
                            direction=direction,
                            has_deepseek=False,
                            has_trendline=bool(has_trendline)
                        )
                        if learning_adjustment != 1.0:
                            original_strength = signal_strength
                            signal_strength = min(max(signal_strength * learning_adjustment, 0.1), 1.0)
                            logger.info(f"📚 {symbol} learning adjustment: {original_strength:.2f} → {signal_strength:.2f} (x{learning_adjustment:.2f})")
                    except Exception as e:
                        logger.warning(f"Could not get learning adjustment: {e}")

                # Log filter status
                if not signal_valid:
                    logger.info(f"⚠️ {symbol} signal filtered: {signal} → {rejection_reason or 'low_strength'} (strength={signal_strength:.2f}, trend={trend_filter})")

                # Save chart and signal to database
                try:
                    db = get_db()

                    # Save chart image (always save for visual tracking)
                    db.save_chart(
                        symbol=symbol,
                        timeframe="5m",
                        price=price,
                        image_data=img_bytes,
                        signal=signal if signal_valid else f"{signal}_filtered",
                        direction=direction if signal_valid else 'filtered',
                        analysis_text=analysis
                    )

                    # Only save actionable signals for outcome tracking
                    if signal_valid and signal != 'neutral':
                        signal_id = f"{symbol}_5m_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
                        db.save_chart_signal(
                            signal_id=signal_id,
                            signal_type="chart_5m",
                            symbol=symbol,
                            price=price,
                            direction=direction,
                            confidence=signal_strength,  # Use the validated strength
                            support_levels=sr.get('supports', [])[:3],
                            resistance_levels=sr.get('resistances', [])[:3],
                            asc_support_price=asc.get('current_price'),
                            desc_resistance_price=desc.get('current_price'),
                            trendline_signal=signal,
                            # Trend context for learning analytics
                            trend_direction=trend_ctx.get("trend_direction"),
                            trend_strength=trend_ctx.get("trend_strength"),
                            ema_position=trend_ctx.get("ema_position"),
                            rsi_value=trend_ctx.get("rsi_value"),
                            macd_histogram=trend_ctx.get("macd_histogram"),
                            patterns_detected=trend_ctx.get("patterns_detected"),
                            volume_trend=trend_ctx.get("volume_trend"),
                            volatility_regime=trend_ctx.get("volatility_regime")
                        )
                        logger.info(f"📀 Saved {symbol} 5m VALID signal (strength={signal_strength:.2f}, trend={trend_ctx.get('trend_direction', 'unknown')})")
                    else:
                        logger.info(f"📀 Saved {symbol} 5m chart (signal filtered or neutral)")
                except Exception as e:
                    logger.error(f"Failed to save chart to database: {e}")

                logger.info(f"✅ Posted {symbol} 5m chart")
                success_count += 1
                await asyncio.sleep(1)  # Rate limit

            except Exception as e:
                logger.error(f"❌ Error generating {symbol} 5m chart: {e}", exc_info=True)
                failed_tickers.append(symbol)

        logger.info(f"📊 5m charts complete: {success_count}/{len(TICKERS)} successful")
        if failed_tickers:
            logger.warning(f"⚠️ Failed tickers: {failed_tickers}")
        self.last_30m_run = datetime.utcnow()

    async def generate_daily_charts(self) -> None:
        """Generate daily charts for all tickers with 24hr analysis."""
        from src.technical_analysis import detect_trendlines, calculate_support_resistance
        from src.pattern_detector import PatternDetector, PricePredictor

        logger.info(f"📅 Generating daily charts for ALL {len(TICKERS)} tickers: {TICKERS}")
        success_count = 0
        failed_tickers = []

        # Initialize predictor for price predictions
        predictor = PricePredictor()

        for symbol in TICKERS:
            logger.info(f"📅 Processing {symbol} daily chart...")
            try:
                # Get 90 days of daily candles for macro view
                candles = self.hl.get_candles(symbol, interval="1d", limit=90)
                if not candles or len(candles) < 30:
                    logger.warning(f"Not enough daily candles for {symbol}")
                    failed_tickers.append(f"{symbol}(no_data)")
                    continue

                # Analysis - use lookback=60 for macro S/R levels over 90 days
                daily_lookback = 60
                trendlines = detect_trendlines(candles, lookback=daily_lookback, min_touches=2)
                sr = calculate_support_resistance(candles, lookback=daily_lookback)

                # 🎯 PRICE PREDICTION - predict where price will be 5 candles (5 days) ahead
                prediction = None
                prediction_dict = None
                trend_ctx = {}  # Will be populated with trend context for learning
                try:
                    # Get patterns for prediction context
                    pattern_detector = PatternDetector()
                    candles_4h = self.hl.get_candles(symbol, interval="4h", limit=100)
                    candles_1h = self.hl.get_candles(symbol, interval="1h", limit=100)

                    patterns = pattern_detector.get_alert_patterns(
                        candles_5m=[],  # Not relevant for daily
                        candles_15m=[],
                        candles_1h=candles_1h or [],
                        min_score=50
                    )

                    # 📊 Calculate trend context for learning
                    trend_ctx = calculate_trend_context(candles, patterns)

                    prediction = predictor.predict_price_5_candles(
                        symbol=symbol,
                        candles=candles,
                        timeframe="1d",
                        patterns=patterns
                    )
                    prediction_dict = prediction.to_dict()

                    logger.info(f"🎯 {symbol} Daily Prediction: ${prediction.predicted_price:,.2f} ({prediction.predicted_direction}) conf={prediction.confidence:.0%}")
                    logger.debug(f"📊 {symbol} daily trend context: dir={trend_ctx['trend_direction']}, strength={trend_ctx['trend_strength']}, ema={trend_ctx['ema_position']}")

                    # Save prediction to database with trend context
                    db = get_db()
                    db.save_prediction(
                        symbol=symbol,
                        timeframe="1d",
                        current_price=prediction.current_price,
                        predicted_price=prediction.predicted_price,
                        predicted_direction=prediction.predicted_direction,
                        confidence=prediction.confidence,
                        predicted_pct_change=prediction.predicted_pct_change,
                        reasoning=prediction.reasoning,
                        patterns_used=prediction.patterns_used,
                        # Trend context for learning
                        trend_direction=trend_ctx.get("trend_direction"),
                        trend_strength=trend_ctx.get("trend_strength"),
                        ema_position=trend_ctx.get("ema_position"),
                        rsi_value=trend_ctx.get("rsi_value"),
                        macd_histogram=trend_ctx.get("macd_histogram"),
                        volatility_regime=trend_ctx.get("volatility_regime")
                    )
                except Exception as pe:
                    logger.warning(f"Daily prediction failed for {symbol}: {pe}")
                    trend_ctx = calculate_trend_context(candles)  # Still calc for signal save

                # Generate chart - pass same lookback used for detection + prediction
                img_bytes = await self.generate_chart_image(
                    candles, symbol, "1D", trendlines, sr, lookback=daily_lookback,
                    prediction=prediction_dict
                )

                # Generate daily analysis
                analysis = self._generate_daily_analysis(symbol, candles, trendlines, sr)

                # Get DeepSeek trading recommendation
                deepseek_take = await self._get_deepseek_daily_take(symbol, candles, trendlines, sr)

                msg = f"📅 **{symbol} Daily Chart** ({datetime.now().strftime('%Y-%m-%d')})\n\n"
                msg += analysis
                if deepseek_take:
                    msg += f"\n\n🤖 **DeepSeek's Take:**\n{deepseek_take}"

                # Send to ticker channel
                await self._send_chart_to_channel(symbol, msg, img_bytes, f"{symbol.lower()}_daily.png")

                # Save daily chart and signal to database
                try:
                    price = candles[-1]['close']
                    signal = trendlines.get('signal', 'neutral')
                    asc = trendlines.get('ascending_support', {})
                    desc = trendlines.get('descending_resistance', {})

                    # Determine direction - IMPORTANT: "breaking" reverses the meaning!
                    # - "breaking_support" = price falling BELOW support = BEARISH
                    # - "breaking_resistance" = price rising ABOVE resistance = BULLISH
                    if signal == 'breaking_resistance':
                        direction = 'bullish'  # Breaking ABOVE resistance = bullish breakout
                    elif signal == 'breaking_support':
                        direction = 'bearish'  # Breaking BELOW support = bearish breakdown
                    elif 'support' in signal or 'bullish' in signal.lower():
                        direction = 'bullish'  # At/testing support = expecting bounce up
                    elif 'resistance' in signal or 'bearish' in signal.lower():
                        direction = 'bearish'  # At/testing resistance = expecting rejection down
                    else:
                        direction = 'neutral'

                    # Check if signal passes all validation filters
                    signal_valid = trendlines.get('signal_valid', True)
                    signal_strength = trendlines.get('signal_strength', 0.5)
                    trend_filter = trendlines.get('trend_filter', 'unknown')
                    rejection_reason = trendlines.get('rejection_reason')

                    # 📚 APPLY LEARNING ADJUSTMENT to daily confidence
                    learning_adjustment = 1.0
                    if self.signal_learner and signal != 'neutral':
                        try:
                            has_trendline = asc.get('current_price') or desc.get('current_price')
                            learning_adjustment = self.signal_learner.get_confidence_adjustment(
                                symbol=symbol,
                                direction=direction,
                                has_deepseek=bool(deepseek_take),
                                has_trendline=bool(has_trendline)
                            )
                            if learning_adjustment != 1.0:
                                original_strength = signal_strength
                                signal_strength = min(max(signal_strength * learning_adjustment, 0.1), 1.0)
                                logger.info(f"📚 {symbol} daily learning adjustment: {original_strength:.2f} → {signal_strength:.2f} (x{learning_adjustment:.2f})")
                        except Exception as e:
                            logger.warning(f"Could not get daily learning adjustment: {e}")

                    if not signal_valid:
                        logger.info(f"⚠️ {symbol} daily signal filtered: {signal} → {rejection_reason or 'low_strength'} (strength={signal_strength:.2f}, trend={trend_filter})")

                    # Parse DeepSeek bias
                    ds_bias = None
                    if deepseek_take:
                        ds_upper = deepseek_take.upper()
                        if 'LONG' in ds_upper:
                            ds_bias = 'LONG'
                        elif 'SHORT' in ds_upper:
                            ds_bias = 'SHORT'
                        else:
                            ds_bias = 'NEUTRAL'

                    db = get_db()

                    # Save chart image (always save for visual tracking)
                    db.save_chart(
                        symbol=symbol,
                        timeframe="1d",
                        price=price,
                        image_data=img_bytes,
                        signal=signal if signal_valid else f"{signal}_filtered",
                        direction=direction if signal_valid else 'filtered',
                        analysis_text=analysis + (f"\n\nDeepSeek: {deepseek_take}" if deepseek_take else "")
                    )

                    # Only save actionable signals for outcome tracking
                    if signal_valid and signal != 'neutral':
                        signal_id = f"{symbol}_daily_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
                        db.save_chart_signal(
                            signal_id=signal_id,
                            signal_type="chart_daily",
                            symbol=symbol,
                            price=price,
                            direction=direction,
                            confidence=signal_strength,
                            support_levels=sr.get('supports', [])[:3],
                            resistance_levels=sr.get('resistances', [])[:3],
                            asc_support_price=asc.get('current_price'),
                            desc_resistance_price=desc.get('current_price'),
                            trendline_signal=signal,
                            deepseek_bias=ds_bias,
                            # Trend context for learning analytics
                            trend_direction=trend_ctx.get("trend_direction"),
                            trend_strength=trend_ctx.get("trend_strength"),
                            ema_position=trend_ctx.get("ema_position"),
                            rsi_value=trend_ctx.get("rsi_value"),
                            macd_histogram=trend_ctx.get("macd_histogram"),
                            patterns_detected=trend_ctx.get("patterns_detected"),
                            volume_trend=trend_ctx.get("volume_trend"),
                            volatility_regime=trend_ctx.get("volatility_regime")
                        )
                        logger.info(f"📀 Saved {symbol} daily VALID signal (strength={signal_strength:.2f}, trend={trend_ctx.get('trend_direction', 'unknown')})")
                    else:
                        logger.info(f"📀 Saved {symbol} daily chart (signal filtered or neutral)")
                except Exception as e:
                    logger.error(f"Failed to save daily chart to database: {e}")

                logger.info(f"✅ Posted {symbol} daily chart")
                success_count += 1
                await asyncio.sleep(1)

            except Exception as e:
                logger.error(f"❌ Error generating {symbol} daily chart: {e}", exc_info=True)
                failed_tickers.append(symbol)

        logger.info(f"📅 Daily charts complete: {success_count}/{len(TICKERS)} successful")
        if failed_tickers:
            logger.warning(f"⚠️ Failed tickers: {failed_tickers}")
        self.last_daily_run = datetime.utcnow()

    async def generate_vista_analysis(self) -> None:
        """Generate hourly Vista AI market analysis with trade setups.

        Posts a comprehensive analysis to Discord with:
        - Market overview across all tickers
        - Best trade setups ranked
        - Entry zones, stop losses, targets
        """
        from src.technical_analysis import detect_trendlines, calculate_support_resistance

        logger.info("🔮 Vista AI: Generating hourly market analysis...")

        if not self.llm or not hasattr(self.llm, 'deepseek_client'):
            logger.warning("Vista AI: DeepSeek not available, skipping analysis")
            self.last_vista_run = datetime.utcnow()
            return

        # Get recent alpha calls to avoid repetition
        recent_calls = []
        if self.db:
            try:
                alerts = self.db.get_discord_alerts(alert_type="alpha_call", limit=10)
                recent_calls = [a.get("symbol") for a in alerts if a.get("symbol")]
            except Exception as e:
                logger.warning(f"Could not get recent alpha calls: {e}")

        # Gather data for all tickers
        market_data = {}
        for symbol in TICKERS:
            try:
                # Get both 5m and daily data
                candles_5m = self.hl.get_candles(symbol, interval="5m", limit=100)
                candles_daily = self.hl.get_candles(symbol, interval="1d", limit=30)

                if not candles_5m or not candles_daily:
                    continue

                trendlines_5m = detect_trendlines(candles_5m, lookback=50, min_touches=2)
                trendlines_daily = detect_trendlines(candles_daily, lookback=30, min_touches=2)
                sr_5m = calculate_support_resistance(candles_5m, lookback=50)
                sr_daily = calculate_support_resistance(candles_daily, lookback=30)

                price = candles_5m[-1]['close']

                # Calculate key metrics
                change_1h = ((price - candles_5m[-12]['close']) / candles_5m[-12]['close'] * 100) if len(candles_5m) >= 12 else 0
                change_24h = ((price - candles_daily[-2]['close']) / candles_daily[-2]['close'] * 100) if len(candles_daily) >= 2 else 0

                market_data[symbol] = {
                    'price': price,
                    'change_1h': change_1h,
                    'change_24h': change_24h,
                    'signal_5m': trendlines_5m.get('signal', 'neutral'),
                    'signal_daily': trendlines_daily.get('signal', 'neutral'),
                    'supports': sr_daily.get('supports', [])[:3],
                    'resistances': sr_daily.get('resistances', [])[:3],
                    'asc_support': trendlines_daily.get('ascending_support', {}).get('current_price'),
                    'desc_resistance': trendlines_daily.get('descending_resistance', {}).get('current_price'),
                }
            except Exception as e:
                logger.error(f"Vista AI: Error getting {symbol} data: {e}")

        if not market_data:
            logger.warning("Vista AI: No market data available")
            self.last_vista_run = datetime.utcnow()
            return

        # Build prompt for DeepSeek - ask for structured JSON response
        prompt = self._build_vista_prompt(market_data, recent_calls)

        # Build system prompt with variety instruction
        avoid_symbols = recent_calls[:3] if recent_calls else []
        avoid_msg = ""
        if avoid_symbols:
            avoid_msg = f"\n\nIMPORTANT: You recently called {', '.join(avoid_symbols)}. DO NOT pick these again unless they have significantly different setups now. Vary your picks across all available symbols."

        system_prompt = f"""You are Vista AI, a crypto trading analyst.
Analyze the market data and identify the BEST trade setup.

IMPORTANT RULES:
1. VARY your picks - don't keep calling the same symbol repeatedly
2. Focus on BTC and ETH more often as they have the best liquidity
3. Only call altcoins when they have exceptional setups
4. Prioritize setups with clear support/resistance levels and tight stops{avoid_msg}

Respond in this EXACT JSON format:
{{
  "market_overview": "2-3 sentence market summary",
  "best_setup": {{
    "symbol": "BTC/ETH/SOL/etc",
    "direction": "LONG or SHORT",
    "entry": 95000,
    "stop_loss": 94000,
    "target": 98000,
    "reasoning": "Why this is a good trade"
  }},
  "secondary_setup": {{
    "symbol": "ETH/SOL/etc",
    "direction": "LONG or SHORT",
    "entry": 3400,
    "stop_loss": 3300,
    "target": 3600,
    "reasoning": "Why this is also worth watching"
  }}
}}

Be specific with prices. Only call setups you're confident in."""

        try:
            import asyncio
            import json as json_module
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self.llm.deepseek_client.chat.completions.create(
                    model="deepseek-chat",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=800,
                    temperature=0.5  # Slightly higher temp for more variety
                )
            )
            analysis_text = response.choices[0].message.content.strip()

            # Try to parse JSON response
            try:
                # Extract JSON from response (handle markdown code blocks)
                if "```json" in analysis_text:
                    analysis_text = analysis_text.split("```json")[1].split("```")[0]
                elif "```" in analysis_text:
                    analysis_text = analysis_text.split("```")[1].split("```")[0]

                analysis = json_module.loads(analysis_text)

                # Send alpha call for best setup with @everyone
                if self.discord and analysis.get("best_setup"):
                    setup = analysis["best_setup"]
                    chosen_symbol = setup.get("symbol", "BTC")

                    # Check if this symbol was just called (within last 3 calls)
                    recently_called = chosen_symbol in recent_calls[:3]

                    if recently_called:
                        # Log but don't send if same symbol called too recently
                        logger.warning(f"⚠️ Vista AI chose {chosen_symbol} again - skipping to avoid spam")
                        # Try secondary setup instead
                        if analysis.get("secondary_setup"):
                            setup = analysis["secondary_setup"]
                            chosen_symbol = setup.get("symbol", "BTC")
                            if chosen_symbol not in recent_calls[:3]:
                                recently_called = False  # Secondary is fine
                            else:
                                logger.warning(f"⚠️ Secondary setup ({chosen_symbol}) also recent - skipping alpha call")

                    if not recently_called:
                        await self.discord.send_alpha_call(
                            symbol=chosen_symbol,
                            direction=setup.get("direction", "LONG"),
                            entry=float(setup.get("entry", 0)),
                            stop_loss=float(setup.get("stop_loss", 0)),
                            target=float(setup.get("target", 0)),
                            reasoning=setup.get("reasoning", "Vista AI identified this setup"),
                            confidence=0.75
                        )
                        logger.info(f"✅ Alpha call sent: {setup.get('direction')} {chosen_symbol}")

                # Also send market overview to alpha calls channel
                if self.discord and analysis.get("market_overview"):
                    overview_msg = f"🔮 **Vista AI Market Update** - {datetime.utcnow().strftime('%H:%M UTC')}\n\n"
                    overview_msg += analysis.get("market_overview", "")
                    await self._send_vista_to_discord(overview_msg)

            except (json_module.JSONDecodeError, KeyError) as e:
                # Fallback: send raw analysis if JSON parsing fails
                logger.warning(f"Vista AI: Could not parse JSON, sending raw: {e}")
                msg = f"🔮 **Vista AI - Hourly Analysis**\n"
                msg += f"*{datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}*\n\n"
                msg += analysis_text
                if self.discord:
                    await self._send_vista_to_discord(msg)

            logger.info("✅ Vista AI analysis posted to Discord")

        except Exception as e:
            logger.error(f"Vista AI: DeepSeek analysis failed: {e}")

        self.last_vista_run = datetime.utcnow()

    def _build_vista_prompt(self, market_data: Dict, recent_calls: List[str] = None) -> str:
        """Build the prompt for Vista AI analysis with learning context."""
        lines = []

        # 📚 ADD LEARNING CONTEXT FROM DATABASE
        try:
            db = get_db()
            # Get overall DeepSeek accuracy
            ds_stats = db.get_deepseek_accuracy(days=14)
            if ds_stats['total_predictions'] >= 3:
                acc = ds_stats['accuracy_pct']
                lines.append("=== YOUR RECENT PERFORMANCE ===")
                lines.append(f"Accuracy: {acc:.0f}% ({ds_stats['correct']}/{ds_stats['correct']+ds_stats['incorrect']})")

                if acc < 50:
                    lines.append("⚠️ BELOW 50% - Be more selective! Say NEUTRAL when uncertain.")
                elif acc > 65:
                    lines.append("✅ Good performance. Maintain disciplined approach.")

                # Show best performing symbol/direction combos
                patterns = db.get_winning_patterns(min_samples=3)
                best_combos = patterns.get('best_symbol_direction_combos', [])[:3]
                if best_combos:
                    lines.append("\nYour best performing setups:")
                    for combo in best_combos:
                        win_rate = (combo['correct'] / combo['total'] * 100) if combo['total'] > 0 else 0
                        lines.append(f"  - {combo['symbol']} {combo['direction']}: {win_rate:.0f}% ({combo['correct']}/{combo['total']})")

                # Show recent misses to avoid
                if ds_stats['recent_misses']:
                    lines.append("\nRecent misses (avoid similar setups):")
                    for miss in ds_stats['recent_misses'][:3]:
                        lines.append(f"  - {miss['symbol']} {miss['deepseek_bias']}: moved {miss.get('outcome_pct_4h', 0):+.1f}%")

                lines.append("")
        except Exception as e:
            logger.warning(f"Could not get Vista learning context: {e}")

        lines.append("=== CURRENT MARKET DATA ===\n")

        # Show recent calls to encourage variety
        if recent_calls:
            # Count frequency of each symbol in recent calls
            from collections import Counter
            call_counts = Counter(recent_calls[:10])
            overused = [s for s, c in call_counts.items() if c >= 3]
            if overused:
                lines.append(f"⚠️ AVOID THESE (called too often recently): {', '.join(overused)}\n")

        for symbol, data in market_data.items():
            # Mark recently called symbols
            marker = "⚠️" if symbol in (recent_calls or [])[:3] else "📊"
            lines.append(f"{marker} **{symbol}**: {format_price(data['price'])}")
            lines.append(f"  1h: {data['change_1h']:+.1f}% | 24h: {data['change_24h']:+.1f}%")
            lines.append(f"  5m Signal: {data['signal_5m']} | Daily Signal: {data['signal_daily']}")

            supports = data.get('supports') or []
            resistances = data.get('resistances') or []
            if supports:
                lines.append(f"  Support: {format_price(supports[0])}")
            if resistances:
                lines.append(f"  Resistance: {format_price(resistances[0])}")
            if data.get('asc_support'):
                lines.append(f"  Ascending Support: {format_price(data['asc_support'])}")
            if data.get('desc_resistance'):
                lines.append(f"  Descending Resistance: {format_price(data['desc_resistance'])}")
            lines.append("")

        lines.append("\nProvide trade setups with specific entry, stop, and target prices.")
        lines.append("Remember: Pick DIFFERENT symbols than recently called unless there's a significantly better setup now.")
        lines.append("Your predictions are tracked - only call LONG/SHORT when confident, otherwise say NO CLEAR SETUP.")
        return "\n".join(lines)

    async def _send_vista_to_discord(self, message: str) -> bool:
        """Send Vista AI analysis to Discord alpha_calls channel."""
        if not self.discord:
            logger.warning("Vista AI: Discord not available")
            return False

        try:
            import discord
            # Send to alpha_calls channel (or fallback to default)
            channel_id = self.discord.channels.alpha_calls or self.discord.channels.default
            if not channel_id:
                logger.error("Vista AI: No alpha_calls channel configured")
                return False

            channel = self.discord.client.get_channel(channel_id)
            if not channel:
                channel = await self.discord.client.fetch_channel(channel_id)

            if channel:
                await channel.send(content=message)
                return True
            else:
                logger.error("Vista AI: Could not find Discord channel")
                return False
        except Exception as e:
            logger.error(f"Vista AI: Failed to send to Discord: {e}")
            return False

    async def _get_deepseek_daily_take(self, symbol: str, candles: List[Dict],
                                        trendlines: Dict, sr: Dict) -> str:
        """Get DeepSeek's quick trading recommendation for daily chart.

        Now includes learning context from database to help DeepSeek self-correct.
        """
        if not self.llm or not hasattr(self.llm, 'deepseek_client'):
            # Fallback: generate rule-based recommendation
            return self._generate_rule_based_take(symbol, candles, trendlines, sr)

        try:
            price = candles[-1]['close']
            signal = trendlines.get('signal', 'neutral')

            # Build context
            supports = sr.get('supports', [])[:3]
            resistances = sr.get('resistances', [])[:3]
            nearest_support = supports[0] if supports else price * 0.95
            nearest_resistance = resistances[0] if resistances else price * 1.05

            asc = trendlines.get('ascending_support', {})
            desc = trendlines.get('descending_resistance', {})

            # 📚 GET LEARNING CONTEXT FROM DATABASE
            learning_context = ""
            try:
                db = get_db()
                learning_context = db.get_deepseek_prompt_context(symbol, days=14)
                if learning_context:
                    learning_context = f"\n{learning_context}\n"
            except Exception as e:
                logger.warning(f"Could not get learning context: {e}")

            # Build system prompt with learning feedback
            system_prompt = """You're a crypto trader giving daily bias. Be specific with prices. Max 3 sentences.

IMPORTANT: Your predictions are tracked. Price must move >0.5% in 4 hours in your direction to be "correct".
- If accuracy is below 50%, be more conservative and say NEUTRAL when uncertain
- Only call LONG/SHORT when you have high conviction
- Learn from your recent misses"""

            prompt = f"""{learning_context}
=== CURRENT ANALYSIS FOR {symbol} ===

Current price: {format_price(price)}
Trendline signal: {signal}
Key support: {format_price(nearest_support)} ({((price - nearest_support) / price * 100):.1f}% below)
Key resistance: {format_price(nearest_resistance)} ({((nearest_resistance - price) / price * 100):.1f}% above)
Ascending support line at: {format_price(asc.get('current_price', 0))}
Descending resistance line at: {format_price(desc.get('current_price', 0))}

Based on your learning context above and this data, state:
1. Your bias: LONG, SHORT, or NEUTRAL (say NEUTRAL if uncertain!)
2. Entry zone, stop loss, and target with specific prices
3. Brief reasoning (1-2 sentences)"""

            # Use LLM service's deepseek_client directly (sync call in async context)
            import asyncio
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self.llm.deepseek_client.chat.completions.create(
                    model="deepseek-chat",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=200,
                    temperature=0.3
                )
            )
            return response.choices[0].message.content.strip()

        except Exception as e:
            logger.error(f"DeepSeek daily take failed: {e}")
            return self._generate_rule_based_take(symbol, candles, trendlines, sr)

    def _generate_rule_based_take(self, symbol: str, candles: List[Dict],
                                   trendlines: Dict, sr: Dict) -> str:
        """Generate rule-based trading recommendation when LLM unavailable."""
        price = candles[-1]['close']
        signal = trendlines.get('signal', 'neutral')

        supports = sr.get('supports', [])[:3]
        resistances = sr.get('resistances', [])[:3]
        nearest_support = supports[0] if supports else price * 0.95
        nearest_resistance = resistances[0] if resistances else price * 1.05

        dist_to_support = (price - nearest_support) / price * 100
        dist_to_resistance = (nearest_resistance - price) / price * 100

        if "breaking_resistance" in signal or "above_resistance" in signal:
            bias = "LONG"
            entry = f"{format_price(price)}-{format_price(price * 1.01)} on pullback"
            stop = f"{format_price(nearest_support)}"
            target = f"{format_price(nearest_resistance * 1.05)}"
        elif "breaking_support" in signal or "below_support" in signal:
            bias = "SHORT"
            entry = f"{format_price(price * 0.99)}-{format_price(price)} on bounce"
            stop = f"{format_price(nearest_resistance)}"
            target = f"{format_price(nearest_support * 0.95)}"
        elif dist_to_support < 2:
            bias = "LONG"
            entry = f"{format_price(nearest_support)}-{format_price(nearest_support * 1.01)}"
            stop = f"{format_price(nearest_support * 0.98)}"
            target = f"{format_price(nearest_resistance)}"
        elif dist_to_resistance < 2:
            bias = "SHORT"
            entry = f"{format_price(nearest_resistance * 0.99)}-{format_price(nearest_resistance)}"
            stop = f"{format_price(nearest_resistance * 1.02)}"
            target = f"{format_price(nearest_support)}"
        else:
            bias = "NEUTRAL"
            entry = f"Wait for {format_price(nearest_support)} or {format_price(nearest_resistance)}"
            stop = "N/A"
            target = "N/A"

        return f"**{bias}** | Entry: {entry} | Stop: {stop} | Target: {target}"

    async def _send_chart_to_channel(self, symbol: str, message: str,
                                      img_bytes: bytes, filename: str) -> bool:
        """Send chart image to the appropriate Discord channel."""
        import discord

        if not self.discord:
            logger.warning(f"Chart for {symbol}: Discord notifier not available")
            return False

        if not self.discord.client:
            logger.warning(f"Chart for {symbol}: Discord client not initialized")
            return False

        if not self.discord.client.is_ready():
            logger.warning(f"Chart for {symbol}: Discord client not ready yet")
            return False

        try:
            # Get channel for symbol
            channel_id = self.discord._get_channel_for_symbol(symbol)
            if not channel_id:
                logger.error(f"❌ No channel configured for {symbol}! Check DISCORD_CHANNEL_{symbol}_SIGNALS env var")
                return False
            logger.info(f"📊 Sending {symbol} chart to channel {channel_id}")

            channel = self.discord.client.get_channel(channel_id)
            if not channel:
                logger.info(f"Channel not in cache, fetching...")
                channel = await self.discord.client.fetch_channel(channel_id)

            if channel:
                file = discord.File(BytesIO(img_bytes), filename=filename)
                await channel.send(content=message, file=file)
                logger.info(f"✅ Chart sent to {symbol} channel")
                return True
            else:
                logger.error(f"Could not find channel {channel_id} for {symbol}")
                return False
        except Exception as e:
            logger.error(f"Failed to send chart for {symbol}: {e}", exc_info=True)
            return False

    async def _check_prediction_outcomes(self) -> None:
        """Check pending predictions and update with actual outcomes."""
        from datetime import timedelta

        try:
            db = get_db()

            # Get pending predictions
            pending_5m = db.get_pending_predictions(timeframe="5m")
            pending_1d = db.get_pending_predictions(timeframe="1d")

            now = datetime.utcnow()
            checked_count = 0

            # Check 5m predictions (5 candles = 25 minutes)
            for pred in pending_5m:
                pred_time = datetime.fromisoformat(pred["timestamp"])
                elapsed_minutes = (now - pred_time).total_seconds() / 60

                # Check after 25 minutes (5 x 5m candles)
                if elapsed_minutes >= 25:
                    try:
                        actual_price = self.hl.get_price(pred["symbol"])
                        if actual_price:
                            result = db.update_prediction_outcome(pred["id"], actual_price)
                            checked_count += 1

                            # Log result
                            direction_emoji = "✅" if result.get("direction_correct") else "❌"
                            logger.info(f"🎯 {pred['symbol']} 5m prediction: {direction_emoji} "
                                       f"Predicted ${pred['predicted_price']:,.0f} → Actual ${actual_price:,.0f} "
                                       f"(error: {result.get('error_pct', 0):.2f}%)")
                    except Exception as e:
                        logger.warning(f"Failed to check 5m prediction {pred['id']}: {e}")

            # Check daily predictions (5 candles = 5 days)
            for pred in pending_1d:
                pred_time = datetime.fromisoformat(pred["timestamp"])
                elapsed_days = (now - pred_time).total_seconds() / 86400

                # Check after 5 days
                if elapsed_days >= 5:
                    try:
                        actual_price = self.hl.get_price(pred["symbol"])
                        if actual_price:
                            result = db.update_prediction_outcome(pred["id"], actual_price)
                            checked_count += 1

                            direction_emoji = "✅" if result.get("direction_correct") else "❌"
                            logger.info(f"🎯 {pred['symbol']} Daily prediction: {direction_emoji} "
                                       f"Predicted ${pred['predicted_price']:,.0f} → Actual ${actual_price:,.0f} "
                                       f"(error: {result.get('error_pct', 0):.2f}%)")
                    except Exception as e:
                        logger.warning(f"Failed to check daily prediction {pred['id']}: {e}")

            if checked_count > 0:
                # Log overall accuracy
                accuracy = db.get_prediction_accuracy(days=30)
                logger.info(f"📊 Prediction accuracy (30d): {accuracy['accuracy_pct']:.1f}% "
                           f"({accuracy['correct_direction']}/{accuracy['total_predictions']} correct)")

        except Exception as e:
            logger.error(f"Error checking prediction outcomes: {e}")

    async def run_scheduler(self) -> None:
        """Main scheduler loop - runs every minute to check if charts need generating."""
        logger.info("🕐 Chart scheduler started")

        # Wait for Discord to be ready before generating charts
        if self.discord and self.discord.client:
            logger.info("⏳ Waiting for Discord to be ready...")
            for _ in range(30):  # Wait up to 30 seconds
                if self.discord.client.is_ready():
                    logger.info("✅ Discord is ready")
                    break
                await asyncio.sleep(1)
            else:
                logger.warning("⚠️ Discord not ready after 30s, proceeding anyway")

        # Generate 5m charts immediately on startup
        logger.info("📊 Generating initial 5m charts on startup...")
        try:
            await self.generate_5m_charts()
            logger.info("✅ Initial 5m charts generated")
        except Exception as e:
            logger.error(f"Failed to generate startup charts: {e}", exc_info=True)

        # Also run Vista AI analysis on startup
        logger.info("🔮 Running initial Vista AI analysis...")
        try:
            await self.generate_vista_analysis()
        except Exception as e:
            logger.error(f"Failed to generate Vista analysis: {e}", exc_info=True)

        # Log next scheduled runs
        logger.info(f"📅 Chart scheduler loop starting - 5m every 30min, Vista AI hourly, daily every 24h")

        loop_count = 0
        while True:
            try:
                now = datetime.utcnow()
                loop_count += 1

                # Log every 10 minutes to show scheduler is alive
                if loop_count % 10 == 0:
                    time_since_5m = (now - self.last_30m_run).total_seconds() if self.last_30m_run else 0
                    mins_until_next = max(0, (1800 - time_since_5m) / 60)
                    logger.info(f"📊 Chart scheduler alive - next 5m charts in {mins_until_next:.0f} min")

                # Check if 30 minutes have passed for 5m charts
                if self.last_30m_run is None or (now - self.last_30m_run).total_seconds() >= 1800:
                    logger.info("⏰ 30 minutes passed - generating 5m charts...")
                    await self.generate_5m_charts()
                    logger.info("✅ 5m charts generation complete")

                # Check if 1 hour has passed for Vista AI analysis
                if self.last_vista_run is None or (now - self.last_vista_run).total_seconds() >= 3600:
                    logger.info("⏰ 1 hour passed - running Vista AI analysis...")
                    await self.generate_vista_analysis()

                # Check if 24 hours have passed for daily charts
                if self.last_daily_run is None or (now - self.last_daily_run).total_seconds() >= 86400:
                    logger.info("⏰ 24 hours passed - generating daily charts...")
                    await self.generate_daily_charts()

                # Check prediction outcomes every 5 minutes
                if loop_count % 5 == 0:
                    await self._check_prediction_outcomes()

                # Sleep for 1 minute before checking again
                await asyncio.sleep(60)

            except asyncio.CancelledError:
                logger.info("📊 Chart scheduler task cancelled")
                raise
            except Exception as e:
                logger.error(f"Chart scheduler error: {e}", exc_info=True)
                await asyncio.sleep(60)

