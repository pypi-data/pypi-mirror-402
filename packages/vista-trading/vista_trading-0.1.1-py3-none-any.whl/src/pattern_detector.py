"""
Advanced Chart Pattern Detection for Discord Alerts

Detects high-probability patterns used by institutional traders:
1. Trend Continuation (flags, pennants, triangles)
2. Reversal Patterns (double top/bottom, H&S, wedges)
3. Liquidity/Smart Money Patterns (sweeps, FVGs, order blocks)
4. Volume-Confirmed Patterns

Each pattern is scored based on:
- Pattern strength
- Trend alignment
- Volume confirmation
- Higher timeframe support
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class PatternType(Enum):
    """Pattern categories."""
    CONTINUATION_BULL = "continuation_bull"
    CONTINUATION_BEAR = "continuation_bear"
    REVERSAL_BULL = "reversal_bull"
    REVERSAL_BEAR = "reversal_bear"
    BREAKOUT = "breakout"
    LIQUIDITY = "liquidity"


@dataclass
class Pattern:
    """Detected pattern with scoring."""
    name: str
    type: PatternType
    direction: str  # "bullish" or "bearish"
    strength: float  # 0-100
    confidence: float  # 0-1
    entry_zone: float
    stop_loss: float
    target: float
    timeframe: str
    volume_confirmed: bool = False
    trend_aligned: bool = False
    htf_support: bool = False  # Higher timeframe support
    signals: List[str] = field(default_factory=list)

    @property
    def score(self) -> int:
        """Calculate total pattern score (0-100)."""
        score = self.strength * 0.4  # Base pattern strength
        score += self.confidence * 30  # Confidence
        if self.volume_confirmed:
            score += 15
        if self.trend_aligned:
            score += 10
        if self.htf_support:
            score += 5
        return min(100, int(score))


class PatternDetector:
    """Advanced pattern detection engine."""

    def __init__(self):
        self.min_pattern_score = 60  # Minimum score to alert

    def detect_all_patterns(
        self,
        candles_5m: List[Dict],
        candles_15m: List[Dict],
        candles_1h: List[Dict],
        candles_4h: List[Dict] = None,
        volume_profile: Dict = None
    ) -> List[Pattern]:
        """Detect all patterns across timeframes.

        Args:
            candles_5m: 5-minute candles (200+)
            candles_15m: 15-minute candles (100+)
            candles_1h: 1-hour candles (100+)
            candles_4h: 4-hour candles (optional, for HTF context)
            volume_profile: Volume profile data

        Returns:
            List of Pattern objects sorted by score
        """
        patterns = []

        # Detect patterns on each timeframe
        for tf, candles in [("5m", candles_5m), ("15m", candles_15m), ("1h", candles_1h)]:
            if not candles or len(candles) < 50:
                continue

            # Get HTF trend for alignment check
            htf_trend = self._get_htf_trend(candles_1h if tf == "5m" else candles_4h)

            # 1. Trend Continuation Patterns
            patterns.extend(self._detect_flags(candles, tf, htf_trend))
            patterns.extend(self._detect_triangles(candles, tf, htf_trend))
            patterns.extend(self._detect_channels(candles, tf, htf_trend))

            # 2. Reversal Patterns
            patterns.extend(self._detect_double_patterns(candles, tf, htf_trend))
            patterns.extend(self._detect_head_shoulders(candles, tf, htf_trend))
            patterns.extend(self._detect_wedges(candles, tf, htf_trend))

            # 3. Candlestick Reversal Patterns
            patterns.extend(self._detect_engulfing(candles, tf, htf_trend))
            patterns.extend(self._detect_star_patterns(candles, tf, htf_trend))
            patterns.extend(self._detect_doji_patterns(candles, tf, htf_trend))
            patterns.extend(self._detect_hammer_patterns(candles, tf, htf_trend))
            patterns.extend(self._detect_three_candle_formations(candles, tf, htf_trend))
            patterns.extend(self._detect_piercing_darkcloud(candles, tf, htf_trend))
            patterns.extend(self._detect_harami(candles, tf, htf_trend))
            patterns.extend(self._detect_tweezer(candles, tf, htf_trend))

            # 4. Liquidity/Smart Money Patterns
            patterns.extend(self._detect_liquidity_sweep(candles, tf, htf_trend))
            patterns.extend(self._detect_fair_value_gap(candles, tf, htf_trend))
            patterns.extend(self._detect_order_blocks(candles, tf, htf_trend))

            # 5. Harmonic Patterns (Fibonacci-based)
            patterns.extend(self._detect_harmonic_patterns(candles, tf, htf_trend))

            # 6. Complex Patterns
            patterns.extend(self._detect_cup_and_handle(candles, tf, htf_trend))
            patterns.extend(self._detect_rounding_patterns(candles, tf, htf_trend))

            # 7. Volume Patterns
            if volume_profile:
                patterns.extend(self._detect_volume_patterns(candles, tf, volume_profile))

        # Filter by minimum score and sort
        patterns = [p for p in patterns if p.score >= self.min_pattern_score]
        patterns.sort(key=lambda x: x.score, reverse=True)

        return patterns

    def _get_htf_trend(self, candles: List[Dict]) -> str:
        """Get higher timeframe trend direction."""
        if not candles or len(candles) < 21:
            return "neutral"

        closes = [c["close"] for c in candles]
        ema_9 = sum(closes[-9:]) / 9
        ema_21 = sum(closes[-21:]) / 21

        if ema_9 > ema_21 * 1.002:
            return "bullish"
        elif ema_9 < ema_21 * 0.998:
            return "bearish"
        return "neutral"

    def _calc_atr(self, candles: List[Dict], period: int = 14) -> float:
        """Calculate ATR for stop loss/target calculation."""
        if len(candles) < period:
            return candles[-1]["high"] - candles[-1]["low"] if candles else 0

        tr_list = []
        for i in range(1, len(candles)):
            c = candles[i]
            prev_c = candles[i-1]
            tr = max(
                c["high"] - c["low"],
                abs(c["high"] - prev_c["close"]),
                abs(c["low"] - prev_c["close"])
            )
            tr_list.append(tr)

        return sum(tr_list[-period:]) / period

    # ========================================================================
    # TREND CONTINUATION PATTERNS
    # ========================================================================

    def _detect_flags(self, candles: List[Dict], tf: str, htf_trend: str) -> List[Pattern]:
        """Detect bull and bear flags.

        Flag = Strong impulse move → tight consolidation → continuation
        """
        patterns = []
        if len(candles) < 30:
            return patterns

        closes = [c["close"] for c in candles]
        highs = [c["high"] for c in candles]
        lows = [c["low"] for c in candles]
        volumes = [c.get("volume", 0) for c in candles]

        price = closes[-1]
        atr = self._calc_atr(candles)

        # Look for impulse move in last 20 candles
        for lookback in [10, 15, 20]:
            if len(candles) < lookback + 10:
                continue

            impulse_start = candles[-lookback - 10]
            impulse_end = candles[-lookback]

            impulse_move = (impulse_end["close"] - impulse_start["close"]) / impulse_start["close"]

            # Consolidation range after impulse
            consol_candles = candles[-lookback:]
            consol_high = max(c["high"] for c in consol_candles)
            consol_low = min(c["low"] for c in consol_candles)
            consol_range = (consol_high - consol_low) / price

            # Bull Flag: Strong up move (>3%) + tight consolidation (<2%)
            if impulse_move > 0.03 and consol_range < 0.025:
                # Check for slight downward drift (characteristic of bull flag)
                first_half_avg = sum(c["close"] for c in consol_candles[:len(consol_candles)//2]) / (len(consol_candles)//2)
                second_half_avg = sum(c["close"] for c in consol_candles[len(consol_candles)//2:]) / (len(consol_candles)//2)

                is_flag = second_half_avg <= first_half_avg  # Slight drift down or flat

                if is_flag:
                    # Volume should decrease during consolidation
                    impulse_vol = sum(volumes[-lookback-10:-lookback]) / 10 if volumes[-1] > 0 else 0
                    consol_vol = sum(volumes[-lookback:]) / lookback if volumes[-1] > 0 else 0
                    vol_confirmed = consol_vol < impulse_vol * 0.7 if impulse_vol > 0 else False

                    patterns.append(Pattern(
                        name="Bull Flag",
                        type=PatternType.CONTINUATION_BULL,
                        direction="bullish",
                        strength=min(80, impulse_move * 1000),  # Stronger impulse = stronger pattern
                        confidence=0.7 if vol_confirmed else 0.5,
                        entry_zone=consol_high,  # Entry on breakout above consolidation
                        stop_loss=consol_low - atr * 0.5,
                        target=price + (impulse_end["close"] - impulse_start["close"]),  # Measure move
                        timeframe=tf,
                        volume_confirmed=vol_confirmed,
                        trend_aligned=htf_trend == "bullish",
                        htf_support=htf_trend == "bullish",
                        signals=[
                            f"Impulse: +{impulse_move*100:.1f}%",
                            f"Consol range: {consol_range*100:.1f}%",
                            "Vol declining" if vol_confirmed else "Vol neutral"
                        ]
                    ))

            # Bear Flag: Strong down move (>3%) + tight consolidation
            elif impulse_move < -0.03 and consol_range < 0.025:
                first_half_avg = sum(c["close"] for c in consol_candles[:len(consol_candles)//2]) / (len(consol_candles)//2)
                second_half_avg = sum(c["close"] for c in consol_candles[len(consol_candles)//2:]) / (len(consol_candles)//2)

                is_flag = second_half_avg >= first_half_avg  # Slight drift up

                if is_flag:
                    impulse_vol = sum(volumes[-lookback-10:-lookback]) / 10 if volumes[-1] > 0 else 0
                    consol_vol = sum(volumes[-lookback:]) / lookback if volumes[-1] > 0 else 0
                    vol_confirmed = consol_vol < impulse_vol * 0.7 if impulse_vol > 0 else False

                    patterns.append(Pattern(
                        name="Bear Flag",
                        type=PatternType.CONTINUATION_BEAR,
                        direction="bearish",
                        strength=min(80, abs(impulse_move) * 1000),
                        confidence=0.7 if vol_confirmed else 0.5,
                        entry_zone=consol_low,
                        stop_loss=consol_high + atr * 0.5,
                        target=price + (impulse_end["close"] - impulse_start["close"]),
                        timeframe=tf,
                        volume_confirmed=vol_confirmed,
                        trend_aligned=htf_trend == "bearish",
                        htf_support=htf_trend == "bearish",
                        signals=[
                            f"Impulse: {impulse_move*100:.1f}%",
                            f"Consol range: {consol_range*100:.1f}%",
                            "Vol declining" if vol_confirmed else "Vol neutral"
                        ]
                    ))

        return patterns

    def _detect_triangles(self, candles: List[Dict], tf: str, htf_trend: str) -> List[Pattern]:
        """Detect ascending, descending, and symmetrical triangles."""
        patterns = []
        if len(candles) < 30:
            return patterns

        # Use last 30 candles for triangle detection
        recent = candles[-30:]
        highs = [c["high"] for c in recent]
        lows = [c["low"] for c in recent]
        price = recent[-1]["close"]
        atr = self._calc_atr(candles)

        # Find swing highs and lows
        swing_highs = []
        swing_lows = []

        for i in range(2, len(recent) - 2):
            if highs[i] > highs[i-1] and highs[i] > highs[i-2] and highs[i] > highs[i+1] and highs[i] > highs[i+2]:
                swing_highs.append((i, highs[i]))
            if lows[i] < lows[i-1] and lows[i] < lows[i-2] and lows[i] < lows[i+1] and lows[i] < lows[i+2]:
                swing_lows.append((i, lows[i]))

        if len(swing_highs) < 2 or len(swing_lows) < 2:
            return patterns

        # Calculate slopes
        high_slope = (swing_highs[-1][1] - swing_highs[0][1]) / (swing_highs[-1][0] - swing_highs[0][0]) if len(swing_highs) >= 2 else 0
        low_slope = (swing_lows[-1][1] - swing_lows[0][1]) / (swing_lows[-1][0] - swing_lows[0][0]) if len(swing_lows) >= 2 else 0

        # Ascending Triangle: Flat top, rising bottom
        if abs(high_slope) < price * 0.0005 and low_slope > price * 0.001:
            resistance = sum(h[1] for h in swing_highs) / len(swing_highs)
            patterns.append(Pattern(
                name="Ascending Triangle",
                type=PatternType.CONTINUATION_BULL,
                direction="bullish",
                strength=70,
                confidence=0.65,
                entry_zone=resistance,
                stop_loss=swing_lows[-1][1] - atr,
                target=resistance + (resistance - swing_lows[-1][1]),
                timeframe=tf,
                trend_aligned=htf_trend == "bullish",
                htf_support=htf_trend == "bullish",
                signals=["Flat resistance", "Rising support", "Bullish breakout likely"]
            ))

        # Descending Triangle: Rising bottom, flat top
        elif abs(low_slope) < price * 0.0005 and high_slope < -price * 0.001:
            support = sum(l[1] for l in swing_lows) / len(swing_lows)
            patterns.append(Pattern(
                name="Descending Triangle",
                type=PatternType.CONTINUATION_BEAR,
                direction="bearish",
                strength=70,
                confidence=0.65,
                entry_zone=support,
                stop_loss=swing_highs[-1][1] + atr,
                target=support - (swing_highs[-1][1] - support),
                timeframe=tf,
                trend_aligned=htf_trend == "bearish",
                htf_support=htf_trend == "bearish",
                signals=["Descending resistance", "Flat support", "Bearish breakdown likely"]
            ))

        # Symmetrical Triangle: Converging lines
        elif high_slope < -price * 0.0005 and low_slope > price * 0.0005:
            apex_price = (swing_highs[-1][1] + swing_lows[-1][1]) / 2
            direction = "bullish" if htf_trend == "bullish" else "bearish" if htf_trend == "bearish" else "neutral"
            patterns.append(Pattern(
                name="Symmetrical Triangle",
                type=PatternType.BREAKOUT,
                direction=direction,
                strength=60,
                confidence=0.55,
                entry_zone=apex_price,
                stop_loss=swing_lows[-1][1] - atr if direction == "bullish" else swing_highs[-1][1] + atr,
                target=apex_price + (swing_highs[0][1] - swing_lows[0][1]) * (1 if direction == "bullish" else -1),
                timeframe=tf,
                trend_aligned=htf_trend != "neutral",
                signals=["Converging trendlines", "Volatility compression", f"Bias: {direction}"]
            ))

        return patterns


    def _detect_channels(self, candles: List[Dict], tf: str, htf_trend: str) -> List[Pattern]:
        """Detect rising and falling channels."""
        patterns = []
        if len(candles) < 40:
            return patterns

        # Implementation for channels
        recent = candles[-40:]
        highs = [c["high"] for c in recent]
        lows = [c["low"] for c in recent]
        price = recent[-1]["close"]
        atr = self._calc_atr(candles)

        # Find swing points
        swing_highs = []
        swing_lows = []

        for i in range(2, len(recent) - 2):
            if highs[i] > max(highs[i-2:i]) and highs[i] > max(highs[i+1:i+3]):
                swing_highs.append((i, highs[i]))
            if lows[i] < min(lows[i-2:i]) and lows[i] < min(lows[i+1:i+3]):
                swing_lows.append((i, lows[i]))

        if len(swing_highs) < 2 or len(swing_lows) < 2:
            return patterns

        # Calculate parallel lines
        high_slope = (swing_highs[-1][1] - swing_highs[0][1]) / max(1, swing_highs[-1][0] - swing_highs[0][0])
        low_slope = (swing_lows[-1][1] - swing_lows[0][1]) / max(1, swing_lows[-1][0] - swing_lows[0][0])

        # Check if slopes are similar (parallel)
        if abs(high_slope - low_slope) < price * 0.0003:
            if high_slope > price * 0.0005:
                # Rising channel
                patterns.append(Pattern(
                    name="Rising Channel",
                    type=PatternType.CONTINUATION_BULL,
                    direction="bullish",
                    strength=65,
                    confidence=0.6,
                    entry_zone=swing_lows[-1][1] + (low_slope * 5),
                    stop_loss=swing_lows[-1][1] - atr,
                    target=swing_highs[-1][1] + (high_slope * 10),
                    timeframe=tf,
                    trend_aligned=htf_trend == "bullish",
                    signals=["Parallel ascending lines", "Controlled accumulation"]
                ))
            elif high_slope < -price * 0.0005:
                # Falling channel
                patterns.append(Pattern(
                    name="Falling Channel",
                    type=PatternType.CONTINUATION_BEAR,
                    direction="bearish",
                    strength=65,
                    confidence=0.6,
                    entry_zone=swing_highs[-1][1] + (high_slope * 5),
                    stop_loss=swing_highs[-1][1] + atr,
                    target=swing_lows[-1][1] + (low_slope * 10),
                    timeframe=tf,
                    trend_aligned=htf_trend == "bearish",
                    signals=["Parallel descending lines", "Controlled distribution"]
                ))

        return patterns

    # ========================================================================
    # REVERSAL PATTERNS
    # ========================================================================

    def _detect_double_patterns(self, candles: List[Dict], tf: str, htf_trend: str) -> List[Pattern]:
        """Detect double top (M) and double bottom (W) patterns."""
        patterns = []
        if len(candles) < 50:
            return patterns

        recent = candles[-50:]
        highs = [c["high"] for c in recent]
        lows = [c["low"] for c in recent]
        price = recent[-1]["close"]
        atr = self._calc_atr(candles)

        # Find two highest highs for double top
        sorted_highs = sorted(enumerate(highs), key=lambda x: x[1], reverse=True)
        if len(sorted_highs) >= 2:
            idx1, high1 = sorted_highs[0]
            idx2, high2 = sorted_highs[1]

            # Double Top: Two highs within 1% of each other, separated by at least 10 candles
            if abs(idx1 - idx2) >= 10 and abs(high1 - high2) / high1 < 0.01:
                neckline = min(lows[min(idx1, idx2):max(idx1, idx2)+1])

                # Confirm price is below the neckline or approaching it
                if price < (high1 + neckline) / 2:
                    patterns.append(Pattern(
                        name="Double Top",
                        type=PatternType.REVERSAL_BEAR,
                        direction="bearish",
                        strength=75,
                        confidence=0.7,
                        entry_zone=neckline,
                        stop_loss=high1 + atr * 0.5,
                        target=neckline - (high1 - neckline),
                        timeframe=tf,
                        trend_aligned=htf_trend != "bullish",
                        signals=["M pattern", f"Resistance ${high1:,.0f}", "Sellers exhausted buyers"]
                    ))

        # Find two lowest lows for double bottom
        sorted_lows = sorted(enumerate(lows), key=lambda x: x[1])
        if len(sorted_lows) >= 2:
            idx1, low1 = sorted_lows[0]
            idx2, low2 = sorted_lows[1]

            # Double Bottom: Two lows within 1% of each other
            if abs(idx1 - idx2) >= 10 and abs(low1 - low2) / low1 < 0.01:
                neckline = max(highs[min(idx1, idx2):max(idx1, idx2)+1])

                if price > (low1 + neckline) / 2:
                    patterns.append(Pattern(
                        name="Double Bottom",
                        type=PatternType.REVERSAL_BULL,
                        direction="bullish",
                        strength=75,
                        confidence=0.7,
                        entry_zone=neckline,
                        stop_loss=low1 - atr * 0.5,
                        target=neckline + (neckline - low1),
                        timeframe=tf,
                        trend_aligned=htf_trend != "bearish",
                        signals=["W pattern", f"Support ${low1:,.0f}", "Buyers absorbed selling"]
                    ))

        return patterns

    def _detect_head_shoulders(self, candles: List[Dict], tf: str, htf_trend: str) -> List[Pattern]:
        """Detect head & shoulders and inverse H&S patterns."""
        patterns = []
        if len(candles) < 60:
            return patterns

        recent = candles[-60:]
        highs = [c["high"] for c in recent]
        lows = [c["low"] for c in recent]
        price = recent[-1]["close"]
        atr = self._calc_atr(candles)

        # Find swing highs for H&S
        swing_highs = []
        for i in range(5, len(recent) - 5):
            if highs[i] == max(highs[i-5:i+6]):
                swing_highs.append((i, highs[i]))

        # Need 3 swing highs for H&S
        if len(swing_highs) >= 3:
            for i in range(len(swing_highs) - 2):
                left_sh = swing_highs[i]
                head = swing_highs[i + 1]
                right_sh = swing_highs[i + 2]

                # Head must be highest, shoulders roughly equal
                if head[1] > left_sh[1] and head[1] > right_sh[1]:
                    shoulder_diff = abs(left_sh[1] - right_sh[1]) / left_sh[1]
                    if shoulder_diff < 0.03:  # Shoulders within 3%
                        # Find neckline
                        left_trough = min(lows[left_sh[0]:head[0]])
                        right_trough = min(lows[head[0]:right_sh[0]+1])
                        neckline = (left_trough + right_trough) / 2

                        if price < head[1] * 0.97:  # Price has started to drop
                            patterns.append(Pattern(
                                name="Head & Shoulders",
                                type=PatternType.REVERSAL_BEAR,
                                direction="bearish",
                                strength=80,
                                confidence=0.75,
                                entry_zone=neckline,
                                stop_loss=right_sh[1] + atr,
                                target=neckline - (head[1] - neckline),
                                timeframe=tf,
                                trend_aligned=htf_trend != "bullish",
                                signals=["Classic H&S", "Institutional distribution", "High reliability"]
                            ))

        # Find swing lows for Inverse H&S
        swing_lows = []
        for i in range(5, len(recent) - 5):
            if lows[i] == min(lows[i-5:i+6]):
                swing_lows.append((i, lows[i]))

        if len(swing_lows) >= 3:
            for i in range(len(swing_lows) - 2):
                left_sh = swing_lows[i]
                head = swing_lows[i + 1]
                right_sh = swing_lows[i + 2]

                if head[1] < left_sh[1] and head[1] < right_sh[1]:
                    shoulder_diff = abs(left_sh[1] - right_sh[1]) / left_sh[1]
                    if shoulder_diff < 0.03:
                        left_peak = max(highs[left_sh[0]:head[0]])
                        right_peak = max(highs[head[0]:right_sh[0]+1])
                        neckline = (left_peak + right_peak) / 2

                        if price > head[1] * 1.03:
                            patterns.append(Pattern(
                                name="Inverse Head & Shoulders",
                                type=PatternType.REVERSAL_BULL,
                                direction="bullish",
                                strength=80,
                                confidence=0.75,
                                entry_zone=neckline,
                                stop_loss=right_sh[1] - atr,
                                target=neckline + (neckline - head[1]),
                                timeframe=tf,
                                trend_aligned=htf_trend != "bearish",
                                signals=["Inverse H&S", "Smart money accumulation", "High reliability"]
                            ))

        return patterns

    def _detect_wedges(self, candles: List[Dict], tf: str, htf_trend: str) -> List[Pattern]:
        """Detect rising and falling wedges (reversal patterns)."""
        patterns = []
        if len(candles) < 40:
            return patterns

        recent = candles[-40:]
        highs = [c["high"] for c in recent]
        lows = [c["low"] for c in recent]
        price = recent[-1]["close"]
        atr = self._calc_atr(candles)

        # Find swing points
        swing_highs = [(i, highs[i]) for i in range(2, len(recent) - 2)
                       if highs[i] > max(highs[max(0,i-2):i]) and highs[i] > max(highs[i+1:min(len(highs),i+3)])]
        swing_lows = [(i, lows[i]) for i in range(2, len(recent) - 2)
                      if lows[i] < min(lows[max(0,i-2):i]) and lows[i] < min(lows[i+1:min(len(lows),i+3)])]

        if len(swing_highs) < 2 or len(swing_lows) < 2:
            return patterns

        high_slope = (swing_highs[-1][1] - swing_highs[0][1]) / max(1, swing_highs[-1][0] - swing_highs[0][0])
        low_slope = (swing_lows[-1][1] - swing_lows[0][1]) / max(1, swing_lows[-1][0] - swing_lows[0][0])

        # Rising Wedge: Both slopes up, but lows rising faster (converging) = BEARISH
        if high_slope > 0 and low_slope > 0 and low_slope > high_slope * 0.5:
            # Lines converging
            patterns.append(Pattern(
                name="Rising Wedge",
                type=PatternType.REVERSAL_BEAR,
                direction="bearish",
                strength=70,
                confidence=0.65,
                entry_zone=swing_lows[-1][1],
                stop_loss=swing_highs[-1][1] + atr,
                target=swing_lows[0][1],
                timeframe=tf,
                trend_aligned=htf_trend != "bullish",
                signals=["Rising wedge", "Bull momentum dying", "Reversal imminent"]
            ))

        # Falling Wedge: Both slopes down, but highs falling faster = BULLISH
        elif high_slope < 0 and low_slope < 0 and high_slope < low_slope * 0.5:
            patterns.append(Pattern(
                name="Falling Wedge",
                type=PatternType.REVERSAL_BULL,
                direction="bullish",
                strength=70,
                confidence=0.65,
                entry_zone=swing_highs[-1][1],
                stop_loss=swing_lows[-1][1] - atr,
                target=swing_highs[0][1],
                timeframe=tf,
                trend_aligned=htf_trend != "bearish",
                signals=["Falling wedge", "Bear momentum dying", "Reversal imminent"]
            ))

        return patterns

    def _detect_engulfing(self, candles: List[Dict], tf: str, htf_trend: str) -> List[Pattern]:
        """Detect bullish and bearish engulfing patterns."""
        patterns = []
        if len(candles) < 10:
            return patterns

        price = candles[-1]["close"]
        atr = self._calc_atr(candles)

        for i in range(-5, -1):
            if i + 1 >= 0:
                continue
            prev = candles[i]
            curr = candles[i + 1]

            prev_body = prev["close"] - prev["open"]
            curr_body = curr["close"] - curr["open"]

            # Bullish Engulfing: Red candle followed by larger green candle that engulfs it
            if prev_body < 0 and curr_body > 0:
                if curr["open"] <= prev["close"] and curr["close"] >= prev["open"]:
                    if abs(curr_body) > abs(prev_body) * 1.5:
                        patterns.append(Pattern(
                            name="Bullish Engulfing",
                            type=PatternType.REVERSAL_BULL,
                            direction="bullish",
                            strength=65,
                            confidence=0.6,
                            entry_zone=curr["close"],
                            stop_loss=curr["low"] - atr * 0.5,
                            target=curr["close"] + atr * 2,
                            timeframe=tf,
                            trend_aligned=htf_trend != "bearish",
                            signals=["Engulfing pattern", "Demand overcomes supply", "Reversal signal"]
                        ))
                        break

            # Bearish Engulfing: Green candle followed by larger red candle
            elif prev_body > 0 and curr_body < 0:
                if curr["open"] >= prev["close"] and curr["close"] <= prev["open"]:
                    if abs(curr_body) > abs(prev_body) * 1.5:
                        patterns.append(Pattern(
                            name="Bearish Engulfing",
                            type=PatternType.REVERSAL_BEAR,
                            direction="bearish",
                            strength=65,
                            confidence=0.6,
                            entry_zone=curr["close"],
                            stop_loss=curr["high"] + atr * 0.5,
                            target=curr["close"] - atr * 2,
                            timeframe=tf,
                            trend_aligned=htf_trend != "bullish",
                            signals=["Engulfing pattern", "Supply overwhelms demand", "Reversal signal"]
                        ))
                        break

        return patterns

    def _detect_star_patterns(self, candles: List[Dict], tf: str, htf_trend: str) -> List[Pattern]:
        """Detect morning star and evening star (3-candle reversal patterns)."""
        patterns = []
        if len(candles) < 5:
            return patterns

        price = candles[-1]["close"]
        atr = self._calc_atr(candles)

        # Check last few 3-candle sequences
        for i in range(-4, -2):
            if i + 2 >= 0:
                continue
            c1, c2, c3 = candles[i], candles[i+1], candles[i+2]

            body1 = c1["close"] - c1["open"]
            body2 = c2["close"] - c2["open"]
            body3 = c3["close"] - c3["open"]

            # Morning Star: Long red, small body, long green
            if body1 < 0 and abs(body1) > atr * 0.5:  # Strong red
                if abs(body2) < atr * 0.3:  # Small/doji middle
                    if body3 > 0 and body3 > atr * 0.5:  # Strong green
                        if c3["close"] > (c1["open"] + c1["close"]) / 2:  # Closes above midpoint of first
                            patterns.append(Pattern(
                                name="Morning Star",
                                type=PatternType.REVERSAL_BULL,
                                direction="bullish",
                                strength=75,
                                confidence=0.7,
                                entry_zone=c3["close"],
                                stop_loss=min(c1["low"], c2["low"]) - atr * 0.5,
                                target=c3["close"] + atr * 3,
                                timeframe=tf,
                                trend_aligned=htf_trend != "bearish",
                                signals=["Morning star", "Trend exhaustion", "Strong reversal"]
                            ))
                            break

            # Evening Star: Long green, small body, long red
            if body1 > 0 and body1 > atr * 0.5:  # Strong green
                if abs(body2) < atr * 0.3:  # Small/doji middle
                    if body3 < 0 and abs(body3) > atr * 0.5:  # Strong red
                        if c3["close"] < (c1["open"] + c1["close"]) / 2:
                            patterns.append(Pattern(
                                name="Evening Star",
                                type=PatternType.REVERSAL_BEAR,
                                direction="bearish",
                                strength=75,
                                confidence=0.7,
                                entry_zone=c3["close"],
                                stop_loss=max(c1["high"], c2["high"]) + atr * 0.5,
                                target=c3["close"] - atr * 3,
                                timeframe=tf,
                                trend_aligned=htf_trend != "bullish",
                                signals=["Evening star", "Trend exhaustion", "Strong reversal"]
                            ))
                            break

        return patterns

    # ========================================================================
    # SMART MONEY / LIQUIDITY PATTERNS (Most Profitable for Crypto)
    # ========================================================================

    def _detect_liquidity_sweep(self, candles: List[Dict], tf: str, htf_trend: str) -> List[Pattern]:
        """Detect liquidity sweep / stop hunt patterns.

        Liquidity sweep = Price breaks a level to trigger stops, then reverses.
        This is what prop firms and smart money trade.
        """
        patterns = []
        if len(candles) < 30:
            return patterns

        recent = candles[-30:]
        price = recent[-1]["close"]
        atr = self._calc_atr(candles)

        # Find recent swing highs/lows that could have stops clustered
        swing_highs = []
        swing_lows = []

        for i in range(3, len(recent) - 3):
            if recent[i]["high"] == max(c["high"] for c in recent[i-3:i+4]):
                swing_highs.append((i, recent[i]["high"]))
            if recent[i]["low"] == min(c["low"] for c in recent[i-3:i+4]):
                swing_lows.append((i, recent[i]["low"]))

        # Check for bullish liquidity sweep (price swept lows then reversed up)
        if swing_lows:
            lowest = min(swing_lows, key=lambda x: x[1])
            # Check if recent candle wicked below then closed above
            for i in range(-5, 0):
                candle = recent[i]
                if candle["low"] < lowest[1] * 0.998:  # Wicked below level
                    if candle["close"] > lowest[1]:  # But closed above
                        wick_size = candle["close"] - candle["low"]
                        body_size = abs(candle["close"] - candle["open"])

                        if wick_size > body_size * 1.5:  # Long wick = rejection
                            patterns.append(Pattern(
                                name="Liquidity Sweep (Bullish)",
                                type=PatternType.LIQUIDITY,
                                direction="bullish",
                                strength=85,  # High reliability
                                confidence=0.8,
                                entry_zone=candle["close"],
                                stop_loss=candle["low"] - atr * 0.3,
                                target=candle["close"] + atr * 3,
                                timeframe=tf,
                                trend_aligned=htf_trend != "bearish",
                                htf_support=htf_trend == "bullish",
                                signals=[
                                    "Stop hunt below lows",
                                    "Strong rejection wick",
                                    "Smart money long entry"
                                ]
                            ))
                            break

        # Check for bearish liquidity sweep (price swept highs then reversed down)
        if swing_highs:
            highest = max(swing_highs, key=lambda x: x[1])
            for i in range(-5, 0):
                candle = recent[i]
                if candle["high"] > highest[1] * 1.002:  # Wicked above level
                    if candle["close"] < highest[1]:  # But closed below
                        wick_size = candle["high"] - candle["close"]
                        body_size = abs(candle["close"] - candle["open"])

                        if wick_size > body_size * 1.5:
                            patterns.append(Pattern(
                                name="Liquidity Sweep (Bearish)",
                                type=PatternType.LIQUIDITY,
                                direction="bearish",
                                strength=85,
                                confidence=0.8,
                                entry_zone=candle["close"],
                                stop_loss=candle["high"] + atr * 0.3,
                                target=candle["close"] - atr * 3,
                                timeframe=tf,
                                trend_aligned=htf_trend != "bullish",
                                htf_support=htf_trend == "bearish",
                                signals=[
                                    "Stop hunt above highs",
                                    "Strong rejection wick",
                                    "Smart money short entry"
                                ]
                            ))
                            break

        return patterns

    def _detect_fair_value_gap(self, candles: List[Dict], tf: str, htf_trend: str) -> List[Pattern]:
        """Detect Fair Value Gaps (FVG) - institutional imbalance zones.

        FVG = Gap between candle 1's high and candle 3's low (bullish)
              or candle 1's low and candle 3's high (bearish)

        Price tends to return to fill these gaps.
        """
        patterns = []
        if len(candles) < 20:
            return patterns

        recent = candles[-20:]
        price = recent[-1]["close"]
        atr = self._calc_atr(candles)

        # Look for unfilled FVGs
        for i in range(len(recent) - 5, len(recent) - 2):
            c1, c2, c3 = recent[i], recent[i+1], recent[i+2]

            # Bullish FVG: Gap up (c1 high < c3 low)
            if c3["low"] > c1["high"]:
                gap_size = c3["low"] - c1["high"]
                if gap_size > atr * 0.3:  # Significant gap
                    fvg_midpoint = (c1["high"] + c3["low"]) / 2

                    # Check if price is approaching the FVG from above
                    if price > fvg_midpoint and price < c3["low"] * 1.02:
                        patterns.append(Pattern(
                            name="Bullish FVG",
                            type=PatternType.LIQUIDITY,
                            direction="bullish",
                            strength=70,
                            confidence=0.65,
                            entry_zone=fvg_midpoint,
                            stop_loss=c1["high"] - atr,
                            target=price + gap_size * 2,
                            timeframe=tf,
                            trend_aligned=htf_trend == "bullish",
                            signals=[
                                f"Imbalance zone ${fvg_midpoint:,.0f}",
                                "Institutional buy zone",
                                "Gap likely to hold"
                            ]
                        ))

            # Bearish FVG: Gap down (c1 low > c3 high)
            elif c1["low"] > c3["high"]:
                gap_size = c1["low"] - c3["high"]
                if gap_size > atr * 0.3:
                    fvg_midpoint = (c1["low"] + c3["high"]) / 2

                    if price < fvg_midpoint and price > c3["high"] * 0.98:
                        patterns.append(Pattern(
                            name="Bearish FVG",
                            type=PatternType.LIQUIDITY,
                            direction="bearish",
                            strength=70,
                            confidence=0.65,
                            entry_zone=fvg_midpoint,
                            stop_loss=c1["low"] + atr,
                            target=price - gap_size * 2,
                            timeframe=tf,
                            trend_aligned=htf_trend == "bearish",
                            signals=[
                                f"Imbalance zone ${fvg_midpoint:,.0f}",
                                "Institutional sell zone",
                                "Gap likely to hold"
                            ]
                        ))

        return patterns

    def _detect_order_blocks(self, candles: List[Dict], tf: str, htf_trend: str) -> List[Pattern]:
        """Detect Order Blocks - institutional entry zones.

        Order Block = Last opposing candle before a strong move.
        - Bullish OB: Last red candle before strong green move
        - Bearish OB: Last green candle before strong red move
        """
        patterns = []
        if len(candles) < 30:
            return patterns

        recent = candles[-30:]
        price = recent[-1]["close"]
        atr = self._calc_atr(candles)

        # Find strong impulse moves
        for i in range(5, len(recent) - 3):
            # Calculate move after this candle
            move_candles = recent[i+1:i+4]
            move_start = recent[i]["close"]
            move_end = move_candles[-1]["close"]
            move_pct = (move_end - move_start) / move_start

            curr = recent[i]
            curr_body = curr["close"] - curr["open"]

            # Bullish Order Block: Red candle followed by strong up move (>2%)
            if curr_body < 0 and move_pct > 0.02:
                ob_zone = (curr["low"], curr["high"])

                # Check if price has returned to the OB zone
                if price >= curr["low"] * 0.99 and price <= curr["high"] * 1.01:
                    patterns.append(Pattern(
                        name="Bullish Order Block",
                        type=PatternType.LIQUIDITY,
                        direction="bullish",
                        strength=75,
                        confidence=0.7,
                        entry_zone=(curr["low"] + curr["high"]) / 2,
                        stop_loss=curr["low"] - atr * 0.5,
                        target=move_end,
                        timeframe=tf,
                        trend_aligned=htf_trend == "bullish",
                        signals=[
                            "Order block zone",
                            "Institutional entry area",
                            f"Target ${move_end:,.0f}"
                        ]
                    ))
                    break

            # Bearish Order Block: Green candle followed by strong down move
            elif curr_body > 0 and move_pct < -0.02:
                if price <= curr["high"] * 1.01 and price >= curr["low"] * 0.99:
                    patterns.append(Pattern(
                        name="Bearish Order Block",
                        type=PatternType.LIQUIDITY,
                        direction="bearish",
                        strength=75,
                        confidence=0.7,
                        entry_zone=(curr["low"] + curr["high"]) / 2,
                        stop_loss=curr["high"] + atr * 0.5,
                        target=move_end,
                        timeframe=tf,
                        trend_aligned=htf_trend == "bearish",
                        signals=[
                            "Order block zone",
                            "Institutional entry area",
                            f"Target ${move_end:,.0f}"
                        ]
                    ))
                    break

        return patterns

    def _detect_volume_patterns(self, candles: List[Dict], tf: str, volume_profile: Dict) -> List[Pattern]:
        """Detect volume-confirmed patterns."""
        patterns = []
        if len(candles) < 20:
            return patterns

        volumes = [c.get("volume", 0) for c in candles]
        if not any(volumes):
            return patterns

        price = candles[-1]["close"]
        atr = self._calc_atr(candles)
        avg_vol = sum(volumes[-20:]) / 20

        # Volume Climax: Extremely high volume often signals exhaustion
        if volumes[-1] > avg_vol * 3:
            curr = candles[-1]
            is_bullish = curr["close"] > curr["open"]

            patterns.append(Pattern(
                name="Volume Climax",
                type=PatternType.BREAKOUT,
                direction="bearish" if is_bullish else "bullish",  # Exhaustion = reversal
                strength=60,
                confidence=0.55,
                entry_zone=price,
                stop_loss=curr["high"] + atr if is_bullish else curr["low"] - atr,
                target=price - atr * 2 if is_bullish else price + atr * 2,
                timeframe=tf,
                volume_confirmed=True,
                signals=[
                    f"Volume {volumes[-1]/avg_vol:.1f}x average",
                    "Possible exhaustion",
                    "Watch for reversal"
                ]
            ))

        return patterns

    # ========================================================================
    # HARMONIC PATTERNS (Advanced - Fibonacci-based)
    # ========================================================================

    def _detect_harmonic_patterns(self, candles: List[Dict], tf: str, htf_trend: str) -> List[Pattern]:
        """Detect Gartley, Bat, Butterfly, Crab, AB=CD harmonic patterns."""
        patterns = []
        if len(candles) < 50:
            return patterns

        # Find swing points for harmonic analysis
        swings = self._find_swings(candles[-50:])
        if len(swings) < 5:
            return patterns

        price = candles[-1]["close"]
        atr = self._calc_atr(candles)

        # Get last 5 swing points (X, A, B, C, D)
        X, A, B, C, D = [s[1] for s in swings[-5:]]

        # Calculate Fibonacci ratios
        XA = abs(A - X)
        AB = abs(B - A)
        BC = abs(C - B)
        CD = abs(D - C)

        if XA == 0 or AB == 0 or BC == 0:
            return patterns

        AB_XA = AB / XA
        BC_AB = BC / AB
        CD_BC = CD / BC

        # Gartley: AB = 0.618 XA, BC = 0.382-0.886 AB, CD = 1.27-1.618 BC
        if 0.55 < AB_XA < 0.68 and 0.3 < BC_AB < 0.9 and 1.2 < CD_BC < 1.7:
            is_bullish = D < X
            patterns.append(Pattern(
                name="Gartley",
                type=PatternType.REVERSAL_BULL if is_bullish else PatternType.REVERSAL_BEAR,
                direction="bullish" if is_bullish else "bearish",
                strength=80,
                confidence=0.7,
                entry_zone=D,
                stop_loss=D - atr * 1.5 if is_bullish else D + atr * 1.5,
                target=D + (A - D) * 0.618 if is_bullish else D - (D - A) * 0.618,
                timeframe=tf,
                trend_aligned=(htf_trend == "bullish") == is_bullish,
                signals=["Gartley harmonic", f"AB/XA={AB_XA:.2f}", "High R:R reversal"]
            ))

        # Bat: AB = 0.382-0.5 XA, BC = 0.382-0.886 AB, CD = 1.618-2.618 BC
        elif 0.35 < AB_XA < 0.52 and 0.3 < BC_AB < 0.9 and 1.5 < CD_BC < 2.7:
            is_bullish = D < X
            patterns.append(Pattern(
                name="Bat",
                type=PatternType.REVERSAL_BULL if is_bullish else PatternType.REVERSAL_BEAR,
                direction="bullish" if is_bullish else "bearish",
                strength=78,
                confidence=0.68,
                entry_zone=D,
                stop_loss=D - atr * 1.5 if is_bullish else D + atr * 1.5,
                target=D + (A - D) * 0.5 if is_bullish else D - (D - A) * 0.5,
                timeframe=tf,
                trend_aligned=(htf_trend == "bullish") == is_bullish,
                signals=["Bat harmonic", f"AB/XA={AB_XA:.2f}", "Deep retracement reversal"]
            ))

        # Butterfly: AB = 0.786 XA, CD extends beyond X
        elif 0.72 < AB_XA < 0.82:
            is_bullish = D < X
            patterns.append(Pattern(
                name="Butterfly",
                type=PatternType.REVERSAL_BULL if is_bullish else PatternType.REVERSAL_BEAR,
                direction="bullish" if is_bullish else "bearish",
                strength=75,
                confidence=0.65,
                entry_zone=D,
                stop_loss=D - atr * 2 if is_bullish else D + atr * 2,
                target=D + (A - D) * 0.382 if is_bullish else D - (D - A) * 0.382,
                timeframe=tf,
                signals=["Butterfly harmonic", f"AB/XA={AB_XA:.2f}", "Extension reversal"]
            ))

        # AB=CD: Simple harmonic where CD equals AB
        if AB > 0 and 0.95 < CD / AB < 1.05:
            is_bullish = D < A  # If D is lower, expect bullish reversal
            patterns.append(Pattern(
                name="AB=CD",
                type=PatternType.REVERSAL_BULL if is_bullish else PatternType.REVERSAL_BEAR,
                direction="bullish" if is_bullish else "bearish",
                strength=70,
                confidence=0.6,
                entry_zone=D,
                stop_loss=D - atr * 1 if is_bullish else D + atr * 1,
                target=D + AB if is_bullish else D - AB,
                timeframe=tf,
                signals=["AB=CD pattern", "Measured move", f"Target ${D + AB if is_bullish else D - AB:,.0f}"]
            ))

        return patterns

    def _find_swings(self, candles: List[Dict], min_bars: int = 3) -> List[Tuple[int, float]]:
        """Find swing highs and lows."""
        swings = []
        for i in range(min_bars, len(candles) - min_bars):
            is_swing_high = all(candles[i]["high"] >= candles[i+j]["high"] for j in range(-min_bars, min_bars+1) if j != 0)
            is_swing_low = all(candles[i]["low"] <= candles[i+j]["low"] for j in range(-min_bars, min_bars+1) if j != 0)

            if is_swing_high:
                swings.append((i, candles[i]["high"]))
            elif is_swing_low:
                swings.append((i, candles[i]["low"]))
        return swings

    # ========================================================================
    # ADDITIONAL CANDLESTICK PATTERNS
    # ========================================================================

    def _detect_doji_patterns(self, candles: List[Dict], tf: str, htf_trend: str) -> List[Pattern]:
        """Detect doji, dragonfly doji, gravestone doji, spinning top."""
        patterns = []
        if len(candles) < 5:
            return patterns

        price = candles[-1]["close"]
        atr = self._calc_atr(candles)

        for i in range(-3, 0):
            c = candles[i]
            body = abs(c["close"] - c["open"])
            upper_wick = c["high"] - max(c["close"], c["open"])
            lower_wick = min(c["close"], c["open"]) - c["low"]
            total_range = c["high"] - c["low"]

            if total_range == 0:
                continue

            body_pct = body / total_range

            # Classic Doji: Very small body (<10%)
            if body_pct < 0.1:
                # Dragonfly Doji: Long lower wick, no upper wick (bullish)
                if lower_wick > atr * 0.5 and upper_wick < atr * 0.1:
                    patterns.append(Pattern(
                        name="Dragonfly Doji",
                        type=PatternType.REVERSAL_BULL,
                        direction="bullish",
                        strength=68,
                        confidence=0.6,
                        entry_zone=c["close"],
                        stop_loss=c["low"] - atr * 0.3,
                        target=c["close"] + atr * 2,
                        timeframe=tf,
                        trend_aligned=htf_trend != "bearish",
                        signals=["Dragonfly doji", "Demand at lows", "Reversal likely"]
                    ))
                    break

                # Gravestone Doji: Long upper wick, no lower wick (bearish)
                elif upper_wick > atr * 0.5 and lower_wick < atr * 0.1:
                    patterns.append(Pattern(
                        name="Gravestone Doji",
                        type=PatternType.REVERSAL_BEAR,
                        direction="bearish",
                        strength=68,
                        confidence=0.6,
                        entry_zone=c["close"],
                        stop_loss=c["high"] + atr * 0.3,
                        target=c["close"] - atr * 2,
                        timeframe=tf,
                        trend_aligned=htf_trend != "bullish",
                        signals=["Gravestone doji", "Supply at highs", "Reversal likely"]
                    ))
                    break

        return patterns

    def _detect_hammer_patterns(self, candles: List[Dict], tf: str, htf_trend: str) -> List[Pattern]:
        """Detect hammer, inverted hammer, hanging man, shooting star."""
        patterns = []
        if len(candles) < 10:
            return patterns

        price = candles[-1]["close"]
        atr = self._calc_atr(candles)

        # Check last few candles
        for i in range(-5, 0):
            c = candles[i]
            body = abs(c["close"] - c["open"])
            upper_wick = c["high"] - max(c["close"], c["open"])
            lower_wick = min(c["close"], c["open"]) - c["low"]

            if body == 0:
                continue

            # Hammer: Small body at top, long lower wick (2x body min)
            if lower_wick > body * 2 and upper_wick < body * 0.5:
                # After downtrend = Hammer (bullish)
                prev_closes = [candles[j]["close"] for j in range(i-5, i)]
                in_downtrend = prev_closes[0] > prev_closes[-1]

                if in_downtrend:
                    patterns.append(Pattern(
                        name="Hammer",
                        type=PatternType.REVERSAL_BULL,
                        direction="bullish",
                        strength=70,
                        confidence=0.65,
                        entry_zone=c["close"],
                        stop_loss=c["low"] - atr * 0.3,
                        target=c["close"] + atr * 2.5,
                        timeframe=tf,
                        trend_aligned=htf_trend != "bearish",
                        signals=["Hammer candle", "Rejection at lows", "Buy signal"]
                    ))
                    break
                else:
                    # After uptrend = Hanging Man (bearish warning)
                    patterns.append(Pattern(
                        name="Hanging Man",
                        type=PatternType.REVERSAL_BEAR,
                        direction="bearish",
                        strength=60,
                        confidence=0.55,
                        entry_zone=c["close"],
                        stop_loss=c["high"] + atr * 0.3,
                        target=c["close"] - atr * 2,
                        timeframe=tf,
                        signals=["Hanging man", "Potential top", "Bearish warning"]
                    ))
                    break

            # Shooting Star: Small body at bottom, long upper wick
            elif upper_wick > body * 2 and lower_wick < body * 0.5:
                prev_closes = [candles[j]["close"] for j in range(i-5, i)]
                in_uptrend = prev_closes[0] < prev_closes[-1]

                if in_uptrend:
                    patterns.append(Pattern(
                        name="Shooting Star",
                        type=PatternType.REVERSAL_BEAR,
                        direction="bearish",
                        strength=70,
                        confidence=0.65,
                        entry_zone=c["close"],
                        stop_loss=c["high"] + atr * 0.3,
                        target=c["close"] - atr * 2.5,
                        timeframe=tf,
                        trend_aligned=htf_trend != "bullish",
                        signals=["Shooting star", "Rejection at highs", "Sell signal"]
                    ))
                    break
                else:
                    # After downtrend = Inverted Hammer (bullish)
                    patterns.append(Pattern(
                        name="Inverted Hammer",
                        type=PatternType.REVERSAL_BULL,
                        direction="bullish",
                        strength=60,
                        confidence=0.55,
                        entry_zone=c["close"],
                        stop_loss=c["low"] - atr * 0.3,
                        target=c["close"] + atr * 2,
                        timeframe=tf,
                        signals=["Inverted hammer", "Potential bottom", "Bullish warning"]
                    ))
                    break

        return patterns

    def _detect_three_candle_formations(self, candles: List[Dict], tf: str, htf_trend: str) -> List[Pattern]:
        """Detect three white soldiers, three black crows, three inside up/down."""
        patterns = []
        if len(candles) < 10:
            return patterns

        price = candles[-1]["close"]
        atr = self._calc_atr(candles)

        # Check for 3-candle formations
        for i in range(-5, -2):
            c1, c2, c3 = candles[i], candles[i+1], candles[i+2]

            body1 = c1["close"] - c1["open"]
            body2 = c2["close"] - c2["open"]
            body3 = c3["close"] - c3["open"]

            # Three White Soldiers: 3 consecutive bullish candles with higher closes
            if (body1 > 0 and body2 > 0 and body3 > 0 and
                c2["close"] > c1["close"] and c3["close"] > c2["close"] and
                c2["open"] > c1["open"] and c3["open"] > c2["open"]):

                # Each candle should open within previous body
                if c2["open"] < c1["close"] and c3["open"] < c2["close"]:
                    patterns.append(Pattern(
                        name="Three White Soldiers",
                        type=PatternType.CONTINUATION_BULL,
                        direction="bullish",
                        strength=80,
                        confidence=0.75,
                        entry_zone=c3["close"],
                        stop_loss=c1["low"] - atr * 0.5,
                        target=c3["close"] + atr * 3,
                        timeframe=tf,
                        trend_aligned=htf_trend == "bullish",
                        signals=["Three white soldiers", "Strong momentum", "Continuation likely"]
                    ))
                    break

            # Three Black Crows: 3 consecutive bearish candles with lower closes
            elif (body1 < 0 and body2 < 0 and body3 < 0 and
                  c2["close"] < c1["close"] and c3["close"] < c2["close"] and
                  c2["open"] < c1["open"] and c3["open"] < c2["open"]):

                if c2["open"] > c1["close"] and c3["open"] > c2["close"]:
                    patterns.append(Pattern(
                        name="Three Black Crows",
                        type=PatternType.CONTINUATION_BEAR,
                        direction="bearish",
                        strength=80,
                        confidence=0.75,
                        entry_zone=c3["close"],
                        stop_loss=c1["high"] + atr * 0.5,
                        target=c3["close"] - atr * 3,
                        timeframe=tf,
                        trend_aligned=htf_trend == "bearish",
                        signals=["Three black crows", "Strong selling", "Continuation likely"]
                    ))
                    break

        return patterns

    def _detect_piercing_darkcloud(self, candles: List[Dict], tf: str, htf_trend: str) -> List[Pattern]:
        """Detect piercing line (bullish) and dark cloud cover (bearish)."""
        patterns = []
        if len(candles) < 5:
            return patterns

        price = candles[-1]["close"]
        atr = self._calc_atr(candles)

        for i in range(-4, -1):
            c1, c2 = candles[i], candles[i+1]

            body1 = c1["close"] - c1["open"]
            body2 = c2["close"] - c2["open"]
            mid1 = (c1["open"] + c1["close"]) / 2

            # Piercing Line: Bearish candle followed by bullish that closes above midpoint
            if body1 < 0 and body2 > 0:
                if c2["open"] < c1["close"] and c2["close"] > mid1:
                    patterns.append(Pattern(
                        name="Piercing Line",
                        type=PatternType.REVERSAL_BULL,
                        direction="bullish",
                        strength=65,
                        confidence=0.6,
                        entry_zone=c2["close"],
                        stop_loss=c2["low"] - atr * 0.5,
                        target=c2["close"] + atr * 2,
                        timeframe=tf,
                        trend_aligned=htf_trend != "bearish",
                        signals=["Piercing line", "Gap down recovery", "Bullish reversal"]
                    ))
                    break

            # Dark Cloud Cover: Bullish candle followed by bearish that closes below midpoint
            elif body1 > 0 and body2 < 0:
                if c2["open"] > c1["close"] and c2["close"] < mid1:
                    patterns.append(Pattern(
                        name="Dark Cloud Cover",
                        type=PatternType.REVERSAL_BEAR,
                        direction="bearish",
                        strength=65,
                        confidence=0.6,
                        entry_zone=c2["close"],
                        stop_loss=c2["high"] + atr * 0.5,
                        target=c2["close"] - atr * 2,
                        timeframe=tf,
                        trend_aligned=htf_trend != "bullish",
                        signals=["Dark cloud cover", "Gap up failure", "Bearish reversal"]
                    ))
                    break

        return patterns

    def _detect_harami(self, candles: List[Dict], tf: str, htf_trend: str) -> List[Pattern]:
        """Detect bullish and bearish harami patterns."""
        patterns = []
        if len(candles) < 5:
            return patterns

        price = candles[-1]["close"]
        atr = self._calc_atr(candles)

        for i in range(-4, -1):
            c1, c2 = candles[i], candles[i+1]

            body1 = abs(c1["close"] - c1["open"])
            body2 = abs(c2["close"] - c2["open"])

            # Second candle must be completely inside first
            inside = (max(c2["open"], c2["close"]) < max(c1["open"], c1["close"]) and
                     min(c2["open"], c2["close"]) > min(c1["open"], c1["close"]))

            if inside and body2 < body1 * 0.5:  # Small body inside large body
                # Bullish Harami: Large red + small green inside
                if c1["close"] < c1["open"] and c2["close"] > c2["open"]:
                    patterns.append(Pattern(
                        name="Bullish Harami",
                        type=PatternType.REVERSAL_BULL,
                        direction="bullish",
                        strength=62,
                        confidence=0.55,
                        entry_zone=c2["close"],
                        stop_loss=c1["low"] - atr * 0.3,
                        target=c2["close"] + atr * 2,
                        timeframe=tf,
                        signals=["Bullish harami", "Inside bar", "Potential reversal"]
                    ))
                    break

                # Bearish Harami: Large green + small red inside
                elif c1["close"] > c1["open"] and c2["close"] < c2["open"]:
                    patterns.append(Pattern(
                        name="Bearish Harami",
                        type=PatternType.REVERSAL_BEAR,
                        direction="bearish",
                        strength=62,
                        confidence=0.55,
                        entry_zone=c2["close"],
                        stop_loss=c1["high"] + atr * 0.3,
                        target=c2["close"] - atr * 2,
                        timeframe=tf,
                        signals=["Bearish harami", "Inside bar", "Potential reversal"]
                    ))
                    break

        return patterns

    def _detect_tweezer(self, candles: List[Dict], tf: str, htf_trend: str) -> List[Pattern]:
        """Detect tweezer tops and bottoms."""
        patterns = []
        if len(candles) < 5:
            return patterns

        price = candles[-1]["close"]
        atr = self._calc_atr(candles)
        tolerance = atr * 0.1  # Very tight tolerance for tweezers

        for i in range(-4, -1):
            c1, c2 = candles[i], candles[i+1]

            # Tweezer Bottom: Two candles with same low (demand zone)
            if abs(c1["low"] - c2["low"]) < tolerance:
                # First bearish, second bullish = stronger signal
                if c1["close"] < c1["open"] and c2["close"] > c2["open"]:
                    patterns.append(Pattern(
                        name="Tweezer Bottom",
                        type=PatternType.REVERSAL_BULL,
                        direction="bullish",
                        strength=68,
                        confidence=0.6,
                        entry_zone=c2["close"],
                        stop_loss=min(c1["low"], c2["low"]) - atr * 0.3,
                        target=c2["close"] + atr * 2.5,
                        timeframe=tf,
                        trend_aligned=htf_trend != "bearish",
                        signals=["Tweezer bottom", "Double test of lows", "Strong support"]
                    ))
                    break

            # Tweezer Top: Two candles with same high (supply zone)
            if abs(c1["high"] - c2["high"]) < tolerance:
                # First bullish, second bearish = stronger signal
                if c1["close"] > c1["open"] and c2["close"] < c2["open"]:
                    patterns.append(Pattern(
                        name="Tweezer Top",
                        type=PatternType.REVERSAL_BEAR,
                        direction="bearish",
                        strength=68,
                        confidence=0.6,
                        entry_zone=c2["close"],
                        stop_loss=max(c1["high"], c2["high"]) + atr * 0.3,
                        target=c2["close"] - atr * 2.5,
                        timeframe=tf,
                        trend_aligned=htf_trend != "bullish",
                        signals=["Tweezer top", "Double test of highs", "Strong resistance"]
                    ))
                    break

        return patterns

    # ========================================================================
    # COMPLEX PATTERNS
    # ========================================================================

    def _detect_cup_and_handle(self, candles: List[Dict], tf: str, htf_trend: str) -> List[Pattern]:
        """Detect cup and handle pattern (bullish continuation)."""
        patterns = []
        if len(candles) < 40:
            return patterns

        price = candles[-1]["close"]
        atr = self._calc_atr(candles)
        closes = [c["close"] for c in candles]

        # Look for U-shaped cup over last 30-40 candles
        cup_start = max(closes[-40:-30])
        cup_bottom = min(closes[-30:-15])
        cup_end = max(closes[-15:-5])

        # Cup should have similar left and right edges
        cup_depth = (cup_start - cup_bottom) / cup_start

        if 0.1 < cup_depth < 0.35 and abs(cup_start - cup_end) / cup_start < 0.05:
            # Look for handle (small pullback at end)
            handle_high = max(closes[-10:-3])
            handle_low = min(closes[-10:-3])
            handle_depth = (handle_high - handle_low) / handle_high

            if handle_depth < cup_depth * 0.5:  # Handle should be shallower than cup
                breakout_level = cup_end
                target = breakout_level + (cup_start - cup_bottom)  # Measured move

                patterns.append(Pattern(
                    name="Cup and Handle",
                    type=PatternType.CONTINUATION_BULL,
                    direction="bullish",
                    strength=82,
                    confidence=0.75,
                    entry_zone=breakout_level,
                    stop_loss=handle_low - atr * 0.5,
                    target=target,
                    timeframe=tf,
                    trend_aligned=htf_trend == "bullish",
                    signals=["Cup and handle", f"Depth: {cup_depth*100:.1f}%", f"Target ${target:,.0f}"]
                ))

        return patterns

    def _detect_rounding_patterns(self, candles: List[Dict], tf: str, htf_trend: str) -> List[Pattern]:
        """Detect rounding bottom (saucer) and rounding top."""
        patterns = []
        if len(candles) < 30:
            return patterns

        price = candles[-1]["close"]
        atr = self._calc_atr(candles)
        closes = [c["close"] for c in candles[-30:]]

        # Calculate curvature by comparing to linear regression
        mid = len(closes) // 2
        left_avg = sum(closes[:mid]) / mid
        right_avg = sum(closes[mid:]) / (len(closes) - mid)
        center_avg = sum(closes[mid-5:mid+5]) / 10

        # Rounding Bottom: Left high, center low, right high (U-shape)
        if left_avg > center_avg and right_avg > center_avg:
            curve_depth = (left_avg - center_avg) / left_avg
            if 0.05 < curve_depth < 0.2:
                patterns.append(Pattern(
                    name="Rounding Bottom",
                    type=PatternType.REVERSAL_BULL,
                    direction="bullish",
                    strength=75,
                    confidence=0.65,
                    entry_zone=price,
                    stop_loss=min(closes) - atr * 0.5,
                    target=max(closes) + (max(closes) - min(closes)) * 0.5,
                    timeframe=tf,
                    trend_aligned=htf_trend != "bearish",
                    signals=["Rounding bottom", "Gradual accumulation", "Bullish reversal"]
                ))

        # Rounding Top: Left low, center high, right low (inverted U)
        elif left_avg < center_avg and right_avg < center_avg:
            curve_height = (center_avg - left_avg) / center_avg
            if 0.05 < curve_height < 0.2:
                patterns.append(Pattern(
                    name="Rounding Top",
                    type=PatternType.REVERSAL_BEAR,
                    direction="bearish",
                    strength=75,
                    confidence=0.65,
                    entry_zone=price,
                    stop_loss=max(closes) + atr * 0.5,
                    target=min(closes) - (max(closes) - min(closes)) * 0.5,
                    timeframe=tf,
                    trend_aligned=htf_trend != "bullish",
                    signals=["Rounding top", "Gradual distribution", "Bearish reversal"]
                ))

        return patterns


    def get_alert_patterns(
        self,
        candles_5m: List[Dict],
        candles_15m: List[Dict],
        candles_1h: List[Dict],
        candles_4h: List[Dict] = None,
        volume_profile: Dict = None,
        min_score: int = None
    ) -> List[Dict]:
        """Get patterns formatted for Discord alerts.

        Args:
            candles_*: Candle data for each timeframe
            volume_profile: Volume profile data
            min_score: Minimum score to alert (default: 60)

        Returns:
            List of dicts ready for Discord alert
        """
        if min_score:
            self.min_pattern_score = min_score

        patterns = self.detect_all_patterns(
            candles_5m, candles_15m, candles_1h, candles_4h, volume_profile
        )

        alerts = []
        for p in patterns:
            alerts.append({
                "name": p.name,
                "type": p.type.value,
                "direction": p.direction,
                "score": p.score,
                "confidence": p.confidence,
                "entry": p.entry_zone,
                "stop": p.stop_loss,
                "target": p.target,
                "timeframe": p.timeframe,
                "volume_confirmed": p.volume_confirmed,
                "trend_aligned": p.trend_aligned,
                "htf_support": p.htf_support,
                "signals": p.signals,
                "risk_reward": abs(p.target - p.entry_zone) / abs(p.entry_zone - p.stop_loss) if p.stop_loss != p.entry_zone else 0
            })

        return alerts


def format_pattern_alert(symbol: str, pattern: Dict) -> str:
    """Format a pattern alert for Discord.

    Args:
        symbol: Trading symbol
        pattern: Pattern dict from get_alert_patterns()

    Returns:
        Formatted Discord message
    """
    emoji = "🟢" if pattern["direction"] == "bullish" else "🔴"
    type_emoji = {
        "continuation_bull": "📈",
        "continuation_bear": "📉",
        "reversal_bull": "🔄⬆️",
        "reversal_bear": "🔄⬇️",
        "breakout": "💥",
        "liquidity": "🎯"
    }.get(pattern["type"], "📊")

    # Build confirmation badges
    badges = []
    if pattern["volume_confirmed"]:
        badges.append("📊Vol")
    if pattern["trend_aligned"]:
        badges.append("📐Trend")
    if pattern["htf_support"]:
        badges.append("🔝HTF")

    badges_str = " ".join(badges) if badges else ""

    # Calculate risk/reward
    rr = pattern.get("risk_reward", 0)

    message = f"""{emoji} **${symbol}** — {type_emoji} **{pattern["name"]}** ({pattern["timeframe"]})
Score: {pattern["score"]}/100 | Conf: {pattern["confidence"]:.0%} | R:R {rr:.1f}:1
Entry: ${pattern["entry"]:,.0f} → Target: ${pattern["target"]:,.0f} (Stop: ${pattern["stop"]:,.0f})
{badges_str}
{' • '.join(pattern["signals"][:2])}"""

    return message.strip()


def format_pattern_summary(symbol: str, patterns: List[Dict]) -> str:
    """Format a summary of all detected patterns for Discord.

    Args:
        symbol: Trading symbol
        patterns: List of pattern dicts

    Returns:
        Formatted Discord message
    """
    if not patterns:
        return f"📊 **${symbol}** — No high-probability patterns detected"

    # Count by direction
    bullish = [p for p in patterns if p["direction"] == "bullish"]
    bearish = [p for p in patterns if p["direction"] == "bearish"]

    # Get best pattern
    best = patterns[0]
    emoji = "🟢" if best["direction"] == "bullish" else "🔴"

    # Build summary
    lines = [
        f"📊 **${symbol} Pattern Scan** — {len(patterns)} setups found",
        f"🟢 {len(bullish)} bullish | 🔴 {len(bearish)} bearish",
        f"",
        f"{emoji} **Best: {best['name']}** ({best['timeframe']}) — Score {best['score']}/100",
        f"Entry ${best['entry']:,.0f} → ${best['target']:,.0f}"
    ]

    # Add top 3 patterns
    if len(patterns) > 1:
        lines.append("")
        lines.append("Other setups:")
        for p in patterns[1:4]:
            e = "🟢" if p["direction"] == "bullish" else "🔴"
            lines.append(f"  {e} {p['name']} ({p['timeframe']}) — {p['score']}/100")

    return "\n".join(lines)


# ============================================================================
# PRICE PREDICTION SYSTEM
# ============================================================================

@dataclass
class PricePrediction:
    """Price prediction for 5 candles ahead."""
    symbol: str
    timeframe: str
    current_price: float
    predicted_price: float
    predicted_direction: str  # "up", "down", "neutral"
    confidence: float  # 0-1
    predicted_pct_change: float
    reasoning: List[str]
    timestamp: str = ""
    patterns_used: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict:
        return {
            "symbol": self.symbol,
            "timeframe": self.timeframe,
            "current_price": self.current_price,
            "predicted_price": self.predicted_price,
            "predicted_direction": self.predicted_direction,
            "confidence": self.confidence,
            "predicted_pct_change": self.predicted_pct_change,
            "reasoning": self.reasoning,
            "timestamp": self.timestamp,
            "patterns_used": self.patterns_used
        }


class PricePredictor:
    """Predicts price 5 candles ahead based on technical analysis."""

    def __init__(self):
        self.pattern_detector = PatternDetector()

    def predict_price_5_candles(
        self,
        symbol: str,
        candles: List[Dict],
        timeframe: str,
        patterns: List[Dict] = None
    ) -> PricePrediction:
        """Predict where price will be 5 candles ahead.

        Uses:
        1. Detected patterns (target direction)
        2. Trend momentum (EMA slope)
        3. Recent volatility (ATR-based movement)
        4. Support/resistance proximity

        Args:
            symbol: Trading symbol
            candles: Candle data (100+ candles)
            timeframe: Timeframe string
            patterns: Pre-detected patterns (optional)

        Returns:
            PricePrediction object with predicted price and confidence
        """
        from datetime import datetime

        if not candles or len(candles) < 30:
            return PricePrediction(
                symbol=symbol,
                timeframe=timeframe,
                current_price=0,
                predicted_price=0,
                predicted_direction="neutral",
                confidence=0,
                predicted_pct_change=0,
                reasoning=["Insufficient data"],
                timestamp=datetime.utcnow().isoformat()
            )

        current_price = candles[-1]["close"]
        closes = [c["close"] for c in candles]
        highs = [c["high"] for c in candles]
        lows = [c["low"] for c in candles]

        # Calculate key metrics
        atr = self._calc_atr(candles)
        ema_9 = self._calc_ema(closes, 9)
        ema_21 = self._calc_ema(closes, 21)

        # 1. TREND ANALYSIS
        trend_score = 0
        reasoning = []

        # EMA trend
        if ema_9 > ema_21 * 1.001:
            trend_score += 30
            reasoning.append("Bullish EMA alignment")
        elif ema_9 < ema_21 * 0.999:
            trend_score -= 30
            reasoning.append("Bearish EMA alignment")

        # EMA slope (momentum)
        ema_9_prev = self._calc_ema(closes[:-5], 9)
        ema_slope = (ema_9 - ema_9_prev) / ema_9_prev if ema_9_prev > 0 else 0

        if ema_slope > 0.005:
            trend_score += 20
            reasoning.append(f"Strong upward momentum ({ema_slope*100:.2f}%)")
        elif ema_slope < -0.005:
            trend_score -= 20
            reasoning.append(f"Strong downward momentum ({ema_slope*100:.2f}%)")

        # 2. PATTERN ANALYSIS
        pattern_score = 0
        patterns_used = []

        if patterns:
            for p in patterns[:3]:  # Top 3 patterns
                weight = p.get("score", 0) / 100 * 0.3  # Max 30 points from patterns
                if p["direction"] == "bullish":
                    pattern_score += weight * 100
                else:
                    pattern_score -= weight * 100
                patterns_used.append(p["name"])

            if patterns_used:
                reasoning.append(f"Patterns: {', '.join(patterns_used)}")

        # 3. MOMENTUM ANALYSIS (last 5 candles)
        momentum_score = 0
        recent_closes = closes[-5:]

        up_candles = sum(1 for i in range(1, len(recent_closes)) if recent_closes[i] > recent_closes[i-1])

        if up_candles >= 4:
            momentum_score += 20
            reasoning.append("Strong recent upward momentum")
        elif up_candles <= 1:
            momentum_score -= 20
            reasoning.append("Strong recent downward momentum")

        # 4. SUPPORT/RESISTANCE PROXIMITY
        sr_score = 0
        recent_high = max(highs[-20:])
        recent_low = min(lows[-20:])

        price_in_range = (current_price - recent_low) / (recent_high - recent_low) if recent_high > recent_low else 0.5

        if price_in_range < 0.2:
            sr_score += 15
            reasoning.append("Near support level")
        elif price_in_range > 0.8:
            sr_score -= 15
            reasoning.append("Near resistance level")

        # 5. COMBINE SCORES
        total_score = trend_score + pattern_score + momentum_score + sr_score

        # Normalize to direction
        if total_score > 20:
            direction = "up"
        elif total_score < -20:
            direction = "down"
        else:
            direction = "neutral"

        # Calculate confidence (0-1)
        confidence = min(1.0, abs(total_score) / 80)

        # Calculate predicted price based on ATR and confidence
        # 5 candles typically move 0.5-2 ATR
        expected_atr_move = atr * 1.2 * confidence  # Scale by confidence

        if direction == "up":
            predicted_price = current_price + expected_atr_move
            pct_change = expected_atr_move / current_price * 100
        elif direction == "down":
            predicted_price = current_price - expected_atr_move
            pct_change = -expected_atr_move / current_price * 100
        else:
            predicted_price = current_price
            pct_change = 0

        return PricePrediction(
            symbol=symbol,
            timeframe=timeframe,
            current_price=current_price,
            predicted_price=predicted_price,
            predicted_direction=direction,
            confidence=confidence,
            predicted_pct_change=pct_change,
            reasoning=reasoning,
            timestamp=datetime.utcnow().isoformat(),
            patterns_used=patterns_used
        )

    def _calc_atr(self, candles: List[Dict], period: int = 14) -> float:
        """Calculate ATR."""
        if len(candles) < period + 1:
            return candles[-1]["high"] - candles[-1]["low"] if candles else 0

        tr_list = []
        for i in range(1, len(candles)):
            c = candles[i]
            prev = candles[i-1]
            tr = max(
                c["high"] - c["low"],
                abs(c["high"] - prev["close"]),
                abs(c["low"] - prev["close"])
            )
            tr_list.append(tr)

        return sum(tr_list[-period:]) / period

    def _calc_ema(self, values: List[float], period: int) -> float:
        """Calculate EMA of last value."""
        if len(values) < period:
            return sum(values) / len(values) if values else 0

        multiplier = 2 / (period + 1)
        ema = sum(values[:period]) / period

        for val in values[period:]:
            ema = (val - ema) * multiplier + ema

        return ema