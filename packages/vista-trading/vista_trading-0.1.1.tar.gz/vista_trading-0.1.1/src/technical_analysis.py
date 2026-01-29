"""
Technical Analysis Module - RSI, EMA, Volume Profile calculations.
"""

import logging
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)


def _calc_ema(data: List[float], period: int) -> float:
    """Calculate EMA (Exponential Moving Average) and return the final value.

    Args:
        data: List of prices (closes)
        period: EMA period

    Returns:
        Current EMA value
    """
    if len(data) < period:
        return sum(data) / len(data) if data else 0.0

    multiplier = 2 / (period + 1)
    ema = sum(data[:period]) / period  # SMA for first value

    for price in data[period:]:
        ema = (price * multiplier) + (ema * (1 - multiplier))

    return ema


def calculate_rsi(candles: List[Dict], period: int = 14) -> Optional[float]:
    """Calculate RSI (Relative Strength Index).
    
    Args:
        candles: List of candle dicts with 'close' prices
        period: RSI period (default 14)
        
    Returns:
        RSI value 0-100, or None if insufficient data
    """
    if len(candles) < period + 1:
        return None
    
    closes = [c["close"] for c in candles]
    
    # Calculate price changes
    gains = []
    losses = []
    
    for i in range(1, len(closes)):
        change = closes[i] - closes[i-1]
        if change > 0:
            gains.append(change)
            losses.append(0)
        else:
            gains.append(0)
            losses.append(abs(change))
    
    # Use last 'period' changes
    recent_gains = gains[-period:]
    recent_losses = losses[-period:]
    
    avg_gain = sum(recent_gains) / period
    avg_loss = sum(recent_losses) / period
    
    if avg_loss == 0:
        return 100.0
    
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    
    return round(rsi, 2)


def calculate_ema(candles: List[Dict], period: int) -> Optional[float]:
    """Calculate EMA (Exponential Moving Average).
    
    Args:
        candles: List of candle dicts with 'close' prices
        period: EMA period
        
    Returns:
        EMA value or None if insufficient data
    """
    if len(candles) < period:
        return None
    
    closes = [c["close"] for c in candles]
    multiplier = 2 / (period + 1)
    
    # Start with SMA for first EMA value
    ema = sum(closes[:period]) / period
    
    # Calculate EMA for remaining values
    for price in closes[period:]:
        ema = (price * multiplier) + (ema * (1 - multiplier))
    
    return round(ema, 2)


def calculate_ema_crossover(candles: List[Dict], fast: int = 9, slow: int = 21) -> Dict[str, Any]:
    """Calculate EMA crossover signals.
    
    Args:
        candles: List of candle dicts
        fast: Fast EMA period (default 9)
        slow: Slow EMA period (default 21)
        
    Returns:
        Dict with ema_fast, ema_slow, signal (bullish/bearish/neutral)
    """
    ema_fast = calculate_ema(candles, fast)
    ema_slow = calculate_ema(candles, slow)
    
    if ema_fast is None or ema_slow is None:
        return {"ema_fast": None, "ema_slow": None, "signal": "neutral", "spread_pct": 0}
    
    spread_pct = ((ema_fast - ema_slow) / ema_slow) * 100
    
    if ema_fast > ema_slow:
        signal = "bullish"
    elif ema_fast < ema_slow:
        signal = "bearish"
    else:
        signal = "neutral"
    
    return {
        "ema_fast": ema_fast,
        "ema_slow": ema_slow,
        "signal": signal,
        "spread_pct": round(spread_pct, 3)
    }


def calculate_volume_profile(candles: List[Dict], bins: int = 10) -> Dict[str, Any]:
    """Calculate volume profile - where most volume occurred.
    
    Args:
        candles: List of candle dicts with high, low, volume
        bins: Number of price bins
        
    Returns:
        Dict with volume distribution and POC (point of control)
    """
    if not candles:
        return {"poc": None, "high_volume_zone": None, "profile": "neutral"}
    
    # Get price range
    all_highs = [c["high"] for c in candles]
    all_lows = [c["low"] for c in candles]
    total_volume = sum(c["volume"] for c in candles)
    
    price_high = max(all_highs)
    price_low = min(all_lows)
    price_range = price_high - price_low
    
    if price_range == 0 or total_volume == 0:
        return {"poc": price_high, "high_volume_zone": "middle", "profile": "neutral"}
    
    bin_size = price_range / bins
    volume_by_bin = [0] * bins
    
    # Distribute volume across bins
    for c in candles:
        mid_price = (c["high"] + c["low"]) / 2
        bin_idx = min(int((mid_price - price_low) / bin_size), bins - 1)
        volume_by_bin[bin_idx] += c["volume"]
    
    # Find POC (highest volume bin)
    max_vol_idx = volume_by_bin.index(max(volume_by_bin))
    poc = price_low + (max_vol_idx + 0.5) * bin_size
    
    # Determine if volume is concentrated high, low, or middle
    current_price = candles[-1]["close"]
    if poc > current_price * 1.01:
        zone = "above"  # Resistance
    elif poc < current_price * 0.99:
        zone = "below"  # Support
    else:
        zone = "at_price"
    
    return {
        "poc": round(poc, 2),
        "high_volume_zone": zone,
        "total_volume": round(total_volume, 2),
        "profile": "bullish" if zone == "below" else "bearish" if zone == "above" else "neutral"
    }


def calculate_macd(candles: List[Dict], fast: int = 12, slow: int = 26, signal: int = 9) -> Dict[str, Any]:
    """Calculate MACD (Moving Average Convergence Divergence).

    Args:
        candles: List of candle dicts with 'close' prices
        fast: Fast EMA period (default 12)
        slow: Slow EMA period (default 26)
        signal: Signal line period (default 9)

    Returns:
        Dict with macd_line, signal_line, histogram, and signal
    """
    if len(candles) < slow + signal:
        return {"macd_line": None, "signal_line": None, "histogram": None, "signal": "neutral"}

    closes = [c["close"] for c in candles]

    # Calculate EMAs
    def ema_series(data: List[float], period: int) -> List[float]:
        multiplier = 2 / (period + 1)
        ema_values = []
        ema = sum(data[:period]) / period
        ema_values.append(ema)
        for price in data[period:]:
            ema = (price * multiplier) + (ema * (1 - multiplier))
            ema_values.append(ema)
        return ema_values

    ema_fast = ema_series(closes, fast)
    ema_slow = ema_series(closes, slow)

    # Align lengths and calculate MACD line
    offset = slow - fast
    macd_line = [ema_fast[i + offset] - ema_slow[i] for i in range(len(ema_slow))]

    # Calculate signal line (EMA of MACD)
    if len(macd_line) < signal:
        return {"macd_line": None, "signal_line": None, "histogram": None, "signal": "neutral"}

    signal_line = ema_series(macd_line, signal)

    # Get current values
    current_macd = macd_line[-1]
    current_signal = signal_line[-1]
    histogram = current_macd - current_signal

    # Previous values for crossover detection
    prev_macd = macd_line[-2] if len(macd_line) > 1 else current_macd
    prev_signal = signal_line[-2] if len(signal_line) > 1 else current_signal

    # Determine signal
    if current_macd > current_signal and prev_macd <= prev_signal:
        sig = "bullish_cross"
    elif current_macd < current_signal and prev_macd >= prev_signal:
        sig = "bearish_cross"
    elif current_macd > current_signal:
        sig = "bullish"
    elif current_macd < current_signal:
        sig = "bearish"
    else:
        sig = "neutral"

    return {
        "macd_line": round(current_macd, 4),
        "signal_line": round(current_signal, 4),
        "histogram": round(histogram, 4),
        "signal": sig
    }


def calculate_bollinger_bands(candles: List[Dict], period: int = 20, std_dev: float = 2.0) -> Dict[str, Any]:
    """Calculate Bollinger Bands.

    Args:
        candles: List of candle dicts with 'close' prices
        period: Moving average period (default 20)
        std_dev: Standard deviation multiplier (default 2.0)

    Returns:
        Dict with upper, middle, lower bands and position signal
    """
    if len(candles) < period:
        return {"upper": None, "middle": None, "lower": None, "signal": "neutral", "bandwidth": None}

    closes = [c["close"] for c in candles[-period:]]
    current_price = candles[-1]["close"]

    # Calculate SMA (middle band)
    middle = sum(closes) / period

    # Calculate standard deviation
    variance = sum((p - middle) ** 2 for p in closes) / period
    std = variance ** 0.5

    # Calculate bands
    upper = middle + (std_dev * std)
    lower = middle - (std_dev * std)

    # Bandwidth (volatility indicator)
    bandwidth = ((upper - lower) / middle) * 100

    # Position within bands (0 = lower, 1 = upper)
    band_position = (current_price - lower) / (upper - lower) if upper != lower else 0.5

    # Determine signal
    if band_position >= 0.95:
        sig = "overbought"  # Near upper band
    elif band_position <= 0.05:
        sig = "oversold"  # Near lower band
    elif band_position > 0.5:
        sig = "upper_half"
    else:
        sig = "lower_half"

    return {
        "upper": round(upper, 2),
        "middle": round(middle, 2),
        "lower": round(lower, 2),
        "bandwidth": round(bandwidth, 2),
        "band_position": round(band_position, 3),
        "signal": sig
    }


def calculate_support_resistance(candles: List[Dict], lookback: int = 50) -> Dict[str, Any]:
    """Calculate key support and resistance levels using pivot points, swing highs/lows,
    AND consolidation zone detection.

    Args:
        candles: List of candle dicts
        lookback: Number of candles to analyze

    Returns:
        Dict with support/resistance levels and proximity signals
    """
    if len(candles) < lookback:
        lookback = len(candles)

    recent = candles[-lookback:]
    current_price = candles[-1]["close"]

    highs = [c["high"] for c in recent]
    lows = [c["low"] for c in recent]

    # Find swing highs and lows (local extremes)
    swing_highs = []
    swing_lows = []

    for i in range(2, len(recent) - 2):
        # Swing high: higher than 2 candles on each side
        if highs[i] > highs[i-1] and highs[i] > highs[i-2] and highs[i] > highs[i+1] and highs[i] > highs[i+2]:
            swing_highs.append(highs[i])
        # Swing low: lower than 2 candles on each side
        if lows[i] < lows[i-1] and lows[i] < lows[i-2] and lows[i] < lows[i+1] and lows[i] < lows[i+2]:
            swing_lows.append(lows[i])

    # === NEW: CONSOLIDATION ZONE DETECTION ===
    # Look at recent candles (last 10-15) to detect if price is building support/resistance
    # through consolidation (multiple touches at similar levels)
    consolidation_lookback = min(15, len(recent))
    recent_candles = recent[-consolidation_lookback:]
    recent_lows = [c["low"] for c in recent_candles]
    recent_highs = [c["high"] for c in recent_candles]

    # Calculate consolidation zone boundaries
    consol_low = min(recent_lows)
    consol_high = max(recent_highs)
    consol_range_pct = (consol_high - consol_low) / current_price * 100

    # Detect consolidation: range < 1.5% = tight consolidation building S/R
    # KEY INSIGHT: In consolidation, the LOW is support, the HIGH is resistance
    # Don't short near the low, don't long near the high!
    consolidation_zone = None
    is_building_support = False
    is_building_resistance = False

    if consol_range_pct < 1.5:  # Tight consolidation (< 1.5% range)
        # Count touches at low and high of range (within 0.15% - widened for BTC)
        touch_threshold = current_price * 0.0015  # 0.15%
        low_touches = sum(1 for l in recent_lows if abs(l - consol_low) < touch_threshold)
        high_touches = sum(1 for h in recent_highs if abs(h - consol_high) < touch_threshold)

        # Distance to consolidation boundaries
        dist_to_consol_low_pct = (current_price - consol_low) / current_price * 100
        dist_to_consol_high_pct = (consol_high - current_price) / current_price * 100

        # Price in LOWER HALF of consolidation = building support (avoid shorts!)
        # Use 50% threshold - if price is in lower half, we're near support
        if current_price < consol_low + (consol_high - consol_low) * 0.5:
            is_building_support = True
            consolidation_zone = {
                "type": "support_building",
                "level": consol_low,
                "touches": low_touches,
                "range_pct": consol_range_pct,
                "dist_to_level_pct": dist_to_consol_low_pct
            }
        # Price in UPPER HALF of consolidation = building resistance (avoid longs!)
        else:
            is_building_resistance = True
            consolidation_zone = {
                "type": "resistance_building",
                "level": consol_high,
                "touches": high_touches,
                "range_pct": consol_range_pct,
                "dist_to_level_pct": dist_to_consol_high_pct
            }
    elif consol_range_pct < 2.5:
        # Wider consolidation - still track it but weaker signal
        consolidation_zone = {
            "type": "wide_consolidation",
            "low": consol_low,
            "high": consol_high,
            "range_pct": consol_range_pct
        }

    # Get key levels from swing points
    resistances = sorted(set(swing_highs), reverse=True)[:3] if swing_highs else [max(highs)]
    supports = sorted(set(swing_lows))[:3] if swing_lows else [min(lows)]

    # If consolidation detected, ADD consolidation levels to S/R
    if is_building_support and consol_low not in supports:
        supports = [consol_low] + supports[:2]  # Prioritize consolidation support
    if is_building_resistance and consol_high not in resistances:
        resistances = [consol_high] + resistances[:2]  # Prioritize consolidation resistance

    # Find nearest levels
    nearest_resistance = min((r for r in resistances if r > current_price), default=max(highs))
    nearest_support = max((s for s in supports if s < current_price), default=min(lows))

    # Calculate distance to levels
    dist_to_resistance = ((nearest_resistance - current_price) / current_price) * 100
    dist_to_support = ((current_price - nearest_support) / current_price) * 100

    # Signal based on proximity - TIGHTER thresholds for crypto (0.5% not 1%)
    # Consolidation is separate - don't conflate with actual S/R level proximity
    if dist_to_resistance < 0.5:
        sig = "near_resistance"
    elif dist_to_support < 0.5:
        sig = "near_support"
    elif is_building_support and dist_to_support < 1.0:
        sig = "consolidating_support"  # Separate signal - not as strong
    elif is_building_resistance and dist_to_resistance < 1.0:
        sig = "consolidating_resistance"  # Separate signal - not as strong
    else:
        sig = "mid_range"

    return {
        "nearest_resistance": round(nearest_resistance, 2),
        "nearest_support": round(nearest_support, 2),
        "dist_to_resistance_pct": round(dist_to_resistance, 2),
        "dist_to_support_pct": round(dist_to_support, 2),
        "resistances": [round(r, 2) for r in resistances],
        "supports": [round(s, 2) for s in supports],
        "signal": sig,
        "consolidation_zone": consolidation_zone,
        "is_building_support": is_building_support,
        "is_building_resistance": is_building_resistance
    }


def calculate_atr(candles: List[Dict], period: int = 14) -> Optional[float]:
    """Calculate Average True Range (ATR) for volatility.

    Args:
        candles: List of candle dicts
        period: ATR period (default 14)

    Returns:
        ATR value or None
    """
    if len(candles) < period + 1:
        return None

    true_ranges = []
    for i in range(1, len(candles)):
        high = candles[i]["high"]
        low = candles[i]["low"]
        prev_close = candles[i-1]["close"]

        tr = max(
            high - low,
            abs(high - prev_close),
            abs(low - prev_close)
        )
        true_ranges.append(tr)

    # Use last 'period' true ranges
    recent_tr = true_ranges[-period:]
    atr = sum(recent_tr) / period

    return round(atr, 4)


def detect_trendlines(candles: List[Dict], lookback: int = 50, min_touches: int = 2,
                      tolerance_pct: float = 0.008, min_slope_pct: float = 0.02,
                      min_signal_strength: float = 0.5) -> Dict[str, Any]:
    """Detect ascending/descending trendlines from swing points.

    Finds diagonal support (ascending lows) and resistance (descending highs).

    IMPROVED: Now includes trend filter and breach validation to reduce false signals.

    Args:
        candles: List of candle dicts with OHLC
        lookback: Number of candles to analyze
        min_touches: Minimum touches to confirm trendline
        tolerance_pct: How close a point must be to the line to count as a touch (default 0.8%)
        min_slope_pct: Minimum slope %/candle for ascending support (default 0.02%)
        min_signal_strength: Minimum strength threshold for actionable signals (default 0.5)

    Returns:
        Dict with trendline data and signals
    """
    if len(candles) < lookback:
        lookback = len(candles)
    if lookback < 10:
        return {"ascending_support": None, "descending_resistance": None, "signal": "insufficient_data",
                "trend_filter": "insufficient_data", "breach_count": 0}

    recent = candles[-lookback:]
    current_price = recent[-1]["close"]
    current_idx = len(recent) - 1

    # Find swing lows (for ascending support) - standard 2-candle confirmation
    swing_lows = []
    for i in range(2, len(recent) - 2):
        if (recent[i]["low"] < recent[i-1]["low"] and
            recent[i]["low"] < recent[i-2]["low"] and
            recent[i]["low"] < recent[i+1]["low"] and
            recent[i]["low"] < recent[i+2]["low"]):
            swing_lows.append({"idx": i, "price": recent[i]["low"], "time": recent[i].get("t", i)})

    # Find swing highs (for descending resistance) - standard 2-candle confirmation
    swing_highs = []
    for i in range(2, len(recent) - 2):
        if (recent[i]["high"] > recent[i-1]["high"] and
            recent[i]["high"] > recent[i-2]["high"] and
            recent[i]["high"] > recent[i+1]["high"] and
            recent[i]["high"] > recent[i+2]["high"]):
            swing_highs.append({"idx": i, "price": recent[i]["high"], "time": recent[i].get("t", i)})

    # Also check for "soft" swing points in the last 5 candles (1-candle confirmation)
    # This helps capture current trends that aren't fully confirmed yet
    for i in range(max(1, len(recent) - 5), len(recent) - 1):
        # Soft swing low: lower than immediate neighbors
        if (recent[i]["low"] < recent[i-1]["low"] and
            recent[i]["low"] < recent[i+1]["low"]):
            # Check it's not already in swing_lows
            if not any(sl["idx"] == i for sl in swing_lows):
                swing_lows.append({"idx": i, "price": recent[i]["low"], "time": recent[i].get("t", i), "soft": True})

        # Soft swing high: higher than immediate neighbors
        if (recent[i]["high"] > recent[i-1]["high"] and
            recent[i]["high"] > recent[i+1]["high"]):
            if not any(sh["idx"] == i for sh in swing_highs):
                swing_highs.append({"idx": i, "price": recent[i]["high"], "time": recent[i].get("t", i), "soft": True})

    # Also add the most recent candle as potential endpoint if it's at an extreme
    last_idx = len(recent) - 1
    last_candle = recent[-1]
    recent_5_lows = [c["low"] for c in recent[-5:]]
    recent_5_highs = [c["high"] for c in recent[-5:]]

    # If current candle has the lowest low in last 5, add it
    if last_candle["low"] == min(recent_5_lows):
        if not any(sl["idx"] == last_idx for sl in swing_lows):
            swing_lows.append({"idx": last_idx, "price": last_candle["low"], "time": last_candle.get("t", last_idx), "current": True})

    # If current candle has the highest high in last 5, add it
    if last_candle["high"] == max(recent_5_highs):
        if not any(sh["idx"] == last_idx for sh in swing_highs):
            swing_highs.append({"idx": last_idx, "price": last_candle["high"], "time": last_candle.get("t", last_idx), "current": True})

    ascending_support = _find_best_trendline(swing_lows, current_idx, "ascending", min_touches, current_price, tolerance_pct, min_slope_pct)
    descending_resistance = _find_best_trendline(swing_highs, current_idx, "descending", min_touches, current_price, tolerance_pct, min_slope_pct)

    # Calculate current trendline prices (relative to start point)
    asc_price_now = None
    desc_price_now = None

    if ascending_support:
        # Price at current_idx = start_price + slope * (current_idx - start_idx)
        asc_price_now = ascending_support["start_price"] + ascending_support["slope"] * (current_idx - ascending_support["start_idx"])
        ascending_support["current_price"] = round(asc_price_now, 2)
        ascending_support["distance_pct"] = round((current_price - asc_price_now) / asc_price_now * 100, 3)

    if descending_resistance:
        desc_price_now = descending_resistance["start_price"] + descending_resistance["slope"] * (current_idx - descending_resistance["start_idx"])
        descending_resistance["current_price"] = round(desc_price_now, 2)
        descending_resistance["distance_pct"] = round((desc_price_now - current_price) / current_price * 100, 3)

    # ========== TREND FILTER: Calculate 21 EMA ==========
    closes = [c["close"] for c in recent]
    ema21 = _calc_ema(closes, 21)
    trend_filter = "bullish" if current_price > ema21 else "bearish"
    trend_strength = abs(current_price - ema21) / ema21 * 100  # How far from EMA

    # ========== BREACH VALIDATION: Count recent failures ==========
    # Count how many times price closed below support in last 10 candles
    support_breach_count = 0
    resistance_breach_count = 0

    if asc_price_now and ascending_support:
        slope = ascending_support["slope"]
        start_price = ascending_support["start_price"]
        start_idx = ascending_support["start_idx"]
        for i in range(max(0, len(recent) - 10), len(recent)):
            line_price_at_i = start_price + slope * (i - start_idx)
            if recent[i]["close"] < line_price_at_i * 0.995:  # Closed 0.5%+ below
                support_breach_count += 1

    if desc_price_now and descending_resistance:
        slope = descending_resistance["slope"]
        start_price = descending_resistance["start_price"]
        start_idx = descending_resistance["start_idx"]
        for i in range(max(0, len(recent) - 10), len(recent)):
            line_price_at_i = start_price + slope * (i - start_idx)
            if recent[i]["close"] > line_price_at_i * 1.005:  # Closed 0.5%+ above
                resistance_breach_count += 1

    # ========== Generate signal with IMPROVED validation ==========
    signal = "neutral"
    signal_strength = 0.0
    breakout_confidence = 0.0
    signal_valid = True  # Will be set to False if filters reject
    rejection_reason = None

    # Get recent candles for momentum/volume confirmation
    last_candle = recent[-1]
    prev_candle = recent[-2] if len(recent) > 1 else last_candle

    # Check if current candle is bearish (confirms breakdown) or bullish (confirms breakout)
    is_bearish_candle = last_candle["close"] < last_candle["open"]
    is_bullish_candle = last_candle["close"] > last_candle["open"]

    # Check momentum - are we accelerating through the level?
    candle_body_pct = abs(last_candle["close"] - last_candle["open"]) / last_candle["open"] * 100
    strong_momentum = candle_body_pct > 0.3  # 0.3%+ body = strong momentum

    # THRESHOLDS:
    AT_LEVEL_PCT = 0.005  # 0.5%
    BREAK_THRESHOLD_PCT = 0.005  # Must be beyond 0.5% to count as break
    CONFIRMED_BREAK_PCT = 0.01  # 1% = confirmed break

    # Check if price is near ascending support (within 0.5%)
    if asc_price_now and current_price <= asc_price_now * (1 + AT_LEVEL_PCT) and current_price >= asc_price_now * (1 - AT_LEVEL_PCT):
        signal = "at_ascending_support"
        base_strength = min(ascending_support.get("touches", 2) / 4, 1.0)

        # VALIDATION 1: Trend filter - support bounces work better in uptrends
        if trend_filter == "bearish":
            base_strength *= 0.5  # Halve confidence in downtrend
            rejection_reason = "support_in_downtrend"

        # VALIDATION 2: Breach count - don't trust support that's been breached
        if support_breach_count >= 2:
            base_strength *= 0.3  # Heavy penalty for breached support
            rejection_reason = f"support_breached_{support_breach_count}x"
        elif support_breach_count == 1:
            base_strength *= 0.6  # Moderate penalty

        signal_strength = base_strength

    # Check if price is near descending resistance (within 0.5%)
    elif desc_price_now and current_price >= desc_price_now * (1 - AT_LEVEL_PCT) and current_price <= desc_price_now * (1 + AT_LEVEL_PCT):
        signal = "at_descending_resistance"
        base_strength = min(descending_resistance.get("touches", 2) / 4, 1.0)

        # VALIDATION 1: Trend filter - resistance rejections work better in downtrends
        if trend_filter == "bullish":
            base_strength *= 0.5  # Halve confidence in uptrend
            rejection_reason = "resistance_in_uptrend"

        # VALIDATION 2: Breach count - don't trust resistance that's been breached
        if resistance_breach_count >= 2:
            base_strength *= 0.3
            rejection_reason = f"resistance_breached_{resistance_breach_count}x"
        elif resistance_breach_count == 1:
            base_strength *= 0.6

        signal_strength = base_strength

    # Check if breaking above descending resistance (CONFIRMED)
    elif desc_price_now and current_price > desc_price_now * (1 + BREAK_THRESHOLD_PCT):
        break_pct = (current_price - desc_price_now) / desc_price_now * 100

        if is_bullish_candle or strong_momentum or break_pct > CONFIRMED_BREAK_PCT * 100:
            signal = "breaking_resistance"
            breakout_confidence = min(break_pct / 1.5, 1.0)
            base_strength = 0.5 + (breakout_confidence * 0.5)
            if is_bullish_candle and strong_momentum:
                base_strength = min(base_strength + 0.2, 1.0)

            # Breakouts are more reliable when trend already confirms
            if trend_filter == "bullish":
                base_strength = min(base_strength + 0.1, 1.0)

            signal_strength = base_strength
        else:
            signal = "testing_resistance"
            signal_strength = 0.4

    # Check if breaking below ascending support (CONFIRMED)
    elif asc_price_now and current_price < asc_price_now * (1 - BREAK_THRESHOLD_PCT):
        break_pct = (asc_price_now - current_price) / asc_price_now * 100

        if is_bearish_candle or strong_momentum or break_pct > CONFIRMED_BREAK_PCT * 100:
            signal = "breaking_support"
            breakout_confidence = min(break_pct / 1.5, 1.0)
            base_strength = 0.5 + (breakout_confidence * 0.5)
            if is_bearish_candle and strong_momentum:
                base_strength = min(base_strength + 0.2, 1.0)

            # Breakdowns are more reliable when trend already confirms
            if trend_filter == "bearish":
                base_strength = min(base_strength + 0.1, 1.0)

            signal_strength = base_strength
        else:
            signal = "testing_support"
            signal_strength = 0.4

    # ========== FINAL FILTER: Minimum strength threshold ==========
    # Only emit actionable signals if strength meets threshold
    if signal_strength < min_signal_strength and signal != "neutral":
        signal_valid = False
        if not rejection_reason:
            rejection_reason = f"strength_below_{min_signal_strength}"

    return {
        "ascending_support": ascending_support,
        "descending_resistance": descending_resistance,
        "current_price": current_price,
        "signal": signal,
        "signal_strength": signal_strength,
        "signal_valid": signal_valid,  # NEW: Whether signal passes all filters
        "rejection_reason": rejection_reason,  # NEW: Why signal was invalidated
        "breakout_confidence": breakout_confidence,
        "swing_lows_count": len(swing_lows),
        "swing_highs_count": len(swing_highs),
        "trend_filter": trend_filter,  # NEW: Overall trend direction
        "trend_strength_pct": round(trend_strength, 2),  # NEW: Distance from EMA
        "support_breach_count": support_breach_count,  # NEW: Recent support failures
        "resistance_breach_count": resistance_breach_count,  # NEW: Recent resistance failures
        "ema21": round(ema21, 2)  # NEW: EMA value for reference
    }


def _find_best_trendline(points: List[Dict], current_idx: int, direction: str, min_touches: int,
                         current_price: float = None, tolerance_pct: float = 0.008,
                         min_slope_pct: float = 0.02) -> Optional[Dict]:
    """Find the best fitting trendline from swing points.

    Args:
        points: List of swing points with idx and price
        current_idx: Current candle index
        direction: "ascending" (for support) or "descending" (for resistance)
        min_touches: Minimum points that must touch the line
        current_price: Current price (to filter irrelevant lines)
        tolerance_pct: How close a point must be to the line to count as touch (default 0.8%)
        min_slope_pct: Minimum slope for ascending support (default 0.02%/candle)

    Returns:
        Best trendline dict or None
    """
    if len(points) < min_touches:
        return None

    best_line = None
    best_score = 0

    # Try all pairs of points to form trendlines
    for i in range(len(points)):
        for j in range(i + 1, len(points)):
            p1, p2 = points[i], points[j]

            # Calculate slope
            dx = p2["idx"] - p1["idx"]
            if dx == 0:
                continue
            slope = (p2["price"] - p1["price"]) / dx

            # SLOPE DIRECTION CHECK:
            # - Ascending support: slope must be positive (higher lows)
            # - Descending resistance: slope must be negative OR nearly flat (horizontal resistance)
            slope_pct = slope / p1["price"] * 100  # Keep sign for direction check

            if direction == "ascending":
                if slope <= 0:
                    continue
                if abs(slope_pct) < min_slope_pct:  # Support needs meaningful upward slope
                    continue

            if direction == "descending":
                # Allow slightly positive slopes for "flat" resistance zones
                # (e.g., multiple touches at similar levels)
                if slope_pct > 0.02:  # More than 0.02%/candle upward = not resistance
                    continue
                if slope_pct < -0.5:  # Extremely steep = likely old/irrelevant
                    continue

            # Count touches (points within 0.5% of line for daily, more tolerance)
            touches = 0
            total_deviation = 0
            last_touch_idx = 0

            for point in points:
                line_price_at_point = p1["price"] + slope * (point["idx"] - p1["idx"])
                deviation_pct = abs(point["price"] - line_price_at_point) / line_price_at_point

                if deviation_pct < tolerance_pct:  # Use configurable tolerance
                    touches += 1
                    total_deviation += deviation_pct
                    last_touch_idx = max(last_touch_idx, point["idx"])

            if touches >= min_touches:
                # Calculate current line price
                line_price_now = p1["price"] + slope * (current_idx - p1["idx"])

                # RELEVANCE CHECK: Skip lines that are too far from current price
                if current_price:
                    distance_pct = abs(current_price - line_price_now) / current_price * 100

                    # For ascending support: line should be AT or BELOW price (max 15% below)
                    if direction == "ascending":
                        if line_price_now > current_price * 1.02:  # Support above price = broken
                            continue
                        if distance_pct > 15:  # Too far below to be relevant
                            continue

                    # For descending resistance: line should be AT or ABOVE price (max 15% above)
                    if direction == "descending":
                        if line_price_now < current_price * 0.98:  # Resistance below price = broken
                            continue
                        if distance_pct > 15:  # Too far above to be relevant
                            continue

                # RECENCY CHECK: Require at least one touch in recent portion of lookback
                # If p2 (end point) is in the last 30% of candles, the line is automatically relevant
                p2_is_recent = p2["idx"] >= current_idx * 0.7

                if not p2_is_recent:
                    # More lenient for resistance (often tested from below before breaking)
                    if direction == "ascending":
                        recent_threshold = current_idx * 0.6  # Last 40% for support
                    else:
                        recent_threshold = current_idx * 0.4  # Last 60% for resistance (more lenient)

                    if last_touch_idx < recent_threshold:
                        continue  # No recent validation = stale trendline

                # Score = touches * recency bonus * slope strength
                recency_bonus = 1 + (last_touch_idx / current_idx) * 0.5  # Prefer recent touches
                slope_bonus = max(abs(slope_pct) / 0.1, 0.5)  # Some bonus for steeper, but don't penalize flat

                # Big bonus for trendlines that end at recent points (current trend)
                current_trend_bonus = 1.5 if p2_is_recent else 1.0

                score = touches * recency_bonus * slope_bonus * current_trend_bonus

                if score > best_score:
                    best_score = score
                    best_line = {
                        "start_idx": p1["idx"],
                        "end_idx": p2["idx"],
                        "start_price": p1["price"],
                        "end_price": p2["price"],
                        "slope": round(slope, 4),
                        "slope_pct_per_candle": round(slope_pct, 4),
                        "touches": touches,
                        "last_touch_idx": last_touch_idx,
                        "direction": direction,
                        "strength": round(min(touches / 4, 1.0), 2)
                    }

    return best_line


def analyze_5m_momentum(candles_5m: List[Dict]) -> Dict[str, Any]:
    """Quick 5-minute momentum analysis for entry timing.

    Args:
        candles_5m: List of 5m candles (at least 20)

    Returns:
        Dict with momentum signals
    """
    if not candles_5m or len(candles_5m) < 20:
        return {"signal": "insufficient_data", "strength": 0}

    current = candles_5m[-1]
    current_price = current["close"]

    # EMA 9/21 on 5m for micro momentum
    ema_9 = _calculate_ema([c["close"] for c in candles_5m], 9)
    ema_21 = _calculate_ema([c["close"] for c in candles_5m], 21)

    # Recent price action (last 5 candles)
    last_5 = candles_5m[-5:]
    price_change_5 = (last_5[-1]["close"] - last_5[0]["open"]) / last_5[0]["open"] * 100

    # Volume surge check
    volumes = [c.get("v", c.get("volume", 0)) for c in candles_5m]
    avg_volume = sum(volumes[:-1]) / len(volumes[:-1]) if len(volumes) > 1 else volumes[-1]
    current_volume = volumes[-1]
    volume_ratio = current_volume / avg_volume if avg_volume > 0 else 1.0

    # Candle strength (body vs wick ratio)
    body = abs(current["close"] - current["open"])
    total_range = current["high"] - current["low"]
    body_ratio = body / total_range if total_range > 0 else 0.5
    is_bullish_candle = current["close"] > current["open"]

    # Momentum direction
    ema_signal = "neutral"
    if ema_9 and ema_21:
        if ema_9 > ema_21 and current_price > ema_9:
            ema_signal = "bullish"
        elif ema_9 < ema_21 and current_price < ema_9:
            ema_signal = "bearish"

    # Combined signal
    signal = "neutral"
    strength = 0.0

    if ema_signal == "bullish" and price_change_5 > 0.1 and is_bullish_candle:
        signal = "bullish"
        strength = min(0.5 + (volume_ratio - 1) * 0.2 + body_ratio * 0.3, 1.0)
    elif ema_signal == "bearish" and price_change_5 < -0.1 and not is_bullish_candle:
        signal = "bearish"
        strength = min(0.5 + (volume_ratio - 1) * 0.2 + body_ratio * 0.3, 1.0)
    elif volume_ratio > 2.0:
        signal = "volume_spike"
        strength = min(volume_ratio / 4, 0.8)

    return {
        "signal": signal,
        "strength": round(strength, 2),
        "ema_9": round(ema_9, 2) if ema_9 else None,
        "ema_21": round(ema_21, 2) if ema_21 else None,
        "ema_signal": ema_signal,
        "price_change_5_pct": round(price_change_5, 3),
        "volume_ratio": round(volume_ratio, 2),
        "is_volume_spike": volume_ratio > 2.0,
        "candle_bullish": is_bullish_candle,
        "body_ratio": round(body_ratio, 2)
    }


def detect_5m_trend(candles_5m: List[Dict]) -> Dict[str, Any]:
    """
    Detect tradeable short-term trends on 5m chart.

    Looks for:
    1. EMA crossovers (9/21 and 21/50)
    2. Consecutive same-direction candles (3+)
    3. Higher highs/higher lows (uptrend) or lower highs/lower lows (downtrend)
    4. Price breaking recent range

    Args:
        candles_5m: List of 5m candles (at least 50)

    Returns:
        Dict with trend info and scalp opportunity
    """
    if not candles_5m or len(candles_5m) < 50:
        return {
            "trend": "neutral",
            "strength": 0,
            "scalp_signal": None,
            "entry_price": None,
            "stop_loss": None,
            "take_profit": None
        }

    closes = [c["close"] for c in candles_5m]
    highs = [c["high"] for c in candles_5m]
    lows = [c["low"] for c in candles_5m]
    current_price = closes[-1]

    # Calculate EMAs
    ema_9 = _calculate_ema(closes, 9)
    ema_21 = _calculate_ema(closes, 21)
    ema_50 = _calculate_ema(closes, 50)

    # Previous EMAs (5 candles ago) for crossover detection
    prev_closes = closes[:-5]
    prev_ema_9 = _calculate_ema(prev_closes, 9) if len(prev_closes) >= 9 else None
    prev_ema_21 = _calculate_ema(prev_closes, 21) if len(prev_closes) >= 21 else None

    # Detect EMA crossovers
    bullish_cross = False
    bearish_cross = False
    if ema_9 and ema_21 and prev_ema_9 and prev_ema_21:
        # 9 crossing above 21
        if prev_ema_9 <= prev_ema_21 and ema_9 > ema_21:
            bullish_cross = True
        # 9 crossing below 21
        elif prev_ema_9 >= prev_ema_21 and ema_9 < ema_21:
            bearish_cross = True

    # Count consecutive same-direction candles
    last_10 = candles_5m[-10:]
    bullish_streak = 0
    bearish_streak = 0
    for c in reversed(last_10):
        if c["close"] > c["open"]:
            if bearish_streak > 0:
                break
            bullish_streak += 1
        else:
            if bullish_streak > 0:
                break
            bearish_streak += 1

    # Check for higher highs/lows or lower highs/lows
    last_5_highs = highs[-5:]
    last_5_lows = lows[-5:]
    higher_highs = all(last_5_highs[i] >= last_5_highs[i-1] for i in range(1, len(last_5_highs)))
    higher_lows = all(last_5_lows[i] >= last_5_lows[i-1] for i in range(1, len(last_5_lows)))
    lower_highs = all(last_5_highs[i] <= last_5_highs[i-1] for i in range(1, len(last_5_highs)))
    lower_lows = all(last_5_lows[i] <= last_5_lows[i-1] for i in range(1, len(last_5_lows)))

    # Calculate recent range
    range_20 = candles_5m[-20:]
    range_high = max(c["high"] for c in range_20)
    range_low = min(c["low"] for c in range_20)
    range_mid = (range_high + range_low) / 2

    # ATR for stop calculation
    atr = _calculate_atr_simple(candles_5m[-14:])

    # === ANTI-CHASE FILTERS ===
    # RSI - Don't chase extended moves
    rsi = calculate_rsi(candles_5m, period=14)

    # Bollinger Bands - Check position within bands
    bb = calculate_bollinger_bands(candles_5m, period=20, std_dev=2.0)
    bb_position = bb.get("band_position", 0.5) if bb else 0.5  # 0=lower, 1=upper

    # VWAP approximation (volume-weighted average price)
    # Use typical price * volume for recent candles
    vwap_candles = candles_5m[-20:]
    total_vol = sum(c.get("v", c.get("volume", 1)) for c in vwap_candles)
    if total_vol > 0:
        vwap = sum((c["high"] + c["low"] + c["close"]) / 3 * c.get("v", c.get("volume", 1)) for c in vwap_candles) / total_vol
    else:
        vwap = current_price

    # === SUPPORT/RESISTANCE CHECK (CRITICAL!) ===
    # Calculate support/resistance to avoid shorting at support or longing at resistance
    sr_data = calculate_support_resistance(candles_5m, lookback=50)
    nearest_support = sr_data.get("nearest_support", range_low)
    nearest_resistance = sr_data.get("nearest_resistance", range_high)
    dist_to_support_pct = sr_data.get("dist_to_support_pct", 50)
    dist_to_resistance_pct = sr_data.get("dist_to_resistance_pct", 50)
    sr_signal = sr_data.get("signal", "mid_range")

    # Determine trend and strength
    trend = "neutral"
    strength = 0.0
    scalp_signal = None
    entry_price = None
    stop_loss = None
    take_profit = None
    reasons = []
    skip_reason = None  # Why we might skip the scalp

    # BULLISH TREND CONDITIONS
    bullish_score = 0
    if ema_9 and ema_21 and ema_9 > ema_21:
        bullish_score += 25
        reasons.append("EMA 9 > 21")
    if ema_21 and ema_50 and ema_21 > ema_50:
        bullish_score += 15
        reasons.append("EMA 21 > 50")
    if current_price > ema_9:
        bullish_score += 15
        reasons.append("Price > EMA 9")
    if bullish_cross:
        bullish_score += 20
        reasons.append("BULLISH CROSSOVER!")
    if bullish_streak >= 3:
        bullish_score += 15
        reasons.append(f"{bullish_streak} green candles")
    if higher_highs and higher_lows:
        bullish_score += 10
        reasons.append("Higher highs & lows")

    # BEARISH TREND CONDITIONS
    bearish_score = 0
    bear_reasons = []
    if ema_9 and ema_21 and ema_9 < ema_21:
        bearish_score += 25
        bear_reasons.append("EMA 9 < 21")
    if ema_21 and ema_50 and ema_21 < ema_50:
        bearish_score += 15
        bear_reasons.append("EMA 21 < 50")
    if current_price < ema_9:
        bearish_score += 15
        bear_reasons.append("Price < EMA 9")
    if bearish_cross:
        bearish_score += 20
        bear_reasons.append("BEARISH CROSSOVER!")
    if bearish_streak >= 3:
        bearish_score += 15
        bear_reasons.append(f"{bearish_streak} red candles")
    if lower_highs and lower_lows:
        bearish_score += 10
        bear_reasons.append("Lower highs & lows")

    # Determine final trend
    if bullish_score >= 50 and bullish_score > bearish_score:
        trend = "bullish"
        strength = min(bullish_score / 100, 1.0)
        if bullish_score >= 70:  # Strong trend = scalp opportunity
            # === SUPPORT/RESISTANCE FILTER (PRIMARY!) ===
            # DON'T LONG near resistance - wait for breakout or pullback
            if sr_signal == "near_resistance" or dist_to_resistance_pct < 0.5:
                skip_reason = f"Near resistance ${nearest_resistance:.2f} ({dist_to_resistance_pct:.1f}% away) - wait for breakout"
            # === ANTI-CHASE FILTERS (SECONDARY) ===
            elif rsi and rsi > 70:
                skip_reason = f"RSI overbought ({rsi:.0f}) - would chase"
            elif bb_position > 0.90:
                skip_reason = f"At upper BB ({bb_position:.0%}) - extended"
            else:
                # GOOD LONG: At/near support with bullish trend
                scalp_signal = "long"
                entry_price = current_price
                # Stop below support (structure-based stop)
                stop_loss = min(nearest_support * 0.998, current_price - (atr * 2.0)) if atr else nearest_support * 0.998
                # Target = next resistance (let trend play out)
                take_profit = nearest_resistance

    elif bearish_score >= 50 and bearish_score > bullish_score:
        trend = "bearish"
        strength = min(bearish_score / 100, 1.0)
        reasons = bear_reasons
        if bearish_score >= 70:  # Strong trend = scalp opportunity
            # === SUPPORT/RESISTANCE FILTER (PRIMARY!) ===
            # At support with bearish trend = MEAN REVERSION LONG opportunity
            if sr_signal == "near_support" or dist_to_support_pct < 0.5:
                # Mean reversion: Long at support even in bearish trend (bounce play)
                if rsi and rsi < 35:  # RSI oversold = good bounce setup
                    scalp_signal = "long"  # MEAN REVERSION LONG
                    entry_price = current_price
                    stop_loss = nearest_support * 0.995  # Tight stop below support
                    # Target = halfway to resistance (conservative bounce target)
                    take_profit = current_price + (nearest_resistance - current_price) * 0.5
                    reasons = [f"MEAN REVERSION at support ${nearest_support:.0f}", f"RSI oversold ({rsi:.0f})"]
                else:
                    skip_reason = f"Near support ${nearest_support:.2f} ({dist_to_support_pct:.1f}% away) - wait for RSI < 35 for bounce"
            # === ANTI-CHASE FILTERS (SECONDARY) ===
            elif rsi and rsi < 30:
                skip_reason = f"RSI oversold ({rsi:.0f}) - would chase into support"
            elif bb_position < 0.10:
                skip_reason = f"At lower BB ({bb_position:.0%}) - extended down"
            else:
                # GOOD SHORT: At/near resistance with bearish trend
                scalp_signal = "short"
                entry_price = current_price
                # Stop above resistance (structure-based stop)
                stop_loss = max(nearest_resistance * 1.002, current_price + (atr * 2.0)) if atr else nearest_resistance * 1.002
                # Target = next support (let trend play out)
                take_profit = nearest_support

    return {
        "trend": trend,
        "strength": round(strength, 2),
        "score": max(bullish_score, bearish_score),
        "scalp_signal": scalp_signal,
        "skip_reason": skip_reason,  # Why scalp was blocked
        "entry_price": round(entry_price, 2) if entry_price else None,
        "stop_loss": round(stop_loss, 2) if stop_loss else None,
        "take_profit": round(take_profit, 2) if take_profit else None,
        "reasons": reasons,
        "ema_9": round(ema_9, 2) if ema_9 else None,
        "ema_21": round(ema_21, 2) if ema_21 else None,
        "ema_50": round(ema_50, 2) if ema_50 else None,
        "bullish_cross": bullish_cross,
        "bearish_cross": bearish_cross,
        "bullish_streak": bullish_streak,
        "bearish_streak": bearish_streak,
        "atr": round(atr, 2) if atr else None,
        "rsi": round(rsi, 1) if rsi else None,
        "bb_position": round(bb_position, 2) if bb_position else None,
        "vwap": round(vwap, 2) if vwap else None,
        # S/R data for trend-following management
        "nearest_support": round(nearest_support, 2) if nearest_support else None,
        "nearest_resistance": round(nearest_resistance, 2) if nearest_resistance else None,
        "sr_signal": sr_signal
    }


def _calculate_atr_simple(candles: List[Dict]) -> Optional[float]:
    """Simple ATR calculation for a list of candles."""
    if len(candles) < 2:
        return None

    true_ranges = []
    for i in range(1, len(candles)):
        high = candles[i]["high"]
        low = candles[i]["low"]
        prev_close = candles[i-1]["close"]
        tr = max(high - low, abs(high - prev_close), abs(low - prev_close))
        true_ranges.append(tr)

    return sum(true_ranges) / len(true_ranges) if true_ranges else None


def _calculate_ema(prices: List[float], period: int) -> Optional[float]:
    """Calculate EMA for a list of prices."""
    if len(prices) < period:
        return None

    multiplier = 2 / (period + 1)
    ema = sum(prices[:period]) / period  # SMA for first period

    for price in prices[period:]:
        ema = (price - ema) * multiplier + ema

    return ema


# =============================================================================
# CANDLE PATTERN DETECTION
# =============================================================================

def detect_candle_pattern(candle: Dict, prev_candle: Dict = None) -> Dict[str, Any]:
    """Detect candlestick pattern for a single candle.

    Args:
        candle: Current candle with OHLC
        prev_candle: Previous candle (optional, for 2-candle patterns)

    Returns:
        Dict with pattern name, bias (bullish/bearish), and strength
    """
    o, h, l, c = candle["open"], candle["high"], candle["low"], candle["close"]
    body = abs(c - o)
    total_range = h - l

    if total_range == 0:
        return {"pattern": "neutral", "bias": "neutral", "strength": 0}

    body_ratio = body / total_range
    upper_wick = h - max(o, c)
    lower_wick = min(o, c) - l
    is_bullish = c > o

    patterns_found = []

    # === DOJI PATTERNS (tiny body) ===
    if body_ratio < 0.1:
        if upper_wick > body * 2 and lower_wick > body * 2:
            patterns_found.append(("long_legged_doji", "reversal", 0.7))
        elif upper_wick > body * 3 and lower_wick < body:
            patterns_found.append(("gravestone_doji", "bearish", 0.8))
        elif lower_wick > body * 3 and upper_wick < body:
            patterns_found.append(("dragonfly_doji", "bullish", 0.8))
        else:
            patterns_found.append(("doji", "reversal", 0.6))

    # === HAMMER / HANGING MAN (long lower wick) ===
    elif lower_wick > body * 2 and upper_wick < body * 0.5:
        if is_bullish:
            patterns_found.append(("hammer", "bullish", 0.75))
        else:
            patterns_found.append(("hanging_man", "bearish", 0.65))

    # === INVERTED HAMMER / SHOOTING STAR (long upper wick) ===
    elif upper_wick > body * 2 and lower_wick < body * 0.5:
        if is_bullish:
            patterns_found.append(("inverted_hammer", "bullish", 0.65))
        else:
            patterns_found.append(("shooting_star", "bearish", 0.75))

    # === MARUBOZU (strong momentum, tiny wicks) ===
    elif body_ratio > 0.85:
        if is_bullish:
            patterns_found.append(("bullish_marubozu", "bullish", 0.85))
        else:
            patterns_found.append(("bearish_marubozu", "bearish", 0.85))

    # === SPINNING TOP (small body, equal wicks) ===
    elif body_ratio < 0.3 and abs(upper_wick - lower_wick) < total_range * 0.2:
        patterns_found.append(("spinning_top", "neutral", 0.4))

    # === 2-CANDLE PATTERNS (need previous candle) ===
    if prev_candle:
        prev_o, prev_h, prev_l, prev_c = prev_candle["open"], prev_candle["high"], prev_candle["low"], prev_candle["close"]
        prev_body = abs(prev_c - prev_o)
        prev_is_bullish = prev_c > prev_o

        # ENGULFING PATTERNS
        if body > prev_body * 1.5:  # Current body is larger
            if is_bullish and not prev_is_bullish and o <= prev_c and c >= prev_o:
                patterns_found.append(("bullish_engulfing", "bullish", 0.85))
            elif not is_bullish and prev_is_bullish and o >= prev_c and c <= prev_o:
                patterns_found.append(("bearish_engulfing", "bearish", 0.85))

        # HARAMI (baby inside mother)
        if prev_body > body * 1.5:
            if not prev_is_bullish and is_bullish and o > prev_c and c < prev_o:
                patterns_found.append(("bullish_harami", "bullish", 0.65))
            elif prev_is_bullish and not is_bullish and o < prev_c and c > prev_o:
                patterns_found.append(("bearish_harami", "bearish", 0.65))

        # PIERCING LINE (bullish) / DARK CLOUD COVER (bearish)
        if not prev_is_bullish and is_bullish:
            if o < prev_l and c > (prev_o + prev_c) / 2:
                patterns_found.append(("piercing_line", "bullish", 0.7))
        elif prev_is_bullish and not is_bullish:
            if o > prev_h and c < (prev_o + prev_c) / 2:
                patterns_found.append(("dark_cloud_cover", "bearish", 0.7))

    # Return strongest pattern found
    if patterns_found:
        patterns_found.sort(key=lambda x: x[2], reverse=True)
        best = patterns_found[0]
        return {
            "pattern": best[0],
            "bias": best[1],
            "strength": best[2],
            "all_patterns": [p[0] for p in patterns_found]
        }

    # Default strong candle
    return {
        "pattern": "bullish_candle" if is_bullish else "bearish_candle",
        "bias": "bullish" if is_bullish else "bearish",
        "strength": min(body_ratio, 0.5)
    }


def analyze_multi_timeframe_candles(
    candles_5m: List[Dict],
    candles_15m: List[Dict],
    candles_30m: List[Dict]
) -> Dict[str, Any]:
    """Analyze candle patterns across multiple timeframes.

    Looks for pattern confluence across 5m, 15m, and 30m for stronger signals.

    Args:
        candles_5m: 5-minute candles (at least 5)
        candles_15m: 15-minute candles (at least 5)
        candles_30m: 30-minute candles (at least 5)

    Returns:
        Dict with patterns per timeframe, confluence signal, and recommendation
    """
    result = {
        "5m": {"pattern": None, "bias": "neutral", "strength": 0},
        "15m": {"pattern": None, "bias": "neutral", "strength": 0},
        "30m": {"pattern": None, "bias": "neutral", "strength": 0},
        "confluence_signal": "neutral",
        "confluence_strength": 0.0,
        "recommendation": "WAIT"
    }

    # Analyze each timeframe
    timeframes = [
        ("5m", candles_5m),
        ("15m", candles_15m),
        ("30m", candles_30m)
    ]

    bias_scores = {"bullish": 0, "bearish": 0, "neutral": 0, "reversal": 0}

    for tf_name, candles in timeframes:
        if not candles or len(candles) < 2:
            continue

        # Get current and previous candle
        current = candles[-1]
        prev = candles[-2]

        pattern_info = detect_candle_pattern(current, prev)
        result[tf_name] = pattern_info

        # Weight by timeframe (30m > 15m > 5m)
        tf_weight = {"5m": 1.0, "15m": 1.5, "30m": 2.0}[tf_name]

        bias = pattern_info.get("bias", "neutral")
        strength = pattern_info.get("strength", 0)

        bias_scores[bias] += strength * tf_weight

    # Calculate confluence
    total_weight = sum(bias_scores.values())
    if total_weight > 0:
        bullish_pct = bias_scores["bullish"] / total_weight
        bearish_pct = bias_scores["bearish"] / total_weight

        if bullish_pct > 0.6:
            result["confluence_signal"] = "bullish"
            result["confluence_strength"] = bullish_pct
            if bullish_pct > 0.75:
                result["recommendation"] = "STRONG_LONG"
            else:
                result["recommendation"] = "LEAN_LONG"
        elif bearish_pct > 0.6:
            result["confluence_signal"] = "bearish"
            result["confluence_strength"] = bearish_pct
            if bearish_pct > 0.75:
                result["recommendation"] = "STRONG_SHORT"
            else:
                result["recommendation"] = "LEAN_SHORT"
        elif bias_scores["reversal"] > bias_scores["bullish"] + bias_scores["bearish"]:
            result["confluence_signal"] = "reversal_possible"
            result["confluence_strength"] = 0.5
            result["recommendation"] = "WAIT_REVERSAL"
        else:
            result["confluence_signal"] = "mixed"
            result["confluence_strength"] = 0.3
            result["recommendation"] = "WAIT"

    # Add summary text
    patterns_text = []
    for tf in ["5m", "15m", "30m"]:
        if result[tf].get("pattern"):
            patterns_text.append(f"{tf}: {result[tf]['pattern']}")
    result["patterns_summary"] = " | ".join(patterns_text) if patterns_text else "No clear patterns"

    return result


def detect_3_candle_patterns(candles: List[Dict]) -> Dict[str, Any]:
    """Detect 3-candle patterns like morning star, evening star, three soldiers.

    Args:
        candles: List of candles (at least 3)

    Returns:
        Dict with pattern info
    """
    if len(candles) < 3:
        return {"pattern": None, "bias": "neutral", "strength": 0}

    c1, c2, c3 = candles[-3], candles[-2], candles[-1]

    c1_body = abs(c1["close"] - c1["open"])
    c2_body = abs(c2["close"] - c2["open"])
    c3_body = abs(c3["close"] - c3["open"])

    c1_bullish = c1["close"] > c1["open"]
    c2_bullish = c2["close"] > c2["open"]
    c3_bullish = c3["close"] > c3["open"]

    c1_range = c1["high"] - c1["low"]
    c2_range = c2["high"] - c2["low"]
    c3_range = c3["high"] - c3["low"]

    # MORNING STAR (bullish reversal)
    # Big red → small body (gap down) → big green (closes above midpoint of first)
    if not c1_bullish and c1_body > c2_body * 2:
        if c2_body / c2_range < 0.3 if c2_range > 0 else True:  # Small body
            if c3_bullish and c3["close"] > (c1["open"] + c1["close"]) / 2:
                return {"pattern": "morning_star", "bias": "bullish", "strength": 0.85}

    # EVENING STAR (bearish reversal)
    # Big green → small body (gap up) → big red (closes below midpoint of first)
    if c1_bullish and c1_body > c2_body * 2:
        if c2_body / c2_range < 0.3 if c2_range > 0 else True:
            if not c3_bullish and c3["close"] < (c1["open"] + c1["close"]) / 2:
                return {"pattern": "evening_star", "bias": "bearish", "strength": 0.85}

    # THREE WHITE SOLDIERS (strong bullish)
    if c1_bullish and c2_bullish and c3_bullish:
        if c2["close"] > c1["close"] and c3["close"] > c2["close"]:
            if c1_body / c1_range > 0.6 and c2_body / c2_range > 0.6 and c3_body / c3_range > 0.6:
                return {"pattern": "three_white_soldiers", "bias": "bullish", "strength": 0.9}

    # THREE BLACK CROWS (strong bearish)
    if not c1_bullish and not c2_bullish and not c3_bullish:
        if c2["close"] < c1["close"] and c3["close"] < c2["close"]:
            if c1_body / c1_range > 0.6 and c2_body / c2_range > 0.6 and c3_body / c3_range > 0.6:
                return {"pattern": "three_black_crows", "bias": "bearish", "strength": 0.9}

    # THREE INSIDE UP (bullish)
    if not c1_bullish and c2_bullish and c3_bullish:
        if c2["close"] < c1["open"] and c2["open"] > c1["close"]:  # c2 inside c1
            if c3["close"] > c1["open"]:  # c3 closes above c1 open
                return {"pattern": "three_inside_up", "bias": "bullish", "strength": 0.75}

    # THREE INSIDE DOWN (bearish)
    if c1_bullish and not c2_bullish and not c3_bullish:
        if c2["close"] > c1["open"] and c2["open"] < c1["close"]:  # c2 inside c1
            if c3["close"] < c1["open"]:  # c3 closes below c1 open
                return {"pattern": "three_inside_down", "bias": "bearish", "strength": 0.75}

    return {"pattern": None, "bias": "neutral", "strength": 0}


# =============================================================================
# REVERSAL PREDICTION SIGNALS - For Scalping
# =============================================================================

def detect_rsi_divergence(candles: List[Dict], rsi_period: int = 14, lookback: int = 10) -> Dict[str, Any]:
    """Detect RSI divergence - KEY reversal predictor.

    Bullish divergence: Price makes LOWER low, but RSI makes HIGHER low = reversal UP coming
    Bearish divergence: Price makes HIGHER high, but RSI makes LOWER high = reversal DOWN coming

    Args:
        candles: List of candle dicts
        rsi_period: RSI calculation period
        lookback: How many candles back to check for divergence

    Returns:
        Dict with divergence type and strength
    """
    if len(candles) < rsi_period + lookback:
        return {"divergence": "none", "strength": 0, "signal": "neutral"}

    # Calculate RSI for each candle in lookback period
    rsi_values = []
    for i in range(lookback + 1):
        idx = len(candles) - lookback - 1 + i
        if idx >= rsi_period:
            subset = candles[:idx + 1]
            rsi = calculate_rsi(subset, rsi_period)
            rsi_values.append(rsi if rsi else 50)
        else:
            rsi_values.append(50)

    prices = [c["close"] for c in candles[-lookback-1:]]
    lows = [c["low"] for c in candles[-lookback-1:]]
    highs = [c["high"] for c in candles[-lookback-1:]]

    # Find swing points in price and RSI
    # BULLISH DIVERGENCE: Price lower low + RSI higher low
    price_low_idx = lows.index(min(lows))
    recent_price_low = min(lows[-3:])  # Recent low
    older_price_low = min(lows[:lookback-2])  # Earlier low

    recent_rsi_low = min(rsi_values[-3:])
    older_rsi_low = min(rsi_values[:lookback-2])

    # BEARISH DIVERGENCE: Price higher high + RSI lower high
    recent_price_high = max(highs[-3:])
    older_price_high = max(highs[:lookback-2])

    recent_rsi_high = max(rsi_values[-3:])
    older_rsi_high = max(rsi_values[:lookback-2])

    result = {"divergence": "none", "strength": 0, "signal": "neutral"}

    # Check BULLISH divergence (price lower low, RSI higher low)
    if recent_price_low < older_price_low * 0.998:  # Price made lower low (0.2% threshold)
        if recent_rsi_low > older_rsi_low + 3:  # RSI made higher low (3 point threshold)
            strength = min((recent_rsi_low - older_rsi_low) / 10, 1.0)  # Normalize strength
            result = {
                "divergence": "bullish",
                "strength": round(strength, 2),
                "signal": "long",
                "description": f"Price lower low but RSI higher ({older_rsi_low:.0f} -> {recent_rsi_low:.0f})"
            }

    # Check BEARISH divergence (price higher high, RSI lower high)
    if recent_price_high > older_price_high * 1.002:  # Price made higher high
        if recent_rsi_high < older_rsi_high - 3:  # RSI made lower high
            strength = min((older_rsi_high - recent_rsi_high) / 10, 1.0)
            result = {
                "divergence": "bearish",
                "strength": round(strength, 2),
                "signal": "short",
                "description": f"Price higher high but RSI lower ({older_rsi_high:.0f} -> {recent_rsi_high:.0f})"
            }

    return result


def detect_volume_exhaustion(candles: List[Dict], lookback: int = 5) -> Dict[str, Any]:
    """Detect volume exhaustion - momentum running out.

    If price continues but volume is decreasing = move is exhausting, reversal coming.

    Args:
        candles: List of candles
        lookback: Number of candles to analyze

    Returns:
        Dict with exhaustion signal
    """
    if len(candles) < lookback + 5:
        return {"exhaustion": "none", "signal": "neutral", "strength": 0}

    recent = candles[-lookback:]
    prior = candles[-lookback*2:-lookback]

    # Get volumes
    recent_volumes = [c.get("v", c.get("volume", 0)) for c in recent]
    prior_volumes = [c.get("v", c.get("volume", 0)) for c in prior]

    avg_recent_vol = sum(recent_volumes) / len(recent_volumes) if recent_volumes else 0
    avg_prior_vol = sum(prior_volumes) / len(prior_volumes) if prior_volumes else 1

    vol_ratio = avg_recent_vol / avg_prior_vol if avg_prior_vol > 0 else 1.0

    # Price direction
    price_change = (recent[-1]["close"] - recent[0]["open"]) / recent[0]["open"] * 100

    result = {"exhaustion": "none", "signal": "neutral", "strength": 0, "vol_ratio": round(vol_ratio, 2)}

    # BEARISH EXHAUSTION: Price going UP but volume DECREASING
    if price_change > 0.3 and vol_ratio < 0.7:  # Up move with declining volume
        strength = min((1 - vol_ratio) * 1.5, 1.0)
        result = {
            "exhaustion": "bearish",
            "signal": "short",
            "strength": round(strength, 2),
            "vol_ratio": round(vol_ratio, 2),
            "description": f"Up {price_change:.1f}% but volume declining ({vol_ratio:.0%})"
        }

    # BULLISH EXHAUSTION: Price going DOWN but volume DECREASING
    elif price_change < -0.3 and vol_ratio < 0.7:  # Down move with declining volume
        strength = min((1 - vol_ratio) * 1.5, 1.0)
        result = {
            "exhaustion": "bullish",
            "signal": "long",
            "strength": round(strength, 2),
            "vol_ratio": round(vol_ratio, 2),
            "description": f"Down {price_change:.1f}% but volume declining ({vol_ratio:.0%})"
        }

    return result


def detect_reversal_setup(candles: List[Dict], sr_data: Dict, bb_data: Dict) -> Dict[str, Any]:
    """Comprehensive reversal setup detection for scalping.

    Combines multiple signals to predict reversals BEFORE they happen:
    1. Price at support/resistance
    2. RSI divergence
    3. Volume exhaustion
    4. Bollinger band extremes

    Args:
        candles: List of candles (5m recommended)
        sr_data: Support/resistance data
        bb_data: Bollinger bands data

    Returns:
        Dict with reversal probability and recommended action
    """
    if len(candles) < 20:
        return {"setup": "none", "signal": "neutral", "confidence": 0}

    current_price = candles[-1]["close"]
    signals = []
    long_score = 0
    short_score = 0

    # 1. RSI DIVERGENCE (strongest signal)
    divergence = detect_rsi_divergence(candles, rsi_period=14, lookback=10)
    if divergence["divergence"] == "bullish":
        long_score += 35 * divergence["strength"]
        signals.append(f"RSI bullish divergence ({divergence['strength']:.0%})")
    elif divergence["divergence"] == "bearish":
        short_score += 35 * divergence["strength"]
        signals.append(f"RSI bearish divergence ({divergence['strength']:.0%})")

    # 2. VOLUME EXHAUSTION
    exhaustion = detect_volume_exhaustion(candles, lookback=5)
    if exhaustion["exhaustion"] == "bullish":
        long_score += 25 * exhaustion["strength"]
        signals.append(f"Selling exhaustion ({exhaustion['strength']:.0%})")
    elif exhaustion["exhaustion"] == "bearish":
        short_score += 25 * exhaustion["strength"]
        signals.append(f"Buying exhaustion ({exhaustion['strength']:.0%})")

    # 3. SUPPORT/RESISTANCE PROXIMITY
    if sr_data:
        sr_signal = sr_data.get("signal", "mid_range")
        dist_support = sr_data.get("dist_to_support_pct", 100)
        dist_resistance = sr_data.get("dist_to_resistance_pct", 100)

        if sr_signal == "near_support" or dist_support < 0.5:
            long_score += 25
            signals.append(f"At support ({dist_support:.1f}% away)")
        elif sr_signal == "near_resistance" or dist_resistance < 0.5:
            short_score += 25
            signals.append(f"At resistance ({dist_resistance:.1f}% away)")

    # 4. BOLLINGER BAND EXTREMES
    if bb_data:
        bb_position = bb_data.get("band_position", 0.5)
        bb_signal = bb_data.get("signal", "neutral")

        if bb_position <= 0.1 or bb_signal == "oversold":  # Near lower band
            long_score += 15
            signals.append(f"BB oversold ({bb_position:.0%})")
        elif bb_position >= 0.9 or bb_signal == "overbought":  # Near upper band
            short_score += 15
            signals.append(f"BB overbought ({bb_position:.0%})")

    # Calculate final setup
    if long_score > short_score and long_score >= 40:
        return {
            "setup": "long_reversal",
            "signal": "long",
            "confidence": min(long_score, 100),
            "signals": signals,
            "description": "Multiple reversal signals pointing UP"
        }
    elif short_score > long_score and short_score >= 40:
        return {
            "setup": "short_reversal",
            "signal": "short",
            "confidence": min(short_score, 100),
            "signals": signals,
            "description": "Multiple reversal signals pointing DOWN"
        }

    return {"setup": "none", "signal": "neutral", "confidence": max(long_score, short_score), "signals": signals}


# ==================== ADVANCED INDICATORS ====================

def calculate_vwap(candles: List[Dict], anchor: str = "session") -> Dict[str, Any]:
    """Calculate VWAP (Volume Weighted Average Price) - Institutional level.

    VWAP is critical because:
    - Institutional traders use it as a benchmark
    - Price above VWAP = bullish, below = bearish
    - Provides dynamic support/resistance

    Args:
        candles: List of candle dicts with high, low, close, volume
        anchor: "session" (24h), "week", or "day"

    Returns:
        Dict with vwap, upper_band, lower_band, signal
    """
    if not candles or len(candles) < 5:
        return {"vwap": None, "signal": "neutral", "deviation": 0}

    # Calculate typical price and cumulative values
    cumulative_tpv = 0  # Typical Price * Volume
    cumulative_volume = 0
    squared_deviations = []

    vwap_series = []

    for c in candles:
        typical_price = (c["high"] + c["low"] + c["close"]) / 3
        volume = c.get("volume", 1)

        cumulative_tpv += typical_price * volume
        cumulative_volume += volume

        if cumulative_volume > 0:
            vwap = cumulative_tpv / cumulative_volume
            vwap_series.append(vwap)

            # For standard deviation bands
            squared_deviations.append((typical_price - vwap) ** 2)

    if not vwap_series:
        return {"vwap": None, "signal": "neutral", "deviation": 0}

    current_vwap = vwap_series[-1]
    current_price = candles[-1]["close"]

    # Calculate standard deviation for bands
    if len(squared_deviations) > 1:
        variance = sum(squared_deviations) / len(squared_deviations)
        std_dev = variance ** 0.5
    else:
        std_dev = current_vwap * 0.01  # Default 1% if not enough data

    upper_band_1 = current_vwap + std_dev
    upper_band_2 = current_vwap + 2 * std_dev
    lower_band_1 = current_vwap - std_dev
    lower_band_2 = current_vwap - 2 * std_dev

    # Distance from VWAP as percentage
    deviation_pct = ((current_price - current_vwap) / current_vwap) * 100 if current_vwap else 0

    # Generate signal
    if current_price > upper_band_2:
        signal = "overbought"  # Extended above VWAP
    elif current_price > current_vwap:
        signal = "bullish"  # Above VWAP
    elif current_price < lower_band_2:
        signal = "oversold"  # Extended below VWAP
    elif current_price < current_vwap:
        signal = "bearish"  # Below VWAP
    else:
        signal = "neutral"

    return {
        "vwap": round(current_vwap, 2),
        "upper_band_1": round(upper_band_1, 2),
        "upper_band_2": round(upper_band_2, 2),
        "lower_band_1": round(lower_band_1, 2),
        "lower_band_2": round(lower_band_2, 2),
        "deviation_pct": round(deviation_pct, 2),
        "signal": signal,
        "std_dev": round(std_dev, 2)
    }


def calculate_ichimoku(candles: List[Dict], tenkan: int = 9, kijun: int = 26,
                        senkou_b: int = 52) -> Dict[str, Any]:
    """Calculate Ichimoku Cloud - Trend + Momentum + S/R in one indicator.

    Ichimoku provides:
    - Tenkan-sen (Conversion Line): Short-term momentum
    - Kijun-sen (Base Line): Medium-term trend
    - Senkou Span A & B: Future cloud (support/resistance)
    - Chikou Span: Lagging confirmation

    Trading signals:
    - Price above cloud = bullish
    - Price below cloud = bearish
    - Tenkan > Kijun = bullish momentum
    - Cloud color (A > B = bullish, A < B = bearish)

    Args:
        candles: List of candle dicts with high, low, close
        tenkan: Tenkan-sen period (default 9)
        kijun: Kijun-sen period (default 26)
        senkou_b: Senkou Span B period (default 52)
    """
    if len(candles) < senkou_b:
        return {"signal": "neutral", "trend": "unknown", "cloud_signal": "neutral"}

    def donchian_mid(data: List[Dict], period: int, end_idx: int) -> Optional[float]:
        """Calculate Donchian midpoint (highest high + lowest low) / 2"""
        start_idx = max(0, end_idx - period)
        subset = data[start_idx:end_idx]
        if not subset:
            return None
        highest = max(c["high"] for c in subset)
        lowest = min(c["low"] for c in subset)
        return (highest + lowest) / 2

    # Current index
    idx = len(candles)

    # Tenkan-sen (Conversion Line) - 9 period Donchian midpoint
    tenkan_sen = donchian_mid(candles, tenkan, idx)

    # Kijun-sen (Base Line) - 26 period Donchian midpoint
    kijun_sen = donchian_mid(candles, kijun, idx)

    # Senkou Span A - (Tenkan + Kijun) / 2, plotted 26 periods ahead
    # For current analysis, we look at what was calculated 26 periods ago
    if len(candles) >= kijun + kijun:
        tenkan_26_ago = donchian_mid(candles, tenkan, idx - kijun)
        kijun_26_ago = donchian_mid(candles, kijun, idx - kijun)
        if tenkan_26_ago and kijun_26_ago:
            senkou_a = (tenkan_26_ago + kijun_26_ago) / 2
        else:
            senkou_a = None
    else:
        senkou_a = (tenkan_sen + kijun_sen) / 2 if tenkan_sen and kijun_sen else None

    # Senkou Span B - 52 period Donchian midpoint, plotted 26 periods ahead
    if len(candles) >= senkou_b + kijun:
        senkou_b_val = donchian_mid(candles, senkou_b, idx - kijun)
    else:
        senkou_b_val = donchian_mid(candles, senkou_b, idx)

    # Chikou Span - Current close plotted 26 periods back (for confirmation)
    chikou = candles[-1]["close"]
    chikou_comparison_price = candles[-kijun]["close"] if len(candles) > kijun else chikou

    current_price = candles[-1]["close"]

    # === Generate Signals ===
    signals = []
    bullish_points = 0
    bearish_points = 0

    # 1. Price vs Cloud
    if senkou_a and senkou_b_val:
        cloud_top = max(senkou_a, senkou_b_val)
        cloud_bottom = min(senkou_a, senkou_b_val)

        if current_price > cloud_top:
            bullish_points += 30
            signals.append("Price above cloud")
        elif current_price < cloud_bottom:
            bearish_points += 30
            signals.append("Price below cloud")
        else:
            signals.append("Price inside cloud (consolidation)")

        # Cloud color
        if senkou_a > senkou_b_val:
            bullish_points += 10
            signals.append("Bullish cloud (green)")
        else:
            bearish_points += 10
            signals.append("Bearish cloud (red)")

    # 2. Tenkan vs Kijun (TK Cross)
    if tenkan_sen and kijun_sen:
        if tenkan_sen > kijun_sen:
            bullish_points += 25
            signals.append("Tenkan > Kijun (bullish momentum)")
        elif tenkan_sen < kijun_sen:
            bearish_points += 25
            signals.append("Tenkan < Kijun (bearish momentum)")

    # 3. Chikou confirmation
    if chikou > chikou_comparison_price:
        bullish_points += 15
        signals.append("Chikou confirms bullish")
    elif chikou < chikou_comparison_price:
        bearish_points += 15
        signals.append("Chikou confirms bearish")

    # 4. Price vs Kijun (key support/resistance)
    if kijun_sen:
        if current_price > kijun_sen:
            bullish_points += 10
        else:
            bearish_points += 10

    # Determine overall signal
    if bullish_points >= 60:
        signal = "strong_bullish"
        trend = "bullish"
    elif bullish_points >= 40:
        signal = "bullish"
        trend = "bullish"
    elif bearish_points >= 60:
        signal = "strong_bearish"
        trend = "bearish"
    elif bearish_points >= 40:
        signal = "bearish"
        trend = "bearish"
    else:
        signal = "neutral"
        trend = "ranging"

    return {
        "tenkan_sen": round(tenkan_sen, 2) if tenkan_sen else None,
        "kijun_sen": round(kijun_sen, 2) if kijun_sen else None,
        "senkou_a": round(senkou_a, 2) if senkou_a else None,
        "senkou_b": round(senkou_b_val, 2) if senkou_b_val else None,
        "cloud_top": round(cloud_top, 2) if senkou_a and senkou_b_val else None,
        "cloud_bottom": round(cloud_bottom, 2) if senkou_a and senkou_b_val else None,
        "chikou": round(chikou, 2),
        "signal": signal,
        "trend": trend,
        "bullish_score": bullish_points,
        "bearish_score": bearish_points,
        "signals": signals
    }


def calculate_adx(candles: List[Dict], period: int = 14) -> Dict[str, Any]:
    """Calculate ADX (Average Directional Index) for trend strength.

    ADX measures trend STRENGTH (not direction):
    - ADX > 25 = Strong trend (trending market)
    - ADX 20-25 = Emerging trend
    - ADX < 20 = Weak/No trend (ranging market)
    - ADX > 40 = Very strong trend

    +DI and -DI give direction:
    - +DI > -DI = Bullish trend
    - -DI > +DI = Bearish trend

    Args:
        candles: List of candle dicts with high, low, close
        period: ADX period (default 14)

    Returns:
        Dict with adx, plus_di, minus_di, trend_strength, trend_direction
    """
    if len(candles) < period * 2:
        return {"adx": None, "signal": "neutral", "trend_strength": "unknown"}

    # Calculate True Range, +DM, -DM
    tr_list = []
    plus_dm_list = []
    minus_dm_list = []

    for i in range(1, len(candles)):
        high = candles[i]["high"]
        low = candles[i]["low"]
        close = candles[i]["close"]
        prev_high = candles[i-1]["high"]
        prev_low = candles[i-1]["low"]
        prev_close = candles[i-1]["close"]

        # True Range
        tr = max(
            high - low,
            abs(high - prev_close),
            abs(low - prev_close)
        )
        tr_list.append(tr)

        # +DM and -DM
        up_move = high - prev_high
        down_move = prev_low - low

        plus_dm = up_move if up_move > down_move and up_move > 0 else 0
        minus_dm = down_move if down_move > up_move and down_move > 0 else 0

        plus_dm_list.append(plus_dm)
        minus_dm_list.append(minus_dm)

    if len(tr_list) < period:
        return {"adx": None, "signal": "neutral", "trend_strength": "unknown"}

    # Smoothed TR, +DM, -DM using Wilder's smoothing
    def wilder_smooth(data: List[float], period: int) -> List[float]:
        smoothed = [sum(data[:period])]
        for i in range(period, len(data)):
            smoothed.append(smoothed[-1] - smoothed[-1] / period + data[i])
        return smoothed

    atr_smooth = wilder_smooth(tr_list, period)
    plus_dm_smooth = wilder_smooth(plus_dm_list, period)
    minus_dm_smooth = wilder_smooth(minus_dm_list, period)

    # Calculate +DI and -DI
    plus_di_list = []
    minus_di_list = []
    dx_list = []

    for i in range(len(atr_smooth)):
        if atr_smooth[i] > 0:
            plus_di = (plus_dm_smooth[i] / atr_smooth[i]) * 100
            minus_di = (minus_dm_smooth[i] / atr_smooth[i]) * 100
        else:
            plus_di = 0
            minus_di = 0

        plus_di_list.append(plus_di)
        minus_di_list.append(minus_di)

        # DX
        di_sum = plus_di + minus_di
        if di_sum > 0:
            dx = abs(plus_di - minus_di) / di_sum * 100
        else:
            dx = 0
        dx_list.append(dx)

    # ADX is smoothed DX
    if len(dx_list) >= period:
        adx_values = wilder_smooth(dx_list, period)
        adx = adx_values[-1] if adx_values else 0
    else:
        adx = sum(dx_list) / len(dx_list) if dx_list else 0

    plus_di = plus_di_list[-1] if plus_di_list else 0
    minus_di = minus_di_list[-1] if minus_di_list else 0

    # Determine trend strength
    if adx >= 40:
        trend_strength = "very_strong"
    elif adx >= 25:
        trend_strength = "strong"
    elif adx >= 20:
        trend_strength = "emerging"
    else:
        trend_strength = "weak"

    # Determine direction
    if plus_di > minus_di:
        trend_direction = "bullish"
        if adx >= 25:
            signal = "strong_bullish"
        else:
            signal = "bullish"
    elif minus_di > plus_di:
        trend_direction = "bearish"
        if adx >= 25:
            signal = "strong_bearish"
        else:
            signal = "bearish"
    else:
        trend_direction = "neutral"
        signal = "neutral"

    return {
        "adx": round(adx, 2),
        "plus_di": round(plus_di, 2),
        "minus_di": round(minus_di, 2),
        "trend_strength": trend_strength,
        "trend_direction": trend_direction,
        "signal": signal,
        "is_trending": adx >= 25
    }


def calculate_cvd(candles: List[Dict]) -> Dict[str, Any]:
    """Calculate CVD (Cumulative Volume Delta) - Order Flow Analysis.

    CVD shows who's really buying/selling:
    - Rising CVD = Buyers in control (accumulation)
    - Falling CVD = Sellers in control (distribution)
    - CVD divergence from price = potential reversal

    We estimate buy/sell volume from candle structure:
    - If close > open: Buy volume = (close - low) / (high - low) * volume
    - If close < open: Sell volume = (high - close) / (high - low) * volume

    Args:
        candles: List of candle dicts with open, high, low, close, volume

    Returns:
        Dict with cvd, delta, trend, divergence signal
    """
    if not candles or len(candles) < 10:
        return {"cvd": 0, "signal": "neutral", "trend": "neutral"}

    cvd = 0
    cvd_series = []
    delta_series = []

    for c in candles:
        high = c["high"]
        low = c["low"]
        close = c["close"]
        open_price = c["open"]
        volume = c.get("volume", 0)

        price_range = high - low
        if price_range > 0:
            # Estimate buy/sell volume based on close position
            # If close near high = mostly buying
            # If close near low = mostly selling
            close_position = (close - low) / price_range

            buy_volume = volume * close_position
            sell_volume = volume * (1 - close_position)
            delta = buy_volume - sell_volume
        else:
            delta = 0

        cvd += delta
        cvd_series.append(cvd)
        delta_series.append(delta)

    # Analyze CVD trend (last 10 candles)
    recent_cvd = cvd_series[-10:]
    if len(recent_cvd) >= 2:
        cvd_change = recent_cvd[-1] - recent_cvd[0]
        cvd_trend = "rising" if cvd_change > 0 else "falling" if cvd_change < 0 else "flat"
    else:
        cvd_trend = "unknown"

    # Check for divergence
    price_start = candles[-10]["close"] if len(candles) >= 10 else candles[0]["close"]
    price_end = candles[-1]["close"]
    price_change = price_end - price_start

    divergence = None
    if price_change > 0 and cvd_change < 0:
        divergence = "bearish"  # Price up but CVD down = distribution
    elif price_change < 0 and cvd_change > 0:
        divergence = "bullish"  # Price down but CVD up = accumulation

    # Recent delta (last candle)
    recent_delta = delta_series[-1] if delta_series else 0

    # Generate signal
    if divergence == "bullish":
        signal = "bullish_divergence"
    elif divergence == "bearish":
        signal = "bearish_divergence"
    elif cvd_trend == "rising":
        signal = "bullish"
    elif cvd_trend == "falling":
        signal = "bearish"
    else:
        signal = "neutral"

    return {
        "cvd": round(cvd, 2),
        "recent_delta": round(recent_delta, 2),
        "cvd_trend": cvd_trend,
        "divergence": divergence,
        "signal": signal,
        "description": f"CVD {'↑' if cvd_trend == 'rising' else '↓' if cvd_trend == 'falling' else '→'} | {divergence + ' divergence' if divergence else 'No divergence'}"
    }


def detect_market_regime(candles_4h: List[Dict], candles_1h: List[Dict] = None) -> Dict[str, Any]:
    """Detect current market regime for strategy selection.

    Market regimes:
    - TRENDING: ADX > 25, clear direction → Use trend-following
    - RANGING: ADX < 20, price in range → Use mean reversion
    - VOLATILE: ATR spike > 1.5x average → Reduce size, widen stops
    - BREAKOUT: Price at range extreme with volume → Prepare for move

    Args:
        candles_4h: 4-hour candles for regime detection
        candles_1h: Optional 1-hour candles for confirmation

    Returns:
        Dict with regime, recommended strategy, position sizing
    """
    if not candles_4h or len(candles_4h) < 50:
        return {"regime": "unknown", "strategy": "none", "size_multiplier": 0.5}

    # Calculate ADX
    adx_data = calculate_adx(candles_4h, period=14)
    adx = adx_data.get("adx", 0) or 0
    adx_direction = adx_data.get("trend_direction", "neutral")

    # Calculate ATR for volatility
    atr = calculate_atr(candles_4h, period=14)
    current_price = candles_4h[-1]["close"]
    atr_pct = (atr / current_price * 100) if atr and current_price else 0

    # Calculate historical ATR for spike detection
    if len(candles_4h) >= 50:
        historical_atrs = []
        for i in range(20, min(50, len(candles_4h))):
            hist_atr = calculate_atr(candles_4h[:i], period=14)
            if hist_atr:
                historical_atrs.append(hist_atr)

        avg_atr = sum(historical_atrs) / len(historical_atrs) if historical_atrs else atr
        atr_ratio = atr / avg_atr if avg_atr and atr else 1.0
    else:
        atr_ratio = 1.0

    # Calculate price range (for ranging detection)
    highs = [c["high"] for c in candles_4h[-20:]]
    lows = [c["low"] for c in candles_4h[-20:]]
    range_high = max(highs)
    range_low = min(lows)
    range_pct = ((range_high - range_low) / range_low) * 100 if range_low else 0

    # Current price position in range
    range_position = (current_price - range_low) / (range_high - range_low) if (range_high - range_low) > 0 else 0.5

    # === Determine Regime ===
    regime = "unknown"
    strategy = "none"
    size_multiplier = 1.0
    signals = []

    # Check for volatility spike first (overrides other conditions)
    if atr_ratio > 1.5:
        regime = "volatile"
        strategy = "reduce_exposure"
        size_multiplier = 0.5
        signals.append(f"ATR spike: {atr_ratio:.1f}x normal")

    # Strong trend
    elif adx >= 25:
        regime = "trending"
        if adx_direction == "bullish":
            strategy = "trend_long"
            signals.append(f"ADX {adx:.0f} bullish")
        elif adx_direction == "bearish":
            strategy = "trend_short"
            signals.append(f"ADX {adx:.0f} bearish")
        else:
            strategy = "trend_following"

        # Strong trends get full size or bonus
        if adx >= 40:
            size_multiplier = 1.25
            signals.append("Very strong trend")
        else:
            size_multiplier = 1.0

    # Weak trend / Ranging
    elif adx < 20:
        regime = "ranging"
        strategy = "mean_reversion"
        size_multiplier = 0.75
        signals.append(f"ADX {adx:.0f} (weak trend)")

        # Check for potential breakout
        if range_position > 0.9 or range_position < 0.1:
            signals.append(f"Near range {'high' if range_position > 0.9 else 'low'} - potential breakout")
            regime = "breakout_pending"
            strategy = "wait_for_breakout"
            size_multiplier = 0.5

    # Emerging trend
    else:  # 20 <= adx < 25
        regime = "emerging_trend"
        strategy = "cautious_trend"
        size_multiplier = 0.75
        signals.append(f"ADX {adx:.0f} (emerging trend)")

    # Add 1h confirmation if available
    if candles_1h and len(candles_1h) >= 30:
        adx_1h = calculate_adx(candles_1h, period=14)
        adx_1h_val = adx_1h.get("adx", 0) or 0
        if adx_1h_val >= 25 and adx >= 25:
            signals.append("1h confirms strong trend")
            size_multiplier = min(size_multiplier * 1.1, 1.5)

    return {
        "regime": regime,
        "strategy": strategy,
        "size_multiplier": round(size_multiplier, 2),
        "adx": round(adx, 2),
        "adx_direction": adx_direction,
        "atr_pct": round(atr_pct, 2),
        "atr_ratio": round(atr_ratio, 2),
        "range_position": round(range_position, 2),
        "signals": signals,
        "is_trending": adx >= 25,
        "is_ranging": adx < 20,
        "is_volatile": atr_ratio > 1.5
    }


def validate_entry_quality(
    candles_5m: List[Dict],
    candles_15m: List[Dict],
    candles_1h: List[Dict],
    candles_4h: List[Dict],
    trade_side: str,
    strategy_type: str = "swing"
) -> Dict[str, Any]:
    """Validate entry quality before placing a trade.

    REQUIREMENTS:
    1. Price must be within 0.5% of support/resistance
    2. At least 2 timeframes agreeing
    3. Volume confirming the move
    4. NOT entering at RSI extremes (unless mean reversion)

    Args:
        candles_5m, 15m, 1h, 4h: Multi-timeframe candle data
        trade_side: "long" or "short"
        strategy_type: "swing", "scalp", or "mean_reversion"

    Returns:
        Dict with valid, score, reasons, warnings
    """
    current_price = candles_5m[-1]["close"] if candles_5m else 0
    if not current_price:
        return {"valid": False, "score": 0, "reasons": ["No price data"]}

    checks_passed = 0
    total_checks = 4
    reasons = []
    warnings = []

    # === CHECK 1: Price near Support/Resistance ===
    sr_data = calculate_support_resistance(candles_4h) if candles_4h else {}
    supports = sr_data.get("supports", [])
    resistances = sr_data.get("resistances", [])

    near_sr = False
    sr_level = None

    # For LONG: Price should be near support
    if trade_side == "long" and supports:
        for level in supports:
            distance_pct = abs(current_price - level) / current_price * 100
            if distance_pct <= 0.5:
                near_sr = True
                sr_level = level
                reasons.append(f"✓ Near support ${level:.2f} ({distance_pct:.2f}%)")
                break

    # For SHORT: Price should be near resistance
    elif trade_side == "short" and resistances:
        for level in resistances:
            distance_pct = abs(current_price - level) / current_price * 100
            if distance_pct <= 0.5:
                near_sr = True
                sr_level = level
                reasons.append(f"✓ Near resistance ${level:.2f} ({distance_pct:.2f}%)")
                break

    if near_sr:
        checks_passed += 1
    else:
        warnings.append(f"⚠ Price not near key S/R level")

    # === CHECK 2: Timeframe Agreement (need 2+) ===
    timeframe_agreement = 0
    tf_signals = []

    # 5m trend
    if candles_5m and len(candles_5m) >= 20:
        ema_9 = calculate_ema(candles_5m, 9)
        ema_21 = calculate_ema(candles_5m, 21)
        if ema_9 and ema_21:
            if trade_side == "long" and ema_9 > ema_21:
                timeframe_agreement += 1
                tf_signals.append("5m bullish")
            elif trade_side == "short" and ema_9 < ema_21:
                timeframe_agreement += 1
                tf_signals.append("5m bearish")

    # 15m trend
    if candles_15m and len(candles_15m) >= 20:
        ema_9 = calculate_ema(candles_15m, 9)
        ema_21 = calculate_ema(candles_15m, 21)
        if ema_9 and ema_21:
            if trade_side == "long" and ema_9 > ema_21:
                timeframe_agreement += 1
                tf_signals.append("15m bullish")
            elif trade_side == "short" and ema_9 < ema_21:
                timeframe_agreement += 1
                tf_signals.append("15m bearish")

    # 1h trend
    if candles_1h and len(candles_1h) >= 20:
        ema_9 = calculate_ema(candles_1h, 9)
        ema_21 = calculate_ema(candles_1h, 21)
        if ema_9 and ema_21:
            if trade_side == "long" and ema_9 > ema_21:
                timeframe_agreement += 1
                tf_signals.append("1h bullish")
            elif trade_side == "short" and ema_9 < ema_21:
                timeframe_agreement += 1
                tf_signals.append("1h bearish")

    # 4h trend
    if candles_4h and len(candles_4h) >= 20:
        ema_9 = calculate_ema(candles_4h, 9)
        ema_21 = calculate_ema(candles_4h, 21)
        if ema_9 and ema_21:
            if trade_side == "long" and ema_9 > ema_21:
                timeframe_agreement += 1
                tf_signals.append("4h bullish")
            elif trade_side == "short" and ema_9 < ema_21:
                timeframe_agreement += 1
                tf_signals.append("4h bearish")

    if timeframe_agreement >= 2:
        checks_passed += 1
        reasons.append(f"✓ {timeframe_agreement} timeframes agree: {', '.join(tf_signals)}")
    else:
        warnings.append(f"⚠ Only {timeframe_agreement} timeframes agree")

    # === CHECK 3: Volume Confirmation ===
    volume_confirmed = False

    if candles_5m and len(candles_5m) >= 20:
        recent_volumes = [c.get("volume", 0) for c in candles_5m[-5:]]
        avg_volume = sum(c.get("volume", 0) for c in candles_5m[-20:-5]) / 15 if len(candles_5m) >= 20 else 0

        if avg_volume > 0:
            current_vol = recent_volumes[-1] if recent_volumes else 0
            vol_ratio = current_vol / avg_volume

            if vol_ratio >= 1.2:  # 20% above average
                volume_confirmed = True
                checks_passed += 1
                reasons.append(f"✓ Volume confirmed ({vol_ratio:.1f}x average)")
            else:
                warnings.append(f"⚠ Low volume ({vol_ratio:.1f}x average)")

    # === CHECK 4: RSI Filter ===
    rsi_ok = False
    rsi = calculate_rsi(candles_5m) if candles_5m else None

    if rsi:
        # Mean reversion strategy WANTS RSI extremes
        if strategy_type == "mean_reversion":
            if (trade_side == "long" and rsi < 30) or (trade_side == "short" and rsi > 70):
                rsi_ok = True
                checks_passed += 1
                reasons.append(f"✓ RSI extreme for mean reversion ({rsi:.0f})")
            else:
                warnings.append(f"⚠ RSI {rsi:.0f} not extreme for mean reversion")
        else:
            # Trend/swing strategies should NOT enter at extremes
            if trade_side == "long" and rsi < 70:
                rsi_ok = True
                checks_passed += 1
                reasons.append(f"✓ RSI not overbought ({rsi:.0f})")
            elif trade_side == "short" and rsi > 30:
                rsi_ok = True
                checks_passed += 1
                reasons.append(f"✓ RSI not oversold ({rsi:.0f})")
            elif trade_side == "long" and rsi >= 70:
                warnings.append(f"⚠ RSI overbought ({rsi:.0f}) - bad long entry")
            elif trade_side == "short" and rsi <= 30:
                warnings.append(f"⚠ RSI oversold ({rsi:.0f}) - bad short entry")

    # === Calculate Score ===
    score = int((checks_passed / total_checks) * 100)

    # Determine if entry is valid
    # Need at least 3/4 checks, OR 2/4 with timeframe agreement
    valid = checks_passed >= 3 or (checks_passed >= 2 and timeframe_agreement >= 2)

    return {
        "valid": valid,
        "score": score,
        "checks_passed": checks_passed,
        "total_checks": total_checks,
        "reasons": reasons,
        "warnings": warnings,
        "near_sr": near_sr,
        "sr_level": sr_level,
        "timeframe_agreement": timeframe_agreement,
        "volume_confirmed": volume_confirmed,
        "rsi": rsi,
        "recommendation": "PROCEED" if valid else "WAIT FOR BETTER ENTRY"
    }
