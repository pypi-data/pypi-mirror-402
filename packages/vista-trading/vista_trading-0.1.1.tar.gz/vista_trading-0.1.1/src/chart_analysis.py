"""
Chart Analysis Module - Multi-modal trend detection using AI.

This module provides multiple analysis modes:
1. DEEPSEEK-VL VISION: Visual chart analysis (~$0.003/image) - Best value for pattern recognition
2. CLAUDE VISION: Premium visual analysis (expensive, most accurate)
3. TEXT MODE (DeepSeek): Numerical chart description (~$0.0003/call) - Fast screening
4. MULTI-TF SYNTHESIS: Analyze multiple timeframes for confluence (~$0.001/call)
5. PATTERN-SPECIFIC: Specialized prompts for harmonic, wyckoff, elliott patterns

The DeepSeek-VL mode provides excellent pattern recognition at ~10x cheaper than Claude.
"""

import base64
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List
from io import BytesIO
import json
import re

logger = logging.getLogger(__name__)


# ==================== PATTERN-SPECIFIC PROMPTS ====================

PATTERN_PROMPTS = {
    "harmonic": """Identify HARMONIC PATTERNS in this chart:
- GARTLEY: AB=61.8% XA, CD=78.6% XA (most reliable)
- BAT: AB=38-50% XA, D=88.6% XA
- BUTTERFLY: AB=78.6% XA, D=127-161.8% XA
- CRAB: D=161.8% XA (extreme extension)

Look for the XABCD structure. Is pattern complete or forming?
What's the Potential Reversal Zone (PRZ)?""",

    "wyckoff": """Identify WYCKOFF PHASES in this chart:
ACCUMULATION signs:
- Selling Climax (SC): High volume spike at lows
- Automatic Rally (AR): Bounce after SC
- Secondary Test (ST): Retest of lows on lower volume
- Spring: False breakdown below support (BULLISH signal)
- Sign of Strength (SOS): Break above resistance

DISTRIBUTION signs:
- Buying Climax (BC): High volume spike at highs
- Upthrust (UT): False breakout above resistance (BEARISH signal)
- Sign of Weakness (SOW): Break below support

What phase are we in? Is there a Spring or Upthrust setup?""",

    "elliott": """Count ELLIOTT WAVES in this chart:
IMPULSE WAVES (trend direction): 5 waves (1-2-3-4-5)
- Wave 1: Initial move
- Wave 2: Retracement (never 100% of Wave 1)
- Wave 3: Strongest move (never shortest)
- Wave 4: Consolidation (doesn't overlap Wave 1)
- Wave 5: Final push (often with divergence)

CORRECTIVE WAVES (counter-trend): 3 waves (A-B-C)
- Can be zigzag, flat, or triangle

Which wave are we in? What's the next expected move?""",

    "orderflow": """Analyze ORDER FLOW & VOLUME in this chart:
- Volume spikes: Where is institutional activity?
- Absorption: High volume but price doesn't move = big player absorbing
- Exhaustion: Decreasing volume at extremes = move ending
- Delta: Are buyers or sellers more aggressive?
- POC (Point of Control): Where is most volume traded?

Look for volume clusters at key levels. Is smart money accumulating or distributing?""",

    "divergence": """Identify DIVERGENCES in this chart:
REGULAR DIVERGENCE (reversal signal):
- Bullish: Price makes lower low, RSI makes higher low
- Bearish: Price makes higher high, RSI makes lower high

HIDDEN DIVERGENCE (continuation signal):
- Bullish: Price makes higher low, RSI makes lower low
- Bearish: Price makes lower high, RSI makes higher high

Is there divergence? How many touches? Is it confirmed?""",

    "breakout": """Analyze BREAKOUT/BREAKDOWN potential:
- Is price compressing? (Decreasing range = energy building)
- Triangle patterns: Ascending (bullish), Descending (bearish), Symmetric
- Rectangle/Range: Where are the clear boundaries?
- Volume: Is it contracting? (Good for breakout)
- False breakouts: Any recent failures at these levels?

Which direction is more likely? What would confirm the breakout?"""
}


# ==================== MULTI-TIMEFRAME WEIGHTS ====================

MTF_WEIGHTS = {
    "1m": 0.05,   # Noise
    "5m": 0.15,   # Short-term momentum
    "15m": 0.20,  # Intraday trend
    "30m": 0.20,  # Swing setup
    "1h": 0.25,   # Primary trend
    "4h": 0.10,   # Major trend
    "1d": 0.05,   # Context
}


class ChartAnalyzer:
    """Analyzes charts using Claude Vision or DeepSeek text analysis."""

    def __init__(self, anthropic_client, deepseek_client=None, use_vision: bool = False):
        """Initialize with clients for analysis.

        Args:
            anthropic_client: Anthropic client for Claude Vision (optional, expensive)
            deepseek_client: OpenAI-compatible client for DeepSeek (cheap, default)
            use_vision: If True, use Claude Vision. If False, use DeepSeek text (default)
        """
        self.client = anthropic_client
        self.deepseek_client = deepseek_client
        self.use_vision = use_vision and anthropic_client is not None

    def generate_chart_image(self, candles: List[Dict], symbol: str,
                              timeframe: str = "1h") -> Optional[bytes]:
        """Generate a chart image from candle data using matplotlib.

        Args:
            candles: List of candle dicts with open, high, low, close, volume
            symbol: Trading symbol for title
            timeframe: Timeframe string for title

        Returns:
            PNG image bytes or None if failed
        """
        try:
            import matplotlib
            matplotlib.use('Agg')  # Non-interactive backend
            import matplotlib.pyplot as plt
            import matplotlib.dates as mdates
            from datetime import datetime
            import numpy as np

            if len(candles) < 20:
                logger.warning("Not enough candles for chart generation")
                return None

            # Prepare data
            dates = [datetime.fromtimestamp(c.get("time", c.get("t", 0))/1000)
                     if c.get("time", c.get("t", 0)) > 1e10
                     else datetime.fromtimestamp(c.get("time", c.get("t", 0)))
                     for c in candles]
            opens = [c.get("open", c.get("o", 0)) for c in candles]
            highs = [c.get("high", c.get("h", 0)) for c in candles]
            lows = [c.get("low", c.get("l", 0)) for c in candles]
            closes = [c.get("close", c.get("c", 0)) for c in candles]
            volumes = [c.get("volume", c.get("v", 0)) for c in candles]

            # Calculate EMAs
            def calc_ema(data, period):
                ema = [sum(data[:period]) / period]
                mult = 2 / (period + 1)
                for price in data[period:]:
                    ema.append((price * mult) + (ema[-1] * (1 - mult)))
                return [None] * (period - 1) + ema

            ema9 = calc_ema(closes, 9)
            ema21 = calc_ema(closes, 21)
            ema50 = calc_ema(closes, 50) if len(closes) >= 50 else [None] * len(closes)

            # Create figure with subplots
            fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(14, 10),
                                                 gridspec_kw={'height_ratios': [3, 1, 1]})
            fig.patch.set_facecolor('#1a1a2e')

            # Plot candlesticks
            ax1.set_facecolor('#1a1a2e')
            for i, (d, o, h, l, c) in enumerate(zip(dates, opens, highs, lows, closes)):
                color = '#00ff88' if c >= o else '#ff4466'
                ax1.plot([d, d], [l, h], color=color, linewidth=1)
                ax1.plot([d, d], [o, c], color=color, linewidth=4)

            # Plot EMAs
            ax1.plot(dates, ema9, color='#ffaa00', linewidth=1.5, label='EMA 9', alpha=0.8)
            ax1.plot(dates, ema21, color='#00aaff', linewidth=1.5, label='EMA 21', alpha=0.8)
            if ema50[0] is not None:
                ax1.plot(dates, ema50, color='#ff00ff', linewidth=1.5, label='EMA 50', alpha=0.8)

            ax1.set_title(f'{symbol} {timeframe} Chart', color='white', fontsize=14)
            ax1.legend(loc='upper left', facecolor='#2a2a3e', edgecolor='none', labelcolor='white')
            ax1.tick_params(colors='white')
            ax1.grid(True, alpha=0.2)
            ax1.set_ylabel('Price', color='white')

            # Plot volume
            ax2.set_facecolor('#1a1a2e')
            colors = ['#00ff88' if c >= o else '#ff4466' for o, c in zip(opens, closes)]
            ax2.bar(dates, volumes, color=colors, alpha=0.7, width=0.02)
            ax2.set_ylabel('Volume', color='white')
            ax2.tick_params(colors='white')
            ax2.grid(True, alpha=0.2)

            # Calculate and plot RSI
            def calc_rsi(closes, period=14):
                deltas = [closes[i] - closes[i-1] for i in range(1, len(closes))]
                gains = [d if d > 0 else 0 for d in deltas]
                losses = [-d if d < 0 else 0 for d in deltas]

                avg_gain = sum(gains[:period]) / period
                avg_loss = sum(losses[:period]) / period

                rsi_values = [None] * period
                for i in range(period, len(deltas)):
                    avg_gain = (avg_gain * (period - 1) + gains[i]) / period
                    avg_loss = (avg_loss * (period - 1) + losses[i]) / period
                    rs = avg_gain / avg_loss if avg_loss > 0 else 100
                    rsi_values.append(100 - (100 / (1 + rs)))
                return [None] + rsi_values

            rsi = calc_rsi(closes)
            ax3.set_facecolor('#1a1a2e')
            ax3.plot(dates, rsi, color='#ffaa00', linewidth=1.5)
            ax3.axhline(y=70, color='#ff4466', linestyle='--', alpha=0.5)
            ax3.axhline(y=30, color='#00ff88', linestyle='--', alpha=0.5)
            ax3.axhline(y=50, color='white', linestyle='--', alpha=0.3)
            ax3.fill_between(dates, 70, 100, alpha=0.1, color='#ff4466')
            ax3.fill_between(dates, 0, 30, alpha=0.1, color='#00ff88')
            ax3.set_ylabel('RSI', color='white')
            ax3.set_ylim(0, 100)
            ax3.tick_params(colors='white')
            ax3.grid(True, alpha=0.2)

            # Format x-axis
            ax3.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d %H:%M'))
            plt.xticks(rotation=45)

            plt.tight_layout()

            # Save to bytes
            buf = BytesIO()
            plt.savefig(buf, format='png', facecolor='#1a1a2e', edgecolor='none', dpi=100)
            buf.seek(0)
            plt.close(fig)

            return buf.read()

        except ImportError as e:
            logger.error(f"matplotlib not installed: {e}")
            return None
        except Exception as e:
            logger.error(f"Failed to generate chart: {e}")
            return None
    
    def analyze_chart_with_vision(self, image_bytes: bytes, symbol: str, 
                                   timeframe: str = "1h") -> Dict[str, Any]:
        """Use Claude Vision to analyze a chart image.
        
        Args:
            image_bytes: PNG/JPEG image data
            symbol: The trading symbol
            timeframe: Chart timeframe
            
        Returns:
            Dict with trend analysis, patterns, and signals
        """
        try:
            # Encode image to base64
            image_b64 = base64.standard_b64encode(image_bytes).decode("utf-8")

            prompt = f"""You are an expert technical analyst. Analyze this {symbol} {timeframe} chart.

=== SYSTEMATIC ANALYSIS FRAMEWORK ===

STEP 1: PRICE STRUCTURE
- What is the dominant trend? (HH/HL = uptrend, LH/LL = downtrend)
- Is price making new highs/lows or consolidating?
- Where is price relative to the EMAs? (Above all = bullish, Below all = bearish)

STEP 2: MOMENTUM CHECK
- RSI reading: Is it diverging from price? (Lower RSI with higher price = bearish divergence)
- Is momentum accelerating or decelerating?
- Are there any momentum exhaustion signals?

STEP 3: PATTERN RECOGNITION
- Continuation patterns: flags, pennants, triangles
- Reversal patterns: H&S, double tops/bottoms, wedges
- Is the pattern confirmed or still forming?

STEP 4: KEY LEVELS
- Identify the nearest strong support (recent swing lows, volume clusters)
- Identify the nearest strong resistance (recent swing highs, round numbers)
- How far is price from these levels?

STEP 5: VOLUME ANALYSIS
- Is volume increasing on moves in the trend direction? (Confirms trend)
- Is volume decreasing? (Weakening conviction)
- Any volume spikes indicating institutional activity?

=== YOUR REASONING (Explain your thought process) ===
Think through each step above and explain WHY you see what you see.

=== OUTPUT (JSON) ===
{{
    "trend_direction": "bullish" | "bearish" | "neutral",
    "trend_strength": 1-10,
    "key_support": <price>,
    "key_resistance": <price>,
    "pattern": "pattern name" | "none",
    "pattern_stage": "forming" | "confirmed" | "none",
    "momentum_signal": "strong_buy" | "buy" | "neutral" | "sell" | "strong_sell",
    "volume_confirms": true | false,
    "divergence_detected": "bullish" | "bearish" | "none",
    "confidence": 0.0-1.0,
    "reasoning": "2-3 sentence explanation of the key factors driving your analysis",
    "trade_idea": "What would be the logical trade setup based on this chart?"
}}

Be specific about price levels you observe. If unsure, say so and lower confidence."""

            # Use Sonnet for reliable JSON output (Haiku struggles with structured output)
            model = "claude-sonnet-4-20250514"

            response = self.client.messages.create(
                model=model,
                max_tokens=1024,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": "image/png",
                                    "data": image_b64
                                }
                            },
                            {
                                "type": "text",
                                "text": prompt
                            }
                        ]
                    }
                ]
            )
            
            # Parse response
            import json
            result_text = response.content[0].text
            # Clean up potential markdown
            if "```json" in result_text:
                result_text = result_text.split("```json")[1].split("```")[0]
            elif "```" in result_text:
                result_text = result_text.split("```")[1].split("```")[0]
            
            return json.loads(result_text.strip())
            
        except Exception as e:
            logger.error(f"Vision analysis failed: {e}")
            return {
                "trend_direction": "neutral",
                "trend_strength": 5,
                "confidence": 0.0,
                "error": str(e)
            }

    def analyze_trend(self, candles: List[Dict], symbol: str,
                      timeframe: str = "1h") -> Dict[str, Any]:
        """Full trend analysis - uses DeepSeek text (cheap) or Claude Vision (expensive).

        Args:
            candles: List of candle data
            symbol: Trading symbol
            timeframe: Chart timeframe

        Returns:
            Dict with visual trend analysis
        """
        # Use DeepSeek text analysis by default (cost-effective)
        if not self.use_vision or self.deepseek_client:
            return self.analyze_chart_with_deepseek(candles, symbol, timeframe)

        # Expensive path: Claude Vision (only if explicitly enabled)
        image_bytes = self.generate_chart_image(candles, symbol, timeframe)

        if image_bytes is None:
            logger.warning("Could not generate chart, using indicator-only analysis")
            return self._fallback_trend_analysis(candles)

        # Analyze with Claude Vision
        result = self.analyze_chart_with_vision(image_bytes, symbol, timeframe)
        result["source"] = "vision"
        result["chart_generated"] = True
        return result

    def analyze_chart_with_deepseek(self, candles: List[Dict], symbol: str,
                                     timeframe: str = "1h") -> Dict[str, Any]:
        """COST-EFFECTIVE: Analyze chart data with DeepSeek using text description.

        Instead of generating an image, we describe the chart numerically.
        This provides 90% of the insight at ~1% of the cost (~$0.0003/analysis).

        Args:
            candles: List of candle data
            symbol: Trading symbol
            timeframe: Chart timeframe

        Returns:
            Dict with trend analysis, patterns, and signals
        """
        if not self.deepseek_client:
            logger.warning("DeepSeek client not available, using fallback")
            return self._fallback_trend_analysis(candles)

        try:
            # Build comprehensive chart description
            chart_description = self._build_chart_description(candles, symbol, timeframe)

            prompt = f"""You are an expert technical analyst. Analyze this {symbol} {timeframe} chart data.

{chart_description}

=== ANALYSIS FRAMEWORK ===
1. TREND: Is price making HH/HL (uptrend) or LH/LL (downtrend)?
2. MOMENTUM: Is RSI diverging? Is momentum accelerating or exhausting?
3. PATTERNS: Any continuation (flags, triangles) or reversal (H&S, double top/bottom)?
4. KEY LEVELS: Nearest strong support and resistance from the swing points
5. VOLUME: Does volume confirm the move or show exhaustion?

=== OUTPUT (JSON ONLY) ===
{{
    "trend_direction": "bullish" | "bearish" | "neutral",
    "trend_strength": 1-10,
    "key_support": <price>,
    "key_resistance": <price>,
    "pattern": "pattern name" | "none",
    "pattern_stage": "forming" | "confirmed" | "none",
    "momentum_signal": "strong_buy" | "buy" | "neutral" | "sell" | "strong_sell",
    "volume_confirms": true | false,
    "divergence_detected": "bullish" | "bearish" | "none",
    "confidence": 0.0-1.0,
    "reasoning": "2-3 sentence explanation",
    "trade_idea": "What would be the logical trade setup?"
}}"""

            response = self.deepseek_client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {"role": "system", "content": "You are a technical analyst. Analyze chart data precisely. Respond with JSON only."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=500
            )

            result_text = response.choices[0].message.content

            # Parse JSON response
            import json
            import re

            # Extract JSON from response
            json_match = re.search(r'\{[\s\S]*\}', result_text)
            if json_match:
                result = json.loads(json_match.group())
                result["source"] = "deepseek_text"
                result["cost_estimate"] = "$0.0003"
                return result
            else:
                logger.warning("Could not parse DeepSeek response as JSON")
                return self._fallback_trend_analysis(candles)

        except Exception as e:
            logger.error(f"DeepSeek chart analysis failed: {e}")
            return self._fallback_trend_analysis(candles)

    def _build_chart_description(self, candles: List[Dict], symbol: str, timeframe: str) -> str:
        """Build a comprehensive text description of the chart for DeepSeek."""
        if len(candles) < 20:
            return "Insufficient data"

        # Extract OHLCV data
        opens = [c.get("open", c.get("o", 0)) for c in candles]
        highs = [c.get("high", c.get("h", 0)) for c in candles]
        lows = [c.get("low", c.get("l", 0)) for c in candles]
        closes = [c.get("close", c.get("c", 0)) for c in candles]
        volumes = [c.get("volume", c.get("v", 0)) for c in candles]

        current_price = closes[-1]

        # Calculate EMAs
        def calc_ema(data, period):
            if len(data) < period:
                return None
            ema = sum(data[:period]) / period
            mult = 2 / (period + 1)
            for price in data[period:]:
                ema = (price * mult) + (ema * (1 - mult))
            return ema

        ema9 = calc_ema(closes, 9)
        ema21 = calc_ema(closes, 21)
        ema50 = calc_ema(closes, 50) if len(closes) >= 50 else None

        # Calculate RSI
        def calc_rsi(closes, period=14):
            if len(closes) < period + 1:
                return 50
            deltas = [closes[i] - closes[i-1] for i in range(1, len(closes))]
            gains = [d if d > 0 else 0 for d in deltas]
            losses = [-d if d < 0 else 0 for d in deltas]
            avg_gain = sum(gains[-period:]) / period
            avg_loss = sum(losses[-period:]) / period
            if avg_loss == 0:
                return 100
            rs = avg_gain / avg_loss
            return 100 - (100 / (1 + rs))

        rsi = calc_rsi(closes)

        # Find swing highs/lows (last 50 candles)
        recent_highs = highs[-50:]
        recent_lows = lows[-50:]
        swing_high = max(recent_highs)
        swing_low = min(recent_lows)

        # Recent price action (last 10 candles)
        recent_closes = closes[-10:]
        price_change_10 = ((recent_closes[-1] - recent_closes[0]) / recent_closes[0]) * 100

        # Volume analysis
        avg_vol_20 = sum(volumes[-20:]) / 20 if len(volumes) >= 20 else sum(volumes) / len(volumes)
        recent_vol = sum(volumes[-5:]) / 5
        vol_ratio = recent_vol / avg_vol_20 if avg_vol_20 > 0 else 1

        # Higher highs / Lower lows detection
        hh_count = 0
        ll_count = 0
        for i in range(-10, -1):
            if highs[i] > highs[i-1]:
                hh_count += 1
            if lows[i] < lows[i-1]:
                ll_count += 1

        # Bollinger Bands
        sma20 = sum(closes[-20:]) / 20
        variance = sum((c - sma20) ** 2 for c in closes[-20:]) / 20
        std_dev = variance ** 0.5
        bb_upper = sma20 + (2 * std_dev)
        bb_lower = sma20 - (2 * std_dev)
        bb_position = (current_price - bb_lower) / (bb_upper - bb_lower) if (bb_upper - bb_lower) > 0 else 0.5

        # Pre-calculate conditional values to avoid f-string issues
        ema9_rel = 'above' if current_price > ema9 else 'below'
        ema21_rel = 'above' if current_price > ema21 else 'below'
        ema50_str = f"${ema50:,.2f}" if ema50 else 'N/A'
        ema50_rel = f"(price {'above' if current_price > ema50 else 'below'})" if ema50 else ''

        if ema9 and ema21 and ema50 and ema9 > ema21 > ema50:
            ema_alignment = '9>21>50 BULLISH'
        elif ema9 and ema21 and ema50 and ema9 < ema21 < ema50:
            ema_alignment = '9<21<50 BEARISH'
        else:
            ema_alignment = 'MIXED'

        rsi_status = 'OVERBOUGHT' if rsi > 70 else 'OVERSOLD' if rsi < 30 else 'NEUTRAL'
        structure = 'UPTREND (HH/HL)' if hh_count > 6 else 'DOWNTREND (LH/LL)' if ll_count > 6 else 'RANGING'
        bb_status = 'near upper' if bb_position > 0.8 else 'near lower' if bb_position < 0.2 else 'middle'
        vol_status = 'HIGH' if vol_ratio > 1.5 else 'LOW' if vol_ratio < 0.7 else 'NORMAL'

        dist_high = ((swing_high - current_price) / current_price) * 100
        dist_low = ((current_price - swing_low) / current_price) * 100

        description = f"""=== {symbol} {timeframe} CHART DATA ===

PRICE:
- Current: ${current_price:,.2f}
- 10-candle change: {price_change_10:+.2f}%
- Range high (50): ${swing_high:,.2f}
- Range low (50): ${swing_low:,.2f}
- Distance from high: {dist_high:.2f}%
- Distance from low: {dist_low:.2f}%

MOVING AVERAGES:
- EMA 9: ${ema9:,.2f} (price {ema9_rel})
- EMA 21: ${ema21:,.2f} (price {ema21_rel})
- EMA 50: {ema50_str} {ema50_rel}
- EMA alignment: {ema_alignment}

MOMENTUM:
- RSI(14): {rsi:.1f} ({rsi_status})
- Higher Highs (last 10): {hh_count}/9
- Lower Lows (last 10): {ll_count}/9
- Structure: {structure}

BOLLINGER BANDS:
- Upper: ${bb_upper:,.2f}
- Middle (SMA20): ${sma20:,.2f}
- Lower: ${bb_lower:,.2f}
- Position: {bb_position:.0%} ({bb_status})

VOLUME:
- Recent vs Average: {vol_ratio:.2f}x ({vol_status})

LAST 5 CANDLES (newest first):
"""
        # Add last 5 candles
        for i in range(-1, -6, -1):
            o, h, l, c, v = opens[i], highs[i], lows[i], closes[i], volumes[i]
            candle_type = "BULLISH" if c > o else "BEARISH" if c < o else "DOJI"
            body_pct = abs(c - o) / o * 100 if o > 0 else 0
            description += f"  {-i}. {candle_type} O:{o:.2f} H:{h:.2f} L:{l:.2f} C:{c:.2f} (body: {body_pct:.2f}%)\n"

        return description

    # ==================== DEEPSEEK-VL VISION ANALYSIS ====================

    def analyze_chart_with_deepseek_vision(self, image_bytes: bytes, symbol: str,
                                            timeframe: str = "1h") -> Dict[str, Any]:
        """Use DeepSeek-VL (Vision-Language) for visual chart analysis.

        ~10x cheaper than Claude Vision (~$0.003/image vs $0.03/image).
        Excellent for pattern recognition, trend identification, and S/R levels.

        Args:
            image_bytes: PNG/JPEG image data
            symbol: Trading symbol
            timeframe: Chart timeframe

        Returns:
            Dict with trend analysis, patterns, and signals
        """
        if not self.deepseek_client:
            logger.warning("DeepSeek client not available for vision analysis")
            return self._fallback_trend_analysis([])

        try:
            image_b64 = base64.b64encode(image_bytes).decode("utf-8")

            prompt = f"""Analyze this {symbol} {timeframe} chart as an expert technical analyst.

=== SYSTEMATIC ANALYSIS ===
1. TREND: Higher highs/lows (uptrend) or lower highs/lows (downtrend)?
2. STRUCTURE: Key support/resistance levels visible
3. PATTERNS: Any chart patterns (triangles, H&S, double top/bottom, flags)?
4. MOMENTUM: RSI position, any divergences?
5. VOLUME: Confirming or diverging from price?

=== OUTPUT JSON ===
{{"trend_direction": "bullish/bearish/neutral", "trend_strength": 1-10,
"key_support": <price>, "key_resistance": <price>,
"pattern": "pattern name or none", "pattern_stage": "forming/confirmed/none",
"momentum_signal": "strong_buy/buy/neutral/sell/strong_sell",
"divergence_detected": "bullish/bearish/none", "confidence": 0.0-1.0,
"reasoning": "2-3 sentences", "trade_idea": "suggested setup"}}"""

            response = self.deepseek_client.chat.completions.create(
                model="deepseek-chat",  # DeepSeek-VL uses same endpoint
                messages=[{
                    "role": "user",
                    "content": [
                        {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{image_b64}"}},
                        {"type": "text", "text": prompt}
                    ]
                }],
                max_tokens=600
            )

            result_text = response.choices[0].message.content
            json_match = re.search(r'\{[\s\S]*\}', result_text)
            if json_match:
                result = json.loads(json_match.group())
                result["source"] = "deepseek_vision"
                result["cost_estimate"] = "$0.003"
                return result

            return self._fallback_trend_analysis([])

        except Exception as e:
            logger.error(f"DeepSeek Vision analysis failed: {e}")
            return self._fallback_trend_analysis([])

    def analyze_with_vision(self, candles: List[Dict], symbol: str,
                            timeframe: str = "1h", use_deepseek: bool = True) -> Dict[str, Any]:
        """Visual chart analysis - generates image and analyzes with AI.

        Args:
            candles: Candle data for chart generation
            symbol: Trading symbol
            timeframe: Chart timeframe
            use_deepseek: If True, use DeepSeek-VL (cheap). If False, use Claude (expensive).

        Returns:
            Dict with visual analysis results
        """
        image_bytes = self.generate_chart_image(candles, symbol, timeframe)
        if image_bytes is None:
            logger.warning("Could not generate chart image")
            return self._fallback_trend_analysis(candles)

        if use_deepseek and self.deepseek_client:
            return self.analyze_chart_with_deepseek_vision(image_bytes, symbol, timeframe)
        elif self.client:
            return self.analyze_chart_with_vision(image_bytes, symbol, timeframe)
        else:
            return self._fallback_trend_analysis(candles)

    # ==================== PATTERN-SPECIFIC ANALYSIS ====================

    def analyze_pattern(self, candles: List[Dict], symbol: str,
                        pattern_type: str, timeframe: str = "1h") -> Dict[str, Any]:
        """Analyze chart for a specific pattern type using specialized prompts.

        Args:
            candles: Candle data
            symbol: Trading symbol
            pattern_type: One of: harmonic, wyckoff, elliott, orderflow, divergence, breakout
            timeframe: Chart timeframe

        Returns:
            Dict with pattern-specific analysis
        """
        if pattern_type not in PATTERN_PROMPTS:
            logger.warning(f"Unknown pattern type: {pattern_type}")
            return {"error": f"Unknown pattern: {pattern_type}"}

        if not self.deepseek_client:
            return {"error": "DeepSeek client required for pattern analysis"}

        try:
            chart_desc = self._build_chart_description(candles, symbol, timeframe)
            pattern_prompt = PATTERN_PROMPTS[pattern_type]

            prompt = f"""{chart_desc}

=== {pattern_type.upper()} PATTERN ANALYSIS ===
{pattern_prompt}

=== OUTPUT JSON ===
{{"pattern_found": true/false, "pattern_name": "specific pattern",
"confidence": 0.0-1.0, "stage": "forming/confirmed/completed",
"entry_zone": <price or null>, "target": <price or null>,
"invalidation": <price or null>, "reasoning": "explanation"}}"""

            response = self.deepseek_client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {"role": "system", "content": f"You are a {pattern_type} pattern specialist. JSON only."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=400
            )

            result_text = response.choices[0].message.content
            json_match = re.search(r'\{[\s\S]*\}', result_text)
            if json_match:
                result = json.loads(json_match.group())
                result["pattern_type"] = pattern_type
                result["source"] = "pattern_specific"
                result["cost_estimate"] = "$0.0005"
                return result

            return {"pattern_found": False, "error": "parse_failed"}

        except Exception as e:
            logger.error(f"Pattern analysis failed: {e}")
            return {"pattern_found": False, "error": str(e)}

    def scan_all_patterns(self, candles: List[Dict], symbol: str,
                          timeframe: str = "1h") -> Dict[str, Any]:
        """Scan for all pattern types and return findings.

        Args:
            candles: Candle data
            symbol: Trading symbol
            timeframe: Chart timeframe

        Returns:
            Dict with all pattern scan results
        """
        results = {}
        for pattern_type in PATTERN_PROMPTS.keys():
            results[pattern_type] = self.analyze_pattern(candles, symbol, pattern_type, timeframe)

        # Find highest confidence patterns
        found_patterns = [
            (ptype, data) for ptype, data in results.items()
            if data.get("pattern_found") and data.get("confidence", 0) > 0.6
        ]
        found_patterns.sort(key=lambda x: x[1].get("confidence", 0), reverse=True)

        return {
            "all_scans": results,
            "high_confidence_patterns": found_patterns[:3],
            "total_cost_estimate": f"${len(PATTERN_PROMPTS) * 0.0005:.4f}"
        }

    # ==================== MULTI-TIMEFRAME SYNTHESIS ====================

    def analyze_multi_timeframe(self, candles_by_tf: Dict[str, List[Dict]],
                                 symbol: str) -> Dict[str, Any]:
        """Analyze multiple timeframes and synthesize confluence signals.

        Args:
            candles_by_tf: Dict mapping timeframe to candle list
                           e.g., {"5m": [...], "1h": [...], "4h": [...]}
            symbol: Trading symbol

        Returns:
            Dict with individual TF analysis and synthesized signal
        """
        if not self.deepseek_client:
            return {"error": "DeepSeek client required"}

        try:
            # Analyze each timeframe
            tf_analyses = {}
            for tf, candles in candles_by_tf.items():
                if candles and len(candles) >= 20:
                    tf_analyses[tf] = self.analyze_chart_with_deepseek(candles, symbol, tf)

            if not tf_analyses:
                return {"error": "No valid timeframe data"}

            # Build synthesis prompt
            tf_summary = "\n".join([
                f"{tf}: {data.get('trend_direction', 'unknown')} "
                f"(strength: {data.get('trend_strength', 5)}/10, "
                f"conf: {data.get('confidence', 0):.0%})"
                for tf, data in tf_analyses.items()
            ])

            synthesis_prompt = f"""Multi-timeframe analysis for {symbol}:

{tf_summary}

=== SYNTHESIS RULES ===
- Higher timeframes (4h, 1h) define the trend
- Lower timeframes (15m, 5m) provide entry timing
- Confluence = multiple TFs agree = higher confidence
- Conflict = TFs disagree = wait for clarity

=== OUTPUT JSON ===
{{"overall_bias": "bullish/bearish/neutral",
"confluence_score": 0-100, "aligned_timeframes": ["list"],
"conflicting_timeframes": ["list"],
"recommended_action": "long/short/wait",
"entry_timeframe": "best TF for entry",
"reasoning": "synthesis explanation"}}"""

            response = self.deepseek_client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {"role": "system", "content": "Synthesize multi-TF analysis. Be decisive. JSON only."},
                    {"role": "user", "content": synthesis_prompt}
                ],
                max_tokens=300
            )

            result_text = response.choices[0].message.content
            json_match = re.search(r'\{[\s\S]*\}', result_text)
            if json_match:
                synthesis = json.loads(json_match.group())
                return {
                    "individual_analyses": tf_analyses,
                    "synthesis": synthesis,
                    "source": "multi_tf_synthesis",
                    "cost_estimate": f"${(len(tf_analyses) + 1) * 0.0003:.4f}"
                }

            return {"individual_analyses": tf_analyses, "synthesis": {"error": "parse_failed"}}

        except Exception as e:
            logger.error(f"Multi-TF synthesis failed: {e}")
            return {"error": str(e)}

    def get_confluence_score(self, candles_by_tf: Dict[str, List[Dict]],
                              symbol: str) -> Dict[str, Any]:
        """Quick confluence check across timeframes (cheaper than full synthesis).

        Returns a simple score without full AI analysis per timeframe.
        """
        if not candles_by_tf:
            return {"score": 0, "bias": "neutral"}

        bullish_count = 0
        bearish_count = 0
        total_weight = 0

        for tf, candles in candles_by_tf.items():
            if not candles or len(candles) < 21:
                continue

            weight = MTF_WEIGHTS.get(tf, 0.1)
            closes = [c.get("close", c.get("c", 0)) for c in candles]
            sma21 = sum(closes[-21:]) / 21
            current = closes[-1]

            if current > sma21 * 1.005:  # 0.5% above
                bullish_count += weight
            elif current < sma21 * 0.995:  # 0.5% below
                bearish_count += weight

            total_weight += weight

        if total_weight == 0:
            return {"score": 0, "bias": "neutral"}

        bullish_pct = bullish_count / total_weight
        bearish_pct = bearish_count / total_weight

        if bullish_pct > 0.6:
            bias = "bullish"
            score = int(bullish_pct * 100)
        elif bearish_pct > 0.6:
            bias = "bearish"
            score = int(bearish_pct * 100)
        else:
            bias = "neutral"
            score = 50

        return {
            "score": score,
            "bias": bias,
            "bullish_weight": round(bullish_pct, 2),
            "bearish_weight": round(bearish_pct, 2),
            "timeframes_analyzed": list(candles_by_tf.keys())
        }

    def _fallback_trend_analysis(self, candles: List[Dict]) -> Dict[str, Any]:
        """Fallback analysis using just indicators (no vision)."""
        if len(candles) < 21:
            return {"trend_direction": "neutral", "trend_strength": 5, "confidence": 0.3, "source": "fallback"}

        closes = [c.get("close", c.get("c", 0)) for c in candles]

        # Simple trend: compare current price to 21-period SMA
        sma21 = sum(closes[-21:]) / 21
        current = closes[-1]

        pct_diff = ((current - sma21) / sma21) * 100

        if pct_diff > 2:
            direction = "bullish"
            strength = min(10, int(5 + pct_diff))
        elif pct_diff < -2:
            direction = "bearish"
            strength = min(10, int(5 + abs(pct_diff)))
        else:
            direction = "neutral"
            strength = 5

        return {
            "trend_direction": direction,
            "trend_strength": strength,
            "confidence": 0.5,
            "source": "fallback",
            "chart_generated": False
        }


class ThinkingTracker:
    """Tracks Claude's analysis patterns to identify biases and improve accuracy."""

    def __init__(self):
        self.analysis_history: List[Dict] = []
        self.max_history = 100

    def record_analysis(self, symbol: str, analysis: Dict,
                        actual_outcome: str = None) -> None:
        """Record an analysis for pattern tracking."""
        record = {
            "timestamp": datetime.now().isoformat(),
            "symbol": symbol,
            "trend_called": analysis.get("trend_direction"),
            "confidence": analysis.get("confidence", 0),
            "reasoning": analysis.get("reasoning", ""),
            "pattern": analysis.get("pattern", "none"),
            "divergence": analysis.get("divergence_detected", "none"),
            "actual_outcome": actual_outcome  # Fill in later
        }
        self.analysis_history.append(record)

        # Trim to max history
        if len(self.analysis_history) > self.max_history:
            self.analysis_history = self.analysis_history[-self.max_history:]

    def update_outcome(self, symbol: str, outcome: str) -> None:
        """Update the most recent analysis for a symbol with actual outcome."""
        for record in reversed(self.analysis_history):
            if record["symbol"] == symbol and record["actual_outcome"] is None:
                record["actual_outcome"] = outcome
                break

    def get_accuracy_stats(self) -> Dict[str, Any]:
        """Calculate accuracy stats from recorded analyses."""
        if not self.analysis_history:
            return {"total": 0, "accuracy": 0, "bias": "none"}

        completed = [r for r in self.analysis_history if r["actual_outcome"]]
        if not completed:
            return {"total": len(self.analysis_history), "accuracy": 0, "bias": "unknown"}

        correct = sum(1 for r in completed if r["trend_called"] == r["actual_outcome"])

        # Check for biases
        bullish_calls = sum(1 for r in self.analysis_history if r["trend_called"] == "bullish")
        bearish_calls = sum(1 for r in self.analysis_history if r["trend_called"] == "bearish")
        total = len(self.analysis_history)

        bias = "none"
        if bullish_calls / total > 0.7:
            bias = "bullish_bias"
        elif bearish_calls / total > 0.7:
            bias = "bearish_bias"

        return {
            "total": len(self.analysis_history),
            "completed": len(completed),
            "accuracy": correct / len(completed) if completed else 0,
            "bullish_calls_pct": bullish_calls / total,
            "bearish_calls_pct": bearish_calls / total,
            "detected_bias": bias
        }

    def get_reasoning_patterns(self) -> Dict[str, int]:
        """Analyze common phrases in Claude's reasoning."""
        patterns = {
            "momentum": 0,
            "support": 0,
            "resistance": 0,
            "divergence": 0,
            "consolidation": 0,
            "breakout": 0,
            "reversal": 0,
            "continuation": 0,
            "volume": 0,
            "EMA": 0
        }

        for record in self.analysis_history:
            reasoning = record.get("reasoning", "").lower()
            for pattern in patterns:
                if pattern.lower() in reasoning:
                    patterns[pattern] += 1

        return patterns

    def get_meta_analysis(self) -> str:
        """Generate a meta-analysis of Claude's thinking patterns."""
        stats = self.get_accuracy_stats()
        patterns = self.get_reasoning_patterns()

        top_patterns = sorted(patterns.items(), key=lambda x: x[1], reverse=True)[:5]

        report = f"""
=== CLAUDE THINKING META-ANALYSIS ===
Total Analyses: {stats['total']}
Accuracy: {stats.get('accuracy', 0):.0%}
Detected Bias: {stats.get('detected_bias', 'unknown')}

Top Reasoning Themes:
"""
        for pattern, count in top_patterns:
            report += f"  - {pattern}: {count} mentions\n"

        if stats.get("detected_bias") == "bullish_bias":
            report += "\n⚠️ WARNING: Claude shows bullish bias - be cautious on long calls"
        elif stats.get("detected_bias") == "bearish_bias":
            report += "\n⚠️ WARNING: Claude shows bearish bias - be cautious on short calls"

        return report

