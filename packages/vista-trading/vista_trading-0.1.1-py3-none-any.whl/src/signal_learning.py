"""
Signal Learning System - Learn from Discord Alerts & Charts

Records every signal/alert sent to Discord and tracks outcomes to improve future signals.

Key metrics tracked:
- Signal accuracy (did price move in predicted direction?)
- S/R level reliability (did levels hold or break?)
- Trendline quality (did trendlines predict direction?)
- DeepSeek recommendation accuracy

This creates a feedback loop:
1. Signal sent to Discord → recorded with full context
2. Periodic outcome check (1h, 4h, 24h after)
3. Feed outcomes to TradeAnalyzer and ML predictor
4. Adjust future signal thresholds based on what worked
"""

import asyncio
import json
import logging
from dataclasses import dataclass, asdict, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any
from enum import Enum

logger = logging.getLogger(__name__)

# Storage paths
LEARNING_DIR = Path("data/signal_learning")
SIGNALS_FILE = LEARNING_DIR / "signals.json"
OUTCOMES_FILE = LEARNING_DIR / "outcomes.json"
STATS_FILE = LEARNING_DIR / "stats.json"


class SignalType(Enum):
    CHART_5M = "chart_5m"
    CHART_DAILY = "chart_daily"
    BREAKOUT = "breakout"
    SR_TOUCH = "sr_touch"
    VOLUME_SPIKE = "volume_spike"
    WHALE_ALERT = "whale_alert"
    TRADE_SIGNAL = "trade_signal"


@dataclass
class RecordedSignal:
    """A signal/alert sent to Discord with full context."""
    signal_id: str
    signal_type: str
    symbol: str
    timestamp: str
    price_at_signal: float
    
    # Signal details
    direction: str  # "bullish", "bearish", "neutral"
    confidence: float  # 0.0 to 1.0
    
    # Context at time of signal
    support_levels: List[float] = field(default_factory=list)
    resistance_levels: List[float] = field(default_factory=list)
    asc_support_price: Optional[float] = None
    desc_resistance_price: Optional[float] = None
    trendline_signal: str = "neutral"
    
    # DeepSeek recommendation (if any)
    deepseek_bias: Optional[str] = None  # "LONG", "SHORT", "NEUTRAL"
    deepseek_entry: Optional[str] = None
    deepseek_stop: Optional[str] = None
    deepseek_target: Optional[str] = None
    
    # Outcome tracking
    outcome_checked: bool = False
    price_1h: Optional[float] = None
    price_4h: Optional[float] = None
    price_24h: Optional[float] = None
    outcome_direction: Optional[str] = None  # "correct", "incorrect", "neutral"
    outcome_pct_1h: Optional[float] = None
    outcome_pct_4h: Optional[float] = None
    outcome_pct_24h: Optional[float] = None
    
    def to_dict(self) -> dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: dict) -> 'RecordedSignal':
        return cls(**data)


class SignalLearningStore:
    """Persists signals and outcomes for learning."""
    
    def __init__(self):
        LEARNING_DIR.mkdir(parents=True, exist_ok=True)
        self.signals: List[RecordedSignal] = self._load_signals()
        self.stats: Dict[str, Any] = self._load_json(STATS_FILE) or self._init_stats()
        
        # Pending outcome checks
        self.pending_checks: Dict[str, datetime] = {}  # signal_id -> next_check_time
        
        logger.info(f"SignalLearningStore loaded {len(self.signals)} signals")
    
    def _load_signals(self) -> List[RecordedSignal]:
        """Load signals from disk."""
        try:
            if SIGNALS_FILE.exists():
                with open(SIGNALS_FILE, 'r') as f:
                    data = json.load(f)
                    return [RecordedSignal.from_dict(s) for s in data]
        except Exception as e:
            logger.error(f"Failed to load signals: {e}")
        return []
    
    def _load_json(self, path: Path) -> Optional[Dict]:
        try:
            if path.exists():
                with open(path, 'r') as f:
                    return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load {path}: {e}")
        return None
    
    def _save_signals(self):
        """Save signals to disk."""
        try:
            with open(SIGNALS_FILE, 'w') as f:
                json.dump([s.to_dict() for s in self.signals], f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save signals: {e}")
    
    def _save_stats(self):
        """Save stats to disk."""
        try:
            with open(STATS_FILE, 'w') as f:
                json.dump(self.stats, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save stats: {e}")
    
    def _init_stats(self) -> Dict[str, Any]:
        """Initialize stats structure."""
        return {
            "total_signals": 0,
            "signals_by_type": {},
            "accuracy_by_type": {},
            "accuracy_by_symbol": {},
            "deepseek_accuracy": {"correct": 0, "incorrect": 0, "total": 0},
            "sr_reliability": {"held": 0, "broke": 0, "total": 0},
            "trendline_accuracy": {"correct": 0, "incorrect": 0, "total": 0},
            "last_updated": None
        }

    def record_signal(
        self,
        signal_type: SignalType,
        symbol: str,
        price: float,
        direction: str,
        confidence: float = 0.5,
        support_levels: List[float] = None,
        resistance_levels: List[float] = None,
        asc_support: Optional[float] = None,
        desc_resistance: Optional[float] = None,
        trendline_signal: str = "neutral",
        deepseek_bias: Optional[str] = None,
        deepseek_entry: Optional[str] = None,
        deepseek_stop: Optional[str] = None,
        deepseek_target: Optional[str] = None,
    ) -> RecordedSignal:
        """Record a signal sent to Discord for outcome tracking."""

        signal_id = f"{symbol}_{signal_type.value}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"

        signal = RecordedSignal(
            signal_id=signal_id,
            signal_type=signal_type.value,
            symbol=symbol,
            timestamp=datetime.utcnow().isoformat(),
            price_at_signal=price,
            direction=direction,
            confidence=confidence,
            support_levels=support_levels or [],
            resistance_levels=resistance_levels or [],
            asc_support_price=asc_support,
            desc_resistance_price=desc_resistance,
            trendline_signal=trendline_signal,
            deepseek_bias=deepseek_bias,
            deepseek_entry=deepseek_entry,
            deepseek_stop=deepseek_stop,
            deepseek_target=deepseek_target,
        )

        self.signals.append(signal)
        self._save_signals()

        # Schedule outcome checks
        now = datetime.utcnow()
        self.pending_checks[signal_id] = now + timedelta(hours=1)

        # Update stats
        self.stats["total_signals"] += 1
        self.stats["signals_by_type"][signal_type.value] = \
            self.stats["signals_by_type"].get(signal_type.value, 0) + 1
        self._save_stats()

        logger.info(f"📝 Recorded signal {signal_id}: {direction} @ ${price:,.2f}")
        return signal

    def get_pending_outcome_checks(self) -> List[RecordedSignal]:
        """Get signals that need outcome checking."""
        now = datetime.utcnow()
        pending = []

        for signal in self.signals:
            if signal.outcome_checked:
                continue

            signal_time = datetime.fromisoformat(signal.timestamp)
            # Check if at least 1h has passed
            if now - signal_time >= timedelta(hours=1):
                pending.append(signal)

        return pending

    def update_outcome(
        self,
        signal_id: str,
        current_price: float,
        hours_elapsed: float
    ) -> bool:
        """Update signal with price outcome.

        Returns True if all outcome checks are complete (24h passed).
        """
        signal = next((s for s in self.signals if s.signal_id == signal_id), None)
        if not signal:
            return False

        price_at_signal = signal.price_at_signal
        pct_change = ((current_price - price_at_signal) / price_at_signal) * 100

        # Update based on hours elapsed
        if hours_elapsed >= 1 and signal.price_1h is None:
            signal.price_1h = current_price
            signal.outcome_pct_1h = pct_change
            logger.info(f"📊 {signal_id} 1h outcome: {pct_change:+.2f}%")

        if hours_elapsed >= 4 and signal.price_4h is None:
            signal.price_4h = current_price
            signal.outcome_pct_4h = pct_change
            logger.info(f"📊 {signal_id} 4h outcome: {pct_change:+.2f}%")

        if hours_elapsed >= 24 and signal.price_24h is None:
            signal.price_24h = current_price
            signal.outcome_pct_24h = pct_change

            # Determine if prediction was correct
            self._evaluate_outcome(signal)
            signal.outcome_checked = True
            logger.info(f"📊 {signal_id} 24h FINAL: {pct_change:+.2f}% - {signal.outcome_direction}")

        self._save_signals()
        return signal.outcome_checked

    def _evaluate_outcome(self, signal: RecordedSignal):
        """Evaluate if the signal's direction was correct."""
        # Use 4h outcome as primary measure
        pct = signal.outcome_pct_4h or signal.outcome_pct_24h or 0

        if signal.direction == "bullish":
            if pct > 0.5:
                signal.outcome_direction = "correct"
            elif pct < -0.5:
                signal.outcome_direction = "incorrect"
            else:
                signal.outcome_direction = "neutral"
        elif signal.direction == "bearish":
            if pct < -0.5:
                signal.outcome_direction = "correct"
            elif pct > 0.5:
                signal.outcome_direction = "incorrect"
            else:
                signal.outcome_direction = "neutral"
        else:
            signal.outcome_direction = "neutral"

        # Update accuracy stats
        self._update_accuracy_stats(signal)

    def _update_accuracy_stats(self, signal: RecordedSignal):
        """Update accuracy statistics after outcome evaluation."""
        sig_type = signal.signal_type
        symbol = signal.symbol
        outcome = signal.outcome_direction

        # By type
        if sig_type not in self.stats["accuracy_by_type"]:
            self.stats["accuracy_by_type"][sig_type] = {"correct": 0, "incorrect": 0, "neutral": 0}
        self.stats["accuracy_by_type"][sig_type][outcome] += 1

        # By symbol
        if symbol not in self.stats["accuracy_by_symbol"]:
            self.stats["accuracy_by_symbol"][symbol] = {"correct": 0, "incorrect": 0, "neutral": 0}
        self.stats["accuracy_by_symbol"][symbol][outcome] += 1

        # DeepSeek accuracy
        if signal.deepseek_bias and signal.deepseek_bias != "NEUTRAL":
            self.stats["deepseek_accuracy"]["total"] += 1
            if outcome == "correct":
                self.stats["deepseek_accuracy"]["correct"] += 1
            elif outcome == "incorrect":
                self.stats["deepseek_accuracy"]["incorrect"] += 1

        # Trendline accuracy
        if signal.trendline_signal != "neutral":
            self.stats["trendline_accuracy"]["total"] += 1
            if outcome == "correct":
                self.stats["trendline_accuracy"]["correct"] += 1
            elif outcome == "incorrect":
                self.stats["trendline_accuracy"]["incorrect"] += 1

        self.stats["last_updated"] = datetime.utcnow().isoformat()
        self._save_stats()

    def get_learning_insights(self) -> Dict[str, Any]:
        """Get insights from accumulated signal outcomes."""
        stats = self.stats
        insights = {
            "total_signals_tracked": stats["total_signals"],
            "signal_types": {},
            "symbol_accuracy": {},
            "deepseek_performance": {},
            "trendline_performance": {},
            "recommendations": []
        }

        # Calculate accuracy by signal type
        for sig_type, counts in stats.get("accuracy_by_type", {}).items():
            total = counts.get("correct", 0) + counts.get("incorrect", 0) + counts.get("neutral", 0)
            if total > 0:
                accuracy = counts.get("correct", 0) / max(1, counts["correct"] + counts["incorrect"])
                insights["signal_types"][sig_type] = {
                    "accuracy": round(accuracy * 100, 1),
                    "total": total,
                    "correct": counts.get("correct", 0),
                    "incorrect": counts.get("incorrect", 0)
                }

        # Calculate accuracy by symbol
        for symbol, counts in stats.get("accuracy_by_symbol", {}).items():
            total = counts.get("correct", 0) + counts.get("incorrect", 0)
            if total > 0:
                accuracy = counts.get("correct", 0) / total
                insights["symbol_accuracy"][symbol] = {
                    "accuracy": round(accuracy * 100, 1),
                    "total": total
                }

        # DeepSeek performance
        ds = stats.get("deepseek_accuracy", {})
        ds_total = ds.get("correct", 0) + ds.get("incorrect", 0)
        if ds_total > 0:
            insights["deepseek_performance"] = {
                "accuracy": round(ds.get("correct", 0) / ds_total * 100, 1),
                "total_predictions": ds.get("total", 0),
                "correct": ds.get("correct", 0),
                "incorrect": ds.get("incorrect", 0)
            }

        # Trendline performance
        tl = stats.get("trendline_accuracy", {})
        tl_total = tl.get("correct", 0) + tl.get("incorrect", 0)
        if tl_total > 0:
            insights["trendline_performance"] = {
                "accuracy": round(tl.get("correct", 0) / tl_total * 100, 1),
                "total": tl.get("total", 0)
            }

        # Generate recommendations
        if insights.get("deepseek_performance", {}).get("accuracy", 50) < 45:
            insights["recommendations"].append("⚠️ DeepSeek accuracy below 45% - consider reducing confidence weight")
        if insights.get("trendline_performance", {}).get("accuracy", 50) < 45:
            insights["recommendations"].append("⚠️ Trendline signals underperforming - review detection params")

        # Check which symbols perform best
        best_symbol = max(insights.get("symbol_accuracy", {}).items(),
                         key=lambda x: x[1]["accuracy"], default=(None, {"accuracy": 0}))
        if best_symbol[0] and best_symbol[1]["accuracy"] > 60:
            insights["recommendations"].append(f"✅ {best_symbol[0]} has highest accuracy ({best_symbol[1]['accuracy']:.0f}%)")

        return insights

    def get_training_data_for_ml(self) -> List[Dict]:
        """Export signals with outcomes for ML training.

        Returns data compatible with the TradePredictor.
        """
        training_data = []

        for signal in self.signals:
            if not signal.outcome_checked:
                continue

            # Create feature dict for ML
            data = {
                "symbol": signal.symbol,
                "signal_type": signal.signal_type,
                "direction": signal.direction,
                "confidence": signal.confidence,
                "trendline_signal": signal.trendline_signal,
                "deepseek_bias": signal.deepseek_bias,
                "has_support_nearby": bool(signal.asc_support_price),
                "has_resistance_nearby": bool(signal.desc_resistance_price),
                # Outcome (target variable)
                "outcome": 1 if signal.outcome_direction == "correct" else 0,
                "outcome_pct_4h": signal.outcome_pct_4h or 0,
                "outcome_pct_24h": signal.outcome_pct_24h or 0,
            }
            training_data.append(data)

        return training_data


class SignalLearner:
    """Main class for signal learning - integrates with Discord notifier."""

    def __init__(self, hl_client=None):
        self.store = SignalLearningStore()
        self.hl_client = hl_client
        self._check_task: Optional[asyncio.Task] = None

    async def start_outcome_tracking(self):
        """Start background task to check signal outcomes."""
        if self._check_task is None or self._check_task.done():
            self._check_task = asyncio.create_task(self._outcome_check_loop())
            logger.info("🎓 Signal learning outcome tracking started")

    async def stop_outcome_tracking(self):
        """Stop the outcome tracking task."""
        if self._check_task and not self._check_task.done():
            self._check_task.cancel()
            try:
                await self._check_task
            except asyncio.CancelledError:
                pass

    async def _outcome_check_loop(self):
        """Periodically check outcomes for pending signals."""
        while True:
            try:
                await asyncio.sleep(300)  # Check every 5 minutes

                if not self.hl_client:
                    continue

                pending = self.store.get_pending_outcome_checks()
                if not pending:
                    continue

                logger.info(f"🔍 Checking outcomes for {len(pending)} signals...")

                for signal in pending:
                    try:
                        # Get current price
                        price = self.hl_client.get_price(signal.symbol)
                        if not price:
                            continue

                        # Calculate hours elapsed
                        signal_time = datetime.fromisoformat(signal.timestamp)
                        hours_elapsed = (datetime.utcnow() - signal_time).total_seconds() / 3600

                        # Update outcome
                        self.store.update_outcome(signal.signal_id, price, hours_elapsed)

                    except Exception as e:
                        logger.error(f"Error checking outcome for {signal.signal_id}: {e}")

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Outcome check loop error: {e}")
                await asyncio.sleep(60)

    def record_chart_signal(
        self,
        symbol: str,
        interval: str,
        price: float,
        direction: str,
        confidence: float,
        support_levels: List[float] = None,
        resistance_levels: List[float] = None,
        asc_support: Optional[float] = None,
        desc_resistance: Optional[float] = None,
        trendline_signal: str = "neutral",
        deepseek_bias: Optional[str] = None,
        deepseek_entry: Optional[str] = None,
        deepseek_stop: Optional[str] = None,
        deepseek_target: Optional[str] = None,
    ) -> RecordedSignal:
        """Record a chart signal (from 5m or daily charts)."""
        signal_type = SignalType.CHART_5M if "5" in interval or "m" in interval.lower() else SignalType.CHART_DAILY

        return self.store.record_signal(
            signal_type=signal_type,
            symbol=symbol,
            price=price,
            direction=direction,
            confidence=confidence,
            support_levels=support_levels,
            resistance_levels=resistance_levels,
            asc_support=asc_support,
            desc_resistance=desc_resistance,
            trendline_signal=trendline_signal,
            deepseek_bias=deepseek_bias,
            deepseek_entry=deepseek_entry,
            deepseek_stop=deepseek_stop,
            deepseek_target=deepseek_target,
        )

    def record_trade_signal(
        self,
        symbol: str,
        side: str,
        price: float,
        confidence: float,
        **kwargs
    ) -> RecordedSignal:
        """Record a trade signal."""
        direction = "bullish" if side.lower() == "long" else "bearish"

        return self.store.record_signal(
            signal_type=SignalType.TRADE_SIGNAL,
            symbol=symbol,
            price=price,
            direction=direction,
            confidence=confidence,
            **kwargs
        )

    def get_insights(self) -> Dict[str, Any]:
        """Get learning insights from signal history."""
        return self.store.get_learning_insights()

    def get_training_data(self) -> List[Dict]:
        """Get training data for ML model."""
        return self.store.get_training_data_for_ml()

    def get_confidence_adjustment(self, symbol: str, direction: str,
                                   has_deepseek: bool = False,
                                   has_trendline: bool = False) -> float:
        """Get confidence adjustment based on historical performance.

        Returns a multiplier (0.5 to 1.5) to adjust signal confidence.
        """
        insights = self.store.get_learning_insights()
        adjustments = []

        # Symbol-based adjustment
        symbol_acc = insights.get("symbol_accuracy", {}).get(symbol, {})
        if symbol_acc.get("total", 0) >= 5:
            accuracy = symbol_acc["accuracy"] / 100
            # Above 60% = boost, below 40% = reduce
            if accuracy > 0.6:
                adjustments.append(1.0 + (accuracy - 0.6))  # Up to 1.4
            elif accuracy < 0.4:
                adjustments.append(0.6 + accuracy)  # Down to 0.6

        # DeepSeek adjustment
        if has_deepseek:
            ds = insights.get("deepseek_performance", {})
            if ds.get("total_predictions", 0) >= 10:
                ds_acc = ds.get("accuracy", 50) / 100
                if ds_acc > 0.55:
                    adjustments.append(1.0 + (ds_acc - 0.55) * 2)  # Boost if accurate
                elif ds_acc < 0.45:
                    adjustments.append(0.8)  # Reduce if inaccurate

        # Trendline adjustment
        if has_trendline:
            tl = insights.get("trendline_performance", {})
            if tl.get("total", 0) >= 10:
                tl_acc = tl.get("accuracy", 50) / 100
                if tl_acc > 0.55:
                    adjustments.append(1.0 + (tl_acc - 0.55))
                elif tl_acc < 0.45:
                    adjustments.append(0.85)

        if not adjustments:
            return 1.0  # No adjustment

        # Average all adjustments
        return sum(adjustments) / len(adjustments)

    def should_trust_deepseek(self) -> bool:
        """Check if DeepSeek recommendations should be trusted based on history."""
        insights = self.store.get_learning_insights()
        ds = insights.get("deepseek_performance", {})

        if ds.get("total_predictions", 0) < 10:
            return True  # Not enough data, trust by default

        return ds.get("accuracy", 50) >= 45  # Trust if at least 45% accurate

    def should_trust_trendlines(self) -> bool:
        """Check if trendline signals should be trusted based on history."""
        insights = self.store.get_learning_insights()
        tl = insights.get("trendline_performance", {})

        if tl.get("total", 0) < 10:
            return True  # Not enough data, trust by default

        return tl.get("accuracy", 50) >= 45

