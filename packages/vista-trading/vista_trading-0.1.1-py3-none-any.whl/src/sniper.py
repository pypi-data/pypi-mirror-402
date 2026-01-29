"""
Sniper Module - Advanced entry detection and limit order management.

Features:
1. Orderbook Absorption Detection - Detect whale walls being eaten
2. Limit Order Sniping - Place orders at key levels
3. Confluence Scoring - Weighted multi-signal scoring
4. Trendline Bounce Detection - Entry on support/resistance touches
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum

logger = logging.getLogger(__name__)


class SignalType(Enum):
    BULLISH = "bullish"
    BEARISH = "bearish"
    NEUTRAL = "neutral"


@dataclass
class SniperConfig:
    """Configuration for the sniper system."""
    # Orderbook absorption thresholds
    absorption_threshold_pct: float = 30.0  # Wall reduced by 30% = absorption
    whale_wall_min_size_usd: float = 100000  # $100k minimum for whale wall
    
    # Limit order settings
    limit_order_offset_pct: float = 0.1  # Place limit 0.1% inside level
    limit_order_timeout_seconds: int = 300  # Cancel after 5 minutes
    
    # Confluence thresholds
    min_confluence_score: float = 60.0  # Minimum score to trigger entry
    strong_confluence_score: float = 80.0  # Strong signal threshold
    
    # Fast loop settings
    fast_loop_interval_seconds: float = 5.0  # Check every 5 seconds


@dataclass
class OrderbookSnapshot:
    """Snapshot of orderbook state for absorption detection."""
    timestamp: datetime
    bid_walls: List[Dict]  # [{price, size, size_usd}]
    ask_walls: List[Dict]
    total_bid_volume: float
    total_ask_volume: float
    imbalance: float  # -1 to +1


@dataclass
class PendingLimitOrder:
    """Tracks a pending limit order."""
    symbol: str
    side: str  # "buy" or "sell"
    price: float
    size: float
    reason: str  # Why this order was placed
    created_at: datetime
    order_id: Optional[str] = None
    level_type: str = "support"  # "support", "resistance", "trendline"


class OrderbookAbsorptionDetector:
    """Detects when whale walls are being absorbed (momentum signal)."""
    
    def __init__(self, config: SniperConfig):
        self.config = config
        self.snapshots: Dict[str, List[OrderbookSnapshot]] = {}  # symbol -> snapshots
        self.max_snapshots = 60  # Keep last 60 snapshots (5 min at 5s intervals)
    
    def record_snapshot(self, symbol: str, orderbook: Dict, current_price: float) -> None:
        """Record orderbook snapshot for absorption analysis."""
        if symbol not in self.snapshots:
            self.snapshots[symbol] = []

        bids = orderbook.get("bids", [])
        asks = orderbook.get("asks", [])

        # Find whale walls (large orders)
        bid_walls = self._find_whale_walls(bids, current_price, "bid")
        ask_walls = self._find_whale_walls(asks, current_price, "ask")

        # Calculate volumes (handle multiple formats)
        bid_volume = self._calculate_total_volume(bids)
        ask_volume = self._calculate_total_volume(asks)
        total = bid_volume + ask_volume
        imbalance = (bid_volume - ask_volume) / total if total > 0 else 0

        snapshot = OrderbookSnapshot(
            timestamp=datetime.utcnow(),
            bid_walls=bid_walls,
            ask_walls=ask_walls,
            total_bid_volume=bid_volume,
            total_ask_volume=ask_volume,
            imbalance=imbalance
        )
        
        self.snapshots[symbol].append(snapshot)

        # Trim old snapshots
        if len(self.snapshots[symbol]) > self.max_snapshots:
            self.snapshots[symbol] = self.snapshots[symbol][-self.max_snapshots:]

    def _calculate_total_volume(self, orders: List) -> float:
        """Calculate total volume from orderbook orders.

        Handles multiple formats:
        - List of [price, size] arrays
        - List of dicts with {sz} or {size}
        """
        total = 0.0
        for order in orders:
            try:
                if isinstance(order, (list, tuple)) and len(order) >= 2:
                    total += float(order[1])  # [price, size]
                elif isinstance(order, dict):
                    total += float(order.get("sz", order.get("size", 0)))
            except (TypeError, ValueError, IndexError):
                continue
        return total

    def _find_whale_walls(self, orders: List, current_price: float, side: str) -> List[Dict]:
        """Find whale-sized orders in the orderbook.

        Handles multiple orderbook formats:
        - List of [price, size] arrays
        - List of dicts with {px, sz} or {price, size}
        """
        walls = []
        for order in orders[:20]:  # Check top 20 levels
            try:
                # Handle different formats
                if isinstance(order, (list, tuple)) and len(order) >= 2:
                    # Format: [price, size]
                    price = float(order[0])
                    size = float(order[1])
                elif isinstance(order, dict):
                    # Format: {px, sz} or {price, size}
                    price = float(order.get("px", order.get("price", 0)))
                    size = float(order.get("sz", order.get("size", 0)))
                else:
                    continue

                size_usd = size * price

                if size_usd >= self.config.whale_wall_min_size_usd:
                    walls.append({
                        "price": price,
                        "size": size,
                        "size_usd": size_usd,
                        "distance_pct": abs(price - current_price) / current_price * 100 if current_price > 0 else 0
                    })
            except (TypeError, ValueError, IndexError):
                continue

        return walls
    
    def detect_absorption(self, symbol: str) -> Dict[str, Any]:
        """Detect if whale walls are being absorbed."""
        if symbol not in self.snapshots or len(self.snapshots[symbol]) < 10:
            return {"detected": False, "signal": "insufficient_data"}
        
        snapshots = self.snapshots[symbol]
        current = snapshots[-1]
        # Compare to 30 seconds ago (6 snapshots at 5s intervals)
        past_idx = max(0, len(snapshots) - 7)
        past = snapshots[past_idx]
        
        result = {
            "detected": False,
            "signal": "neutral",
            "strength": 0.0,
            "details": []
        }
        
        # Check bid wall absorption (walls shrinking = selling pressure winning)
        for past_wall in past.bid_walls:
            # Find same wall in current snapshot
            current_wall = next(
                (w for w in current.bid_walls if abs(w["price"] - past_wall["price"]) < 0.01),
                None
            )
            if current_wall:
                reduction_pct = (past_wall["size"] - current_wall["size"]) / past_wall["size"] * 100
                if reduction_pct >= self.config.absorption_threshold_pct:
                    result["detected"] = True
                    result["signal"] = "bearish"  # Bid wall being eaten = bearish
                    result["strength"] = min(reduction_pct / 50, 1.0)
                    result["details"].append({
                        "type": "bid_absorption",
                        "price": past_wall["price"],
                        "reduction_pct": round(reduction_pct, 1)
                    })
            elif past_wall["size_usd"] > self.config.whale_wall_min_size_usd * 2:
                # Large wall completely disappeared
                result["detected"] = True
                result["signal"] = "bearish"
                result["strength"] = 0.9
                result["details"].append({
                    "type": "bid_wall_removed",
                    "price": past_wall["price"],
                    "size_usd": past_wall["size_usd"]
                })

        # Check ask wall absorption (walls shrinking = buying pressure winning)
        for past_wall in past.ask_walls:
            current_wall = next(
                (w for w in current.ask_walls if abs(w["price"] - past_wall["price"]) < 0.01),
                None
            )
            if current_wall:
                reduction_pct = (past_wall["size"] - current_wall["size"]) / past_wall["size"] * 100
                if reduction_pct >= self.config.absorption_threshold_pct:
                    result["detected"] = True
                    result["signal"] = "bullish"  # Ask wall being eaten = bullish
                    result["strength"] = min(reduction_pct / 50, 1.0)
                    result["details"].append({
                        "type": "ask_absorption",
                        "price": past_wall["price"],
                        "reduction_pct": round(reduction_pct, 1)
                    })
            elif past_wall["size_usd"] > self.config.whale_wall_min_size_usd * 2:
                result["detected"] = True
                result["signal"] = "bullish"
                result["strength"] = 0.9
                result["details"].append({
                    "type": "ask_wall_removed",
                    "price": past_wall["price"],
                    "size_usd": past_wall["size_usd"]
                })

        # Imbalance shift detection
        imbalance_shift = current.imbalance - past.imbalance
        if abs(imbalance_shift) > 0.15:  # Significant shift
            if result["signal"] == "neutral":
                result["signal"] = "bullish" if imbalance_shift > 0 else "bearish"
            result["imbalance_shift"] = round(imbalance_shift, 3)

        return result


class LimitOrderSniper:
    """Manages limit orders at key support/resistance levels."""

    def __init__(self, hl_client, config: SniperConfig):
        self.hl = hl_client
        self.config = config
        self.pending_orders: Dict[str, List[PendingLimitOrder]] = {}  # symbol -> orders
        self.filled_levels: Dict[str, List[float]] = {}  # Track filled levels to avoid re-entry

    def place_snipe_order(
        self,
        symbol: str,
        side: str,
        target_price: float,
        size: float,
        reason: str,
        level_type: str = "support",
        stop_loss_price: Optional[float] = None,
        take_profit_price: Optional[float] = None
    ) -> Optional[PendingLimitOrder]:
        """Place a limit order with SL/TP to snipe a key level.

        IMPORTANT: All snipe orders MUST have SL/TP attached for risk management.
        If not provided, defaults are calculated based on entry price.
        """

        # Adjust price slightly inside the level for better fill
        if side == "buy":
            # Place slightly above support for buy
            order_price = target_price * (1 + self.config.limit_order_offset_pct / 100)
        else:
            # Place slightly below resistance for sell
            order_price = target_price * (1 - self.config.limit_order_offset_pct / 100)

        order_price = round(order_price, 2)

        # Calculate default SL/TP if not provided (1.5% SL, 3% TP = 2:1 R:R)
        if stop_loss_price is None:
            if side == "buy":
                stop_loss_price = order_price * 0.985  # 1.5% below entry
            else:
                stop_loss_price = order_price * 1.015  # 1.5% above entry

        if take_profit_price is None:
            if side == "buy":
                take_profit_price = order_price * 1.03  # 3% above entry
            else:
                take_profit_price = order_price * 0.97  # 3% below entry

        logger.info(f"🎯 SNIPE ORDER: {side.upper()} {size} {symbol} @ ${order_price:.2f} ({reason})")
        logger.info(f"   🛑 SL: ${stop_loss_price:.2f} | 🎯 TP: ${take_profit_price:.2f}")

        # Place the limit order WITH SL/TP attached
        result = self.hl.place_limit_order_with_sltp(
            symbol=symbol,
            side=side,
            size=size,
            price=order_price,
            stop_loss_price=stop_loss_price,
            take_profit_price=take_profit_price
        )

        if result.get("success"):
            order = PendingLimitOrder(
                symbol=symbol,
                side=side,
                price=order_price,
                size=size,
                reason=reason,
                created_at=datetime.utcnow(),
                order_id=result.get("order_id"),
                level_type=level_type
            )

            if symbol not in self.pending_orders:
                self.pending_orders[symbol] = []
            self.pending_orders[symbol].append(order)

            logger.info(f"✅ Snipe order placed with SL/TP: {order.order_id}")
            return order
        else:
            logger.error(f"❌ Failed to place snipe order: {result.get('error')}")
            return None

    def check_and_cancel_stale_orders(self) -> List[str]:
        """Cancel orders that have been pending too long."""
        cancelled = []
        now = datetime.utcnow()
        timeout = timedelta(seconds=self.config.limit_order_timeout_seconds)

        for symbol, orders in list(self.pending_orders.items()):
            for order in orders[:]:
                if now - order.created_at > timeout:
                    if order.order_id:
                        result = self.hl.cancel_order(symbol, order.order_id)
                        if result.get("success"):
                            logger.info(f"⏰ Cancelled stale snipe order: {order.order_id}")
                            cancelled.append(order.order_id)
                    orders.remove(order)

        return cancelled

    def get_snipe_opportunities(
        self,
        symbol: str,
        current_price: float,
        support_levels: List[float],
        resistance_levels: List[float],
        trendline_support: Optional[float] = None,
        trendline_resistance: Optional[float] = None
    ) -> List[Dict]:
        """Find opportunities to place snipe orders."""
        opportunities = []

        # Check support levels for buy snipes (price within 1%)
        for level in support_levels:
            distance_pct = (current_price - level) / level * 100
            if 0.2 < distance_pct < 1.5:  # Between 0.2% and 1.5% above support
                opportunities.append({
                    "type": "support_snipe",
                    "side": "buy",
                    "level": level,
                    "distance_pct": distance_pct,
                    "priority": 1.5 - distance_pct  # Closer = higher priority
                })

        # Check resistance levels for sell snipes
        for level in resistance_levels:
            distance_pct = (level - current_price) / current_price * 100
            if 0.2 < distance_pct < 1.5:
                opportunities.append({
                    "type": "resistance_snipe",
                    "side": "sell",
                    "level": level,
                    "distance_pct": distance_pct,
                    "priority": 1.5 - distance_pct
                })

        # Trendline snipes (higher priority)
        if trendline_support:
            distance_pct = (current_price - trendline_support) / trendline_support * 100
            if 0.1 < distance_pct < 1.0:
                opportunities.append({
                    "type": "trendline_support_snipe",
                    "side": "buy",
                    "level": trendline_support,
                    "distance_pct": distance_pct,
                    "priority": 2.0 - distance_pct  # Higher priority for trendlines
                })

        if trendline_resistance:
            distance_pct = (trendline_resistance - current_price) / current_price * 100
            if 0.1 < distance_pct < 1.0:
                opportunities.append({
                    "type": "trendline_resistance_snipe",
                    "side": "sell",
                    "level": trendline_resistance,
                    "distance_pct": distance_pct,
                    "priority": 2.0 - distance_pct
                })

        # Sort by priority (highest first)
        opportunities.sort(key=lambda x: x["priority"], reverse=True)

        return opportunities


class ConfluenceScorer:
    """
    Weighted confluence scoring from multiple signals.

    Score breakdown (100 points max):
    - Trendline touch: 25 points
    - 5m momentum aligned: 15 points
    - 1h EMA aligned: 15 points
    - 4h EMA aligned: 15 points
    - Whale consensus: 10 points
    - Orderbook absorption: 10 points
    - Volume spike: 5 points
    - Fear & Greed extreme: 5 points
    """

    WEIGHTS = {
        "trendline": 25,
        "momentum_5m": 15,
        "ema_1h": 15,
        "ema_4h": 15,
        "whale_consensus": 10,
        "orderbook_absorption": 10,
        "volume_spike": 5,
        "fear_greed": 5
    }

    def __init__(self, config: SniperConfig):
        self.config = config

    def calculate_score(self, signals: Dict[str, Any], direction: str) -> Dict[str, Any]:
        """
        Calculate confluence score for a given direction.

        Args:
            signals: Dict containing all signal data
            direction: "long" or "short"

        Returns:
            Dict with total score, breakdown, and recommendation
        """
        score = 0.0
        breakdown = {}
        reasons = []
        blockers = []  # Signals that block the trade

        # 1. Trendline Analysis (25 points)
        trendline = signals.get("trendline", {})
        tl_signal = trendline.get("signal", "neutral")
        tl_strength = trendline.get("signal_strength", 0)

        if direction == "long" and tl_signal == "at_ascending_support":
            points = self.WEIGHTS["trendline"] * tl_strength
            score += points
            breakdown["trendline"] = points
            reasons.append(f"At ascending trendline support ({tl_strength:.0%} strength)")
        elif direction == "short" and tl_signal == "at_descending_resistance":
            points = self.WEIGHTS["trendline"] * tl_strength
            score += points
            breakdown["trendline"] = points
            reasons.append(f"At descending trendline resistance ({tl_strength:.0%} strength)")
        elif direction == "long" and tl_signal == "breaking_support":
            blockers.append("Breaking below ascending support - DON'T LONG")
        elif direction == "short" and tl_signal == "breaking_resistance":
            blockers.append("Breaking above descending resistance - DON'T SHORT")
        else:
            breakdown["trendline"] = 0

        # 2. 5m Momentum (15 points)
        momentum_5m = signals.get("momentum_5m", {})
        mom_signal = momentum_5m.get("signal", "neutral")
        mom_strength = momentum_5m.get("strength", 0)

        if (direction == "long" and mom_signal == "bullish") or \
           (direction == "short" and mom_signal == "bearish"):
            points = self.WEIGHTS["momentum_5m"] * mom_strength
            score += points
            breakdown["momentum_5m"] = points
            reasons.append(f"5m momentum {mom_signal} ({mom_strength:.0%})")
        elif (direction == "long" and mom_signal == "bearish") or \
             (direction == "short" and mom_signal == "bullish"):
            breakdown["momentum_5m"] = -5  # Penalty
            score -= 5
            blockers.append(f"5m momentum against direction ({mom_signal})")
        else:
            breakdown["momentum_5m"] = 0

        # 3. 1h EMA (15 points)
        ema_1h = signals.get("ema_1h_signal", "neutral")
        if (direction == "long" and ema_1h == "bullish") or \
           (direction == "short" and ema_1h == "bearish"):
            score += self.WEIGHTS["ema_1h"]
            breakdown["ema_1h"] = self.WEIGHTS["ema_1h"]
            reasons.append(f"1h EMA {ema_1h}")
        elif ema_1h != "neutral":
            breakdown["ema_1h"] = -5
            score -= 5
        else:
            breakdown["ema_1h"] = 0

        # 4. 4h EMA (15 points)
        ema_4h = signals.get("ema_4h_signal", "neutral")
        if (direction == "long" and ema_4h == "bullish") or \
           (direction == "short" and ema_4h == "bearish"):
            score += self.WEIGHTS["ema_4h"]
            breakdown["ema_4h"] = self.WEIGHTS["ema_4h"]
            reasons.append(f"4h EMA {ema_4h}")
        elif ema_4h != "neutral":
            breakdown["ema_4h"] = -5
            score -= 5
        else:
            breakdown["ema_4h"] = 0

        # 5. Whale Consensus (10 points)
        whale = signals.get("whale_consensus", {})
        whale_signal = whale.get("signal", "neutral")
        whale_strength = whale.get("strength", 0)

        if (direction == "long" and whale_signal == "bullish") or \
           (direction == "short" and whale_signal == "bearish"):
            points = self.WEIGHTS["whale_consensus"] * whale_strength
            score += points
            breakdown["whale_consensus"] = points
            longs = whale.get("longs", 0)
            shorts = whale.get("shorts", 0)
            reasons.append(f"Whale consensus {whale_signal} ({longs}L/{shorts}S)")
        else:
            breakdown["whale_consensus"] = 0

        # 6. Orderbook Absorption (10 points)
        absorption = signals.get("orderbook_absorption", {})
        abs_signal = absorption.get("signal", "neutral")
        abs_strength = absorption.get("strength", 0)

        if absorption.get("detected"):
            if (direction == "long" and abs_signal == "bullish") or \
               (direction == "short" and abs_signal == "bearish"):
                points = self.WEIGHTS["orderbook_absorption"] * abs_strength
                score += points
                breakdown["orderbook_absorption"] = points
                reasons.append(f"Orderbook absorption {abs_signal}")
            elif abs_signal != "neutral":
                breakdown["orderbook_absorption"] = -5
                score -= 5
                blockers.append(f"Orderbook absorption against ({abs_signal})")
        else:
            breakdown["orderbook_absorption"] = 0

        # 7. Volume Spike (5 points)
        volume = signals.get("volume", {})
        if volume.get("is_spike") or volume.get("volume_ratio", 1) > 2:
            score += self.WEIGHTS["volume_spike"]
            breakdown["volume_spike"] = self.WEIGHTS["volume_spike"]
            reasons.append(f"Volume spike ({volume.get('volume_ratio', 1):.1f}x)")
        else:
            breakdown["volume_spike"] = 0

        # 8. Fear & Greed Extreme (5 points) - Contrarian
        fg = signals.get("fear_greed", {})
        fg_value = fg.get("value", 50)

        if direction == "long" and fg_value < 25:  # Extreme fear = buy
            score += self.WEIGHTS["fear_greed"]
            breakdown["fear_greed"] = self.WEIGHTS["fear_greed"]
            reasons.append(f"Extreme fear ({fg_value}) - contrarian long")
        elif direction == "short" and fg_value > 75:  # Extreme greed = sell
            score += self.WEIGHTS["fear_greed"]
            breakdown["fear_greed"] = self.WEIGHTS["fear_greed"]
            reasons.append(f"Extreme greed ({fg_value}) - contrarian short")
        else:
            breakdown["fear_greed"] = 0

        # Cap score at 100
        score = min(max(score, 0), 100)

        # Determine recommendation
        if blockers:
            recommendation = "BLOCK"
            confidence = 0
        elif score >= self.config.strong_confluence_score:
            recommendation = "STRONG_ENTRY"
            confidence = score / 100
        elif score >= self.config.min_confluence_score:
            recommendation = "ENTRY"
            confidence = score / 100
        else:
            recommendation = "WAIT"
            confidence = score / 100

        return {
            "direction": direction,
            "score": round(score, 1),
            "max_score": 100,
            "recommendation": recommendation,
            "confidence": round(confidence, 2),
            "breakdown": breakdown,
            "reasons": reasons,
            "blockers": blockers
        }

    def get_best_direction(self, signals: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate scores for both directions and return the best one."""
        long_score = self.calculate_score(signals, "long")
        short_score = self.calculate_score(signals, "short")

        if long_score["recommendation"] == "BLOCK" and short_score["recommendation"] == "BLOCK":
            return {"direction": "none", "score": 0, "recommendation": "BLOCKED", "reason": "Both directions blocked"}

        if long_score["score"] > short_score["score"] and long_score["recommendation"] != "BLOCK":
            return {**long_score, "alternative": short_score}
        elif short_score["recommendation"] != "BLOCK":
            return {**short_score, "alternative": long_score}
        else:
            return {**long_score, "alternative": short_score}


class PositionSniper:
    """
    Main sniper class combining all detection and entry systems.
    """

    def __init__(self, hl_client, config: SniperConfig = None):
        self.hl = hl_client
        self.config = config or SniperConfig()

        self.absorption_detector = OrderbookAbsorptionDetector(self.config)
        self.limit_sniper = LimitOrderSniper(hl_client, self.config)
        self.confluence_scorer = ConfluenceScorer(self.config)

        self.last_analysis: Dict[str, Dict] = {}  # symbol -> last analysis result

    def analyze_entry(
        self,
        symbol: str,
        current_price: float,
        orderbook: Dict,
        trendline_data: Dict,
        momentum_5m: Dict,
        ema_1h_signal: str,
        ema_4h_signal: str,
        whale_data: Dict,
        volume_data: Dict,
        fear_greed: Dict
    ) -> Dict[str, Any]:
        """
        Full sniper analysis for entry opportunity.

        Returns comprehensive analysis with confluence score and recommendations.
        """
        # Record orderbook snapshot for absorption detection
        self.absorption_detector.record_snapshot(symbol, orderbook, current_price)

        # Detect orderbook absorption
        absorption = self.absorption_detector.detect_absorption(symbol)

        # Build signals dict for confluence scoring
        signals = {
            "trendline": trendline_data,
            "momentum_5m": momentum_5m,
            "ema_1h_signal": ema_1h_signal,
            "ema_4h_signal": ema_4h_signal,
            "whale_consensus": whale_data,
            "orderbook_absorption": absorption,
            "volume": volume_data,
            "fear_greed": fear_greed
        }

        # Get confluence scores
        best_direction = self.confluence_scorer.get_best_direction(signals)

        # Get snipe opportunities
        support_levels = trendline_data.get("supports", [])
        resistance_levels = trendline_data.get("resistances", [])
        tl_support = trendline_data.get("ascending_support", {}).get("current_price") if trendline_data.get("ascending_support") else None
        tl_resistance = trendline_data.get("descending_resistance", {}).get("current_price") if trendline_data.get("descending_resistance") else None

        snipe_opportunities = self.limit_sniper.get_snipe_opportunities(
            symbol, current_price, support_levels, resistance_levels, tl_support, tl_resistance
        )

        result = {
            "symbol": symbol,
            "current_price": current_price,
            "timestamp": datetime.utcnow().isoformat(),
            "confluence": best_direction,
            "absorption": absorption,
            "snipe_opportunities": snipe_opportunities[:3],  # Top 3
            "signals_summary": {
                "trendline": trendline_data.get("signal", "neutral"),
                "momentum_5m": momentum_5m.get("signal", "neutral"),
                "ema_1h": ema_1h_signal,
                "ema_4h": ema_4h_signal,
                "whale": whale_data.get("signal", "neutral"),
                "absorption": absorption.get("signal", "neutral")
            }
        }

        self.last_analysis[symbol] = result

        # Log the analysis
        self._log_analysis(result)

        return result

    def _log_analysis(self, analysis: Dict) -> None:
        """Log sniper analysis in readable format."""
        symbol = analysis["symbol"]
        conf = analysis["confluence"]

        # Compact single-line sniper output
        emoji = "🎯" if conf["recommendation"] in ["ENTRY", "STRONG_ENTRY"] else "⏳"
        snipe_info = ""
        if analysis.get("snipe_opportunities"):
            opp = analysis["snipe_opportunities"][0]
            snipe_info = f" | Snipe: ${opp['level']:.2f}"
        logger.info(f"{emoji} {symbol}: {conf['direction'].upper()} {conf['score']}/100{snipe_info}")

    def should_enter(self, symbol: str) -> Tuple[bool, str, float]:
        """
        Quick check if we should enter a position.

        Returns:
            (should_enter, direction, confidence)
        """
        if symbol not in self.last_analysis:
            return False, "none", 0

        analysis = self.last_analysis[symbol]
        conf = analysis["confluence"]

        if conf["recommendation"] in ["ENTRY", "STRONG_ENTRY"]:
            return True, conf["direction"], conf["confidence"]

        return False, conf["direction"], conf["confidence"]
