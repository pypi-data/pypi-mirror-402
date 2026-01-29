"""
Adaptive Parameters - Context-Aware Indicator Thresholds

The same RSI value means different things in different regimes:
- RSI 70 in a strong uptrend = normal, not overbought
- RSI 70 in a range = overbought, expect pullback

This module dynamically adjusts indicator thresholds based on:
1. Market Regime (trending, ranging, volatile)
2. Volatility Level
3. Recent Price Action
4. Time of Day / Market Session

Using static thresholds is like using one-size-fits-all clothing.
Adaptive parameters FIT the current market conditions.
"""

import logging
from typing import Dict, Any, List
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class MarketRegime(Enum):
    """Market regime classifications."""
    STRONG_UPTREND = "strong_uptrend"
    UPTREND = "uptrend"
    RANGING = "ranging"
    DOWNTREND = "downtrend"
    STRONG_DOWNTREND = "strong_downtrend"
    HIGH_VOLATILITY = "high_volatility"


@dataclass
class AdaptiveThresholds:
    """Dynamic thresholds that adapt to market conditions."""
    # RSI thresholds
    rsi_overbought: float = 70
    rsi_oversold: float = 30
    rsi_extreme_overbought: float = 80
    rsi_extreme_oversold: float = 20
    
    # Trend strength thresholds
    adx_trending: float = 25
    adx_strong_trend: float = 40
    
    # Bollinger Band position
    bb_overbought: float = 0.8  # Above 80% of band
    bb_oversold: float = 0.2   # Below 20% of band
    
    # Stop loss / Take profit multipliers
    stop_loss_atr_mult: float = 1.5
    take_profit_atr_mult: float = 2.0
    
    # Position sizing multiplier
    size_multiplier: float = 1.0
    
    # Confidence threshold for entry
    min_confidence: float = 0.6


# Regime-specific parameter presets
REGIME_PARAMETERS = {
    MarketRegime.STRONG_UPTREND: AdaptiveThresholds(
        rsi_overbought=80,      # Higher in strong trends
        rsi_oversold=40,        # RSI rarely goes below 40
        rsi_extreme_overbought=90,
        rsi_extreme_oversold=35,
        adx_trending=20,        # Lower threshold (already trending)
        adx_strong_trend=35,
        bb_overbought=0.95,     # Expect price to ride upper band
        bb_oversold=0.5,
        stop_loss_atr_mult=2.0, # Wider stops in trends
        take_profit_atr_mult=3.0,  # Let winners run
        size_multiplier=1.2,    # Larger size with trend
        min_confidence=0.5      # Lower bar for trend entries
    ),
    MarketRegime.UPTREND: AdaptiveThresholds(
        rsi_overbought=75,
        rsi_oversold=35,
        rsi_extreme_overbought=85,
        rsi_extreme_oversold=25,
        adx_trending=22,
        adx_strong_trend=35,
        bb_overbought=0.85,
        bb_oversold=0.3,
        stop_loss_atr_mult=1.75,
        take_profit_atr_mult=2.5,
        size_multiplier=1.1,
        min_confidence=0.55
    ),
    MarketRegime.RANGING: AdaptiveThresholds(
        rsi_overbought=65,      # Tighter in ranges
        rsi_oversold=35,
        rsi_extreme_overbought=75,
        rsi_extreme_oversold=25,
        adx_trending=30,        # Higher threshold (need confirmation)
        adx_strong_trend=45,
        bb_overbought=0.75,     # Mean reversion expected
        bb_oversold=0.25,
        stop_loss_atr_mult=1.0, # Tighter stops
        take_profit_atr_mult=1.5,  # Quick profits
        size_multiplier=0.8,    # Smaller size
        min_confidence=0.65     # Need more confirmation
    ),
    MarketRegime.DOWNTREND: AdaptiveThresholds(
        rsi_overbought=60,      # Lower (bounces are weak)
        rsi_oversold=25,
        rsi_extreme_overbought=70,
        rsi_extreme_oversold=15,
        adx_trending=22,
        adx_strong_trend=35,
        bb_overbought=0.7,
        bb_oversold=0.15,
        stop_loss_atr_mult=1.75,
        take_profit_atr_mult=2.5,
        size_multiplier=1.1,    # Can be aggressive shorting
        min_confidence=0.55
    ),
    MarketRegime.STRONG_DOWNTREND: AdaptiveThresholds(
        rsi_overbought=55,
        rsi_oversold=20,
        rsi_extreme_overbought=65,
        rsi_extreme_oversold=10,
        adx_trending=20,
        adx_strong_trend=35,
        bb_overbought=0.5,      # Price rides lower band
        bb_oversold=0.05,
        stop_loss_atr_mult=2.0,
        take_profit_atr_mult=3.0,
        size_multiplier=1.2,
        min_confidence=0.5
    ),
    MarketRegime.HIGH_VOLATILITY: AdaptiveThresholds(
        rsi_overbought=75,      # RSI swings wildly
        rsi_oversold=25,
        rsi_extreme_overbought=85,
        rsi_extreme_oversold=15,
        adx_trending=30,        # Need stronger confirmation
        adx_strong_trend=50,
        bb_overbought=0.9,
        bb_oversold=0.1,
        stop_loss_atr_mult=2.5, # Much wider stops
        take_profit_atr_mult=4.0,  # Big moves possible
        size_multiplier=0.5,    # REDUCE SIZE
        min_confidence=0.75     # Need high confidence
    )
}


def detect_regime(
    candles: List[Dict],
    adx: float = None,
    atr_ratio: float = None
) -> MarketRegime:
    """
    Detect current market regime from price data.

    Args:
        candles: OHLCV data (50+ recommended)
        adx: Pre-calculated ADX value (optional)
        atr_ratio: ATR relative to recent average (optional)

    Returns:
        MarketRegime enum value
    """
    if len(candles) < 20:
        return MarketRegime.RANGING

    # Calculate basics if not provided
    closes = [c.get("close", c.get("c", 0)) for c in candles]
    highs = [c.get("high", c.get("h", 0)) for c in candles]
    lows = [c.get("low", c.get("l", 0)) for c in candles]

    # Simple trend detection using EMAs
    def ema(data, period):
        if len(data) < period:
            return sum(data) / len(data)
        k = 2 / (period + 1)
        result = sum(data[:period]) / period
        for price in data[period:]:
            result = price * k + result * (1 - k)
        return result

    ema20 = ema(closes, 20)
    ema50 = ema(closes, 50) if len(closes) >= 50 else ema20
    current_price = closes[-1]

    # Price position relative to EMAs
    above_ema20 = current_price > ema20
    above_ema50 = current_price > ema50
    ema20_above_ema50 = ema20 > ema50

    # Calculate price change over last 20 candles
    price_change_20 = (closes[-1] - closes[-20]) / closes[-20] * 100 if len(closes) >= 20 else 0

    # Calculate volatility (ATR-like)
    if atr_ratio is None:
        true_ranges = []
        for i in range(1, len(candles)):
            tr = max(
                highs[i] - lows[i],
                abs(highs[i] - closes[i-1]),
                abs(lows[i] - closes[i-1])
            )
            true_ranges.append(tr)

        if len(true_ranges) >= 20:
            recent_atr_val = sum(true_ranges[-5:]) / 5
            avg_atr = sum(true_ranges[-20:]) / 20
            atr_ratio = recent_atr_val / avg_atr if avg_atr > 0 else 1.0
        else:
            atr_ratio = 1.0

    # Check for high volatility first (overrides other conditions)
    if atr_ratio > 1.5:
        return MarketRegime.HIGH_VOLATILITY

    # Determine trend based on EMAs and price action
    if above_ema20 and above_ema50 and ema20_above_ema50:
        if price_change_20 > 5 or (adx and adx > 35):
            return MarketRegime.STRONG_UPTREND
        elif price_change_20 > 2:
            return MarketRegime.UPTREND

    if not above_ema20 and not above_ema50 and not ema20_above_ema50:
        if price_change_20 < -5 or (adx and adx > 35):
            return MarketRegime.STRONG_DOWNTREND
        elif price_change_20 < -2:
            return MarketRegime.DOWNTREND

    return MarketRegime.RANGING


def get_adaptive_thresholds(
    candles: List[Dict] = None,
    regime: MarketRegime = None,
    adx: float = None,
    atr_ratio: float = None,
    volatility_pct: float = None
) -> AdaptiveThresholds:
    """
    Get adaptive thresholds for the current market conditions.

    Args:
        candles: OHLCV data for regime detection
        regime: Pre-determined regime (optional)
        adx: ADX value for fine-tuning
        atr_ratio: ATR ratio for volatility adjustment
        volatility_pct: Daily volatility percentage

    Returns:
        AdaptiveThresholds configured for current conditions
    """
    # Detect regime if not provided
    if regime is None:
        if candles:
            regime = detect_regime(candles, adx, atr_ratio)
        else:
            regime = MarketRegime.RANGING

    # Get base thresholds for this regime
    thresholds = REGIME_PARAMETERS.get(regime, REGIME_PARAMETERS[MarketRegime.RANGING])

    # Fine-tune based on additional factors
    if atr_ratio:
        # Adjust stops based on current volatility
        if atr_ratio > 1.3:
            thresholds.stop_loss_atr_mult *= 1.2
            thresholds.take_profit_atr_mult *= 1.2
            thresholds.size_multiplier *= 0.8
        elif atr_ratio < 0.7:
            thresholds.stop_loss_atr_mult *= 0.9
            thresholds.take_profit_atr_mult *= 0.9

    # Adjust for ADX strength
    if adx:
        if adx > 40:  # Very strong trend
            thresholds.min_confidence *= 0.9  # Lower bar
            thresholds.size_multiplier *= 1.1
        elif adx < 15:  # Very weak trend
            thresholds.min_confidence *= 1.1  # Higher bar
            thresholds.size_multiplier *= 0.9

    return thresholds


def apply_adaptive_analysis(
    signal: Dict[str, Any],
    candles: List[Dict],
    rsi: float = None,
    bb_position: float = None,
    adx: float = None
) -> Dict[str, Any]:
    """
    Apply adaptive analysis to a trading signal.

    Adjusts confidence and recommendations based on regime-appropriate thresholds.

    Args:
        signal: Original trading signal dict
        candles: OHLCV data
        rsi: Current RSI value
        bb_position: Bollinger Band position (0-1)
        adx: ADX value

    Returns:
        Enhanced signal with adaptive adjustments
    """
    # Detect regime and get thresholds
    regime = detect_regime(candles, adx)
    thresholds = get_adaptive_thresholds(candles, regime, adx)

    # Copy signal to avoid mutation
    result = signal.copy()
    result["regime"] = regime.value
    result["adaptive_thresholds"] = {
        "rsi_overbought": thresholds.rsi_overbought,
        "rsi_oversold": thresholds.rsi_oversold,
        "min_confidence": thresholds.min_confidence,
        "size_multiplier": thresholds.size_multiplier,
        "stop_atr_mult": thresholds.stop_loss_atr_mult,
        "tp_atr_mult": thresholds.take_profit_atr_mult
    }

    # Adjust signal based on adaptive thresholds
    adjustments = []
    confidence_modifier = 1.0

    if rsi is not None:
        if rsi > thresholds.rsi_extreme_overbought:
            if signal.get("bias") == "bullish":
                adjustments.append(f"RSI {rsi:.0f} extreme for {regime.value} - reduce confidence")
                confidence_modifier *= 0.7
            else:
                adjustments.append(f"RSI {rsi:.0f} extreme - supports bearish")
                confidence_modifier *= 1.1
        elif rsi < thresholds.rsi_extreme_oversold:
            if signal.get("bias") == "bearish":
                adjustments.append(f"RSI {rsi:.0f} extreme for {regime.value} - reduce confidence")
                confidence_modifier *= 0.7
            else:
                adjustments.append(f"RSI {rsi:.0f} extreme - supports bullish")
                confidence_modifier *= 1.1
        elif rsi > thresholds.rsi_overbought:
            adjustments.append(f"RSI {rsi:.0f} overbought for {regime.value}")
            if signal.get("bias") == "bullish":
                confidence_modifier *= 0.85
        elif rsi < thresholds.rsi_oversold:
            adjustments.append(f"RSI {rsi:.0f} oversold for {regime.value}")
            if signal.get("bias") == "bearish":
                confidence_modifier *= 0.85

    if bb_position is not None:
        if bb_position > thresholds.bb_overbought:
            adjustments.append(f"BB position {bb_position:.0%} high for {regime.value}")
            if signal.get("bias") == "bullish" and regime != MarketRegime.STRONG_UPTREND:
                confidence_modifier *= 0.9
        elif bb_position < thresholds.bb_oversold:
            adjustments.append(f"BB position {bb_position:.0%} low for {regime.value}")
            if signal.get("bias") == "bearish" and regime != MarketRegime.STRONG_DOWNTREND:
                confidence_modifier *= 0.9

    # Apply confidence modifier
    original_conf = signal.get("confidence", 0.5)
    adjusted_conf = min(original_conf * confidence_modifier, 1.0)
    result["confidence"] = round(adjusted_conf, 2)
    result["original_confidence"] = original_conf
    result["confidence_modifier"] = round(confidence_modifier, 2)
    result["adjustments"] = adjustments

    # Determine if signal meets adaptive threshold
    result["meets_threshold"] = adjusted_conf >= thresholds.min_confidence
    result["size_multiplier"] = thresholds.size_multiplier

    return result
