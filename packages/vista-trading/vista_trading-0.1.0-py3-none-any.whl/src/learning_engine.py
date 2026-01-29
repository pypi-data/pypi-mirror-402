"""
Complete Learning Engine for Trading Bot.

Implements the full learning loop:
1. Chart Prediction Validator - Track if predictions were correct
2. Entry Condition Capture - Save market state on every trade
3. Whale Outcome Tracker - Correlate whale activity with price moves
4. Pattern Analyzer - Find winning condition combinations
5. Confidence Scorer - Score setups based on historical similarity

Usage:
    from src.learning_engine import LearningEngine
    engine = LearningEngine(hl_client)
    
    # Validate predictions
    await engine.validate_chart_predictions()
    
    # Get confidence for a setup
    confidence = engine.get_setup_confidence(symbol, direction, conditions)
    
    # Get best patterns
    patterns = engine.get_winning_patterns(symbol)
"""

import logging
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from collections import defaultdict

logger = logging.getLogger(__name__)


@dataclass
class MarketConditions:
    """Snapshot of market conditions at trade entry."""
    symbol: str
    timestamp: str
    price: float
    # Momentum
    rsi: float = 0.0
    macd: float = 0.0
    macd_signal: float = 0.0
    macd_hist: float = 0.0
    # Trend
    trend: str = "NEUTRAL"  # BULLISH, BEARISH, NEUTRAL
    adx: float = 0.0
    ema_9: float = 0.0
    ema_21: float = 0.0
    ema_50: float = 0.0
    price_vs_ema: str = "NEUTRAL"  # ABOVE_ALL, BELOW_ALL, MIXED
    # Volatility
    atr: float = 0.0
    atr_pct: float = 0.0
    bb_position: str = "MIDDLE"  # UPPER, MIDDLE, LOWER
    # Volume
    volume_ratio: float = 1.0
    # Levels
    distance_to_support_pct: float = 0.0
    distance_to_resistance_pct: float = 0.0
    at_support: bool = False
    at_resistance: bool = False
    # Patterns
    chart_signal: str = ""
    chart_direction: str = ""
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    def get_condition_key(self) -> str:
        """Generate a key for pattern matching."""
        rsi_zone = "oversold" if self.rsi < 30 else "overbought" if self.rsi > 70 else "neutral"
        return f"{self.trend}_{rsi_zone}_{self.bb_position}"


class LearningEngine:
    """Central learning engine that tracks and learns from all trading data."""
    
    def __init__(self, hl_client=None):
        self.hl = hl_client
        self._db = None
        
    @property
    def db(self):
        if self._db is None:
            from src.database import get_db
            self._db = get_db()
        return self._db
    
    # =========================================================================
    # 1. CHART PREDICTION VALIDATOR
    # =========================================================================
    
    async def validate_chart_predictions(self, hours_after: int = 1) -> Dict[str, Any]:
        """Validate chart predictions against actual price moves.
        
        Checks predictions made X hours ago and compares to current price.
        Updates chart records with validation results.
        """
        if not self.hl:
            return {"error": "No HL client"}
        
        results = {"validated": 0, "correct": 0, "incorrect": 0, "by_signal": {}}
        cutoff_start = (datetime.utcnow() - timedelta(hours=hours_after + 1)).isoformat()
        cutoff_end = (datetime.utcnow() - timedelta(hours=hours_after)).isoformat()
        
        try:
            with self.db._get_conn() as conn:
                # Ensure validation columns exist
                self._ensure_chart_validation_columns(conn)
                
                # Get unvalidated predictions from X hours ago
                charts = conn.execute("""
                    SELECT id, symbol, price, direction, signal, timestamp
                    FROM charts 
                    WHERE timestamp BETWEEN ? AND ?
                    AND validated IS NULL
                    AND direction IS NOT NULL
                """, (cutoff_start, cutoff_end)).fetchall()
                
                for chart in charts:
                    symbol = chart["symbol"]
                    predicted_direction = chart["direction"].lower()
                    entry_price = chart["price"]
                    signal = chart["signal"] or "unknown"

                    if not entry_price or entry_price == 0:
                        continue

                    # Get current price
                    try:
                        current_price = self.hl.get_price(symbol)
                        if not current_price:
                            continue
                    except:
                        continue

                    # Determine actual direction
                    price_change_pct = (current_price - entry_price) / entry_price * 100
                    actual_direction = "bullish" if price_change_pct > 0.1 else "bearish" if price_change_pct < -0.1 else "neutral"

                    # Check if prediction was correct
                    correct = (predicted_direction == actual_direction) or \
                              (predicted_direction == "bullish" and price_change_pct > 0) or \
                              (predicted_direction == "bearish" and price_change_pct < 0)

                    # Update chart record
                    conn.execute("""
                        UPDATE charts SET
                            validated = 1,
                            actual_direction = ?,
                            price_after = ?,
                            price_change_pct = ?,
                            prediction_correct = ?
                        WHERE id = ?
                    """, (actual_direction, current_price, price_change_pct, 1 if correct else 0, chart["id"]))

                    results["validated"] += 1
                    if correct:
                        results["correct"] += 1
                    else:
                        results["incorrect"] += 1

                    # Track by signal type
                    if signal not in results["by_signal"]:
                        results["by_signal"][signal] = {"correct": 0, "total": 0}
                    results["by_signal"][signal]["total"] += 1
                    if correct:
                        results["by_signal"][signal]["correct"] += 1

                conn.commit()

        except Exception as e:
            logger.error(f"Chart validation error: {e}")
            results["error"] = str(e)

        if results["validated"] > 0:
            results["accuracy"] = results["correct"] / results["validated"] * 100
            logger.info(f"📊 Validated {results['validated']} charts: {results['accuracy']:.1f}% accurate")

        return results

    def _ensure_chart_validation_columns(self, conn):
        """Add validation columns to charts table if they don't exist."""
        try:
            conn.execute("ALTER TABLE charts ADD COLUMN validated INTEGER DEFAULT NULL")
        except:
            pass
        try:
            conn.execute("ALTER TABLE charts ADD COLUMN actual_direction TEXT")
        except:
            pass
        try:
            conn.execute("ALTER TABLE charts ADD COLUMN price_after REAL")
        except:
            pass
        try:
            conn.execute("ALTER TABLE charts ADD COLUMN price_change_pct REAL")
        except:
            pass
        try:
            conn.execute("ALTER TABLE charts ADD COLUMN prediction_correct INTEGER")
        except:
            pass

    def get_chart_prediction_stats(self, symbol: str = None, signal_type: str = None) -> Dict:
        """Get chart prediction accuracy statistics."""
        with self.db._get_conn() as conn:
            # Ensure columns exist first
            self._ensure_chart_validation_columns(conn)

            query = "SELECT * FROM charts WHERE validated = 1"
            params = []

            if symbol:
                query += " AND symbol = ?"
                params.append(symbol)
            if signal_type:
                query += " AND signal = ?"
                params.append(signal_type)

            rows = conn.execute(query, params).fetchall()

            if not rows:
                return {"total": 0, "accuracy": 0}

            correct = sum(1 for r in rows if r["prediction_correct"])

            # Group by signal type
            by_signal = defaultdict(lambda: {"correct": 0, "total": 0})
            for r in rows:
                sig = r["signal"] or "unknown"
                by_signal[sig]["total"] += 1
                if r["prediction_correct"]:
                    by_signal[sig]["correct"] += 1

            # Calculate accuracy per signal
            signal_accuracy = {}
            for sig, stats in by_signal.items():
                if stats["total"] >= 5:  # Minimum samples
                    signal_accuracy[sig] = {
                        "accuracy": stats["correct"] / stats["total"] * 100,
                        "total": stats["total"]
                    }

            return {
                "total": len(rows),
                "correct": correct,
                "accuracy": correct / len(rows) * 100,
                "by_signal": signal_accuracy
            }

    # =========================================================================
    # 2. ENTRY CONDITION CAPTURE
    # =========================================================================

    def capture_entry_conditions(self, symbol: str, market_data: Dict[str, Any]) -> MarketConditions:
        """Capture full market conditions at trade entry.

        Args:
            symbol: Trading symbol
            market_data: Full market data dict from _gather_market_data

        Returns:
            MarketConditions dataclass with all relevant conditions
        """
        price = market_data.get("price", 0)

        # RSI zone
        rsi = market_data.get("rsi", 50)

        # Trend
        trend = market_data.get("trend", "NEUTRAL")
        adx = market_data.get("adx", 0)

        # EMAs
        ema_9 = market_data.get("ema_9", price)
        ema_21 = market_data.get("ema_21", price)
        ema_50 = market_data.get("ema_50", price)

        # Determine price vs EMA position
        above_9 = price > ema_9 if ema_9 else True
        above_21 = price > ema_21 if ema_21 else True
        above_50 = price > ema_50 if ema_50 else True

        if above_9 and above_21 and above_50:
            price_vs_ema = "ABOVE_ALL"
        elif not above_9 and not above_21 and not above_50:
            price_vs_ema = "BELOW_ALL"
        else:
            price_vs_ema = "MIXED"

        # Bollinger Band position
        bb_upper = market_data.get("bb_upper", price * 1.02)
        bb_lower = market_data.get("bb_lower", price * 0.98)
        bb_mid = (bb_upper + bb_lower) / 2 if bb_upper and bb_lower else price

        if price >= bb_upper * 0.99:
            bb_position = "UPPER"
        elif price <= bb_lower * 1.01:
            bb_position = "LOWER"
        else:
            bb_position = "MIDDLE"

        # Support/Resistance
        support = market_data.get("support", price * 0.95)
        resistance = market_data.get("resistance", price * 1.05)

        dist_to_support = (price - support) / price * 100 if support else 5
        dist_to_resistance = (resistance - price) / price * 100 if resistance else 5

        conditions = MarketConditions(
            symbol=symbol,
            timestamp=datetime.utcnow().isoformat(),
            price=price,
            rsi=rsi,
            macd=market_data.get("macd", 0),
            macd_signal=market_data.get("macd_signal", 0),
            macd_hist=market_data.get("macd_hist", 0),
            trend=trend,
            adx=adx,
            ema_9=ema_9,
            ema_21=ema_21,
            ema_50=ema_50,
            price_vs_ema=price_vs_ema,
            atr=market_data.get("atr", 0),
            atr_pct=market_data.get("atr_pct", 0),
            bb_position=bb_position,
            volume_ratio=market_data.get("vol_ratio", 1.0),
            distance_to_support_pct=dist_to_support,
            distance_to_resistance_pct=dist_to_resistance,
            at_support=dist_to_support < 0.5,
            at_resistance=dist_to_resistance < 0.5,
            chart_signal=market_data.get("signal", ""),
            chart_direction=market_data.get("direction", "")
        )

        return conditions

    def save_trade_with_conditions(self, trade_id: str, symbol: str, side: str,
                                    entry_price: float, conditions: MarketConditions) -> None:
        """Save a trade with full entry conditions for learning."""
        try:
            # Update the trade record with conditions
            with self.db._get_conn() as conn:
                conn.execute("""
                    UPDATE completed_trades
                    SET entry_conditions = ?
                    WHERE trade_id = ? OR (symbol = ? AND entry_price = ? AND side = ?)
                """, (json.dumps(conditions.to_dict()), trade_id, symbol, entry_price, side))

                if conn.total_changes == 0:
                    # Try inserting if update didn't match
                    logger.debug(f"Trade {trade_id} not found for condition update")
                else:
                    logger.info(f"📊 Saved entry conditions for {symbol} {side}: {conditions.get_condition_key()}")
        except Exception as e:
            logger.error(f"Failed to save trade conditions: {e}")

    # =========================================================================
    # 3. WHALE OUTCOME TRACKER
    # =========================================================================

    async def validate_whale_events(self, hours_after: int = 1) -> Dict[str, Any]:
        """Validate whale events - did following the whale result in profit?

        Checks whale events from X hours ago and compares price then vs now.
        """
        if not self.hl:
            return {"error": "No HL client"}

        results = {"validated": 0, "profitable": 0, "unprofitable": 0, "by_side": {}}
        cutoff_start = (datetime.utcnow() - timedelta(hours=hours_after + 1)).isoformat()
        cutoff_end = (datetime.utcnow() - timedelta(hours=hours_after)).isoformat()

        try:
            with self.db._get_conn() as conn:
                # Ensure validation columns exist
                self._ensure_whale_validation_columns(conn)

                # Get unvalidated whale events from X hours ago
                whales = conn.execute("""
                    SELECT id, symbol, side, entry_price, timestamp
                    FROM whale_events
                    WHERE timestamp BETWEEN ? AND ?
                    AND validated IS NULL
                    AND entry_price > 0
                """, (cutoff_start, cutoff_end)).fetchall()

                for whale in whales:
                    symbol = whale["symbol"]
                    whale_side = whale["side"].lower() if whale["side"] else "unknown"
                    entry_price = whale["entry_price"]

                    if not entry_price or entry_price == 0:
                        continue

                    # Get current price
                    try:
                        current_price = self.hl.get_price(symbol)
                        if not current_price:
                            continue
                    except:
                        continue

                    # Calculate price change
                    price_change_pct = (current_price - entry_price) / entry_price * 100

                    # Was following the whale profitable?
                    # If whale bought (long), profit if price went up
                    # If whale sold (short), profit if price went down
                    if whale_side in ["long", "buy"]:
                        profitable = price_change_pct > 0
                    elif whale_side in ["short", "sell"]:
                        profitable = price_change_pct < 0
                    else:
                        profitable = False

                    # Update whale record
                    conn.execute("""
                        UPDATE whale_events SET
                            validated = 1,
                            price_after = ?,
                            price_change_pct = ?,
                            profitable_to_follow = ?
                        WHERE id = ?
                    """, (current_price, price_change_pct, 1 if profitable else 0, whale["id"]))

                    results["validated"] += 1
                    if profitable:
                        results["profitable"] += 1
                    else:
                        results["unprofitable"] += 1

                    # Track by side
                    if whale_side not in results["by_side"]:
                        results["by_side"][whale_side] = {"profitable": 0, "total": 0, "avg_change": 0}
                    results["by_side"][whale_side]["total"] += 1
                    if profitable:
                        results["by_side"][whale_side]["profitable"] += 1

                conn.commit()

        except Exception as e:
            logger.error(f"Whale validation error: {e}")
            results["error"] = str(e)

        if results["validated"] > 0:
            results["follow_rate"] = results["profitable"] / results["validated"] * 100
            logger.info(f"🐋 Validated {results['validated']} whale events: {results['follow_rate']:.1f}% profitable to follow")

        return results

    def _ensure_whale_validation_columns(self, conn):
        """Add validation columns to whale_events table if they don't exist."""
        for col, dtype in [("validated", "INTEGER"), ("price_after", "REAL"),
                           ("price_change_pct", "REAL"), ("profitable_to_follow", "INTEGER")]:
            try:
                conn.execute(f"ALTER TABLE whale_events ADD COLUMN {col} {dtype}")
            except:
                pass

    def get_whale_follow_stats(self, symbol: str = None) -> Dict:
        """Get statistics on following whale trades."""
        query = "SELECT * FROM whale_events WHERE validated = 1"
        params = []

        if symbol:
            query += " AND symbol = ?"
            params.append(symbol)

        with self.db._get_conn() as conn:
            # Ensure columns exist first
            self._ensure_whale_validation_columns(conn)

            try:
                rows = conn.execute(query, params).fetchall()
            except:
                return {"total": 0, "follow_rate": 0}

            if not rows:
                return {"total": 0, "follow_rate": 0}

            profitable = sum(1 for r in rows if r.get("profitable_to_follow"))
            avg_change = sum(r.get("price_change_pct", 0) or 0 for r in rows) / len(rows)

            # Group by side
            by_side = defaultdict(lambda: {"profitable": 0, "total": 0, "total_change": 0})
            for r in rows:
                side = (r.get("side") or "unknown").lower()
                by_side[side]["total"] += 1
                by_side[side]["total_change"] += r.get("price_change_pct", 0) or 0
                if r.get("profitable_to_follow"):
                    by_side[side]["profitable"] += 1

            side_stats = {}
            for side, stats in by_side.items():
                if stats["total"] >= 5:
                    side_stats[side] = {
                        "follow_rate": stats["profitable"] / stats["total"] * 100,
                        "avg_change": stats["total_change"] / stats["total"],
                        "total": stats["total"]
                    }

            return {
                "total": len(rows),
                "profitable": profitable,
                "follow_rate": profitable / len(rows) * 100,
                "avg_price_change": avg_change,
                "by_side": side_stats
            }

    # =========================================================================
    # 4. PATTERN ANALYZER
    # =========================================================================

    def analyze_winning_patterns(self, symbol: str = None, min_trades: int = 5) -> Dict[str, Any]:
        """Analyze trades to find winning condition patterns.

        Groups trades by entry conditions and calculates win rate per pattern.
        Returns patterns sorted by profitability.
        """
        trades = self.db.get_completed_trades(symbol=symbol, limit=500)

        if not trades:
            return {"patterns": [], "message": "No trades to analyze"}

        # Group by condition patterns
        patterns = defaultdict(lambda: {"wins": 0, "losses": 0, "total_pnl": 0, "trades": []})

        for trade in trades:
            conditions = trade.get("entry_conditions", {})
            if isinstance(conditions, str):
                try:
                    conditions = json.loads(conditions)
                except:
                    conditions = {}

            # Skip trades without proper conditions
            if not conditions or conditions.get("source") == "hyperliquid_sync":
                continue

            # Build pattern key
            trend = conditions.get("trend", "NEUTRAL")
            rsi = conditions.get("rsi", 50)
            rsi_zone = "oversold" if rsi < 30 else "overbought" if rsi > 70 else "neutral"
            bb_pos = conditions.get("bb_position", "MIDDLE")
            price_vs_ema = conditions.get("price_vs_ema", "MIXED")
            side = trade.get("side", "unknown")

            pattern_key = f"{side}_{trend}_{rsi_zone}_{bb_pos}"

            pnl = trade.get("pnl_usd", 0) or 0
            patterns[pattern_key]["total_pnl"] += pnl
            patterns[pattern_key]["trades"].append(trade)

            if pnl > 0:
                patterns[pattern_key]["wins"] += 1
            else:
                patterns[pattern_key]["losses"] += 1

        # Calculate stats and filter
        result_patterns = []
        for key, stats in patterns.items():
            total = stats["wins"] + stats["losses"]
            if total < min_trades:
                continue

            win_rate = stats["wins"] / total * 100
            avg_pnl = stats["total_pnl"] / total

            result_patterns.append({
                "pattern": key,
                "win_rate": win_rate,
                "avg_pnl": avg_pnl,
                "total_trades": total,
                "wins": stats["wins"],
                "losses": stats["losses"],
                "total_pnl": stats["total_pnl"],
                "recommendation": "✅ USE" if win_rate >= 55 else "❌ AVOID" if win_rate < 45 else "⚠️ NEUTRAL"
            })

        # Sort by win rate
        result_patterns.sort(key=lambda x: x["win_rate"], reverse=True)

        return {
            "patterns": result_patterns,
            "best_patterns": [p for p in result_patterns if p["win_rate"] >= 55],
            "worst_patterns": [p for p in result_patterns if p["win_rate"] < 45],
            "total_analyzed": sum(p["total_trades"] for p in result_patterns)
        }

    def get_pattern_insights(self, symbol: str = None) -> List[str]:
        """Get human-readable pattern insights."""
        analysis = self.analyze_winning_patterns(symbol)
        insights = []

        for p in analysis.get("best_patterns", [])[:3]:
            insights.append(f"✅ {p['pattern']}: {p['win_rate']:.0f}% win rate ({p['total_trades']} trades)")

        for p in analysis.get("worst_patterns", [])[:3]:
            insights.append(f"❌ {p['pattern']}: {p['win_rate']:.0f}% win rate - AVOID")

        return insights

    # =========================================================================
    # 5. CONFIDENCE SCORER
    # =========================================================================

    def get_setup_confidence(self, symbol: str, side: str, conditions: MarketConditions) -> Dict[str, Any]:
        """Calculate confidence score for a trade setup based on historical similarity.

        Returns:
            Dict with confidence score (0-100), reasoning, and recommendation
        """
        confidence_factors = []
        total_weight = 0
        weighted_score = 0

        # 1. Pattern Win Rate (weight: 30%)
        pattern_key = f"{side}_{conditions.trend}_{self._get_rsi_zone(conditions.rsi)}_{conditions.bb_position}"
        pattern_analysis = self.analyze_winning_patterns(symbol)

        pattern_match = None
        for p in pattern_analysis.get("patterns", []):
            if p["pattern"] == pattern_key:
                pattern_match = p
                break

        if pattern_match:
            pattern_score = pattern_match["win_rate"]
            confidence_factors.append(f"Pattern '{pattern_key}': {pattern_score:.0f}% historical win rate")
            weighted_score += pattern_score * 0.30
            total_weight += 0.30

        # 2. Chart Prediction Accuracy (weight: 25%)
        chart_stats = self.get_chart_prediction_stats(symbol, conditions.chart_signal)
        if chart_stats.get("total", 0) >= 5:
            chart_score = chart_stats["accuracy"]
            confidence_factors.append(f"Chart signal '{conditions.chart_signal}': {chart_score:.0f}% accuracy")
            weighted_score += chart_score * 0.25
            total_weight += 0.25

        # 3. Whale Alignment (weight: 20%)
        whale_stats = self.get_whale_follow_stats(symbol)
        if whale_stats.get("total", 0) >= 5:
            whale_score = whale_stats["follow_rate"]
            confidence_factors.append(f"Whale follow rate: {whale_score:.0f}%")
            weighted_score += whale_score * 0.20
            total_weight += 0.20

        # 4. Technical Confluence (weight: 15%)
        tech_score = self._calculate_technical_confluence(side, conditions)
        confidence_factors.append(f"Technical confluence: {tech_score:.0f}%")
        weighted_score += tech_score * 0.15
        total_weight += 0.15

        # 5. Recent Performance (weight: 10%)
        recent_trades = self.db.get_completed_trades(symbol=symbol, limit=10)
        if recent_trades:
            recent_wins = sum(1 for t in recent_trades if (t.get("pnl_usd") or 0) > 0)
            recent_score = recent_wins / len(recent_trades) * 100
            confidence_factors.append(f"Recent {symbol} trades: {recent_wins}/{len(recent_trades)} wins")
            weighted_score += recent_score * 0.10
            total_weight += 0.10

        # Calculate final confidence
        if total_weight > 0:
            confidence = weighted_score / total_weight
        else:
            confidence = 50  # No data = neutral

        # Determine recommendation
        if confidence >= 70:
            recommendation = "STRONG_BUY" if side.lower() in ["long", "buy"] else "STRONG_SELL"
            action = "✅ HIGH CONFIDENCE - Execute with full size"
        elif confidence >= 55:
            recommendation = "BUY" if side.lower() in ["long", "buy"] else "SELL"
            action = "⚠️ MODERATE CONFIDENCE - Execute with reduced size"
        elif confidence >= 40:
            recommendation = "HOLD"
            action = "⚠️ LOW CONFIDENCE - Consider skipping"
        else:
            recommendation = "AVOID"
            action = "❌ VERY LOW CONFIDENCE - Skip this trade"

        return {
            "confidence": round(confidence, 1),
            "recommendation": recommendation,
            "action": action,
            "factors": confidence_factors,
            "pattern_match": pattern_match,
            "size_multiplier": min(1.0, max(0.25, confidence / 70))  # Scale size with confidence
        }

    def _get_rsi_zone(self, rsi: float) -> str:
        """Convert RSI to zone."""
        if rsi < 30:
            return "oversold"
        elif rsi > 70:
            return "overbought"
        return "neutral"

    def _calculate_technical_confluence(self, side: str, conditions: MarketConditions) -> float:
        """Calculate how many technical factors align with the trade direction."""
        score = 50  # Start neutral

        if side.lower() in ["long", "buy"]:
            # Bullish factors
            if conditions.trend == "BULLISH":
                score += 15
            if conditions.rsi < 40:  # Oversold
                score += 10
            if conditions.bb_position == "LOWER":
                score += 10
            if conditions.price_vs_ema == "ABOVE_ALL":
                score += 10
            if conditions.at_support:
                score += 10
            # Bearish factors (reduce score)
            if conditions.trend == "BEARISH":
                score -= 15
            if conditions.rsi > 70:
                score -= 10
            if conditions.at_resistance:
                score -= 10
        else:
            # Short trade - opposite logic
            if conditions.trend == "BEARISH":
                score += 15
            if conditions.rsi > 60:
                score += 10
            if conditions.bb_position == "UPPER":
                score += 10
            if conditions.at_resistance:
                score += 10
            if conditions.trend == "BULLISH":
                score -= 15
            if conditions.rsi < 30:
                score -= 10

        return max(0, min(100, score))

    # =========================================================================
    # UNIFIED LEARNING CONTEXT FOR AI
    # =========================================================================

    def get_full_learning_context(self, symbol: str = None) -> Dict[str, Any]:
        """Get complete learning context for AI decision making.

        Combines all learning sources into a single context dict.
        """
        context = {
            "chart_predictions": {},
            "whale_insights": {},
            "pattern_insights": [],
            "recent_performance": {},
            "recommendations": []
        }

        # Chart prediction stats
        chart_stats = self.get_chart_prediction_stats(symbol)
        if chart_stats.get("total", 0) > 0:
            context["chart_predictions"] = {
                "total_validated": chart_stats["total"],
                "overall_accuracy": f"{chart_stats['accuracy']:.1f}%",
                "by_signal": chart_stats.get("by_signal", {})
            }
            if chart_stats["accuracy"] < 50:
                context["recommendations"].append("⚠️ Chart predictions performing below 50% - use with caution")

        # Whale insights
        whale_stats = self.get_whale_follow_stats(symbol)
        if whale_stats.get("total", 0) > 0:
            context["whale_insights"] = {
                "total_validated": whale_stats["total"],
                "follow_success_rate": f"{whale_stats['follow_rate']:.1f}%",
                "avg_price_change": f"{whale_stats['avg_price_change']:.2f}%",
                "by_side": whale_stats.get("by_side", {})
            }
            if whale_stats["follow_rate"] > 55:
                context["recommendations"].append("✅ Following whales has been profitable - consider their direction")

        # Pattern insights
        context["pattern_insights"] = self.get_pattern_insights(symbol)

        # Recent performance
        recent = self.db.get_completed_trades(symbol=symbol, limit=20)
        if recent:
            wins = sum(1 for t in recent if (t.get("pnl_usd") or 0) > 0)
            total_pnl = sum(t.get("pnl_usd") or 0 for t in recent)
            context["recent_performance"] = {
                "last_20_trades": f"{wins}/20 wins ({wins/20*100:.0f}%)",
                "total_pnl": f"${total_pnl:.2f}"
            }

        return context

    # =========================================================================
    # BACKGROUND VALIDATION RUNNER
    # =========================================================================

    async def run_validation_cycle(self) -> Dict[str, Any]:
        """Run a complete validation cycle for all data sources.

        Should be called periodically (e.g., every hour) to keep learning data fresh.
        """
        results = {
            "timestamp": datetime.utcnow().isoformat(),
            "chart_validation": {},
            "whale_validation": {},
        }

        # Validate chart predictions
        try:
            results["chart_validation"] = await self.validate_chart_predictions(hours_after=1)
        except Exception as e:
            results["chart_validation"] = {"error": str(e)}

        # Validate whale events
        try:
            results["whale_validation"] = await self.validate_whale_events(hours_after=1)
        except Exception as e:
            results["whale_validation"] = {"error": str(e)}

        logger.info(f"📚 Learning validation cycle complete: "
                    f"Charts={results['chart_validation'].get('validated', 0)}, "
                    f"Whales={results['whale_validation'].get('validated', 0)}")

        return results

