"""
ML-based trade prediction using LightGBM.

This module provides:
1. Feature engineering from EntryConditions
2. Win probability prediction model
3. Continuous learning from new trades
4. Feature importance analysis
"""

import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
import json
import os

import numpy as np

try:
    import lightgbm as lgb
    LIGHTGBM_AVAILABLE = True
except ImportError:
    LIGHTGBM_AVAILABLE = False
    lgb = None

logger = logging.getLogger(__name__)


@dataclass
class PredictionResult:
    """Result of a trade prediction."""
    win_probability: float
    confidence: str  # "high", "medium", "low"
    key_factors: List[Tuple[str, float]]  # (feature_name, importance)
    recommendation: str  # "strong_take", "take", "skip", "strong_skip"

    def to_dict(self) -> dict:
        return {
            "win_probability": self.win_probability,
            "confidence": self.confidence,
            "key_factors": self.key_factors,
            "recommendation": self.recommendation
        }


class TradePredictor:
    """LightGBM-based trade win/loss predictor.

    Features:
    - Learns from historical trades with entry conditions
    - Predicts win probability for new trade setups
    - Provides feature importance for explainability
    - Continuously improves with each trade
    """

    # Feature columns extracted from EntryConditions
    FEATURE_COLS = [
        'rsi', 'bb_position', 'vwap_distance_pct', 'trend_5m_score', 'trend_15m_score',
        'atr_pct', 'hour_of_day', 'day_of_week', 'funding_rate', 'volume_ratio',
        'regime_strength', 'smc_confidence', 'orderbook_imbalance',
        'sl_distance_pct', 'tp_distance_pct', 'risk_reward_ratio',
        'signal_confidence', 'adx',
        # Encoded categoricals
        'trend_1h_bullish', 'trend_1h_bearish',
        'macd_bullish', 'macd_bearish',
        'regime_trending', 'regime_ranging', 'regime_volatile',
        'vol_regime_low', 'vol_regime_high', 'vol_regime_extreme',
        'smc_bias_bullish', 'smc_bias_bearish',
        'near_order_block', 'in_fair_value_gap',
        'side_long'  # 1 for long, 0 for short
    ]

    def __init__(self, model_path: str = "data/trade_predictor.lgb"):
        self.model_path = model_path
        self.model: Optional[lgb.Booster] = None
        self.feature_importance: Dict[str, float] = {}
        self.training_stats: Dict[str, Any] = {
            "total_trades": 0,
            "last_trained": None,
            "train_accuracy": 0.0,
            "val_accuracy": 0.0
        }

        if not LIGHTGBM_AVAILABLE:
            logger.warning("LightGBM not available. ML predictions disabled.")
            return

        # Try to load existing model
        self._load_model()

    def _load_model(self):
        """Load model from disk if exists."""
        if not LIGHTGBM_AVAILABLE:
            return

        if os.path.exists(self.model_path):
            try:
                self.model = lgb.Booster(model_file=self.model_path)
                # Load stats
                stats_path = self.model_path.replace('.lgb', '_stats.json')
                if os.path.exists(stats_path):
                    with open(stats_path, 'r') as f:
                        self.training_stats = json.load(f)
                logger.info(f"Loaded ML model with {self.training_stats['total_trades']} trades")
            except Exception as e:
                logger.error(f"Failed to load ML model: {e}")
                self.model = None

    def _save_model(self):
        """Save model to disk."""
        if not self.model:
            return

        try:
            os.makedirs(os.path.dirname(self.model_path), exist_ok=True)
            self.model.save_model(self.model_path)
            # Save stats
            stats_path = self.model_path.replace('.lgb', '_stats.json')
            with open(stats_path, 'w') as f:
                json.dump(self.training_stats, f)
            logger.info(f"Saved ML model to {self.model_path}")
        except Exception as e:
            logger.error(f"Failed to save ML model: {e}")

    def _extract_features(self, entry_conditions, side: str) -> np.ndarray:
        """Extract feature vector from EntryConditions."""
        ec = entry_conditions

        features = [
            ec.rsi if ec else 50.0,
            ec.bb_position if ec else 0.5,
            ec.vwap_distance_pct if ec else 0.0,
            ec.trend_5m_score if ec else 0,
            ec.trend_15m_score if ec else 0,
            ec.atr_pct if ec else 0.0,
            ec.hour_of_day if ec else 12,
            ec.day_of_week if ec else 0,
            ec.funding_rate if ec else 0.0,
            ec.volume_ratio if ec else 1.0,
            ec.regime_strength if ec else 0.0,
            ec.smc_confidence if ec else 0.0,
            ec.orderbook_imbalance if ec else 0.0,
            ec.sl_distance_pct if ec else 0.0,
            ec.tp_distance_pct if ec else 0.0,
            ec.risk_reward_ratio if ec else 0.0,
            ec.signal_confidence if ec else 0.5,
            ec.adx if ec else 0.0,
            # One-hot encoded categoricals
            1.0 if ec and ec.trend_1h_signal == "bullish" else 0.0,
            1.0 if ec and ec.trend_1h_signal == "bearish" else 0.0,
            1.0 if ec and ec.macd_signal == "bullish" else 0.0,
            1.0 if ec and ec.macd_signal == "bearish" else 0.0,
            1.0 if ec and "trend" in (ec.adaptive_regime or "").lower() else 0.0,
            1.0 if ec and "rang" in (ec.adaptive_regime or "").lower() else 0.0,
            1.0 if ec and "volat" in (ec.adaptive_regime or "").lower() else 0.0,
            1.0 if ec and (ec.volatility_regime or "") == "low" else 0.0,
            1.0 if ec and (ec.volatility_regime or "") == "high" else 0.0,
            1.0 if ec and (ec.volatility_regime or "") == "extreme" else 0.0,
            1.0 if ec and ec.smc_bias == "bullish" else 0.0,
            1.0 if ec and ec.smc_bias == "bearish" else 0.0,
            1.0 if ec and ec.near_order_block else 0.0,
            1.0 if ec and ec.in_fair_value_gap else 0.0,
            1.0 if side == "long" else 0.0
        ]
        return np.array(features, dtype=np.float32)

    def train(self, trades: List, min_trades: int = 30) -> Dict[str, Any]:
        """Train/retrain model on historical trades.

        Args:
            trades: List of Trade objects with entry_conditions
            min_trades: Minimum trades required to train

        Returns:
            Training results dict
        """
        if not LIGHTGBM_AVAILABLE:
            return {"status": "error", "message": "LightGBM not available"}

        # Filter trades with entry conditions
        valid_trades = [t for t in trades if t.entry_conditions is not None]

        if len(valid_trades) < min_trades:
            return {
                "status": "insufficient_data",
                "message": f"Need {min_trades} trades with conditions, have {len(valid_trades)}"
            }

        # Prepare training data
        X = np.array([self._extract_features(t.entry_conditions, t.side) for t in valid_trades])
        y = np.array([1 if t.pnl_pct > 0 else 0 for t in valid_trades])

        # Split train/val (80/20)
        split_idx = int(len(X) * 0.8)
        X_train, X_val = X[:split_idx], X[split_idx:]
        y_train, y_val = y[:split_idx], y[split_idx:]

        # Create datasets
        train_data = lgb.Dataset(X_train, label=y_train, feature_name=self.FEATURE_COLS)
        val_data = lgb.Dataset(X_val, label=y_val, feature_name=self.FEATURE_COLS)

        # Model parameters
        params = {
            'objective': 'binary',
            'metric': 'auc',
            'boosting_type': 'gbdt',
            'num_leaves': 31,
            'learning_rate': 0.05,
            'feature_fraction': 0.8,
            'bagging_fraction': 0.8,
            'bagging_freq': 5,
            'verbose': -1,
            'min_data_in_leaf': 5,
            'max_depth': 6
        }

        # Train
        self.model = lgb.train(
            params,
            train_data,
            num_boost_round=100,
            valid_sets=[val_data],
            callbacks=[lgb.early_stopping(stopping_rounds=10, verbose=False)]
        )

        # Calculate accuracies
        train_preds = (self.model.predict(X_train) > 0.5).astype(int)
        val_preds = (self.model.predict(X_val) > 0.5).astype(int)
        train_acc = (train_preds == y_train).mean()
        val_acc = (val_preds == y_val).mean()

        # Store feature importance
        importance = self.model.feature_importance(importance_type='gain')
        self.feature_importance = dict(zip(self.FEATURE_COLS, importance))

        # Update stats
        self.training_stats = {
            "total_trades": len(valid_trades),
            "last_trained": datetime.utcnow().isoformat(),
            "train_accuracy": float(train_acc),
            "val_accuracy": float(val_acc),
            "feature_importance": self.feature_importance
        }

        # Save model
        self._save_model()

        logger.info(f"ML model trained: {len(valid_trades)} trades, val_acc={val_acc:.1%}")

        return {
            "status": "success",
            "trades_used": len(valid_trades),
            "train_accuracy": train_acc,
            "val_accuracy": val_acc,
            "top_features": sorted(self.feature_importance.items(), key=lambda x: -x[1])[:5]
        }

    def predict(self, entry_conditions, side: str) -> PredictionResult:
        """Predict win probability for a trade setup.

        Args:
            entry_conditions: EntryConditions object
            side: "long" or "short"

        Returns:
            PredictionResult with probability and recommendation
        """
        if not LIGHTGBM_AVAILABLE or not self.model:
            return PredictionResult(
                win_probability=0.5,
                confidence="low",
                key_factors=[],
                recommendation="skip"
            )

        # Extract features and predict
        features = self._extract_features(entry_conditions, side).reshape(1, -1)
        prob = float(self.model.predict(features)[0])

        # Determine confidence based on how far from 0.5
        distance = abs(prob - 0.5)
        if distance > 0.25:
            confidence = "high"
        elif distance > 0.15:
            confidence = "medium"
        else:
            confidence = "low"

        # Get top contributing factors
        if self.feature_importance:
            sorted_features = sorted(self.feature_importance.items(), key=lambda x: -x[1])
            key_factors = sorted_features[:5]
        else:
            key_factors = []

        # Generate recommendation
        if prob >= 0.65:
            recommendation = "strong_take"
        elif prob >= 0.55:
            recommendation = "take"
        elif prob >= 0.45:
            recommendation = "skip"  # Too uncertain
        elif prob >= 0.35:
            recommendation = "skip"
        else:
            recommendation = "strong_skip"

        return PredictionResult(
            win_probability=prob,
            confidence=confidence,
            key_factors=key_factors,
            recommendation=recommendation
        )

    def should_take_trade(self, entry_conditions, side: str, min_probability: float = 0.55) -> Tuple[bool, str]:
        """Simple yes/no decision on whether to take a trade.

        Args:
            entry_conditions: EntryConditions object
            side: "long" or "short"
            min_probability: Minimum win probability to take trade

        Returns:
            (should_take, reason)
        """
        if not LIGHTGBM_AVAILABLE or not self.model:
            return True, "ML model not available, defaulting to take"

        result = self.predict(entry_conditions, side)

        if result.win_probability >= min_probability:
            return True, f"ML: {result.win_probability:.0%} win prob (>={min_probability:.0%})"
        else:
            return False, f"ML: {result.win_probability:.0%} win prob (<{min_probability:.0%})"

    def get_feature_importance_report(self) -> str:
        """Get human-readable feature importance report."""
        if not self.feature_importance:
            return "No model trained yet."

        lines = [
            "=" * 60,
            "🤖 ML MODEL FEATURE IMPORTANCE",
            "=" * 60,
            f"Trained on: {self.training_stats.get('total_trades', 0)} trades",
            f"Validation Accuracy: {self.training_stats.get('val_accuracy', 0):.1%}",
            "",
            "TOP PREDICTIVE FEATURES:"
        ]

        sorted_features = sorted(self.feature_importance.items(), key=lambda x: -x[1])
        total_importance = sum(self.feature_importance.values())

        for i, (feature, importance) in enumerate(sorted_features[:10], 1):
            pct = importance / total_importance * 100 if total_importance > 0 else 0
            lines.append(f"  {i}. {feature}: {pct:.1f}%")

        lines.append("=" * 60)
        return "\n".join(lines)

    def update_with_trade(self, trade, retrain_threshold: int = 50) -> bool:
        """Update model with a new completed trade.

        Triggers retraining when enough new trades accumulate.

        Args:
            trade: Completed Trade object
            retrain_threshold: Retrain after this many new trades

        Returns:
            True if model was retrained
        """
        # Track for periodic retraining (implementation would store trades)
        # For now, this is a placeholder - actual implementation would
        # accumulate trades and retrain periodically
        return False

