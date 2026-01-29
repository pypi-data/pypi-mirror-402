"""
MICRO Intelligence Module - Professional short-term trading intelligence.

This is ONLY for MICRO strategy (5m/15m trades, hold minutes to hours).
NOT used by MACRO strategy.

Components:
1. Market Regime Detection (trend/range/expansion/compression/exhaustion)
2. Liquidity Intelligence (order book imbalance, gaps, absorption)
3. Volatility Structure (ATR slope, BB width delta)
4. Pattern Confidence Scoring (multi-factor quality score)
5. Position Risk Intelligence (dynamic sizing)
6. Multi-Timeframe Alignment
"""

import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


class MicroRegime(Enum):
    """Market regime for MICRO trading decisions."""
    TREND_UP = "trend_up"           # Use pullback longs
    TREND_DOWN = "trend_down"       # Use pullback shorts
    RANGE = "range"                 # Use mean reversion
    EXPANSION = "expansion"         # Use breakouts
    COMPRESSION = "compression"     # Wait for breakout
    EXHAUSTION = "exhaustion"       # Reduce risk, expect reversal


@dataclass
class MicroIntelligence:
    """Complete intelligence package for a MICRO trade decision."""
    regime: MicroRegime
    regime_confidence: float
    
    # Pattern scoring
    pattern_score: float            # 0-100 quality score
    pattern_type: str               # "flag", "wedge", "reversal", etc.
    pattern_stage: str              # "forming", "breakout", "extended"
    
    # Liquidity
    orderbook_bias: str             # "bullish", "bearish", "neutral"
    orderbook_imbalance: float      # -1 to 1
    liquidity_gaps: List[float]     # Price levels with thin liquidity
    
    # Volatility
    volatility_state: str           # "expanding", "contracting", "stable"
    atr_percentile: float           # 0-100 (current ATR vs history)
    
    # Risk adjustment
    size_multiplier: float          # 0.5-1.5 based on conditions
    stop_multiplier: float          # Tighter/wider stops
    
    # MTF alignment
    mtf_aligned: bool               # Do timeframes agree?
    mtf_bias: str                   # Overall bias from MTF
    
    # Trade recommendation
    should_trade: bool
    trade_bias: str                 # "long", "short", "none"
    reasoning: List[str]


class MicroIntelligenceEngine:
    """
    Professional intelligence engine for MICRO trades only.
    
    Analyzes market structure to determine:
    - WHAT regime we're in (trend/range/compression/etc)
    - HOW GOOD is the current setup (pattern score)
    - WHAT SIZE to use (risk-adjusted)
    - WHETHER to trade at all
    """
    
    def __init__(self):
        self.atr_history: Dict[str, List[float]] = {}  # symbol -> ATR values
        self.regime_history: Dict[str, List[MicroRegime]] = {}
        self.recent_trades: List[Dict] = []  # For win rate tracking
        
    def analyze(
        self,
        symbol: str,
        candles_5m: List[Dict],
        candles_15m: List[Dict],
        candles_1h: List[Dict],
        orderbook: Dict[str, Any],
        current_price: float
    ) -> MicroIntelligence:
        """
        Complete MICRO intelligence analysis.
        
        Returns intelligence package with regime, pattern score,
        liquidity analysis, and trade recommendation.
        """
        # 1. Detect market regime
        regime, regime_conf, regime_reasons = self._detect_regime(
            candles_5m, candles_15m, candles_1h
        )
        
        # 2. Score the current pattern
        pattern_score, pattern_type, pattern_stage = self._score_pattern(
            candles_5m, candles_15m, regime
        )
        
        # 3. Analyze liquidity
        ob_bias, ob_imbalance, gaps = self._analyze_liquidity(orderbook, current_price)
        
        # 4. Analyze volatility structure
        vol_state, atr_pctl = self._analyze_volatility(symbol, candles_5m)
        
        # 5. Check MTF alignment
        mtf_aligned, mtf_bias = self._check_mtf_alignment(
            candles_5m, candles_15m, candles_1h
        )
        
        # 6. Calculate risk adjustments
        size_mult, stop_mult = self._calculate_risk_adjustments(
            regime, pattern_score, atr_pctl, mtf_aligned
        )
        
        # 7. Make trade recommendation
        should_trade, trade_bias, reasoning = self._make_recommendation(
            regime, pattern_score, pattern_stage, ob_bias, 
            mtf_aligned, mtf_bias, vol_state
        )
        
        return MicroIntelligence(
            regime=regime,
            regime_confidence=regime_conf,
            pattern_score=pattern_score,
            pattern_type=pattern_type,
            pattern_stage=pattern_stage,
            orderbook_bias=ob_bias,
            orderbook_imbalance=ob_imbalance,
            liquidity_gaps=gaps,
            volatility_state=vol_state,
            atr_percentile=atr_pctl,
            size_multiplier=size_mult,
            stop_multiplier=stop_mult,
            mtf_aligned=mtf_aligned,
            mtf_bias=mtf_bias,
            should_trade=should_trade,
            trade_bias=trade_bias,
            reasoning=reasoning + regime_reasons
        )

    # ==================== 1. REGIME DETECTION ====================

    def _detect_regime(
        self,
        candles_5m: List[Dict],
        candles_15m: List[Dict],
        candles_1h: List[Dict]
    ) -> tuple[MicroRegime, float, List[str]]:
        """
        Detect market regime using:
        - ADX (trend strength)
        - ATR percentile (volatility level)
        - BB width (compression/expansion)
        - EMA slope (directional bias)
        """
        reasons = []

        if not candles_5m or len(candles_5m) < 20:
            return MicroRegime.RANGE, 0.5, ["Insufficient data"]

        # Calculate ADX (simplified - using directional movement)
        adx = self._calculate_adx(candles_5m)

        # Calculate ATR percentile
        atr_pctl = self._calculate_atr_percentile(candles_5m)

        # Calculate BB width
        bb_width = self._calculate_bb_width(candles_5m)

        # Calculate EMA slope
        ema_slope = self._calculate_ema_slope(candles_5m)

        # Determine regime
        if adx > 25:
            # Strong trend
            if ema_slope > 0:
                regime = MicroRegime.TREND_UP
                reasons.append(f"ADX={adx:.0f} (trending), EMA rising")
            else:
                regime = MicroRegime.TREND_DOWN
                reasons.append(f"ADX={adx:.0f} (trending), EMA falling")
            confidence = min(0.9, 0.6 + (adx - 25) / 50)

        elif bb_width < 0.015:
            # Compression - volatility squeeze
            regime = MicroRegime.COMPRESSION
            reasons.append(f"BB width={bb_width:.3f} (squeeze)")
            confidence = 0.7

        elif atr_pctl > 80:
            # High volatility - expansion or exhaustion
            if adx > 20:
                regime = MicroRegime.EXPANSION
                reasons.append(f"ATR pctl={atr_pctl:.0f} (expanding), ADX={adx:.0f}")
            else:
                regime = MicroRegime.EXHAUSTION
                reasons.append(f"ATR pctl={atr_pctl:.0f} (exhaustion), weak ADX")
            confidence = 0.7

        else:
            # Ranging market
            regime = MicroRegime.RANGE
            reasons.append(f"ADX={adx:.0f} (<25), ranging market")
            confidence = 0.6

        return regime, confidence, reasons

    def _calculate_adx(self, candles: List[Dict], period: int = 14) -> float:
        """Calculate ADX (Average Directional Index)."""
        if len(candles) < period + 1:
            return 20  # Default neutral

        # Calculate +DM, -DM, TR
        plus_dm = []
        minus_dm = []
        tr_list = []

        for i in range(1, len(candles)):
            high = candles[i].get("high", 0)
            low = candles[i].get("low", 0)
            prev_high = candles[i-1].get("high", 0)
            prev_low = candles[i-1].get("low", 0)
            prev_close = candles[i-1].get("close", 0)

            # True Range
            tr = max(high - low, abs(high - prev_close), abs(low - prev_close))
            tr_list.append(tr)

            # Directional Movement
            up_move = high - prev_high
            down_move = prev_low - low

            plus_dm.append(up_move if up_move > down_move and up_move > 0 else 0)
            minus_dm.append(down_move if down_move > up_move and down_move > 0 else 0)

        if len(tr_list) < period:
            return 20

        # Smooth with Wilder's method
        def wilder_smooth(data, period):
            smoothed = [sum(data[:period]) / period]
            for i in range(period, len(data)):
                smoothed.append((smoothed[-1] * (period - 1) + data[i]) / period)
            return smoothed

        atr = wilder_smooth(tr_list, period)
        smooth_plus = wilder_smooth(plus_dm, period)
        smooth_minus = wilder_smooth(minus_dm, period)

        if not atr or atr[-1] == 0:
            return 20

        # +DI and -DI
        plus_di = (smooth_plus[-1] / atr[-1]) * 100 if atr[-1] > 0 else 0
        minus_di = (smooth_minus[-1] / atr[-1]) * 100 if atr[-1] > 0 else 0

        # DX
        di_sum = plus_di + minus_di
        if di_sum == 0:
            return 20
        dx = abs(plus_di - minus_di) / di_sum * 100

        return dx  # Simplified - using DX as proxy for ADX

    def _calculate_atr_percentile(self, candles: List[Dict], period: int = 14) -> float:
        """Calculate current ATR as percentile of recent history."""
        if len(candles) < period * 2:
            return 50

        atrs = []
        for i in range(period, len(candles)):
            tr_sum = 0
            for j in range(i - period, i):
                high = candles[j].get("high", 0)
                low = candles[j].get("low", 0)
                prev_close = candles[j-1].get("close", high) if j > 0 else high
                tr = max(high - low, abs(high - prev_close), abs(low - prev_close))
                tr_sum += tr
            atrs.append(tr_sum / period)

        if not atrs:
            return 50

        current_atr = atrs[-1]
        lower_count = sum(1 for a in atrs if a < current_atr)
        return (lower_count / len(atrs)) * 100

    def _calculate_bb_width(self, candles: List[Dict], period: int = 20) -> float:
        """Calculate Bollinger Band width as % of price."""
        if len(candles) < period:
            return 0.02

        closes = [c.get("close", 0) for c in candles[-period:]]
        if not closes or closes[-1] == 0:
            return 0.02

        mean = sum(closes) / len(closes)
        variance = sum((c - mean) ** 2 for c in closes) / len(closes)
        std = variance ** 0.5

        # BB width = (Upper - Lower) / Middle = 4 * std / mean
        return (4 * std) / mean if mean > 0 else 0.02

    def _calculate_ema_slope(self, candles: List[Dict], period: int = 20) -> float:
        """Calculate EMA slope (positive = up, negative = down)."""
        if len(candles) < period + 5:
            return 0

        closes = [c.get("close", 0) for c in candles]

        # Calculate EMA
        mult = 2 / (period + 1)
        ema = [sum(closes[:period]) / period]
        for i in range(period, len(closes)):
            ema.append((closes[i] * mult) + (ema[-1] * (1 - mult)))

        if len(ema) < 5:
            return 0

        # Slope = change over last 5 periods
        return (ema[-1] - ema[-5]) / ema[-5] * 100 if ema[-5] > 0 else 0

    # ==================== 2. LIQUIDITY INTELLIGENCE ====================

    def _analyze_liquidity(
        self,
        orderbook: Dict[str, Any],
        current_price: float
    ) -> tuple[str, float, List[float]]:
        """
        Analyze order book for:
        - Imbalance (bid vs ask pressure)
        - Liquidity gaps (thin levels)
        - Hidden liquidity signals
        """
        if not orderbook:
            return "neutral", 0.0, []

        bids = orderbook.get("bids", [])
        asks = orderbook.get("asks", [])

        if not bids or not asks:
            return "neutral", 0.0, []

        # Calculate bid/ask sizes within 1% of price
        range_pct = 0.01
        bid_size = sum(
            b.get("size", 0) for b in bids
            if b.get("price", 0) >= current_price * (1 - range_pct)
        )
        ask_size = sum(
            a.get("size", 0) for a in asks
            if a.get("price", 0) <= current_price * (1 + range_pct)
        )

        total = bid_size + ask_size
        if total == 0:
            return "neutral", 0.0, []

        # Imbalance: -1 (bearish) to +1 (bullish)
        imbalance = (bid_size - ask_size) / total

        # Determine bias
        if imbalance > 0.2:
            bias = "bullish"
        elif imbalance < -0.2:
            bias = "bearish"
        else:
            bias = "neutral"

        # Find liquidity gaps (levels with < 20% of average size)
        gaps = []
        avg_bid_size = bid_size / len(bids) if bids else 0
        avg_ask_size = ask_size / len(asks) if asks else 0

        for b in bids[:10]:  # Check top 10 levels
            if b.get("size", 0) < avg_bid_size * 0.2:
                gaps.append(b.get("price", 0))

        for a in asks[:10]:
            if a.get("size", 0) < avg_ask_size * 0.2:
                gaps.append(a.get("price", 0))

        return bias, imbalance, gaps

    # ==================== 3. VOLATILITY STRUCTURE ====================

    def _analyze_volatility(
        self,
        symbol: str,
        candles: List[Dict]
    ) -> tuple[str, float]:
        """
        Analyze volatility structure:
        - Is volatility expanding or contracting?
        - Where is current ATR vs history?
        """
        if not candles or len(candles) < 20:
            return "stable", 50

        # Calculate ATR for recent periods
        recent_atrs = []
        for i in range(max(14, len(candles) - 10), len(candles)):
            high = candles[i].get("high", 0)
            low = candles[i].get("low", 0)
            prev_close = candles[i-1].get("close", high)
            tr = max(high - low, abs(high - prev_close), abs(low - prev_close))
            recent_atrs.append(tr)

        if len(recent_atrs) < 5:
            return "stable", 50

        # ATR trend (expanding or contracting)
        first_half = sum(recent_atrs[:len(recent_atrs)//2]) / (len(recent_atrs)//2)
        second_half = sum(recent_atrs[len(recent_atrs)//2:]) / (len(recent_atrs) - len(recent_atrs)//2)

        if second_half > first_half * 1.15:
            state = "expanding"
        elif second_half < first_half * 0.85:
            state = "contracting"
        else:
            state = "stable"

        # Calculate percentile
        atr_pctl = self._calculate_atr_percentile(candles)

        # Store for history
        if symbol not in self.atr_history:
            self.atr_history[symbol] = []
        self.atr_history[symbol].append(recent_atrs[-1] if recent_atrs else 0)
        self.atr_history[symbol] = self.atr_history[symbol][-100:]  # Keep last 100

        return state, atr_pctl

    # ==================== 4. PATTERN CONFIDENCE SCORING ====================

    def _score_pattern(
        self,
        candles_5m: List[Dict],
        candles_15m: List[Dict],
        regime: MicroRegime
    ) -> tuple[float, str, str]:
        """
        Score pattern quality using multiple factors:
        - Volume expansion
        - EMA alignment
        - ATR expansion
        - RSI structure
        - Price structure (HH/HL or LH/LL)

        Returns: (score 0-100, pattern_type, stage)
        """
        if not candles_5m or len(candles_5m) < 10:
            return 0, "none", "insufficient_data"

        # START WITH BASE SCORE (more lenient - start at 30 instead of 0)
        score = 30  # Base score so we can trade in quiet markets
        pattern_type = "none"
        stage = "forming"

        recent = candles_5m[-10:]
        closes = [c.get("close", 0) for c in recent]
        highs = [c.get("high", 0) for c in recent]
        lows = [c.get("low", 0) for c in recent]
        volumes = [c.get("volume", 0) for c in recent]

        # 1. VOLUME EXPANSION (+15 points) - LOWERED thresholds
        if volumes and volumes[-1] > 0:
            avg_vol = sum(volumes[:-1]) / (len(volumes) - 1) if len(volumes) > 1 else volumes[0]
            if volumes[-1] > avg_vol * 1.3:  # Was 1.5
                score += 15  # Strong volume
            elif volumes[-1] > avg_vol * 1.1:  # Was 1.2
                score += 8  # Moderate volume
            elif volumes[-1] > avg_vol * 0.8:
                score += 3  # Decent volume (new)

        # 2. EMA ALIGNMENT (+15 points) - MORE LENIENT
        ema_8 = self._simple_ema(closes, 8)
        ema_21 = self._simple_ema(closes, min(21, len(closes)))
        if ema_8 and ema_21:
            # Give points for ANY alignment, not just trending regime
            if ema_8[-1] > ema_21[-1]:
                score += 10  # Bullish alignment (any regime)
                if regime in [MicroRegime.TREND_UP, MicroRegime.EXPANSION]:
                    score += 5  # Bonus if regime agrees
            elif ema_8[-1] < ema_21[-1]:
                score += 10  # Bearish alignment (any regime)
                if regime in [MicroRegime.TREND_DOWN]:
                    score += 5  # Bonus if regime agrees

        # 3. ATR EXPANSION (+10 points) - Lowered threshold
        atr_current = self._calculate_single_atr(candles_5m[-14:])
        atr_prev = self._calculate_single_atr(candles_5m[-28:-14]) if len(candles_5m) >= 28 else atr_current
        if atr_prev > 0:
            if atr_current > atr_prev * 1.1:  # Was 1.2
                score += 10  # Volatility expanding (breakout potential)
            elif atr_current > atr_prev * 0.9:
                score += 5  # Stable volatility

        # 4. RSI STRUCTURE (+15 points) - WIDER ranges
        rsi = self._calculate_rsi(closes)
        if rsi:
            if 35 < rsi < 65:  # Was 40-60
                score += 10  # Neutral zone - good for entries
            elif rsi < 40:  # Was <35
                score += 12  # Oversold - potential long
            elif rsi > 60:  # Was >65
                score += 12  # Overbought - potential short

        # 5. PRICE STRUCTURE (+15 points) - More lenient
        if len(highs) >= 6:
            # Check for higher highs / higher lows (bullish)
            hh = highs[-1] > highs[-3]  # Removed third condition
            hl = lows[-1] > lows[-3]
            # Check for lower highs / lower lows (bearish)
            lh = highs[-1] < highs[-3]
            ll = lows[-1] < lows[-3]

            if hh and hl:
                score += 15
                pattern_type = "uptrend_structure"
            elif lh and ll:
                score += 15
                pattern_type = "downtrend_structure"
            elif hh or hl:
                score += 8  # Partial bullish structure
                pattern_type = "partial_bullish"
            elif lh or ll:
                score += 8  # Partial bearish structure
                pattern_type = "partial_bearish"

        # 6. PATTERN DETECTION (+15 points)
        detected = self._detect_specific_pattern(candles_5m)
        if detected["type"] != "none":
            score += 15
            pattern_type = detected["type"]
            stage = detected["stage"]

        # Cap at 100
        score = min(100, score)

        return score, pattern_type, stage

    def _simple_ema(self, data: List[float], period: int) -> List[float]:
        """Simple EMA calculation."""
        if len(data) < period:
            return data
        mult = 2 / (period + 1)
        ema = [sum(data[:period]) / period]
        for i in range(period, len(data)):
            ema.append((data[i] * mult) + (ema[-1] * (1 - mult)))
        return ema

    def _calculate_single_atr(self, candles: List[Dict]) -> float:
        """Calculate single ATR value."""
        if len(candles) < 2:
            return 0
        trs = []
        for i in range(1, len(candles)):
            high = candles[i].get("high", 0)
            low = candles[i].get("low", 0)
            prev_close = candles[i-1].get("close", high)
            tr = max(high - low, abs(high - prev_close), abs(low - prev_close))
            trs.append(tr)
        return sum(trs) / len(trs) if trs else 0

    def _calculate_rsi(self, closes: List[float], period: int = 14) -> Optional[float]:
        """Calculate RSI."""
        if len(closes) < period + 1:
            return None
        gains = []
        losses = []
        for i in range(1, len(closes)):
            change = closes[i] - closes[i-1]
            gains.append(max(0, change))
            losses.append(max(0, -change))

        avg_gain = sum(gains[-period:]) / period
        avg_loss = sum(losses[-period:]) / period

        if avg_loss == 0:
            return 100
        rs = avg_gain / avg_loss
        return 100 - (100 / (1 + rs))

    def _detect_specific_pattern(self, candles: List[Dict]) -> Dict[str, str]:
        """Detect specific chart patterns."""
        if len(candles) < 10:
            return {"type": "none", "stage": "none"}

        recent = candles[-10:]
        highs = [c.get("high", 0) for c in recent]
        lows = [c.get("low", 0) for c in recent]
        closes = [c.get("close", 0) for c in recent]

        # Check for flag pattern (impulse + consolidation)
        first_half_range = max(highs[:5]) - min(lows[:5])
        second_half_range = max(highs[5:]) - min(lows[5:])

        if first_half_range > 0 and second_half_range < first_half_range * 0.4:
            # Consolidation after impulse
            if closes[4] > closes[0]:  # Bullish impulse
                return {"type": "bull_flag", "stage": "consolidating"}
            else:
                return {"type": "bear_flag", "stage": "consolidating"}

        # Check for wedge (converging highs and lows)
        high_slope = (highs[-1] - highs[0]) / len(highs)
        low_slope = (lows[-1] - lows[0]) / len(lows)

        if high_slope < 0 and low_slope > 0:
            # Converging - symmetrical triangle
            return {"type": "compression", "stage": "squeezing"}
        elif high_slope < 0 and low_slope < 0 and abs(high_slope) > abs(low_slope):
            # Falling wedge (bullish)
            return {"type": "falling_wedge", "stage": "forming"}
        elif high_slope > 0 and low_slope > 0 and high_slope > low_slope:
            # Rising wedge (bearish)
            return {"type": "rising_wedge", "stage": "forming"}

        return {"type": "none", "stage": "none"}

    # ==================== 5. MTF ALIGNMENT ====================

    def _check_mtf_alignment(
        self,
        candles_5m: List[Dict],
        candles_15m: List[Dict],
        candles_1h: List[Dict]
    ) -> tuple[bool, str]:
        """
        Check if multiple timeframes agree on direction.

        TF Roles:
        - 5m: Execution timing
        - 15m: Setup structure
        - 1h: Overall bias

        Only trade when lower TFs agree with higher TFs.
        """
        def get_bias(candles: List[Dict]) -> str:
            if not candles or len(candles) < 5:
                return "neutral"
            closes = [c.get("close", 0) for c in candles[-5:]]
            if closes[-1] > closes[0] * 1.002:
                return "bullish"
            elif closes[-1] < closes[0] * 0.998:
                return "bearish"
            return "neutral"

        bias_5m = get_bias(candles_5m)
        bias_15m = get_bias(candles_15m)
        bias_1h = get_bias(candles_1h)

        # Check alignment
        all_bullish = all(b == "bullish" for b in [bias_5m, bias_15m, bias_1h])
        all_bearish = all(b == "bearish" for b in [bias_5m, bias_15m, bias_1h])

        # 1h is the master bias
        master_bias = bias_1h

        # Aligned if 5m and 15m match 1h direction (or neutral)
        aligned = (
            (bias_5m == master_bias or bias_5m == "neutral") and
            (bias_15m == master_bias or bias_15m == "neutral")
        )

        return aligned, master_bias

    # ==================== 6. RISK ADJUSTMENTS ====================

    def _calculate_risk_adjustments(
        self,
        regime: MicroRegime,
        pattern_score: float,
        atr_percentile: float,
        mtf_aligned: bool
    ) -> tuple[float, float]:
        """
        Calculate dynamic position size and stop multipliers.

        Based on:
        - Market regime
        - Pattern quality
        - Volatility level
        - MTF alignment
        - Recent performance
        """
        size_mult = 1.0
        stop_mult = 1.0

        # Regime adjustments
        if regime == MicroRegime.COMPRESSION:
            size_mult *= 0.7  # Smaller before breakout
            stop_mult *= 0.8  # Tighter stops
        elif regime == MicroRegime.EXHAUSTION:
            size_mult *= 0.5  # Much smaller on exhaustion
            stop_mult *= 1.2  # Wider stops (choppy)
        elif regime == MicroRegime.EXPANSION:
            size_mult *= 1.2  # Can size up in expansion
            stop_mult *= 1.1  # Slightly wider stops

        # Pattern quality adjustment
        if pattern_score >= 80:
            size_mult *= 1.2  # Great pattern = bigger size
        elif pattern_score >= 60:
            size_mult *= 1.0  # Good pattern
        elif pattern_score >= 40:
            size_mult *= 0.7  # Weak pattern = smaller
        else:
            size_mult *= 0.5  # Poor pattern

        # Volatility adjustment
        if atr_percentile > 80:
            size_mult *= 0.8  # Reduce in high vol
            stop_mult *= 1.2  # Wider stops
        elif atr_percentile < 20:
            stop_mult *= 0.8  # Tighter in low vol

        # MTF alignment bonus
        if mtf_aligned:
            size_mult *= 1.1  # Aligned = confidence boost
        else:
            size_mult *= 0.8  # Misaligned = reduce

        # Recent performance adjustment (if we have trade history)
        win_rate = self._get_recent_win_rate()
        if win_rate < 0.4:
            size_mult *= 0.6  # Losing streak = reduce size
        elif win_rate > 0.6:
            size_mult *= 1.1  # Winning = slight increase

        # Cap multipliers
        size_mult = max(0.3, min(1.5, size_mult))
        stop_mult = max(0.7, min(1.5, stop_mult))

        return size_mult, stop_mult

    def _get_recent_win_rate(self) -> float:
        """Get win rate from recent trades."""
        if len(self.recent_trades) < 5:
            return 0.5  # Default neutral

        wins = sum(1 for t in self.recent_trades[-20:] if t.get("pnl", 0) > 0)
        return wins / min(20, len(self.recent_trades))

    def record_trade_result(self, pnl: float, pattern_type: str, regime: str):
        """Record trade result for learning."""
        self.recent_trades.append({
            "pnl": pnl,
            "pattern": pattern_type,
            "regime": regime,
            "timestamp": datetime.utcnow()
        })
        # Keep last 100 trades
        self.recent_trades = self.recent_trades[-100:]

    # ==================== 7. TRADE RECOMMENDATION ====================

    def _make_recommendation(
        self,
        regime: MicroRegime,
        pattern_score: float,
        pattern_stage: str,
        orderbook_bias: str,
        mtf_aligned: bool,
        mtf_bias: str,
        volatility_state: str
    ) -> tuple[bool, str, List[str]]:
        """
        NEUTRAL SCANNING: Evaluate BOTH directions independently, pick better setup.

        Instead of letting regime dictate direction, we score both long and short
        setups and return the one with better confluence.

        Returns: (should_trade, direction, reasoning)
        """
        reasons = []

        # === HARD BLOCKS (apply to both directions) ===

        # Don't trade weak patterns
        if pattern_score < 25:
            reasons.append(f"BLOCKED: Pattern score {pattern_score:.0f} < 25")
            return False, "none", reasons

        # Don't trade misaligned MTF with weak patterns
        if not mtf_aligned and pattern_score < 50:
            reasons.append(f"BLOCKED: MTF misaligned and pattern score {pattern_score:.0f} < 50")
            return False, "none", reasons

        # === NEUTRAL SCORING: Evaluate BOTH directions ===
        long_score, long_reasons = self._score_direction(
            "long", regime, pattern_score, pattern_stage,
            orderbook_bias, mtf_aligned, mtf_bias, volatility_state
        )

        short_score, short_reasons = self._score_direction(
            "short", regime, pattern_score, pattern_stage,
            orderbook_bias, mtf_aligned, mtf_bias, volatility_state
        )

        reasons.append(f"NEUTRAL SCAN: Long={long_score:.0f} vs Short={short_score:.0f}")

        # === SELECT BETTER SETUP ===
        min_score = 2  # Minimum score to consider valid

        long_valid = long_score >= min_score
        short_valid = short_score >= min_score

        if not long_valid and not short_valid:
            reasons.append("Neither direction meets minimum score")
            return False, "none", reasons

        if long_valid and not short_valid:
            direction = "long"
            reasons.extend(long_reasons)
        elif short_valid and not long_valid:
            direction = "short"
            reasons.extend(short_reasons)
        elif long_score > short_score:
            direction = "long"
            reasons.extend(long_reasons)
            reasons.append(f"Long wins: {long_score:.0f} > {short_score:.0f}")
        elif short_score > long_score:
            direction = "short"
            reasons.extend(short_reasons)
            reasons.append(f"Short wins: {short_score:.0f} > {long_score:.0f}")
        else:
            # Tied - use orderbook as tiebreaker
            if orderbook_bias == "bullish":
                direction = "long"
                reasons.append("Tied scores, OB bullish → LONG")
            elif orderbook_bias == "bearish":
                direction = "short"
                reasons.append("Tied scores, OB bearish → SHORT")
            else:
                reasons.append("Tied scores, no OB bias → No trade")
                return False, "none", reasons

        reasons.append(f"✅ TRADE: {direction.upper()} | Score: {pattern_score:.0f} | Regime: {regime.value}")
        return True, direction, reasons

    def _score_direction(
        self,
        direction: str,
        regime: MicroRegime,
        pattern_score: float,
        pattern_stage: str,
        orderbook_bias: str,
        mtf_aligned: bool,
        mtf_bias: str,
        volatility_state: str
    ) -> tuple[float, List[str]]:
        """Score a specific direction independently.

        This allows neutral comparison between long and short setups.
        """
        score = 0.0
        reasons = []
        is_long = direction == "long"

        # === 1. REGIME ALIGNMENT (smaller weight - don't let regime dominate) ===
        if is_long:
            if regime == MicroRegime.TREND_UP:
                score += 2
                reasons.append("With uptrend +2")
            elif regime == MicroRegime.TREND_DOWN:
                score -= 1  # Penalty but not blocking
                reasons.append("Against downtrend -1")
            elif regime == MicroRegime.RANGE:
                score += 1  # Range is neutral, slight bonus for mean reversion
                reasons.append("Range regime +1")
        else:  # Short
            if regime == MicroRegime.TREND_DOWN:
                score += 2
                reasons.append("With downtrend +2")
            elif regime == MicroRegime.TREND_UP:
                score -= 1
                reasons.append("Against uptrend -1")
            elif regime == MicroRegime.RANGE:
                score += 1
                reasons.append("Range regime +1")

        # === 2. ORDERBOOK ALIGNMENT ===
        if is_long and orderbook_bias == "bullish":
            score += 2
            reasons.append("OB bullish +2")
        elif is_long and orderbook_bias == "bearish":
            score -= 1
            reasons.append("OB bearish -1")
        elif not is_long and orderbook_bias == "bearish":
            score += 2
            reasons.append("OB bearish +2")
        elif not is_long and orderbook_bias == "bullish":
            score -= 1
            reasons.append("OB bullish -1")

        # === 3. MTF ALIGNMENT ===
        mtf_bullish = mtf_bias in ["long", "bullish"]
        mtf_bearish = mtf_bias in ["short", "bearish"]

        if is_long and mtf_bullish:
            score += 2
            reasons.append("MTF bullish +2")
        elif is_long and mtf_bearish:
            score -= 1
            reasons.append("MTF bearish -1")
        elif not is_long and mtf_bearish:
            score += 2
            reasons.append("MTF bearish +2")
        elif not is_long and mtf_bullish:
            score -= 1
            reasons.append("MTF bullish -1")

        # === 4. PATTERN STAGE ALIGNMENT ===
        stage_lower = pattern_stage.lower()
        if is_long:
            if "bullish" in stage_lower or "uptrend" in stage_lower or "reversal_up" in stage_lower:
                score += 2
                reasons.append("Bullish pattern +2")
            elif "bearish" in stage_lower or "downtrend" in stage_lower:
                score -= 1
                reasons.append("Bearish pattern -1")
        else:
            if "bearish" in stage_lower or "downtrend" in stage_lower or "reversal_down" in stage_lower:
                score += 2
                reasons.append("Bearish pattern +2")
            elif "bullish" in stage_lower or "uptrend" in stage_lower:
                score -= 1
                reasons.append("Bullish pattern -1")

        # === 5. VOLATILITY REGIME BONUS ===
        if volatility_state == "low" and regime == MicroRegime.COMPRESSION:
            # Compression breakouts can go either way - add to both
            score += 1
            reasons.append("Compression breakout potential +1")

        # === 6. PATTERN SCORE BONUS (higher pattern = more confident) ===
        if pattern_score >= 60:
            score += 1
            reasons.append(f"High pattern score ({pattern_score:.0f}) +1")

        return score, reasons

    # ==================== UTILITY: FORMAT FOR LLM ====================

    def format_for_llm(self, intel: MicroIntelligence) -> str:
        """Format intelligence for LLM prompt injection."""
        return f"""=== MICRO INTELLIGENCE REPORT ===

🎯 REGIME: {intel.regime.value.upper()} (conf: {intel.regime_confidence:.0%})
   → {self._get_regime_strategy(intel.regime)}

📊 PATTERN: {intel.pattern_type} ({intel.pattern_stage})
   Score: {intel.pattern_score:.0f}/100

📈 ORDERBOOK: {intel.orderbook_bias.upper()} (imbalance: {intel.orderbook_imbalance:+.2f})
   {"Liquidity gaps at: " + ", ".join(f"${g:,.0f}" for g in intel.liquidity_gaps[:3]) if intel.liquidity_gaps else "No gaps detected"}

⚡ VOLATILITY: {intel.volatility_state.upper()} (ATR pctl: {intel.atr_percentile:.0f})

🔗 MTF ALIGNMENT: {"✅ ALIGNED" if intel.mtf_aligned else "❌ MISALIGNED"} | Bias: {intel.mtf_bias.upper()}

💰 RISK ADJUSTMENTS:
   Size: {intel.size_multiplier:.1f}x | Stop: {intel.stop_multiplier:.1f}x

{'🚀 RECOMMENDATION: ' + intel.trade_bias.upper() if intel.should_trade else '⏸️ RECOMMENDATION: NO TRADE'}

REASONING:
{chr(10).join('• ' + r for r in intel.reasoning)}
"""

    def _get_regime_strategy(self, regime: MicroRegime) -> str:
        """Get strategy hint for regime."""
        strategies = {
            MicroRegime.TREND_UP: "Use pullback longs, buy dips",
            MicroRegime.TREND_DOWN: "Use pullback shorts, sell rallies",
            MicroRegime.RANGE: "Use mean reversion at S/R levels",
            MicroRegime.EXPANSION: "Trade breakouts with momentum",
            MicroRegime.COMPRESSION: "Wait for breakout, don't force",
            MicroRegime.EXHAUSTION: "Reduce risk, look for reversal"
        }
        return strategies.get(regime, "Analyze structure")

