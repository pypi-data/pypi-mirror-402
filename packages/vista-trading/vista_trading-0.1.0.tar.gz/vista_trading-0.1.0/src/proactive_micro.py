"""
Proactive MICRO Trading Strategy - Always On, Always Scanning.

This module makes MICRO an aggressive, proactive trader that:
1. Continuously scans for momentum-based entries
2. Uses adaptive SL/TP based on volatility regime
3. Dynamically trails positions based on market conditions
4. Capitalizes on short-term momentum shifts

Key Philosophy:
- Don't wait for perfect setups - capture momentum
- Tight stops, let winners run
- Adapt SL/TP to current volatility
- Be aggressive in trending markets, defensive in ranging
"""

import logging
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from enum import Enum
from datetime import datetime
import math

logger = logging.getLogger(__name__)


class VolatilityRegime(Enum):
    """Current volatility state affects SL/TP sizing."""
    COMPRESSED = "compressed"    # Low vol - tight stops, breakout potential
    NORMAL = "normal"            # Average vol - standard parameters
    EXPANDING = "expanding"      # Rising vol - wider stops, momentum plays
    EXPLOSIVE = "explosive"      # High vol - very wide stops, reduced size


class MomentumState(Enum):
    """Momentum classification for entry timing."""
    STRONG_BULLISH = "strong_bullish"
    WEAK_BULLISH = "weak_bullish"
    NEUTRAL = "neutral"
    WEAK_BEARISH = "weak_bearish"
    STRONG_BEARISH = "strong_bearish"


@dataclass
class ProactiveScan:
    """Result of proactive market scan."""
    should_enter: bool
    direction: str  # "long", "short", "none"
    confidence: float
    momentum_state: MomentumState
    volatility_regime: VolatilityRegime
    
    # Adaptive SL/TP
    stop_loss: float
    take_profit: float
    sl_distance_pct: float
    rr_ratio: float
    
    # Position sizing
    size_multiplier: float
    
    # Entry reasoning
    triggers: List[str]
    reasoning: str


class ProactiveMicroStrategy:
    """
    Proactive MICRO strategy that constantly hunts for trades.
    
    Entry Triggers (need 2+ for entry):
    1. Momentum confirmation (EMA crossover, RSI direction)
    2. Volume expansion (above average)
    3. Price structure (break of recent high/low)
    4. Orderbook imbalance (directional pressure)
    
    Adaptive SL/TP:
    - Compressed vol: 0.3-0.5% stop, 2:1 R:R
    - Normal vol: 0.5-1.0% stop, 2.5:1 R:R
    - Expanding vol: 1.0-1.5% stop, 3:1 R:R
    - Explosive vol: 1.5-2.5% stop, 3.5:1 R:R (reduced size)
    """
    
    def __init__(self):
        self.atr_history: Dict[str, List[float]] = {}  # Track ATR over time
        self.last_scan: Dict[str, datetime] = {}
        self.momentum_history: Dict[str, List[float]] = {}
        
        # Adaptive parameters by volatility regime
        self.regime_params = {
            VolatilityRegime.COMPRESSED: {
                "sl_pct_min": 0.003, "sl_pct_max": 0.005,
                "rr_target": 2.5, "size_mult": 1.2,
                "trail_activation_pct": 0.5, "trail_lock_pct": 0.3
            },
            VolatilityRegime.NORMAL: {
                "sl_pct_min": 0.005, "sl_pct_max": 0.01,
                "rr_target": 2.5, "size_mult": 1.0,
                "trail_activation_pct": 0.8, "trail_lock_pct": 0.4
            },
            VolatilityRegime.EXPANDING: {
                "sl_pct_min": 0.01, "sl_pct_max": 0.015,
                "rr_target": 3.0, "size_mult": 0.8,
                "trail_activation_pct": 1.2, "trail_lock_pct": 0.5
            },
            VolatilityRegime.EXPLOSIVE: {
                "sl_pct_min": 0.015, "sl_pct_max": 0.025,
                "rr_target": 3.5, "size_mult": 0.5,
                "trail_activation_pct": 2.0, "trail_lock_pct": 0.6
            }
        }
    
    def scan_for_opportunity(
        self,
        symbol: str,
        price: float,
        candles_5m: List[Dict],
        candles_15m: List[Dict],
        candles_1h: List[Dict],
        orderbook: Dict,
        rsi: float,
        atr: float,
        volume_ratio: float
    ) -> ProactiveScan:
        """
        Proactively scan for trading opportunities.
        
        This runs every cycle looking for momentum setups,
        not waiting for price to reach specific levels.
        """
        # 1. Detect volatility regime
        vol_regime = self._detect_volatility_regime(symbol, atr, price, candles_5m)
        
        # 2. Analyze momentum
        momentum = self._analyze_momentum(candles_5m, candles_15m, rsi)
        
        # 3. Check entry triggers
        triggers, direction, confidence = self._check_entry_triggers(
            candles_5m, candles_15m, candles_1h,
            orderbook, rsi, volume_ratio, momentum
        )
        
        # 4. Calculate adaptive SL/TP
        sl, tp, sl_pct, rr = self._calculate_adaptive_sltp(
            price, direction, vol_regime, atr
        )
        
        # 5. Determine if we should enter - QUALITY FOCUSED (not just aggressive)
        # Need 2+ triggers for entry, only 1 trigger allowed if confidence is very high
        min_triggers = 1 if confidence >= 0.75 else 2  # Increased from 0.60
        min_confidence = 0.55  # Increased from 0.45 - better entry quality
        should_enter = len(triggers) >= min_triggers and confidence >= min_confidence and direction != "none"

        # 6. Get size multiplier
        params = self.regime_params[vol_regime]
        size_mult = params["size_mult"]

        # Boost size for high confidence
        if confidence >= 0.75:
            size_mult *= 1.2
        elif confidence < 0.60:
            size_mult *= 0.8

        # === DETAILED LOGGING ===
        logger.info(f"   📊 SCAN DETAILS {symbol}:")
        logger.info(f"      Triggers ({len(triggers)}): {', '.join(triggers) if triggers else 'none'}")
        logger.info(f"      Direction: {direction} | Confidence: {confidence:.0%}")
        logger.info(f"      Min triggers needed: {min_triggers} | Min conf: {min_confidence:.0%}")
        logger.info(f"      Vol regime: {vol_regime.value} | Momentum: {momentum.value}")
        if direction != "none":
            logger.info(f"      SL: {sl_pct:.2f}% | R:R: {rr:.1f}:1 | Size: {size_mult:.1f}x")
        logger.info(f"      ENTRY: {'✅ YES' if should_enter else '❌ NO'}")

        reasoning = self._generate_reasoning(triggers, momentum, vol_regime, confidence)

        return ProactiveScan(
            should_enter=should_enter,
            direction=direction,
            confidence=confidence,
            momentum_state=momentum,
            volatility_regime=vol_regime,
            stop_loss=sl,
            take_profit=tp,
            sl_distance_pct=sl_pct,
            rr_ratio=rr,
            size_multiplier=size_mult,
            triggers=triggers,
            reasoning=reasoning
        )

    def _detect_volatility_regime(
        self, symbol: str, atr: float, price: float, candles: List[Dict]
    ) -> VolatilityRegime:
        """Detect current volatility regime using ATR percentile."""
        if not candles or len(candles) < 20:
            return VolatilityRegime.NORMAL

        atr_pct = (atr / price) * 100

        # Track ATR history for percentile calculation
        if symbol not in self.atr_history:
            self.atr_history[symbol] = []

        self.atr_history[symbol].append(atr_pct)
        if len(self.atr_history[symbol]) > 100:
            self.atr_history[symbol] = self.atr_history[symbol][-100:]

        # Calculate percentile
        history = sorted(self.atr_history[symbol])
        if len(history) < 10:
            # Not enough data - use absolute thresholds
            if atr_pct < 0.5:
                return VolatilityRegime.COMPRESSED
            elif atr_pct < 1.0:
                return VolatilityRegime.NORMAL
            elif atr_pct < 2.0:
                return VolatilityRegime.EXPANDING
            else:
                return VolatilityRegime.EXPLOSIVE

        # Use percentile ranking
        rank = history.index(min(history, key=lambda x: abs(x - atr_pct)))
        percentile = (rank / len(history)) * 100

        if percentile < 20:
            return VolatilityRegime.COMPRESSED
        elif percentile < 60:
            return VolatilityRegime.NORMAL
        elif percentile < 85:
            return VolatilityRegime.EXPANDING
        else:
            return VolatilityRegime.EXPLOSIVE

    def _analyze_momentum(
        self, candles_5m: List[Dict], candles_15m: List[Dict], rsi: float
    ) -> MomentumState:
        """Analyze current momentum state."""
        if not candles_5m or len(candles_5m) < 10:
            return MomentumState.NEUTRAL

        # Calculate price momentum (rate of change)
        closes = [c.get("close", c.get("c", 0)) for c in candles_5m[-10:]]
        if len(closes) < 10 or closes[0] == 0:
            return MomentumState.NEUTRAL

        roc_5 = ((closes[-1] - closes[-5]) / closes[-5]) * 100
        roc_10 = ((closes[-1] - closes[0]) / closes[0]) * 100

        # EMA momentum (comparing fast vs slow)
        ema_8 = self._calc_ema(closes, 8)
        ema_21 = self._calc_ema(closes, min(21, len(closes)))
        ema_diff_pct = ((ema_8 - ema_21) / ema_21) * 100 if ema_21 > 0 else 0

        # Score momentum
        momentum_score = 0

        # Rate of change contribution
        if roc_5 > 0.5:
            momentum_score += 2
        elif roc_5 > 0.1:
            momentum_score += 1
        elif roc_5 < -0.5:
            momentum_score -= 2
        elif roc_5 < -0.1:
            momentum_score -= 1

        # 10-period ROC contribution
        if roc_10 > 1.0:
            momentum_score += 2
        elif roc_10 > 0.3:
            momentum_score += 1
        elif roc_10 < -1.0:
            momentum_score -= 2
        elif roc_10 < -0.3:
            momentum_score -= 1

        # EMA relationship
        if ema_diff_pct > 0.3:
            momentum_score += 1
        elif ema_diff_pct < -0.3:
            momentum_score -= 1

        # RSI contribution (widened)
        if rsi > 55:  # Lowered from 60
            momentum_score += 1
        elif rsi < 45:  # Raised from 40
            momentum_score -= 1

        # Map score to state (lowered thresholds for more sensitivity)
        if momentum_score >= 3:  # Lowered from 4
            return MomentumState.STRONG_BULLISH
        elif momentum_score >= 1:  # Lowered from 2
            return MomentumState.WEAK_BULLISH
        elif momentum_score <= -3:  # Raised from -4
            return MomentumState.STRONG_BEARISH
        elif momentum_score <= -1:  # Raised from -2
            return MomentumState.WEAK_BEARISH
        else:
            return MomentumState.NEUTRAL

    def _check_entry_triggers(
        self,
        candles_5m: List[Dict],
        candles_15m: List[Dict],
        candles_1h: List[Dict],
        orderbook: Dict,
        rsi: float,
        volume_ratio: float,
        momentum: MomentumState
    ) -> Tuple[List[str], str, float]:
        """NEUTRAL SCANNING: Evaluate BOTH directions independently, pick better setup.

        Instead of letting momentum bias one direction, we score both long and short
        setups separately and return the one with the better risk-adjusted score.
        """
        if not candles_5m or len(candles_5m) < 5:
            return [], "none", 0.0

        closes = [c.get("close", c.get("c", 0)) for c in candles_5m[-20:]]
        highs = [c.get("high", c.get("h", 0)) for c in candles_5m[-20:]]
        lows = [c.get("low", c.get("l", 0)) for c in candles_5m[-20:]]
        current_price = closes[-1]

        # === EVALUATE LONG SETUP ===
        long_triggers, long_score = self._evaluate_direction_setup(
            "long", closes, highs, lows, current_price, orderbook, rsi, volume_ratio, candles_5m
        )

        # === EVALUATE SHORT SETUP ===
        short_triggers, short_score = self._evaluate_direction_setup(
            "short", closes, highs, lows, current_price, orderbook, rsi, volume_ratio, candles_5m
        )

        # === NEUTRAL SELECTION: Pick the better setup ===
        # Minimum score of 2 to be considered valid
        min_score = 2

        long_valid = long_score >= min_score
        short_valid = short_score >= min_score

        if not long_valid and not short_valid:
            return [], "none", 0.0

        # If only one is valid, use that
        if long_valid and not short_valid:
            direction = "long"
            confidence = min(0.9, 0.4 + (long_score * 0.1))
            triggers = long_triggers
        elif short_valid and not long_valid:
            direction = "short"
            confidence = min(0.9, 0.4 + (short_score * 0.1))
            triggers = short_triggers
        else:
            # Both valid - pick the one with higher score
            # If tied, look at RSI for mean reversion edge
            if long_score > short_score:
                direction = "long"
                confidence = min(0.9, 0.4 + (long_score * 0.1))
                triggers = long_triggers
            elif short_score > long_score:
                direction = "short"
                confidence = min(0.9, 0.4 + (short_score * 0.1))
                triggers = short_triggers
            else:
                # Tied scores - use RSI as tiebreaker (mean reversion)
                if rsi < 45:  # Oversold favors long
                    direction = "long"
                    confidence = min(0.85, 0.4 + (long_score * 0.1))
                    triggers = long_triggers
                elif rsi > 55:  # Overbought favors short
                    direction = "short"
                    confidence = min(0.85, 0.4 + (short_score * 0.1))
                    triggers = short_triggers
                else:
                    direction = "none"
                    confidence = 0.3
                    triggers = []

        return triggers, direction, confidence

    def _evaluate_direction_setup(
        self,
        direction: str,
        closes: List[float],
        highs: List[float],
        lows: List[float],
        current_price: float,
        orderbook: Dict,
        rsi: float,
        volume_ratio: float,
        candles_5m: List[Dict]
    ) -> Tuple[List[str], int]:
        """Evaluate setup quality for a specific direction (long or short).

        Returns triggers and score for this direction only.
        This allows neutral comparison between long and short setups.
        """
        triggers = []
        score = 0
        is_long = direction == "long"

        # === 1. RSI POSITION (mean reversion + momentum) ===
        if is_long:
            if rsi < 35:  # Oversold - good for long
                triggers.append("rsi_oversold")
                score += 2
            elif rsi < 45:  # Approaching oversold
                triggers.append("rsi_low")
                score += 1
            elif 50 <= rsi <= 65:  # Bullish momentum zone
                triggers.append("rsi_bullish_zone")
                score += 1
        else:  # Short
            if rsi > 65:  # Overbought - good for short
                triggers.append("rsi_overbought")
                score += 2
            elif rsi > 55:  # Approaching overbought
                triggers.append("rsi_high")
                score += 1
            elif 35 <= rsi <= 50:  # Bearish momentum zone
                triggers.append("rsi_bearish_zone")
                score += 1

        # === 2. PRICE STRUCTURE ===
        recent_high = max(highs[-6:-1]) if len(highs) > 6 else max(highs[:-1])
        recent_low = min(lows[-6:-1]) if len(lows) > 6 else min(lows[:-1])

        if is_long:
            # Near recent low = good long entry
            dist_to_low = (current_price - recent_low) / current_price * 100
            if dist_to_low < 0.3:  # Within 0.3% of recent low
                triggers.append("near_support")
                score += 2
            elif dist_to_low < 0.6:
                triggers.append("approaching_support")
                score += 1
            # Breaking above recent high = momentum
            if current_price > recent_high:
                triggers.append("break_high")
                score += 2
        else:  # Short
            # Near recent high = good short entry
            dist_to_high = (recent_high - current_price) / current_price * 100
            if dist_to_high < 0.3:  # Within 0.3% of recent high
                triggers.append("near_resistance")
                score += 2
            elif dist_to_high < 0.6:
                triggers.append("approaching_resistance")
                score += 1
            # Breaking below recent low = momentum
            if current_price < recent_low:
                triggers.append("break_low")
                score += 2

        # === 3. ORDERBOOK IMBALANCE ===
        ob_imbalance = orderbook.get("imbalance", 0)
        if is_long and ob_imbalance > 0.15:
            triggers.append("orderbook_bid_heavy")
            score += 1
        elif not is_long and ob_imbalance < -0.15:
            triggers.append("orderbook_ask_heavy")
            score += 1

        # === 4. VOLUME CONFIRMATION ===
        if volume_ratio > 1.2:
            if is_long and closes[-1] > closes[-2]:
                triggers.append("volume_up_candle")
                score += 1
            elif not is_long and closes[-1] < closes[-2]:
                triggers.append("volume_down_candle")
                score += 1

        # === 5. EMA STRUCTURE ===
        if len(closes) >= 21:
            ema_8 = self._calc_ema(closes, 8)
            ema_21 = self._calc_ema(closes, 21)
            ema_8_prev = self._calc_ema(closes[:-1], 8)
            ema_21_prev = self._calc_ema(closes[:-1], 21)

            if is_long:
                # Bullish cross or alignment
                if ema_8 > ema_21 and ema_8_prev <= ema_21_prev:
                    triggers.append("ema_bullish_cross")
                    score += 2
                elif ema_8 > ema_21 * 1.001:
                    triggers.append("ema_bullish_aligned")
                    score += 1
                # Price above EMA = bullish
                elif current_price > ema_21:
                    triggers.append("price_above_ema21")
                    score += 1
            else:  # Short
                # Bearish cross or alignment
                if ema_8 < ema_21 and ema_8_prev >= ema_21_prev:
                    triggers.append("ema_bearish_cross")
                    score += 2
                elif ema_8 < ema_21 * 0.999:
                    triggers.append("ema_bearish_aligned")
                    score += 1
                # Price below EMA = bearish
                elif current_price < ema_21:
                    triggers.append("price_below_ema21")
                    score += 1

        # === 6. CANDLESTICK PATTERNS ===
        if len(candles_5m) >= 3:
            pattern = self._detect_candle_pattern(candles_5m[-3:])
            if is_long and pattern == "bullish_engulf":
                triggers.append("candle_bullish_engulf")
                score += 2
            elif not is_long and pattern == "bearish_engulf":
                triggers.append("candle_bearish_engulf")
                score += 2

        # === 7. PRICE MOMENTUM ===
        if len(closes) >= 3:
            avg_recent = sum(closes[-3:]) / 3
            if is_long and current_price > avg_recent * 1.001:
                triggers.append("price_momentum_up")
                score += 1
            elif not is_long and current_price < avg_recent * 0.999:
                triggers.append("price_momentum_down")
                score += 1

        return triggers, score

    def _detect_candle_pattern(self, candles: List[Dict]) -> str:
        """Detect simple candlestick patterns."""
        if len(candles) < 2:
            return "none"

        curr = candles[-1]
        prev = candles[-2]

        curr_open = curr.get("open", curr.get("o", 0))
        curr_close = curr.get("close", curr.get("c", 0))
        prev_open = prev.get("open", prev.get("o", 0))
        prev_close = prev.get("close", prev.get("c", 0))

        curr_body = abs(curr_close - curr_open)
        prev_body = abs(prev_close - prev_open)

        # Bullish engulfing
        if (prev_close < prev_open and  # Previous was red
            curr_close > curr_open and  # Current is green
            curr_body > prev_body * 1.2 and  # Larger body
            curr_close > prev_open):  # Engulfs previous
            return "bullish_engulf"

        # Bearish engulfing
        if (prev_close > prev_open and  # Previous was green
            curr_close < curr_open and  # Current is red
            curr_body > prev_body * 1.2 and  # Larger body
            curr_close < prev_open):  # Engulfs previous
            return "bearish_engulf"

        return "none"

    def _calculate_adaptive_sltp(
        self,
        price: float,
        direction: str,
        vol_regime: VolatilityRegime,
        atr: float
    ) -> Tuple[float, float, float, float]:
        """Calculate adaptive SL/TP based on volatility regime."""
        if direction == "none" or price <= 0:
            return 0, 0, 0, 0

        params = self.regime_params[vol_regime]

        # Calculate stop distance based on regime
        atr_pct = (atr / price) if price > 0 else 0.01

        # Use ATR but bound by regime limits
        sl_pct = max(params["sl_pct_min"], min(params["sl_pct_max"], atr_pct * 1.5))

        # R:R ratio from regime
        rr_ratio = params["rr_target"]
        tp_pct = sl_pct * rr_ratio

        # Calculate actual prices
        if direction == "long":
            stop_loss = price * (1 - sl_pct)
            take_profit = price * (1 + tp_pct)
        else:  # short
            stop_loss = price * (1 + sl_pct)
            take_profit = price * (1 - tp_pct)

        return stop_loss, take_profit, sl_pct * 100, rr_ratio

    def get_adaptive_trail_params(
        self, vol_regime: VolatilityRegime
    ) -> Dict[str, float]:
        """Get trailing parameters for current volatility regime."""
        params = self.regime_params[vol_regime]
        return {
            "activation_pct": params["trail_activation_pct"],
            "lock_in_pct": params["trail_lock_pct"],
            "regime": vol_regime.value
        }

    def calculate_dynamic_trail(
        self,
        side: str,
        entry_price: float,
        current_price: float,
        best_price: float,
        current_sl: float,
        vol_regime: VolatilityRegime,
        pnl_pct: float
    ) -> Tuple[Optional[float], str]:
        """
        Calculate new trailing stop based on market conditions.

        Returns (new_sl, reason) or (None, "") if no update needed.

        Trailing Logic by Regime:
        - COMPRESSED: Trail tighter - lock in gains quickly
        - NORMAL: Standard trailing
        - EXPANDING: Give more room - don't get shaken out
        - EXPLOSIVE: Very wide trail - let momentum run
        """
        params = self.regime_params[vol_regime]
        activation_pct = params["trail_activation_pct"]
        lock_pct = params["trail_lock_pct"]

        # Check if trailing should activate
        if pnl_pct < activation_pct:
            return None, ""

        new_sl = None
        reason = ""

        if side == "long":
            gain_amount = best_price - entry_price

            # Dynamic trailing thresholds based on regime and profit level
            if vol_regime == VolatilityRegime.COMPRESSED:
                # Tight trailing - lock in quickly
                if pnl_pct >= 2.0:
                    new_sl = entry_price + (gain_amount * 0.6)
                    reason = f"compressed_lock_60pct@{pnl_pct:.1f}%"
                elif pnl_pct >= 1.0:
                    new_sl = entry_price + (gain_amount * 0.4)
                    reason = f"compressed_lock_40pct@{pnl_pct:.1f}%"
                elif pnl_pct >= 0.5:
                    new_sl = entry_price * 1.001  # Breakeven
                    reason = "compressed_breakeven"

            elif vol_regime == VolatilityRegime.NORMAL:
                # Standard trailing
                if pnl_pct >= 4.0:
                    new_sl = entry_price + (gain_amount * 0.5)
                    reason = f"normal_lock_50pct@{pnl_pct:.1f}%"
                elif pnl_pct >= 2.0:
                    new_sl = entry_price + (gain_amount * 0.3)
                    reason = f"normal_lock_30pct@{pnl_pct:.1f}%"
                elif pnl_pct >= 1.0:
                    new_sl = entry_price * 1.001
                    reason = "normal_breakeven"

            elif vol_regime == VolatilityRegime.EXPANDING:
                # Give more room
                if pnl_pct >= 6.0:
                    new_sl = entry_price + (gain_amount * 0.4)
                    reason = f"expanding_lock_40pct@{pnl_pct:.1f}%"
                elif pnl_pct >= 3.0:
                    new_sl = entry_price + (gain_amount * 0.2)
                    reason = f"expanding_lock_20pct@{pnl_pct:.1f}%"
                elif pnl_pct >= 1.5:
                    new_sl = entry_price * 1.001
                    reason = "expanding_breakeven"

            else:  # EXPLOSIVE
                # Very wide - let momentum run
                if pnl_pct >= 8.0:
                    new_sl = entry_price + (gain_amount * 0.35)
                    reason = f"explosive_lock_35pct@{pnl_pct:.1f}%"
                elif pnl_pct >= 4.0:
                    new_sl = entry_price + (gain_amount * 0.15)
                    reason = f"explosive_lock_15pct@{pnl_pct:.1f}%"
                elif pnl_pct >= 2.5:
                    new_sl = entry_price * 1.001
                    reason = "explosive_breakeven"

            # Only move SL up, never down
            if new_sl and new_sl > current_sl:
                return new_sl, reason

        else:  # short
            gain_amount = entry_price - best_price

            if vol_regime == VolatilityRegime.COMPRESSED:
                if pnl_pct >= 2.0:
                    new_sl = entry_price - (gain_amount * 0.6)
                    reason = f"compressed_lock_60pct@{pnl_pct:.1f}%"
                elif pnl_pct >= 1.0:
                    new_sl = entry_price - (gain_amount * 0.4)
                    reason = f"compressed_lock_40pct@{pnl_pct:.1f}%"
                elif pnl_pct >= 0.5:
                    new_sl = entry_price * 0.999
                    reason = "compressed_breakeven"

            elif vol_regime == VolatilityRegime.NORMAL:
                if pnl_pct >= 4.0:
                    new_sl = entry_price - (gain_amount * 0.5)
                    reason = f"normal_lock_50pct@{pnl_pct:.1f}%"
                elif pnl_pct >= 2.0:
                    new_sl = entry_price - (gain_amount * 0.3)
                    reason = f"normal_lock_30pct@{pnl_pct:.1f}%"
                elif pnl_pct >= 1.0:
                    new_sl = entry_price * 0.999
                    reason = "normal_breakeven"

            elif vol_regime == VolatilityRegime.EXPANDING:
                if pnl_pct >= 6.0:
                    new_sl = entry_price - (gain_amount * 0.4)
                    reason = f"expanding_lock_40pct@{pnl_pct:.1f}%"
                elif pnl_pct >= 3.0:
                    new_sl = entry_price - (gain_amount * 0.2)
                    reason = f"expanding_lock_20pct@{pnl_pct:.1f}%"
                elif pnl_pct >= 1.5:
                    new_sl = entry_price * 0.999
                    reason = "expanding_breakeven"

            else:  # EXPLOSIVE
                if pnl_pct >= 8.0:
                    new_sl = entry_price - (gain_amount * 0.35)
                    reason = f"explosive_lock_35pct@{pnl_pct:.1f}%"
                elif pnl_pct >= 4.0:
                    new_sl = entry_price - (gain_amount * 0.15)
                    reason = f"explosive_lock_15pct@{pnl_pct:.1f}%"
                elif pnl_pct >= 2.5:
                    new_sl = entry_price * 0.999
                    reason = "explosive_breakeven"

            # Only move SL down, never up (for shorts)
            if new_sl and new_sl < current_sl:
                return new_sl, reason

        return None, ""

    def _calc_ema(self, data: List[float], period: int) -> float:
        """Calculate EMA for given period."""
        if not data or period <= 0:
            return 0

        period = min(period, len(data))
        multiplier = 2 / (period + 1)

        # Start with SMA
        ema = sum(data[:period]) / period

        # Apply EMA formula
        for price in data[period:]:
            ema = (price * multiplier) + (ema * (1 - multiplier))

        return ema

    def _generate_reasoning(
        self,
        triggers: List[str],
        momentum: MomentumState,
        vol_regime: VolatilityRegime,
        confidence: float
    ) -> str:
        """Generate human-readable reasoning for the scan result."""
        if not triggers:
            return "No entry triggers detected"

        parts = [
            f"Momentum: {momentum.value}",
            f"Volatility: {vol_regime.value}",
            f"Triggers: {', '.join(triggers)}",
            f"Confidence: {confidence:.0%}"
        ]

        return " | ".join(parts)

