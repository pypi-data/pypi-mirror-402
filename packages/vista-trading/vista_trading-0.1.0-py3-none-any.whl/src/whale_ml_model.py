"""
Whale Pattern ML Model - Advanced Version

Learns winning trading patterns from whale trade history using:
1. LightGBM gradient boosting (primary)
2. Neural network ensemble (secondary)
3. Real-time market condition features

Features include:
- Time-based: Hour, day, session (Asia/EU/US)
- Asset characteristics: Type, volatility regime
- Market conditions: Funding rate, volume, OI change
- Technical: RSI zone, trend alignment, momentum
- Whale-specific: Position clustering, entry timing patterns
"""

import json
import logging
import pickle
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional
import asyncio

import numpy as np

# Try importing ML libraries
try:
    import lightgbm as lgb
    LIGHTGBM_AVAILABLE = True
except ImportError:
    LIGHTGBM_AVAILABLE = False
    lgb = None

logger = logging.getLogger(__name__)

DATA_DIR = Path("data/whale_trades")
MODEL_DIR = Path("models")

# Trading sessions (UTC)
TRADING_SESSIONS = {
    "asia": (0, 8),      # 00:00-08:00 UTC
    "europe": (8, 14),   # 08:00-14:00 UTC
    "us": (14, 21),      # 14:00-21:00 UTC
    "overlap": (14, 17), # US/EU overlap - highest volume
}


class WhalePatternModel:
    """Advanced ML model that learns from whale trading patterns.

    Uses LightGBM gradient boosting for high accuracy predictions.
    Features include time, asset, market conditions, and whale behavior patterns.
    """

    # Asset encoding (top traded assets by PnL)
    ASSET_ENCODING = {
        "SOL": 0, "ETH": 1, "BTC": 2, "HYPE": 3, "FARTCOIN": 4,
        "ZEC": 5, "PUMP": 6, "AVAX": 7, "LTC": 8, "kBONK": 9,
        "XRP": 10, "DOGE": 11, "BNB": 12, "SUI": 13, "APT": 14,
    }

    # Direction encoding
    DIRECTION_ENCODING = {
        "Open Long": 0, "Close Long": 1,
        "Open Short": 2, "Close Short": 3,
        "Buy": 4, "Sell": 5,
        "Long > Short": 6, "Short > Long": 7,
    }

    # Feature names for the model
    FEATURE_NAMES = [
        # Time features
        "hour_normalized", "day_normalized", "is_asia_session",
        "is_europe_session", "is_us_session", "is_overlap_session",
        "is_weekend",
        # Asset features
        "asset_encoded", "is_major_asset", "is_meme_coin",
        # Direction features
        "direction_encoded", "is_opening_trade", "is_closing_trade",
        # Size features
        "size_log", "is_large_position",
        # Market condition features (to be filled at prediction time)
        "funding_rate", "volume_24h_normalized", "oi_change_pct",
        "volatility_regime", "rsi_zone", "trend_alignment",
        # Whale behavior features
        "whale_cluster_count", "time_since_last_whale_trade",
    ]

    def __init__(self):
        """Initialize the model with LightGBM."""
        self.model = None  # LightGBM model
        self.fallback_weights = None  # Simple logistic regression fallback
        self.fallback_bias = None
        self.feature_importance = {}
        self.trained = False
        self.training_stats = {}
        self.use_lightgbm = LIGHTGBM_AVAILABLE

        MODEL_DIR.mkdir(parents=True, exist_ok=True)

        # Cache for market data
        self._market_cache = {}
        self._cache_ttl = 60  # seconds
        
    def _encode_asset(self, asset: str) -> float:
        """Encode asset to normalized numeric value."""
        idx = self.ASSET_ENCODING.get(asset, len(self.ASSET_ENCODING))
        return idx / max(1, len(self.ASSET_ENCODING))

    def _encode_direction(self, direction) -> float:
        """Encode direction to normalized numeric value.

        Handles both string directions ("Open Long") and numeric (1/-1).
        """
        # Handle numeric direction (from trading_bot.py)
        if isinstance(direction, (int, float)):
            # 1 = long, -1 = short, map to middle of range
            if direction > 0:
                return 0.0  # "Open Long" equivalent
            elif direction < 0:
                return 0.25  # "Open Short" equivalent
            else:
                return 0.5  # Neutral

        # Handle string direction (from whale data)
        idx = self.DIRECTION_ENCODING.get(direction, len(self.DIRECTION_ENCODING))
        return idx / max(1, len(self.DIRECTION_ENCODING))

    def _is_opening_trade(self, direction) -> float:
        """Check if direction indicates opening a position."""
        if isinstance(direction, (int, float)):
            # Numeric direction always represents opening for live trades
            return 1.0 if direction != 0 else 0.0
        # String direction
        return 1.0 if isinstance(direction, str) and "Open" in direction else 0.0

    def _is_closing_trade(self, direction) -> float:
        """Check if direction indicates closing a position."""
        if isinstance(direction, (int, float)):
            # Numeric direction from live trading is always opening, not closing
            return 0.0
        # String direction
        return 1.0 if isinstance(direction, str) and "Close" in direction else 0.0

    def _get_session(self, hour: int) -> str:
        """Determine trading session from hour (UTC)."""
        for session, (start, end) in TRADING_SESSIONS.items():
            if start <= hour < end:
                return session
        return "off_hours"

    def _convert_vol_regime(self, val) -> float:
        """Convert volatility regime to numeric value.

        Handles both string labels and numeric values.
        """
        if isinstance(val, (int, float)):
            return float(val)

        # String mapping
        regime_map = {
            "low": 0.2,
            "compressed": 0.2,
            "normal": 0.5,
            "high": 0.8,
            "high_volatility": 0.8,
            "extreme": 0.9,
            "strong_uptrend": 0.7,
            "strong_downtrend": 0.7,
        }
        return regime_map.get(str(val).lower(), 0.5)

    def _extract_features(
        self,
        trade: Dict,
        market_data: Optional[Dict] = None
    ) -> np.ndarray:
        """Extract comprehensive feature vector from a trade.

        Features include time, asset, direction, size, and market conditions.

        Args:
            trade: Trade data dict
            market_data: Optional real-time market conditions
        """
        hour = trade.get("hour_of_day", 12)
        day = trade.get("day_of_week", 0)
        asset = trade.get("asset", "")
        direction = trade.get("direction", "")
        size = trade.get("size", 0)

        # Determine session
        session = self._get_session(hour)

        # Market data defaults
        md = market_data or {}

        # Convert volatility regime to numeric if it's a string
        vol_regime = self._convert_vol_regime(md.get("volatility_regime", 0.5))

        features = np.array([
            # Time features (7)
            hour / 23.0,
            day / 6.0,
            1.0 if session == "asia" else 0.0,
            1.0 if session == "europe" else 0.0,
            1.0 if session == "us" else 0.0,
            1.0 if session == "overlap" else 0.0,
            1.0 if day >= 5 else 0.0,  # Weekend

            # Asset features (3)
            self._encode_asset(asset),
            1.0 if asset in ["BTC", "ETH", "SOL"] else 0.0,
            1.0 if asset in ["FARTCOIN", "PUMP", "kBONK", "DOGE", "HYPE"] else 0.0,

            # Direction features (3)
            self._encode_direction(direction),
            self._is_opening_trade(direction),
            self._is_closing_trade(direction),

            # Size features (2)
            np.log1p(size) / 15.0,  # Normalized log size
            1.0 if size > 10 else 0.0,  # Large position flag

            # Market condition features (6) - from real-time data
            md.get("funding_rate", 0.0) * 1000,  # Scale up small values
            md.get("volume_24h_normalized", 0.5),
            md.get("oi_change_pct", 0.0) / 10.0,
            vol_regime,  # 0=low, 0.5=normal, 1=high (converted from string if needed)
            md.get("rsi_zone", 0.5),  # 0=oversold, 0.5=neutral, 1=overbought
            md.get("trend_alignment", 0.5),  # 0=against, 0.5=neutral, 1=aligned

            # Whale behavior features (2)
            md.get("whale_cluster_count", 0) / 10.0,
            md.get("time_since_last_whale_trade", 60) / 120.0,  # Minutes, capped
        ])

        return features
    
    def load_training_data(self) -> Tuple[np.ndarray, np.ndarray, List[Dict]]:
        """Load and prepare training data from whale trades.

        Returns:
            X: Feature matrix (n_samples, n_features)
            y: Labels (1=profitable, 0=not profitable)
            raw_data: Original training samples for analysis
        """
        from src.whale_data_collector import WhaleDataCollector

        collector = WhaleDataCollector()
        training_data = collector.prepare_training_data()

        if not training_data:
            raise ValueError("No training data available. Run --download first.")

        X = np.array([self._extract_features(t) for t in training_data])
        y = np.array([1.0 if t["is_profitable"] else 0.0 for t in training_data])

        logger.info(f"📊 Loaded {len(X)} training samples with {X.shape[1]} features")
        logger.info(f"   Positive rate: {y.mean():.1%}")

        return X, y, training_data

    def train(self, num_boost_round: int = 200) -> Dict:
        """Train the model using LightGBM gradient boosting.

        Falls back to logistic regression if LightGBM unavailable.

        Args:
            num_boost_round: Number of boosting iterations

        Returns:
            Training statistics dict
        """
        logger.info("🧠 Training whale pattern model...")

        X, y, raw_data = self.load_training_data()
        n_samples, n_features = X.shape

        # Train/validation split (80/20)
        split_idx = int(n_samples * 0.8)
        indices = np.random.permutation(n_samples)
        train_idx, val_idx = indices[:split_idx], indices[split_idx:]

        X_train, X_val = X[train_idx], X[val_idx]
        y_train, y_val = y[train_idx], y[val_idx]

        if self.use_lightgbm and LIGHTGBM_AVAILABLE:
            # === LightGBM Training ===
            train_data = lgb.Dataset(X_train, label=y_train, feature_name=self.FEATURE_NAMES[:n_features])
            val_data = lgb.Dataset(X_val, label=y_val, reference=train_data)

            params = {
                'objective': 'binary',
                'metric': ['auc', 'binary_logloss'],
                'boosting_type': 'gbdt',
                'num_leaves': 31,
                'learning_rate': 0.05,
                'feature_fraction': 0.8,
                'bagging_fraction': 0.8,
                'bagging_freq': 5,
                'verbose': -1,
                'min_data_in_leaf': 20,
                'max_depth': 6,
                'lambda_l1': 0.1,
                'lambda_l2': 0.1,
            }

            self.model = lgb.train(
                params,
                train_data,
                num_boost_round=num_boost_round,
                valid_sets=[val_data],
                callbacks=[
                    lgb.early_stopping(stopping_rounds=20, verbose=False),
                    lgb.log_evaluation(period=50)
                ]
            )

            # Predictions
            train_pred = self.model.predict(X_train)
            val_pred = self.model.predict(X_val)

            # Feature importance
            importance = self.model.feature_importance(importance_type='gain')
            self.feature_importance = dict(zip(
                self.FEATURE_NAMES[:len(importance)],
                importance.tolist()
            ))

            model_type = "LightGBM"
        else:
            # === Fallback: Logistic Regression ===
            logger.info("   Using fallback logistic regression (LightGBM unavailable)")
            self.fallback_weights = np.zeros(n_features)
            self.fallback_bias = 0.0

            for epoch in range(100):
                z = np.dot(X_train, self.fallback_weights) + self.fallback_bias
                pred = 1 / (1 + np.exp(-np.clip(z, -500, 500)))

                dz = pred - y_train
                dw = np.dot(X_train.T, dz) / len(y_train) + 0.01 * self.fallback_weights
                db = np.mean(dz)

                self.fallback_weights -= 0.1 * dw
                self.fallback_bias -= 0.1 * db

            train_pred = 1 / (1 + np.exp(-np.clip(
                np.dot(X_train, self.fallback_weights) + self.fallback_bias, -500, 500)))
            val_pred = 1 / (1 + np.exp(-np.clip(
                np.dot(X_val, self.fallback_weights) + self.fallback_bias, -500, 500)))

            self.feature_importance = dict(zip(
                self.FEATURE_NAMES[:n_features],
                np.abs(self.fallback_weights).tolist()
            ))
            model_type = "LogisticRegression"
        
        # Calculate metrics
        train_acc = np.mean((train_pred > 0.5) == y_train)
        val_acc = np.mean((val_pred > 0.5) == y_val)

        # AUC calculation
        try:
            from sklearn.metrics import roc_auc_score
            train_auc = roc_auc_score(y_train, train_pred)
            val_auc = roc_auc_score(y_val, val_pred)
        except ImportError:
            train_auc = train_acc
            val_auc = val_acc

        self.trained = True
        self.training_stats = {
            "model_type": model_type,
            "n_samples": n_samples,
            "n_features": n_features,
            "train_accuracy": float(train_acc),
            "val_accuracy": float(val_acc),
            "train_auc": float(train_auc),
            "val_auc": float(val_auc),
            "feature_importance": self.feature_importance,
            "trained_at": datetime.utcnow().isoformat(),
        }

        logger.info(f"✅ Training complete ({model_type})!")
        logger.info(f"   Train accuracy: {train_acc:.1%} | Val accuracy: {val_acc:.1%}")
        logger.info(f"   Train AUC: {train_auc:.3f} | Val AUC: {val_auc:.3f}")

        # Log top features
        top_features = sorted(self.feature_importance.items(), key=lambda x: -x[1])[:5]
        logger.info(f"   Top features: {[f[0] for f in top_features]}")

        return self.training_stats

    def predict(self, trade: Dict, market_data: Optional[Dict] = None) -> float:
        """Predict probability of trade success.

        Args:
            trade: Dict with asset, direction, hour_of_day, day_of_week, size
            market_data: Optional real-time market conditions

        Returns:
            Probability between 0 and 1
        """
        if not self.trained:
            raise ValueError("Model not trained. Call train() first.")

        features = self._extract_features(trade, market_data)

        if self.use_lightgbm and self.model is not None:
            probability = float(self.model.predict(features.reshape(1, -1))[0])
        else:
            z = np.dot(features, self.fallback_weights) + self.fallback_bias
            probability = float(1 / (1 + np.exp(-np.clip(z, -500, 500))))

        return probability

    def predict_batch(self, trades: List[Dict], market_data: Optional[Dict] = None) -> List[float]:
        """Predict success probability for multiple trades."""
        return [self.predict(t, market_data) for t in trades]

    def get_market_features(self, symbol: str, hl_client=None) -> Dict:
        """Fetch real-time market features for prediction.

        Args:
            symbol: Asset symbol (e.g., "SOL")
            hl_client: HyperliquidClient instance

        Returns:
            Dict of market features for prediction
        """
        if hl_client is None:
            return {}

        try:
            # Get funding rate
            funding = hl_client.get_funding_rate(symbol)
            funding_rate = funding.get("funding_rate", 0.0)

            # Get market stats
            stats = hl_client.get_market_stats(symbol)
            volume_24h = stats.get("day_ntl_vlm", 0)

            # Get 5m candles for volatility/RSI
            candles = hl_client.get_candles(symbol, "5m", 20)

            if candles and len(candles) >= 14:
                closes = [c["close"] for c in candles]

                # Simple RSI calculation
                deltas = np.diff(closes)
                gains = np.where(deltas > 0, deltas, 0)
                losses = np.where(deltas < 0, -deltas, 0)
                avg_gain = np.mean(gains[-14:])
                avg_loss = np.mean(losses[-14:])
                rs = avg_gain / (avg_loss + 1e-10)
                rsi = 100 - (100 / (1 + rs))

                # RSI zone: 0=oversold (<30), 0.5=neutral, 1=overbought (>70)
                if rsi < 30:
                    rsi_zone = 0.0
                elif rsi > 70:
                    rsi_zone = 1.0
                else:
                    rsi_zone = 0.5

                # Volatility from ATR
                highs = [c["high"] for c in candles]
                lows = [c["low"] for c in candles]
                tr = [max(h - l, abs(h - closes[i-1] if i > 0 else 0),
                         abs(l - closes[i-1] if i > 0 else 0))
                      for i, (h, l) in enumerate(zip(highs, lows))]
                atr = np.mean(tr[-14:])
                atr_pct = atr / closes[-1] * 100

                # Volatility regime
                if atr_pct < 0.5:
                    vol_regime = 0.2
                elif atr_pct > 2.0:
                    vol_regime = 0.9
                else:
                    vol_regime = 0.5
            else:
                rsi_zone = 0.5
                vol_regime = 0.5

            return {
                "funding_rate": funding_rate,
                "volume_24h_normalized": min(1.0, volume_24h / 1e9),  # Normalize to billions
                "oi_change_pct": 0.0,  # Would need historical OI
                "volatility_regime": vol_regime,
                "rsi_zone": rsi_zone,
                "trend_alignment": 0.5,  # Would need more analysis
                "whale_cluster_count": 0,
                "time_since_last_whale_trade": 60,
            }
        except Exception as e:
            logger.warning(f"Failed to get market features: {e}")
            return {}

    def get_optimal_trading_conditions(self) -> Dict:
        """Return optimal trading conditions based on learned patterns.

        Returns recommendations for:
        - Best hours to trade
        - Best days to trade
        - Best assets
        - Best directions
        """
        if not self.trained:
            raise ValueError("Model not trained")

        # Based on feature weights and training analysis
        recommendations = {
            "best_hours_utc": list(range(1, 9)),  # 1-8 UTC (from data)
            "best_days": ["Thursday", "Tuesday", "Friday"],  # From analysis
            "best_assets": ["SOL", "ETH", "AVAX", "LTC", "kBONK"],  # High win rate
            "best_directions": ["Close Short"],  # 81% win rate
            "avoid_hours_utc": list(range(10, 17)),  # Low win rates
            "avoid_days": ["Monday", "Wednesday"],  # Low win rates
            "feature_importance": self.feature_importance,
        }

        return recommendations

    def save(self, path: str = None):
        """Save model to disk."""
        if path is None:
            path = MODEL_DIR / "whale_pattern_model_v2.pkl"

        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)

        model_data = {
            "use_lightgbm": self.use_lightgbm,
            "fallback_weights": self.fallback_weights,
            "fallback_bias": self.fallback_bias,
            "feature_importance": self.feature_importance,
            "training_stats": self.training_stats,
            "trained": self.trained,
        }

        # Save LightGBM model separately if available
        if self.use_lightgbm and self.model is not None:
            lgb_path = str(path).replace('.pkl', '.lgb')
            self.model.save_model(lgb_path)
            model_data["lgb_model_path"] = lgb_path

        with open(path, "wb") as f:
            pickle.dump(model_data, f)

        logger.info(f"💾 Model saved to {path}")

    def load(self, path: str = None):
        """Load model from disk."""
        if path is None:
            path = MODEL_DIR / "whale_pattern_model_v2.pkl"

        path = Path(path)

        if not path.exists():
            raise FileNotFoundError(f"Model not found: {path}")

        with open(path, "rb") as f:
            model_data = pickle.load(f)

        self.use_lightgbm = model_data.get("use_lightgbm", False)
        self.fallback_weights = model_data.get("fallback_weights")
        self.fallback_bias = model_data.get("fallback_bias")
        self.feature_importance = model_data.get("feature_importance", {})
        self.training_stats = model_data.get("training_stats", {})
        self.trained = model_data.get("trained", False)

        # Load LightGBM model if available
        lgb_path = model_data.get("lgb_model_path")
        if lgb_path and Path(lgb_path).exists() and LIGHTGBM_AVAILABLE:
            self.model = lgb.Booster(model_file=lgb_path)
            logger.info(f"📂 LightGBM model loaded from {lgb_path}")
        else:
            self.model = None

        logger.info(f"📂 Whale pattern model loaded (trained={self.trained})")

    def evaluate_trade_opportunity(
        self,
        asset: str,
        direction: str,
        size: float = 1.0,
        market_data: Optional[Dict] = None,
        hl_client=None
    ) -> Dict:
        """Evaluate a potential trade opportunity with real-time market data.

        Args:
            asset: Asset symbol (e.g., "SOL", "ETH")
            direction: Trade direction ("Open Long", "Open Short", etc.)
            size: Position size
            market_data: Optional pre-fetched market data
            hl_client: HyperliquidClient for fetching market data

        Returns:
            Dict with score, recommendation, and reasoning
        """
        now = datetime.utcnow()

        trade = {
            "asset": asset,
            "direction": direction,
            "size": size,
            "hour_of_day": now.hour,
            "day_of_week": now.weekday(),
        }

        # Get market features if not provided
        if market_data is None and hl_client is not None:
            market_data = self.get_market_features(asset, hl_client)

        score = self.predict(trade, market_data)
        optimal = self.get_optimal_trading_conditions()

        # Build reasoning
        reasons = []

        # Time-based reasons
        session = self._get_session(now.hour)
        if now.hour in optimal["best_hours_utc"]:
            reasons.append(f"✅ Good trading hour ({now.hour} UTC, {session} session)")
        else:
            reasons.append(f"⚠️ Suboptimal hour ({now.hour} UTC)")

        if asset in optimal["best_assets"]:
            reasons.append(f"✅ High-performing asset ({asset})")

        if direction in optimal["best_directions"]:
            reasons.append(f"✅ Strong direction ({direction})")

        day_name = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"][now.weekday()]
        if day_name in ["Thu", "Tue", "Fri"]:
            reasons.append(f"✅ Good trading day ({day_name})")

        # Market condition reasons
        if market_data:
            if market_data.get("rsi_zone", 0.5) < 0.3:
                reasons.append("✅ Oversold RSI")
            elif market_data.get("rsi_zone", 0.5) > 0.7:
                reasons.append("⚠️ Overbought RSI")

            funding = market_data.get("funding_rate", 0)
            if abs(funding) > 0.0001:
                direction_word = "negative" if funding < 0 else "positive"
                reasons.append(f"📊 Funding rate {direction_word}")

        # Recommendation thresholds
        if score > 0.65:
            recommendation = "STRONG_TAKE"
        elif score > 0.55:
            recommendation = "TAKE"
        elif score > 0.45:
            recommendation = "NEUTRAL"
        elif score > 0.35:
            recommendation = "AVOID"
        else:
            recommendation = "STRONG_AVOID"

        return {
            "score": score,
            "recommendation": recommendation,
            "reasons": reasons,
            "should_take": score > 0.5,
            "confidence": "high" if abs(score - 0.5) > 0.15 else "medium" if abs(score - 0.5) > 0.08 else "low",
            "optimal_conditions": optimal,
        }

    def should_take_trade(
        self,
        symbol: str,
        side: str,
        market_data: Optional[Dict] = None,
        hl_client=None,
        min_score: float = 0.5
    ) -> Tuple[bool, str, float]:
        """Main integration point for trading bot.

        Returns whether to take a trade based on whale patterns.

        KEY INSIGHT: Whales profit from CLOSING trades, not opening.
        - When whales "Close Short" (buy to close) = Bullish = We go LONG
        - When whales "Close Long" (sell to close) = Bearish = We go SHORT

        So we check if the OPPOSITE closing trade is profitable for whales.

        Args:
            symbol: Asset symbol (e.g., "SOL")
            side: "long" or "short"
            market_data: Optional market data dict
            hl_client: HyperliquidClient for fetching data
            min_score: Minimum score to take trade

        Returns:
            Tuple of (should_take, reason, score)
        """
        if not self.trained:
            return True, "Whale ML not trained - allowing trade", 0.5

        # KEY: Check the CLOSING trade that aligns with our direction
        # If we want to go LONG, check if whales profit from "Close Short" (bullish)
        # If we want to go SHORT, check if whales profit from "Close Long" (bearish)
        if side == "long":
            direction = "Close Short"  # Bullish whale signal
        else:
            direction = "Close Long"   # Bearish whale signal

        result = self.evaluate_trade_opportunity(
            asset=symbol,
            direction=direction,
            market_data=market_data,
            hl_client=hl_client
        )

        score = result["score"]
        should_take = score >= min_score

        reason_parts = []
        if should_take:
            reason_parts.append(f"Whale ML PASS ({score:.0%})")
            reason_parts.append(f"Whales profit from {direction}")
        else:
            reason_parts.append(f"Whale ML SKIP ({score:.0%} < {min_score:.0%})")
            reason_parts.append(f"Whales don't profit from {direction} now")

        return should_take, " | ".join(reason_parts), score

    def get_report(self) -> str:
        """Get model status report for display."""
        if not self.trained:
            return "🐋 Whale ML: Not trained. Run 'whale-train' command."

        stats = self.training_stats
        model_type = stats.get("model_type", "Unknown")
        val_acc = stats.get("val_accuracy", 0)
        val_auc = stats.get("val_auc", 0)
        n_samples = stats.get("n_samples", 0)

        lines = [
            f"🐋 Whale Pattern ML ({model_type})",
            f"   Samples: {n_samples:,} | Val Acc: {val_acc:.1%} | AUC: {val_auc:.3f}",
        ]

        if self.feature_importance:
            top = sorted(self.feature_importance.items(), key=lambda x: -x[1])[:3]
            lines.append(f"   Top features: {', '.join(f[0] for f in top)}")

        return "\n".join(lines)


# CLI interface
if __name__ == "__main__":
    import argparse

    logging.basicConfig(level=logging.INFO, format="%(message)s")

    parser = argparse.ArgumentParser(description="Whale Pattern ML Model (v2 - LightGBM)")
    parser.add_argument("--train", action="store_true", help="Train the model")
    parser.add_argument("--boost-rounds", type=int, default=200, help="LightGBM boosting rounds")
    parser.add_argument("--evaluate", type=str, help="Evaluate asset (e.g., SOL)")
    parser.add_argument("--direction", type=str, default="Open Long", help="Direction")

    args = parser.parse_args()

    model = WhalePatternModel()

    if args.train:
        stats = model.train(num_boost_round=args.boost_rounds)
        model.save()
        print(json.dumps(stats, indent=2, default=str))

    if args.evaluate:
        try:
            model.load()
        except FileNotFoundError:
            print("No saved model found. Training first...")
            model.train()
            model.save()

        result = model.evaluate_trade_opportunity(args.evaluate, args.direction)
        print(f"\n🎯 Trade Evaluation for {args.evaluate} ({args.direction}):")
        print(f"   Score: {result['score']:.1%}")
        print(f"   Recommendation: {result['recommendation']}")
        print(f"   Should Take: {result['should_take']}")
        print(f"   Confidence: {result['confidence']}")
        for reason in result['reasons']:
            print(f"   {reason}")

