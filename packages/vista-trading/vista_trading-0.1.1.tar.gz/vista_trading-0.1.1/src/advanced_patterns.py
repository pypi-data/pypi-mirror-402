"""
Advanced Pattern Detection Module - Elliott Wave, Fibonacci, Harmonics, Wyckoff.

These are sophisticated pattern recognition algorithms used by professional traders.
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)


# ==================== FIBONACCI RETRACEMENTS ====================

def calculate_fibonacci_levels(candles: List[Dict], lookback: int = 50) -> Dict[str, Any]:
    """Calculate Fibonacci retracement levels from recent swing high/low.
    
    Fib levels are key S/R zones where price often reverses:
    - 23.6% - Shallow retracement (strong trend)
    - 38.2% - Common retracement
    - 50.0% - Psychological level
    - 61.8% - Golden ratio (most important)
    - 78.6% - Deep retracement
    
    Args:
        candles: List of candle dicts with high, low, close
        lookback: Number of candles to find swing points
        
    Returns:
        Dict with fib levels, trend direction, and current price position
    """
    if not candles or len(candles) < lookback:
        return {"levels": {}, "trend": "unknown", "signal": "neutral"}
    
    recent = candles[-lookback:]
    highs = [c["high"] for c in recent]
    lows = [c["low"] for c in recent]
    
    swing_high = max(highs)
    swing_low = min(lows)
    swing_high_idx = highs.index(swing_high)
    swing_low_idx = lows.index(swing_low)
    
    current_price = candles[-1]["close"]
    price_range = swing_high - swing_low
    
    if price_range == 0:
        return {"levels": {}, "trend": "flat", "signal": "neutral"}
    
    # Determine trend direction based on which swing came first
    if swing_low_idx < swing_high_idx:
        # Uptrend: Low came first, retracements from high
        trend = "uptrend"
        levels = {
            "0.0%": swing_high,
            "23.6%": swing_high - (price_range * 0.236),
            "38.2%": swing_high - (price_range * 0.382),
            "50.0%": swing_high - (price_range * 0.500),
            "61.8%": swing_high - (price_range * 0.618),
            "78.6%": swing_high - (price_range * 0.786),
            "100.0%": swing_low,
            # Extensions for targets
            "127.2%": swing_high + (price_range * 0.272),
            "161.8%": swing_high + (price_range * 0.618),
        }
    else:
        # Downtrend: High came first, retracements from low
        trend = "downtrend"
        levels = {
            "0.0%": swing_low,
            "23.6%": swing_low + (price_range * 0.236),
            "38.2%": swing_low + (price_range * 0.382),
            "50.0%": swing_low + (price_range * 0.500),
            "61.8%": swing_low + (price_range * 0.618),
            "78.6%": swing_low + (price_range * 0.786),
            "100.0%": swing_high,
            # Extensions for targets
            "127.2%": swing_low - (price_range * 0.272),
            "161.8%": swing_low - (price_range * 0.618),
        }
    
    # Find nearest fib level to current price
    nearest_level = None
    nearest_distance = float('inf')
    for level_name, level_price in levels.items():
        distance = abs(current_price - level_price)
        if distance < nearest_distance:
            nearest_distance = distance
            nearest_level = level_name
    
    distance_pct = (nearest_distance / current_price) * 100
    
    # Generate signal
    signal = "neutral"
    if distance_pct < 0.5:  # Within 0.5% of fib level
        if trend == "uptrend" and nearest_level in ["38.2%", "50.0%", "61.8%"]:
            signal = "buy_zone"  # Potential long entry
        elif trend == "downtrend" and nearest_level in ["38.2%", "50.0%", "61.8%"]:
            signal = "sell_zone"  # Potential short entry
    
    return {
        "levels": {k: round(v, 2) for k, v in levels.items()},
        "trend": trend,
        "swing_high": round(swing_high, 2),
        "swing_low": round(swing_low, 2),
        "current_price": round(current_price, 2),
        "nearest_level": nearest_level,
        "nearest_price": round(levels.get(nearest_level, current_price), 2),
        "distance_pct": round(distance_pct, 3),
        "signal": signal,
        "golden_pocket": {
            "upper": round(levels.get("61.8%", 0), 2),
            "lower": round(levels.get("65.0%", levels.get("61.8%", 0) - price_range * 0.03), 2)
        }
    }


def find_swing_points(candles: List[Dict], strength: int = 3) -> List[Dict]:
    """Find significant swing highs and lows.
    
    A swing high has 'strength' lower highs on each side.
    A swing low has 'strength' higher lows on each side.
    
    Args:
        candles: List of candles
        strength: Number of candles on each side to confirm swing
        
    Returns:
        List of swing points with type, price, and index
    """
    if len(candles) < strength * 2 + 1:
        return []
    
    swings = []
    
    for i in range(strength, len(candles) - strength):
        # Check for swing high
        is_swing_high = True
        for j in range(1, strength + 1):
            if candles[i]["high"] <= candles[i-j]["high"] or candles[i]["high"] <= candles[i+j]["high"]:
                is_swing_high = False
                break
        
        if is_swing_high:
            swings.append({
                "type": "high",
                "price": candles[i]["high"],
                "index": i,
                "time": candles[i].get("time", candles[i].get("t", 0))
            })
        
        # Check for swing low
        is_swing_low = True
        for j in range(1, strength + 1):
            if candles[i]["low"] >= candles[i-j]["low"] or candles[i]["low"] >= candles[i+j]["low"]:
                is_swing_low = False
                break
        
        if is_swing_low:
            swings.append({
                "type": "low",
                "price": candles[i]["low"],
                "index": i,
                "time": candles[i].get("time", candles[i].get("t", 0))
            })
    
    return sorted(swings, key=lambda x: x["index"])


# ==================== ELLIOTT WAVE ANALYSIS ====================

def detect_elliott_waves(candles: List[Dict], min_wave_pct: float = 1.0) -> Dict[str, Any]:
    """Detect Elliott Wave patterns in price action.

    Elliott Wave Theory:
    - Impulse waves: 5 waves in trend direction (1-2-3-4-5)
    - Corrective waves: 3 waves against trend (A-B-C)

    Wave Rules:
    1. Wave 2 cannot retrace more than 100% of Wave 1
    2. Wave 3 cannot be the shortest impulse wave
    3. Wave 4 cannot overlap Wave 1's territory

    Args:
        candles: List of candle dicts
        min_wave_pct: Minimum wave size as percentage

    Returns:
        Dict with wave count, current position, and next expected move
    """
    if len(candles) < 50:
        return {"pattern": None, "wave_count": 0, "signal": "insufficient_data"}

    # Find swing points for wave counting
    swings = find_swing_points(candles, strength=3)

    if len(swings) < 5:
        return {"pattern": None, "wave_count": len(swings), "signal": "forming"}

    current_price = candles[-1]["close"]

    # Analyze recent swings for wave pattern
    recent_swings = swings[-7:]  # Look at last 7 swing points

    # Determine if we're in an impulse or corrective structure
    # Count alternating highs and lows
    wave_sequence = []
    for swing in recent_swings:
        wave_sequence.append(swing["type"])

    # Check for 5-wave impulse pattern (alternating H-L-H-L-H or L-H-L-H-L)
    impulse_up = ["low", "high", "low", "high", "low"]  # 5-wave up
    impulse_down = ["high", "low", "high", "low", "high"]  # 5-wave down

    pattern = None
    wave_position = None
    next_move = "unknown"

    # Check last 5 swings for impulse pattern
    if len(recent_swings) >= 5:
        last_5_types = [s["type"] for s in recent_swings[-5:]]
        last_5_prices = [s["price"] for s in recent_swings[-5:]]

        if last_5_types == impulse_up:
            # Validate wave rules
            wave1 = last_5_prices[1] - last_5_prices[0]  # Low to High
            wave2 = last_5_prices[1] - last_5_prices[2]  # High to Low
            wave3 = last_5_prices[3] - last_5_prices[2]  # Low to High
            wave4 = last_5_prices[3] - last_5_prices[4]  # High to Low

            # Rule 1: Wave 2 < 100% of Wave 1
            rule1 = wave2 < wave1
            # Rule 2: Wave 3 is not shortest
            rule2 = wave3 >= wave1 or wave3 >= (last_5_prices[4] if len(last_5_prices) > 4 else wave3)
            # Rule 3: Wave 4 doesn't overlap Wave 1
            rule3 = last_5_prices[4] > last_5_prices[1]

            if rule1 and rule3:
                pattern = "impulse_up"
                wave_position = 5
                next_move = "correction_expected"

        elif last_5_types == impulse_down:
            pattern = "impulse_down"
            wave_position = 5
            next_move = "correction_expected"

    # Check for ABC correction
    if len(recent_swings) >= 3 and pattern is None:
        last_3_types = [s["type"] for s in recent_swings[-3:]]

        if last_3_types == ["high", "low", "high"]:
            pattern = "abc_correction_up"
            wave_position = "C"
            next_move = "impulse_down_expected"
        elif last_3_types == ["low", "high", "low"]:
            pattern = "abc_correction_down"
            wave_position = "C"
            next_move = "impulse_up_expected"

    # Generate trading signal
    signal = "neutral"
    if pattern == "impulse_up" and wave_position == 5:
        signal = "bearish"  # Expect correction
    elif pattern == "impulse_down" and wave_position == 5:
        signal = "bullish"  # Expect correction up
    elif pattern == "abc_correction_down":
        signal = "bullish"  # Expect impulse up
    elif pattern == "abc_correction_up":
        signal = "bearish"  # Expect impulse down

    return {
        "pattern": pattern,
        "wave_position": wave_position,
        "wave_count": len(swings),
        "next_move": next_move,
        "signal": signal,
        "swings": recent_swings[-5:],
        "current_price": round(current_price, 2)
    }


# ==================== HARMONIC PATTERNS ====================

def detect_harmonic_patterns(candles: List[Dict]) -> Dict[str, Any]:
    """Detect harmonic patterns (Gartley, Bat, Butterfly, Crab).

    Harmonic patterns use Fibonacci ratios between 5 points (X, A, B, C, D):

    GARTLEY:
    - XA: Impulse move
    - AB: 61.8% retracement of XA
    - BC: 38.2-88.6% retracement of AB
    - CD: 127.2-161.8% extension of BC
    - D: 78.6% retracement of XA (entry point)

    BAT:
    - AB: 38.2-50% of XA
    - BC: 38.2-88.6% of AB
    - D: 88.6% of XA

    BUTTERFLY:
    - AB: 78.6% of XA
    - BC: 38.2-88.6% of AB
    - D: 127.2-161.8% of XA (beyond X)

    CRAB:
    - AB: 38.2-61.8% of XA
    - BC: 38.2-88.6% of AB
    - D: 161.8% of XA (extreme extension)

    Args:
        candles: List of candle dicts

    Returns:
        Dict with pattern type, completion %, and projected reversal zone
    """
    if len(candles) < 30:
        return {"pattern": None, "signal": "insufficient_data"}

    # Find swing points
    swings = find_swing_points(candles, strength=2)

    if len(swings) < 5:
        return {"pattern": None, "signal": "need_more_swings", "swing_count": len(swings)}

    # Get last 5 swing points as potential XABCD
    recent = swings[-5:]

    # Extract prices
    X = recent[0]["price"]
    A = recent[1]["price"]
    B = recent[2]["price"]
    C = recent[3]["price"]
    D_current = recent[4]["price"]  # Current potential D point

    current_price = candles[-1]["close"]

    # Calculate retracement ratios
    XA = abs(A - X)
    AB = abs(B - A)
    BC = abs(C - B)
    CD = abs(D_current - C)

    if XA == 0:
        return {"pattern": None, "signal": "invalid_xa"}

    AB_ratio = AB / XA
    BC_ratio = BC / AB if AB > 0 else 0

    # Determine pattern direction (bullish or bearish)
    is_bullish = recent[0]["type"] == "high"  # X is high = bullish pattern forming

    # Check for each pattern
    patterns_found = []

    # GARTLEY: AB=61.8%, D=78.6%
    if 0.55 <= AB_ratio <= 0.68:
        D_target = X - (XA * 0.786) if is_bullish else X + (XA * 0.786)
        completion = abs(current_price - D_target) / XA * 100
        if completion < 5:  # Within 5% of completion
            patterns_found.append({
                "name": "Gartley",
                "direction": "bullish" if is_bullish else "bearish",
                "completion_pct": round(100 - completion, 1),
                "prz": round(D_target, 2),  # Potential Reversal Zone
                "stop": round(X, 2),
                "target1": round(A, 2),
                "target2": round(C, 2)
            })

    # BAT: AB=38.2-50%, D=88.6%
    if 0.35 <= AB_ratio <= 0.55:
        D_target = X - (XA * 0.886) if is_bullish else X + (XA * 0.886)
        completion = abs(current_price - D_target) / XA * 100
        if completion < 5:
            patterns_found.append({
                "name": "Bat",
                "direction": "bullish" if is_bullish else "bearish",
                "completion_pct": round(100 - completion, 1),
                "prz": round(D_target, 2),
                "stop": round(X, 2),
                "target1": round(A, 2)
            })

    # BUTTERFLY: AB=78.6%, D=127.2-161.8%
    if 0.72 <= AB_ratio <= 0.85:
        D_target = X - (XA * 1.272) if is_bullish else X + (XA * 1.272)
        completion = abs(current_price - D_target) / XA * 100
        if completion < 8:  # Wider zone for extensions
            patterns_found.append({
                "name": "Butterfly",
                "direction": "bullish" if is_bullish else "bearish",
                "completion_pct": round(100 - completion, 1),
                "prz": round(D_target, 2),
                "stop": round(X - (XA * 0.2) if is_bullish else X + (XA * 0.2), 2),
                "target1": round(A, 2)
            })

    # CRAB: D=161.8% (most extreme)
    if 0.35 <= AB_ratio <= 0.65:
        D_target = X - (XA * 1.618) if is_bullish else X + (XA * 1.618)
        completion = abs(current_price - D_target) / XA * 100
        if completion < 10:
            patterns_found.append({
                "name": "Crab",
                "direction": "bullish" if is_bullish else "bearish",
                "completion_pct": round(100 - completion, 1),
                "prz": round(D_target, 2),
                "stop": round(D_target * 0.97 if is_bullish else D_target * 1.03, 2),
                "target1": round(A, 2)
            })

    if not patterns_found:
        return {
            "pattern": None,
            "signal": "no_harmonic",
            "ratios": {
                "AB": round(AB_ratio, 3),
                "BC": round(BC_ratio, 3)
            }
        }

    # Return best pattern (highest completion)
    best = max(patterns_found, key=lambda x: x["completion_pct"])

    return {
        "pattern": best["name"],
        "direction": best["direction"],
        "completion_pct": best["completion_pct"],
        "prz": best["prz"],
        "stop_loss": best["stop"],
        "target": best.get("target1"),
        "signal": "long" if best["direction"] == "bullish" else "short",
        "all_patterns": patterns_found
    }


# ==================== WYCKOFF ANALYSIS ====================

def detect_wyckoff_phase(candles: List[Dict]) -> Dict[str, Any]:
    """Detect Wyckoff market phase and key events.

    Wyckoff Market Cycle:
    1. ACCUMULATION: Smart money buying after downtrend
       - PS (Preliminary Support): First buying appears
       - SC (Selling Climax): Panic selling, high volume
       - AR (Automatic Rally): Dead cat bounce
       - ST (Secondary Test): Retest of lows
       - SPRING: False breakdown (best entry)
       - SOS (Sign of Strength): Break above range

    2. MARKUP: Uptrend phase
       - Higher highs, higher lows
       - Increasing volume on up moves

    3. DISTRIBUTION: Smart money selling at tops
       - PSY (Preliminary Supply): First selling
       - BC (Buying Climax): Euphoric buying, high volume
       - AR (Automatic Reaction): Pullback
       - ST (Secondary Test): Retest of highs
       - UPTHRUST: False breakout (short signal)
       - SOW (Sign of Weakness): Break below range

    4. MARKDOWN: Downtrend phase
       - Lower highs, lower lows

    Args:
        candles: List of candles (recommend 100+)

    Returns:
        Dict with phase, events, and trading signals
    """
    if len(candles) < 50:
        return {"phase": "unknown", "signal": "insufficient_data"}

    # Calculate key metrics
    closes = [c["close"] for c in candles]
    highs = [c["high"] for c in candles]
    lows = [c["low"] for c in candles]
    volumes = [c.get("volume", c.get("v", 0)) for c in candles]

    current_price = closes[-1]
    avg_volume = sum(volumes[-20:]) / 20 if len(volumes) >= 20 else sum(volumes) / len(volumes)

    # Define range (last 50 candles)
    range_high = max(highs[-50:])
    range_low = min(lows[-50:])
    range_size = range_high - range_low

    if range_size == 0:
        return {"phase": "flat", "signal": "neutral"}

    # Price position in range (0 = bottom, 1 = top)
    range_position = (current_price - range_low) / range_size

    # Volume analysis
    recent_vol = sum(volumes[-5:]) / 5
    vol_ratio = recent_vol / avg_volume if avg_volume > 0 else 1

    # Trend analysis (using 20 and 50 period)
    sma_20 = sum(closes[-20:]) / 20
    sma_50 = sum(closes[-50:]) / 50

    # Detect phase based on price action and volume
    events = []
    phase = "unknown"
    signal = "neutral"

    # Check for ACCUMULATION signs
    if range_position < 0.3:  # Price near bottom of range
        # Check for Spring (false breakdown with recovery)
        recent_low = min(lows[-10:])
        if recent_low < range_low and current_price > recent_low:
            events.append("SPRING detected - potential reversal")
            phase = "accumulation"
            signal = "bullish"

        # Check for Selling Climax (high volume at lows)
        if vol_ratio > 2.0 and range_position < 0.2:
            events.append("Selling Climax - panic selling")
            phase = "accumulation"
            signal = "watch_for_spring"

        # Secondary Test
        if 0.1 < range_position < 0.25 and vol_ratio < 1.0:
            events.append("Secondary Test - low volume retest")
            phase = "accumulation"
            signal = "bullish"

    # Check for DISTRIBUTION signs
    elif range_position > 0.7:  # Price near top of range
        # Check for Upthrust (false breakout with rejection)
        recent_high = max(highs[-10:])
        if recent_high > range_high and current_price < recent_high:
            events.append("UPTHRUST detected - potential reversal")
            phase = "distribution"
            signal = "bearish"

        # Check for Buying Climax (high volume at highs)
        if vol_ratio > 2.0 and range_position > 0.8:
            events.append("Buying Climax - euphoric buying")
            phase = "distribution"
            signal = "watch_for_upthrust"

        # Secondary Test at highs
        if 0.75 < range_position < 0.9 and vol_ratio < 1.0:
            events.append("Secondary Test of highs")
            phase = "distribution"
            signal = "bearish"

    # Check for MARKUP (uptrend)
    elif sma_20 > sma_50 and current_price > sma_20:
        phase = "markup"
        signal = "bullish_trend"
        events.append("Markup phase - uptrend in progress")

        # Sign of Strength
        if range_position > 0.5 and vol_ratio > 1.2:
            events.append("Sign of Strength - strong buying")

    # Check for MARKDOWN (downtrend)
    elif sma_20 < sma_50 and current_price < sma_20:
        phase = "markdown"
        signal = "bearish_trend"
        events.append("Markdown phase - downtrend in progress")

        # Sign of Weakness
        if range_position < 0.5 and vol_ratio > 1.2:
            events.append("Sign of Weakness - strong selling")

    # Ranging market
    else:
        phase = "ranging"
        signal = "neutral"
        events.append("Trading range - wait for breakout")

    return {
        "phase": phase,
        "signal": signal,
        "events": events,
        "range_high": round(range_high, 2),
        "range_low": round(range_low, 2),
        "range_position": round(range_position, 3),
        "volume_ratio": round(vol_ratio, 2),
        "current_price": round(current_price, 2),
        "recommendation": _get_wyckoff_recommendation(phase, signal, range_position)
    }


def _get_wyckoff_recommendation(phase: str, signal: str, range_pos: float) -> str:
    """Get actionable recommendation based on Wyckoff analysis."""
    if phase == "accumulation":
        if signal == "bullish":
            return "LOOK FOR LONG - Spring/ST detected, smart money accumulating"
        return "WATCH - Accumulation in progress, wait for spring"
    elif phase == "distribution":
        if signal == "bearish":
            return "LOOK FOR SHORT - Upthrust/ST detected, smart money distributing"
        return "WATCH - Distribution in progress, wait for upthrust"
    elif phase == "markup":
        return "TREND LONG - Buy dips to SMA20"
    elif phase == "markdown":
        return "TREND SHORT - Sell rallies to SMA20"
    else:
        return "WAIT - No clear phase, stay on sidelines"


# ==================== ORDER FLOW HEATMAP ====================

def analyze_order_flow_heatmap(
    order_book: Dict[str, List],
    recent_trades: List[Dict] = None,
    price_levels: int = 20
) -> Dict[str, Any]:
    """Analyze order book depth as a heatmap to find liquidity clusters.

    Order Flow Heatmap shows:
    - WHERE liquidity is concentrated (whale walls)
    - Potential support/resistance from order clusters
    - Absorption zones (orders getting filled)
    - Vacuum zones (low liquidity = fast moves)

    Args:
        order_book: Dict with 'bids' and 'asks' lists
        recent_trades: Optional list of recent trades
        price_levels: Number of price levels to analyze

    Returns:
        Dict with heatmap data, key levels, and signals
    """
    bids = order_book.get("bids", [])
    asks = order_book.get("asks", [])

    if not bids or not asks:
        return {"signal": "no_data", "heatmap": []}

    # Parse order book data
    bid_levels = []
    ask_levels = []

    for bid in bids[:price_levels]:
        if isinstance(bid, dict):
            price, size = bid.get("price", 0), bid.get("size", 0)
        else:
            price, size = float(bid[0]), float(bid[1])
        bid_levels.append({"price": price, "size": size, "side": "bid"})

    for ask in asks[:price_levels]:
        if isinstance(ask, dict):
            price, size = ask.get("price", 0), ask.get("size", 0)
        else:
            price, size = float(ask[0]), float(ask[1])
        ask_levels.append({"price": price, "size": size, "side": "ask"})

    if not bid_levels or not ask_levels:
        return {"signal": "no_data", "heatmap": []}

    # Calculate statistics
    total_bid_size = sum(b["size"] for b in bid_levels)
    total_ask_size = sum(a["size"] for a in ask_levels)

    # Find large orders (walls)
    avg_bid_size = total_bid_size / len(bid_levels) if bid_levels else 0
    avg_ask_size = total_ask_size / len(ask_levels) if ask_levels else 0

    bid_walls = [b for b in bid_levels if b["size"] > avg_bid_size * 3]
    ask_walls = [a for a in ask_levels if a["size"] > avg_ask_size * 3]

    # Find vacuum zones (very low liquidity)
    bid_vacuums = [b for b in bid_levels if b["size"] < avg_bid_size * 0.3]
    ask_vacuums = [a for a in ask_levels if a["size"] < avg_ask_size * 0.3]

    # Calculate imbalance
    imbalance = (total_bid_size - total_ask_size) / (total_bid_size + total_ask_size) if (total_bid_size + total_ask_size) > 0 else 0

    # Get current spread
    best_bid = bid_levels[0]["price"] if bid_levels else 0
    best_ask = ask_levels[0]["price"] if ask_levels else 0
    spread = best_ask - best_bid
    spread_pct = (spread / best_bid * 100) if best_bid > 0 else 0

    # Analyze recent trades if available
    trade_flow = {"buy_volume": 0, "sell_volume": 0, "net_flow": 0}
    if recent_trades:
        for trade in recent_trades[-50:]:  # Last 50 trades
            size = trade.get("size", trade.get("sz", 0))
            side = trade.get("side", "")
            if side == "buy" or side == "B":
                trade_flow["buy_volume"] += float(size)
            else:
                trade_flow["sell_volume"] += float(size)
        trade_flow["net_flow"] = trade_flow["buy_volume"] - trade_flow["sell_volume"]

    # Generate signal
    signal = "neutral"
    reasons = []

    # Strong bid wall = support
    if bid_walls:
        strongest_bid_wall = max(bid_walls, key=lambda x: x["size"])
        reasons.append(f"Bid wall at ${strongest_bid_wall['price']:.2f} ({strongest_bid_wall['size']:.2f})")
        signal = "support_below"

    # Strong ask wall = resistance
    if ask_walls:
        strongest_ask_wall = max(ask_walls, key=lambda x: x["size"])
        reasons.append(f"Ask wall at ${strongest_ask_wall['price']:.2f} ({strongest_ask_wall['size']:.2f})")
        if signal == "support_below":
            signal = "range_bound"
        else:
            signal = "resistance_above"

    # Imbalance signals
    if imbalance > 0.3:
        signal = "bullish_imbalance"
        reasons.append(f"Strong bid pressure ({imbalance:.0%})")
    elif imbalance < -0.3:
        signal = "bearish_imbalance"
        reasons.append(f"Strong ask pressure ({imbalance:.0%})")

    # Vacuum zones (fast move potential)
    if ask_vacuums and len(ask_vacuums) > 3:
        reasons.append("Ask vacuum above - potential fast move up")
    if bid_vacuums and len(bid_vacuums) > 3:
        reasons.append("Bid vacuum below - potential fast move down")

    return {
        "signal": signal,
        "imbalance": round(imbalance, 3),
        "imbalance_pct": f"{imbalance * 100:.1f}%",
        "total_bid_size": round(total_bid_size, 2),
        "total_ask_size": round(total_ask_size, 2),
        "bid_walls": [{"price": w["price"], "size": w["size"]} for w in bid_walls[:3]],
        "ask_walls": [{"price": w["price"], "size": w["size"]} for w in ask_walls[:3]],
        "spread_pct": round(spread_pct, 4),
        "best_bid": best_bid,
        "best_ask": best_ask,
        "trade_flow": trade_flow,
        "reasons": reasons,
        "recommendation": _get_orderflow_recommendation(signal, imbalance, bid_walls, ask_walls)
    }


def _get_orderflow_recommendation(signal: str, imbalance: float, bid_walls: list, ask_walls: list) -> str:
    """Get actionable recommendation from order flow analysis."""
    if signal == "bullish_imbalance":
        return "BULLISH - Strong buying pressure, look for long entries"
    elif signal == "bearish_imbalance":
        return "BEARISH - Strong selling pressure, look for short entries"
    elif signal == "support_below" and bid_walls:
        return f"SUPPORT at ${bid_walls[0]['price']:.2f} - Consider longs above this level"
    elif signal == "resistance_above" and ask_walls:
        return f"RESISTANCE at ${ask_walls[0]['price']:.2f} - Consider shorts below this level"
    elif signal == "range_bound":
        return "RANGE - Fade extremes, buy support, sell resistance"
    return "NEUTRAL - No clear order flow edge"


# ==================== COMBINED ANALYSIS ====================

def get_advanced_analysis(candles: List[Dict], order_book: Dict = None) -> Dict[str, Any]:
    """Run all advanced pattern detection and return combined analysis.

    Args:
        candles: List of candle data
        order_book: Optional order book data

    Returns:
        Combined analysis from all modules
    """
    result = {
        "fibonacci": calculate_fibonacci_levels(candles),
        "elliott_wave": detect_elliott_waves(candles),
        "harmonic": detect_harmonic_patterns(candles),
        "wyckoff": detect_wyckoff_phase(candles)
    }

    if order_book:
        result["order_flow"] = analyze_order_flow_heatmap(order_book)

    # Generate combined signal
    signals = []

    # Collect all signals
    if result["fibonacci"].get("signal") not in ["neutral", "unknown"]:
        signals.append(("fib", result["fibonacci"]["signal"]))
    if result["elliott_wave"].get("signal") not in ["neutral", "insufficient_data", "forming"]:
        signals.append(("elliott", result["elliott_wave"]["signal"]))
    if result["harmonic"].get("signal") not in ["neutral", "insufficient_data", "no_harmonic"]:
        signals.append(("harmonic", result["harmonic"]["signal"]))
    if result["wyckoff"].get("signal") not in ["neutral", "insufficient_data"]:
        signals.append(("wyckoff", result["wyckoff"]["signal"]))

    # Count bullish vs bearish
    bullish = sum(1 for s in signals if "bullish" in s[1].lower() or s[1] in ["long", "buy_zone"])
    bearish = sum(1 for s in signals if "bearish" in s[1].lower() or s[1] in ["short", "sell_zone"])

    if bullish > bearish and bullish >= 2:
        result["combined_signal"] = "BULLISH"
        result["confidence"] = bullish / len(signals) if signals else 0
    elif bearish > bullish and bearish >= 2:
        result["combined_signal"] = "BEARISH"
        result["confidence"] = bearish / len(signals) if signals else 0
    else:
        result["combined_signal"] = "NEUTRAL"
        result["confidence"] = 0

    result["signals_breakdown"] = signals

    return result

