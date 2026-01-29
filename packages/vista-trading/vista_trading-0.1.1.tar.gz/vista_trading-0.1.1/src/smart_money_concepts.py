"""
Smart Money Concepts (SMC) - Institutional Trading Logic

This module implements concepts used by institutional traders:
1. Market Structure - BOS (Break of Structure), CHoCH (Change of Character)
2. Order Blocks - Where institutions placed large orders
3. Fair Value Gaps (FVG) - Imbalances that price tends to fill
4. Liquidity Sweeps - Stop hunts before real moves
5. Premium/Discount Zones - Where smart money buys/sells

These concepts identify WHERE institutions are likely positioned,
giving retail traders an edge by trading alongside smart money.
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class StructureType(Enum):
    """Market structure types."""
    BULLISH = "bullish"
    BEARISH = "bearish"
    RANGING = "ranging"


class StructureBreak(Enum):
    """Types of structure breaks."""
    BOS = "bos"  # Break of Structure - continuation
    CHOCH = "choch"  # Change of Character - reversal
    NONE = "none"


@dataclass
class SwingPoint:
    """A swing high or swing low point."""
    index: int
    price: float
    is_high: bool  # True = swing high, False = swing low
    strength: int  # How many candles on each side confirm it


@dataclass
class OrderBlock:
    """An order block - where institutions placed orders."""
    index: int
    high: float
    low: float
    is_bullish: bool  # Bullish OB = demand, Bearish OB = supply
    volume: float
    strength: float  # 0-1, how strong the OB is
    mitigated: bool = False  # Has price returned and tested it?


@dataclass
class FairValueGap:
    """A fair value gap (imbalance)."""
    index: int
    high: float  # Upper bound of gap
    low: float   # Lower bound of gap
    is_bullish: bool  # Bullish FVG = gap up, Bearish FVG = gap down
    filled_pct: float = 0.0  # How much has been filled (0-1)


def find_swing_points(candles: List[Dict], lookback: int = 3) -> List[SwingPoint]:
    """
    Find swing highs and swing lows in price data.
    
    A swing high has 'lookback' lower highs on each side.
    A swing low has 'lookback' higher lows on each side.
    
    Args:
        candles: OHLCV candle data
        lookback: Number of candles on each side to confirm swing
        
    Returns:
        List of SwingPoint objects
    """
    if len(candles) < (lookback * 2 + 1):
        return []
    
    swings = []
    highs = [c.get("high", c.get("h", 0)) for c in candles]
    lows = [c.get("low", c.get("l", 0)) for c in candles]
    
    for i in range(lookback, len(candles) - lookback):
        # Check for swing high
        is_swing_high = True
        for j in range(1, lookback + 1):
            if highs[i] <= highs[i - j] or highs[i] <= highs[i + j]:
                is_swing_high = False
                break
        
        if is_swing_high:
            swings.append(SwingPoint(
                index=i,
                price=highs[i],
                is_high=True,
                strength=lookback
            ))
        
        # Check for swing low
        is_swing_low = True
        for j in range(1, lookback + 1):
            if lows[i] >= lows[i - j] or lows[i] >= lows[i + j]:
                is_swing_low = False
                break
        
        if is_swing_low:
            swings.append(SwingPoint(
                index=i,
                price=lows[i],
                is_high=False,
                strength=lookback
            ))
    
    return sorted(swings, key=lambda x: x.index)


def detect_market_structure(candles: List[Dict], lookback: int = 3) -> Dict[str, Any]:
    """
    Detect current market structure using SMC concepts.
    
    Market Structure Rules:
    - Bullish: Higher Highs (HH) and Higher Lows (HL)
    - Bearish: Lower Highs (LH) and Lower Lows (LL)
    - BOS (Break of Structure): Price breaks previous swing in trend direction
    - CHoCH (Change of Character): Price breaks previous swing AGAINST trend
    
    Args:
        candles: OHLCV candle data (minimum 50 candles recommended)
        lookback: Swing detection sensitivity
        
    Returns:
        Dict with structure analysis
    """
    if len(candles) < 20:
        return {"structure": "unknown", "bias": "neutral", "confidence": 0}
    
    swings = find_swing_points(candles, lookback)
    
    if len(swings) < 4:
        return {"structure": "unknown", "bias": "neutral", "confidence": 0}
    
    # Separate swing highs and lows
    swing_highs = [s for s in swings if s.is_high]
    swing_lows = [s for s in swings if not s.is_high]
    
    if len(swing_highs) < 2 or len(swing_lows) < 2:
        return {"structure": "unknown", "bias": "neutral", "confidence": 0}
    
    # Get recent swings for structure analysis
    recent_highs = swing_highs[-4:] if len(swing_highs) >= 4 else swing_highs
    recent_lows = swing_lows[-4:] if len(swing_lows) >= 4 else swing_lows
    
    # Count HH/HL and LH/LL patterns
    hh_count = sum(1 for i in range(1, len(recent_highs))
                   if recent_highs[i].price > recent_highs[i-1].price)
    hl_count = sum(1 for i in range(1, len(recent_lows))
                   if recent_lows[i].price > recent_lows[i-1].price)
    lh_count = sum(1 for i in range(1, len(recent_highs))
                   if recent_highs[i].price < recent_highs[i-1].price)
    ll_count = sum(1 for i in range(1, len(recent_lows))
                   if recent_lows[i].price < recent_lows[i-1].price)

    # Determine structure
    bullish_score = hh_count + hl_count
    bearish_score = lh_count + ll_count

    current_price = candles[-1].get("close", candles[-1].get("c", 0))
    last_swing_high = swing_highs[-1].price if swing_highs else 0
    last_swing_low = swing_lows[-1].price if swing_lows else 0
    prev_swing_high = swing_highs[-2].price if len(swing_highs) >= 2 else last_swing_high
    prev_swing_low = swing_lows[-2].price if len(swing_lows) >= 2 else last_swing_low

    # Detect BOS or CHoCH
    structure_break = StructureBreak.NONE
    break_level = 0

    if bullish_score > bearish_score:
        structure = StructureType.BULLISH
        # In bullish structure, breaking below prev swing low = CHoCH
        if current_price < prev_swing_low:
            structure_break = StructureBreak.CHOCH
            break_level = prev_swing_low
        # Breaking above last swing high = BOS (continuation)
        elif current_price > last_swing_high:
            structure_break = StructureBreak.BOS
            break_level = last_swing_high
    elif bearish_score > bullish_score:
        structure = StructureType.BEARISH
        # In bearish structure, breaking above prev swing high = CHoCH
        if current_price > prev_swing_high:
            structure_break = StructureBreak.CHOCH
            break_level = prev_swing_high
        # Breaking below last swing low = BOS (continuation)
        elif current_price < last_swing_low:
            structure_break = StructureBreak.BOS
            break_level = last_swing_low
    else:
        structure = StructureType.RANGING

    # Calculate confidence
    total_swings = max(len(recent_highs) + len(recent_lows) - 2, 1)
    if structure == StructureType.BULLISH:
        confidence = bullish_score / total_swings
    elif structure == StructureType.BEARISH:
        confidence = bearish_score / total_swings
    else:
        confidence = 0.3

    # Determine bias based on structure and breaks
    if structure_break == StructureBreak.CHOCH:
        # CHoCH suggests reversal - flip bias
        bias = "bearish" if structure == StructureType.BULLISH else "bullish"
        confidence *= 0.8  # Slightly less confident on reversal
    elif structure_break == StructureBreak.BOS:
        # BOS confirms trend
        bias = structure.value
        confidence = min(confidence * 1.2, 1.0)  # More confident
    else:
        bias = structure.value if structure != StructureType.RANGING else "neutral"

    return {
        "structure": structure.value,
        "bias": bias,
        "confidence": round(confidence, 2),
        "structure_break": structure_break.value,
        "break_level": break_level,
        "last_swing_high": last_swing_high,
        "last_swing_low": last_swing_low,
        "prev_swing_high": prev_swing_high,
        "prev_swing_low": prev_swing_low,
        "hh_count": hh_count,
        "hl_count": hl_count,
        "lh_count": lh_count,
        "ll_count": ll_count,
        "swing_points": [(s.index, s.price, "high" if s.is_high else "low") for s in swings[-10:]]
    }


def detect_order_blocks(candles: List[Dict], structure: Dict = None) -> List[Dict]:
    """
    Detect Order Blocks - candles where institutions placed large orders.

    Bullish Order Block: Last bearish candle before a strong bullish move
    Bearish Order Block: Last bullish candle before a strong bearish move

    Args:
        candles: OHLCV data
        structure: Market structure context (optional)

    Returns:
        List of order block dictionaries
    """
    if len(candles) < 10:
        return []

    order_blocks = []

    for i in range(2, len(candles) - 2):
        c_prev = candles[i - 1]
        c_curr = candles[i]
        c_next = candles[i + 1]
        c_next2 = candles[i + 2] if i + 2 < len(candles) else c_next

        prev_open = c_prev.get("open", c_prev.get("o", 0))
        prev_close = c_prev.get("close", c_prev.get("c", 0))
        prev_high = c_prev.get("high", c_prev.get("h", 0))
        prev_low = c_prev.get("low", c_prev.get("l", 0))
        prev_vol = c_prev.get("volume", c_prev.get("v", 0))

        curr_open = c_curr.get("open", c_curr.get("o", 0))
        curr_close = c_curr.get("close", c_curr.get("c", 0))
        curr_high = c_curr.get("high", c_curr.get("h", 0))
        curr_low = c_curr.get("low", c_curr.get("l", 0))

        next_close = c_next.get("close", c_next.get("c", 0))
        next2_close = c_next2.get("close", c_next2.get("c", 0))

        # Average volume for context
        avg_vol = sum(c.get("volume", c.get("v", 0)) for c in candles[max(0,i-10):i]) / 10

        prev_is_bearish = prev_close < prev_open
        prev_is_bullish = prev_close > prev_open

        # Strong move = next candles move significantly in one direction
        move_up = (next2_close - curr_close) / curr_close * 100 if curr_close else 0
        move_down = (curr_close - next2_close) / curr_close * 100 if curr_close else 0

        # Bullish Order Block: Bearish candle followed by strong bullish move
        if prev_is_bearish and move_up > 0.5:  # >0.5% move
            strength = min(move_up / 2, 1.0)  # Normalize strength
            if prev_vol > avg_vol * 1.2:  # Volume confirmation
                strength = min(strength * 1.3, 1.0)

            order_blocks.append({
                "index": i - 1,
                "high": prev_high,
                "low": prev_low,
                "mid": (prev_high + prev_low) / 2,
                "is_bullish": True,
                "type": "demand",
                "strength": round(strength, 2),
                "volume_ratio": round(prev_vol / avg_vol, 2) if avg_vol else 1,
                "mitigated": False
            })

        # Bearish Order Block: Bullish candle followed by strong bearish move
        if prev_is_bullish and move_down > 0.5:
            strength = min(move_down / 2, 1.0)
            if prev_vol > avg_vol * 1.2:
                strength = min(strength * 1.3, 1.0)

            order_blocks.append({
                "index": i - 1,
                "high": prev_high,
                "low": prev_low,
                "mid": (prev_high + prev_low) / 2,
                "is_bullish": False,
                "type": "supply",
                "strength": round(strength, 2),
                "volume_ratio": round(prev_vol / avg_vol, 2) if avg_vol else 1,
                "mitigated": False
            })

    # Check which OBs have been mitigated (price returned to them)
    current_price = candles[-1].get("close", candles[-1].get("c", 0))
    for ob in order_blocks:
        # OB is mitigated if price has returned to it after creation
        candles_after_ob = candles[ob["index"] + 3:]  # Give it a few candles
        for c in candles_after_ob:
            c_low = c.get("low", c.get("l", 0))
            c_high = c.get("high", c.get("h", 0))
            if ob["is_bullish"] and c_low <= ob["high"]:
                ob["mitigated"] = True
                break
            elif not ob["is_bullish"] and c_high >= ob["low"]:
                ob["mitigated"] = True
                break

    # Return only unmitigated OBs (still valid) sorted by strength
    valid_obs = [ob for ob in order_blocks if not ob["mitigated"]]
    return sorted(valid_obs, key=lambda x: x["strength"], reverse=True)[:5]


def detect_fair_value_gaps(candles: List[Dict]) -> List[Dict]:
    """
    Detect Fair Value Gaps (FVG) - price imbalances that tend to get filled.

    Bullish FVG: Gap between candle 1's high and candle 3's low (in uptrend)
    Bearish FVG: Gap between candle 1's low and candle 3's high (in downtrend)

    Price tends to return to fill these gaps before continuing.

    Args:
        candles: OHLCV data

    Returns:
        List of FVG dictionaries
    """
    if len(candles) < 5:
        return []

    fvgs = []

    for i in range(2, len(candles)):
        c1 = candles[i - 2]  # First candle
        c2 = candles[i - 1]  # Middle candle (impulse)
        c3 = candles[i]      # Third candle

        c1_high = c1.get("high", c1.get("h", 0))
        c1_low = c1.get("low", c1.get("l", 0))
        c2_high = c2.get("high", c2.get("h", 0))
        c2_low = c2.get("low", c2.get("l", 0))
        c3_high = c3.get("high", c3.get("h", 0))
        c3_low = c3.get("low", c3.get("l", 0))

        # Bullish FVG: c3's low is above c1's high (gap in between)
        if c3_low > c1_high:
            gap_size = c3_low - c1_high
            gap_pct = (gap_size / c1_high) * 100 if c1_high else 0

            if gap_pct > 0.1:  # Minimum 0.1% gap
                fvgs.append({
                    "index": i - 1,
                    "high": c3_low,  # Upper bound of gap
                    "low": c1_high,  # Lower bound of gap
                    "mid": (c3_low + c1_high) / 2,
                    "is_bullish": True,
                    "gap_pct": round(gap_pct, 2),
                    "filled_pct": 0.0
                })

        # Bearish FVG: c3's high is below c1's low (gap in between)
        if c3_high < c1_low:
            gap_size = c1_low - c3_high
            gap_pct = (gap_size / c1_low) * 100 if c1_low else 0

            if gap_pct > 0.1:
                fvgs.append({
                    "index": i - 1,
                    "high": c1_low,  # Upper bound of gap
                    "low": c3_high,  # Lower bound of gap
                    "mid": (c1_low + c3_high) / 2,
                    "is_bullish": False,
                    "gap_pct": round(gap_pct, 2),
                    "filled_pct": 0.0
                })

    # Calculate fill percentage for each FVG
    current_price = candles[-1].get("close", candles[-1].get("c", 0))
    for fvg in fvgs:
        candles_after = candles[fvg["index"] + 2:]
        gap_range = fvg["high"] - fvg["low"]

        for c in candles_after:
            c_high = c.get("high", c.get("h", 0))
            c_low = c.get("low", c.get("l", 0))

            if fvg["is_bullish"]:
                # Price needs to come down into the gap
                if c_low <= fvg["high"]:
                    filled = min((fvg["high"] - c_low) / gap_range, 1.0) if gap_range else 0
                    fvg["filled_pct"] = max(fvg["filled_pct"], filled)
            else:
                # Price needs to come up into the gap
                if c_high >= fvg["low"]:
                    filled = min((c_high - fvg["low"]) / gap_range, 1.0) if gap_range else 0
                    fvg["filled_pct"] = max(fvg["filled_pct"], filled)

        fvg["filled_pct"] = round(fvg["filled_pct"], 2)

    # Return unfilled or partially filled FVGs (< 80% filled)
    valid_fvgs = [fvg for fvg in fvgs if fvg["filled_pct"] < 0.8]
    return sorted(valid_fvgs, key=lambda x: x["index"], reverse=True)[:5]


def detect_liquidity_levels(candles: List[Dict], swings: List[SwingPoint] = None) -> Dict[str, Any]:
    """
    Detect liquidity levels - where stop losses are likely clustered.

    Liquidity exists:
    - Above swing highs (shorts' stop losses)
    - Below swing lows (longs' stop losses)
    - At round numbers

    Smart money often sweeps these levels before reversing.

    Args:
        candles: OHLCV data
        swings: Pre-calculated swing points (optional)

    Returns:
        Dict with liquidity analysis
    """
    if len(candles) < 20:
        return {"buy_side": [], "sell_side": [], "swept": []}

    if swings is None:
        swings = find_swing_points(candles, lookback=3)

    current_price = candles[-1].get("close", candles[-1].get("c", 0))
    recent_high = max(c.get("high", c.get("h", 0)) for c in candles[-20:])
    recent_low = min(c.get("low", c.get("l", 0)) for c in candles[-20:])

    # Buy-side liquidity (above swing highs - shorts' stops)
    buy_side_liq = []
    for swing in swings:
        if swing.is_high and swing.price > current_price:
            buy_side_liq.append({
                "level": swing.price,
                "strength": swing.strength,
                "distance_pct": ((swing.price - current_price) / current_price) * 100
            })

    # Sell-side liquidity (below swing lows - longs' stops)
    sell_side_liq = []
    for swing in swings:
        if not swing.is_high and swing.price < current_price:
            sell_side_liq.append({
                "level": swing.price,
                "strength": swing.strength,
                "distance_pct": ((current_price - swing.price) / current_price) * 100
            })

    # Detect recent liquidity sweeps (price went past a level then reversed)
    swept_levels = []
    for i in range(-10, -1):
        if i >= -len(candles):
            c = candles[i]
            c_high = c.get("high", c.get("h", 0))
            c_low = c.get("low", c.get("l", 0))
            c_close = c.get("close", c.get("c", 0))

            # Check if wick swept above a swing high then closed below
            for swing in swings:
                if swing.is_high and c_high > swing.price > c_close:
                    swept_levels.append({
                        "level": swing.price,
                        "type": "buy_side_swept",
                        "candle_idx": i,
                        "implication": "bearish"  # Smart money grabbed longs' stops
                    })
                elif not swing.is_high and c_low < swing.price < c_close:
                    swept_levels.append({
                        "level": swing.price,
                        "type": "sell_side_swept",
                        "candle_idx": i,
                        "implication": "bullish"  # Smart money grabbed shorts' stops
                    })

    # Sort by distance from current price
    buy_side_liq = sorted(buy_side_liq, key=lambda x: x["distance_pct"])[:3]
    sell_side_liq = sorted(sell_side_liq, key=lambda x: x["distance_pct"])[:3]

    return {
        "buy_side": buy_side_liq,
        "sell_side": sell_side_liq,
        "swept": swept_levels[-3:] if swept_levels else [],
        "nearest_buy_liq": buy_side_liq[0]["level"] if buy_side_liq else None,
        "nearest_sell_liq": sell_side_liq[0]["level"] if sell_side_liq else None
    }


def get_premium_discount_zones(candles: List[Dict], lookback: int = 50) -> Dict[str, Any]:
    """
    Calculate Premium and Discount zones based on recent range.

    - Premium Zone (upper 50%): Where smart money SELLS
    - Discount Zone (lower 50%): Where smart money BUYS
    - Equilibrium (50%): Fair value

    Args:
        candles: OHLCV data
        lookback: Candles to consider for range

    Returns:
        Dict with zone analysis
    """
    if len(candles) < lookback:
        lookback = len(candles)

    recent = candles[-lookback:]
    range_high = max(c.get("high", c.get("h", 0)) for c in recent)
    range_low = min(c.get("low", c.get("l", 0)) for c in recent)

    range_size = range_high - range_low
    equilibrium = (range_high + range_low) / 2

    current_price = candles[-1].get("close", candles[-1].get("c", 0))

    # Calculate position in range (0 = bottom, 1 = top)
    position = (current_price - range_low) / range_size if range_size else 0.5

    # Determine zone
    if position > 0.7:
        zone = "deep_premium"
        bias = "bearish"  # Expect pullback
        strength = (position - 0.5) * 2
    elif position > 0.5:
        zone = "premium"
        bias = "neutral_bearish"
        strength = (position - 0.5) * 2
    elif position < 0.3:
        zone = "deep_discount"
        bias = "bullish"  # Expect bounce
        strength = (0.5 - position) * 2
    elif position < 0.5:
        zone = "discount"
        bias = "neutral_bullish"
        strength = (0.5 - position) * 2
    else:
        zone = "equilibrium"
        bias = "neutral"
        strength = 0

    return {
        "zone": zone,
        "bias": bias,
        "strength": round(strength, 2),
        "position": round(position, 2),
        "range_high": range_high,
        "range_low": range_low,
        "equilibrium": equilibrium,
        "premium_zone": (equilibrium, range_high),
        "discount_zone": (range_low, equilibrium)
    }


def analyze_smart_money(candles: List[Dict], timeframe: str = "1h") -> Dict[str, Any]:
    """
    Complete Smart Money Concepts analysis.

    Combines all SMC concepts into actionable trading signals.

    Args:
        candles: OHLCV data (50+ candles recommended)
        timeframe: For context in logging

    Returns:
        Comprehensive SMC analysis
    """
    if len(candles) < 20:
        return {
            "valid": False,
            "reason": "Insufficient data",
            "bias": "neutral",
            "confidence": 0
        }

    # Run all SMC analysis
    swings = find_swing_points(candles, lookback=3)
    structure = detect_market_structure(candles, lookback=3)
    order_blocks = detect_order_blocks(candles, structure)
    fvgs = detect_fair_value_gaps(candles)
    liquidity = detect_liquidity_levels(candles, swings)
    zones = get_premium_discount_zones(candles)

    current_price = candles[-1].get("close", candles[-1].get("c", 0))

    # === BUILD TRADING SIGNAL ===
    bullish_factors = []
    bearish_factors = []

    # Factor 1: Market Structure
    if structure["bias"] == "bullish":
        bullish_factors.append(("structure", structure["confidence"]))
    elif structure["bias"] == "bearish":
        bearish_factors.append(("structure", structure["confidence"]))

    # Factor 2: Structure Break
    if structure["structure_break"] == "bos":
        if structure["structure"] == "bullish":
            bullish_factors.append(("bos_continuation", 0.8))
        else:
            bearish_factors.append(("bos_continuation", 0.8))
    elif structure["structure_break"] == "choch":
        # CHoCH is reversal signal
        if structure["structure"] == "bullish":
            bearish_factors.append(("choch_reversal", 0.9))
        else:
            bullish_factors.append(("choch_reversal", 0.9))

    # Factor 3: Order Blocks
    for ob in order_blocks[:2]:  # Top 2 OBs
        dist = abs(current_price - ob["mid"]) / current_price * 100
        if dist < 1:  # Price near OB
            if ob["is_bullish"]:
                bullish_factors.append(("near_demand_ob", ob["strength"]))
            else:
                bearish_factors.append(("near_supply_ob", ob["strength"]))

    # Factor 4: Fair Value Gaps
    for fvg in fvgs[:2]:  # Top 2 FVGs
        dist = abs(current_price - fvg["mid"]) / current_price * 100
        if dist < 1.5:  # Price near FVG
            # FVG acts as magnet - price likely to fill it
            if fvg["is_bullish"] and current_price > fvg["mid"]:
                bearish_factors.append(("fvg_below", 0.6))  # Expect fill down
            elif not fvg["is_bullish"] and current_price < fvg["mid"]:
                bullish_factors.append(("fvg_above", 0.6))  # Expect fill up

    # Factor 5: Liquidity Sweeps
    for sweep in liquidity.get("swept", []):
        if sweep["implication"] == "bullish":
            bullish_factors.append(("liquidity_swept", 0.85))
        else:
            bearish_factors.append(("liquidity_swept", 0.85))

    # Factor 6: Premium/Discount Zones
    if zones["zone"] in ["deep_discount", "discount"]:
        bullish_factors.append(("discount_zone", zones["strength"]))
    elif zones["zone"] in ["deep_premium", "premium"]:
        bearish_factors.append(("premium_zone", zones["strength"]))

    # === CALCULATE FINAL SIGNAL ===
    bullish_score = sum(weight for _, weight in bullish_factors)
    bearish_score = sum(weight for _, weight in bearish_factors)

    total_score = bullish_score + bearish_score
    if total_score == 0:
        bias = "neutral"
        confidence = 0.3
        strength = 0
    elif bullish_score > bearish_score:
        bias = "bullish"
        confidence = bullish_score / (bullish_score + bearish_score + 0.1)
        strength = min(10, int(bullish_score * 3))
    else:
        bias = "bearish"
        confidence = bearish_score / (bullish_score + bearish_score + 0.1)
        strength = min(10, int(bearish_score * 3))

    # Determine signal quality
    if confidence > 0.7 and strength >= 7:
        signal = "strong_" + bias
    elif confidence > 0.5 and strength >= 5:
        signal = bias
    else:
        signal = "weak_" + bias if bias != "neutral" else "neutral"

    return {
        "valid": True,
        "timeframe": timeframe,
        "bias": bias,
        "signal": signal,
        "confidence": round(confidence, 2),
        "strength": strength,
        "structure": structure,
        "order_blocks": order_blocks,
        "fair_value_gaps": fvgs,
        "liquidity": liquidity,
        "zones": zones,
        "bullish_factors": [(name, round(w, 2)) for name, w in bullish_factors],
        "bearish_factors": [(name, round(w, 2)) for name, w in bearish_factors],
        "key_levels": {
            "nearest_demand": order_blocks[0]["low"] if order_blocks and order_blocks[0]["is_bullish"] else None,
            "nearest_supply": order_blocks[0]["high"] if order_blocks and not order_blocks[0]["is_bullish"] else None,
            "swing_high": structure.get("last_swing_high"),
            "swing_low": structure.get("last_swing_low"),
            "buy_liquidity": liquidity.get("nearest_buy_liq"),
            "sell_liquidity": liquidity.get("nearest_sell_liq")
        }
    }

