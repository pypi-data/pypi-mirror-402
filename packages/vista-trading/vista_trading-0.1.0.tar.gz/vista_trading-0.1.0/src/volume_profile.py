"""
Volume Profile Analysis - Where Real Support/Resistance Lives

Volume Profile shows WHERE trading activity occurred, not just WHEN.
This reveals:
1. Point of Control (POC) - Price level with highest volume (fair value)
2. Value Area (VA) - Where 70% of volume traded (consensus range)
3. High Volume Nodes (HVN) - Strong S/R levels
4. Low Volume Nodes (LVN) - Price rejection zones

Unlike traditional S/R (based on swing points), Volume Profile shows
where real institutional activity occurred.
"""

import logging
from typing import List, Dict, Any, Tuple
from collections import defaultdict
import math

logger = logging.getLogger(__name__)


def calculate_volume_profile(
    candles: List[Dict],
    num_bins: int = 50,
    value_area_pct: float = 0.70
) -> Dict[str, Any]:
    """
    Calculate Volume Profile from candle data.
    
    Distributes volume across price bins to show where trading occurred.
    
    Args:
        candles: OHLCV candle data
        num_bins: Number of price levels to divide range into
        value_area_pct: Percentage of volume for Value Area (default 70%)
        
    Returns:
        Dict with POC, VAH, VAL, and volume distribution
    """
    if len(candles) < 10:
        return {"valid": False, "reason": "Insufficient data"}
    
    # Get price range
    all_highs = [c.get("high", c.get("h", 0)) for c in candles]
    all_lows = [c.get("low", c.get("l", 0)) for c in candles]
    
    price_high = max(all_highs)
    price_low = min(all_lows)
    price_range = price_high - price_low
    
    if price_range == 0:
        return {"valid": False, "reason": "No price range"}
    
    bin_size = price_range / num_bins
    
    # Initialize volume bins
    volume_bins = defaultdict(float)
    
    # Distribute each candle's volume across its price range
    for candle in candles:
        c_high = candle.get("high", candle.get("h", 0))
        c_low = candle.get("low", candle.get("l", 0))
        c_volume = candle.get("volume", candle.get("v", 0))
        c_close = candle.get("close", candle.get("c", 0))
        c_open = candle.get("open", candle.get("o", 0))
        
        if c_volume == 0:
            continue
        
        # Find bins this candle touches
        low_bin = int((c_low - price_low) / bin_size)
        high_bin = int((c_high - price_low) / bin_size)
        
        # Clamp to valid range
        low_bin = max(0, min(low_bin, num_bins - 1))
        high_bin = max(0, min(high_bin, num_bins - 1))
        
        # Distribute volume (more weight near close for accuracy)
        bins_touched = high_bin - low_bin + 1
        if bins_touched > 0:
            # Weight distribution towards close price
            close_bin = int((c_close - price_low) / bin_size)
            close_bin = max(0, min(close_bin, num_bins - 1))
            
            for b in range(low_bin, high_bin + 1):
                # Give more volume to bins near close
                distance = abs(b - close_bin)
                weight = 1 / (1 + distance * 0.5)
                volume_bins[b] += c_volume * weight / bins_touched
    
    if not volume_bins:
        return {"valid": False, "reason": "No volume data"}
    
    # Find Point of Control (highest volume bin)
    poc_bin = max(volume_bins.keys(), key=lambda x: volume_bins[x])
    poc_price = price_low + (poc_bin + 0.5) * bin_size
    poc_volume = volume_bins[poc_bin]
    
    # Calculate total volume
    total_volume = sum(volume_bins.values())
    
    # Calculate Value Area (70% of volume around POC)
    target_volume = total_volume * value_area_pct
    va_volume = volume_bins[poc_bin]
    va_bins = {poc_bin}
    
    # Expand outward from POC until we capture target volume
    lower_bin = poc_bin - 1
    upper_bin = poc_bin + 1
    
    while va_volume < target_volume and (lower_bin >= 0 or upper_bin < num_bins):
        lower_vol = volume_bins.get(lower_bin, 0) if lower_bin >= 0 else 0
        upper_vol = volume_bins.get(upper_bin, 0) if upper_bin < num_bins else 0
        
        if lower_vol >= upper_vol and lower_bin >= 0:
            va_volume += lower_vol
            va_bins.add(lower_bin)
            lower_bin -= 1
        elif upper_bin < num_bins:
            va_volume += upper_vol
            va_bins.add(upper_bin)
            upper_bin += 1
        else:
            break
    
    va_low_bin = min(va_bins)
    va_high_bin = max(va_bins)
    
    val_price = price_low + (va_low_bin + 0.5) * bin_size  # Value Area Low
    vah_price = price_low + (va_high_bin + 0.5) * bin_size  # Value Area High
    
    # Find High Volume Nodes (HVN) - significant volume clusters
    avg_volume = total_volume / num_bins
    hvn_threshold = avg_volume * 1.5
    
    high_volume_nodes = []
    for b, vol in volume_bins.items():
        if vol > hvn_threshold:
            node_price = price_low + (b + 0.5) * bin_size
            high_volume_nodes.append({
                "price": round(node_price, 2),
                "volume": round(vol, 2),
                "strength": round(vol / avg_volume, 2)
            })
    
    # Sort HVN by volume (strongest first)
    high_volume_nodes = sorted(high_volume_nodes, key=lambda x: x["volume"], reverse=True)[:5]
    
    # Find Low Volume Nodes (LVN) - price rejection zones
    lvn_threshold = avg_volume * 0.5
    
    low_volume_nodes = []
    for b, vol in volume_bins.items():
        if vol < lvn_threshold and vol > 0:
            node_price = price_low + (b + 0.5) * bin_size
            low_volume_nodes.append({
                "price": round(node_price, 2),
                "volume": round(vol, 2),
                "weakness": round(avg_volume / vol if vol > 0 else 10, 2)
            })
    
    low_volume_nodes = sorted(low_volume_nodes, key=lambda x: x["weakness"], reverse=True)[:5]

    # Current price position relative to value area
    current_price = candles[-1].get("close", candles[-1].get("c", 0))

    if current_price > vah_price:
        position = "above_value"
        bias = "bullish_breakout"  # Price accepted above VA
    elif current_price < val_price:
        position = "below_value"
        bias = "bearish_breakdown"  # Price accepted below VA
    else:
        position = "inside_value"
        bias = "neutral"  # Fair value range

    # Distance to key levels
    dist_to_poc = ((current_price - poc_price) / poc_price) * 100
    dist_to_vah = ((vah_price - current_price) / current_price) * 100
    dist_to_val = ((current_price - val_price) / current_price) * 100

    return {
        "valid": True,
        "poc": round(poc_price, 2),  # Point of Control
        "vah": round(vah_price, 2),  # Value Area High
        "val": round(val_price, 2),  # Value Area Low
        "position": position,
        "bias": bias,
        "dist_to_poc_pct": round(dist_to_poc, 2),
        "dist_to_vah_pct": round(dist_to_vah, 2),
        "dist_to_val_pct": round(dist_to_val, 2),
        "high_volume_nodes": high_volume_nodes,
        "low_volume_nodes": low_volume_nodes,
        "price_range": (round(price_low, 2), round(price_high, 2)),
        "total_volume": round(total_volume, 2)
    }


def get_vp_support_resistance(candles: List[Dict], current_price: float) -> Dict[str, Any]:
    """
    Get support and resistance levels from Volume Profile.

    Unlike swing-based S/R, these levels represent where actual
    trading activity occurred - much more reliable.

    Args:
        candles: OHLCV data
        current_price: Current market price

    Returns:
        Dict with volume-based support and resistance levels
    """
    vp = calculate_volume_profile(candles)

    if not vp.get("valid"):
        return {"supports": [], "resistances": [], "valid": False}

    supports = []
    resistances = []

    # POC acts as major S/R
    poc = vp["poc"]
    if poc < current_price:
        supports.append({
            "price": poc,
            "type": "poc",
            "strength": "very_strong",
            "description": "Point of Control - highest volume level"
        })
    else:
        resistances.append({
            "price": poc,
            "type": "poc",
            "strength": "very_strong",
            "description": "Point of Control - highest volume level"
        })

    # Value Area boundaries
    vah = vp["vah"]
    val = vp["val"]

    if vah > current_price:
        resistances.append({
            "price": vah,
            "type": "vah",
            "strength": "strong",
            "description": "Value Area High - 70% volume boundary"
        })

    if val < current_price:
        supports.append({
            "price": val,
            "type": "val",
            "strength": "strong",
            "description": "Value Area Low - 70% volume boundary"
        })

    # High Volume Nodes as S/R
    for hvn in vp.get("high_volume_nodes", []):
        if hvn["price"] < current_price:
            supports.append({
                "price": hvn["price"],
                "type": "hvn",
                "strength": "medium" if hvn["strength"] < 2 else "strong",
                "description": f"High Volume Node ({hvn['strength']:.1f}x avg)"
            })
        else:
            resistances.append({
                "price": hvn["price"],
                "type": "hvn",
                "strength": "medium" if hvn["strength"] < 2 else "strong",
                "description": f"High Volume Node ({hvn['strength']:.1f}x avg)"
            })

    # Sort by proximity to current price
    supports = sorted(supports, key=lambda x: current_price - x["price"])[:3]
    resistances = sorted(resistances, key=lambda x: x["price"] - current_price)[:3]

    return {
        "supports": supports,
        "resistances": resistances,
        "nearest_support": supports[0]["price"] if supports else None,
        "nearest_resistance": resistances[0]["price"] if resistances else None,
        "in_value_area": vp["position"] == "inside_value",
        "valid": True
    }


def analyze_volume_profile(candles: List[Dict], timeframe: str = "1h") -> Dict[str, Any]:
    """
    Complete Volume Profile analysis for trading decisions.

    Args:
        candles: OHLCV data (50+ candles recommended)
        timeframe: For context

    Returns:
        Trading-relevant volume profile analysis
    """
    vp = calculate_volume_profile(candles)

    if not vp.get("valid"):
        return {
            "valid": False,
            "bias": "neutral",
            "confidence": 0,
            "signal": "no_signal"
        }

    current_price = candles[-1].get("close", candles[-1].get("c", 0))
    sr = get_vp_support_resistance(candles, current_price)

    # Determine trading signal based on VP
    signal = "neutral"
    confidence = 0.5
    reasoning = []

    # Position relative to value area
    if vp["position"] == "above_value":
        signal = "bullish"
        confidence = 0.65
        reasoning.append("Price above Value Area - bullish acceptance")

        # Check if price near VAH (potential support now)
        if abs(vp["dist_to_vah_pct"]) < 0.5:
            signal = "bullish_bounce"
            confidence = 0.75
            reasoning.append("Testing VAH as support - high probability bounce")

    elif vp["position"] == "below_value":
        signal = "bearish"
        confidence = 0.65
        reasoning.append("Price below Value Area - bearish acceptance")

        # Check if price near VAL (potential resistance now)
        if abs(vp["dist_to_val_pct"]) < 0.5:
            signal = "bearish_rejection"
            confidence = 0.75
            reasoning.append("Testing VAL as resistance - high probability rejection")

    else:  # Inside value area
        signal = "neutral"
        confidence = 0.4
        reasoning.append("Price inside Value Area - wait for breakout")

        # Check if near POC
        if abs(vp["dist_to_poc_pct"]) < 0.3:
            signal = "at_fair_value"
            reasoning.append("At POC - fair value, expect consolidation")

    # Check for low volume node breakout potential
    for lvn in vp.get("low_volume_nodes", []):
        lvn_dist = abs(current_price - lvn["price"]) / current_price * 100
        if lvn_dist < 0.5:
            reasoning.append(f"Near LVN ${lvn['price']:.2f} - expect fast move through")
            if current_price > lvn["price"]:
                signal = "bullish_acceleration" if signal == "bullish" else signal
            else:
                signal = "bearish_acceleration" if signal == "bearish" else signal
            confidence = min(confidence + 0.1, 0.9)
            break

    return {
        "valid": True,
        "timeframe": timeframe,
        "signal": signal,
        "bias": "bullish" if "bullish" in signal else "bearish" if "bearish" in signal else "neutral",
        "confidence": round(confidence, 2),
        "poc": vp["poc"],
        "vah": vp["vah"],
        "val": vp["val"],
        "position": vp["position"],
        "supports": sr["supports"],
        "resistances": sr["resistances"],
        "nearest_support": sr["nearest_support"],
        "nearest_resistance": sr["nearest_resistance"],
        "reasoning": reasoning,
        "high_volume_nodes": vp["high_volume_nodes"],
        "low_volume_nodes": vp["low_volume_nodes"]
    }

