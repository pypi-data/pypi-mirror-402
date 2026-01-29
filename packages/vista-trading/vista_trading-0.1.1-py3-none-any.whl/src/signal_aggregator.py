"""
Bayesian Signal Aggregator - Probabilistic Signal Combination

Instead of simple weighted averages, this uses Bayesian reasoning:
1. Start with a prior probability (base rate)
2. Update with each signal as new evidence (likelihood ratios)
3. Account for signal correlation (avoid double-counting)
4. Output calibrated confidence scores

This approach:
- Handles conflicting signals properly
- Produces well-calibrated probabilities
- Avoids overconfidence when signals are correlated
- Learns from historical accuracy of each signal
"""

import logging
import math
from typing import Dict, Any, List, Tuple, Optional
from dataclasses import dataclass, field
from datetime import datetime
from collections import defaultdict

logger = logging.getLogger(__name__)


@dataclass
class SignalSource:
    """A signal source with its historical performance."""
    name: str
    # Likelihood ratios: P(signal|bullish) / P(signal|bearish)
    # >1 means signal is bullish evidence, <1 means bearish evidence
    bullish_lr: float = 2.0  # Default: signal is 2x more likely if market is bullish
    bearish_lr: float = 2.0
    neutral_lr: float = 1.0
    # Historical win rate when this signal fires
    historical_accuracy: float = 0.5
    # Correlation with other signals (0-1, higher = more correlated)
    correlation_factor: float = 0.3
    # Weight in final calculation
    weight: float = 1.0


# Default signal configurations based on typical performance
DEFAULT_SIGNALS = {
    "smc_structure": SignalSource(
        name="SMC Market Structure",
        bullish_lr=2.5, bearish_lr=2.5,
        historical_accuracy=0.58,
        correlation_factor=0.4,
        weight=1.5
    ),
    "smc_orderblock": SignalSource(
        name="SMC Order Block",
        bullish_lr=2.2, bearish_lr=2.2,
        historical_accuracy=0.55,
        correlation_factor=0.5,  # Correlated with structure
        weight=1.2
    ),
    "smc_fvg": SignalSource(
        name="SMC Fair Value Gap",
        bullish_lr=1.8, bearish_lr=1.8,
        historical_accuracy=0.52,
        correlation_factor=0.4,
        weight=1.0
    ),
    "smc_liquidity": SignalSource(
        name="SMC Liquidity Sweep",
        bullish_lr=2.8, bearish_lr=2.8,
        historical_accuracy=0.60,
        correlation_factor=0.3,
        weight=1.8
    ),
    "volume_profile": SignalSource(
        name="Volume Profile",
        bullish_lr=1.9, bearish_lr=1.9,
        historical_accuracy=0.54,
        correlation_factor=0.2,  # Low correlation with SMC
        weight=1.3
    ),
    "rsi_signal": SignalSource(
        name="RSI Signal",
        bullish_lr=1.6, bearish_lr=1.6,
        historical_accuracy=0.51,
        correlation_factor=0.6,  # High correlation with other momentum
        weight=0.8
    ),
    "ema_signal": SignalSource(
        name="EMA Trend",
        bullish_lr=1.7, bearish_lr=1.7,
        historical_accuracy=0.53,
        correlation_factor=0.7,  # Very correlated with other trend
        weight=0.9
    ),
    "macd_signal": SignalSource(
        name="MACD Signal",
        bullish_lr=1.5, bearish_lr=1.5,
        historical_accuracy=0.50,
        correlation_factor=0.6,
        weight=0.7
    ),
    "candle_pattern": SignalSource(
        name="Candle Pattern",
        bullish_lr=1.4, bearish_lr=1.4,
        historical_accuracy=0.48,
        correlation_factor=0.3,
        weight=0.6
    ),
    "whale_signal": SignalSource(
        name="Whale Activity",
        bullish_lr=2.0, bearish_lr=2.0,
        historical_accuracy=0.56,
        correlation_factor=0.2,  # Independent
        weight=1.4
    ),
    "funding_rate": SignalSource(
        name="Funding Rate",
        bullish_lr=1.6, bearish_lr=1.6,
        historical_accuracy=0.52,
        correlation_factor=0.3,
        weight=0.9
    ),
    "fear_greed": SignalSource(
        name="Fear & Greed",
        bullish_lr=1.3, bearish_lr=1.3,
        historical_accuracy=0.51,
        correlation_factor=0.4,
        weight=0.6
    ),
    "deepseek_analysis": SignalSource(
        name="DeepSeek Analysis",
        bullish_lr=2.2, bearish_lr=2.2,
        historical_accuracy=0.55,
        correlation_factor=0.5,  # Moderately independent
        weight=1.5
    ),
    "regime": SignalSource(
        name="Market Regime",
        bullish_lr=1.8, bearish_lr=1.8,
        historical_accuracy=0.54,
        correlation_factor=0.5,
        weight=1.1
    )
}


class BayesianAggregator:
    """
    Aggregates multiple trading signals using Bayesian inference.
    """
    
    def __init__(self, base_rate: float = 0.5):
        """
        Initialize aggregator.
        
        Args:
            base_rate: Prior probability of bullish outcome (default 0.5 = no bias)
        """
        self.base_rate = base_rate
        self.signals = DEFAULT_SIGNALS.copy()
        self.signal_history: Dict[str, List[Dict]] = defaultdict(list)

    def aggregate_signals(
        self,
        signal_data: Dict[str, Tuple[str, float]]
    ) -> Dict[str, Any]:
        """
        Aggregate multiple signals into a single probabilistic assessment.

        Uses Bayes' theorem to update probability with each signal.

        Args:
            signal_data: Dict of signal_name -> (direction, strength)
                         direction: "bullish", "bearish", or "neutral"
                         strength: 0-1 confidence in the signal

        Returns:
            Dict with aggregated probability and confidence
        """
        # Start with prior odds
        prior_odds = self.base_rate / (1 - self.base_rate)

        # Track signals used
        signals_used = []
        cumulative_correlation = 0

        # Sort signals by weight (process most important first)
        sorted_signals = sorted(
            signal_data.items(),
            key=lambda x: self.signals.get(x[0], SignalSource(x[0])).weight,
            reverse=True
        )

        log_odds = math.log(prior_odds)

        for signal_name, (direction, strength) in sorted_signals:
            if direction == "neutral" or strength < 0.1:
                continue

            # Get signal configuration
            signal_config = self.signals.get(signal_name, SignalSource(signal_name))

            # Get likelihood ratio based on direction
            if direction == "bullish":
                lr = signal_config.bullish_lr
            elif direction == "bearish":
                lr = 1 / signal_config.bearish_lr  # Inverse for bearish
            else:
                lr = signal_config.neutral_lr

            # Adjust LR by signal strength
            adjusted_lr = 1 + (lr - 1) * strength

            # Apply correlation discount (reduce impact if correlated with previous signals)
            correlation_discount = 1 - (cumulative_correlation * signal_config.correlation_factor)
            correlation_discount = max(0.3, correlation_discount)  # Floor at 30%

            # Update log odds (Bayesian update)
            if adjusted_lr > 0:
                log_odds += math.log(adjusted_lr) * correlation_discount * signal_config.weight

            # Update cumulative correlation
            cumulative_correlation = min(1.0, cumulative_correlation + signal_config.correlation_factor * 0.3)

            signals_used.append({
                "name": signal_name,
                "direction": direction,
                "strength": round(strength, 2),
                "lr": round(adjusted_lr, 2),
                "discount": round(correlation_discount, 2),
                "contribution": round(math.log(adjusted_lr) * correlation_discount * signal_config.weight, 3)
            })

        # Convert log odds back to probability
        posterior_odds = math.exp(log_odds)
        posterior_prob = posterior_odds / (1 + posterior_odds)

        # Determine direction and confidence
        if posterior_prob > 0.55:
            direction = "bullish"
            confidence = (posterior_prob - 0.5) * 2  # Scale 0.5-1 to 0-1
        elif posterior_prob < 0.45:
            direction = "bearish"
            confidence = (0.5 - posterior_prob) * 2
        else:
            direction = "neutral"
            confidence = 0

        # Calculate signal strength (1-10 scale)
        strength_score = int(min(10, max(1, abs(posterior_prob - 0.5) * 20)))

        # Calculate signal quality (how many independent signals agree)
        agreement_score = sum(1 for s in signals_used if s["direction"] == direction)
        disagreement_score = sum(1 for s in signals_used if s["direction"] != direction and s["direction"] != "neutral")

        quality = "high" if agreement_score >= 4 and disagreement_score <= 1 else \
                  "medium" if agreement_score >= 2 else "low"

        return {
            "direction": direction,
            "probability": round(posterior_prob, 3),
            "confidence": round(confidence, 2),
            "strength": strength_score,
            "quality": quality,
            "signals_bullish": sum(1 for s in signals_used if s["direction"] == "bullish"),
            "signals_bearish": sum(1 for s in signals_used if s["direction"] == "bearish"),
            "signals_used": signals_used,
            "log_odds": round(log_odds, 3),
            "prior": self.base_rate
        }

    def get_trading_signal(
        self,
        smc_analysis: Dict = None,
        volume_profile: Dict = None,
        rsi: float = None,
        ema_signal: str = None,
        macd_signal: str = None,
        candle_pattern: Dict = None,
        whale_signal: Dict = None,
        funding_rate: float = None,
        fear_greed: Dict = None,
        deepseek_analysis: Dict = None,
        regime: Dict = None
    ) -> Dict[str, Any]:
        """
        Get aggregated trading signal from all available inputs.

        This is the main entry point for the trading bot.
        """
        signal_data = {}

        # SMC Analysis
        if smc_analysis and smc_analysis.get("valid"):
            bias = smc_analysis.get("bias", "neutral")
            conf = smc_analysis.get("confidence", 0.5)
            signal_data["smc_structure"] = (bias, conf)

            # Order blocks
            obs = smc_analysis.get("order_blocks", [])
            if obs:
                # If near bullish OB, bullish signal
                ob_bias = "bullish" if obs[0].get("is_bullish") else "bearish"
                signal_data["smc_orderblock"] = (ob_bias, obs[0].get("strength", 0.5))

            # FVGs
            fvgs = smc_analysis.get("fair_value_gaps", [])
            if fvgs:
                fvg_bias = "bullish" if fvgs[0].get("is_bullish") else "bearish"
                signal_data["smc_fvg"] = (fvg_bias, 0.6)

            # Liquidity sweeps
            sweeps = smc_analysis.get("liquidity", {}).get("swept", [])
            if sweeps:
                sweep_bias = sweeps[-1].get("implication", "neutral")
                signal_data["smc_liquidity"] = (sweep_bias, 0.8)

        # Volume Profile
        if volume_profile and volume_profile.get("valid"):
            vp_bias = volume_profile.get("bias", "neutral")
            vp_conf = volume_profile.get("confidence", 0.5)
            if "bullish" in vp_bias:
                signal_data["volume_profile"] = ("bullish", vp_conf)
            elif "bearish" in vp_bias:
                signal_data["volume_profile"] = ("bearish", vp_conf)

        # RSI
        if rsi is not None:
            if rsi > 70:
                signal_data["rsi_signal"] = ("bearish", min((rsi - 70) / 30, 1.0))
            elif rsi < 30:
                signal_data["rsi_signal"] = ("bullish", min((30 - rsi) / 30, 1.0))

        # EMA
        if ema_signal:
            if ema_signal == "bullish":
                signal_data["ema_signal"] = ("bullish", 0.6)
            elif ema_signal == "bearish":
                signal_data["ema_signal"] = ("bearish", 0.6)

        # MACD
        if macd_signal:
            if macd_signal == "bullish":
                signal_data["macd_signal"] = ("bullish", 0.5)
            elif macd_signal == "bearish":
                signal_data["macd_signal"] = ("bearish", 0.5)

        # Candle Pattern
        if candle_pattern:
            cp_bias = candle_pattern.get("bias", "neutral")
            cp_strength = candle_pattern.get("strength", 0) / 100
            if cp_bias != "neutral":
                signal_data["candle_pattern"] = (cp_bias, cp_strength)

        # Whale Signal
        if whale_signal:
            ws_signal = whale_signal.get("signal", "neutral")
            ws_strength = whale_signal.get("strength", 0.5)
            if ws_signal != "neutral":
                signal_data["whale_signal"] = (ws_signal, ws_strength)

        # Funding Rate (negative = bullish, positive = bearish contrarian)
        if funding_rate is not None:
            if funding_rate > 0.0003:  # High positive = crowded long
                signal_data["funding_rate"] = ("bearish", min(funding_rate * 1000, 1.0))
            elif funding_rate < -0.0001:  # Negative = shorts paying
                signal_data["funding_rate"] = ("bullish", min(abs(funding_rate) * 1000, 1.0))

        # Fear & Greed
        if fear_greed:
            fg_value = fear_greed.get("value", 50)
            if fg_value < 25:  # Extreme fear = contrarian bullish
                signal_data["fear_greed"] = ("bullish", (25 - fg_value) / 25)
            elif fg_value > 75:  # Extreme greed = contrarian bearish
                signal_data["fear_greed"] = ("bearish", (fg_value - 75) / 25)

        # DeepSeek Analysis
        if deepseek_analysis:
            ds_bias = deepseek_analysis.get("trend_direction", "neutral")
            ds_conf = deepseek_analysis.get("confidence", 0.5)
            if ds_bias != "neutral":
                signal_data["deepseek_analysis"] = (ds_bias, ds_conf)

        # Market Regime
        if regime:
            reg_type = regime.get("regime", "unknown")
            if reg_type in ["trending", "strong_uptrend", "uptrend"]:
                signal_data["regime"] = ("bullish", 0.6)
            elif reg_type in ["downtrend", "strong_downtrend"]:
                signal_data["regime"] = ("bearish", 0.6)

        # Aggregate all signals
        result = self.aggregate_signals(signal_data)

        # Add recommendation
        if result["confidence"] >= 0.6 and result["quality"] in ["high", "medium"]:
            result["recommendation"] = "ENTRY"
        elif result["confidence"] >= 0.4:
            result["recommendation"] = "CONSIDER"
        else:
            result["recommendation"] = "WAIT"

        return result

    def record_outcome(self, signal_name: str, direction: str, was_correct: bool):
        """
        Record the outcome of a signal for learning.

        Over time, this updates the accuracy estimates for each signal.
        """
        self.signal_history[signal_name].append({
            "direction": direction,
            "correct": was_correct,
            "timestamp": datetime.utcnow().isoformat()
        })

        # Update accuracy estimate if we have enough history
        history = self.signal_history[signal_name]
        if len(history) >= 20:
            recent = history[-50:]  # Last 50 outcomes
            accuracy = sum(1 for h in recent if h["correct"]) / len(recent)

            # Update signal configuration
            if signal_name in self.signals:
                old_acc = self.signals[signal_name].historical_accuracy
                # Exponential moving average of accuracy
                self.signals[signal_name].historical_accuracy = old_acc * 0.8 + accuracy * 0.2

                # Adjust likelihood ratios based on accuracy
                if accuracy > 0.55:
                    self.signals[signal_name].bullish_lr *= 1.02
                    self.signals[signal_name].bearish_lr *= 1.02
                elif accuracy < 0.45:
                    self.signals[signal_name].bullish_lr *= 0.98
                    self.signals[signal_name].bearish_lr *= 0.98


# Global instance for easy access
_aggregator = None

def get_aggregator() -> BayesianAggregator:
    """Get or create the global aggregator instance."""
    global _aggregator
    if _aggregator is None:
        _aggregator = BayesianAggregator()
    return _aggregator

