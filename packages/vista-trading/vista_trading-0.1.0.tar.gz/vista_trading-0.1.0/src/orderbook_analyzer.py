"""
Order Book Analyzer - Professional L2 order flow analysis for trading edge.

This module analyzes the order book to detect:
1. Bid/Ask Imbalance - Pressure from buyers vs sellers
2. Wall Detection - Large orders that act as support/resistance
3. Absorption - Large orders being eaten (smart money entering)
4. Spoofing Detection - Walls that disappear (fake liquidity)
5. Liquidity Gaps - Price levels with thin order book (fast moves)
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class OrderBookSnapshot:
    """A snapshot of the order book at a point in time."""
    timestamp: datetime
    bids: List[Tuple[float, float]]  # [(price, size), ...]
    asks: List[Tuple[float, float]]  # [(price, size), ...]
    mid_price: float
    spread: float
    spread_pct: float
    bid_depth: float  # Total bid size
    ask_depth: float  # Total ask size
    imbalance: float  # Positive = more bids, negative = more asks


@dataclass
class WallInfo:
    """Information about a detected wall (large order)."""
    price: float
    size: float
    side: str  # "bid" or "ask"
    distance_pct: float  # Distance from mid price
    strength: float  # Relative to average order size


class OrderBookAnalyzer:
    """Analyze L2 order book data for trading signals."""

    def __init__(self, info_client=None):
        """
        Args:
            info_client: Hyperliquid Info client for fetching L2 data
        """
        self.info = info_client
        self.snapshots: Dict[str, List[OrderBookSnapshot]] = {}  # symbol -> snapshots
        self.max_snapshots = 60  # Keep 60 snapshots (~5 min at 5s intervals)
        self.wall_threshold = 3.0  # Order > 3x average = wall
        self.imbalance_threshold = 0.3  # 30% imbalance = significant

    def analyze(self, symbol: str, depth: int = 20) -> Dict[str, Any]:
        """
        Comprehensive order book analysis.

        Returns:
            Dict with imbalance, walls, signals, and trading bias
        """
        if not self.info:
            return self._empty_analysis()

        try:
            # Fetch L2 snapshot
            book = self.info.l2_snapshot(symbol)
            if not book or "levels" not in book:
                return self._empty_analysis()

            levels = book.get("levels", [[], []])
            raw_bids = levels[0][:depth] if len(levels) > 0 else []
            raw_asks = levels[1][:depth] if len(levels) > 1 else []

            if not raw_bids or not raw_asks:
                return self._empty_analysis()

            # Parse bids and asks
            bids = [(float(b["px"]), float(b["sz"])) for b in raw_bids]
            asks = [(float(a["px"]), float(a["sz"])) for a in raw_asks]

            # Calculate basic metrics
            best_bid = bids[0][0]
            best_ask = asks[0][0]
            mid_price = (best_bid + best_ask) / 2
            spread = best_ask - best_bid
            spread_pct = (spread / mid_price) * 100

            # Calculate depth
            bid_depth = sum(size for _, size in bids)
            ask_depth = sum(size for _, size in asks)
            total_depth = bid_depth + ask_depth

            # Imbalance: positive = buying pressure, negative = selling pressure
            imbalance = (bid_depth - ask_depth) / total_depth if total_depth > 0 else 0

            # Store snapshot for historical analysis
            snapshot = OrderBookSnapshot(
                timestamp=datetime.utcnow(),
                bids=bids, asks=asks, mid_price=mid_price,
                spread=spread, spread_pct=spread_pct,
                bid_depth=bid_depth, ask_depth=ask_depth,
                imbalance=imbalance
            )
            self._store_snapshot(symbol, snapshot)

            # Detect walls
            walls = self._detect_walls(bids, asks, mid_price)

            # Detect liquidity gaps
            gaps = self._detect_gaps(bids, asks, mid_price)

            # Calculate signals
            signals = self._calculate_signals(symbol, snapshot, walls, gaps)

            return {
                "mid_price": mid_price,
                "spread": spread,
                "spread_pct": round(spread_pct, 4),
                "bid_depth": round(bid_depth, 2),
                "ask_depth": round(ask_depth, 2),
                "imbalance": round(imbalance, 3),
                "imbalance_pct": round(imbalance * 100, 1),
                "walls": walls,
                "gaps": gaps,
                "signals": signals,
                "bias": signals.get("bias", "neutral"),
                "confidence": signals.get("confidence", 0),
                "summary": self._generate_summary(imbalance, walls, signals)
            }

        except Exception as e:
            logger.error(f"Order book analysis failed for {symbol}: {e}")
            return self._empty_analysis()


    def _detect_walls(self, bids: List[Tuple[float, float]],
                      asks: List[Tuple[float, float]],
                      mid_price: float) -> Dict[str, List[Dict]]:
        """Detect large orders (walls) that may act as support/resistance."""
        # Calculate average order size
        all_sizes = [size for _, size in bids + asks]
        avg_size = sum(all_sizes) / len(all_sizes) if all_sizes else 1

        bid_walls = []
        ask_walls = []

        # Check bids for walls
        for price, size in bids:
            if size >= avg_size * self.wall_threshold:
                dist_pct = ((mid_price - price) / mid_price) * 100
                if dist_pct <= 2.0:  # Only walls within 2% of mid
                    bid_walls.append({
                        "price": price,
                        "size": round(size, 2),
                        "distance_pct": round(dist_pct, 2),
                        "strength": round(size / avg_size, 1),
                        "type": "support"
                    })

        # Check asks for walls
        for price, size in asks:
            if size >= avg_size * self.wall_threshold:
                dist_pct = ((price - mid_price) / mid_price) * 100
                if dist_pct <= 2.0:
                    ask_walls.append({
                        "price": price,
                        "size": round(size, 2),
                        "distance_pct": round(dist_pct, 2),
                        "strength": round(size / avg_size, 1),
                        "type": "resistance"
                    })

        return {"bid_walls": bid_walls, "ask_walls": ask_walls}

    def _detect_gaps(self, bids: List[Tuple[float, float]],
                     asks: List[Tuple[float, float]],
                     mid_price: float) -> Dict[str, List[Dict]]:
        """Detect liquidity gaps where price could move quickly."""
        bid_gaps = []
        ask_gaps = []

        # Check bid side gaps
        for i in range(len(bids) - 1):
            price1, _ = bids[i]
            price2, _ = bids[i + 1]
            gap_pct = ((price1 - price2) / mid_price) * 100
            if gap_pct > 0.1:  # Gap > 0.1%
                bid_gaps.append({
                    "from_price": price1,
                    "to_price": price2,
                    "gap_pct": round(gap_pct, 2),
                    "type": "bid_gap"
                })

        # Check ask side gaps
        for i in range(len(asks) - 1):
            price1, _ = asks[i]
            price2, _ = asks[i + 1]
            gap_pct = ((price2 - price1) / mid_price) * 100
            if gap_pct > 0.1:
                ask_gaps.append({
                    "from_price": price1,
                    "to_price": price2,
                    "gap_pct": round(gap_pct, 2),
                    "type": "ask_gap"
                })

        return {"bid_gaps": bid_gaps, "ask_gaps": ask_gaps}

    def _calculate_signals(self, symbol: str, snapshot: OrderBookSnapshot,
                          walls: Dict, gaps: Dict) -> Dict[str, Any]:
        """Calculate trading signals from order book analysis."""
        reasons = []
        bullish_score = 0
        bearish_score = 0

        # 1. Imbalance signal (most important)
        imb = snapshot.imbalance
        if imb > self.imbalance_threshold:
            bullish_score += 30
            reasons.append(f"Strong bid imbalance: {imb*100:.0f}%")
        elif imb < -self.imbalance_threshold:
            bearish_score += 30
            reasons.append(f"Strong ask imbalance: {abs(imb)*100:.0f}%")
        elif imb > 0.1:
            bullish_score += 15
            reasons.append(f"Mild bid imbalance: {imb*100:.0f}%")
        elif imb < -0.1:
            bearish_score += 15
            reasons.append(f"Mild ask imbalance: {abs(imb)*100:.0f}%")

        # 2. Wall signals
        bid_walls = walls.get("bid_walls", [])
        ask_walls = walls.get("ask_walls", [])

        if bid_walls:
            # Strong bid walls = support = bullish
            total_strength = sum(w["strength"] for w in bid_walls)
            bullish_score += min(20, total_strength * 5)
            closest = min(bid_walls, key=lambda w: w["distance_pct"])
            reasons.append(f"Bid wall ${closest['price']:,.0f} ({closest['strength']:.1f}x avg)")

        if ask_walls:
            # Strong ask walls = resistance = bearish
            total_strength = sum(w["strength"] for w in ask_walls)
            bearish_score += min(20, total_strength * 5)
            closest = min(ask_walls, key=lambda w: w["distance_pct"])
            reasons.append(f"Ask wall ${closest['price']:,.0f} ({closest['strength']:.1f}x avg)")

        # 3. Gap signals (potential for fast moves)
        bid_gaps = gaps.get("bid_gaps", [])
        ask_gaps = gaps.get("ask_gaps", [])

        if bid_gaps and not ask_gaps:
            bearish_score += 10
            reasons.append("Bid-side liquidity gap (downside risk)")
        elif ask_gaps and not bid_gaps:
            bullish_score += 10
            reasons.append("Ask-side liquidity gap (upside potential)")

        # 4. Historical imbalance trend (if we have history)
        if symbol in self.snapshots and len(self.snapshots[symbol]) >= 5:
            recent = self.snapshots[symbol][-5:]
            avg_imb = sum(s.imbalance for s in recent) / len(recent)
            if avg_imb > 0.15 and imb > avg_imb:
                bullish_score += 15
                reasons.append("Sustained buying pressure")
            elif avg_imb < -0.15 and imb < avg_imb:
                bearish_score += 15
                reasons.append("Sustained selling pressure")

        # Calculate final bias
        total_score = bullish_score + bearish_score
        if bullish_score > bearish_score + 15:
            bias = "bullish"
            confidence = min(95, (bullish_score / max(total_score, 1)) * 100)
        elif bearish_score > bullish_score + 15:
            bias = "bearish"
            confidence = min(95, (bearish_score / max(total_score, 1)) * 100)
        else:
            bias = "neutral"
            confidence = 50

        return {
            "bias": bias,
            "confidence": round(confidence, 0),
            "bullish_score": bullish_score,
            "bearish_score": bearish_score,
            "reasons": reasons
        }

    def _generate_summary(self, imbalance: float, walls: Dict,
                         signals: Dict) -> str:
        """Generate human-readable summary."""
        bias = signals.get("bias", "neutral")
        conf = signals.get("confidence", 0)

        imb_str = "buying" if imbalance > 0 else "selling"
        wall_count = len(walls.get("bid_walls", [])) + len(walls.get("ask_walls", []))

        return f"OB: {bias.upper()} ({conf:.0f}%) | {abs(imbalance)*100:.0f}% {imb_str} pressure | {wall_count} walls"

    def get_absorption_signal(self, symbol: str) -> Dict[str, Any]:
        """
        Detect absorption: when large orders are being eaten (smart money).

        Requires historical snapshots to detect walls disappearing.
        """
        if symbol not in self.snapshots or len(self.snapshots[symbol]) < 3:
            return {"detected": False, "side": None, "strength": 0}

        # Compare recent snapshots
        old = self.snapshots[symbol][-3]
        new = self.snapshots[symbol][-1]

        # Check if bid depth decreased significantly while price stable
        bid_change = (new.bid_depth - old.bid_depth) / old.bid_depth if old.bid_depth > 0 else 0
        ask_change = (new.ask_depth - old.ask_depth) / old.ask_depth if old.ask_depth > 0 else 0
        price_change = (new.mid_price - old.mid_price) / old.mid_price if old.mid_price > 0 else 0

        # Absorption on bid side: bids getting hit but price not falling much
        if bid_change < -0.2 and abs(price_change) < 0.001:
            return {
                "detected": True,
                "side": "bid_absorption",
                "strength": abs(bid_change),
                "interpretation": "Large bids being absorbed - potential breakdown"
            }

        # Absorption on ask side: asks getting lifted but price not rising much
        if ask_change < -0.2 and abs(price_change) < 0.001:
            return {
                "detected": True,
                "side": "ask_absorption",
                "strength": abs(ask_change),
                "interpretation": "Large asks being absorbed - potential breakout"
            }

        return {"detected": False, "side": None, "strength": 0}

    def _store_snapshot(self, symbol: str, snapshot: OrderBookSnapshot) -> None:
        """Store snapshot for historical analysis."""
        if symbol not in self.snapshots:
            self.snapshots[symbol] = []
        self.snapshots[symbol].append(snapshot)
        if len(self.snapshots[symbol]) > self.max_snapshots:
            self.snapshots[symbol] = self.snapshots[symbol][-self.max_snapshots:]

    def _empty_analysis(self) -> Dict[str, Any]:
        """Return empty analysis when data unavailable."""
        return {
            "mid_price": 0, "spread": 0, "spread_pct": 0,
            "bid_depth": 0, "ask_depth": 0, "imbalance": 0, "imbalance_pct": 0,
            "walls": {"bid_walls": [], "ask_walls": []},
            "gaps": {"bid_gaps": [], "ask_gaps": []},
            "signals": {"bias": "neutral", "confidence": 0, "reasons": []},
            "bias": "neutral", "confidence": 0, "summary": "No order book data"
        }

    def validate_sr_entry(
        self,
        symbol: str,
        sr_signal: str,
        sr_data: Dict[str, Any],
        trend_1h: str,
        min_pressure_pct: float = 60.0,
        min_rr: float = 2.5
    ) -> Dict[str, Any]:
        """
        Validate a Support/Resistance entry using Order Book confluence.

        SHORT setup (near_resistance):
        - Order Book BEARISH with ≥60% selling pressure
        - At least one sell wall exists above price
        - Aggregated trade flow is negative (imbalance < 0)
        - Bid absorption OR ask rejection detected
        - 1H trend is NOT bullish

        LONG setup (near_support):
        - Order Book BULLISH with ≥60% buying pressure
        - At least one buy wall exists below price
        - Aggregated trade flow is positive (imbalance > 0)
        - Ask absorption OR bid rejection detected
        - 1H trend is NOT bearish

        Args:
            symbol: Trading symbol
            sr_signal: "near_resistance" or "near_support"
            sr_data: Support/Resistance data with nearest levels
            trend_1h: 1H trend ("bullish", "bearish", "neutral")
            min_pressure_pct: Minimum pressure percentage (default 60%)
            min_rr: Minimum Risk:Reward ratio (default 2.5)

        Returns:
            Dict with:
                - valid: bool - Whether entry is valid
                - direction: "long" or "short" or None
                - thesis: Dict with entry, stop, target if valid
                - reasons: List of validation reasons
                - failures: List of failed conditions
        """
        result = {
            "valid": False,
            "direction": None,
            "thesis": None,
            "reasons": [],
            "failures": [],
            "conditions_met": 0,
            "conditions_required": 5
        }

        # Get order book analysis
        ob_analysis = self.analyze(symbol, depth=20)
        absorption = self.get_absorption_signal(symbol)

        imbalance = ob_analysis.get("imbalance", 0)
        imbalance_pct = abs(imbalance * 100)
        ob_bias = ob_analysis.get("bias", "neutral")
        walls = ob_analysis.get("walls", {"bid_walls": [], "ask_walls": []})
        bid_walls = walls.get("bid_walls", [])
        ask_walls = walls.get("ask_walls", [])

        current_price = ob_analysis.get("mid_price", 0)

        # === SHORT SETUP (near resistance) ===
        if sr_signal == "near_resistance":
            result["direction"] = "short"
            resistance = sr_data.get("nearest_resistance", current_price * 1.01)
            support = sr_data.get("nearest_support", current_price * 0.97)

            # Condition 1: Order Book BEARISH with ≥60% selling pressure
            if ob_bias == "bearish" and imbalance < 0 and imbalance_pct >= min_pressure_pct:
                result["conditions_met"] += 1
                result["reasons"].append(f"✓ OB BEARISH with {imbalance_pct:.0f}% selling pressure")
            else:
                result["failures"].append(f"✗ OB not bearish enough (bias={ob_bias}, pressure={imbalance_pct:.0f}%)")

            # Condition 2: At least one sell wall above price
            if ask_walls:
                closest_wall = min(ask_walls, key=lambda w: w["distance_pct"])
                result["conditions_met"] += 1
                result["reasons"].append(f"✓ Sell wall at ${closest_wall['price']:,.0f} ({closest_wall['strength']:.1f}x avg)")
            else:
                result["failures"].append("✗ No sell walls above price")

            # Condition 3: Aggregated trade flow is negative
            if imbalance < -0.1:  # At least 10% selling imbalance
                result["conditions_met"] += 1
                result["reasons"].append(f"✓ Trade flow negative ({imbalance*100:.0f}%)")
            else:
                result["failures"].append(f"✗ Trade flow not negative enough ({imbalance*100:.0f}%)")

            # Condition 4: Bid absorption OR ask rejection detected
            absorption_detected = False
            if absorption.get("detected"):
                if absorption.get("side") == "bid_absorption":
                    absorption_detected = True
                    result["reasons"].append(f"✓ Bid absorption detected - {absorption.get('interpretation')}")
            # Also check if asks are being rejected (building up)
            if not absorption_detected and len(ask_walls) >= 2:
                absorption_detected = True
                result["reasons"].append("✓ Ask rejection - multiple sell walls stacking")
            if absorption_detected:
                result["conditions_met"] += 1
            else:
                result["failures"].append("✗ No absorption/rejection pattern")

            # Condition 5: 1H trend is NOT bullish
            if trend_1h != "bullish":
                result["conditions_met"] += 1
                result["reasons"].append(f"✓ 1H trend not bullish ({trend_1h})")
            else:
                result["failures"].append(f"✗ 1H trend is bullish - avoid shorting")

            # Build thesis if valid
            if result["conditions_met"] >= 4:  # At least 4/5 conditions
                # Entry at resistance or rejection wick
                entry = resistance if resistance > current_price else current_price

                # Stop above liquidity wall (or 0.5% above resistance)
                if ask_walls:
                    highest_wall = max(ask_walls, key=lambda w: w["price"])
                    stop = highest_wall["price"] * 1.003  # Just above the wall
                else:
                    stop = resistance * 1.005  # 0.5% above resistance

                # Target to nearest support
                target = support

                # Calculate R:R
                risk = stop - entry
                reward = entry - target
                rr_ratio = reward / risk if risk > 0 else 0

                if rr_ratio >= min_rr:
                    result["valid"] = True
                    result["thesis"] = {
                        "side": "short",
                        "entry": round(entry, 2),
                        "stop_loss": round(stop, 2),
                        "take_profit": round(target, 2),
                        "risk_usd": round(risk, 2),
                        "reward_usd": round(reward, 2),
                        "risk_reward": round(rr_ratio, 2),
                        "thesis_summary": f"SHORT at resistance ${entry:,.0f}. Stop ${stop:,.0f} (above wall). Target ${target:,.0f} (support). R:R {rr_ratio:.1f}"
                    }
                    result["reasons"].append(f"✓ R:R = {rr_ratio:.1f} (min {min_rr})")
                else:
                    result["failures"].append(f"✗ R:R too low: {rr_ratio:.1f} < {min_rr}")

        # === LONG SETUP (near support) ===
        elif sr_signal == "near_support":
            result["direction"] = "long"
            support = sr_data.get("nearest_support", current_price * 0.99)
            resistance = sr_data.get("nearest_resistance", current_price * 1.03)

            # Condition 1: Order Book BULLISH with ≥60% buying pressure
            if ob_bias == "bullish" and imbalance > 0 and imbalance_pct >= min_pressure_pct:
                result["conditions_met"] += 1
                result["reasons"].append(f"✓ OB BULLISH with {imbalance_pct:.0f}% buying pressure")
            else:
                result["failures"].append(f"✗ OB not bullish enough (bias={ob_bias}, pressure={imbalance_pct:.0f}%)")

            # Condition 2: At least one buy wall below price
            if bid_walls:
                closest_wall = min(bid_walls, key=lambda w: w["distance_pct"])
                result["conditions_met"] += 1
                result["reasons"].append(f"✓ Buy wall at ${closest_wall['price']:,.0f} ({closest_wall['strength']:.1f}x avg)")
            else:
                result["failures"].append("✗ No buy walls below price")

            # Condition 3: Aggregated trade flow is positive
            if imbalance > 0.1:  # At least 10% buying imbalance
                result["conditions_met"] += 1
                result["reasons"].append(f"✓ Trade flow positive ({imbalance*100:.0f}%)")
            else:
                result["failures"].append(f"✗ Trade flow not positive enough ({imbalance*100:.0f}%)")

            # Condition 4: Ask absorption OR bid rejection detected
            absorption_detected = False
            if absorption.get("detected"):
                if absorption.get("side") == "ask_absorption":
                    absorption_detected = True
                    result["reasons"].append(f"✓ Ask absorption detected - {absorption.get('interpretation')}")
            # Also check if bids are being rejected (building up)
            if not absorption_detected and len(bid_walls) >= 2:
                absorption_detected = True
                result["reasons"].append("✓ Bid rejection - multiple buy walls stacking")
            if absorption_detected:
                result["conditions_met"] += 1
            else:
                result["failures"].append("✗ No absorption/rejection pattern")

            # Condition 5: 1H trend is NOT bearish
            if trend_1h != "bearish":
                result["conditions_met"] += 1
                result["reasons"].append(f"✓ 1H trend not bearish ({trend_1h})")
            else:
                result["failures"].append(f"✗ 1H trend is bearish - avoid longing")

            # Build thesis if valid
            if result["conditions_met"] >= 4:  # At least 4/5 conditions
                # Entry at support or bounce wick
                entry = support if support < current_price else current_price

                # Stop below liquidity wall (or 0.5% below support)
                if bid_walls:
                    lowest_wall = min(bid_walls, key=lambda w: w["price"])
                    stop = lowest_wall["price"] * 0.997  # Just below the wall
                else:
                    stop = support * 0.995  # 0.5% below support

                # Target to nearest resistance
                target = resistance

                # Calculate R:R
                risk = entry - stop
                reward = target - entry
                rr_ratio = reward / risk if risk > 0 else 0

                if rr_ratio >= min_rr:
                    result["valid"] = True
                    result["thesis"] = {
                        "side": "long",
                        "entry": round(entry, 2),
                        "stop_loss": round(stop, 2),
                        "take_profit": round(target, 2),
                        "risk_usd": round(risk, 2),
                        "reward_usd": round(reward, 2),
                        "risk_reward": round(rr_ratio, 2),
                        "thesis_summary": f"LONG at support ${entry:,.0f}. Stop ${stop:,.0f} (below wall). Target ${target:,.0f} (resistance). R:R {rr_ratio:.1f}"
                    }
                    result["reasons"].append(f"✓ R:R = {rr_ratio:.1f} (min {min_rr})")
                else:
                    result["failures"].append(f"✗ R:R too low: {rr_ratio:.1f} < {min_rr}")

        else:
            result["failures"].append(f"S/R signal '{sr_signal}' not actionable (need near_resistance or near_support)")

        return result

