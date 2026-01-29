"""
Alpha Signal Generators - Free data sources for leading indicators.

This module provides alpha-generating signals from free APIs:
1. Fear & Greed Index - Market sentiment from alternative.me
2. Whale Address Tracking - Track profitable Hyperliquid traders
3. Order Book Analysis - Detect whale walls and imbalances
4. Funding Rate Signals - Crowded trade detection
5. Volume Spike Detection - Unusual activity alerts
"""

import logging
import aiohttp
import asyncio
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime, timedelta

from src.database import get_db

logger = logging.getLogger(__name__)


@dataclass
class AlphaSignal:
    """Represents an alpha signal with metadata."""
    name: str
    value: float
    signal: str  # "bullish", "bearish", "neutral"
    strength: float  # 0.0 to 1.0
    description: str
    timestamp: datetime = field(default_factory=datetime.utcnow)


class FearGreedIndex:
    """Fetch and analyze the Crypto Fear & Greed Index."""
    
    API_URL = "https://api.alternative.me/fng/"
    
    def __init__(self):
        self.last_value: Optional[int] = None
        self.last_classification: Optional[str] = None
        self.last_fetch: Optional[datetime] = None
        self.cache_duration = timedelta(minutes=30)  # Cache for 30 min
    
    async def fetch(self) -> Dict[str, Any]:
        """Fetch current Fear & Greed Index."""
        # Return cached value if fresh
        if (self.last_fetch and 
            datetime.utcnow() - self.last_fetch < self.cache_duration and
            self.last_value is not None):
            return self._get_cached_result()
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(self.API_URL, timeout=10) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get("data"):
                            latest = data["data"][0]
                            self.last_value = int(latest.get("value", 50))
                            self.last_classification = latest.get("value_classification", "Neutral")
                            self.last_fetch = datetime.utcnow()
                            
                            return self._get_cached_result()
        except Exception as e:
            logger.error(f"Failed to fetch Fear & Greed Index: {e}")
        
        # Return neutral on error
        return {
            "value": 50,
            "classification": "Neutral",
            "signal": "neutral",
            "strength": 0.0,
            "description": "Unable to fetch Fear & Greed Index"
        }
    
    def _get_cached_result(self) -> Dict[str, Any]:
        """Generate signal from cached value."""
        value = self.last_value or 50
        classification = self.last_classification or "Neutral"
        
        # Generate trading signal
        if value <= 20:
            signal = "bullish"
            strength = (25 - value) / 25  # Stronger signal at lower values
            description = f"Extreme Fear ({value}) - Contrarian BUY signal"
        elif value <= 35:
            signal = "bullish"
            strength = (40 - value) / 40 * 0.5
            description = f"Fear ({value}) - Potential buying opportunity"
        elif value >= 80:
            signal = "bearish"
            strength = (value - 75) / 25
            description = f"Extreme Greed ({value}) - Contrarian SELL signal"
        elif value >= 65:
            signal = "bearish"
            strength = (value - 60) / 40 * 0.5
            description = f"Greed ({value}) - Consider taking profits"
        else:
            signal = "neutral"
            strength = 0.0
            description = f"Neutral sentiment ({value})"
        
        return {
            "value": value,
            "classification": classification,
            "signal": signal,
            "strength": round(strength, 2),
            "description": description
        }


class WhaleTracker:
    """Track known whale addresses on Hyperliquid."""

    # Known profitable whale addresses - populated from KNOWN_WHALE_ADDRESSES at module level
    # These include famous traders like the "Hyperliquid Whale", GCR, and James Wynn counter-traders
    DEFAULT_WHALES = []  # Will be populated from KNOWN_WHALE_ADDRESSES

    def __init__(self, hyperliquid_info, load_defaults: bool = True):
        """Initialize with Hyperliquid Info client.

        Args:
            hyperliquid_info: Hyperliquid Info client for fetching positions
            load_defaults: If True, automatically load known whale addresses
        """
        self.info = hyperliquid_info
        self.tracked_whales: List[Dict] = []
        self.whale_positions: Dict[str, List[Dict]] = {}  # address -> positions
        self.position_history: Dict[str, List[Dict]] = {}  # address -> history

        # Load default whale addresses if requested
        if load_defaults:
            self._load_default_whales()
    
    def _load_default_whales(self):
        """Load default whale addresses from KNOWN_WHALE_ADDRESSES."""
        # Import at runtime to avoid circular dependency
        for whale_data in KNOWN_WHALE_ADDRESSES:
            self.add_whale(
                address=whale_data["address"],
                name=whale_data.get("name", ""),
                reason=whale_data.get("reason", "")
            )
        logger.info(f"🐋 Loaded {len(self.tracked_whales)} default whale addresses")

    def add_whale(self, address: str, name: str = "", reason: str = ""):
        """Add a whale address to track."""
        whale = {
            "address": address.lower(),
            "name": name or f"Whale_{address[:8]}",
            "track_reason": reason
        }
        if not any(w["address"] == whale["address"] for w in self.tracked_whales):
            self.tracked_whales.append(whale)
            logger.info(f"🐋 Now tracking whale: {whale['name']} ({address[:10]}...)")
    
    def remove_whale(self, address: str):
        """Remove a whale from tracking."""
        self.tracked_whales = [w for w in self.tracked_whales if w["address"] != address.lower()]

    def get_whale_positions(self, address: str) -> List[Dict]:
        """Get current positions for a whale address."""
        try:
            state = self.info.user_state(address)
            if state is None:
                return []
            positions = []

            for pos in state.get("assetPositions", []):
                position_data = pos.get("position", {})
                size = float(position_data.get("szi", 0) or 0)
                if size == 0:
                    continue

                positions.append({
                    "symbol": position_data.get("coin", "?"),
                    "size": size,
                    "side": "long" if size > 0 else "short",
                    "entry_price": float(position_data.get("entryPx", 0) or 0),
                    "unrealized_pnl": float(position_data.get("unrealizedPnl", 0) or 0),
                    "leverage": float(position_data.get("leverage", {}).get("value", 1) or 1),
                    "margin_used": float(position_data.get("marginUsed", 0) or 0),
                })

            return positions
        except Exception as e:
            logger.error(f"Failed to get whale positions for {address[:10]}...: {e}")
            return []

    def scan_all_whales(self) -> Dict[str, Any]:
        """Scan all tracked whales and detect changes."""
        results = {
            "whale_count": len(self.tracked_whales),
            "total_positions": 0,
            "new_positions": [],
            "closed_positions": [],
            "whale_consensus": {},  # symbol -> {longs: n, shorts: n}
            "positions_by_whale": {},
        }

        for whale in self.tracked_whales:
            address = whale["address"]
            name = whale["name"]

            current_positions = self.get_whale_positions(address)
            previous_positions = self.whale_positions.get(address, [])

            # Detect new positions
            prev_symbols = {p["symbol"] for p in previous_positions}
            for pos in current_positions:
                if pos["symbol"] not in prev_symbols:
                    results["new_positions"].append({
                        "whale": name,
                        "address": address,
                        **pos
                    })

            # Detect closed positions
            curr_symbols = {p["symbol"] for p in current_positions}
            for pos in previous_positions:
                if pos["symbol"] not in curr_symbols:
                    results["closed_positions"].append({
                        "whale": name,
                        "address": address,
                        **pos
                    })

            # Update stored positions
            self.whale_positions[address] = current_positions
            results["positions_by_whale"][name] = current_positions
            results["total_positions"] += len(current_positions)

            # Build consensus
            for pos in current_positions:
                symbol = pos["symbol"]
                if symbol not in results["whale_consensus"]:
                    results["whale_consensus"][symbol] = {"longs": 0, "shorts": 0, "total_size": 0}

                if pos["side"] == "long":
                    results["whale_consensus"][symbol]["longs"] += 1
                else:
                    results["whale_consensus"][symbol]["shorts"] += 1
                results["whale_consensus"][symbol]["total_size"] += abs(pos["size"])

        return results

    def get_whale_signal(self, symbol: str) -> Dict[str, Any]:
        """Get aggregated whale signal for a symbol, weighted by historical accuracy.

        Uses database to check:
        1. Overall whale follow accuracy
        2. Per-whale accuracy (weight better whales higher)
        3. Per-symbol accuracy (some symbols more predictable)
        """
        scan = self.scan_all_whales()
        consensus = scan["whale_consensus"].get(symbol, {"longs": 0, "shorts": 0})

        longs = consensus.get("longs", 0)
        shorts = consensus.get("shorts", 0)
        total = longs + shorts

        # Get historical accuracy data
        try:
            db = get_db()
            symbol_accuracy = db.get_symbol_accuracy(symbol)
            whale_accuracy = db.get_whale_accuracy()  # Overall whale follow accuracy
            historical_multiplier = symbol_accuracy["overall"]["confidence_multiplier"]
            whale_win_rate = whale_accuracy["win_rate"]
        except Exception as e:
            logger.debug(f"Could not get historical accuracy: {e}")
            historical_multiplier = 1.0
            whale_win_rate = 0.5

        if total == 0:
            return {
                "signal": "neutral",
                "strength": 0.0,
                "longs": 0,
                "shorts": 0,
                "description": f"No whale positions in {symbol}",
                "new_positions": [p for p in scan.get("new_positions", []) if p.get("symbol") == symbol],
                "closed_positions": [p for p in scan.get("closed_positions", []) if p.get("symbol") == symbol],
                "whale_consensus": scan.get("whale_consensus", {}),
                "positions_by_whale": scan.get("positions_by_whale", {}),
                "historical_multiplier": historical_multiplier,
                "whale_win_rate": whale_win_rate,
            }

        long_ratio = longs / total

        if long_ratio >= 0.7:
            signal = "bullish"
            base_strength = (long_ratio - 0.5) * 2
            description = f"Whales bullish on {symbol}: {longs} long vs {shorts} short"
        elif long_ratio <= 0.3:
            signal = "bearish"
            base_strength = (0.5 - long_ratio) * 2
            description = f"Whales bearish on {symbol}: {shorts} short vs {longs} long"
        else:
            signal = "neutral"
            base_strength = 0.0
            description = f"Whales mixed on {symbol}: {longs} long, {shorts} short"

        # Apply historical accuracy multiplier to strength
        # If whales have been accurate on this symbol, boost the signal
        adjusted_strength = base_strength * historical_multiplier

        # Add accuracy info to description
        if historical_multiplier > 1.1:
            description += f" (historically accurate: {whale_win_rate:.0%} win rate)"
        elif historical_multiplier < 0.9:
            description += f" (historically weak: {whale_win_rate:.0%} win rate)"

        return {
            "signal": signal,
            "strength": round(adjusted_strength, 2),
            "base_strength": round(base_strength, 2),
            "longs": longs,
            "shorts": shorts,
            "description": description,
            # Include position change data for Discord alerts
            "new_positions": [p for p in scan.get("new_positions", []) if p.get("symbol") == symbol],
            "closed_positions": [p for p in scan.get("closed_positions", []) if p.get("symbol") == symbol],
            "whale_consensus": scan.get("whale_consensus", {}),
            "positions_by_whale": scan.get("positions_by_whale", {}),
            # Historical accuracy data
            "historical_multiplier": historical_multiplier,
            "whale_win_rate": whale_win_rate,
        }


class OrderBookAnalyzer:
    """Analyze order book for whale walls and imbalances."""

    def __init__(self, hyperliquid_info):
        """Initialize with Hyperliquid Info client."""
        self.info = hyperliquid_info

    def get_full_orderbook(self, symbol: str, depth: int = 20) -> Dict[str, Any]:
        """Get full order book with analysis."""
        try:
            book = self.info.l2_snapshot(symbol)
            if book is None:
                return {"bids": [], "asks": [], "bid_count": 0, "ask_count": 0}
            levels = book.get("levels", [[], []])

            bids = levels[0][:depth] if len(levels) > 0 else []
            asks = levels[1][:depth] if len(levels) > 1 else []

            return {
                "bids": bids,
                "asks": asks,
                "bid_count": len(bids),
                "ask_count": len(asks)
            }
        except Exception as e:
            logger.error(f"Failed to get orderbook for {symbol}: {e}")
            return {"bids": [], "asks": [], "bid_count": 0, "ask_count": 0}

    def analyze_orderbook(self, symbol: str, current_price: float = 0) -> Dict[str, Any]:
        """Analyze order book for trading signals."""
        book = self.get_full_orderbook(symbol, depth=50)
        bids = book["bids"]
        asks = book["asks"]

        if not bids or not asks:
            return {
                "signal": "neutral",
                "strength": 0.0,
                "bid_volume": 0,
                "ask_volume": 0,
                "imbalance": 0,
                "whale_walls": [],
                "description": "No orderbook data"
            }

        # Calculate volumes
        bid_volume = sum(float(b.get("sz", 0)) for b in bids)
        ask_volume = sum(float(a.get("sz", 0)) for a in asks)
        total_volume = bid_volume + ask_volume

        # Calculate imbalance (-1 to +1, positive = more bids = bullish)
        imbalance = (bid_volume - ask_volume) / total_volume if total_volume > 0 else 0

        # Detect whale walls (orders > 3x average size)
        all_sizes = [float(b.get("sz", 0)) for b in bids] + [float(a.get("sz", 0)) for a in asks]
        avg_size = sum(all_sizes) / len(all_sizes) if all_sizes else 0
        whale_threshold = avg_size * 3

        whale_walls = []
        for bid in bids:
            size = float(bid.get("sz", 0))
            price = float(bid.get("px", 0))
            if size >= whale_threshold:
                whale_walls.append({
                    "side": "bid",
                    "price": price,
                    "size": size,
                    "usd_value": size * price
                })

        for ask in asks:
            size = float(ask.get("sz", 0))
            price = float(ask.get("px", 0))
            if size >= whale_threshold:
                whale_walls.append({
                    "side": "ask",
                    "price": price,
                    "size": size,
                    "usd_value": size * price
                })

        # Generate signal
        if imbalance > 0.3:
            signal = "bullish"
            strength = min(imbalance, 1.0)
            description = f"Strong bid support ({imbalance:.1%} imbalance)"
        elif imbalance < -0.3:
            signal = "bearish"
            strength = min(abs(imbalance), 1.0)
            description = f"Heavy sell pressure ({imbalance:.1%} imbalance)"
        else:
            signal = "neutral"
            strength = 0.0
            description = f"Balanced orderbook ({imbalance:.1%} imbalance)"

        # Add whale wall info to description
        if whale_walls:
            bid_walls = [w for w in whale_walls if w["side"] == "bid"]
            ask_walls = [w for w in whale_walls if w["side"] == "ask"]
            if bid_walls:
                description += f" | {len(bid_walls)} bid wall(s)"
            if ask_walls:
                description += f" | {len(ask_walls)} ask wall(s)"

        return {
            "signal": signal,
            "strength": round(strength, 2),
            "bid_volume": round(bid_volume, 2),
            "ask_volume": round(ask_volume, 2),
            "imbalance": round(imbalance, 3),
            "whale_walls": whale_walls[:5],  # Top 5 walls
            "description": description
        }


class FundingRateSignals:
    """Generate signals from funding rate extremes."""

    # Thresholds for signal generation (hourly rates)
    EXTREME_HIGH = 0.0003  # 0.03% per hour = 0.24% per 8h = very crowded long
    HIGH = 0.00015         # 0.015% per hour = 0.12% per 8h = crowded long
    EXTREME_LOW = -0.0003  # -0.03% per hour = crowded short
    LOW = -0.00015         # -0.015% per hour = crowded short

    def __init__(self, hyperliquid_client):
        """Initialize with Hyperliquid client."""
        self.hl = hyperliquid_client

    def get_funding_signal(self, symbol: str) -> Dict[str, Any]:
        """Get trading signal from funding rate."""
        try:
            funding_data = self.hl.get_funding_rate(symbol)
            if funding_data is None:
                return {
                    "signal": "neutral",
                    "strength": 0.0,
                    "funding_rate": 0,
                    "funding_rate_8h": 0,
                    "description": "Funding data unavailable"
                }
            funding_rate = funding_data.get("funding_rate", 0)
            funding_8h = funding_data.get("funding_rate_8h", funding_rate * 8)

            # Generate contrarian signal
            if funding_rate >= self.EXTREME_HIGH:
                signal = "bearish"  # Fade the crowded longs
                strength = min((funding_rate - self.EXTREME_HIGH) / self.EXTREME_HIGH + 0.7, 1.0)
                description = f"EXTREME funding ({funding_8h:.3%}/8h) - Longs overcrowded, fade"
            elif funding_rate >= self.HIGH:
                signal = "bearish"
                strength = (funding_rate - self.HIGH) / (self.EXTREME_HIGH - self.HIGH) * 0.5
                description = f"High funding ({funding_8h:.3%}/8h) - Longs getting crowded"
            elif funding_rate <= self.EXTREME_LOW:
                signal = "bullish"  # Fade the crowded shorts
                strength = min((abs(funding_rate) - abs(self.EXTREME_LOW)) / abs(self.EXTREME_LOW) + 0.7, 1.0)
                description = f"EXTREME negative funding ({funding_8h:.3%}/8h) - Shorts overcrowded, fade"
            elif funding_rate <= self.LOW:
                signal = "bullish"
                strength = (abs(funding_rate) - abs(self.LOW)) / (abs(self.EXTREME_LOW) - abs(self.LOW)) * 0.5
                description = f"Negative funding ({funding_8h:.3%}/8h) - Shorts getting crowded"
            else:
                signal = "neutral"
                strength = 0.0
                description = f"Normal funding ({funding_8h:.3%}/8h)"

            return {
                "signal": signal,
                "strength": round(strength, 2),
                "funding_rate_hourly": funding_rate,
                "funding_rate_8h": funding_8h,
                "description": description
            }
        except Exception as e:
            logger.error(f"Failed to get funding signal for {symbol}: {e}")
            return {
                "signal": "neutral",
                "strength": 0.0,
                "funding_rate_hourly": 0,
                "funding_rate_8h": 0,
                "description": "Unable to fetch funding rate"
            }


class VolumeSpikeDetector:
    """Detect unusual volume activity and divergences."""

    def __init__(self, hyperliquid_client):
        """Initialize with Hyperliquid client."""
        self.hl = hyperliquid_client
        self.volume_history: Dict[str, List[float]] = {}  # symbol -> recent volumes

    def analyze_volume(self, symbol: str, candles: List[Dict] = None) -> Dict[str, Any]:
        """Analyze volume for spikes and divergences."""
        try:
            # Get candles if not provided
            if candles is None:
                candles = self.hl.get_candles(symbol, interval="15m", limit=50)

            if candles is None or len(candles) < 20:
                return {
                    "signal": "neutral",
                    "strength": 0.0,
                    "volume_ratio": 1.0,
                    "is_spike": False,
                    "divergence": "none",
                    "description": "Insufficient data for volume analysis"
                }

            # Calculate volume metrics
            volumes = [c.get("volume", 0) for c in candles]
            current_volume = volumes[-1] if volumes else 0
            avg_volume = sum(volumes[:-1]) / len(volumes[:-1]) if len(volumes) > 1 else current_volume

            # Volume ratio (current vs average)
            volume_ratio = current_volume / avg_volume if avg_volume > 0 else 1.0

            # Detect spike (>2x average)
            is_spike = volume_ratio >= 2.0

            # Check for price-volume divergence
            prices = [c.get("close", 0) for c in candles]
            price_change = (prices[-1] - prices[-5]) / prices[-5] if prices[-5] > 0 else 0
            volume_change = (volumes[-1] - volumes[-5]) / volumes[-5] if volumes[-5] > 0 else 0

            divergence = "none"
            if price_change > 0.01 and volume_change < -0.3:
                divergence = "bearish"  # Price up, volume down = weak rally
            elif price_change < -0.01 and volume_change < -0.3:
                divergence = "bullish"  # Price down, volume down = weak selloff
            elif price_change > 0.01 and volume_change > 0.5:
                divergence = "bullish_confirmation"  # Price up, volume up = strong
            elif price_change < -0.01 and volume_change > 0.5:
                divergence = "bearish_confirmation"  # Price down, volume up = strong

            # Generate signal
            if is_spike and divergence == "bullish_confirmation":
                signal = "bullish"
                strength = min(volume_ratio / 4, 1.0)
                description = f"Volume spike ({volume_ratio:.1f}x) confirms bullish move"
            elif is_spike and divergence == "bearish_confirmation":
                signal = "bearish"
                strength = min(volume_ratio / 4, 1.0)
                description = f"Volume spike ({volume_ratio:.1f}x) confirms bearish move"
            elif divergence == "bearish":
                signal = "bearish"
                strength = 0.4
                description = f"Bearish divergence: price up but volume declining"
            elif divergence == "bullish":
                signal = "bullish"
                strength = 0.4
                description = f"Bullish divergence: price down but volume declining (weak selling)"
            elif is_spike:
                signal = "attention"
                strength = min(volume_ratio / 4, 0.6)
                description = f"Volume spike detected ({volume_ratio:.1f}x average) - watch for breakout"
            else:
                signal = "neutral"
                strength = 0.0
                description = f"Normal volume ({volume_ratio:.1f}x average)"

            return {
                "signal": signal,
                "strength": round(strength, 2),
                "volume_ratio": round(volume_ratio, 2),
                "is_spike": is_spike,
                "divergence": divergence,
                "current_volume": current_volume,
                "avg_volume": round(avg_volume, 2),
                "description": description
            }
        except Exception as e:
            logger.error(f"Failed to analyze volume for {symbol}: {e}")
            return {
                "signal": "neutral",
                "strength": 0.0,
                "volume_ratio": 1.0,
                "is_spike": False,
                "divergence": "none",
                "description": "Volume analysis failed"
            }


class LiquidationLevelAnalyzer:
    """Analyze liquidation levels - where forced selling/buying will happen.

    Liquidation levels are magnets for price because:
    - Stop hunts target these levels
    - Cascading liquidations cause rapid moves
    - Smart money trades INTO liquidation levels

    Sources:
    - Coinglass API (free tier)
    - Estimated from funding rates and open interest
    """

    COINGLASS_API = "https://open-api.coinglass.com/public/v2"

    def __init__(self, api_key: str = None):
        """Initialize with optional Coinglass API key."""
        self.api_key = api_key
        self.cache = {}
        self.cache_duration = timedelta(minutes=5)
        self.last_fetch = {}

    async def fetch_liquidation_levels(self, symbol: str) -> Dict[str, Any]:
        """Fetch liquidation heatmap data."""
        cache_key = f"liq_{symbol}"

        # Check cache
        if cache_key in self.cache:
            cached_time = self.last_fetch.get(cache_key)
            if cached_time and datetime.utcnow() - cached_time < self.cache_duration:
                return self.cache[cache_key]

        try:
            # Try Coinglass API if key available
            if self.api_key:
                return await self._fetch_coinglass(symbol)

            # Fallback to estimation
            return self._estimate_liquidation_levels(symbol)

        except Exception as e:
            logger.error(f"Failed to fetch liquidation levels for {symbol}: {e}")
            return {
                "signal": "neutral",
                "strength": 0.0,
                "long_liquidation_zone": None,
                "short_liquidation_zone": None,
                "description": "Liquidation data unavailable"
            }

    async def _fetch_coinglass(self, symbol: str) -> Dict[str, Any]:
        """Fetch from Coinglass API."""
        url = f"{self.COINGLASS_API}/liquidation/info"
        headers = {"coinglassSecret": self.api_key}
        params = {"symbol": symbol.replace("-PERP", "")}

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers, params=params, timeout=10) as response:
                    if response.status == 200:
                        data = await response.json()
                        return self._parse_coinglass_response(data, symbol)
        except Exception as e:
            logger.error(f"Coinglass API error: {e}")

        return self._estimate_liquidation_levels(symbol)

    def _parse_coinglass_response(self, data: Dict, symbol: str) -> Dict[str, Any]:
        """Parse Coinglass liquidation response."""
        if not data or data.get("code") != "0":
            return self._estimate_liquidation_levels(symbol)

        liq_data = data.get("data", [])
        if not liq_data:
            return self._estimate_liquidation_levels(symbol)

        # Extract liquidation zones
        long_liqs = []
        short_liqs = []

        for item in liq_data:
            price = float(item.get("price", 0))
            long_vol = float(item.get("longLiquidation", 0))
            short_vol = float(item.get("shortLiquidation", 0))

            if long_vol > 0:
                long_liqs.append({"price": price, "volume": long_vol})
            if short_vol > 0:
                short_liqs.append({"price": price, "volume": short_vol})

        # Find highest concentration zones
        long_zone = max(long_liqs, key=lambda x: x["volume"])["price"] if long_liqs else None
        short_zone = max(short_liqs, key=lambda x: x["volume"])["price"] if short_liqs else None

        result = {
            "signal": "neutral",
            "strength": 0.5,
            "long_liquidation_zone": long_zone,
            "short_liquidation_zone": short_zone,
            "long_liquidations": long_liqs[:5],
            "short_liquidations": short_liqs[:5],
            "description": f"Long liqs near ${long_zone:.0f}, Short liqs near ${short_zone:.0f}" if long_zone and short_zone else "Limited liquidation data"
        }

        # Cache result
        cache_key = f"liq_{symbol}"
        self.cache[cache_key] = result
        self.last_fetch[cache_key] = datetime.utcnow()

        return result

    def _estimate_liquidation_levels(self, symbol: str) -> Dict[str, Any]:
        """Estimate liquidation levels from typical leverage patterns.

        Common crypto leverage:
        - 10x leverage = 10% move to liquidation
        - 20x leverage = 5% move to liquidation
        - Most retail uses 5-20x
        """
        # This is an estimation - real data from Coinglass is better
        return {
            "signal": "neutral",
            "strength": 0.0,
            "long_liquidation_zone": None,
            "short_liquidation_zone": None,
            "estimated": True,
            "description": "Liquidation levels estimated (no API key)"
        }

    def get_liquidation_signal(self, current_price: float, long_zone: float = None,
                                short_zone: float = None) -> Dict[str, Any]:
        """Generate trading signal from liquidation proximity."""
        if not long_zone and not short_zone:
            return {"signal": "neutral", "strength": 0.0, "description": "No liquidation data"}

        signals = []
        signal = "neutral"
        strength = 0.0

        # Check proximity to liquidation zones
        if long_zone:
            dist_to_long = ((long_zone - current_price) / current_price) * 100
            if -2 <= dist_to_long <= 0:
                # Price just passed through long liquidations - bearish cascade likely
                signal = "bearish"
                strength = 0.7
                signals.append(f"Long liquidations triggered at ${long_zone:.0f}")
            elif 0 < dist_to_long <= 3:
                # Approaching long liquidations - potential magnet
                signal = "bearish"
                strength = 0.4
                signals.append(f"Approaching long liqs ${long_zone:.0f} ({dist_to_long:.1f}% away)")

        if short_zone:
            dist_to_short = ((short_zone - current_price) / current_price) * 100
            if 0 <= dist_to_short <= 2:
                # Price just passed through short liquidations
                signal = "bullish"
                strength = 0.7
                signals.append(f"Short liquidations triggered at ${short_zone:.0f}")
            elif -3 <= dist_to_short < 0:
                # Approaching short liquidations
                signal = "bullish"
                strength = 0.4
                signals.append(f"Approaching short liqs ${short_zone:.0f} ({abs(dist_to_short):.1f}% away)")

        return {
            "signal": signal,
            "strength": strength,
            "long_zone": long_zone,
            "short_zone": short_zone,
            "signals": signals,
            "description": "; ".join(signals) if signals else "No immediate liquidation levels"
        }


class OptionsFlowAnalyzer:
    """Analyze options flow - big money positioning.

    Options flow reveals institutional positioning:
    - Large call buying = bullish bets
    - Large put buying = bearish bets/hedging
    - Put/Call ratio extremes = contrarian signals
    - Unusual options activity = informed trading

    Note: Crypto options data is limited compared to equities.
    Main sources: Deribit (BTC/ETH options), some aggregators.
    """

    DERIBIT_API = "https://www.deribit.com/api/v2/public"

    def __init__(self):
        """Initialize options flow analyzer."""
        self.cache = {}
        self.cache_duration = timedelta(minutes=10)
        self.last_fetch = {}

    async def fetch_options_metrics(self, base_symbol: str = "BTC") -> Dict[str, Any]:
        """Fetch options metrics (put/call ratio, max pain, etc)."""
        cache_key = f"options_{base_symbol}"

        # Check cache
        if cache_key in self.cache:
            cached_time = self.last_fetch.get(cache_key)
            if cached_time and datetime.utcnow() - cached_time < self.cache_duration:
                return self.cache[cache_key]

        try:
            # Fetch from Deribit
            result = await self._fetch_deribit_metrics(base_symbol)

            # Cache result
            self.cache[cache_key] = result
            self.last_fetch[cache_key] = datetime.utcnow()

            return result

        except Exception as e:
            logger.error(f"Failed to fetch options metrics: {e}")
            return {
                "signal": "neutral",
                "strength": 0.0,
                "put_call_ratio": None,
                "max_pain": None,
                "description": "Options data unavailable"
            }

    async def _fetch_deribit_metrics(self, base_symbol: str) -> Dict[str, Any]:
        """Fetch options data from Deribit."""
        currency = base_symbol.upper()

        try:
            async with aiohttp.ClientSession() as session:
                # Get index price
                index_url = f"{self.DERIBIT_API}/get_index_price"
                async with session.get(index_url, params={"index_name": f"{currency.lower()}_usd"}, timeout=10) as resp:
                    if resp.status == 200:
                        index_data = await resp.json()
                        index_price = index_data.get("result", {}).get("index_price", 0)
                    else:
                        index_price = 0

                # Get options summary
                summary_url = f"{self.DERIBIT_API}/get_book_summary_by_currency"
                params = {"currency": currency, "kind": "option"}

                async with session.get(summary_url, params=params, timeout=10) as response:
                    if response.status == 200:
                        data = await response.json()
                        return self._parse_deribit_options(data, index_price, currency)

        except Exception as e:
            logger.error(f"Deribit API error: {e}")

        return {
            "signal": "neutral",
            "strength": 0.0,
            "put_call_ratio": None,
            "description": "Could not fetch Deribit options data"
        }

    def _parse_deribit_options(self, data: Dict, index_price: float, currency: str) -> Dict[str, Any]:
        """Parse Deribit options data."""
        if not data or "result" not in data:
            return {"signal": "neutral", "strength": 0.0, "description": "No options data"}

        options = data["result"]

        # Calculate put/call metrics
        total_call_volume = 0
        total_put_volume = 0
        total_call_oi = 0
        total_put_oi = 0

        for opt in options:
            name = opt.get("instrument_name", "")
            volume = opt.get("volume", 0) or 0
            oi = opt.get("open_interest", 0) or 0

            if "-C" in name:  # Call option
                total_call_volume += volume
                total_call_oi += oi
            elif "-P" in name:  # Put option
                total_put_volume += volume
                total_put_oi += oi

        # Calculate put/call ratio
        if total_call_volume > 0:
            pcr_volume = total_put_volume / total_call_volume
        else:
            pcr_volume = 1.0

        if total_call_oi > 0:
            pcr_oi = total_put_oi / total_call_oi
        else:
            pcr_oi = 1.0

        # Generate signal
        # High PCR (>1.2) = bearish sentiment / could be contrarian bullish
        # Low PCR (<0.7) = bullish sentiment / could be contrarian bearish
        if pcr_volume > 1.5:
            signal = "bullish"  # Contrarian - too many puts
            strength = min((pcr_volume - 1.5) / 1.0 + 0.5, 1.0)
            description = f"Extreme put buying (PCR: {pcr_volume:.2f}) - Contrarian bullish"
        elif pcr_volume > 1.2:
            signal = "cautious_bullish"
            strength = 0.3
            description = f"High put/call ratio ({pcr_volume:.2f}) - Some hedging"
        elif pcr_volume < 0.5:
            signal = "bearish"  # Contrarian - too many calls
            strength = min((0.5 - pcr_volume) / 0.3 + 0.5, 1.0)
            description = f"Extreme call buying (PCR: {pcr_volume:.2f}) - Contrarian bearish"
        elif pcr_volume < 0.7:
            signal = "cautious_bearish"
            strength = 0.3
            description = f"Low put/call ratio ({pcr_volume:.2f}) - Bullish sentiment"
        else:
            signal = "neutral"
            strength = 0.0
            description = f"Normal options activity (PCR: {pcr_volume:.2f})"

        return {
            "signal": signal,
            "strength": round(strength, 2),
            "put_call_ratio_volume": round(pcr_volume, 2),
            "put_call_ratio_oi": round(pcr_oi, 2),
            "total_call_volume": total_call_volume,
            "total_put_volume": total_put_volume,
            "total_call_oi": total_call_oi,
            "total_put_oi": total_put_oi,
            "index_price": index_price,
            "currency": currency,
            "description": description
        }

    def get_options_signal(self, symbol: str = "BTC") -> Dict[str, Any]:
        """Get simplified options signal (sync wrapper)."""
        # For sync contexts, return cached or neutral
        cache_key = f"options_{symbol}"
        if cache_key in self.cache:
            return self.cache[cache_key]
        return {"signal": "neutral", "strength": 0.0, "description": "No cached options data"}


class AlphaSignalAggregator:
    """Aggregates all alpha signals into a unified view."""

    def __init__(self, hyperliquid_client=None, hyperliquid_info=None, coinglass_api_key: str = None):
        """Initialize all alpha signal generators."""
        self.fear_greed = FearGreedIndex()

        # Initialize HyperLiquid-dependent analyzers if client provided
        self.whale_tracker = WhaleTracker(hyperliquid_info) if hyperliquid_info else None
        self.orderbook_analyzer = OrderBookAnalyzer(hyperliquid_info) if hyperliquid_info else None
        self.funding_signals = FundingRateSignals(hyperliquid_client) if hyperliquid_client else None
        self.volume_detector = VolumeSpikeDetector(hyperliquid_client) if hyperliquid_client else None

        # NEW: Liquidation and Options flow analyzers
        self.liquidation_analyzer = LiquidationLevelAnalyzer(api_key=coinglass_api_key)
        self.options_analyzer = OptionsFlowAnalyzer()

    async def get_all_signals(self, symbol: str, candles: List[Dict] = None, current_price: float = None) -> Dict[str, Any]:
        """Get all alpha signals for a symbol."""
        signals = {
            "symbol": symbol,
            "timestamp": datetime.utcnow().isoformat(),
            "fear_greed": None,
            "whale_tracking": None,
            "orderbook": None,
            "funding_rate": None,
            "volume": None,
            "liquidations": None,
            "options_flow": None,
            "aggregate": None
        }

        # Fetch Fear & Greed (async)
        signals["fear_greed"] = await self.fear_greed.fetch()

        # Get whale signal if tracker available
        if self.whale_tracker and self.whale_tracker.tracked_whales:
            signals["whale_tracking"] = self.whale_tracker.get_whale_signal(symbol)

        # Get orderbook analysis
        if self.orderbook_analyzer:
            signals["orderbook"] = self.orderbook_analyzer.analyze_orderbook(symbol)

        # Get funding rate signal
        if self.funding_signals:
            signals["funding_rate"] = self.funding_signals.get_funding_signal(symbol)

        # Get volume analysis
        if self.volume_detector:
            signals["volume"] = self.volume_detector.analyze_volume(symbol, candles)

        # NEW: Fetch liquidation levels
        liq_data = await self.liquidation_analyzer.fetch_liquidation_levels(symbol)
        if current_price and liq_data:
            signals["liquidations"] = self.liquidation_analyzer.get_liquidation_signal(
                current_price,
                liq_data.get("long_liquidation_zone"),
                liq_data.get("short_liquidation_zone")
            )
        else:
            signals["liquidations"] = liq_data

        # NEW: Fetch options flow (for BTC/ETH)
        base_symbol = symbol.replace("-PERP", "").replace("USDT", "")
        if base_symbol in ["BTC", "ETH"]:
            signals["options_flow"] = await self.options_analyzer.fetch_options_metrics(base_symbol)
        else:
            signals["options_flow"] = {"signal": "neutral", "strength": 0.0, "description": f"No options market for {base_symbol}"}

        # Calculate aggregate signal
        signals["aggregate"] = self._aggregate_signals(signals)

        return signals

    def _aggregate_signals(self, signals: Dict[str, Any]) -> Dict[str, Any]:
        """Combine all signals into a weighted aggregate."""
        weights = {
            "fear_greed": 0.12,      # Sentiment
            "whale_tracking": 0.25,   # Highest alpha
            "orderbook": 0.20,        # Order flow
            "funding_rate": 0.12,     # Crowding
            "volume": 0.11,           # Confirmation
            "liquidations": 0.10,     # NEW: Liquidation levels
            "options_flow": 0.10      # NEW: Options positioning
        }

        bullish_score = 0.0
        bearish_score = 0.0
        total_weight = 0.0
        active_signals = []

        for signal_name, weight in weights.items():
            signal_data = signals.get(signal_name)
            if not signal_data or signal_data.get("signal") in [None, "neutral", "attention"]:
                continue

            signal_type = signal_data.get("signal", "neutral")
            strength = signal_data.get("strength", 0.0)

            if signal_type == "bullish":
                bullish_score += weight * strength
                active_signals.append(f"{signal_name}: bullish ({strength:.0%})")
            elif signal_type == "bearish":
                bearish_score += weight * strength
                active_signals.append(f"{signal_name}: bearish ({strength:.0%})")

            total_weight += weight

        # Normalize scores
        if total_weight > 0:
            bullish_score /= total_weight
            bearish_score /= total_weight

        # Determine aggregate signal
        net_score = bullish_score - bearish_score

        if net_score > 0.15:
            signal = "bullish"
            strength = min(net_score, 1.0)
            description = f"Aggregate BULLISH ({net_score:.0%})"
        elif net_score < -0.15:
            signal = "bearish"
            strength = min(abs(net_score), 1.0)
            description = f"Aggregate BEARISH ({net_score:.0%})"
        else:
            signal = "neutral"
            strength = 0.0
            description = "Mixed/neutral signals"

        return {
            "signal": signal,
            "strength": round(strength, 2),
            "bullish_score": round(bullish_score, 2),
            "bearish_score": round(bearish_score, 2),
            "net_score": round(net_score, 2),
            "active_signals": active_signals,
            "description": description
        }

    def format_for_llm(self, signals: Dict[str, Any]) -> str:
        """Format all signals for LLM consumption."""
        lines = [
            "=" * 50,
            "📊 ALPHA SIGNALS REPORT",
            "=" * 50,
        ]

        # Fear & Greed
        fg = signals.get("fear_greed", {})
        if fg:
            emoji = "😱" if fg.get("value", 50) < 30 else "🤑" if fg.get("value", 50) > 70 else "😐"
            lines.append(f"\n{emoji} FEAR & GREED INDEX: {fg.get('value', 'N/A')}")
            lines.append(f"   Signal: {fg.get('signal', 'N/A').upper()} | {fg.get('description', '')}")

        # Whale Tracking
        wt = signals.get("whale_tracking", {})
        if wt:
            lines.append(f"\n🐋 WHALE TRACKING:")
            lines.append(f"   Signal: {wt.get('signal', 'N/A').upper()} | {wt.get('description', '')}")
            if wt.get("longs", 0) or wt.get("shorts", 0):
                lines.append(f"   Positions: {wt.get('longs', 0)} long / {wt.get('shorts', 0)} short")

        # Order Book
        ob = signals.get("orderbook", {})
        if ob:
            lines.append(f"\n📖 ORDER BOOK:")
            lines.append(f"   Signal: {ob.get('signal', 'N/A').upper()} | {ob.get('description', '')}")
            lines.append(f"   Bid Vol: {ob.get('bid_volume', 0):,.0f} | Ask Vol: {ob.get('ask_volume', 0):,.0f}")
            if ob.get("whale_walls"):
                lines.append(f"   Whale Walls: {len(ob.get('whale_walls', []))} detected")

        # Funding Rate
        fr = signals.get("funding_rate", {})
        if fr:
            lines.append(f"\n💰 FUNDING RATE:")
            lines.append(f"   Signal: {fr.get('signal', 'N/A').upper()} | {fr.get('description', '')}")
            lines.append(f"   8h Rate: {fr.get('funding_rate_8h', 0):.4%}")

        # Volume
        vol = signals.get("volume", {})
        if vol:
            spike_emoji = "🔥" if vol.get("is_spike") else "📉"
            lines.append(f"\n{spike_emoji} VOLUME ANALYSIS:")
            lines.append(f"   Signal: {vol.get('signal', 'N/A').upper()} | {vol.get('description', '')}")
            lines.append(f"   Volume Ratio: {vol.get('volume_ratio', 1):.1f}x average")

        # Aggregate
        agg = signals.get("aggregate", {})
        if agg:
            lines.append(f"\n{'=' * 50}")
            signal_emoji = "🟢" if agg.get("signal") == "bullish" else "🔴" if agg.get("signal") == "bearish" else "⚪"
            lines.append(f"{signal_emoji} AGGREGATE SIGNAL: {agg.get('signal', 'N/A').upper()}")
            lines.append(f"   Strength: {agg.get('strength', 0):.0%}")
            lines.append(f"   Net Score: {agg.get('net_score', 0):+.0%}")
            if agg.get("active_signals"):
                lines.append(f"   Active: {', '.join(agg.get('active_signals', []))}")

        lines.append("=" * 50)
        return "\n".join(lines)

    def format_compact(self, signals: Dict[str, Any]) -> str:
        """One-line compact format for terminal logging."""
        parts = []

        # Fear & Greed
        fg = signals.get("fear_greed", {})
        if fg:
            parts.append(f"F&G:{fg.get('value', '?')}")

        # Whale
        wt = signals.get("whale_tracking", {})
        if wt and wt.get("signal") != "neutral":
            parts.append(f"🐋:{wt.get('signal', '?')[:4]}")

        # Orderbook
        ob = signals.get("orderbook", {})
        if ob and ob.get("signal") != "neutral":
            parts.append(f"OB:{ob.get('signal', '?')[:4]}")

        # Aggregate
        agg = signals.get("aggregate", {})
        if agg:
            sig = agg.get("signal", "neutral").upper()[:4]
            score = agg.get("net_score", 0)
            parts.append(f"AGG:{sig}({score:+.0%})")

        return " | ".join(parts) if parts else "No signals"

    def add_whale_to_track(self, address: str, name: str = "", reason: str = ""):
        """Add a whale address to track."""
        if self.whale_tracker:
            self.whale_tracker.add_whale(address, name, reason)
            return True
        return False

    def get_tracked_whales(self) -> List[Dict]:
        """Get list of tracked whales."""
        if self.whale_tracker:
            return self.whale_tracker.tracked_whales
        return []


# Pre-configured whale addresses from Hyperliquid leaderboard
# These are known high-profile traders identified from on-chain analysis and public reports
KNOWN_WHALE_ADDRESSES = [
    # User-specified whale addresses for tracking
    {"address": "0xd47587702a91731dc1089b5db0932cf820151a91", "name": "Whale_d475", "reason": "High-profit trader"},
    {"address": "0x880ac484a1743862989a441d6d867238c7aa311c", "name": "Whale_880a", "reason": "High-profit trader"},
    {"address": "0x5b5d51203a0f9079f8aeb098a6523a13f298c060", "name": "Whale_5b5d", "reason": "High-profit trader"},
    {"address": "0xa312114b5795dff9b8db50474dd57701aa78ad1e", "name": "Whale_a312", "reason": "High-profit trader"},
    {"address": "0x7fdafde5cfb5465924316eced2d3715494c517d1", "name": "Whale_7fda", "reason": "High-profit trader"},
    {"address": "0xecb63caa47c7c4e77f60f1ce858cf28dc2b82b00", "name": "Wintermute", "reason": "Major market maker - #2 all-time PnL ($163M+)"},
    {"address": "0xe554b76acda9ff3836fb04935bdbbaf59854c270", "name": "Whale_e554", "reason": "High-profit trader"},
    {"address": "0x856c35038594767646266bc7fd68dc26480e910d", "name": "Whale_856c", "reason": "High-profit trader"},
    {"address": "0xb83de012dba672c76a7dbbbf3e459cb59d7d6e36", "name": "Whale_b83d", "reason": "High-profit trader"},
    {"address": "0x35d1151ef1aab579cbb3109e69fa82f94ff5acb1", "name": "Whale_35d1", "reason": "High-profit trader"},
    # Additional whale addresses (added 2026-01-13)
    {"address": "0x8af700ba841f30e0a3fcb0ee4c4a9d223e1efa05", "name": "Whale_8af7", "reason": "High-profit trader"},
    {"address": "0x716bd8d3337972db99995dda5c4b34d954a61d95", "name": "Whale_716b", "reason": "High-profit trader"},
    {"address": "0x20c2d95a3dfdca9e9ad12794d5fa6fad99da44f5", "name": "Whale_20c2", "reason": "High-profit trader"},
    {"address": "0x0ddf9bae2af4b874b96d287a5ad42eb47138a902", "name": "Whale_0ddf", "reason": "High-profit trader"},
    {"address": "0x45d26f28196d226497130c4bac709d808fed4029", "name": "Whale_45d2", "reason": "High-profit trader"},
]


def get_default_whale_addresses() -> list:
    """Return the list of known whale addresses for tracking."""
    return KNOWN_WHALE_ADDRESSES.copy()
