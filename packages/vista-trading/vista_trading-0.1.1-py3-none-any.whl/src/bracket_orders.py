"""
Smart Bracket Order System - Data-Driven Level Detection & OCO Orders

This system places HIGH-QUALITY limit orders at validated S/R levels using:
1. Multi-source level detection (swing, volume profile, order book, Fib, SMC)
2. Level quality scoring (confluence = higher score)
3. OCO logic (one fills, cancel the other)
4. Regime-aware placement (brackets in ranges, directional in trends)
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import time

logger = logging.getLogger(__name__)


@dataclass
class ValidatedLevel:
    """A price level validated by multiple data sources."""
    price: float
    side: str  # "support" or "resistance"
    quality_score: float  # 0-100, higher = better
    sources: List[str]  # Which analysis methods confirmed this level
    confluence_count: int  # How many sources agree
    
    # Order placement data
    entry_price: float = 0.0
    stop_loss: float = 0.0
    take_profit: float = 0.0
    rr_ratio: float = 0.0
    
    # Metadata
    distance_pct: float = 0.0  # Distance from current price
    atr_distance: float = 0.0  # Distance in ATR units
    strength: str = "medium"  # "weak", "medium", "strong", "very_strong"
    
    def __post_init__(self):
        """Set strength based on quality score."""
        if self.quality_score >= 80:
            self.strength = "very_strong"
        elif self.quality_score >= 60:
            self.strength = "strong"
        elif self.quality_score >= 40:
            self.strength = "medium"
        else:
            self.strength = "weak"


@dataclass 
class BracketOrder:
    """A bracket order (limit entry with SL/TP)."""
    symbol: str
    side: str  # "long" or "short"
    entry_price: float
    stop_loss: float
    take_profit: float
    size: float
    
    # Level info
    level_quality: float
    level_sources: List[str]
    
    # Order IDs (set after placement)
    entry_oid: Optional[str] = None
    sl_oid: Optional[str] = None
    tp_oid: Optional[str] = None
    
    # State tracking
    status: str = "pending"  # "pending", "placed", "filled", "cancelled", "expired"
    placed_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    filled_at: Optional[datetime] = None
    
    # Performance
    rr_ratio: float = 0.0
    distance_pct: float = 0.0


class SmartBracketSystem:
    """
    Data-driven bracket order system.
    
    Places limit orders at high-quality S/R levels detected by multiple sources.
    Uses OCO logic: when one side fills, cancel the other.
    """
    
    def __init__(
        self,
        hl_client,
        min_quality_score: float = 50.0,  # Minimum level quality to place orders
        min_confluence: int = 2,  # Minimum sources agreeing
        min_rr_ratio: float = 2.0,  # Minimum risk:reward
        max_distance_pct: float = 3.0,  # Max distance from price to place orders
        min_distance_pct: float = 0.5,  # Min distance (avoid immediate fills)
        order_expiry_hours: int = 4,  # Cancel unfilled orders after N hours
    ):
        self.hl = hl_client
        self.min_quality_score = min_quality_score
        self.min_confluence = min_confluence
        self.min_rr_ratio = min_rr_ratio
        self.max_distance_pct = max_distance_pct
        self.min_distance_pct = min_distance_pct
        self.order_expiry_hours = order_expiry_hours
        
        # Track active bracket orders per symbol
        self.active_brackets: Dict[str, Dict[str, BracketOrder]] = {}  # symbol -> {side: order}
        
        # Level cache to avoid recalculating
        self.level_cache: Dict[str, Tuple[List[ValidatedLevel], float]] = {}  # symbol -> (levels, timestamp)
        self.cache_ttl = 300  # 5 minutes
        
    def analyze_levels(
        self,
        symbol: str,
        current_price: float,
        market_data: Dict[str, Any]
    ) -> List[ValidatedLevel]:
        """
        Analyze and score all potential S/R levels from multiple sources.
        
        Sources used:
        1. Swing highs/lows (technical_analysis.calculate_support_resistance)
        2. Volume Profile (POC, VAH, VAL)
        3. Order Book walls (large limit orders)
        4. Fibonacci levels (38.2%, 50%, 61.8%)
        5. Smart Money (Order Blocks, FVG)
        6. Trendlines (ascending support, descending resistance)
        7. VWAP bands
        8. Ichimoku cloud (Senkou spans)
        
        Returns:
            List of ValidatedLevel sorted by quality score (highest first)
        """
        # Check cache
        cached = self.level_cache.get(symbol)
        if cached:
            levels, cached_time = cached
            if time.time() - cached_time < self.cache_ttl:
                return levels
        
        all_levels: Dict[float, Dict[str, Any]] = {}  # price -> {sources, scores}
        
        # Helper to add/merge levels
        def add_level(price: float, side: str, source: str, base_score: float, metadata: Dict = None):
            """Add a level, merging with existing if close enough."""
            # Find nearby level (within 0.2%)
            threshold = current_price * 0.002
            for existing_price in list(all_levels.keys()):
                if abs(existing_price - price) < threshold:
                    # Merge into existing
                    all_levels[existing_price]["sources"].append(source)
                    all_levels[existing_price]["score"] += base_score * 0.5  # Confluence bonus
                    if metadata:
                        all_levels[existing_price]["metadata"].update(metadata)
                    return
            
            # New level
            all_levels[price] = {
                "price": price,
                "side": side,
                "sources": [source],
                "score": base_score,
                "metadata": metadata or {}
            }

        # === SOURCE 1: SWING HIGHS/LOWS (base: 15 points) ===
        sr_data = market_data.get("sr_data", {})
        for support in sr_data.get("supports", []):
            if support < current_price:
                add_level(support, "support", "swing_low", 15)
        for resistance in sr_data.get("resistances", []):
            if resistance > current_price:
                add_level(resistance, "resistance", "swing_high", 15)

        # Consolidation zones get extra weight
        consol = sr_data.get("consolidation_zone", {})
        if consol:
            if consol.get("type") == "support_building":
                add_level(consol["level"], "support", "consolidation", 20, {"touches": consol.get("touches", 0)})
            elif consol.get("type") == "resistance_building":
                add_level(consol["level"], "resistance", "consolidation", 20, {"touches": consol.get("touches", 0)})

        # === SOURCE 2: VOLUME PROFILE (base: 20 points - very reliable) ===
        vp_data = market_data.get("volume_profile", {})
        if vp_data.get("valid"):
            poc = vp_data.get("poc")
            vah = vp_data.get("vah")
            val = vp_data.get("val")

            if poc:
                side = "support" if poc < current_price else "resistance"
                add_level(poc, side, "volume_poc", 25, {"type": "Point of Control"})
            if vah and vah > current_price:
                add_level(vah, "resistance", "volume_vah", 18, {"type": "Value Area High"})
            if val and val < current_price:
                add_level(val, "support", "volume_val", 18, {"type": "Value Area Low"})

            # High volume nodes
            for node in vp_data.get("high_volume_nodes", []):
                side = "support" if node["price"] < current_price else "resistance"
                add_level(node["price"], side, "volume_node", 12, {"volume": node.get("volume", 0)})

        # === SOURCE 3: ORDER BOOK WALLS (base: 18 points - real-time liquidity) ===
        ob_data = market_data.get("orderbook", {})
        walls = ob_data.get("walls", {})

        for wall in walls.get("bid_walls", []):
            if wall.get("distance_pct", 10) <= self.max_distance_pct:
                strength_bonus = min(wall.get("strength", 1) * 3, 10)  # Up to 10 bonus points
                add_level(wall["price"], "support", "orderbook_wall", 18 + strength_bonus,
                         {"size": wall.get("size", 0), "strength": wall.get("strength", 0)})

        for wall in walls.get("ask_walls", []):
            if wall.get("distance_pct", 10) <= self.max_distance_pct:
                strength_bonus = min(wall.get("strength", 1) * 3, 10)
                add_level(wall["price"], "resistance", "orderbook_wall", 18 + strength_bonus,
                         {"size": wall.get("size", 0), "strength": wall.get("strength", 0)})

        # === SOURCE 4: FIBONACCI LEVELS (base: 12-18 points) ===
        fib_data = market_data.get("fibonacci", {})
        fib_levels = fib_data.get("levels", {})

        # Weight by importance: 61.8% > 50% > 38.2% > 78.6% > 23.6%
        fib_weights = {"0.618": 18, "0.5": 15, "0.382": 12, "0.786": 10, "0.236": 8}

        for level_name, weight in fib_weights.items():
            price = fib_levels.get(level_name)
            if price:
                side = "support" if price < current_price else "resistance"
                add_level(price, side, f"fib_{level_name}", weight, {"fib_level": level_name})

        # === SOURCE 5: SMART MONEY CONCEPTS (base: 20-25 points - institutional) ===
        smc_data = market_data.get("smart_money", {})

        # Order Blocks - where institutions placed orders
        for ob in smc_data.get("order_blocks", []):
            if not ob.get("mitigated", True):  # Only unmitigated OBs
                if ob.get("is_bullish"):
                    add_level(ob["low"], "support", "order_block", 22,
                             {"type": "bullish_ob", "strength": ob.get("strength", 0.5)})
                else:
                    add_level(ob["high"], "resistance", "order_block", 22,
                             {"type": "bearish_ob", "strength": ob.get("strength", 0.5)})

        # Fair Value Gaps - imbalances price tends to fill
        for fvg in smc_data.get("fair_value_gaps", []):
            if fvg.get("filled_pct", 1.0) < 0.5:  # Less than 50% filled
                if fvg.get("is_bullish"):
                    add_level(fvg["low"], "support", "fvg", 15, {"type": "bullish_fvg"})
                else:
                    add_level(fvg["high"], "resistance", "fvg", 15, {"type": "bearish_fvg"})

        # Liquidity zones (where stops are likely)
        liq_zones = smc_data.get("liquidity_zones", {})
        for zone in liq_zones.get("below_price", []):
            add_level(zone["price"], "support", "liquidity_zone", 12, {"type": "stop_hunt_target"})
        for zone in liq_zones.get("above_price", []):
            add_level(zone["price"], "resistance", "liquidity_zone", 12, {"type": "stop_hunt_target"})

        # === SOURCE 6: TRENDLINES (base: 15 points) ===
        trendlines = market_data.get("trendlines", {})

        asc_support = trendlines.get("ascending_support", {})
        if asc_support and asc_support.get("current_price"):
            add_level(asc_support["current_price"], "support", "ascending_trendline", 15,
                     {"touches": asc_support.get("touches", 2), "slope": asc_support.get("slope", 0)})

        desc_resist = trendlines.get("descending_resistance", {})
        if desc_resist and desc_resist.get("current_price"):
            add_level(desc_resist["current_price"], "resistance", "descending_trendline", 15,
                     {"touches": desc_resist.get("touches", 2), "slope": desc_resist.get("slope", 0)})

        # === SOURCE 7: VWAP BANDS (base: 10 points) ===
        vwap_data = market_data.get("vwap", {})
        if vwap_data.get("vwap"):
            vwap = vwap_data["vwap"]
            lower_band = vwap_data.get("lower_band", vwap * 0.99)
            upper_band = vwap_data.get("upper_band", vwap * 1.01)

            if lower_band < current_price:
                add_level(lower_band, "support", "vwap_lower", 10)
            if upper_band > current_price:
                add_level(upper_band, "resistance", "vwap_upper", 10)

            # VWAP itself is key S/R
            side = "support" if vwap < current_price else "resistance"
            add_level(vwap, side, "vwap", 12)

        # === SOURCE 8: ICHIMOKU CLOUD (base: 12 points) ===
        ichimoku = market_data.get("ichimoku", {})
        senkou_a = ichimoku.get("senkou_a")
        senkou_b = ichimoku.get("senkou_b")
        kijun = ichimoku.get("kijun_sen")

        if senkou_a and senkou_b:
            cloud_top = max(senkou_a, senkou_b)
            cloud_bottom = min(senkou_a, senkou_b)

            if cloud_bottom < current_price:
                add_level(cloud_bottom, "support", "ichimoku_cloud", 12, {"type": "cloud_bottom"})
            if cloud_top > current_price:
                add_level(cloud_top, "resistance", "ichimoku_cloud", 12, {"type": "cloud_top"})

        if kijun:
            side = "support" if kijun < current_price else "resistance"
            add_level(kijun, side, "kijun_sen", 10, {"type": "base_line"})

        # === CONVERT TO ValidatedLevel OBJECTS ===
        validated_levels = []
        atr = market_data.get("atr", current_price * 0.02)

        for price, data in all_levels.items():
            distance_pct = abs(current_price - price) / current_price * 100

            # Skip levels outside our range
            if distance_pct < self.min_distance_pct or distance_pct > self.max_distance_pct:
                continue

            # Calculate final quality score
            base_score = data["score"]
            confluence = len(data["sources"])

            # Confluence multiplier: more sources = higher confidence
            confluence_multiplier = 1.0 + (confluence - 1) * 0.15  # +15% per extra source
            final_score = min(base_score * confluence_multiplier, 100)

            # Distance penalty: prefer levels not too far
            if distance_pct > 2.0:
                final_score *= 0.9  # 10% penalty for levels >2% away

            validated_levels.append(ValidatedLevel(
                price=price,
                side=data["side"],
                quality_score=final_score,
                sources=data["sources"],
                confluence_count=confluence,
                distance_pct=distance_pct,
                atr_distance=abs(current_price - price) / atr if atr else 0
            ))

        # Sort by quality score (highest first)
        validated_levels.sort(key=lambda x: x.quality_score, reverse=True)

        # Cache results
        self.level_cache[symbol] = (validated_levels, time.time())

        return validated_levels

    def calculate_bracket_levels(
        self,
        level: ValidatedLevel,
        current_price: float,
        atr: float,
        leverage: int = 10
    ) -> ValidatedLevel:
        """
        Calculate entry, SL, and TP for a bracket order at this level.

        For SUPPORT (long entry):
        - Entry: At support level
        - SL: Below support (0.5% or 1.5 ATR, whichever is smaller but respects 5% max loss)
        - TP: Next resistance or 2.5x risk distance

        For RESISTANCE (short entry):
        - Entry: At resistance level
        - SL: Above resistance
        - TP: Next support or 2.5x risk distance
        """
        # Max SL distance based on 5% max position loss
        max_sl_pct = 5.0 / leverage

        if level.side == "support":
            # LONG at support
            level.entry_price = level.price

            # SL below support - use 1.5 ATR or 0.5%, whichever fits under max
            sl_distance_atr = atr * 1.5
            sl_distance_pct = level.price * 0.005  # 0.5%
            sl_distance = min(sl_distance_atr, sl_distance_pct)

            # Enforce max SL
            max_sl_distance = level.price * (max_sl_pct / 100)
            sl_distance = min(sl_distance, max_sl_distance)

            level.stop_loss = level.price - sl_distance

            # TP: 2.5x risk or next resistance
            risk_distance = level.price - level.stop_loss
            level.take_profit = level.price + (risk_distance * 2.5)

        else:  # resistance
            # SHORT at resistance
            level.entry_price = level.price

            # SL above resistance
            sl_distance_atr = atr * 1.5
            sl_distance_pct = level.price * 0.005
            sl_distance = min(sl_distance_atr, sl_distance_pct)

            max_sl_distance = level.price * (max_sl_pct / 100)
            sl_distance = min(sl_distance, max_sl_distance)

            level.stop_loss = level.price + sl_distance

            # TP: 2.5x risk
            risk_distance = level.stop_loss - level.price
            level.take_profit = level.price - (risk_distance * 2.5)

        # Calculate R:R
        if level.side == "support":
            risk = level.entry_price - level.stop_loss
            reward = level.take_profit - level.entry_price
        else:
            risk = level.stop_loss - level.entry_price
            reward = level.entry_price - level.take_profit

        level.rr_ratio = reward / risk if risk > 0 else 0

        return level

    def get_best_bracket_levels(
        self,
        symbol: str,
        current_price: float,
        market_data: Dict[str, Any],
        leverage: int = 10
    ) -> Tuple[Optional[ValidatedLevel], Optional[ValidatedLevel]]:
        """
        Get the best support (for long) and resistance (for short) levels.

        Returns:
            (best_support, best_resistance) - either can be None if no quality level found
        """
        levels = self.analyze_levels(symbol, current_price, market_data)
        atr = market_data.get("atr", current_price * 0.02)

        best_support = None
        best_resistance = None

        for level in levels:
            # Filter by quality
            if level.quality_score < self.min_quality_score:
                continue
            if level.confluence_count < self.min_confluence:
                continue

            # Calculate SL/TP
            level = self.calculate_bracket_levels(level, current_price, atr, leverage)

            # Filter by R:R
            if level.rr_ratio < self.min_rr_ratio:
                continue

            # Assign to best support/resistance
            if level.side == "support" and best_support is None:
                best_support = level
            elif level.side == "resistance" and best_resistance is None:
                best_resistance = level

            # Got both? Stop looking
            if best_support and best_resistance:
                break

        return best_support, best_resistance

    async def place_bracket_orders(
        self,
        symbol: str,
        current_price: float,
        market_data: Dict[str, Any],
        position_size_usd: float,
        leverage: int = 10
    ) -> Dict[str, Any]:
        """
        Place bracket orders at best S/R levels.

        In RANGING market: Place both long at support AND short at resistance (OCO)
        In TRENDING market: Only place in trend direction

        Returns:
            Dict with placed orders info
        """
        regime = market_data.get("adaptive_regime", "ranging")
        adx = market_data.get("adx", 20)
        trend_direction = market_data.get("trend_direction", "neutral")

        best_support, best_resistance = self.get_best_bracket_levels(
            symbol, current_price, market_data, leverage
        )

        results = {"long_order": None, "short_order": None, "regime": regime}

        # Determine which orders to place based on regime
        place_long = False
        place_short = False

        if regime in ["ranging", "low_volatility"] or adx < 20:
            # Ranging: Place both sides (OCO)
            place_long = best_support is not None
            place_short = best_resistance is not None
            results["strategy"] = "oco_bracket"
            logger.info(f"📊 {symbol} RANGING (ADX={adx:.0f}) - placing OCO brackets")
        else:
            # Trending: Only trade with trend
            if trend_direction == "bullish" or regime == "trending_up":
                place_long = best_support is not None
                results["strategy"] = "trend_long_only"
                logger.info(f"📈 {symbol} TRENDING UP - long bracket only")
            elif trend_direction == "bearish" or regime == "trending_down":
                place_short = best_resistance is not None
                results["strategy"] = "trend_short_only"
                logger.info(f"📉 {symbol} TRENDING DOWN - short bracket only")
            else:
                # Unclear trend, place both
                place_long = best_support is not None
                place_short = best_resistance is not None
                results["strategy"] = "oco_bracket"

        # Calculate position size
        notional = position_size_usd * leverage
        size = notional / current_price

        # Round size appropriately
        if current_price > 1000:
            size = round(size, 5)
        else:
            size = round(size, 3)

        # Place LONG bracket at support
        if place_long and best_support:
            try:
                order_result = await self._place_single_bracket(
                    symbol, "long", best_support, size
                )
                if order_result.get("success"):
                    results["long_order"] = {
                        "entry": best_support.entry_price,
                        "stop_loss": best_support.stop_loss,
                        "take_profit": best_support.take_profit,
                        "rr_ratio": best_support.rr_ratio,
                        "quality": best_support.quality_score,
                        "sources": best_support.sources,
                        "oid": order_result.get("oid")
                    }
                    logger.info(f"✅ LONG bracket placed: Entry ${best_support.entry_price:,.2f} | "
                               f"SL ${best_support.stop_loss:,.2f} | TP ${best_support.take_profit:,.2f} | "
                               f"Quality: {best_support.quality_score:.0f} | Sources: {best_support.sources}")
            except Exception as e:
                logger.error(f"Failed to place long bracket: {e}")

        # Place SHORT bracket at resistance
        if place_short and best_resistance:
            try:
                order_result = await self._place_single_bracket(
                    symbol, "short", best_resistance, size
                )
                if order_result.get("success"):
                    results["short_order"] = {
                        "entry": best_resistance.entry_price,
                        "stop_loss": best_resistance.stop_loss,
                        "take_profit": best_resistance.take_profit,
                        "rr_ratio": best_resistance.rr_ratio,
                        "quality": best_resistance.quality_score,
                        "sources": best_resistance.sources,
                        "oid": order_result.get("oid")
                    }
                    logger.info(f"✅ SHORT bracket placed: Entry ${best_resistance.entry_price:,.2f} | "
                               f"SL ${best_resistance.stop_loss:,.2f} | TP ${best_resistance.take_profit:,.2f} | "
                               f"Quality: {best_resistance.quality_score:.0f} | Sources: {best_resistance.sources}")
            except Exception as e:
                logger.error(f"Failed to place short bracket: {e}")

        # Store active brackets for OCO management
        if results["long_order"] or results["short_order"]:
            self.active_brackets[symbol] = {
                "long": results["long_order"],
                "short": results["short_order"],
                "placed_at": datetime.now(),
                "expires_at": datetime.now() + timedelta(hours=self.order_expiry_hours)
            }

        return results

    async def _place_single_bracket(
        self,
        symbol: str,
        side: str,
        level: ValidatedLevel,
        size: float
    ) -> Dict[str, Any]:
        """Place a single bracket order (limit entry with native SL/TP)."""
        try:
            # Place limit order with native SL/TP
            result = self.hl.place_limit_order_with_sl_tp(
                symbol=symbol,
                side=side,
                size=size,
                limit_price=level.entry_price,
                stop_loss=level.stop_loss,
                take_profit=level.take_profit,
                reduce_only=False
            )

            return {
                "success": result.get("success", False),
                "oid": result.get("oid"),
                "sl_oid": result.get("sl_oid"),
                "tp_oid": result.get("tp_oid")
            }
        except Exception as e:
            logger.error(f"Bracket order placement failed: {e}")
            return {"success": False, "error": str(e)}

    async def check_and_manage_brackets(self, symbol: str) -> Dict[str, Any]:
        """
        Check bracket orders and implement OCO logic.

        - If one side fills, cancel the other
        - If orders expire, cancel both
        - Update tracking state

        Returns:
            Dict with status and any actions taken
        """
        if symbol not in self.active_brackets:
            return {"status": "no_brackets"}

        brackets = self.active_brackets[symbol]
        now = datetime.now()
        actions = []

        # Check for expiry
        if brackets.get("expires_at") and now > brackets["expires_at"]:
            logger.info(f"⏰ {symbol} brackets expired - cancelling")
            await self._cancel_all_brackets(symbol)
            del self.active_brackets[symbol]
            return {"status": "expired", "actions": ["cancelled_all"]}

        # Check if we have a position (one bracket filled)
        try:
            positions = self.hl.get_positions()
            has_position = False
            position_side = None

            for pos in positions:
                if pos.get("symbol") == symbol:
                    size = pos.get("size", pos.get("szi", 0))
                    if isinstance(size, str):
                        size = float(size)
                    if abs(size) > 0:
                        has_position = True
                        position_side = "long" if size > 0 else "short"
                        break

            if has_position:
                # OCO: Cancel the opposite side
                opposite_side = "short" if position_side == "long" else "long"
                opposite_order = brackets.get(opposite_side)

                if opposite_order and opposite_order.get("oid"):
                    logger.info(f"🔄 {symbol} {position_side.upper()} filled - cancelling {opposite_side} bracket (OCO)")
                    try:
                        self.hl.cancel_order(symbol, opposite_order["oid"])
                        actions.append(f"cancelled_{opposite_side}")
                    except Exception as e:
                        logger.warning(f"Failed to cancel opposite bracket: {e}")

                # Clean up tracking (position now managed by main bot)
                del self.active_brackets[symbol]
                return {
                    "status": "filled",
                    "filled_side": position_side,
                    "actions": actions
                }

        except Exception as e:
            logger.error(f"Error checking bracket status: {e}")

        return {"status": "active", "actions": actions}

    async def _cancel_all_brackets(self, symbol: str) -> None:
        """Cancel all bracket orders for a symbol."""
        brackets = self.active_brackets.get(symbol, {})

        for side in ["long", "short"]:
            order = brackets.get(side)
            if order and order.get("oid"):
                try:
                    self.hl.cancel_order(symbol, order["oid"])
                    logger.info(f"❌ Cancelled {side} bracket for {symbol}")
                except Exception as e:
                    logger.warning(f"Failed to cancel {side} bracket: {e}")

    def get_bracket_status(self, symbol: str) -> Dict[str, Any]:
        """Get current bracket order status for a symbol."""
        if symbol not in self.active_brackets:
            return {"has_brackets": False}

        brackets = self.active_brackets[symbol]
        return {
            "has_brackets": True,
            "long_order": brackets.get("long"),
            "short_order": brackets.get("short"),
            "placed_at": brackets.get("placed_at"),
            "expires_at": brackets.get("expires_at"),
            "time_remaining": (brackets["expires_at"] - datetime.now()).total_seconds() / 3600
                             if brackets.get("expires_at") else None
        }

    def log_level_analysis(self, symbol: str, levels: List[ValidatedLevel]) -> None:
        """Log detailed analysis of detected levels."""
        logger.info(f"\n{'='*60}")
        logger.info(f"📊 {symbol} LEVEL ANALYSIS - Top Quality Levels")
        logger.info(f"{'='*60}")

        supports = [l for l in levels if l.side == "support"][:3]
        resistances = [l for l in levels if l.side == "resistance"][:3]

        if supports:
            logger.info(f"\n🟢 SUPPORT LEVELS (for LONG entries):")
            for i, level in enumerate(supports, 1):
                logger.info(f"  {i}. ${level.price:,.2f} | Quality: {level.quality_score:.0f} | "
                           f"Confluence: {level.confluence_count} | Sources: {', '.join(level.sources)}")

        if resistances:
            logger.info(f"\n🔴 RESISTANCE LEVELS (for SHORT entries):")
            for i, level in enumerate(resistances, 1):
                logger.info(f"  {i}. ${level.price:,.2f} | Quality: {level.quality_score:.0f} | "
                           f"Confluence: {level.confluence_count} | Sources: {', '.join(level.sources)}")

        logger.info(f"{'='*60}\n")

