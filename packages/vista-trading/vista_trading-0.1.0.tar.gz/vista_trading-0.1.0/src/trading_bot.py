"""
Trading Bot - Main bot logic combining market data, AI analysis, and execution.

ARCHITECTURE OVERVIEW:
=====================
Unified swing trading strategy with LLM-driven entries:

SWING TRADING:
   - Entry: LLM signal + 1H trend alignment + confluence
   - Exit: ONLY stop loss, take profit, or trailing stop
   - NO mid-trade trend reversal exits
   - ATR-based position sizing and stop placement

KEY PRINCIPLE: Once in a trade, let it play out to stop or target.
              No arbitrary exits based on indicator changes.
"""

import asyncio
import logging
from typing import Dict, Optional, Any, List
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from decimal import Decimal, ROUND_UP
from enum import Enum

from .hyperliquid_client import HyperliquidClient
from .llm_service import LLMService, TradeSignal
from .technical_analysis import (
    calculate_rsi, calculate_ema, calculate_ema_crossover, calculate_volume_profile,
    calculate_macd, calculate_bollinger_bands, calculate_support_resistance, calculate_atr,
    detect_trendlines, analyze_5m_momentum, detect_5m_trend,
    analyze_multi_timeframe_candles, detect_3_candle_patterns,
    detect_rsi_divergence, detect_volume_exhaustion, detect_reversal_setup,
    # NEW: Advanced indicators
    calculate_vwap, calculate_ichimoku, calculate_adx, calculate_cvd,
    detect_market_regime, validate_entry_quality
)
from .performance_tracker import PerformanceTracker, TradeAnalyzer, EntryConditions
from .alpha_signals import AlphaSignalAggregator
from .chart_analysis import ChartAnalyzer, ThinkingTracker
from .sniper import PositionSniper, SniperConfig
from .orderbook_analyzer import OrderBookAnalyzer
from .advanced_patterns import (
    calculate_fibonacci_levels, detect_elliott_waves,
    detect_harmonic_patterns, detect_wyckoff_phase,
    analyze_order_flow_heatmap, get_advanced_analysis
)
# NEW: Professional-grade analysis modules
from .smart_money_concepts import analyze_smart_money
from .volume_profile import analyze_volume_profile, get_vp_support_resistance
from .micro_intelligence import MicroIntelligenceEngine, MicroRegime
from .proactive_micro import ProactiveMicroStrategy, VolatilityRegime
from .adaptive_parameters import (
    detect_regime, get_adaptive_thresholds, apply_adaptive_analysis, MarketRegime
)
from .signal_aggregator import BayesianAggregator, get_aggregator
from .discord_notifier import DiscordNotifier, DiscordChannels
from .realtime_monitor import RealtimeMonitor, EventDrivenAnalyzer, PriceEvent, LearningDataStore
from .pattern_detector import PatternDetector
from .tickers import (
    TRADING_TICKERS, MAX_LEVERAGE, CORRELATION_GROUPS,
    get_max_leverage, get_size_decimals
)
from .database import get_db
from .learning_engine import LearningEngine, MarketConditions
# Note: bracket_orders.py exists but is not used - MICRO and MACRO handle limit orders directly

logger = logging.getLogger(__name__)


class StrategyType(Enum):
    """Strategy type for position tracking.

    MICRO: Short-term (5m/15m/30m), hold 15min-1d
           - DeepSeek for fast signal scanning
           - EMA, RSI, MACD, BB, ATR, VWAP
           - Multi-timeframe alignment (2 of 3 must agree)
    """
    MICRO = "micro"   # 5m/15m/30m, hold 15min-1d, DeepSeek signals


@dataclass
class Position:
    """Position tracking for MICRO strategy.

    Single SL per position - moves to break-even when in profit.
    No trailing stops - just one SL that gets updated.
    """
    symbol: str
    side: str  # "long" or "short"
    entry_price: float
    size: float
    stop_loss: float
    take_profit: float
    entry_time: datetime = field(default_factory=datetime.utcnow)

    # Track best price for break-even logic
    best_price: float = 0.0
    sl_moved_to_breakeven: bool = False  # Track if we've moved SL to break-even

    # Order IDs for exchange-native SL/TP
    sl_oid: Optional[str] = None
    tp_oid: Optional[str] = None

    def __post_init__(self):
        if self.best_price == 0.0:
            self.best_price = self.entry_price


@dataclass
class BotConfig:
    """Bot configuration for MICRO-only trading strategy."""
    symbols: list = None
    position_size_usd: float = 10.0
    min_order_value_usd: float = 10.0
    tick_interval: int = 60

    # Legacy compatibility fields (used by run.py)
    min_confidence: float = 0.65        # Minimum confidence for trades (institutional standard)
    use_claude: bool = True             # Use Claude for analysis

    # ========== CENTRALIZED STOP LOSS / TAKE PROFIT CONFIG ==========
    # These are POSITION-BASED (margin loss %), NOT ticker-based
    # With leverage factored in: price_move_% = margin_loss_% / leverage
    #
    # 🚨 CRITICAL: Stops were TOO TIGHT - getting stopped in SECONDS!
    # At 40x leverage, 3% margin = 0.075% price move = $67 on BTC = INSTANT STOP
    # WIDENED to 5% margin = 0.125% price move = $112 on BTC = survivable noise

    sl_margin_pct: float = 5.0          # WIDENED from 3% - was getting stopped instantly
    tp_rr_ratio: float = 2.0            # 2:1 reward:risk (TP at 10% margin profit)

    # Break-even trigger: Move SL to entry when position reaches this % profit
    breakeven_trigger_pct: float = 3.0  # Move SL to entry at +3% margin profit (was 2%)

    # Leverage is now centralized in src/tickers.py - use get_max_leverage(symbol)
    # Legacy fields removed: leverage_btc, leverage_eth, leverage_sol

    # ========== MICRO STRATEGY CONFIG (5m/15m/30m, hold 15min-1d) ==========
    micro_enabled: bool = True
    micro_min_confidence: float = 0.65  # Minimum confidence (institutional standard)
    micro_position_pct: float = 0.50    # 50% of base position size
    micro_max_hold_hours: int = 24      # Max hold time for micro trades
    micro_cooldown_minutes: int = 5     # Cooldown between micro trades
    # (MACRO strategy removed - MICRO only)

    # ========== RISK MANAGEMENT ==========
    # Emergency stops
    emergency_stop_pct: float = -10.0   # Hard stop at -10%
    stop_loss_pct: float = 3.0          # Default stop loss %
    take_profit_pct: float = 6.0        # Default take profit %

    # ATR-based stops (ENABLED for volatility-adaptive protection)
    use_atr_stops: bool = True  # ENABLED - adapt stops to market volatility
    atr_stop_multiplier: float = 2.0  # 2x ATR for stop distance
    atr_max_stop_pct: float = 5.0  # Cap at 5% to prevent huge stops

    # Trailing stops (WIDENED - was getting stopped out too early)
    trailing_stop_activation_pct: float = 1.5   # WIDENED from 0.85% - let trade develop
    trailing_stop_distance_pct: float = 0.8     # WIDENED from 0.3% - give more room to breathe
    use_trailing_tp: bool = True                # Enable trailing TP (data shows leaving $ on table)

    # Partial profit taking
    partial_profit_target_pct: float = 1.5  # Take partial at +1.5% (earlier than before)
    partial_profit_pct: float = 33.0        # Take 33% off (keep more running)

    # Pyramiding
    pyramid_enabled: bool = False
    pyramid_trigger_pct: float = 2.0
    pyramid_max_adds: int = 2
    pyramid_size_pct: float = 50.0

    # Visual Analysis
    use_visual_analysis: bool = True  # Enable chart analysis (uses DeepSeek text by default)
    use_claude_vision: bool = False   # If True, use expensive Claude Vision. If False, use DeepSeek text

    # Real-Time Monitoring (WebSocket price streaming with event-driven AI)
    realtime_monitor_enabled: bool = True  # Enable WebSocket price streaming + chart scheduler
    realtime_sr_proximity_pct: float = 0.2  # Alert when within 0.2% of S/R
    realtime_volatility_threshold_pct: float = 1.0  # Alert on 1%+ moves in 1 minute

    # ========== PORTFOLIO RISK MANAGEMENT ==========
    # Daily Loss Limit - stop trading after X% daily loss
    daily_loss_limit_pct: float = -5.0  # Stop trading after -5% daily
    daily_loss_reset_hour: int = 0  # Reset at midnight UTC

    # Circuit Breaker - pause after consecutive losses
    circuit_breaker_enabled: bool = True
    circuit_breaker_losses: int = 3  # Pause after 3 consecutive losses
    circuit_breaker_pause_minutes: int = 60  # Pause for 1 hour

    # Portfolio Heat - max total exposure
    max_portfolio_heat_pct: float = 85.0  # Max 85% total leverage (BTC 40x + ETH 25x + SOL 20x = 85%)
    max_same_direction_positions: int = 2  # Max 2 positions same direction

    # Correlation Check - prevent concentrated risk
    correlation_check_enabled: bool = True
    max_correlated_exposure_pct: float = 100.0  # Max exposure in correlated assets

    # Performance-Based Sizing
    performance_sizing_enabled: bool = True
    win_streak_bonus_pct: float = 25.0  # +25% size per win (max 2 wins = +50%)
    lose_streak_reduction_pct: float = 25.0  # -25% size per loss (max 2 losses = -50%)
    drawdown_reduction_threshold_pct: float = 10.0  # Reduce size when drawdown > 10%
    drawdown_size_reduction_pct: float = 50.0  # Reduce to 50% size in drawdown

    # Time-of-Day / Session Filter
    time_filter_enabled: bool = False  # Disabled - trade 24/7 (crypto markets never sleep)
    trading_hours_utc: tuple = (0, 24)  # Trade all hours (legacy setting, unused when disabled)

    # Session-based filtering (more sophisticated than simple hours)
    # Each session has different characteristics - adapt accordingly
    session_filter_enabled: bool = True
    # Sessions: Asia (00:00-08:00 UTC), Europe (08:00-14:00 UTC), US (14:00-21:00 UTC)
    # Set multipliers for position sizing per session (1.0 = normal, <1 = smaller, >1 = larger)
    session_size_mult_asia: float = 0.7    # Asia = lower volatility, smaller positions
    session_size_mult_europe: float = 1.0  # Europe = good moves, normal size
    session_size_mult_us: float = 1.2      # US = most volume, larger positions
    session_size_mult_overlap: float = 1.3 # US/EU overlap (14:00-17:00 UTC) = best time
    # Avoid dead zones (21:00-00:00 UTC = post-US, pre-Asia)
    avoid_dead_zone: bool = True

    def __post_init__(self):
        if self.symbols is None:
            self.symbols = TRADING_TICKERS.copy()


# Use centralized config from src/tickers.py
# MAX_LEVERAGE and CORRELATION_GROUPS are imported from there
MAX_LEVERAGE_MAP = MAX_LEVERAGE  # Alias for backwards compatibility


class RiskManager:
    """Portfolio-level risk management for professional trading.

    Implements:
    1. Daily loss limit - stop trading after X% daily loss
    2. Circuit breaker - pause after consecutive losses
    3. Portfolio heat - max total exposure
    4. Correlation check - prevent concentrated directional risk
    5. Performance-based sizing - scale with win/loss streaks
    """

    def __init__(self, config: BotConfig, perf_tracker):
        self.config = config
        self.perf_tracker = perf_tracker

        # Daily tracking
        self.daily_pnl_pct: float = 0.0
        self.daily_start_equity: float = 0.0
        self.last_reset_date: Optional[datetime] = None

        # Circuit breaker state
        self.consecutive_losses: int = 0
        self.circuit_breaker_until: Optional[datetime] = None

        # Position tracking: symbol -> side
        self.active_positions: Dict[str, str] = {}

    def reset_daily_stats(self, current_equity: float) -> None:
        """Reset daily stats at configured hour."""
        now = datetime.utcnow()
        reset_hour = self.config.daily_loss_reset_hour

        # Check if we need to reset
        if self.last_reset_date is None or now.date() > self.last_reset_date.date():
            if now.hour >= reset_hour:
                self.daily_pnl_pct = 0.0
                self.daily_start_equity = current_equity
                self.last_reset_date = now
                logger.info(f"📅 Daily stats reset. Starting equity: ${current_equity:.2f}")

    def update_daily_pnl(self, current_equity: float) -> None:
        """Update daily P&L tracking."""
        if self.daily_start_equity > 0:
            self.daily_pnl_pct = ((current_equity - self.daily_start_equity) / self.daily_start_equity) * 100

    def record_trade_result(self, pnl_pct: float) -> None:
        """Record trade result for circuit breaker."""
        if pnl_pct < 0:
            self.consecutive_losses += 1
            if self.consecutive_losses >= self.config.circuit_breaker_losses:
                pause_until = datetime.utcnow() + timedelta(minutes=self.config.circuit_breaker_pause_minutes)
                self.circuit_breaker_until = pause_until
                logger.warning(f"🔴 CIRCUIT BREAKER: {self.consecutive_losses} consecutive losses - pausing until {pause_until}")
        else:
            self.consecutive_losses = 0  # Reset on win

    def update_position(self, symbol: str, side: Optional[str]) -> None:
        """Update position tracking for correlation checks."""
        if side and side != "none":
            self.active_positions[symbol] = side
        else:
            if symbol in self.active_positions:
                del self.active_positions[symbol]

    def can_trade(self, symbol: str, side: str, current_equity: float) -> tuple[bool, str]:
        """Master check - can we take this trade? Returns (allowed, reason)."""
        logger.debug(f"🔍 RISK CHECK: {symbol} {side} | Positions: {self.active_positions}")

        # 1. Daily loss limit check
        self.update_daily_pnl(current_equity)
        if self.daily_pnl_pct <= self.config.daily_loss_limit_pct:
            return False, f"DAILY_LOSS_LIMIT: {self.daily_pnl_pct:.1f}% <= {self.config.daily_loss_limit_pct}%"

        # 2. Circuit breaker check
        if self.config.circuit_breaker_enabled and self.circuit_breaker_until:
            if datetime.utcnow() < self.circuit_breaker_until:
                remaining = (self.circuit_breaker_until - datetime.utcnow()).total_seconds() / 60
                return False, f"CIRCUIT_BREAKER: {remaining:.0f} min remaining ({self.consecutive_losses} losses)"
            else:
                self.circuit_breaker_until = None  # Reset
                self.consecutive_losses = 0
                logger.info("🟢 Circuit breaker reset - trading resumed")

        # 3. Time filter (if enabled)
        if self.config.time_filter_enabled:
            hour = datetime.utcnow().hour
            start_hour, end_hour = self.config.trading_hours_utc
            if not (start_hour <= hour < end_hour):
                return False, f"TIME_FILTER: Hour {hour} outside {start_hour}-{end_hour} UTC"

        # 4. Check if we already have a position on this symbol
        if symbol in self.active_positions:
            existing = self.active_positions[symbol]
            return False, f"ALREADY_IN_POSITION: {existing.upper()} on {symbol}"

        # 5. Correlation check - block opposite directions on correlated assets
        if self.config.correlation_check_enabled:
            has_conflict, conflict_reason = self._check_correlated_conflict(symbol, side)
            if has_conflict:
                return False, conflict_reason

        return True, "OK"

    def _check_correlated_conflict(self, symbol: str, side: str) -> tuple[bool, str]:
        """Check if taking this position conflicts with correlated assets.

        Returns (has_conflict, reason).
        Blocks opposite directions on correlated crypto assets.
        """
        # Find which correlation group this symbol belongs to
        symbol_group = None
        for group, symbols in CORRELATION_GROUPS.items():
            if symbol in symbols:
                symbol_group = group
                break

        if not symbol_group:
            return False, ""

        group_symbols = CORRELATION_GROUPS[symbol_group]
        opposite_side = "short" if side == "long" else "long"

        # Check for conflicts with existing positions
        for s, d in self.active_positions.items():
            if s in group_symbols and s != symbol and d == opposite_side:
                return True, f"CORRELATED_CONFLICT: Cannot {side.upper()} {symbol} while {s} is {d.upper()}"

        return False, ""

    def get_position_size_multiplier(self) -> float:
        """Get position size multiplier based on performance."""
        if not self.config.performance_sizing_enabled:
            return 1.0

        multiplier = 1.0

        # Check current streak from performance tracker
        metrics = self.perf_tracker.get_overall_metrics()
        current_streak = metrics.get("current_streak", 0)
        max_drawdown = metrics.get("max_drawdown_pct", 0)

        # Win streak bonus (max +50%)
        if current_streak > 0:
            bonus = min(current_streak, 2) * (self.config.win_streak_bonus_pct / 100)
            multiplier += bonus
            logger.info(f"📈 Win streak bonus: +{bonus*100:.0f}% (streak: {current_streak})")

        # Loss streak reduction (max -50%)
        elif current_streak < 0:
            reduction = min(abs(current_streak), 2) * (self.config.lose_streak_reduction_pct / 100)
            multiplier -= reduction
            logger.info(f"📉 Loss streak reduction: -{reduction*100:.0f}% (streak: {current_streak})")

        # Drawdown reduction
        if max_drawdown > self.config.drawdown_reduction_threshold_pct:
            dd_multiplier = self.config.drawdown_size_reduction_pct / 100
            multiplier *= dd_multiplier
            logger.warning(f"⚠️ Drawdown reduction: {dd_multiplier*100:.0f}% (DD: {max_drawdown:.1f}%)")

        # Clamp between 0.25 and 1.5
        return max(0.25, min(1.5, multiplier))

    def get_status(self) -> Dict[str, Any]:
        """Get current risk status for logging/display."""
        return {
            "daily_pnl_pct": round(self.daily_pnl_pct, 2),
            "consecutive_losses": self.consecutive_losses,
            "circuit_breaker_active": self.circuit_breaker_until is not None,
            "active_positions": dict(self.active_positions),
            "size_multiplier": round(self.get_position_size_multiplier(), 2)
        }


class TradingBot:
    """Main trading bot with LLM-driven swing trading strategy."""

    def __init__(self, hl_client: HyperliquidClient, llm_service: LLMService, config: BotConfig):
        self.hl = hl_client
        self.llm = llm_service
        self.config = config
        self.is_running = False
        self.last_signal: Optional[TradeSignal] = None

        # Timing - CONTINUOUS OPPORTUNITY SCANNING
        self.scan_interval = 15  # Scan for opportunities every 15 seconds
        self.full_analysis_interval = 300  # Full market analysis every 5 minutes (for caching)
        self.last_full_analysis_time: Dict[str, datetime] = {}  # Per-symbol last full analysis

        # Cooldowns - AGGRESSIVE SETTINGS for proactive trading
        self.last_trade_time: Dict[str, datetime] = {}
        self.last_trade_side: Dict[str, str] = {}
        self.last_trade_price: Dict[str, float] = {}  # Track exit price
        self.trade_cooldown_hours = 0.5  # 30 min general cooldown (was 1h)
        self.same_direction_cooldown_hours = 2  # 2h same-direction (was 4h)

        # ========== UNIFIED POSITION REGISTRY ==========
        # Single source of truth for all active positions
        self.positions: Dict[str, Position] = {}  # symbol -> Position

        # Legacy state (kept for compatibility during transition)
        self.active_thesis: Dict[str, Dict] = {}
        self.trailing_stops: Dict[str, Dict] = {}
        self.partial_taken: Dict[str, bool] = {}
        self.atr_cache: Dict[str, Dict] = {}
        self.pending_scales: Dict[str, Dict] = {}
        self.pyramid_adds: Dict[str, int] = {}
        self.pyramid_entries: Dict[str, List[Dict]] = {}

        # ========== POSITION STATE ==========
        self.positions: Dict[str, Dict] = {}  # Active positions: symbol -> position data
        self.last_trade_time: Dict[str, datetime] = {}  # Cooldown tracking

        # Proactive limit orders at S/R levels
        self.pending_limits: Dict[str, Dict] = {}  # key -> {order_id, level, side, size, sl, tp, placed_at}
        self.limit_ttl_minutes = 60  # Cancel unfilled orders after 60 min
        self.limit_max_orders = 2  # Max pending limit orders per symbol

        # MICRO INTELLIGENCE ENGINE - Professional market analysis
        self.micro_intel = MicroIntelligenceEngine()

        # PROACTIVE MICRO STRATEGY - Always-on momentum hunter
        self.proactive_micro = ProactiveMicroStrategy()
        self.proactive_micro_enabled = True  # Enable proactive scanning
        self.proactive_scan_interval_seconds = 30  # Scan every 30 seconds
        self.last_proactive_scan: Dict[str, datetime] = {}

        # Sniper system
        self.sniper = PositionSniper(hl_client, SniperConfig())
        self.use_sniper = True
        self.sniper_min_score = 50  # Increased from 35 - need higher quality setups
        # Level snipes: Place limit orders at strong S/R levels
        # SL/TP attached via place_limit_order_with_sltp (native TPSL grouping)
        self.level_snipe_enabled = False  # DISABLED - focus on quality entries, not auto-snipes
        self.pending_snipes: Dict[str, Dict] = {}
        self.snipe_order_ttl_minutes = 30

        # ========== ADAPTIVE ORDER MANAGEMENT ==========
        self.adaptive_orders_enabled = True
        self.level_shift_threshold_pct = 1.5  # Re-place order if level shifts > 1.5%
        self.adaptive_interval_minutes = 15  # Check every 15 min
        self.last_adaptive_check: Dict[str, datetime] = {}  # Per-symbol tracking

        # Position scaling
        self.scaling_enabled = True
        self.scale_tranches = 2
        self.scale_dip_pct = 0.5

        # Services
        self.perf_tracker = PerformanceTracker()
        self.trade_analyzer = TradeAnalyzer(self.perf_tracker)  # Learning system
        self.use_learning = True  # Enable learning-based filtering

        # Advanced learning components
        try:
            from performance_tracker import LLMTradeReviewer, AdaptiveParameterOptimizer, RegimePerformanceTracker
        except ImportError:
            from src.performance_tracker import LLMTradeReviewer, AdaptiveParameterOptimizer, RegimePerformanceTracker
        self.llm_reviewer = LLMTradeReviewer(self.perf_tracker, llm_service.anthropic_client)
        self.param_optimizer = AdaptiveParameterOptimizer(self.perf_tracker)
        self.regime_tracker = RegimePerformanceTracker(self.perf_tracker)
        self.last_weekly_review: Optional[datetime] = None

        # ML-based trade prediction
        try:
            from ml_learning import TradePredictor
        except ImportError:
            from src.ml_learning import TradePredictor
        self.ml_predictor = TradePredictor()
        self.use_ml_filter = True  # Enable ML-based filtering
        self.ml_min_probability = 0.55  # Min win probability to take trade

        # Whale Pattern ML Model - Learns from profitable whale trades
        try:
            from src.whale_ml_model import WhalePatternModel
            self.whale_ml = WhalePatternModel()
            try:
                self.whale_ml.load()
                logger.info(f"🐋 Whale ML loaded: {self.whale_ml.training_stats.get('val_accuracy', 0):.1%} accuracy")
            except FileNotFoundError:
                logger.info("🐋 Whale ML not trained yet. Run 'whale-train' to enable.")
            self.use_whale_ml_filter = True
            self.whale_ml_min_score = 0.4  # Lower threshold since model is very accurate
        except ImportError as e:
            logger.warning(f"Whale ML not available: {e}")
            self.whale_ml = None
            self.use_whale_ml_filter = False

        self.alpha_signals = AlphaSignalAggregator(
            hyperliquid_client=hl_client,
            hyperliquid_info=hl_client.info if hasattr(hl_client, 'info') else None
        )
        self.last_alpha_signals: Dict[str, Dict] = {}
        # Chart analyzer: DeepSeek text by default (cheap), Claude Vision only if explicitly enabled
        use_expensive_vision = config.use_claude_vision if hasattr(config, 'use_claude_vision') else False
        self.chart_analyzer = ChartAnalyzer(
            anthropic_client=llm_service.anthropic_client,
            deepseek_client=llm_service.deepseek_client,
            use_vision=use_expensive_vision
        )
        self.thinking_tracker = ThinkingTracker()
        # Enable visual analysis by default now (uses cheap DeepSeek)
        self.use_visual_analysis = config.use_visual_analysis if hasattr(config, 'use_visual_analysis') else True
        self.visual_analysis_cache: Dict[str, Dict] = {}
        self.visual_cache_ttl_minutes = 60

        # Track entry conditions for current trades (for learning)
        self.pending_entry_conditions: Dict[str, EntryConditions] = {}

        # Order Book Analyzer (L2 data for professional edge)
        self.orderbook_analyzer = OrderBookAnalyzer(
            info_client=hl_client.info if hasattr(hl_client, 'info') else None
        )
        self.use_orderbook_analysis = True

        # ========== MARKET REGIME ANALYSIS (DeepSeek) ==========
        self.market_regime_cache: Dict[str, Dict] = {}  # symbol -> regime data
        self.regime_cache_ttl_minutes = 15  # Refresh every 15 min
        self.last_regime_update: Dict[str, datetime] = {}

        # ========== PORTFOLIO RISK MANAGER ==========
        self.risk_manager = RiskManager(config, self.perf_tracker)

        # ========== DISCORD NOTIFIER (Multi-Channel) ==========
        # Sends ONLY market analysis (NO account data or transactions)
        import os
        discord_token = os.getenv("DISCORD_BOT_TOKEN")
        self.discord: Optional[DiscordNotifier] = None
        if discord_token:
            try:
                # Load all channels dynamically from env for ALL trading tickers
                channels = DiscordChannels.from_env(os.getenv)
                self.discord = DiscordNotifier(discord_token, channels=channels)
                # Log which tickers have channels configured
                configured = list(channels.signal_channels.keys())
                logger.info(f"✅ Discord notifier configured for {len(configured)} tickers: {configured}")
            except Exception as e:
                logger.warning(f"Discord setup failed: {e}")
        # Event-driven alerts (no periodic spam)
        self.last_discord_alert: Dict[str, datetime] = {}  # Track last alert per event type
        self.last_known_trend: Dict[str, str] = {}  # Track trend to detect flips
        self.alerted_sr_levels: Dict[str, set] = {}  # Track S/R levels already alerted

        # ========== PATTERN DETECTOR (Chart Patterns for Discord Alerts) ==========
        self.pattern_detector = PatternDetector()
        self.pattern_alert_cooldown_minutes = 30  # Don't spam same pattern
        self.last_pattern_alert: Dict[str, datetime] = {}  # Track last alert per pattern

        # ========== REAL-TIME MONITOR (WebSocket price streaming) ==========
        self.realtime_monitor: Optional[RealtimeMonitor] = None
        self.event_analyzer: Optional[EventDrivenAnalyzer] = None
        self.realtime_task: Optional[asyncio.Task] = None  # Background task for monitor

        # ========== CHART SCHEDULER (standalone mode when realtime disabled) ==========
        self.chart_scheduler = None
        self.chart_scheduler_task: Optional[asyncio.Task] = None

        # ========== WHALE POSITION MONITOR ==========
        self.whale_monitor_task: Optional[asyncio.Task] = None
        self.whale_monitor_interval: int = 60  # Check every 60 seconds
        self.last_whale_positions: Dict[str, Dict] = {}  # Track last known positions

        # ========== LEARNING DATA PERSISTENCE ==========
        self.learning_store = LearningDataStore()  # S/R exits & whale trades for learning

        # ========== SIGNAL LEARNING (from Discord alerts) ==========
        from .signal_learning import SignalLearner
        self.signal_learner = SignalLearner(hl_client=self.hl)
        logger.info("📚 Signal learner initialized for Discord alert training")

        # ========== COMPREHENSIVE LEARNING ENGINE ==========
        self.learning_engine = LearningEngine(hl_client=self.hl)
        self.last_learning_validation = datetime.utcnow()
        self.learning_validation_interval = timedelta(hours=1)  # Validate predictions hourly
        logger.info("🧠 Comprehensive learning engine initialized")

    # ========================================================================
    # CENTRALIZED STOP LOSS / TAKE PROFIT CALCULATOR
    # ========================================================================
    # ALL SL/TP calculations go through this ONE method.
    # Config: sl_margin_pct (3%), tp_rr_ratio (2:1), leverage per symbol
    #
    # POSITION-BASED stops: 3% margin loss with leverage factored in
    # Example BTC (40x): 3% margin loss = 0.075% price move
    # ========================================================================

    def get_leverage(self, symbol: str) -> int:
        """Get leverage for a symbol from centralized config."""
        return get_max_leverage(symbol)

    def calculate_sltp(self, symbol: str, entry_price: float, side: str,
                        volatility_regime: str = "normal") -> dict:
        """
        CENTRALIZED SL/TP CALCULATOR - ALL stop loss and take profit calculations go here.

        Stop losses are POSITION-BASED (% loss on margin), NOT ticker-based.
        With leverage factored in: price_move_% = margin_loss_% / leverage

        VOLATILITY ADAPTATION:
        - LOW volatility: Tighter SL (2%), smaller TP (3%) - scalp the range
        - NORMAL volatility: Standard SL (3%), normal TP (6%)
        - HIGH volatility: Wider SL (5%), larger TP (10%) - give room to breathe

        Example BTC (3% margin SL, 40x leverage):
        - Price move to trigger SL = 3% / 40 = 0.075%
        - If BTC at $100,000, SL triggers at $100,075 (short) or $99,925 (long)

        Args:
            symbol: Trading symbol (BTC, ETH, SOL)
            entry_price: Entry price
            side: "long" or "short"
            volatility_regime: "low", "normal", or "high"

        Returns:
            dict with: stop_loss, take_profit, sl_margin_pct, sl_price_pct, tp_margin_pct, leverage
        """
        leverage = self.get_leverage(symbol)
        base_sl = self.config.sl_margin_pct
        base_rr = self.config.tp_rr_ratio

        # === VOLATILITY REGIME ADAPTATION ===
        if volatility_regime == "low":
            # Low vol = tight range, use tighter stops and smaller targets
            sl_margin_pct = base_sl * 0.67  # 3% -> 2%
            rr_ratio = 1.5  # Aim for 1.5:1 (3% TP)
            vol_note = "LOW VOL: Tight SL, smaller TP"
        elif volatility_regime == "high":
            # High vol = wide swings, give more room
            sl_margin_pct = base_sl * 1.67  # 3% -> 5%
            rr_ratio = 2.0  # Keep 2:1 (10% TP)
            vol_note = "HIGH VOL: Wide SL, larger TP"
        else:  # normal
            sl_margin_pct = base_sl
            rr_ratio = base_rr
            vol_note = "NORMAL VOL: Standard SL/TP"

        # Convert margin % to price % (this is the key calculation)
        # Price move % = Margin loss % / Leverage
        sl_price_pct = sl_margin_pct / leverage
        sl_distance = entry_price * (sl_price_pct / 100)

        # TP based on R:R ratio
        tp_margin_pct = sl_margin_pct * rr_ratio
        tp_distance = sl_distance * rr_ratio

        # Calculate actual prices
        if side == "long":
            stop_loss = entry_price - sl_distance
            take_profit = entry_price + tp_distance
        else:  # short
            stop_loss = entry_price + sl_distance
            take_profit = entry_price - tp_distance

        # Round prices appropriately
        stop_loss = self.hl.round_price(symbol, stop_loss)
        take_profit = self.hl.round_price(symbol, take_profit)

        logger.debug(f"📐 SL/TP ({vol_note}): SL {sl_margin_pct:.1f}% margin ({sl_price_pct:.3f}% price), TP {tp_margin_pct:.1f}% margin")

        return {
            "stop_loss": stop_loss,
            "take_profit": take_profit,
            "sl_margin_pct": sl_margin_pct,
            "sl_price_pct": sl_price_pct,
            "tp_margin_pct": tp_margin_pct,
            "rr_ratio": rr_ratio,
            "leverage": leverage,
            "volatility_regime": volatility_regime
        }

    def calculate_breakeven_sl(self, symbol: str, entry_price: float, side: str) -> float:
        """
        Calculate break-even stop loss price (entry price + small buffer for fees).
        Called when position goes green to lock in entry.

        Args:
            symbol: Trading symbol
            entry_price: Original entry price
            side: "long" or "short"

        Returns:
            Break-even stop loss price
        """
        # Small buffer for fees/slippage (0.05% of entry)
        buffer = entry_price * 0.0005

        if side == "long":
            # For longs, SL just below entry
            be_sl = entry_price - buffer
        else:
            # For shorts, SL just above entry
            be_sl = entry_price + buffer

        return self.hl.round_price(symbol, be_sl)

    def _get_leverage_aware_sl(
        self,
        symbol: str,
        entry_price: float,
        side: str,
        strategy: str = "micro"
    ) -> tuple:
        """
        Calculate LEVERAGE-AWARE stop loss and take profit.

        CRITICAL: SL is based on MARGIN LOSS %, not ticker price %.

        Formula: price_move_% = margin_loss_% / leverage

        Example (BTC, 40x leverage, 3% margin SL):
        - Price move to trigger SL = 3% / 40 = 0.075%
        - If BTC at $100,000: SL at $99,925 (long) or $100,075 (short)
        - This means a $75 move triggers SL, not a $3,000 move!

        Args:
            symbol: Trading symbol (BTC, ETH, SOL)
            entry_price: Entry price
            side: "long" or "short"
            strategy: "micro" (3% margin SL) - MACRO removed

        Returns:
            tuple: (stop_loss, take_profit, sl_price_pct, sl_margin_pct)
        """
        leverage = self.get_leverage(symbol)

        # MICRO: 3% margin loss (position-based, not ticker-based)
        sl_margin_pct = 3.0

        # CRITICAL CALCULATION: Convert margin % to price %
        # price_move_% = margin_loss_% / leverage
        sl_price_pct = sl_margin_pct / leverage
        sl_distance = entry_price * (sl_price_pct / 100)

        # R:R = 2:1 (TP at 2x the distance)
        rr_ratio = 2.0
        tp_distance = sl_distance * rr_ratio

        # Calculate actual prices
        if side == "long":
            stop_loss = entry_price - sl_distance
            take_profit = entry_price + tp_distance
        else:  # short
            stop_loss = entry_price + sl_distance
            take_profit = entry_price - tp_distance

        # Round prices
        stop_loss = self.hl.round_price(symbol, stop_loss)
        take_profit = self.hl.round_price(symbol, take_profit)

        return (stop_loss, take_profit, sl_price_pct, sl_margin_pct)

    async def start(self) -> None:
        """Start the trading bot."""
        logger.info("Starting Trading Bot...")

        # Connect to exchange
        connected = await self.hl.connect()
        if not connected:
            raise RuntimeError("Failed to connect to Hyperliquid")

        # Re-initialize components now that we're connected
        # (hl.info is None before connect() is called)
        self.alpha_signals = AlphaSignalAggregator(
            hyperliquid_client=self.hl,
            hyperliquid_info=self.hl.info
        )
        logger.info("✅ Alpha signals initialized")

        # Re-initialize order book analyzer with the connected info client
        self.orderbook_analyzer = OrderBookAnalyzer(info_client=self.hl.info)
        logger.info("✅ Order book analyzer initialized")

        # Get initial state
        state = self.hl.get_account_state()
        logger.info(f"Account equity: ${state['equity']:.2f}")

        # Initialize performance tracking
        self.perf_tracker.set_starting_equity(state['equity'])

        # === SYNC RISK MANAGER WITH EXCHANGE POSITIONS ===
        await self._sync_risk_manager_with_exchange()

        # === INITIALIZE LEARNING SYSTEM ===
        if self.use_learning:
            logger.info("🧠 Initializing learning system...")
            analysis = self.trade_analyzer.analyze_patterns()
            if analysis.get("status") == "analyzed":
                logger.info(self.trade_analyzer.get_learning_summary())
            else:
                logger.info(f"🧠 Learning: Need {self.trade_analyzer.min_trades_for_learning}+ trades to start learning (have {analysis.get('trades_analyzed', 0)})")

        # === CONNECT DISCORD NOTIFIER ===
        if self.discord:
            try:
                # Set LLM service for assistant channel responses
                self.discord.set_llm_service(self.llm)

                connected = await self.discord.connect()
                if connected:
                    logger.info("✅ Discord bot connected - sending market analysis")
                    # Send startup message (NO account/position data - only market symbols)
                    await self.discord.send_bot_status(
                        f"🤖 **Market Scanner Started**\n"
                        f"📊 Watching: {', '.join(self.config.symbols)}\n"
                        f"🔍 Scanning for setups..."
                    )
                else:
                    logger.warning("Discord connection failed - continuing without Discord")
            except Exception as e:
                logger.warning(f"Discord error: {e}")

        # === START REAL-TIME MONITOR (WebSocket price streaming) ===
        if self.config.realtime_monitor_enabled:
            await self._start_realtime_monitor()

        # === START CHART SCHEDULER (runs even without realtime monitor) ===
        if self.discord and not self.config.realtime_monitor_enabled:
            # Start chart scheduler independently if realtime monitor is disabled
            await self._start_chart_scheduler_standalone()

        # === START WHALE POSITION MONITOR ===
        if self.discord:
            await self._start_whale_monitor()

        # === START DATABASE OUTCOME TRACKING ===
        # Track outcomes for all signals/events in SQLite
        self.outcome_tracking_task = asyncio.create_task(self._run_outcome_tracking())
        logger.info("📀 Database outcome tracking started")

        self.is_running = True
        logger.info(f"Bot started - Trading {', '.join(self.config.symbols)}")

    async def stop(self) -> None:
        """Stop the trading bot."""
        logger.info("Stopping Trading Bot...")
        self.is_running = False

        # Stop realtime monitor
        if self.realtime_monitor:
            await self.realtime_monitor.stop()
            if self.realtime_task:
                self.realtime_task.cancel()

        # Stop chart scheduler
        if self.event_analyzer:
            await self.event_analyzer.stop_chart_scheduler()

        # Stop whale monitor
        if self.whale_monitor_task:
            self.whale_monitor_task.cancel()

        # Stop outcome tracking
        if hasattr(self, 'outcome_tracking_task') and self.outcome_tracking_task:
            self.outcome_tracking_task.cancel()

        # Disconnect Discord
        if self.discord:
            await self.discord.disconnect()

    async def _start_realtime_monitor(self) -> None:
        """Start the real-time WebSocket price monitor."""
        try:
            # Create event handler callback
            async def handle_price_event(event: PriceEvent):
                """Handle significant price events with AI analysis."""
                if self.event_analyzer:
                    await self.event_analyzer.handle_event(event)

            # Initialize monitor
            self.realtime_monitor = RealtimeMonitor(
                symbols=self.config.symbols,
                testnet=self.hl.testnet,
                on_event=handle_price_event
            )

            # Configure thresholds from config
            self.realtime_monitor.sr_proximity_pct = self.config.realtime_sr_proximity_pct
            self.realtime_monitor.volatility_threshold_pct = self.config.realtime_volatility_threshold_pct

            # Initialize event analyzer (triggers AI on events)
            self.event_analyzer = EventDrivenAnalyzer(
                chart_analyzer=self.chart_analyzer,
                llm_service=self.llm,  # TradingBot uses self.llm, not self.llm_service
                hl_client=self.hl,
                discord=self.discord,
                signal_learner=self.signal_learner  # For learning from chart signals
            )

            # Start monitor in background task
            self.realtime_task = asyncio.create_task(self.realtime_monitor.start())
            logger.info("🔴 LIVE: Real-time price monitor started")

            # Start chart scheduler (30min 5m charts, 24h daily charts)
            if self.discord:
                await self.event_analyzer.start_chart_scheduler()

            # Start signal learning outcome tracking
            if self.signal_learner:
                await self.signal_learner.start_outcome_tracking()
                logger.info("📚 Signal learning outcome tracking started")

        except Exception as e:
            logger.error(f"Failed to start realtime monitor: {e}")

    def update_realtime_sr_levels(self, symbol: str, supports: List[float], resistances: List[float]) -> None:
        """Update S/R levels for the realtime monitor (call after computing S/R)."""
        if self.realtime_monitor:
            self.realtime_monitor.set_sr_levels(symbol, supports, resistances)

    async def _start_chart_scheduler_standalone(self) -> None:
        """Start chart scheduler without the realtime monitor.

        This allows scheduled charts to be posted even when WebSocket monitoring is disabled.
        """
        try:
            from src.chart_scheduler import ChartScheduler

            self.chart_scheduler = ChartScheduler(
                hl_client=self.hl,
                discord_notifier=self.discord,
                llm_service=self.llm,  # TradingBot uses self.llm, not self.llm_service
                signal_learner=self.signal_learner
            )

            # Start scheduler as background task
            self.chart_scheduler_task = asyncio.create_task(
                self.chart_scheduler.run_scheduler()
            )
            logger.info("📊 Chart scheduler started (30min for 5m charts, 24h for daily)")

            # Also start signal learning outcome tracking
            if self.signal_learner:
                await self.signal_learner.start_outcome_tracking()
                logger.info("📚 Signal learning outcome tracking started")

        except Exception as e:
            logger.error(f"Failed to start chart scheduler: {e}")

    async def _run_outcome_tracking(self) -> None:
        """Background loop to track signal outcomes in database.

        Runs every 5 minutes to process pending outcome checks:
        - Whale events (5m, 1h after)
        - Chart signals (1h, 4h, 24h after)
        - S/R breakouts (5m, 15m, 1h after)
        """
        logger.info("📀 Starting outcome tracking loop...")

        while self.is_running:
            try:
                db = get_db()

                # Process pending outcomes using current prices
                def get_current_price(symbol: str) -> float:
                    return self.hl.get_price(symbol)

                processed = db.process_pending_outcomes(get_current_price)

                if processed > 0:
                    logger.info(f"📀 Processed {processed} signal outcomes")

                # Wait 5 minutes before next check
                await asyncio.sleep(300)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Outcome tracking error: {e}")
                await asyncio.sleep(60)

    async def _start_whale_monitor(self) -> None:
        """Start the whale position monitor in background."""
        if not self.discord or not hasattr(self.alpha_signals, 'whale_tracker'):
            return

        logger.info("🐋 Starting whale position monitor...")
        self.whale_monitor_task = asyncio.create_task(self._whale_monitor_loop())

    async def _whale_monitor_loop(self) -> None:
        """Background loop to monitor whale positions every 60 seconds."""
        while self.is_running:
            try:
                await self._check_whale_positions()
                await asyncio.sleep(self.whale_monitor_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Whale monitor error: {e}")
                await asyncio.sleep(30)

    async def _check_whale_positions(self) -> None:
        """Check for whale position changes and send Discord alerts.

        Sends alerts to:
        1. #whales channel (all whale activity)
        2. Ticker-specific channel for all trading tickers

        Also records events for bot learning.
        """
        if not self.discord:
            return
        if not hasattr(self.alpha_signals, 'whale_tracker') or not self.alpha_signals.whale_tracker:
            return

        try:
            whale_tracker = self.alpha_signals.whale_tracker
            scan = whale_tracker.scan_all_whales()

            new_positions = scan.get("new_positions", [])
            closed_positions = scan.get("closed_positions", [])

            now = datetime.utcnow()

            # Track symbols we trade for ticker-specific alerts
            tracked_symbols = set(TRADING_TICKERS)

            # Send alerts for new positions
            for pos in new_positions:
                whale_name = pos.get("whale", "Unknown")
                symbol = pos.get("symbol", "?")
                side = pos.get("side", "?")

                # Rate limit: 30 min between same whale/symbol/side alerts
                alert_key = f"whale_open_{whale_name}_{symbol}_{side}"
                last_alert = self.last_discord_alert.get(alert_key, datetime.min)

                if (now - last_alert).total_seconds() > 1800:
                    self.last_discord_alert[alert_key] = now

                    # 1. Send to #whales channel
                    await self.discord.send_whale_position_alert(pos, action="opened")

                    # 2. Also send to ticker-specific channel for all trading tickers
                    if symbol in tracked_symbols:
                        await self._send_whale_to_ticker_channel(pos, action="opened")

                    # 3. Record for learning
                    self.learning_store.record_whale_event(pos, action="opened")

                    logger.info(f"🐋 Discord: {whale_name} OPENED {side.upper()} {symbol}")

            # Send alerts for closed positions
            for pos in closed_positions:
                whale_name = pos.get("whale", "Unknown")
                symbol = pos.get("symbol", "?")
                side = pos.get("side", "?")

                alert_key = f"whale_close_{whale_name}_{symbol}_{side}"
                last_alert = self.last_discord_alert.get(alert_key, datetime.min)

                if (now - last_alert).total_seconds() > 1800:
                    self.last_discord_alert[alert_key] = now

                    # 1. Send to #whales channel
                    await self.discord.send_whale_position_alert(pos, action="closed")

                    # 2. Also send to ticker-specific channel for all trading tickers
                    if symbol in tracked_symbols:
                        await self._send_whale_to_ticker_channel(pos, action="closed")

                    # 3. Record for learning
                    self.learning_store.record_whale_event(pos, action="closed")

                    logger.info(f"🐋 Discord: {whale_name} CLOSED {side.upper()} {symbol}")

            # Log whale activity summary periodically
            if new_positions or closed_positions:
                logger.info(f"🐋 Whale scan: {len(new_positions)} new, {len(closed_positions)} closed positions")

        except Exception as e:
            logger.error(f"Whale position check failed: {e}")

    async def _send_whale_to_ticker_channel(self, pos: Dict, action: str) -> None:
        """Send whale alert to ticker-specific channel for all trading tickers.

        This provides context for trading decisions on that ticker.
        """
        if not self.discord:
            return

        whale_name = pos.get("whale", "Unknown")
        symbol = pos.get("symbol", "?")
        side = pos.get("side", "?").upper()
        size = abs(pos.get("size", 0))
        entry = pos.get("entry_price", 0)
        leverage = pos.get("leverage", 1)
        notional = pos.get("notional_usd", 0)

        # Format notional nicely
        if notional >= 1_000_000:
            notional_str = f"${notional/1_000_000:.1f}M"
        elif notional >= 1_000:
            notional_str = f"${notional/1_000:.0f}K"
        else:
            notional_str = f"${notional:,.0f}"

        side_emoji = "🟢" if side == "LONG" else "🔴"
        action_emoji = "🐋" if action == "opened" else "💨"

        if action == "opened":
            message = f"{action_emoji} **Whale {action}** {side_emoji}{side} ${symbol} — {notional_str} @ ${entry:,.0f} ({leverage}x)"
        else:
            pnl_pct = pos.get("pnl_pct", 0)
            pnl_emoji = "✅" if pnl_pct > 0 else "❌"
            message = f"{action_emoji} **Whale closed** {side_emoji}{side} ${symbol} — {pnl_emoji} {pnl_pct:+.1f}%"

        # Get the channel for this symbol
        channel_id = self.discord._get_channel_for_symbol(symbol)
        if channel_id:
            await self.discord._queue_or_send(channel_id, message)

    async def _sync_risk_manager_with_exchange(self) -> None:
        """Sync risk manager position tracking with actual exchange positions.

        This ensures the risk manager knows about all open positions,
        especially after bot restarts. This is CRITICAL for consistent
        behavior across all symbols.
        """
        logger.info("🔄 Syncing risk manager with exchange positions...")

        state = self.hl.get_account_state()
        synced_count = 0

        # First, clear all stale positions in risk manager
        self.risk_manager.active_positions.clear()

        for pos in state.get("positions", []):
            szi = float(pos.get("szi", 0) or 0)
            if szi == 0:
                continue

            symbol = pos.get("coin", "")
            if not symbol:
                continue

            side = "long" if szi > 0 else "short"
            entry_price = float(pos.get("entryPx", 0) or 0)

            # Update risk manager
            self.risk_manager.update_position(symbol, side)
            synced_count += 1
            logger.info(f"   ✅ {symbol}: {side.upper()} @ ${entry_price:,.0f}")

        if synced_count > 0:
            logger.info(f"🔄 Synced {synced_count} positions with risk manager")
        else:
            logger.info("🔄 No open positions to sync")

        # Log current risk manager state
        logger.info(f"📊 Risk Manager State: {self.risk_manager.active_positions}")

    async def run(self) -> None:
        """Main bot loop - CONTINUOUS OPPORTUNITY SCANNING.

        NO FIXED DECISION INTERVAL - scans continuously and trades immediately
        when a high-quality opportunity is detected.

        MICRO STRATEGY: 5m/15m/30m timeframes, hold 15min-1d
        - Continuous scanning every 15 seconds
        - Immediate entry when opportunity score is high
        - DeepSeek for signal analysis (cached to reduce API calls)
        - Quant scoring for entry validation
        """
        logger.info(f"🔄 CONTINUOUS MODE: Scanning every {self.scan_interval}s, trading on opportunity")

        while self.is_running:
            try:
                # Run volatility monitor (risk management)
                await self._volatility_monitor()

                # Check snipe order fills
                if self.level_snipe_enabled and self.pending_snipes:
                    await self._check_snipe_fills()

                # Adaptive order management - re-evaluate pending limits if market changed
                if self.adaptive_orders_enabled:
                    for symbol in self.config.symbols:
                        has_orders = any(k.startswith(f"{symbol}_") for k in self.pending_limits)
                        has_snipes = bool(self.pending_snipes.get(symbol))

                        if has_orders or has_snipes:
                            try:
                                market_data = await self._gather_market_data_async(symbol)
                                if market_data:
                                    await self._check_and_adapt_pending_orders(symbol, market_data, has_orders, False)
                            except Exception as e:
                                logger.debug(f"Adaptive check skipped for {symbol}: {e}")

                # CONTINUOUS OPPORTUNITY SCAN - check all symbols for opportunities
                await self._continuous_opportunity_scan()

                # Track alpha call outcomes (for learning which patterns work)
                await self._track_alpha_call_outcomes()

                # Run learning validation cycle (hourly)
                await self._run_learning_validation()

                await asyncio.sleep(self.scan_interval)
            except Exception as e:
                logger.error(f"Error in bot loop: {e}", exc_info=True)
                await asyncio.sleep(5)

    async def _continuous_opportunity_scan(self) -> None:
        """Continuously scan for trading opportunities and act immediately.

        This replaces the fixed-interval _tick() approach. We:
        1. Quick-scan each symbol for opportunity signals
        2. If opportunity score is HIGH, do full analysis and potentially trade
        3. Use cached data for LLM calls to avoid rate limits
        """
        scan_results = []
        for symbol in self.config.symbols:
            try:
                # Check if we're already in a position for this symbol
                pos = self._get_position_info(symbol)
                has_position = pos["side"] != "none"

                if has_position:
                    # Manage existing position (trailing stops, etc)
                    market_data = await self._gather_market_data_async(symbol)
                    if market_data:
                        await self._manage_position(symbol, market_data)
                    scan_results.append(f"{symbol}:POS")
                    continue

                # === QUICK OPPORTUNITY CHECK (lightweight) ===
                quick_signal = await self._quick_opportunity_check(symbol)

                # Log scan result for visibility
                score = quick_signal.get('score', 0)
                direction = quick_signal.get('direction', 'neutral')[:1].upper()
                scan_results.append(f"{symbol}:{score}{direction}")

                if quick_signal["has_opportunity"]:
                    logger.info(f"\n{'='*40} OPPORTUNITY: {symbol} {'='*40}")
                    logger.info(f"⚡ Quick signal: {quick_signal['direction'].upper()} | Score: {quick_signal['score']}/100 | Reason: {quick_signal['reason']}")

                    # Full analysis and potential trade
                    await self._execute_opportunity(symbol, quick_signal)

            except Exception as e:
                scan_results.append(f"{symbol}:ERR")
                logger.debug(f"Scan error for {symbol}: {e}")

        # Log compact scan summary
        logger.info(f"🔍 Scan: {' | '.join(scan_results)} (≥30 triggers analysis)")

    async def _quick_opportunity_check(self, symbol: str) -> Dict[str, Any]:
        """Fast, lightweight check for trading opportunity.

        Uses minimal API calls to detect:
        - Price at key S/R level
        - Strong momentum shift
        - Orderbook imbalance spike
        - Whale activity

        Returns dict with has_opportunity, direction, score, reason
        """
        try:
            # Get current price
            price = self.hl.get_price(symbol)
            if not price:
                return {"has_opportunity": False, "direction": "neutral", "score": 0, "reason": "No price"}

            # Get 5m candles for quick momentum check
            candles_5m = self.hl.get_candles(symbol, interval="5m", limit=20)
            if not candles_5m or len(candles_5m) < 10:
                return {"has_opportunity": False, "direction": "neutral", "score": 0, "reason": "No candles"}

            score = 0
            signals = []
            direction = "neutral"

            # === 1. MOMENTUM CHECK (last 3 candles) ===
            recent = candles_5m[-3:]
            momentum_up = all(c["close"] > c["open"] for c in recent)
            momentum_down = all(c["close"] < c["open"] for c in recent)

            if momentum_up:
                score += 25
                signals.append("3-bar bullish momentum")
                direction = "long"
            elif momentum_down:
                score += 25
                signals.append("3-bar bearish momentum")
                direction = "short"

            # === 2. VOLUME SPIKE CHECK ===
            avg_volume = sum(c.get("volume", 0) for c in candles_5m[-10:-1]) / 9
            last_volume = candles_5m[-1].get("volume", 0)
            if avg_volume > 0 and last_volume > avg_volume * 2:
                score += 20
                signals.append(f"Volume spike ({last_volume/avg_volume:.1f}x)")

            # === 3. ORDERBOOK IMBALANCE ===
            orderbook = self.hl.get_orderbook(symbol)
            bids = orderbook.get("bids", [])
            asks = orderbook.get("asks", [])

            if bids and asks:
                # Handle both dict format {'px': x, 'sz': y} and list format [px, sz]
                def get_size(entry):
                    if isinstance(entry, dict):
                        return float(entry.get('sz', 0))
                    return float(entry[1]) if len(entry) > 1 else 0

                bid_vol = sum(get_size(b) for b in bids[:5])
                ask_vol = sum(get_size(a) for a in asks[:5])
                total = bid_vol + ask_vol

                if total > 0:
                    imbalance = (bid_vol - ask_vol) / total
                    if imbalance > 0.3:
                        score += 20
                        signals.append(f"OB bid imbalance ({imbalance:.0%})")
                        if direction == "neutral":
                            direction = "long"
                    elif imbalance < -0.3:
                        score += 20
                        signals.append(f"OB ask imbalance ({imbalance:.0%})")
                        if direction == "neutral":
                            direction = "short"

            # === 4. RSI EXTREME CHECK ===
            closes = [c["close"] for c in candles_5m]
            if len(closes) >= 14:
                gains = []
                losses = []
                for i in range(1, len(closes)):
                    diff = closes[i] - closes[i-1]
                    if diff > 0:
                        gains.append(diff)
                        losses.append(0)
                    else:
                        gains.append(0)
                        losses.append(abs(diff))

                avg_gain = sum(gains[-14:]) / 14
                avg_loss = sum(losses[-14:]) / 14

                if avg_loss > 0:
                    rs = avg_gain / avg_loss
                    rsi = 100 - (100 / (1 + rs))

                    if rsi < 25:
                        score += 25
                        signals.append(f"RSI oversold ({rsi:.0f})")
                        if direction == "neutral":
                            direction = "long"
                    elif rsi > 75:
                        score += 25
                        signals.append(f"RSI overbought ({rsi:.0f})")
                        if direction == "neutral":
                            direction = "short"

            # === 5. S/R LEVEL PROXIMITY ===
            # Quick S/R from recent highs/lows
            highs = [c["high"] for c in candles_5m[-20:]]
            lows = [c["low"] for c in candles_5m[-20:]]
            recent_high = max(highs)
            recent_low = min(lows)

            dist_to_high = (recent_high - price) / price
            dist_to_low = (price - recent_low) / price

            if dist_to_low < 0.003:  # Within 0.3% of recent low
                score += 15
                signals.append(f"Near support ${recent_low:.2f}")
                if direction == "neutral":
                    direction = "long"
            elif dist_to_high < 0.003:  # Within 0.3% of recent high
                score += 15
                signals.append(f"Near resistance ${recent_high:.2f}")
                if direction == "neutral":
                    direction = "short"

            # Determine if this is a real opportunity
            # Lower threshold (30) to be more active, full analysis still filters
            has_opportunity = score >= 30 and direction != "neutral"

            return {
                "has_opportunity": has_opportunity,
                "direction": direction,
                "score": score,
                "reason": ", ".join(signals) if signals else "No signals",
                "price": price
            }

        except Exception as e:
            logger.debug(f"Quick check error for {symbol}: {e}")
            return {"has_opportunity": False, "direction": "neutral", "score": 0, "reason": str(e)}

    async def _execute_opportunity(self, symbol: str, quick_signal: Dict) -> None:
        """Execute a trading opportunity after quick signal detection.

        Does full analysis to confirm the opportunity before trading.
        Uses the same logic as _tick but for a single symbol.
        """
        # Full market data gathering
        market_data = await self._gather_market_data_async(symbol)
        if not market_data:
            logger.warning(f"Failed to gather market data for {symbol}")
            return

        # Add quick signal info to market data
        market_data["quick_signal"] = quick_signal
        market_data["quick_direction"] = quick_signal.get("direction", "neutral")
        market_data["quick_score"] = quick_signal.get("score", 0)

        # Run full tick analysis for this single symbol
        # We create a temporary symbols list with just this symbol
        original_symbols = self.config.symbols
        self.config.symbols = [symbol]
        try:
            await self._tick()
        finally:
            self.config.symbols = original_symbols

    async def _volatility_monitor(self) -> None:
        """HANDS-OFF position monitor - exchange SL/TP handles exits.

        THIS MONITOR DOES NOT CLOSE POSITIONS.
        It only:
        1. Logs position status
        2. Checks if exchange closed the position (SL/TP hit)
        3. Cleans up tracking if position was closed by exchange

        ALL exits happen via native SL/TP orders on Hyperliquid.
        """
        state = self.hl.get_account_state()

        for pos in state.get("positions", []):
            szi = float(pos.get("szi", 0) or 0)
            if szi == 0:
                continue

            symbol = pos.get("coin", "?")
            entry_price = float(pos.get("entryPx", 0) or 0)
            current_price = self.hl.get_price(symbol) or entry_price
            side = "long" if szi > 0 else "short"

            if entry_price <= 0:
                continue

            # Get full position info with margin-based P&L
            pos_info = self._get_position_info(symbol)
            pnl_pct = pos_info.get("position_pnl_pct", 0)
            leverage = pos_info.get("leverage", 1)

            # Get position tracking data
            pos_data = self.positions.get(symbol) or self.positions.get(symbol) or {}
            current_sl = pos_data.get("trailing_stop", pos_data.get("stop_loss", 0))
            current_tp = pos_data.get("current_tp_price", pos_data.get("take_profit", 0))

            # Log position status (no action taken)
            logger.info(f"📊 {symbol} {side.upper()}: {pnl_pct:+.2f}% | Price: ${current_price:,.2f} | SL: ${current_sl:,.2f} | TP: ${current_tp:,.2f}")

    def _check_atr_stop(self, symbol: str, side: str, entry_price: float, current_price: float) -> tuple:
        """Check if ATR-based stop is triggered. Returns (triggered, stop_price)."""
        if not self.config.use_atr_stops:
            return False, 0.0

        # Get or calculate ATR stop
        atr_info = self.atr_cache.get(symbol, {})
        atr_stop = atr_info.get("stop_price", 0)

        if not atr_stop:
            # Calculate fresh ATR stop
            atr = self._get_current_atr(symbol)
            if atr and atr > 0:
                atr_distance = atr * self.config.atr_stop_multiplier
                # Cap at max stop percentage
                max_distance = entry_price * (self.config.atr_max_stop_pct / 100)
                atr_distance = min(atr_distance, max_distance)

                if side == "long":
                    atr_stop = entry_price - atr_distance
                else:
                    atr_stop = entry_price + atr_distance

                self.atr_cache[symbol] = {
                    "atr": atr,
                    "stop_price": atr_stop,
                    "timestamp": datetime.utcnow()
                }
                logger.info(f"📐 ATR Stop set for {symbol}: ${atr_stop:.2f} (ATR: ${atr:.2f})")

        # Check if stop hit
        if atr_stop > 0:
            if side == "long" and current_price <= atr_stop:
                return True, atr_stop
            elif side == "short" and current_price >= atr_stop:
                return True, atr_stop

        return False, atr_stop

    def _get_current_atr(self, symbol: str) -> float:
        """Get current ATR for symbol from recent candles."""
        try:
            candles = self.hl.get_candles(symbol, interval="1h", limit=20)
            if len(candles) < 14:
                return 0.0

            # Calculate ATR manually
            true_ranges = []
            for i in range(1, len(candles)):
                high = candles[i].get("high", 0)
                low = candles[i].get("low", 0)
                prev_close = candles[i-1].get("close", 0)

                tr = max(
                    high - low,
                    abs(high - prev_close),
                    abs(low - prev_close)
                )
                true_ranges.append(tr)

            # Simple moving average of TR
            atr = sum(true_ranges[-14:]) / 14
            return atr
        except Exception as e:
            logger.error(f"Failed to calculate ATR for {symbol}: {e}")
            return 0.0

    def _update_trailing_stop(self, symbol: str, side: str, current_price: float, pnl_pct: float) -> bool:
        """Update trailing stop and return True if triggered."""
        trail_info = self.trailing_stops.get(symbol, {
            "activated": False,
            "high_water_mark": current_price,
            "stop_price": 0
        })

        # Check if we should activate trailing stop
        if not trail_info["activated"] and pnl_pct >= self.config.trailing_stop_activation_pct:
            trail_info["activated"] = True
            trail_info["high_water_mark"] = current_price
            trail_distance = current_price * (self.config.trailing_stop_distance_pct / 100)
            if side == "long":
                trail_info["stop_price"] = current_price - trail_distance
            else:
                trail_info["stop_price"] = current_price + trail_distance
            self.trailing_stops[symbol] = trail_info
            logger.info(f"✅ TRAILING STOP ACTIVATED for {symbol} at +{pnl_pct:.1f}%")
            logger.info(f"   High: ${current_price:.2f}, Stop: ${trail_info['stop_price']:.2f}")
            return False

        # Update high water mark and trailing stop if activated
        if trail_info["activated"]:
            if side == "long" and current_price > trail_info["high_water_mark"]:
                trail_info["high_water_mark"] = current_price
                trail_distance = current_price * (self.config.trailing_stop_distance_pct / 100)
                trail_info["stop_price"] = current_price - trail_distance
                self.trailing_stops[symbol] = trail_info
                logger.debug(f"📈 Trail updated: HWM ${current_price:.2f}, Stop ${trail_info['stop_price']:.2f}")
            elif side == "short" and current_price < trail_info["high_water_mark"]:
                trail_info["high_water_mark"] = current_price
                trail_distance = current_price * (self.config.trailing_stop_distance_pct / 100)
                trail_info["stop_price"] = current_price + trail_distance
                self.trailing_stops[symbol] = trail_info
                logger.debug(f"📉 Trail updated: HWM ${current_price:.2f}, Stop ${trail_info['stop_price']:.2f}")

            # Check if trailing stop hit
            if side == "long" and current_price <= trail_info["stop_price"]:
                return True
            elif side == "short" and current_price >= trail_info["stop_price"]:
                return True

        return False

    async def _check_partial_profit(self, symbol: str, side: str, current_size: float, pnl_pct: float) -> None:
        """Take partial profit at first target (50% of position)."""
        # Skip if already taken partial or not at target
        if self.partial_taken.get(symbol, False):
            return

        if pnl_pct < self.config.partial_profit_target_pct:
            return

        # Calculate partial size (50% of current position)
        partial_size = current_size * (self.config.partial_profit_pct / 100)
        if partial_size * self.hl.get_price(symbol) < self.config.min_order_value_usd:
            logger.info(f"Partial profit size too small for {symbol}, skipping")
            return

        logger.info(f"💰 PARTIAL PROFIT: Taking {self.config.partial_profit_pct:.0f}% off {symbol} at +{pnl_pct:.1f}%")

        # Close partial position
        close_side = "sell" if side == "long" else "buy"
        result = self.hl.place_market_order(symbol, close_side, partial_size, reduce_only=True)

        if result.get("success"):
            self.partial_taken[symbol] = True
            logger.info(f"✅ Partial profit taken: {partial_size:.6f} {symbol}")
            # Update thesis with partial info
            if symbol in self.active_thesis:
                self.active_thesis[symbol]["partial_taken"] = True
                self.active_thesis[symbol]["partial_pnl_pct"] = pnl_pct
        else:
            logger.error(f"Failed to take partial profit: {result.get('error')}")

    def _get_trading_session(self) -> tuple[str, float, bool]:
        """Get current trading session and position size multiplier.

        Returns:
            tuple: (session_name, size_multiplier, is_good_time)

        Sessions:
        - Asia:   00:00-08:00 UTC (lower volatility)
        - Europe: 08:00-14:00 UTC (good setups)
        - US:     14:00-21:00 UTC (highest volume)
        - US/EU Overlap: 14:00-17:00 UTC (BEST time)
        - Dead Zone: 21:00-00:00 UTC (avoid)
        """
        hour = datetime.utcnow().hour

        # US/EU Overlap - BEST trading time
        if 14 <= hour < 17:
            return "US/EU Overlap", self.config.session_size_mult_overlap, True

        # US Session
        elif 14 <= hour < 21:
            return "US", self.config.session_size_mult_us, True

        # Europe Session
        elif 8 <= hour < 14:
            return "Europe", self.config.session_size_mult_europe, True

        # Asia Session
        elif 0 <= hour < 8:
            return "Asia", self.config.session_size_mult_asia, True

        # Dead Zone (21:00-00:00 UTC)
        else:
            if self.config.avoid_dead_zone:
                return "Dead Zone", 0.0, False  # 0.0 = don't trade
            return "Dead Zone", 0.5, True  # If trading allowed, use small size

    def _is_on_cooldown(self, symbol: str, new_side: str = None, current_price: float = None) -> bool:
        """Check if symbol is on trade cooldown or blocked from same-direction re-entry.

        Prevents:
        - Re-entering too quickly after a trade
        - Re-entering same direction at a worse price
        """
        if symbol not in self.last_trade_time:
            return False

        elapsed_hours = (datetime.utcnow() - self.last_trade_time[symbol]).total_seconds() / 3600

        # General cooldown - minimum time between trades
        if elapsed_hours < self.trade_cooldown_hours:
            return True

        # Block same-direction re-entry for cooldown period
        if new_side and symbol in self.last_trade_side:
            if self.last_trade_side[symbol] == new_side:
                # Time-based cooldown
                if elapsed_hours < self.same_direction_cooldown_hours:
                    return True

                # Price-based check: Don't re-enter at worse price
                if current_price and symbol in self.last_trade_price:
                    last_price = self.last_trade_price[symbol]
                    if new_side == "long" and current_price > last_price * 1.005:  # 0.5% worse
                        logger.info(f"BLOCKED: Would re-enter LONG at ${current_price:.2f} > exit ${last_price:.2f}")
                        return True
                    if new_side == "short" and current_price < last_price * 0.995:  # 0.5% worse
                        logger.info(f"BLOCKED: Would re-enter SHORT at ${current_price:.2f} < exit ${last_price:.2f}")
                        return True

        return False

    def _record_trade(self, symbol: str, side: str = None, exit_price: float = None) -> None:
        """Record that a trade was made for cooldown tracking."""
        self.last_trade_time[symbol] = datetime.utcnow()
        if side:
            self.last_trade_side[symbol] = side
        if exit_price:
            self.last_trade_price[symbol] = exit_price

    def _capture_entry_conditions(
        self,
        symbol: str,
        market_data: Dict,
        strategy_type: str = "swing",
        signal_confidence: float = 0.5,
        stop_loss: float = 0.0,
        take_profit: float = 0.0,
        entry_price: float = 0.0
    ) -> EntryConditions:
        """Capture comprehensive market conditions for learning (called at trade entry).

        Args:
            symbol: Trading symbol
            market_data: Full market data dict
            strategy_type: "swing", "micro", "macro", or "snipe"
            signal_confidence: Claude's confidence (0-1)
            stop_loss: Stop loss price (for SL/TP learning)
            take_profit: Take profit price (for SL/TP learning)
            entry_price: Entry price (for calculating SL/TP distances)
        """
        now = datetime.utcnow()
        price = entry_price or market_data.get("price", 0)

        # Extract indicators from market data
        trend_5m = market_data.get("trend_5m", {})
        bb_data = market_data.get("bb_data", {})
        smc_analysis = market_data.get("smc_analysis", {})
        orderbook = market_data.get("orderbook_analysis", {})
        volume_profile = market_data.get("volume_profile", {})

        # Calculate SL/TP distances as percentages
        sl_distance_pct = 0.0
        tp_distance_pct = 0.0
        risk_reward = 0.0
        if price > 0 and stop_loss > 0:
            sl_distance_pct = abs(price - stop_loss) / price * 100
        if price > 0 and take_profit > 0:
            tp_distance_pct = abs(take_profit - price) / price * 100
        if sl_distance_pct > 0:
            risk_reward = tp_distance_pct / sl_distance_pct

        # Determine volume profile zone
        vp_zone = "neutral"
        if volume_profile:
            poc = volume_profile.get("poc_price", price)
            hvn_raw = volume_profile.get("high_volume_nodes", [])
            lvn_raw = volume_profile.get("low_volume_nodes", [])

            # Extract prices from nodes (could be floats or dicts with 'price' key)
            def extract_price(node):
                if isinstance(node, (int, float)):
                    return float(node)
                elif isinstance(node, dict):
                    return float(node.get("price", 0))
                return 0

            hvn = [extract_price(n) for n in hvn_raw if extract_price(n) > 0]
            lvn = [extract_price(n) for n in lvn_raw if extract_price(n) > 0]

            if hvn and any(abs(price - node) / price < 0.005 for node in hvn):
                vp_zone = "high_volume"
            elif lvn and any(abs(price - node) / price < 0.005 for node in lvn):
                vp_zone = "low_volume"
            elif poc and abs(price - poc) / price < 0.01:
                vp_zone = "poc_area"

        return EntryConditions(
            # === BASIC INDICATORS ===
            rsi=market_data.get("rsi", 50.0) or 50.0,
            bb_position=trend_5m.get("bb_position", 0.5) or bb_data.get("band_position", 0.5) or 0.5,
            vwap_distance_pct=self._calc_vwap_distance(market_data),
            trend_5m_score=trend_5m.get("score", 0) or 0,
            trend_15m_score=market_data.get("momentum_15m", {}).get("score", 0) or 0,
            trend_1h_signal=market_data.get("ema_macro_signal", "neutral") or "neutral",
            atr_pct=self._calc_atr_pct(market_data),
            hour_of_day=now.hour,
            day_of_week=now.weekday(),
            funding_rate=market_data.get("funding_rate_8h", 0) or 0,
            volume_ratio=market_data.get("volume_ratio", 1.0) or 1.0,

            # === ENHANCED INDICATORS ===
            macd_signal=market_data.get("macd_signal", "neutral") or "neutral",
            ema_fast_signal=market_data.get("ema_fast_signal", "neutral") or "neutral",
            ema_mid_signal=market_data.get("ema_mid_signal", "neutral") or "neutral",
            ema_macro_signal=market_data.get("ema_macro_signal", "neutral") or "neutral",

            # === MARKET REGIME ===
            market_regime=market_data.get("market_regime", "unknown") or "unknown",
            adaptive_regime=market_data.get("adaptive_regime", "ranging") or "ranging",
            regime_strength=market_data.get("regime_strength", 0.0) or 0.0,

            # === SMART MONEY CONCEPTS ===
            smc_bias=smc_analysis.get("bias", "neutral") or "neutral",
            smc_confidence=smc_analysis.get("confidence", 0.0) or 0.0,
            near_order_block=smc_analysis.get("near_order_block", False),
            in_fair_value_gap=smc_analysis.get("in_fvg", False),

            # === ORDERBOOK ===
            orderbook_imbalance=orderbook.get("imbalance", 0.0) or 0.0,
            bid_wall_distance_pct=orderbook.get("bid_wall_distance_pct", 0.0) or 0.0,
            ask_wall_distance_pct=orderbook.get("ask_wall_distance_pct", 0.0) or 0.0,

            # === SL/TP TRACKING ===
            sl_distance_pct=sl_distance_pct,
            tp_distance_pct=tp_distance_pct,
            risk_reward_ratio=risk_reward,

            # === CONFIDENCE & STRATEGY ===
            signal_confidence=signal_confidence,
            strategy_type=strategy_type,

            # === ADDITIONAL CONTEXT ===
            adx=market_data.get("adx", 0.0) or 0.0,
            cvd_signal=market_data.get("cvd_signal", "neutral") or "neutral",
            volume_profile_zone=vp_zone,
        )

    def _calc_vwap_distance(self, market_data: Dict) -> float:
        """Calculate distance from VWAP as percentage."""
        price = market_data.get("price", 0)
        trend_5m = market_data.get("trend_5m", {})
        vwap = trend_5m.get("vwap", price)
        if vwap and price:
            return ((price - vwap) / vwap) * 100
        return 0.0

    def _calc_atr_pct(self, market_data: Dict) -> float:
        """Calculate ATR as percentage of price."""
        price = market_data.get("price", 0)
        trend_5m = market_data.get("trend_5m", {})
        atr = trend_5m.get("atr", 0)
        if atr and price:
            return (atr / price) * 100
        return 0.0

    async def _tick(self) -> None:
        """Execute one trading cycle for all symbols."""
        # Analyze each symbol
        for symbol in self.config.symbols:
            # 1. Gather market data (including alpha signals)
            market_data = await self._gather_market_data_async(symbol)
            price = market_data['price']
            logger.info(f"{symbol} Price: ${price:.2f}")

            # 1.5 Send Discord updates (market analysis only - NO account data)
            await self._send_discord_updates(symbol, market_data)

            # 2. Check if we have an active position to manage
            pos = self._get_position_info(symbol)
            has_position = pos["side"] != "none"

            # 3. If in position, manage it (check stop/target) - no cooldown for exits
            if has_position:
                logger.info(f">>> POSITION EXISTS: {pos['side'].upper()} {pos['abs_size']} @ ${pos['entry_price']:.2f} | P&L: {self._calc_pnl_pct(pos, price):+.2f}% <<<")
                await self._manage_position(symbol, market_data)
                logger.info(f">>> SKIPPING NEW TRADE - Already in position for {symbol} <<<")
                continue  # Don't look for new trades while in position

            # ═══════════════════════════════════════════════════════════════════════
            # 4. DEEPSEEK-ONLY DECISION MAKING (Institutional Framework)
            # DeepSeek is the SOLE decision maker. All other data is context only.
            # ═══════════════════════════════════════════════════════════════════════

            # === GATHER ALL CONTEXT DATA FOR DEEPSEEK ===
            # Quant score provides technical context (NOT trade decisions)
            quant_score = self._calculate_quant_score(market_data)
            market_data["quant_score"] = quant_score
            quant_points = quant_score.get("score", 50)
            quant_direction = quant_score.get("direction", "neutral")

            # S/R context
            sr_signal = market_data.get("sr_signal", "mid_range")
            price = market_data.get("price", 0)

            # === DEEPSEEK MAKES THE DECISION ===
            logger.info(f"🧠 DEEPSEEK DECISION: {symbol} @ ${price:,.2f} | Quant context: {quant_points}/100 {quant_direction}")
            signal = self.llm.analyze_with_deepseek(market_data)
            logger.info(f"🧠 DEEPSEEK: {signal.action.upper()} @ {signal.confidence:.0%} | {signal.reasoning[:80]}...")

            # Log the thesis summary (compact mode - skip full reasoning)
            if signal.thesis_summary:
                logger.info(f"THESIS: {signal.thesis_summary}")
            self.last_signal = signal

            # 5. Check if we should enter based on thesis
            if signal.action not in ["long", "short"]:
                if self.level_snipe_enabled:
                    await self._place_level_snipes(symbol, market_data)
                continue

            if signal.confidence < self.config.min_confidence:
                # WEAK THESIS - Also place snipes if levels are clear
                if self.level_snipe_enabled:
                    await self._place_level_snipes(symbol, market_data)
                logger.info(f"Thesis not strong enough - {signal.confidence:.2f} < {self.config.min_confidence} (snipes may be placed)")
                continue

            # ═══════════════════════════════════════════════════════════════════════
            # DEEPSEEK'S DECISION IS FINAL - NO OTHER SYSTEM CAN OVERRIDE
            # All context data (RSI, SMC, Bayesian, etc.) was already given to DeepSeek.
            # DeepSeek has the institutional mandate to consider all factors.
            # ═══════════════════════════════════════════════════════════════════════

            # Log context data for transparency (NOT used for blocking)
            rsi = market_data.get("rsi", 50)
            smc_bias = market_data.get("smc_bias", "neutral")
            bayesian_dir = market_data.get("bayesian_direction", "neutral")
            ema_4h = market_data.get("ema_4h_signal", "neutral")
            logger.info(f"📊 CONTEXT: RSI={rsi:.0f} | SMC={smc_bias} | Bayesian={bayesian_dir} | 4H={ema_4h}")

            # Store quant for logging
            trade_quality = "A" if quant_points >= 75 else "B" if quant_points >= 60 else "C"
            logger.info(f"📊 QUALITY: {trade_quality} (Quant: {quant_points}/100)")

            # Set for downstream use
            trendline_signal = market_data.get("trendline_signal", "neutral")
            confluence_score = quant_points

            # ═══════════════════════════════════════════════════════════════════════
            # DEEPSEEK DECISION IS TRUSTED - SKIP SNIPER/LIQUIDATION OVERRIDES
            # DeepSeek already has all trendline, liquidation, and confluence data.
            # Its institutional mandate includes considering all risk factors.
            # ═══════════════════════════════════════════════════════════════════════

            # Log context for transparency (NOT used for blocking)
            liq_signal = market_data.get("liquidation_signal", "neutral")
            if liq_signal != "neutral":
                logger.info(f"📊 LIQUIDATION CONTEXT: {liq_signal} (DeepSeek already considered this)")
            if trendline_signal != "neutral":
                logger.info(f"📊 TRENDLINE CONTEXT: {trendline_signal} (DeepSeek already considered this)")

            # 6. Check cooldown (including same-direction block and worse-price prevention)
            if self._is_on_cooldown(symbol, signal.action, price):
                last_side = self.last_trade_side.get(symbol, "none")
                if symbol in self.last_trade_time:
                    elapsed_hours = (datetime.utcnow() - self.last_trade_time[symbol]).total_seconds() / 3600
                    if last_side == signal.action:
                        hours_left = self.same_direction_cooldown_hours - elapsed_hours
                        if hours_left > 0:
                            logger.info(f"BLOCKED: Same direction cooldown - {hours_left:.1f}h remaining")
                    else:
                        hours_left = self.trade_cooldown_hours - elapsed_hours
                        if hours_left > 0:
                            logger.info(f"On cooldown - {hours_left:.1f}h remaining")
                continue

            # 7. All checks passed - execute entry with thesis
            logger.info(f">>> NEW THESIS: {signal.action.upper()} with {signal.confidence:.0%} confidence <<<")
            if signal.thesis_summary:
                logger.info(f">>> ACTION PLAN: {signal.thesis_summary} <<<")
            await self._execute_entry(signal, market_data)
            continue  # Don't also scalp if we just entered a swing trade

        # === 8. LIMIT ORDER PLACEMENT (one symbol at a time) ===
        # Process each symbol sequentially: MACRO first (HTF levels), then MICRO (short-term S/R)
        # This ensures BTC has all 4 limit orders (macro long/short + micro long/short) before ETH starts
        for symbol in self.config.symbols:
            pos = self._get_position_info(symbol)
            market_data = await self._gather_market_data_async(symbol)

            logger.debug(f"📊 Processing {symbol} limit orders...")
            # (MACRO removed - MICRO only, market orders via _check_micro_opportunity)

        # === 9. IMMEDIATE OPPORTUNITIES (market orders if already at S/R) ===
        # Only after all limit orders are in place, check for immediate entries
        for symbol in self.config.symbols:
            pos = self._get_position_info(symbol)
            if pos["side"] != "none":
                continue
            market_data = await self._gather_market_data_async(symbol)

            # Check MICRO opportunity (market order if conditions met)
            if self.config.micro_enabled:
                await self._check_micro_opportunity(symbol, market_data)

    # ==================== MICRO STRATEGY (5m/15m/30m) ====================

    async def _check_micro_opportunity(self, symbol: str, market_data: Dict) -> None:
        """PROACTIVE MICRO STRATEGY: Always-on momentum hunter.

        PROACTIVE MODE:
        1. Constantly scan for momentum-based entries
        2. Use adaptive SL/TP based on volatility regime
        3. Enter on momentum confirmation (don't wait for perfect setups)
        4. Let intelligence and LLM confirm the direction

        KEY CHANGES:
        - Shorter cooldown (1 min vs 3 min)
        - More aggressive entry triggers
        - Adaptive stops based on volatility
        """
        # Check cooldown (1 minute between trades - more aggressive)
        if symbol in self.last_trade_time:
            elapsed = (datetime.utcnow() - self.last_trade_time[symbol]).total_seconds() / 60
            if elapsed < 1:  # Reduced from 3 to 1 minute
                return

        price = market_data.get("price", 0)
        if price <= 0:
            return

        candles_5m = market_data.get("candles_5m", [])
        candles_15m = market_data.get("candles_15m", [])
        candles_1h = market_data.get("candles_1h", [])
        orderbook = market_data.get("orderbook_analysis", {})
        rsi = market_data.get("rsi", 50)
        atr = market_data.get("atr", price * 0.01)
        volume_ratio = market_data.get("volume_ratio", 1.0)

        # === STEP 1: PROACTIVE SCAN (Fast momentum check) ===
        if self.proactive_micro_enabled:
            try:
                scan = self.proactive_micro.scan_for_opportunity(
                    symbol=symbol,
                    price=price,
                    candles_5m=candles_5m,
                    candles_15m=candles_15m,
                    candles_1h=candles_1h,
                    orderbook=orderbook,
                    rsi=rsi,
                    atr=atr,
                    volume_ratio=volume_ratio
                )

                # Log proactive scan results
                logger.info(f"🔍 PROACTIVE {symbol}: {scan.momentum_state.value} | Vol: {scan.volatility_regime.value} | Triggers: {len(scan.triggers)}")

                if scan.should_enter:
                    logger.info(f"   ⚡ PROACTIVE ENTRY: {scan.direction.upper()} | Conf: {scan.confidence:.0%}")
                    logger.info(f"   📐 Adaptive SL/TP: Stop={scan.sl_distance_pct:.2f}% | R:R={scan.rr_ratio:.1f}:1")
                    logger.info(f"   🎯 Triggers: {', '.join(scan.triggers)}")

                    # Store adaptive parameters for execution
                    market_data["proactive_scan"] = scan
                    market_data["proactive_stop_loss"] = scan.stop_loss
                    market_data["proactive_take_profit"] = scan.take_profit
                    market_data["proactive_size_mult"] = scan.size_multiplier
                    market_data["volatility_regime"] = scan.volatility_regime.value

            except Exception as e:
                logger.error(f"PROACTIVE scan failed: {e}")

        # === STEP 2: RUN MICRO INTELLIGENCE ENGINE ===
        try:
            intel = self.micro_intel.analyze(
                symbol=symbol,
                candles_5m=candles_5m,
                candles_15m=candles_15m,
                candles_1h=candles_1h,
                orderbook=orderbook,
                current_price=price
            )
        except Exception as e:
            logger.error(f"MICRO Intelligence failed: {e}")
            return

        # Log intelligence report
        logger.info(f"📊 MICRO INTEL {symbol}: {intel.regime.value.upper()} | Pattern: {intel.pattern_score:.0f}/100 | OB: {intel.orderbook_bias}")

        # === STEP 3: DIRECTION CONSENSUS - Resolve conflicts between signals ===
        # Priority: 1) S/R building blocks, 2) Agreement = highest confidence, 3) Opportunity bias

        proactive_entry = market_data.get("proactive_scan")
        opportunity_bias = market_data.get("opportunity_bias", "neutral")
        resistance_building = market_data.get("resistance_building", {})
        support_building = market_data.get("support_building", {})
        direction = None
        confidence_boost = 0

        # Gather all signals
        proactive_dir = proactive_entry.direction if proactive_entry and proactive_entry.should_enter else None
        intel_dir = intel.trade_bias if intel.should_trade else None
        opp_dir = opportunity_bias.lower() if opportunity_bias.lower() in ["long", "short"] else None

        # === S/R BUILDING OVERRIDE - Block counter-S/R trades ===
        # If resistance building with 3+ touches, BLOCK LONGS
        res_touches = resistance_building.get("touches", 0) if resistance_building else 0
        sup_touches = support_building.get("touches", 0) if support_building else 0

        if res_touches >= 3:
            logger.info(f"   🔨 RESISTANCE BUILDING ({res_touches} touches) - blocking LONG signals")
            if proactive_dir == "long":
                proactive_dir = None  # Cancel proactive long
            if intel_dir == "long":
                intel_dir = None  # Cancel intel long
            # Suggest SHORT if we haven't already
            if not opp_dir:
                opp_dir = "short"

        if sup_touches >= 3:
            logger.info(f"   🔨 SUPPORT BUILDING ({sup_touches} touches) - blocking SHORT signals")
            if proactive_dir == "short":
                proactive_dir = None
            if intel_dir == "short":
                intel_dir = None
            if not opp_dir:
                opp_dir = "long"

        # Log the signals (after S/R filtering)
        logger.info(f"   📊 Direction signals: Proactive={proactive_dir} | Intel={intel_dir} | Opportunity={opp_dir}")

        if proactive_dir and intel_dir:
            if proactive_dir == intel_dir:
                # Perfect agreement
                direction = proactive_dir
                confidence_boost = 0.2
                logger.info(f"   ✅ PROACTIVE + INTEL AGREE: {direction.upper()}")
            else:
                # Conflict - use opportunity bias as tiebreaker
                if opp_dir:
                    if opp_dir == proactive_dir:
                        direction = proactive_dir
                        confidence_boost = 0.1
                        logger.info(f"   ⚡ PROACTIVE + OPPORTUNITY agree: {direction.upper()} (intel said {intel_dir})")
                    elif opp_dir == intel_dir:
                        direction = intel_dir
                        confidence_boost = 0.1
                        logger.info(f"   ⚡ INTEL + OPPORTUNITY agree: {direction.upper()} (proactive said {proactive_dir})")
                    else:
                        # All three disagree - use intel (more structured analysis)
                        direction = intel_dir
                        confidence_boost = 0.05
                        logger.info(f"   ⚠️ All signals conflict - using Intel: {direction.upper()}")
                else:
                    # No opportunity bias - default to intel
                    direction = intel_dir
                    confidence_boost = 0.05
                    logger.info(f"   ⚠️ Using Intel direction: {direction.upper()} (proactive said {proactive_dir})")
        elif proactive_dir:
            direction = proactive_dir
            confidence_boost = 0.1
        elif intel_dir:
            direction = intel_dir
        elif opp_dir:
            # Use opportunity bias as last resort if it has strong signal
            direction = opp_dir
            confidence_boost = 0.05
            logger.info(f"   📊 Using Opportunity bias: {direction.upper()}")
        else:
            # Neither found an entry
            logger.debug(f"   MICRO {symbol}: No entry - proactive={proactive_entry is not None}, intel={intel.should_trade}")
            return

        # === STEP 4: LLM CONFIRMATION (with full context) ===
        market_data["micro_intelligence"] = self.micro_intel.format_for_llm(intel)
        market_data["intel_regime"] = intel.regime.value
        market_data["intel_bias"] = intel.trade_bias if intel.should_trade else direction
        market_data["intel_pattern_score"] = intel.pattern_score

        try:
            signal = self.llm.analyze_micro(market_data)
        except Exception as e:
            logger.error(f"MICRO LLM analysis failed: {e}")
            return

        # LLM can override, but we're VERY lenient with proactive entries (aggressive mode)
        if signal.action == "hold":
            # If proactive scan found ANYTHING, override LLM hold
            if proactive_entry and proactive_entry.should_enter:
                logger.info(f"   🔄 LLM said HOLD but proactive found entry ({proactive_entry.confidence:.0%}) - PROCEEDING")
                signal.action = direction
                signal.confidence = max(proactive_entry.confidence, 0.55)  # Floor at 55%
            # Also override if intelligence found a trade
            elif intel.should_trade and intel.trade_bias in ["long", "short"]:
                logger.info(f"   🔄 LLM said HOLD but Intel says {intel.trade_bias.upper()} - PROCEEDING")
                signal.action = intel.trade_bias
                signal.confidence = 0.55  # Use floor confidence
            else:
                logger.debug(f"   MICRO {symbol}: LLM says HOLD, no override available")
                return

        # Direction alignment check (more flexible)
        if signal.action != direction:
            # Allow LLM to override if it's very confident
            if signal.confidence >= 0.75:
                logger.info(f"   🔄 LLM override: {signal.action.upper()} (was {direction}) with {signal.confidence:.0%} confidence")
                direction = signal.action
            else:
                logger.warning(f"   MICRO {symbol}: Direction mismatch - LLM:{signal.action} vs Expected:{direction}")
                return

        # Apply confidence boost
        signal.confidence = min(0.95, signal.confidence + confidence_boost)

        # Check minimum confidence - HIGHER thresholds for quality entries
        # We want to snipe GOOD entries, not just any entry
        if proactive_entry and proactive_entry.should_enter:
            min_conf = 0.60  # Increased from 0.45 - need better setups
        elif intel.should_trade:
            min_conf = 0.70  # Increased from 0.65 - need solid intel confidence
        else:
            min_conf = self.config.micro_min_confidence  # 0.70 default

        if signal.confidence < min_conf:
            logger.debug(f"   MICRO {symbol}: {signal.action} rejected (conf={signal.confidence:.0%} < {min_conf:.0%})")
            return

        # === STEP 5: ADAPTIVE SL/TP (Use proactive scan values if available) ===
        # Priority: Proactive adaptive > LLM provided > Default calculation

        if proactive_entry and proactive_entry.should_enter:
            # Use proactive scan's adaptive SL/TP
            stop_loss = proactive_entry.stop_loss
            take_profit = proactive_entry.take_profit
            rr_ratio = proactive_entry.rr_ratio
            vol_regime = proactive_entry.volatility_regime.value
            logger.info(f"   📐 Using ADAPTIVE SL/TP ({vol_regime}): SL={proactive_entry.sl_distance_pct:.2f}%")
        elif signal.stop_loss and signal.stop_loss > 0:
            stop_loss = signal.stop_loss
            if signal.take_profit and signal.take_profit > 0:
                take_profit = signal.take_profit
            else:
                sl_distance = abs(price - stop_loss)
                take_profit = price + (sl_distance * 2.5) if signal.action == "long" else price - (sl_distance * 2.5)
            sl_distance = abs(price - stop_loss)
            tp_distance = abs(take_profit - price)
            rr_ratio = tp_distance / sl_distance if sl_distance > 0 else 2.5
        else:
            # MICRO: ALWAYS USE FIXED 3% STOP LOSS
            pass  # Will be set below

        # === MICRO STRATEGY: LEVERAGE-AWARE STOP LOSS ===
        # SL calculated to limit margin loss, not just price move
        leverage = self.get_leverage(symbol)
        stop_loss, take_profit, sl_pct, margin_loss_pct = self._get_leverage_aware_sl(
            symbol, price, signal.action, "micro"
        )
        rr_ratio = 2.0
        logger.info(f"   📐 MICRO SL: {sl_pct:.2f}% price = {margin_loss_pct:.0f}% margin @ {leverage}x | R:R=2:1")

        # Recalculate R:R after any adjustments
        sl_distance = abs(price - stop_loss)
        tp_distance = abs(take_profit - price)
        rr_ratio = tp_distance / sl_distance if sl_distance > 0 else 0

        if rr_ratio < 1.5:
            logger.warning(f"   MICRO {symbol}: {signal.action} rejected (R:R={rr_ratio:.1f} < 1.5)")
            return

        # === STEP 6: RSI SAFETY CHECK (more lenient in proactive mode) ===
        rsi = market_data.get("rsi", 50)
        rsi_limit_long = 80 if proactive_entry else 75  # More lenient with proactive
        rsi_limit_short = 20 if proactive_entry else 25

        if signal.action == "long" and rsi > rsi_limit_long:
            logger.warning(f"   MICRO {symbol}: LONG blocked - RSI={rsi:.0f} > {rsi_limit_long} (overbought)")
            return
        if signal.action == "short" and rsi < rsi_limit_short:
            logger.warning(f"   MICRO {symbol}: SHORT blocked - RSI={rsi:.0f} < {rsi_limit_short} (oversold)")
            return

        # === STEP 7: LOG AND EXECUTE ===
        vol_regime_str = market_data.get("volatility_regime", "normal")
        size_mult = proactive_entry.size_multiplier if proactive_entry else intel.size_multiplier

        logger.info(f"🎯 MICRO TRADE: {signal.action.upper()} {symbol} @ ${price:,.0f}")
        logger.info(f"   📊 Intel: {intel.regime.value} | Pattern: {intel.pattern_score:.0f} | Conf: {signal.confidence:.0%}")
        logger.info(f"   📈 OB: {intel.orderbook_bias} ({intel.orderbook_imbalance:+.2f}) | MTF: {'✅' if intel.mtf_aligned else '❌'}")
        logger.info(f"   🌡️ Vol Regime: {vol_regime_str} | Size: {size_mult:.1f}x")
        logger.info(f"   🎯 SL=${stop_loss:,.0f} | TP=${take_profit:,.0f} | R:R={rr_ratio:.1f}:1")
        logger.info(f"   💡 {signal.reasoning[:80]}...")

        # Store for execution
        signal.stop_loss = stop_loss
        signal.take_profit = take_profit
        market_data["micro_stop_level"] = stop_loss
        market_data["micro_target_level"] = take_profit
        market_data["micro_rr_ratio"] = rr_ratio
        market_data["micro_size_multiplier"] = size_mult
        market_data["micro_stop_multiplier"] = intel.stop_multiplier
        market_data["volatility_regime"] = vol_regime_str

        # === EXECUTE MARKET ORDER ===
        await self._execute_micro_entry(symbol, signal, market_data)

    def _evaluate_micro_setup(
        self, symbol: str, direction: str, price: float,
        support: float, resistance: float, atr: float,
        market_data: Dict, consolidation_zone: Dict, smc_structure: Dict
    ) -> Optional[Dict]:
        """Evaluate a micro trade setup and return score + parameters if valid."""

        score = 0
        reasons = []

        # === HARD BLOCK: RSI COUNTER-TREND PREVENTION ===
        rsi = market_data.get("rsi", 50)
        rsi_1h = market_data.get("rsi_1h", rsi)

        # NO LONGS when RSI > 75 (overbought - likely to reverse down)
        if direction == "long" and (rsi > 75 or rsi_1h > 75):
            logger.warning(f"🚫 MICRO BLOCKED: No LONG when RSI={rsi:.0f}/1H={rsi_1h:.0f} > 75 (overbought)")
            return None

        # NO SHORTS when RSI < 25 (oversold - likely to bounce)
        if direction == "short" and (rsi < 25 or rsi_1h < 25):
            logger.warning(f"🚫 MICRO BLOCKED: No SHORT when RSI={rsi:.0f}/1H={rsi_1h:.0f} < 25 (oversold)")
            return None

        # === HARD BLOCK: MACRO TREND ALIGNMENT ===
        ema_macro = market_data.get("ema_macro_signal", "neutral")
        ema_4h = market_data.get("ema_4h_signal", ema_macro)

        # Don't long against strong bearish macro (both 1H and 4H bearish)
        if direction == "long" and ema_macro == "bearish" and ema_4h == "bearish":
            logger.warning(f"🚫 MICRO BLOCKED: No LONG against bearish 1H+4H trend")
            return None

        # Don't short against strong bullish macro (both 1H and 4H bullish)
        if direction == "short" and ema_macro == "bullish" and ema_4h == "bullish":
            logger.warning(f"🚫 MICRO BLOCKED: No SHORT against bullish 1H+4H trend")
            return None

        # === LEVERAGE-AWARE STOP LOSS ===
        # Max 3% loss on margin with actual leverage (BTC=40x, ETH=25x, SOL=20x)
        # e.g., 3% margin loss at 40x = 0.075% price move
        leverage = market_data.get("leverage", 40)  # Default to BTC leverage
        max_margin_loss_pct = 3.0  # Maximum 3% loss on margin
        max_price_move_pct = max_margin_loss_pct / leverage  # e.g., 3% / 50 = 0.06%
        max_stop_distance = price * (max_price_move_pct / 100)

        if direction == "long":
            # LONG at support
            entry_level = support
            dist_to_level = (price - support) / price * 100

            # Stop below support - but capped to max_stop_distance for risk management
            structural_stop = support * 0.998  # 0.2% below support
            stop_loss = max(structural_stop, price - max_stop_distance)

            # If stop would be above current price, invalid setup
            if stop_loss >= price:
                return None

            # Target at resistance or 2:1 minimum
            reward_distance = resistance - price
            risk_distance = price - stop_loss

            if risk_distance <= 0:
                return None

            rr_ratio = reward_distance / risk_distance
            take_profit = price + (reward_distance * 0.8)  # 80% of distance to resistance

            # Calculate actual margin risk %
            price_risk_pct = (risk_distance / price) * 100
            margin_risk_pct = price_risk_pct * leverage

            # Trend scoring (soft, not hard block since we already blocked strong counter-trend)
            if ema_macro == "bearish":
                score -= 1
                reasons.append("against_1h_trend")
            elif ema_macro == "bullish":
                score += 2
                reasons.append("with_trend")

        else:
            # SHORT at resistance
            entry_level = resistance
            dist_to_level = (resistance - price) / price * 100

            # Stop above resistance - capped to max_stop_distance
            structural_stop = resistance * 1.002  # 0.2% above resistance
            stop_loss = min(structural_stop, price + max_stop_distance)

            # If stop would be below current price, invalid setup
            if stop_loss <= price:
                return None

            # Target at support or 2:1 minimum
            reward_distance = price - support
            risk_distance = stop_loss - price

            if risk_distance <= 0:
                return None

            rr_ratio = reward_distance / risk_distance
            take_profit = price - (reward_distance * 0.8)

            # Trend scoring
            if ema_macro == "bullish":
                score -= 1
                reasons.append("against_1h_trend")
            elif ema_macro == "bearish":
                score += 2
                reasons.append("with_trend")

            # Calculate actual margin risk %
            price_risk_pct = (risk_distance / price) * 100
            margin_risk_pct = price_risk_pct * leverage

        # === MINIMUM R:R CHECK ===
        if rr_ratio < 1.5:
            return None  # Must have at least 1.5:1 R:R

        # === SCORING ===

        # 1. R:R quality (0-3 points)
        if rr_ratio >= 3.0:
            score += 3
            reasons.append(f"rr_{rr_ratio:.1f}")
        elif rr_ratio >= 2.5:
            score += 2
            reasons.append(f"rr_{rr_ratio:.1f}")
        elif rr_ratio >= 2.0:
            score += 1
            reasons.append(f"rr_{rr_ratio:.1f}")

        # 2. Distance to level (0-2 points) - closer is better
        if dist_to_level <= 0.5:
            score += 2
            reasons.append("at_level")
        elif dist_to_level <= 1.0:
            score += 1
            reasons.append("near_level")

        # 3. Fresh/consolidation level (0-2 points)
        if consolidation_zone.get("level"):
            consol_level = consolidation_zone["level"]
            if direction == "long" and abs(support - consol_level) / support < 0.01:
                score += 2
                reasons.append("fresh_support")
            elif direction == "short" and abs(resistance - consol_level) / resistance < 0.01:
                score += 2
                reasons.append("fresh_resistance")

        # 4. SMC structure alignment (0-2 points)
        swing_low = smc_structure.get("last_swing_low")
        swing_high = smc_structure.get("last_swing_high")
        if direction == "long" and swing_low and abs(support - swing_low) / support < 0.01:
            score += 1
            reasons.append("smc_swing_low")
        elif direction == "short" and swing_high and abs(resistance - swing_high) / resistance < 0.01:
            score += 1
            reasons.append("smc_swing_high")

        # 5. RSI confirmation (0-1 point)
        rsi = market_data.get("rsi", 50)
        if direction == "long" and rsi < 40:
            score += 1
            reasons.append(f"rsi_{rsi:.0f}")
        elif direction == "short" and rsi > 60:
            score += 1
            reasons.append(f"rsi_{rsi:.0f}")

        # === MINIMUM SCORE CHECK ===
        if score < 5:  # Need at least 5 points to trade (high quality only)
            return None

        return {
            "direction": direction,
            "stop_loss": stop_loss,
            "take_profit": take_profit,
            "rr_ratio": rr_ratio,
            "score": score,
            "reasons": reasons,
            "dist_to_level": dist_to_level
        }

    async def _execute_micro_entry(self, symbol: str, signal, market_data: Dict) -> None:
        """Execute MICRO strategy entry - MARKET ORDER with SL/TP attached.

        LLM decides the trade, this function executes it immediately.
        Uses native exchange SL/TP so position runs without bot babysitting.
        """
        price = market_data.get("price", 0)
        atr = market_data.get("atr", price * 0.01)

        # === PORTFOLIO RISK CHECK (prevent conflicting positions on correlated assets) ===
        state = self.hl.get_account_state()
        current_equity = state.get("equity", 0)
        can_trade, risk_reason = self.risk_manager.can_trade(symbol, signal.action, current_equity)
        if not can_trade:
            logger.warning(f"🛑 RISK BLOCKED {symbol} {signal.action.upper()}: {risk_reason}")
            return

        # === ML PREDICTION CHECK ===
        if self.use_ml_filter and self.ml_predictor.model:
            entry_cond = self._capture_entry_conditions(
                symbol=symbol,
                market_data=market_data,
                strategy_type="micro",
                signal_confidence=signal.confidence
            )
            ml_take, ml_reason = self.ml_predictor.should_take_trade(
                entry_cond, signal.action, self.ml_min_probability
            )
            if not ml_take:
                logger.info(f"🤖 MICRO ML SKIP {symbol}: {ml_reason}")
                return
            logger.info(f"🤖 MICRO ML PASS {symbol}: {ml_reason}")

        # === WHALE PATTERN ML CHECK ===
        if self.use_whale_ml_filter and self.whale_ml and self.whale_ml.trained:
            should_take, whale_reason, whale_score = self.whale_ml.should_take_trade(
                symbol=symbol,
                side=signal.action,
                market_data=market_data,
                hl_client=self.hl,
                min_score=self.whale_ml_min_score
            )
            if not should_take:
                logger.info(f"🐋 MICRO WHALE SKIP {symbol}: {whale_reason}")
                return
            logger.info(f"🐋 MICRO {whale_reason}")

        # Get MICRO intelligence-based size multiplier (from regime, pattern score, MTF alignment)
        intel_size_mult = market_data.get("micro_size_multiplier", 1.0)
        intel_stop_mult = market_data.get("micro_stop_multiplier", 1.0)
        regime = market_data.get("intel_regime", "range")

        # Position size with intelligence multiplier
        base_margin = self.config.position_size_usd * self.config.micro_position_pct * intel_size_mult
        leverage = self.hl.get_max_leverage(symbol)
        notional = base_margin * leverage
        size = notional / price

        # Round size
        if price > 1000:
            size = round(size, 5)
        else:
            size = round(size, 3)

        # === USE PRE-CALCULATED S/R-BASED SL/TP (from _check_micro_opportunity) ===
        # This ensures we're using structure-based stops, not arbitrary ATR multiples
        stop_loss = market_data.get("micro_stop_level")
        take_profit = market_data.get("micro_target_level")
        rr_ratio = market_data.get("micro_rr_ratio", 2.0)

        if not stop_loss or not take_profit:
            # Fallback to Claude if pre-calculated levels missing (shouldn't happen)
            logger.warning(f"   ⚠️ Pre-calculated SL/TP missing, falling back to Claude")
            sltp_decision = self.llm.decide_sltp(
                symbol=symbol,
                side=signal.action,
                entry_price=price,
                leverage=leverage,
                market_data=market_data,
                signal_reasoning=signal.reasoning
            )
            stop_loss = sltp_decision.stop_loss
            take_profit = sltp_decision.take_profit
            rr_ratio = sltp_decision.risk_reward_ratio

        # === MICRO: LEVERAGE-AWARE STOP LOSS (3% MARGIN LOSS) ===
        # SL based on MARGIN loss, not ticker price!
        # Example: 3% margin loss at 40x = 0.075% ticker move
        stop_loss, take_profit, sl_price_pct, sl_margin_pct = self._get_leverage_aware_sl(
            symbol, price, signal.action, "micro"
        )

        logger.info(f"   📐 MICRO SL: {sl_margin_pct:.0f}% MARGIN loss = {sl_price_pct:.3f}% price @ {leverage}x")
        logger.info(f"   📐 SL=${stop_loss:,.2f} | 🎯 TP: DeepSeek decides (no fixed target)")

        try:
            order_side = "buy" if signal.action == "long" else "sell"

            # Use SL-ONLY orders - DeepSeek decides when to take profit!
            # This lets winners run without arbitrary TP limits
            result = self.hl.place_market_order_with_sl_only(
                symbol=symbol,
                side=order_side,
                size=size,
                stop_loss_price=stop_loss
            )

            if result.get("success"):
                fill_price = result.get("entry_price", price)

                logger.info(f"✅ MICRO: {signal.action.upper()} {size} {symbol} @ ${fill_price:,.2f}")
                logger.info(f"   🔒 SL SET: Stop=${stop_loss:,.2f} | 🎯 TP: DeepSeek will decide exit")
                logger.info(f"   ⚡ Let winners run - AI decides when momentum exhausts!")

                # === CAPTURE ENTRY CONDITIONS FOR LEARNING ===
                entry_conditions = self._capture_entry_conditions(
                    symbol=symbol,
                    market_data=market_data,
                    strategy_type="micro",
                    signal_confidence=signal.confidence,
                    stop_loss=stop_loss,
                    take_profit=None,  # No fixed TP - DeepSeek decides
                    entry_price=fill_price
                )
                self.pending_entry_conditions[symbol] = entry_conditions
                logger.info(f"   🧠 Entry conditions captured for learning")

                self.last_trade_time[symbol] = datetime.utcnow()
                entry_now = datetime.utcnow()
                self.positions[symbol] = {
                    "strategy": "MICRO",
                    "side": signal.action,
                    "entry_price": fill_price,
                    "stop_loss": stop_loss,
                    "take_profit": None,  # No fixed TP - DeepSeek decides exit
                    "size": size,
                    "atr": atr,
                    "entry_time": entry_now,
                    "best_price": fill_price,
                    "worst_price": fill_price,  # MFE/MAE tracking
                    "best_price_time": entry_now,
                    "worst_price_time": entry_now,
                    "trailing_stop": stop_loss,
                    "thesis": signal.thesis_summary,
                    "native_sltp": True,
                    "deepseek_exit": True,  # Flag: DeepSeek manages exit
                    "sl_oid": result.get("sl_oid"),  # Track SL order ID
                    "tp_oid": None,  # No TP order - DeepSeek decides
                    "current_tp_price": None,  # No fixed TP
                    "volatility_regime": market_data.get("volatility_regime", "normal"),  # For adaptive trailing
                    "tf_alignment": {"5m": market_data.get("ema_fast_signal"),
                                    "15m": market_data.get("ema_mid_signal")},
                    "entry_conditions": entry_conditions  # For learning
                }

                # === RECORD TRADE SIGNAL FOR LEARNING (SQLite) ===
                try:
                    db = get_db()
                    db.save_trade_signal(
                        symbol=symbol,
                        side=signal.action,
                        entry_price=fill_price,
                        confidence=signal.confidence,
                        support_levels=market_data.get("support_levels", []),
                        resistance_levels=market_data.get("resistance_levels", []),
                        stop_loss=sl_price,
                        take_profit=tp_price,
                        metadata=entry_conditions
                    )
                    logger.info(f"   📀 Trade signal saved to database")
                except Exception as e:
                    logger.warning(f"Failed to save trade signal: {e}")

                # === UPDATE RISK MANAGER (critical for correlation checks) ===
                self.risk_manager.update_position(symbol, signal.action)
            else:
                logger.warning(f"❌ Order failed: {result.get('error', 'Unknown')}")
        except Exception as e:
            logger.error(f"❌ MICRO execution error: {e}")

    async def _place_proactive_micro_limits(self, symbol: str, market_data: Dict) -> None:
        """Place PROACTIVE limit orders at upcoming S/R levels.

        Instead of waiting for price to reach S/R and then market ordering,
        place limit orders AT the levels BEFORE price arrives.

        This gives:
        - Better fills (at exact level, not chasing)
        - Lower fees (limit vs market)
        - Truly proactive entries
        """
        price = market_data.get("price", 0)
        if price <= 0:
            return

        # Check if we already have max pending orders for this symbol
        symbol_orders = [k for k in self.pending_limits if k.startswith(f"{symbol}_")]
        if len(symbol_orders) >= self.limit_max_orders:
            return

        # Get S/R levels (existing swing highs/lows)
        nearest_support = market_data.get("nearest_support", 0)
        nearest_resistance = market_data.get("nearest_resistance", 0)
        supports = market_data.get("supports", [nearest_support] if nearest_support else [])
        resistances = market_data.get("resistances", [nearest_resistance] if nearest_resistance else [])

        # === NEW: DETECT RECENTLY FORMED S/R LEVELS ===
        # These are levels that formed in the last few candles (consolidation, swing points)
        consolidation_zone = market_data.get("consolidation_zone", {})
        is_building_support = market_data.get("is_building_support", False)
        is_building_resistance = market_data.get("is_building_resistance", False)

        # Add consolidation levels as high-priority targets
        if is_building_support and consolidation_zone.get("level"):
            consol_support = consolidation_zone["level"]
            if consol_support not in supports and consol_support < price:
                supports = [consol_support] + list(supports)[:2]  # Prioritize new support
                logger.debug(f"📍 NEW SUPPORT forming @ ${consol_support:.0f} (touches: {consolidation_zone.get('touches', 0)})")

        if is_building_resistance and consolidation_zone.get("level"):
            consol_resistance = consolidation_zone["level"]
            if consol_resistance not in resistances and consol_resistance > price:
                resistances = [consol_resistance] + list(resistances)[:2]  # Prioritize new resistance
                logger.debug(f"📍 NEW RESISTANCE forming @ ${consol_resistance:.0f} (touches: {consolidation_zone.get('touches', 0)})")

        # Also check for recent swing highs/lows from SMC analysis
        smc_analysis = market_data.get("smc_analysis") or {}
        smc_structure = smc_analysis.get("structure") or {}

        # SMC stores swings in structure dict as last_swing_low/high
        recent_swing_low = smc_structure.get("last_swing_low") or smc_structure.get("prev_swing_low")
        recent_swing_high = smc_structure.get("last_swing_high") or smc_structure.get("prev_swing_high")

        if recent_swing_low and recent_swing_low not in supports and recent_swing_low < price:
            dist_pct = (price - recent_swing_low) / price * 100
            if 0.5 <= dist_pct <= 4.0:  # Only if reasonably close
                supports = list(supports) + [recent_swing_low]
                logger.debug(f"📍 SMC swing low @ ${recent_swing_low:.0f}")

        if recent_swing_high and recent_swing_high not in resistances and recent_swing_high > price:
            dist_pct = (recent_swing_high - price) / price * 100
            if 0.5 <= dist_pct <= 4.0:
                resistances = list(resistances) + [recent_swing_high]
                logger.debug(f"📍 SMC swing high @ ${recent_swing_high:.0f}")

        # Check trendline touches as dynamic S/R
        asc_trendline = market_data.get("ascending_trendline_price")
        desc_trendline = market_data.get("descending_trendline_price")

        if asc_trendline and asc_trendline < price:
            dist_pct = (price - asc_trendline) / price * 100
            if 0.5 <= dist_pct <= 3.0 and asc_trendline not in supports:
                supports = list(supports) + [asc_trendline]
                logger.debug(f"📍 Ascending trendline support @ ${asc_trendline:.0f}")

        if desc_trendline and desc_trendline > price:
            dist_pct = (desc_trendline - price) / price * 100
            if 0.5 <= dist_pct <= 3.0 and desc_trendline not in resistances:
                resistances = list(resistances) + [desc_trendline]
                logger.debug(f"📍 Descending trendline resistance @ ${desc_trendline:.0f}")

        # Get trend context
        ema_macro = market_data.get("ema_macro_signal", "neutral")
        rsi = market_data.get("rsi", 50)

        # === IDENTIFY VALID LEVELS TO PLACE ORDERS ===
        valid_levels = []

        # LONG orders at support levels (0.5-4% below current price)
        # Tighter range for new/consolidation levels, wider for established swing lows
        for support in supports:
            if support <= 0:
                continue
            dist_pct = (price - support) / price * 100

            # Check if this is a "fresh" level (consolidation or recent swing)
            is_fresh_level = (
                support == consolidation_zone.get("level") or
                support == recent_swing_low or
                support == asc_trendline
            )

            # Fresh levels can be closer (0.5%), established need 1% buffer
            min_dist = 0.5 if is_fresh_level else 1.0
            max_dist = 4.0 if is_fresh_level else 3.0  # Fresh levels can be further (catching dips)

            if min_dist <= dist_pct <= max_dist:
                # LEVERAGE-AWARE SL: 3% margin loss
                stop_loss, take_profit, sl_price_pct, sl_margin_pct = self._get_leverage_aware_sl(
                    symbol, support, "long", "micro"
                )
                rr_ratio = 2.0

                valid_levels.append({
                    "side": "long",
                    "level": support,
                    "stop_loss": stop_loss,
                    "take_profit": take_profit,
                    "rr_ratio": rr_ratio,
                    "dist_pct": dist_pct,
                    "is_fresh": is_fresh_level,
                    "sl_price_pct": sl_price_pct,
                    "sl_margin_pct": sl_margin_pct,
                    "source": "consolidation" if support == consolidation_zone.get("level") else
                              "swing_low" if support == recent_swing_low else
                              "trendline" if support == asc_trendline else "historical"
                })

        # SHORT orders at resistance levels (0.5-4% above current price)
        for resistance in resistances:
            if resistance <= 0:
                continue
            dist_pct = (resistance - price) / price * 100

            # Check if this is a "fresh" level
            is_fresh_level = (
                resistance == consolidation_zone.get("level") or
                resistance == recent_swing_high or
                resistance == desc_trendline
            )

            min_dist = 0.5 if is_fresh_level else 1.0
            max_dist = 4.0 if is_fresh_level else 3.0

            if min_dist <= dist_pct <= max_dist:
                # LEVERAGE-AWARE SL: 3% margin loss
                stop_loss, take_profit, sl_price_pct, sl_margin_pct = self._get_leverage_aware_sl(
                    symbol, resistance, "short", "micro"
                )
                rr_ratio = 2.0

                valid_levels.append({
                    "side": "short",
                    "level": resistance,
                    "stop_loss": stop_loss,
                    "take_profit": take_profit,
                    "rr_ratio": rr_ratio,
                    "dist_pct": dist_pct,
                    "is_fresh": is_fresh_level,
                    "sl_price_pct": sl_price_pct,
                    "sl_margin_pct": sl_margin_pct,
                    "source": "consolidation" if resistance == consolidation_zone.get("level") else
                              "swing_high" if resistance == recent_swing_high else
                              "trendline" if resistance == desc_trendline else "historical"
                })

        if not valid_levels:
            return

        # Sort by: 1) Fresh levels first (higher priority), 2) Then by distance (closer = more likely to hit)
        valid_levels.sort(key=lambda x: (not x.get("is_fresh", False), x["dist_pct"]))

        # === PLACE LIMIT ORDERS (max 1 per direction) ===
        placed_long = any(self.pending_limits.get(f"{symbol}_{k}", {}).get("side") == "long" for k in range(10))
        placed_short = any(self.pending_limits.get(f"{symbol}_{k}", {}).get("side") == "short" for k in range(10))

        for level_info in valid_levels:
            if level_info["side"] == "long" and placed_long:
                continue
            if level_info["side"] == "short" and placed_short:
                continue

            # Position sizing
            leverage = self.hl.get_max_leverage(symbol)
            base_margin = self.config.position_size_usd * self.config.micro_position_pct
            notional = base_margin * leverage
            size = notional / level_info["level"]
            size = round(size, 5) if level_info["level"] > 1000 else round(size, 3)

            # Place limit order with SL/TP
            order_side = "buy" if level_info["side"] == "long" else "sell"
            level_source = level_info.get("source", "historical")
            is_fresh = level_info.get("is_fresh", False)
            fresh_tag = "🆕 NEW " if is_fresh else ""

            logger.info(f"🎯 PROACTIVE MICRO: {fresh_tag}Placing {order_side.upper()} limit @ ${level_info['level']:,.0f}")
            logger.info(f"   📍 Source: {level_source.upper()} | Dist: {level_info['dist_pct']:.1f}%")
            logger.info(f"   📐 SL=${level_info['stop_loss']:,.0f} | TP=${level_info['take_profit']:,.0f} | R:R={level_info['rr_ratio']:.1f}")

            result = self.hl.place_limit_order_with_sltp(
                symbol=symbol,
                side=order_side,
                size=size,
                price=level_info["level"],
                stop_loss_price=level_info["stop_loss"],
                take_profit_price=level_info["take_profit"]
            )

            if result.get("success"):
                order_id = result.get("order_id") or result.get("entry_oid")
                order_key = f"{symbol}_{level_info['level']:.0f}"

                self.pending_limits[order_key] = {
                    "order_id": order_id,
                    "symbol": symbol,
                    "side": level_info["side"],
                    "level": level_info["level"],
                    "size": size,
                    "stop_loss": level_info["stop_loss"],
                    "take_profit": level_info["take_profit"],
                    "rr_ratio": level_info["rr_ratio"],
                    "placed_at": datetime.utcnow(),
                    "sl_oid": result.get("sl_oid"),
                    "tp_oid": result.get("tp_oid"),
                    "level_source": level_source,
                    "is_fresh_level": is_fresh,
                    "macro_signal": ema_macro  # Track for adaptive cancellation
                }

                logger.info(f"   ✅ Order placed: {order_key} (oid={order_id})")

                if level_info["side"] == "long":
                    placed_long = True
                else:
                    placed_short = True
            else:
                logger.warning(f"   ❌ Failed to place limit: {result.get('error')}")

    async def _check_micro_limit_fills(self, symbol: str) -> None:
        """Check if any proactive MICRO limit orders have filled.

        Also handles:
        - Cancelling stale orders (older than TTL)
        - Updating position tracking when filled
        """
        now = datetime.utcnow()
        orders_to_remove = []

        for order_key, order_info in list(self.pending_limits.items()):
            if not order_key.startswith(f"{symbol}_"):
                continue

            order_id = order_info.get("order_id")
            placed_at = order_info.get("placed_at", now)

            # Check if order is stale
            age_minutes = (now - placed_at).total_seconds() / 60
            if age_minutes > self.limit_ttl_minutes:
                # Cancel stale order
                logger.info(f"🕐 Cancelling stale MICRO limit: {order_key} (age={age_minutes:.0f}min)")
                if order_id:
                    self.hl.cancel_order(symbol, order_id)
                orders_to_remove.append(order_key)
                continue

            # Check if order filled by looking for position
            pos = self._get_position_info(symbol)
            expected_side = order_info.get("side")

            if pos["side"] == expected_side and pos["abs_size"] > 0:
                # Order filled! Track the position
                logger.info(f"✅ PROACTIVE MICRO FILLED: {symbol} {expected_side.upper()} @ ${order_info['level']:,.0f}")

                # Add to micro_positions tracking with MFE/MAE
                self.positions[symbol] = {
                    "strategy": "MICRO_PROACTIVE",
                    "side": expected_side,
                    "entry_price": order_info["level"],
                    "stop_loss": order_info["stop_loss"],
                    "take_profit": order_info["take_profit"],
                    "size": order_info["size"],
                    "entry_time": now,
                    "best_price": order_info["level"],
                    "worst_price": order_info["level"],  # MFE/MAE tracking
                    "best_price_time": now,
                    "worst_price_time": now,
                    "native_sltp": True,
                    "sl_oid": order_info.get("sl_oid"),
                    "tp_oid": order_info.get("tp_oid"),
                    "current_tp_price": order_info["take_profit"],
                    "rr_ratio": order_info.get("rr_ratio", 2.0)
                }

                # Update risk manager
                self.risk_manager.update_position(symbol, expected_side)

                # Update cooldown
                self.last_trade_time[symbol] = now

                orders_to_remove.append(order_key)
            else:
                # Check if order still exists in open orders
                open_orders_result = self.hl.get_open_orders()
                if open_orders_result.get("success"):
                    open_orders = open_orders_result.get("result", [])
                    order_ids = [o.get("oid") for o in open_orders if isinstance(o, dict)]

                    if order_id and order_id not in order_ids:
                        # Order gone but no position = cancelled/rejected
                        logger.info(f"📭 MICRO limit order {order_key} no longer active")
                        orders_to_remove.append(order_key)

        # Clean up removed orders
        for key in orders_to_remove:
            if key in self.pending_limits:
                del self.pending_limits[key]

    # ==================== LEVEL SNIPE ORDERS ====================
    # (MACRO strategy removed - MICRO only)

    async def _place_level_snipes(self, symbol: str, market_data: Dict) -> None:
        """Place limit orders at support (for long) and resistance (for short).

        When there's no clear immediate entry, we 'snipe' the levels:
        - BID at support level for a LONG entry
        - ASK at resistance level for a SHORT entry

        This way we don't just wait - we let the market come to us.
        """
        price = market_data.get("price", 0)
        if price <= 0:
            return

        # Get support and resistance levels (prefer visual/Claude levels, fallback to calculated)
        support = market_data.get("visual_support") or market_data.get("nearest_support")
        resistance = market_data.get("visual_resistance") or market_data.get("nearest_resistance")

        # Also check trendline levels
        trendline_support = market_data.get("ascending_trendline_price")
        trendline_resistance = market_data.get("descending_trendline_price")

        # Use trendline if closer to price
        if trendline_support and (not support or abs(price - trendline_support) < abs(price - support)):
            support = trendline_support
        if trendline_resistance and (not resistance or abs(price - trendline_resistance) < abs(price - resistance)):
            resistance = trendline_resistance

        if not support and not resistance:
            logger.info(f"📍 {symbol}: No clear S/R levels for snipe orders")
            return

        # === PORTFOLIO RISK CHECK (prevent conflicting snipe orders) ===
        state = self.hl.get_account_state()
        current_equity = state.get("equity", 0)

        # Check if we can place long or short snipes based on correlation
        can_long, long_reason = self.risk_manager.can_trade(symbol, "long", current_equity)
        can_short, short_reason = self.risk_manager.can_trade(symbol, "short", current_equity)

        if not can_long and not can_short:
            logger.info(f"📍 {symbol}: Snipe orders blocked by risk manager")
            return

        # Check if we already have snipe orders for this symbol
        existing_snipes = self.pending_snipes.get(symbol, {})

        # Calculate position size for snipes (use normal swing size)
        leverage = self.hl.get_max_leverage(symbol)
        base_margin = self.config.position_size_usd
        notional = base_margin * leverage

        orders_placed = []

        # Place LONG snipe at support (if support is below current price by at least 0.3%)
        if support and support < price * 0.997 and can_long:  # At least 0.3% below + risk check
            dist_to_support_pct = (price - support) / price * 100

            # Only snipe if support is within reasonable range (0.3% - 5%)
            if 0.3 <= dist_to_support_pct <= 5.0:
                size = notional / support
                size = round(size, 4) if support > 1000 else round(size, 2)

                # Cancel existing long snipe if price moved significantly
                if existing_snipes.get("long_order_id"):
                    old_support = existing_snipes.get("support_price", 0)
                    if abs(old_support - support) / support > 0.01:  # >1% difference
                        self.hl.cancel_order(symbol, existing_snipes["long_order_id"])
                        logger.info(f"🔄 Cancelled old LONG snipe at ${old_support:.2f}")
                        existing_snipes["long_order_id"] = None

                # Place new long snipe if we don't have one
                if not existing_snipes.get("long_order_id"):
                    # LEVERAGE-AWARE SL: 3% margin loss, not 3% ticker move!
                    sl_long, tp_long, sl_price_pct, sl_margin_pct = self._get_leverage_aware_sl(
                        symbol, support, "long", "micro"
                    )

                    result = self.hl.place_limit_order_with_sltp(
                        symbol=symbol,
                        side="buy",
                        size=size,
                        price=support,
                        stop_loss_price=sl_long,
                        take_profit_price=tp_long
                    )
                    if result.get("success"):
                        order_id = result.get("order_id") or result.get("entry_oid")
                        existing_snipes["long_order_id"] = order_id
                        existing_snipes["support_price"] = support
                        existing_snipes["long_size"] = size
                        existing_snipes["long_sl"] = sl_long
                        existing_snipes["long_tp"] = tp_long
                        existing_snipes["placed_time"] = datetime.utcnow()
                        orders_placed.append(f"LONG @ ${support:,.2f}")
                        logger.info(f"🎯 SNIPE: BID {size} {symbol} @ ${support:,.2f} ({dist_to_support_pct:.1f}% below)")
                        logger.info(f"   🛑 SL=${sl_long:,.2f} ({sl_margin_pct:.0f}% margin = {sl_price_pct:.3f}% price @ {leverage}x)")

        # Place SHORT snipe at resistance (if resistance is above current price by at least 0.3%)
        if resistance and resistance > price * 1.003 and can_short:  # At least 0.3% above + risk check
            dist_to_resistance_pct = (resistance - price) / price * 100

            # Only snipe if resistance is within reasonable range (0.3% - 5%)
            if 0.3 <= dist_to_resistance_pct <= 5.0:
                size = notional / resistance
                size = round(size, 4) if resistance > 1000 else round(size, 2)

                # Cancel existing short snipe if price moved significantly
                if existing_snipes.get("short_order_id"):
                    old_resistance = existing_snipes.get("resistance_price", 0)
                    if abs(old_resistance - resistance) / resistance > 0.01:  # >1% difference
                        self.hl.cancel_order(symbol, existing_snipes["short_order_id"])
                        logger.info(f"🔄 Cancelled old SHORT snipe at ${old_resistance:.2f}")
                        existing_snipes["short_order_id"] = None

                # Place new short snipe if we don't have one
                if not existing_snipes.get("short_order_id"):
                    # LEVERAGE-AWARE SL: 3% margin loss, not 3% ticker move!
                    sl_short, tp_short, sl_price_pct, sl_margin_pct = self._get_leverage_aware_sl(
                        symbol, resistance, "short", "micro"
                    )

                    result = self.hl.place_limit_order_with_sltp(
                        symbol=symbol,
                        side="sell",
                        size=size,
                        price=resistance,
                        stop_loss_price=sl_short,
                        take_profit_price=tp_short
                    )
                    if result.get("success"):
                        order_id = result.get("order_id") or result.get("entry_oid")
                        existing_snipes["short_order_id"] = order_id
                        existing_snipes["resistance_price"] = resistance
                        existing_snipes["short_size"] = size
                        existing_snipes["short_sl"] = sl_short
                        existing_snipes["short_tp"] = tp_short
                        existing_snipes["placed_time"] = datetime.utcnow()
                        orders_placed.append(f"SHORT @ ${resistance:,.2f}")
                        logger.info(f"🎯 SNIPE: ASK {size} {symbol} @ ${resistance:,.2f} ({dist_to_resistance_pct:.1f}% above)")
                        logger.info(f"   🛑 SL=${sl_short:,.2f} ({sl_margin_pct:.0f}% margin = {sl_price_pct:.3f}% price @ {leverage}x)")

        # Save snipe state
        if existing_snipes:
            self.pending_snipes[symbol] = existing_snipes

        if orders_placed:
            logger.info(f"📋 {symbol} SNIPE ORDERS ACTIVE: {' | '.join(orders_placed)}")
        elif support or resistance:
            logger.info(f"📍 {symbol}: S/R levels ({support:.2f}/{resistance:.2f}) too close or already sniped")

    async def _check_snipe_fills(self) -> None:
        """Check if any snipe orders have been filled.

        NOTE: SL/TP are already attached via place_limit_order_with_sltp()
        using Hyperliquid's native TPSL grouping. We do NOT add additional
        SL/TP here - just track the fill for position management.
        """
        for symbol in list(self.pending_snipes.keys()):
            snipes = self.pending_snipes[symbol]

            # Check order status (handle API errors)
            open_orders_result = self.hl.get_open_orders()
            if not open_orders_result.get("success"):
                logger.debug(f"Skipping snipe check: API error")
                continue
            open_orders = open_orders_result.get("result", [])
            # Filter to this symbol
            open_orders = [o for o in open_orders if o.get("coin") == symbol]
            open_order_ids = [o.get("oid") for o in open_orders if isinstance(o, dict)]

            # Check if long snipe filled
            long_oid = snipes.get("long_order_id")
            if long_oid and long_oid not in open_order_ids:
                # Order is gone - either filled or cancelled
                pos = self._get_position_info(symbol)
                if pos["side"] == "long" and pos["abs_size"] > 0:
                    entry_price = snipes.get('support_price', pos.get('entry_price', 0))
                    size = snipes.get('long_size', pos['abs_size'])
                    sl_price = snipes.get('long_sl', entry_price * 0.97)
                    tp_price = snipes.get('long_tp', entry_price * 1.06)

                    logger.info(f"✅ SNIPE FILLED: LONG {symbol} @ ~${entry_price:,.2f}")
                    logger.info(f"   🔒 SL/TP already set via native TPSL: SL=${sl_price:,.2f} | TP=${tp_price:,.2f}")

                    # NO DUPLICATE SL/TP - already attached via place_limit_order_with_sltp!
                    # Just record the trade and update tracking
                    self._record_trade(symbol, "long")

                    # === CAPTURE ENTRY CONDITIONS FOR LEARNING ===
                    try:
                        market_data = await self._gather_market_data_async(symbol)
                        if market_data:
                            entry_conditions = self._capture_entry_conditions(
                                symbol=symbol,
                                market_data=market_data,
                                strategy_type="snipe",
                                signal_confidence=0.7,  # Snipes are S/R based
                                stop_loss=sl_price,
                                take_profit=tp_price,
                                entry_price=entry_price
                            )
                            self.pending_entry_conditions[symbol] = entry_conditions
                            logger.info(f"   🧠 Snipe entry conditions captured for learning")
                    except Exception as e:
                        logger.debug(f"Could not capture snipe entry conditions: {e}")

                    # Track position for management
                    snipe_now = datetime.utcnow()
                    self.positions[symbol] = {
                        "strategy": "SNIPE",
                        "side": "long",
                        "entry_price": entry_price,
                        "stop_loss": sl_price,
                        "take_profit": tp_price,
                        "size": size,
                        "entry_time": snipe_now,
                        "native_sltp": True,  # SL/TP managed by exchange
                    }

                    # === UPDATE RISK MANAGER (critical for correlation checks) ===
                    self.risk_manager.update_position(symbol, "long")
                snipes["long_order_id"] = None

            # Check if short snipe filled
            short_oid = snipes.get("short_order_id")
            if short_oid and short_oid not in open_order_ids:
                pos = self._get_position_info(symbol)
                if pos["side"] == "short" and pos["abs_size"] > 0:
                    entry_price = snipes.get('resistance_price', pos.get('entry_price', 0))
                    size = snipes.get('short_size', pos['abs_size'])
                    sl_price = snipes.get('short_sl', entry_price * 1.03)
                    tp_price = snipes.get('short_tp', entry_price * 0.94)

                    logger.info(f"✅ SNIPE FILLED: SHORT {symbol} @ ~${entry_price:,.2f}")
                    logger.info(f"   🔒 SL/TP already set via native TPSL: SL=${sl_price:,.2f} | TP=${tp_price:,.2f}")

                    # NO DUPLICATE SL/TP - already attached via place_limit_order_with_sltp!
                    # Just record the trade and update tracking
                    self._record_trade(symbol, "short")

                    # === CAPTURE ENTRY CONDITIONS FOR LEARNING ===
                    try:
                        market_data = await self._gather_market_data_async(symbol)
                        if market_data:
                            entry_conditions = self._capture_entry_conditions(
                                symbol=symbol,
                                market_data=market_data,
                                strategy_type="snipe",
                                signal_confidence=0.7,  # Snipes are S/R based
                                stop_loss=sl_price,
                                take_profit=tp_price,
                                entry_price=entry_price
                            )
                            self.pending_entry_conditions[symbol] = entry_conditions
                            logger.info(f"   🧠 Snipe entry conditions captured for learning")
                    except Exception as e:
                        logger.debug(f"Could not capture snipe entry conditions: {e}")

                    # Track position for management
                    snipe_now = datetime.utcnow()
                    self.positions[symbol] = {
                        "strategy": "SNIPE",
                        "side": "short",
                        "entry_price": entry_price,
                        "stop_loss": sl_price,
                        "take_profit": tp_price,
                        "size": size,
                        "entry_time": snipe_now,
                        "native_sltp": True,  # SL/TP managed by exchange
                    }

                    # === UPDATE RISK MANAGER (critical for correlation checks) ===
                    self.risk_manager.update_position(symbol, "short")
                snipes["short_order_id"] = None

            # Check TTL - cancel old snipes
            placed_time = snipes.get("placed_time")
            if placed_time:
                age_minutes = (datetime.utcnow() - placed_time).total_seconds() / 60
                if age_minutes > self.snipe_order_ttl_minutes:
                    # Cancel stale orders
                    if snipes.get("long_order_id"):
                        self.hl.cancel_order(symbol, snipes["long_order_id"])
                        logger.info(f"⏰ Cancelled stale LONG snipe on {symbol}")
                    if snipes.get("short_order_id"):
                        self.hl.cancel_order(symbol, snipes["short_order_id"])
                        logger.info(f"⏰ Cancelled stale SHORT snipe on {symbol}")
                    del self.pending_snipes[symbol]
                    continue

            # Clean up if no orders left
            if not snipes.get("long_order_id") and not snipes.get("short_order_id"):
                del self.pending_snipes[symbol]

    # ==================== ADAPTIVE ORDER MANAGEMENT ====================

    async def _check_and_adapt_pending_orders(
        self, symbol: str, market_data: Dict, check_micro: bool = True, check_macro: bool = True
    ) -> None:
        """Re-evaluate pending limit orders and cancel/replace if conditions changed.

        This prevents stale orders from filling into bad trades when:
        1. Thesis has flipped (bullish → bearish or vice versa)
        2. Key S/R levels have shifted significantly
        3. Market regime has changed

        Timing:
        - MICRO orders: checked every 15 minutes (short-term S/R, faster fills)
        - MACRO orders: checked every 60 minutes (HTF levels, patient approach)
        """
        if not self.adaptive_orders_enabled:
            return

        now = datetime.utcnow()

        # Separate rate limiting for micro vs macro
        last_micro_check = self.last_adaptive_check.get(symbol, datetime.min)
        last_macro_check = self.last_adaptive_check.get(symbol, datetime.min)

        minutes_since_micro = (now - last_micro_check).total_seconds() / 60
        minutes_since_macro = (now - last_macro_check).total_seconds() / 60

        should_check_micro = check_micro and minutes_since_micro >= self.adaptive_interval_minutes
        should_check_macro = check_macro and minutes_since_macro >= self.adaptive_interval_minutes

        if not should_check_micro and not should_check_macro:
            return  # Nothing to check yet

        # Get current market context
        current_macro = market_data.get("ema_macro_signal", "neutral")
        current_mid = market_data.get("ema_mid_signal", "neutral")
        current_price = market_data.get("price", 0)
        current_support = market_data.get("nearest_support", 0)
        current_resistance = market_data.get("nearest_resistance", 0)

        orders_cancelled = []
        orders_to_replace = []

        # === CHECK MICRO LIMITS (DISABLED - MICRO uses market orders only) ===
        # if should_check_micro:
        #     self.last_adaptive_check[symbol] = now
        #     logger.debug(f"🔄 MICRO adaptive check for {symbol} (every {self.adaptive_interval_minutes}m)")

        # MICRO LIMIT ORDERS DISABLED - MICRO uses market orders only
        # The pending_micro_limits dict should always be empty now
        # Keeping this code commented for future reference if we re-enable
        # for order_key, order_info in list(self.pending_limits.items()):
        #     ... (MICRO limit order adaptive checks would go here)

        # === CHECK MACRO LIMITS (every 60 min) ===
        if should_check_macro:
            self.last_adaptive_check[symbol] = now
            logger.debug(f"🔄 MACRO adaptive check for {symbol} (every {self.adaptive_interval_minutes}m)")

        for order_key, order_info in list(self.pending_limits.items()):
            if not should_check_macro:
                break
            if not order_key.startswith(f"{symbol}_macro_"):
                continue

            order_side = order_info.get("side")
            order_level = order_info.get("level", 0)
            order_id = order_info.get("order_id")
            order_macro_at_place = order_info.get("macro_signal", "neutral")

            should_cancel = False
            cancel_reason = ""
            new_level = None

            # MACRO orders have stricter thesis requirements
            # Cancel if BOTH 1h and implied 4h signal disagree
            if order_side == "long" and current_macro == "bearish":
                should_cancel = True
                cancel_reason = f"MACRO trend now BEARISH"
            elif order_side == "short" and current_macro == "bullish":
                should_cancel = True
                cancel_reason = f"MACRO trend now BULLISH"

            if should_cancel and order_id:
                try:
                    self.hl.cancel_order(symbol, order_id)
                    logger.info(f"🔄 ADAPTIVE: Cancelled {order_side.upper()} MACRO limit @ ${order_level:.0f}")
                    logger.info(f"   Reason: {cancel_reason}")
                    orders_cancelled.append(order_key)
                except Exception as e:
                    logger.warning(f"Failed to cancel MACRO limit {order_key}: {e}")

        # === CHECK SNIPE ORDERS ===
        snipes = self.pending_snipes.get(symbol, {})
        if snipes:
            # Cancel long snipe if macro turned bearish
            if snipes.get("long_order_id") and current_macro == "bearish":
                try:
                    self.hl.cancel_order(symbol, snipes["long_order_id"])
                    logger.info(f"🔄 ADAPTIVE: Cancelled LONG snipe - macro now BEARISH")
                    snipes["long_order_id"] = None
                    orders_cancelled.append(f"{symbol}_snipe_long")
                except Exception as e:
                    logger.warning(f"Failed to cancel snipe: {e}")

            # Cancel short snipe if macro turned bullish
            if snipes.get("short_order_id") and current_macro == "bullish":
                try:
                    self.hl.cancel_order(symbol, snipes["short_order_id"])
                    logger.info(f"🔄 ADAPTIVE: Cancelled SHORT snipe - macro now BULLISH")
                    snipes["short_order_id"] = None
                    orders_cancelled.append(f"{symbol}_snipe_short")
                except Exception as e:
                    logger.warning(f"Failed to cancel snipe: {e}")

        # === CLEAN UP CANCELLED ORDERS ===
        for key in orders_cancelled:
            if key in self.pending_limits:
                del self.pending_limits[key]
            if key in self.pending_limits:
                del self.pending_limits[key]

        # === REPLACE ORDERS AT NEW LEVELS ===
        for replacement in orders_to_replace:
            await self._replace_limit_order(symbol, replacement, market_data)

        if orders_cancelled:
            logger.info(f"📋 ADAPTIVE {symbol}: Cancelled {len(orders_cancelled)} orders, replacing {len(orders_to_replace)}")

    async def _replace_limit_order(self, symbol: str, replacement: Dict, market_data: Dict) -> None:
        """Place a replacement limit order at a new level."""
        try:
            side = replacement["side"]
            new_level = replacement["new_level"]
            size = replacement.get("size")

            if not size:
                # Recalculate size
                leverage = self.hl.get_max_leverage(symbol)
                base_margin = self.config.position_size_usd * 0.5  # Use half size for replacement
                notional = base_margin * leverage
                size = notional / new_level
                size = self.hl.round_size(symbol, size)

            # LEVERAGE-AWARE SL: 3% margin loss
            stop_loss, take_profit, sl_price_pct, sl_margin_pct = self._get_leverage_aware_sl(
                symbol, new_level, side, "micro"
            )

            # Place replacement order with SL/TP
            result = self.hl.place_limit_order_with_sltp(
                symbol=symbol,
                side="buy" if side == "long" else "sell",
                size=size,
                price=new_level,
                stop_loss_price=stop_loss,
                take_profit_price=take_profit
            )

            if result.get("success"):
                order_id = result.get("order_id") or result.get("entry_oid")
                order_key = f"{symbol}_{new_level:.0f}"

                self.pending_limits[order_key] = {
                    "order_id": order_id,
                    "symbol": symbol,
                    "side": side,
                    "level": new_level,
                    "size": size,
                    "stop_loss": stop_loss,
                    "take_profit": take_profit,
                    "placed_at": datetime.utcnow(),
                    "macro_signal": market_data.get("ema_macro_signal", "neutral"),
                    "is_replacement": True,
                    "sl_oid": result.get("sl_oid"),
                    "tp_oid": result.get("tp_oid")
                }

                logger.info(f"✅ REPLACEMENT: {side.upper()} limit @ ${new_level:.0f} (was ${replacement['old_level']:.0f})")
                logger.info(f"   📐 SL=${stop_loss:.0f} | TP=${take_profit:.0f}")
            else:
                logger.warning(f"❌ Failed to place replacement order: {result.get('error')}")

        except Exception as e:
            logger.error(f"Error replacing limit order: {e}")

    def _calc_pnl_pct(self, pos: Dict, price: float = None) -> float:
        """Calculate P&L percentage for a position based on MARGIN (leveraged P&L).

        This returns the actual position P&L %, NOT the raw price movement.
        E.g., with 40x leverage, a 0.1% price move = 4% position P&L.

        Args:
            pos: Position info dict from _get_position_info()
            price: Current price (optional, for fallback calculation)

        Returns:
            Position P&L as percentage of margin used
        """
        # Use pre-calculated position P&L % if available (preferred)
        if "position_pnl_pct" in pos and pos["position_pnl_pct"] != 0:
            return pos["position_pnl_pct"]

        # Fallback: calculate from unrealized PnL and margin
        margin_used = pos.get("margin_used", 0)
        unrealized_pnl = pos.get("unrealized_pnl", 0)

        if margin_used > 0:
            return (unrealized_pnl / margin_used) * 100

        # Last fallback: estimate using leverage
        leverage = pos.get("leverage", 1) or 1
        entry_price = pos.get("entry_price", 0)

        if entry_price > 0 and price and price > 0:
            price_pnl = ((price - entry_price) / entry_price) * 100
            if pos.get("side") == "short":
                price_pnl = -price_pnl
            return price_pnl * leverage

        return 0.0

    async def _manage_position(self, symbol: str, market_data: Dict) -> None:
        """Manage position with DEEPSEEK EXIT DECISIONS.

        SL is on exchange for protection. DeepSeek decides when to take profit.
        This lets winners run - AI exits when momentum exhausts, not at arbitrary targets.

        Logic:
        1. Track best price (high water mark for longs, low for shorts)
        2. Trail SL to protect gains as price moves favorably
        3. When profitable, ask DeepSeek if we should exit
        4. DeepSeek analyzes momentum, RSI, patterns to decide
        5. Exit when DeepSeek says momentum is exhausting
        """
        pos = self._get_position_info(symbol)
        price = market_data["price"]
        pnl_pct = self._calc_pnl_pct(pos, price)
        side = pos["side"]

        # Get position tracking data (MICRO or MACRO)
        pos_data = self.positions.get(symbol) or self.positions.get(symbol) or {}

        # Check if position has native SL/TP
        if not pos_data.get("native_sltp"):
            # Legacy position - use old management
            await self._manage_position_legacy(symbol, market_data)
            return

        entry_price = pos_data.get("entry_price", pos.get("entry_price", price))
        best_price = pos_data.get("best_price", entry_price)
        sl_oid = pos_data.get("sl_oid")
        size = pos_data.get("size", pos.get("abs_size", 0))
        atr = pos_data.get("atr", 0)
        deepseek_exit = pos_data.get("deepseek_exit", False)

        # Log current status
        exit_mode = "🤖 DeepSeek" if deepseek_exit else "📊 Trailing TP"
        logger.info(f"🎯 {symbol} {side.upper()}: {pnl_pct:+.2f}% | Price: ${price:,.2f} | Best: ${best_price:,.2f} | Exit: {exit_mode}")

        # === CHECK IF POSITION STILL EXISTS (exchange may have closed it) ===
        if pos.get("abs_size", 0) == 0:
            # Position closed by exchange (SL or TP hit)
            logger.info(f"✅ Position closed by exchange for {symbol}")
            self._cleanup_position_tracking(symbol, side, pnl_pct)
            return

        # === TRAIL SL & TP: ADAPTIVE based on volatility regime ===
        # Get current SL info
        current_sl = pos_data.get("trailing_stop", pos_data.get("stop_loss", 0))

        price_moved_favorably = False
        new_best = best_price

        # Track worst price (MAE) - initialize if not present
        worst_price = pos_data.get("worst_price", entry_price)
        new_worst = worst_price

        if side == "long":
            if price > best_price:
                new_best = price
                price_moved_favorably = True
            if price < worst_price:
                new_worst = price
        else:  # short
            if price < best_price:
                new_best = price
                price_moved_favorably = True
            if price > worst_price:
                new_worst = price

        # === ADAPTIVE TRAILING: Use volatility regime for dynamic trailing ===
        # Get volatility regime from position data or detect it
        vol_regime_str = pos_data.get("volatility_regime", "normal")
        try:
            vol_regime = VolatilityRegime(vol_regime_str)
        except ValueError:
            vol_regime = VolatilityRegime.NORMAL

        if sl_oid:
            # Use proactive_micro's adaptive trailing
            new_sl, sl_reason = self.proactive_micro.calculate_dynamic_trail(
                side=side,
                entry_price=entry_price,
                current_price=price,
                best_price=new_best,
                current_sl=current_sl,
                vol_regime=vol_regime,
                pnl_pct=pnl_pct
            )

            if new_sl and sl_reason:
                result = self.hl.update_sl_order(symbol, sl_oid, side, size, new_sl)
                if result.get("success"):
                    new_sl_oid = result.get("sl_oid", sl_oid)
                    if symbol in self.positions:
                        self.positions[symbol]["sl_oid"] = new_sl_oid
                        self.positions[symbol]["trailing_stop"] = new_sl
                    elif symbol in self.positions:
                        self.positions[symbol]["sl_oid"] = new_sl_oid
                        self.positions[symbol]["trailing_stop"] = new_sl
                    direction = "UP" if side == "long" else "DOWN"
                    logger.info(f"🔒 ADAPTIVE SL TRAILED {direction} ({sl_reason}): {symbol} SL ${current_sl:,.2f} → ${new_sl:,.2f}")

        # === DEEPSEEK EXIT ANALYSIS: Let AI decide when to take profit ===
        # Only analyze exit when position is profitable (>1%) to avoid excessive API calls
        if deepseek_exit and pnl_pct >= 1.0:
            # Check if we've analyzed recently (rate limit: every 2 minutes)
            last_exit_check = pos_data.get("last_exit_check")
            now = datetime.utcnow()
            should_check = True
            if last_exit_check:
                if isinstance(last_exit_check, datetime):
                    time_since_check = (now - last_exit_check).total_seconds()
                    should_check = time_since_check >= 120  # 2 minutes

            if should_check:
                logger.info(f"🤖 Asking DeepSeek: Should we exit {symbol}? P&L: {pnl_pct:+.2f}%")

                # Build position data for exit analysis
                exit_position_data = {
                    "side": side,
                    "entry_price": entry_price,
                    "pnl_pct": pnl_pct,
                    "best_price": new_best,
                    "entry_time": pos_data.get("entry_time")
                }

                # Call DeepSeek exit analyzer
                exit_decision = self.llm.analyze_exit(exit_position_data, market_data)

                # Update last check time
                if symbol in self.positions:
                    self.positions[symbol]["last_exit_check"] = now

                # Act on decision
                if exit_decision["action"] == "exit" and exit_decision["confidence"] >= 0.70:
                    logger.info(f"🎯 DEEPSEEK EXIT SIGNAL: {exit_decision['reasoning'][:100]}")
                    logger.info(f"   Confidence: {exit_decision['confidence']:.0%}")

                    # Close position at market
                    close_side = "sell" if side == "long" else "buy"
                    close_result = self.hl.place_market_order(symbol, close_side, size)

                    if close_result.get("success"):
                        logger.info(f"✅ POSITION CLOSED BY DEEPSEEK: {symbol} @ ${price:,.2f} | P&L: {pnl_pct:+.2f}%")

                        # Cancel the SL order since position is closed
                        if sl_oid:
                            self.hl.cancel_order(symbol, sl_oid)

                        # Cleanup
                        self._cleanup_position_tracking(symbol, side, pnl_pct)
                        return
                    else:
                        logger.warning(f"❌ Failed to close position: {close_result.get('error')}")
                else:
                    logger.info(f"🏃 DEEPSEEK: Let it run! ({exit_decision['action']} @ {exit_decision['confidence']:.0%})")

        # === EMERGENCY EXIT: If giving back too much from peak ===
        # If we were up 5%+ and now giving back more than 40% of gains, exit
        if pnl_pct >= 1.0 and new_best > entry_price:
            peak_pnl = ((new_best - entry_price) / entry_price * 100) if side == "long" else ((entry_price - new_best) / entry_price * 100)
            if peak_pnl >= 5.0:
                drawdown_from_peak = peak_pnl - pnl_pct
                if drawdown_from_peak >= peak_pnl * 0.4:  # Giving back 40%+ of gains
                    logger.warning(f"⚠️ EMERGENCY EXIT: Giving back {drawdown_from_peak:.1f}% from {peak_pnl:.1f}% peak")
                    close_side = "sell" if side == "long" else "buy"
                    close_result = self.hl.place_market_order(symbol, close_side, size)
                    if close_result.get("success"):
                        logger.info(f"✅ EMERGENCY EXIT: {symbol} @ ${price:,.2f} | P&L: {pnl_pct:+.2f}%")
                        if sl_oid:
                            self.hl.cancel_order(symbol, sl_oid)
                        self._cleanup_position_tracking(symbol, side, pnl_pct)
                        return

        # Update best/worst price tracking for MFE/MAE
        now = datetime.utcnow()
        if price_moved_favorably:
            if symbol in self.positions:
                self.positions[symbol]["best_price"] = new_best
                self.positions[symbol]["best_price_time"] = now
            elif symbol in self.positions:
                self.positions[symbol]["best_price"] = new_best
                self.positions[symbol]["best_price_time"] = now

        # Always track worst price (MAE)
        if new_worst != worst_price:
            if symbol in self.positions:
                self.positions[symbol]["worst_price"] = new_worst
                self.positions[symbol]["worst_price_time"] = now
            elif symbol in self.positions:
                self.positions[symbol]["worst_price"] = new_worst
                self.positions[symbol]["worst_price_time"] = now

        # === PYRAMID INTO WINNERS ===
        if self.config.pyramid_enabled and pnl_pct >= self.config.pyramid_trigger_pct:
            await self._check_pyramid_opportunity(symbol, pos, pnl_pct, market_data)

        exit_info = "DeepSeek decides exit" if deepseek_exit else "Trailing TP"
        logger.info(f"✅ HELD: SL protects | {exit_info} | P&L: {pnl_pct:+.2f}%")

    def _cleanup_position_tracking(self, symbol: str, side: str, pnl_pct: float) -> None:
        """Clean up tracking state after position closes and record trade with MFE/MAE."""
        # Record the trade for cooldown tracking
        self._record_trade(symbol, side)

        # Get position data before cleanup for MFE/MAE recording
        pos_data = self.positions.get(symbol) or self.positions.get(symbol) or {}
        entry_price = pos_data.get("entry_price", 0)
        entry_time = pos_data.get("entry_time", datetime.utcnow())
        size = pos_data.get("size", 0)
        entry_conditions = pos_data.get("entry_conditions")  # May be None

        # Calculate MFE/MAE from tracked best/worst prices
        best_price = pos_data.get("best_price", entry_price)
        worst_price = pos_data.get("worst_price", entry_price)
        best_time = pos_data.get("best_price_time", entry_time)
        worst_time = pos_data.get("worst_price_time", entry_time)

        mfe_pct = 0.0
        mae_pct = 0.0
        if entry_price > 0:
            if side == "long":
                mfe_pct = ((best_price - entry_price) / entry_price) * 100 if best_price > entry_price else 0
                mae_pct = ((worst_price - entry_price) / entry_price) * 100 if worst_price < entry_price else 0
            else:  # short
                mfe_pct = ((entry_price - best_price) / entry_price) * 100 if best_price < entry_price else 0
                mae_pct = ((entry_price - worst_price) / entry_price) * 100 if worst_price > entry_price else 0

        # Calculate time to MFE/MAE
        time_to_mfe = int((best_time - entry_time).total_seconds() / 60) if isinstance(best_time, datetime) and isinstance(entry_time, datetime) else 0
        time_to_mae = int((worst_time - entry_time).total_seconds() / 60) if isinstance(worst_time, datetime) and isinstance(entry_time, datetime) else 0

        # Get current price as exit price
        current_price = self.hl.get_price(symbol) or entry_price

        # Record trade to performance tracker with MFE/MAE
        if entry_price > 0 and size > 0:
            self.perf_tracker.record_trade(
                symbol=symbol,
                side=side,
                entry_price=entry_price,
                exit_price=current_price,
                size=size,
                entry_time=entry_time if isinstance(entry_time, datetime) else datetime.utcnow(),
                exit_reason="exchange_sltp",
                entry_conditions=entry_conditions,
                mfe_pct=mfe_pct,
                mae_pct=mae_pct,
                time_to_mfe_minutes=max(0, time_to_mfe),
                time_to_mae_minutes=max(0, time_to_mae)
            )
            logger.info(f"📈 MFE/MAE: Best={mfe_pct:+.2f}% Worst={mae_pct:+.2f}% | Time to best: {time_to_mfe}m")

        logger.info(f"🏁 Position closed by exchange: {symbol} {side.upper()} | P&L: {pnl_pct:+.2f}%")

        # Clean up all tracking
        if symbol in self.positions:
            del self.positions[symbol]
        if symbol in self.positions:
            del self.positions[symbol]
        if symbol in self.active_thesis:
            del self.active_thesis[symbol]
        if symbol in self.trailing_stops:
            del self.trailing_stops[symbol]
        if symbol in self.partial_taken:
            del self.partial_taken[symbol]
        if symbol in self.pyramid_adds:
            del self.pyramid_adds[symbol]
        if symbol in self.pyramid_entries:
            del self.pyramid_entries[symbol]

        # Update risk manager - clear position for this symbol
        self.risk_manager.record_trade_result(pnl_pct)
        self.risk_manager.update_position(symbol, None)

    async def _manage_position_legacy(self, symbol: str, market_data: Dict) -> None:
        """Handle position without local tracking - check exchange for existing SL/TP.

        This is called when we detect a position but don't have it in self.positions.
        This can happen if:
        1. Snipe filled but _check_snipe_fills hasn't run yet
        2. Bot restarted with open position
        3. Manual trade

        We check the exchange for existing SL/TP orders and register them.
        We do NOT place new SL/TP to avoid duplicates - the entry should have them.
        """
        pos = self._get_position_info(symbol)
        price = market_data["price"]
        side = pos["side"]
        size = pos.get("abs_size", 0)
        entry_price = pos.get("entry_price", price)

        logger.info(f"🔍 {symbol} position detected without local tracking - checking exchange for SL/TP...")

        # Check exchange for existing trigger orders (SL/TP)
        open_orders_result = self.hl.get_open_orders()
        if not open_orders_result.get("success"):
            logger.warning(f"⚠️ Could not check open orders for {symbol}")
            # Register position anyway to prevent repeated checks
            self.positions[symbol] = {
                "side": side,
                "entry_price": entry_price,
                "size": size,
                "entry_time": datetime.utcnow(),
                "native_sltp": True,  # Assume it has SL/TP from entry
            }
            return

        open_orders = open_orders_result.get("result", [])
        symbol_orders = [o for o in open_orders if o.get("coin") == symbol]

        # Find existing SL/TP trigger orders
        existing_sl = None
        existing_tp = None
        sl_price = None
        tp_price = None

        for order in symbol_orders:
            # Check if this is a trigger order (has triggerPx field)
            trigger_px = order.get("triggerPx")
            if not trigger_px:
                continue

            trigger_px = float(trigger_px)
            order_is_buy = order.get("side", "").upper() == "B"
            is_reduce_only = order.get("reduceOnly", False)

            # A closing order is opposite side of position
            is_closing = (side == "long" and not order_is_buy) or (side == "short" and order_is_buy)

            if is_closing and is_reduce_only:
                # Determine if SL or TP based on trigger price vs entry
                if side == "long":
                    if trigger_px < entry_price:
                        existing_sl = order.get("oid")
                        sl_price = trigger_px
                    else:
                        existing_tp = order.get("oid")
                        tp_price = trigger_px
                else:  # short
                    if trigger_px > entry_price:
                        existing_sl = order.get("oid")
                        sl_price = trigger_px
                    else:
                        existing_tp = order.get("oid")
                        tp_price = trigger_px

        # Register position with whatever SL/TP we found
        self.positions[symbol] = {
            "side": side,
            "entry_price": entry_price,
            "size": size,
            "entry_time": datetime.utcnow(),
            "best_price": entry_price,
            "native_sltp": True,
            "sl_oid": existing_sl,
            "tp_oid": existing_tp,
            "stop_loss": sl_price,
            "take_profit": tp_price,
            "current_tp_price": tp_price,
        }

        if existing_sl and existing_tp:
            logger.info(f"✅ Found SL/TP on exchange: SL=${sl_price:,.2f} (oid={existing_sl}) | TP=${tp_price:,.2f} (oid={existing_tp})")
        elif existing_sl:
            logger.warning(f"⚠️ Found SL but no TP: SL=${sl_price:,.2f} (oid={existing_sl})")
        elif existing_tp:
            logger.warning(f"⚠️ Found TP but no SL: TP=${tp_price:,.2f} (oid={existing_tp})")
        else:
            logger.warning(f"⚠️ No SL/TP found on exchange for {symbol} - position may be unprotected!")

        logger.info(f"📌 Position registered for tracking")

    def _update_swing_trail(self, symbol: str, side: str, price: float, trail_info: Dict) -> None:
        """Update trailing stop for swing position."""
        if side == "long":
            hwm = trail_info.get("high_water_mark", price)
            if price > hwm:
                # New high - update trail
                new_stop = price * (1 - self.config.trailing_stop_distance_pct / 100)
                self.trailing_stops[symbol]["high_water_mark"] = price
                self.trailing_stops[symbol]["stop_price"] = new_stop
                logger.info(f"📈 SWING TRAIL UP: {symbol} stop raised to ${new_stop:.2f}")
        else:  # short
            lwm = trail_info.get("low_water_mark", price)
            if price < lwm:
                # New low - update trail
                new_stop = price * (1 + self.config.trailing_stop_distance_pct / 100)
                self.trailing_stops[symbol]["low_water_mark"] = price
                self.trailing_stops[symbol]["stop_price"] = new_stop
                logger.info(f"📉 SWING TRAIL DOWN: {symbol} stop lowered to ${new_stop:.2f}")

    def _check_trend_alignment(self, symbol: str, side: str, market_data: Dict) -> tuple:
        """Check if position is aligned with current trend. Returns (aligned, reason).

        KEY INSIGHT: Trust 5m momentum more - it shows real-time reversals.
        - If 5m trend strongly flips against us (score >= 70) = CLOSE
        - If 1h macro flips against us = MAJOR reversal signal
        - If 15m + 5m both flip against us = medium reversal
        """
        # For scalping: 5m = fast, 15m = mid, 1h = macro
        ema_5m = market_data.get("ema_fast_signal", "neutral")
        ema_15m = market_data.get("ema_mid_signal", "neutral")
        ema_1h = market_data.get("ema_macro_signal", "neutral")
        rsi = market_data.get("rsi", 50)

        # 5m TREND - most important for short-term reversals
        trend_5m = market_data.get("trend_5m", {})
        trend_5m_direction = trend_5m.get("trend", "neutral")
        trend_5m_score = trend_5m.get("score", 0)

        # Log current signals for debugging
        logger.debug(f"Trend check {side}: 5m={ema_5m}({trend_5m_score}), 15m={ema_15m}, 1h={ema_1h}, RSI={rsi:.0f}")

        if side == "long":
            # === STRONG 5m REVERSAL: Close if 5m bearish with decent score ===
            # PROACTIVE: Exit at 60+ (was 70) to catch reversals EARLY
            if trend_5m_direction == "bearish" and trend_5m_score >= 60:
                reasons = trend_5m.get("reasons", [])
                logger.warning(f"⚠️ 5m REVERSAL DETECTED: {trend_5m_score}/100 bearish | {reasons[0] if reasons else 'momentum flip'}")
                return False, f"5m_reversal_bearish_{trend_5m_score}"

            # MACRO FLIP: 1h trend turned bearish = close long
            if ema_1h == "bearish":
                # If 1h is bearish and RSI is not oversold, trend has changed
                if rsi > 35:  # Not oversold = not bouncing
                    return False, f"1h_trend_bearish_rsi_{rsi:.0f}"

            # DUAL FLIP: Both 15m and 5m bearish while 1h neutral
            if ema_15m == "bearish" and ema_5m == "bearish" and rsi > 50:
                return False, "dual_timeframe_bearish"

        elif side == "short":
            # === STRONG 5m REVERSAL: Close if 5m bullish with decent score ===
            # PROACTIVE: Exit at 60+ (was 70) to catch reversals EARLY
            if trend_5m_direction == "bullish" and trend_5m_score >= 60:
                reasons = trend_5m.get("reasons", [])
                logger.warning(f"⚠️ 5m REVERSAL DETECTED: {trend_5m_score}/100 bullish | {reasons[0] if reasons else 'momentum flip'}")
                return False, f"5m_reversal_bullish_{trend_5m_score}"

            # MACRO FLIP: 1h trend turned bullish = close short
            if ema_1h == "bullish":
                # If 1h is bullish and RSI is not overbought, trend has changed
                if rsi < 65:  # Not overbought = uptrend intact
                    return False, f"1h_trend_bullish_rsi_{rsi:.0f}"

            # DUAL FLIP: Both 15m and 5m bullish while 1h neutral
            if ema_15m == "bullish" and ema_5m == "bullish" and rsi < 50:
                return False, "dual_timeframe_bullish"

        return True, "aligned"

    async def _check_scale_in(self, symbol: str, current_price: float) -> None:
        """Check if we should scale into position on dip."""
        if symbol not in self.pending_scales:
            return

        scale_info = self.pending_scales[symbol]
        if scale_info["tranches_remaining"] <= 0:
            return

        side = scale_info["side"]
        next_scale_price = scale_info["next_scale_price"]

        # Check if price has dipped enough for scale-in
        should_scale = False
        if side == "long" and current_price <= next_scale_price:
            should_scale = True
        elif side == "short" and current_price >= next_scale_price:
            should_scale = True

        if not should_scale:
            return

        # Execute scale-in
        size = scale_info["tranche_size"]
        tranche_num = self.scale_tranches - scale_info["tranches_remaining"] + 1

        logger.info(f"\n>>> SCALE-IN {side.upper()} {symbol} (TRANCHE {tranche_num}/{self.scale_tranches}) <<<")
        logger.info(f"Price dipped to ${current_price:.2f} (target was ${next_scale_price:.2f})")

        if side == "long":
            result = self.hl.place_market_order(symbol, "buy", size)
        else:
            result = self.hl.place_market_order(symbol, "sell", size)

        if result.get("success"):
            logger.info(f"Scale-in executed: +{size:.6f} {symbol}")
            scale_info["tranches_remaining"] -= 1

            # Update next scale price
            if scale_info["tranches_remaining"] > 0:
                if side == "long":
                    scale_info["next_scale_price"] = current_price * (1 - self.scale_dip_pct / 100)
                else:
                    scale_info["next_scale_price"] = current_price * (1 + self.scale_dip_pct / 100)
                logger.info(f"Next scale-in at ${scale_info['next_scale_price']:.2f}")
            else:
                logger.info(f">>> FULL POSITION BUILT: All {self.scale_tranches} tranches filled <<<")
        else:
            logger.error(f"Scale-in failed: {result.get('error')}")

    async def _check_pyramid_opportunity(self, symbol: str, pos: Dict, pnl_pct: float, market_data: Dict) -> None:
        """Check if we should pyramid (add to) a winning position.

        Pyramiding rules:
        - Only add to winners (position must be profitable by pyramid_trigger_pct)
        - Maximum pyramid_max_adds additions per position
        - Add pyramid_size_pct of original position size
        - Trend must still be aligned
        """
        # Check if pyramiding is enabled and we haven't maxed out adds
        current_adds = self.pyramid_adds.get(symbol, 0)
        if current_adds >= self.config.pyramid_max_adds:
            return

        # Check if position is profitable enough to pyramid
        if pnl_pct < self.config.pyramid_trigger_pct:
            return

        # Check trend alignment before adding
        trend_aligned, _ = self._check_trend_alignment(symbol, pos["side"], market_data)
        if not trend_aligned:
            logger.info(f"⏸️ Pyramid blocked: trend not aligned for {symbol}")
            return

        # Check visual analysis confirms trend (if available)
        visual_trend = market_data.get("visual_trend", "neutral")
        if pos["side"] == "long" and visual_trend == "bearish":
            logger.info(f"⏸️ Pyramid blocked: visual trend bearish")
            return
        elif pos["side"] == "short" and visual_trend == "bullish":
            logger.info(f"⏸️ Pyramid blocked: visual trend bullish")
            return

        # Calculate pyramid size (% of original position)
        original_size = pos.get("abs_size", 0)
        if current_adds > 0 and symbol in self.pyramid_entries:
            # Use original entry size, not current inflated size
            original_size = self.pyramid_entries[symbol][0].get("size", original_size)

        pyramid_size = original_size * (self.config.pyramid_size_pct / 100)

        # Ensure minimum order size
        price = market_data.get("price", 0)
        if price > 0 and pyramid_size * price < self.config.min_order_value_usd:
            logger.info(f"⏸️ Pyramid size too small: ${pyramid_size * price:.2f}")
            return

        # Execute pyramid add
        logger.info(f"\n🔺 PYRAMID ADD #{current_adds + 1} for {symbol}")
        logger.info(f"   Position +{pnl_pct:.2f}% profitable - adding {self.config.pyramid_size_pct}% ({pyramid_size:.6f})")

        side_action = "buy" if pos["side"] == "long" else "sell"
        result = self.hl.place_market_order(symbol, side_action, pyramid_size)

        if result.get("success"):
            # Track the pyramid add
            self.pyramid_adds[symbol] = current_adds + 1
            if symbol not in self.pyramid_entries:
                self.pyramid_entries[symbol] = [{"size": original_size, "price": pos.get("entry_price", price)}]
            self.pyramid_entries[symbol].append({"size": pyramid_size, "price": price})

            logger.info(f"✅ Pyramid executed: +{pyramid_size:.6f} {symbol} @ ${price:.2f}")
            logger.info(f"   Total position now larger - trailing stop will protect gains")
        else:
            logger.error(f"❌ Pyramid failed: {result.get('error')}")

    def _build_thesis(self, symbol: str, side: str, market_data: Dict, llm_reasoning: str = "", thesis_summary: str = "") -> Dict:
        """Build a comprehensive trading thesis for mid-to-long term positions.

        The thesis documents:
        - WHY we're entering (fundamental reasoning)
        - Entry conditions that were met
        - Target exit price
        - Stop loss level
        - What would invalidate the thesis
        """
        entry_price = market_data["price"]
        macro_signal = market_data.get("ema_macro_signal", "neutral")
        mid_signal = market_data.get("ema_mid_signal", "neutral")
        rsi = market_data.get("rsi", 50)
        funding = market_data.get("funding_rate_8h", 0)

        # Calculate target and stop based on config
        if side == "long":
            target_price = entry_price * (1 + self.config.take_profit_pct / 100)
            stop_price = entry_price * (1 + self.config.stop_loss_pct / 100)
        else:
            target_price = entry_price * (1 - self.config.take_profit_pct / 100)
            stop_price = entry_price * (1 - self.config.stop_loss_pct / 100)

        # Build default thesis summary if not provided by LLM
        default_summary = f"{side.upper()} {symbol} @ ${entry_price:.2f} | Target: ${target_price:.2f} (+{self.config.take_profit_pct}%) | Stop: ${stop_price:.2f} ({self.config.stop_loss_pct}%) | Exit if 4H EMA flips or RSI extreme"

        thesis = {
            "side": side,
            "entry_time": datetime.utcnow(),
            "entry_price": entry_price,
            "target_price": target_price,
            "stop_price": stop_price,
            # Entry conditions
            "entry_macro_signal": macro_signal,
            "entry_mid_signal": mid_signal,
            "entry_rsi": rsi,
            "entry_funding": funding,
            # The core thesis reasoning
            "reasoning": llm_reasoning or f"Macro trend {macro_signal}, mid-term {mid_signal}, RSI {rsi:.0f}",
            # Short action summary for the bot to follow
            "thesis_summary": thesis_summary or default_summary,
            "summary": f"{side.upper()} @ ${entry_price:.2f} | Target: ${target_price:.2f} ({self.config.take_profit_pct}%) | Stop: ${stop_price:.2f} ({self.config.stop_loss_pct}%)",
            # Invalidation criteria
            "invalidate_if_macro_flips": True,
            "invalidate_rsi_extreme": 80 if side == "long" else 20,
        }

        # Log the full thesis
        logger.info("=" * 60)
        logger.info(f"TRADING THESIS ESTABLISHED")
        logger.info("=" * 60)
        logger.info(f"Symbol: {symbol}")
        logger.info(f"Direction: {side.upper()}")
        logger.info(f"Entry Price: ${entry_price:.2f}")
        logger.info(f"Target Price: ${target_price:.2f} ({self.config.take_profit_pct}%)")
        logger.info(f"Stop Loss: ${stop_price:.2f} ({self.config.stop_loss_pct}%)")
        logger.info(f"4h:{macro_signal} | 1h:{mid_signal} | RSI:{rsi:.0f}" if rsi else f"4h:{macro_signal} | 1h:{mid_signal}")
        logger.info(f">>> {thesis['thesis_summary']} <<<")

        return thesis

    def _check_thesis_validity(self, symbol: str, side: str, market_data: Dict, thesis: Dict) -> tuple:
        """Check if the trading thesis is still valid. Returns (is_valid, reason).

        TREND-FOLLOWING: We want to let winners run. Only invalidate on EXTREME conditions.
        The trailing stop handles profit protection - thesis check is for MAJOR reversals only.
        """
        rsi = market_data.get("rsi", 50)

        # Check how long we've been in the position
        entry_time = thesis.get("entry_time")
        minutes_in_trade = 0
        if entry_time:
            minutes_in_trade = (datetime.utcnow() - entry_time).total_seconds() / 60

        # GRACE PERIOD: Never invalidate in first 10 minutes
        # This prevents noise-based exits and lets the trade develop
        if minutes_in_trade < 10:
            return True, None

        # RSI EXTREME ONLY - clear momentum exhaustion
        # Only exit on very extreme RSI after position has had time to develop
        if rsi is not None and minutes_in_trade > 15:
            if side == "long" and rsi >= 80:  # Very overbought
                return False, f"rsi_extreme_{rsi:.0f}"
            if side == "short" and rsi <= 20:  # Very oversold
                return False, f"rsi_extreme_{rsi:.0f}"

        # Thesis still valid - let the trade play out
        return True, None

    def _close_and_record(self, symbol: str, side: str, reason: str) -> None:
        """Close position and record for cooldown prevention + performance tracking."""
        # Get position info before closing
        pos = self._get_position_info(symbol)
        entry_price = pos.get("entry_price", 0)
        entry_time = self.active_thesis.get(symbol, {}).get("entry_time", datetime.utcnow())
        size = pos.get("abs_size", 0)

        # Get entry conditions if we stored them (for learning)
        entry_conditions = self.pending_entry_conditions.pop(symbol, None)

        result = self.hl.close_position(symbol)
        if result.get("success"):
            # Get exit price
            exit_price = self.hl.get_price(symbol) or entry_price

            # Calculate P&L for risk manager
            pnl_pct = 0.0
            if entry_price > 0:
                if side == "long":
                    pnl_pct = ((exit_price - entry_price) / entry_price) * 100
                else:
                    pnl_pct = ((entry_price - exit_price) / entry_price) * 100

            # Record trade for performance tracking WITH entry conditions
            if entry_price > 0 and size > 0:
                self.perf_tracker.record_trade(
                    symbol=symbol,
                    side=side,
                    entry_price=entry_price,
                    exit_price=exit_price,
                    size=size,
                    entry_time=entry_time if isinstance(entry_time, datetime) else datetime.utcnow(),
                    exit_reason=reason,
                    entry_conditions=entry_conditions  # For learning!
                )
                # Update equity tracking
                state = self.hl.get_account_state()
                self.perf_tracker.update_equity(state['equity'])

                # Re-analyze patterns after EVERY trade (real-time learning)
                if self.use_learning:
                    logger.info("🧠 Real-time learning: Re-analyzing trade patterns...")
                    self.trade_analyzer.analyze_patterns()
                    # Log key insights from the updated analysis
                    thresholds = self.trade_analyzer.get_learned_thresholds()
                    if thresholds.get("status") == "learned":
                        logger.info(f"   📊 Updated: RSI short<{thresholds.get('rsi_short_max')} | long>{thresholds.get('rsi_long_min')}")
                        if thresholds.get("avoid_regime"):
                            logger.info(f"   ⚠️ Avoid regime: {thresholds['avoid_regime']}")

            logger.info(f"✅ Position closed - reason: {reason}")
            self._record_trade(symbol, side, exit_price)  # Track exit price for re-entry logic

            # === UPDATE RISK MANAGER ===
            self.risk_manager.record_trade_result(pnl_pct)
            self.risk_manager.update_position(symbol, None)  # Clear position

            # === CLEAN UP ALL TRACKING STATE ===
            if symbol in self.active_thesis:
                del self.active_thesis[symbol]
            if symbol in self.pending_scales:
                del self.pending_scales[symbol]
            if symbol in self.trailing_stops:
                del self.trailing_stops[symbol]
            if symbol in self.partial_taken:
                del self.partial_taken[symbol]
            if symbol in self.atr_cache:
                del self.atr_cache[symbol]
            # Reset pyramid tracking
            if symbol in self.pyramid_adds:
                del self.pyramid_adds[symbol]
            if symbol in self.pyramid_entries:
                del self.pyramid_entries[symbol]
        else:
            logger.error(f"Failed to close: {result.get('error')}")

    def _calculate_quant_score(self, market_data: Dict) -> Dict[str, Any]:
        """
        Calculate a pure quantitative score from technical indicators.
        This provides an objective baseline that doesn't require LLM interpretation.

        Returns:
            Dict with:
                - score: 0-100 (absolute strength)
                - direction: "bullish", "bearish", or "neutral"
                - signals: List of contributing signals
                - confidence: How reliable this score is (based on signal agreement)
        """
        bullish = 0
        bearish = 0
        signals = []

        # === TREND INDICATORS (40 points max) ===
        # EMA signals across timeframes
        ema_5m = market_data.get("ema_fast_signal", "neutral")
        ema_15m = market_data.get("ema_mid_signal", "neutral")
        ema_1h = market_data.get("ema_macro_signal", "neutral")

        if ema_1h == "bullish":
            bullish += 20
            signals.append("1H EMA bullish")
        elif ema_1h == "bearish":
            bearish += 20
            signals.append("1H EMA bearish")

        if ema_15m == "bullish":
            bullish += 12
            signals.append("15M EMA bullish")
        elif ema_15m == "bearish":
            bearish += 12
            signals.append("15M EMA bearish")

        if ema_5m == "bullish":
            bullish += 8
            signals.append("5M EMA bullish")
        elif ema_5m == "bearish":
            bearish += 8
            signals.append("5M EMA bearish")

        # === MOMENTUM INDICATORS (30 points max) ===
        # RSI
        rsi = market_data.get("rsi", 50)
        if rsi < 30:
            bullish += 15  # Oversold = bullish
            signals.append(f"RSI oversold ({rsi:.0f})")
        elif rsi > 70:
            bearish += 15  # Overbought = bearish
            signals.append(f"RSI overbought ({rsi:.0f})")
        elif rsi < 45:
            bullish += 5
        elif rsi > 55:
            bearish += 5

        # MACD
        macd_signal = market_data.get("macd_signal", "neutral")
        if macd_signal == "bullish":
            bullish += 10
            signals.append("MACD bullish")
        elif macd_signal == "bearish":
            bearish += 10
            signals.append("MACD bearish")

        # ADX - Trend strength
        adx = market_data.get("adx", 20)
        adx_direction = market_data.get("adx_trend_direction", "neutral")
        if adx and adx > 25:  # Strong trend
            if adx_direction == "bullish":
                bullish += 5
                signals.append(f"ADX strong bullish ({adx:.0f})")
            elif adx_direction == "bearish":
                bearish += 5
                signals.append(f"ADX strong bearish ({adx:.0f})")

        # === PRICE STRUCTURE (20 points max) ===
        # Bollinger Band position
        bb_position = market_data.get("bb_position", 0.5)
        if bb_position is not None:
            if bb_position < 0.2:
                bullish += 10  # Near lower band = bounce potential
                signals.append(f"BB oversold ({bb_position:.0%})")
            elif bb_position > 0.8:
                bearish += 10  # Near upper band = rejection potential
                signals.append(f"BB overbought ({bb_position:.0%})")

        # VWAP
        vwap_signal = market_data.get("vwap_signal", "neutral")
        if vwap_signal == "bullish" or vwap_signal == "oversold":
            bullish += 5
            signals.append("Below VWAP (bullish)")
        elif vwap_signal == "bearish" or vwap_signal == "overbought":
            bearish += 5
            signals.append("Above VWAP (bearish)")

        # Ichimoku
        ichimoku_signal = market_data.get("ichimoku_signal", "neutral")
        if ichimoku_signal == "bullish":
            bullish += 5
            signals.append("Ichimoku bullish")
        elif ichimoku_signal == "bearish":
            bearish += 5
            signals.append("Ichimoku bearish")

        # === ORDER FLOW (10 points max) ===
        # CVD
        cvd_signal = market_data.get("cvd_signal", "neutral")
        if cvd_signal == "bullish":
            bullish += 5
            signals.append("CVD bullish (buying pressure)")
        elif cvd_signal == "bearish":
            bearish += 5
            signals.append("CVD bearish (selling pressure)")

        # Order book imbalance
        ob_bias = market_data.get("ob_bias", "neutral")
        if ob_bias == "bullish":
            bullish += 5
            signals.append("Order book bullish")
        elif ob_bias == "bearish":
            bearish += 5
            signals.append("Order book bearish")

        # === SMART MONEY CONCEPTS (15 points max) ===
        smc_bias = market_data.get("smc_bias", "neutral")
        smc_conf = market_data.get("smc_confidence", 0)
        if smc_bias == "bullish" and smc_conf > 0.5:
            bullish += int(15 * smc_conf)
            signals.append(f"SMC bullish ({smc_conf:.0%})")
        elif smc_bias == "bearish" and smc_conf > 0.5:
            bearish += int(15 * smc_conf)
            signals.append(f"SMC bearish ({smc_conf:.0%})")

        # === VOLUME PROFILE (10 points max) ===
        vp_bias = market_data.get("vp_bias", "neutral")
        vp_position = market_data.get("vp_position", "inside_value")
        if "bullish" in str(vp_bias):
            bullish += 10
            signals.append(f"VP {vp_bias} ({vp_position})")
        elif "bearish" in str(vp_bias):
            bearish += 10
            signals.append(f"VP {vp_bias} ({vp_position})")

        # === BAYESIAN AGGREGATION (15 points max) ===
        bayesian_dir = market_data.get("bayesian_direction", "neutral")
        bayesian_conf = market_data.get("bayesian_confidence", 0)
        bayesian_quality = market_data.get("bayesian_quality", "low")
        if bayesian_dir == "bullish" and bayesian_conf > 0.3:
            quality_mult = 1.0 if bayesian_quality == "high" else 0.7 if bayesian_quality == "medium" else 0.5
            bullish += int(15 * bayesian_conf * quality_mult)
            signals.append(f"Bayesian bullish ({bayesian_conf:.0%} {bayesian_quality})")
        elif bayesian_dir == "bearish" and bayesian_conf > 0.3:
            quality_mult = 1.0 if bayesian_quality == "high" else 0.7 if bayesian_quality == "medium" else 0.5
            bearish += int(15 * bayesian_conf * quality_mult)
            signals.append(f"Bayesian bearish ({bayesian_conf:.0%} {bayesian_quality})")

        # === ADVANCED PATTERNS (20 points max) ===
        # Fibonacci levels
        fib_signal = market_data.get("fib_signal", "neutral")
        if fib_signal == "bullish" or fib_signal == "at_support":
            bullish += 8
            fib_level = market_data.get("fib_nearest_level", "")
            signals.append(f"Fib {fib_signal} ({fib_level})")
        elif fib_signal == "bearish" or fib_signal == "at_resistance":
            bearish += 8
            fib_level = market_data.get("fib_nearest_level", "")
            signals.append(f"Fib {fib_signal} ({fib_level})")

        # Harmonic Patterns (high-probability reversal signals)
        harmonic_signal = market_data.get("harmonic_signal", "neutral")
        harmonic_pattern = market_data.get("harmonic_pattern", "")
        if harmonic_signal == "bullish" and harmonic_pattern:
            bullish += 10
            signals.append(f"Harmonic {harmonic_pattern} bullish")
        elif harmonic_signal == "bearish" and harmonic_pattern:
            bearish += 10
            signals.append(f"Harmonic {harmonic_pattern} bearish")

        # Wyckoff Phase (smart money accumulation/distribution)
        wyckoff_signal = market_data.get("wyckoff_signal", "neutral")
        wyckoff_phase = market_data.get("wyckoff_phase", "")
        if wyckoff_signal == "bullish":
            bullish += 7
            signals.append(f"Wyckoff {wyckoff_phase} (accumulation)")
        elif wyckoff_signal == "bearish":
            bearish += 7
            signals.append(f"Wyckoff {wyckoff_phase} (distribution)")

        # === LIQUIDATION LEVELS (10 points max) ===
        liq_signal = market_data.get("liquidation_signal", "neutral")
        if liq_signal == "bullish":  # Near short liquidation zone = potential squeeze
            bullish += 10
            signals.append("Near short liquidation zone (squeeze potential)")
        elif liq_signal == "bearish":  # Near long liquidation zone = cascade risk
            bearish += 10
            signals.append("Near long liquidation zone (cascade risk)")

        # === CALCULATE FINAL SCORE ===
        total = bullish + bearish
        if total == 0:
            return {"score": 0, "direction": "neutral", "signals": [], "confidence": 0}

        # Direction is determined by which side has more points
        if bullish > bearish + 10:  # Need clear edge
            direction = "bullish"
            score = min(100, int((bullish / (bullish + bearish)) * 100))
        elif bearish > bullish + 10:
            direction = "bearish"
            score = min(100, int((bearish / (bullish + bearish)) * 100))
        else:
            direction = "neutral"
            score = 50

        # Confidence based on signal agreement
        agreement_ratio = max(bullish, bearish) / max(total, 1)
        confidence = int(agreement_ratio * 100)

        return {
            "score": score,
            "direction": direction,
            "signals": signals[:5],  # Top 5 signals
            "confidence": confidence,
            "bullish_points": bullish,
            "bearish_points": bearish
        }

    def _gather_market_data(self, symbol: str) -> Dict[str, Any]:
        """Gather all market data for analysis."""
        # Get price
        price = self.hl.get_price(symbol) or 0

        # Get account state
        state = self.hl.get_account_state()

        # Get orderbook
        book = self.hl.get_orderbook(symbol)

        # Calculate orderbook imbalance
        bid_vol = sum(float(b.get("sz", 0)) for b in book.get("bids", []))
        ask_vol = sum(float(a.get("sz", 0)) for a in book.get("asks", []))
        imbalance = (bid_vol - ask_vol) / (bid_vol + ask_vol + 0.001)

        # Get recent trades direction
        trades = self.hl.get_recent_trades(symbol, limit=20)
        buys = sum(1 for t in trades if t.get("side") == "B")
        # If no trades data, say "unknown" instead of defaulting to bearish
        trade_dir = "unknown" if len(trades) == 0 else ("bullish" if buys > 10 else "bearish" if buys < 10 else "mixed")

        # === MULTI-TIMEFRAME CANDLE DATA (1m, 5m, 15m, 30m, 1h, 4h, 1d) ===
        # 1m candles for ultra-fast momentum/exhaustion detection
        candles_1m = self.hl.get_candles(symbol, interval="1m", limit=60)
        # 5m candles for fast signals (primary for scalping)
        candles_5m = self.hl.get_candles(symbol, interval="5m", limit=100)
        # 15m candles for trend confirmation
        candles_15m = self.hl.get_candles(symbol, interval="15m", limit=100)
        # 30m candles for intermediate structure
        candles_30m = self.hl.get_candles(symbol, interval="30m", limit=60)
        # 1h for higher timeframe context
        candles_1h = self.hl.get_candles(symbol, interval="1h", limit=100)
        # 1d candles for major trend and key S/R
        candles_1d = self.hl.get_candles(symbol, interval="1d", limit=60)

        # RSI on 5m timeframe (fast momentum for scalping)
        rsi = calculate_rsi(candles_5m, period=14)
        rsi_signal = "neutral"
        if rsi is not None:
            if rsi > 70:  # More extreme for scalping
                rsi_signal = "overbought"
            elif rsi < 30:
                rsi_signal = "oversold"

        # FAST EMA Crossover (9/21 on 5m - PRIMARY for scalping entries)
        ema_fast = calculate_ema_crossover(candles_5m, fast=9, slow=21)

        # MID EMA Crossover (9/21 on 15m - trend confirmation)
        ema_mid = calculate_ema_crossover(candles_15m, fast=9, slow=21)

        # MACRO EMA Crossover (9/21 on 1h - higher timeframe context)
        ema_macro = calculate_ema_crossover(candles_1h, fast=9, slow=21)

        # Volume Profile on 15m (more relevant for scalping)
        volume_data = calculate_volume_profile(candles_15m, bins=10)

        # === SCALPING INDICATORS ===
        # MACD on 5m timeframe (fast signals)
        macd_data = calculate_macd(candles_5m, fast=12, slow=26, signal=9)

        # Bollinger Bands on 5m (for mean reversion scalps)
        bb_data = calculate_bollinger_bands(candles_5m, period=20, std_dev=2.0)

        # Support/Resistance levels from 15m (more relevant levels)
        sr_data = calculate_support_resistance(candles_15m, lookback=50)

        # ATR for volatility on 5m
        atr = calculate_atr(candles_5m, period=14)
        atr_pct = (atr / price * 100) if atr and price else 0

        # === ADVANCED INDICATORS ===
        # Get 4H candles for regime detection
        candles_4h = self.hl.get_candles(symbol, interval="4h", limit=60)

        # === MULTI-TIMEFRAME TREND ANALYSIS (1m, 5m, 30m, 1h, 4h, 1d) ===
        # 1m EMA for micro momentum
        ema_1m = calculate_ema_crossover(candles_1m, fast=9, slow=21) if candles_1m else {}
        rsi_1m = calculate_rsi(candles_1m, period=14) if candles_1m else None

        # 30m EMA for intermediate trend
        ema_30m = calculate_ema_crossover(candles_30m, fast=9, slow=21) if candles_30m else {}
        rsi_30m = calculate_rsi(candles_30m, period=14) if candles_30m else None

        # 4H EMA Crossover - macro trend direction
        ema_4h = calculate_ema_crossover(candles_4h, fast=9, slow=21)
        rsi_4h = calculate_rsi(candles_4h, period=14)

        # 1D EMA for major trend (use 21/50 for longer view)
        ema_1d = calculate_ema_crossover(candles_1d, fast=21, slow=50) if candles_1d else {}
        rsi_1d = calculate_rsi(candles_1d, period=14) if candles_1d else None

        # 1H RSI for additional confirmation
        rsi_1h = calculate_rsi(candles_1h, period=14)

        # Daily S/R levels (key institutional levels)
        sr_1d = calculate_support_resistance(candles_1d, lookback=30) if candles_1d else {}

        # VWAP - Institutional level (using 15m for intraday)
        vwap_data = calculate_vwap(candles_15m)

        # Ichimoku Cloud - Trend + momentum + S/R in one
        ichimoku_data = calculate_ichimoku(candles_1h)

        # ADX - Trend strength indicator
        adx_data = calculate_adx(candles_4h, period=14)

        # CVD - Cumulative Volume Delta (order flow)
        cvd_data = calculate_cvd(candles_15m)

        # Market Regime Detection (CRITICAL for strategy selection)
        market_regime = detect_market_regime(candles_4h, candles_1h)

        # === REVERSAL PREDICTION SIGNALS (KEY FOR SCALPING) ===
        rsi_divergence = detect_rsi_divergence(candles_5m, rsi_period=14, lookback=10)
        volume_exhaustion = detect_volume_exhaustion(candles_5m, lookback=5)
        reversal_setup = detect_reversal_setup(candles_5m, sr_data, bb_data)

        # Open Interest and Market Meta
        oi_data = self.hl.get_open_interest(symbol)
        market_meta = self.hl.get_market_meta(symbol)

        # Funding Rate
        funding = self.hl.get_funding_rate(symbol)
        funding_signal = "neutral"
        funding_8h = funding.get("funding_rate_8h", 0)
        if funding_8h > 0.01:  # >0.01% = longs paying
            funding_signal = "bearish"
        elif funding_8h < -0.01:  # <-0.01% = shorts paying
            funding_signal = "bullish"

        # Check current position
        position = "none"
        for pos in state.get("positions", []):
            p = pos.get("position") if isinstance(pos, dict) and isinstance(pos.get("position"), dict) else pos
            if isinstance(p, dict) and p.get("coin") == symbol:
                size = float(p.get("szi", 0) or 0)
                if size > 0:
                    position = f"long {size}"
                elif size < 0:
                    position = f"short {abs(size)}"

        return {
            "symbol": symbol,
            "price": price,
            "change_24h": 0,
            "trade_direction": trade_dir,
            "orderbook_imbalance": imbalance,
            "equity": state["equity"],
            "position": position,
            "bids": book.get("bids", []),
            "asks": book.get("asks", []),
            # FAST indicators (5m timeframe - PRIMARY for scalping)
            "rsi": rsi,
            "rsi_signal": rsi_signal,
            "ema_fast_signal": ema_fast.get("signal"),  # 5m EMA - fastest
            "ema_fast_spread_pct": ema_fast.get("spread_pct"),
            # MID indicators (15m timeframe - trend confirmation)
            "ema_mid_fast": ema_mid.get("ema_fast"),
            "ema_mid_slow": ema_mid.get("ema_slow"),
            "ema_mid_signal": ema_mid.get("signal"),
            "ema_mid_spread_pct": ema_mid.get("spread_pct"),
            # MACRO indicators (1h timeframe - higher TF context)
            "ema_macro_fast": ema_macro.get("ema_fast"),
            "ema_macro_slow": ema_macro.get("ema_slow"),
            "ema_macro_signal": ema_macro.get("signal"),
            "ema_macro_spread_pct": ema_macro.get("spread_pct"),
            # 4H indicators (for macro trend confirmation)
            "ema_4h_signal": ema_4h.get("signal"),
            "ema_4h_spread_pct": ema_4h.get("spread_pct"),
            "rsi_4h": rsi_4h,
            "rsi_1h": rsi_1h,
            # === NEW INDICATORS ===
            # MACD
            "macd_line": macd_data.get("macd_line"),
            "macd_signal_line": macd_data.get("signal_line"),
            "macd_histogram": macd_data.get("histogram"),
            "macd_signal": macd_data.get("signal"),
            # Bollinger Bands
            "bb_upper": bb_data.get("upper"),
            "bb_middle": bb_data.get("middle"),
            "bb_lower": bb_data.get("lower"),
            "bb_bandwidth": bb_data.get("bandwidth"),
            "bb_position": bb_data.get("band_position"),
            "bb_signal": bb_data.get("signal"),
            # Support/Resistance
            "nearest_resistance": sr_data.get("nearest_resistance"),
            "nearest_support": sr_data.get("nearest_support"),
            "resistances": sr_data.get("resistances", []),  # All resistance levels
            "supports": sr_data.get("supports", []),  # All support levels
            "dist_to_resistance_pct": sr_data.get("dist_to_resistance_pct"),
            "dist_to_support_pct": sr_data.get("dist_to_support_pct"),
            "sr_signal": sr_data.get("signal"),
            # NEW: Consolidation zone detection
            "is_building_support": sr_data.get("is_building_support", False),
            "is_building_resistance": sr_data.get("is_building_resistance", False),
            "consolidation_zone": sr_data.get("consolidation_zone"),
            # Volatility
            "atr": atr,
            "atr_pct": atr_pct,
            # Open Interest
            "open_interest": oi_data.get("open_interest"),
            "open_interest_usd": oi_data.get("open_interest_usd"),
            # Market Meta / Liquidation Levels
            "liq_long_10x": market_meta.get("liq_long_10x"),
            "liq_long_25x": market_meta.get("liq_long_25x"),
            "liq_short_10x": market_meta.get("liq_short_10x"),
            "liq_short_25x": market_meta.get("liq_short_25x"),
            "day_volume_usd": market_meta.get("day_ntl_vlm"),
            # Other
            "funding_rate_8h": funding_8h,
            "funding_signal": funding_signal,
            "volume_poc": volume_data.get("poc"),
            "volume_zone": volume_data.get("high_volume_zone"),
            "volume_signal": volume_data.get("profile"),
            # === REVERSAL PREDICTION SIGNALS ===
            "rsi_divergence": rsi_divergence.get("divergence", "none"),
            "rsi_divergence_signal": rsi_divergence.get("signal", "neutral"),
            "rsi_divergence_strength": rsi_divergence.get("strength", 0),
            "volume_exhaustion": volume_exhaustion.get("exhaustion", "none"),
            "volume_exhaustion_signal": volume_exhaustion.get("signal", "neutral"),
            "volume_exhaustion_strength": volume_exhaustion.get("strength", 0),
            "reversal_setup": reversal_setup.get("setup", "none"),
            "reversal_signal": reversal_setup.get("signal", "neutral"),
            "reversal_confidence": reversal_setup.get("confidence", 0),
            "reversal_signals": reversal_setup.get("signals", []),
            # === NEW ADVANCED INDICATORS ===
            # VWAP (Institutional Level)
            "vwap": vwap_data.get("vwap"),
            "vwap_upper_1": vwap_data.get("upper_band_1"),
            "vwap_upper_2": vwap_data.get("upper_band_2"),
            "vwap_lower_1": vwap_data.get("lower_band_1"),
            "vwap_lower_2": vwap_data.get("lower_band_2"),
            "vwap_deviation_pct": vwap_data.get("deviation_pct", 0),
            "vwap_signal": vwap_data.get("signal", "neutral"),
            # Ichimoku Cloud
            "ichimoku_tenkan": ichimoku_data.get("tenkan_sen"),
            "ichimoku_kijun": ichimoku_data.get("kijun_sen"),
            "ichimoku_cloud_top": ichimoku_data.get("cloud_top"),
            "ichimoku_cloud_bottom": ichimoku_data.get("cloud_bottom"),
            "ichimoku_signal": ichimoku_data.get("signal", "neutral"),
            "ichimoku_trend": ichimoku_data.get("trend", "unknown"),
            "ichimoku_bullish_score": ichimoku_data.get("bullish_score", 0),
            "ichimoku_bearish_score": ichimoku_data.get("bearish_score", 0),
            # ADX (Trend Strength)
            "adx": adx_data.get("adx"),
            "adx_plus_di": adx_data.get("plus_di"),
            "adx_minus_di": adx_data.get("minus_di"),
            "adx_trend_strength": adx_data.get("trend_strength", "unknown"),
            "adx_trend_direction": adx_data.get("trend_direction", "neutral"),
            "adx_is_trending": adx_data.get("is_trending", False),
            # CVD (Order Flow)
            "cvd": cvd_data.get("cvd"),
            "cvd_recent_delta": cvd_data.get("recent_delta"),
            "cvd_trend": cvd_data.get("cvd_trend", "unknown"),
            "cvd_divergence": cvd_data.get("divergence"),
            "cvd_signal": cvd_data.get("signal", "neutral"),
            # Market Regime (CRITICAL)
            "market_regime": market_regime.get("regime", "unknown"),
            "regime_strategy": market_regime.get("strategy", "none"),
            "regime_size_multiplier": market_regime.get("size_multiplier", 1.0),
            "regime_is_trending": market_regime.get("is_trending", False),
            "regime_is_ranging": market_regime.get("is_ranging", False),
            "regime_is_volatile": market_regime.get("is_volatile", False),
            "regime_signals": market_regime.get("signals", []),
            # === MULTI-TIMEFRAME DATA (1m, 5m, 15m, 30m, 1h, 4h, 1d) ===
            # 1m data
            "candles_1m": candles_1m,
            "ema_1m_signal": ema_1m.get("signal", "neutral") if ema_1m else "neutral",
            "rsi_1m": rsi_1m,
            # 5m data
            "candles_5m": candles_5m,
            # (ema_fast is already 5m EMA 9/21)
            # 15m data
            "candles_15m": candles_15m,
            # (ema_mid is already 15m EMA 9/21)
            # 30m data
            "candles_30m": candles_30m,
            "ema_30m_signal": ema_30m.get("signal", "neutral") if ema_30m else "neutral",
            "rsi_30m": rsi_30m,
            # 1h data
            "candles_1h": candles_1h,
            # (ema_macro is already 1h EMA 9/21)
            # 4h data
            "candles_4h": candles_4h,
            "ema_4h_signal": ema_4h.get("signal", "neutral") if ema_4h else "neutral",
            # (rsi_4h already included above)
            # 1d data (major trend)
            "candles_1d": candles_1d,
            "ema_1d_signal": ema_1d.get("signal", "neutral") if ema_1d else "neutral",
            "rsi_1d": rsi_1d,
            "sr_1d_supports": sr_1d.get("supports", []) if sr_1d else [],
            "sr_1d_resistances": sr_1d.get("resistances", []) if sr_1d else [],
        }

    async def _gather_market_data_async(self, symbol: str) -> Dict[str, Any]:
        """Gather all market data including alpha signals (async version)."""
        # Get base market data synchronously
        market_data = self._gather_market_data(symbol)

        # === LOG REVERSAL SIGNALS (KEY FOR SCALPING) ===
        reversal_setup = market_data.get("reversal_setup", "none")
        if reversal_setup != "none":
            conf = market_data.get("reversal_confidence", 0)
            signals = market_data.get("reversal_signals", [])
            logger.info(f"🔄 REVERSAL DETECTED: {reversal_setup.upper()} ({conf:.0f}%)")
            for sig in signals[:3]:
                logger.info(f"   └─ {sig}")
        else:
            # Log individual components even if no full setup
            rsi_div = market_data.get("rsi_divergence", "none")
            vol_ex = market_data.get("volume_exhaustion", "none")
            sr_sig = market_data.get("sr_signal", "mid_range")
            if rsi_div != "none" or vol_ex != "none" or sr_sig in ["near_support", "near_resistance"]:
                parts = []
                if rsi_div != "none":
                    parts.append(f"RSI div:{rsi_div}")
                if vol_ex != "none":
                    parts.append(f"Vol exhaust:{vol_ex}")
                if sr_sig != "mid_range":
                    parts.append(f"S/R:{sr_sig}")
                logger.info(f"📍 Reversal hints: {' | '.join(parts)}")

        # Log consolidation zone detection (critical for avoiding bad shorts)
        is_building_support = market_data.get("is_building_support", False)
        is_building_resistance = market_data.get("is_building_resistance", False)
        consolidation_zone = market_data.get("consolidation_zone")
        if is_building_support and consolidation_zone:
            logger.info(f"🔨 {symbol}: SUPPORT BUILDING @ ${consolidation_zone.get('level', 0):,.0f} ({consolidation_zone.get('touches', 0)} touches, {consolidation_zone.get('range_pct', 0):.2f}% range) - AVOID SHORTS!")
            # Store for MICRO strategy direction blocking
            market_data["support_building"] = {
                "level": consolidation_zone.get("level", 0),
                "touches": consolidation_zone.get("touches", 0),
                "range_pct": consolidation_zone.get("range_pct", 0)
            }
        elif is_building_resistance and consolidation_zone:
            logger.info(f"🔨 {symbol}: RESISTANCE BUILDING @ ${consolidation_zone.get('level', 0):,.0f} ({consolidation_zone.get('touches', 0)} touches, {consolidation_zone.get('range_pct', 0):.2f}% range) - AVOID LONGS!")
            # Store for MICRO strategy direction blocking
            market_data["resistance_building"] = {
                "level": consolidation_zone.get("level", 0),
                "touches": consolidation_zone.get("touches", 0),
                "range_pct": consolidation_zone.get("range_pct", 0)
            }

        # Get 15m candles for volume analysis
        candles_15m = self.hl.get_candles(symbol, interval="15m", limit=50)

        # === ORDER BOOK ANALYSIS (L2 Data for Professional Edge) ===
        if self.use_orderbook_analysis:
            try:
                ob_analysis = self.orderbook_analyzer.analyze(symbol, depth=20)
                market_data["ob_imbalance"] = ob_analysis.get("imbalance", 0)
                market_data["ob_imbalance_pct"] = ob_analysis.get("imbalance_pct", 0)
                market_data["ob_bias"] = ob_analysis.get("bias", "neutral")
                market_data["ob_confidence"] = ob_analysis.get("confidence", 0)
                market_data["ob_bid_depth"] = ob_analysis.get("bid_depth", 0)
                market_data["ob_ask_depth"] = ob_analysis.get("ask_depth", 0)
                market_data["ob_spread_pct"] = ob_analysis.get("spread_pct", 0)
                market_data["ob_walls"] = ob_analysis.get("walls", {})
                market_data["ob_signals"] = ob_analysis.get("signals", {})
                market_data["ob_summary"] = ob_analysis.get("summary", "")

                # Log order book analysis
                logger.info(f"📗 {ob_analysis.get('summary', 'No OB data')}")

                # Check for absorption (smart money)
                absorption = self.orderbook_analyzer.get_absorption_signal(symbol)
                if absorption.get("detected"):
                    logger.info(f"⚡ ABSORPTION: {absorption.get('side')} | {absorption.get('interpretation')}")
                    market_data["ob_absorption"] = absorption
                else:
                    market_data["ob_absorption"] = None
            except Exception as e:
                logger.warning(f"Order book analysis failed: {e}")
                market_data["ob_imbalance"] = 0
                market_data["ob_bias"] = "neutral"

        # Fetch alpha signals asynchronously (now includes liquidation levels and options flow)
        try:
            current_price = market_data.get("price", 0)
            alpha_signals = await self.alpha_signals.get_all_signals(symbol, candles_15m, current_price)
            self.last_alpha_signals[symbol] = alpha_signals

            # Log alpha signals (compact for terminal, full for LLM)
            alpha_report = self.alpha_signals.format_for_llm(alpha_signals)
            alpha_compact = self.alpha_signals.format_compact(alpha_signals)
            logger.info(f"📊 Alpha: {alpha_compact}")

            # Add alpha signals to market data for LLM
            market_data["alpha_signals"] = alpha_signals
            market_data["alpha_report"] = alpha_report

            # Extract key alpha metrics for direct access
            fg = alpha_signals.get("fear_greed", {})
            market_data["fear_greed_value"] = fg.get("value", 50)
            market_data["fear_greed_signal"] = fg.get("signal", "neutral")

            # NEW: Extract liquidation and options data
            liq = alpha_signals.get("liquidations", {})
            market_data["liquidation_signal"] = liq.get("signal", "neutral")
            market_data["liquidation_long_zone"] = liq.get("long_zone")
            market_data["liquidation_short_zone"] = liq.get("short_zone")

            opt = alpha_signals.get("options_flow", {})
            market_data["options_signal"] = opt.get("signal", "neutral")
            market_data["options_pcr"] = opt.get("put_call_ratio_volume")

            ob = alpha_signals.get("orderbook", {})
            market_data["orderbook_signal"] = ob.get("signal", "neutral")
            market_data["orderbook_strength"] = ob.get("strength", 0)
            market_data["whale_walls_count"] = len(ob.get("whale_walls", []))

            vol = alpha_signals.get("volume", {})
            market_data["volume_spike"] = vol.get("is_spike", False)
            market_data["volume_ratio"] = vol.get("volume_ratio", 1.0)
            market_data["volume_divergence"] = vol.get("divergence", "none")

            agg = alpha_signals.get("aggregate", {})
            market_data["alpha_aggregate_signal"] = agg.get("signal", "neutral")
            market_data["alpha_aggregate_strength"] = agg.get("strength", 0)
            market_data["alpha_net_score"] = agg.get("net_score", 0)

        except Exception as e:
            logger.warning(f"Failed to fetch alpha signals: {e}")
            market_data["alpha_signals"] = None
            market_data["alpha_report"] = "Alpha signals unavailable"

        # === DEEPSEEK MARKET REGIME ANALYSIS (Strategic LLM - Every 15 min) ===
        try:
            cache_entry = self.market_regime_cache.get(symbol)
            use_cached = False

            if cache_entry and symbol in self.last_regime_update:
                cache_age_min = (datetime.utcnow() - self.last_regime_update[symbol]).total_seconds() / 60
                if cache_age_min < self.regime_cache_ttl_minutes:
                    use_cached = True

            if not use_cached:
                # Run DeepSeek regime analysis (costs ~$0.001)
                regime_analysis = self.llm.analyze_market_regime(market_data)
                self.market_regime_cache[symbol] = regime_analysis
                self.last_regime_update[symbol] = datetime.utcnow()
                logger.info(f"🎯 REGIME ({symbol}): {regime_analysis.get('regime', 'unknown')} | Bias: {regime_analysis.get('bias', 'neutral')} | Vol: {regime_analysis.get('volatility', 'normal')}")
                logger.info(f"   └─ Strategy: {regime_analysis.get('recommendation', 'N/A')}")
            else:
                regime_analysis = cache_entry

            # Add to market data
            market_data["llm_regime"] = regime_analysis.get("regime", "unknown")
            market_data["llm_bias"] = regime_analysis.get("bias", "neutral")
            market_data["llm_volatility"] = regime_analysis.get("volatility", "normal")
            market_data["llm_regime_recommendation"] = regime_analysis.get("recommendation", "")

        except Exception as e:
            logger.warning(f"DeepSeek regime analysis failed: {e}")
            market_data["llm_regime"] = "unknown"
            market_data["llm_bias"] = "neutral"

        # === EDGE METRICS (Strategy Self-Awareness) ===
        try:
            edge_metrics = self.perf_tracker.get_overall_metrics()
            market_data["edge_quality"] = edge_metrics.get("edge_quality", "UNKNOWN")
            market_data["expected_value"] = edge_metrics.get("expected_value", 0)
            market_data["profit_factor"] = edge_metrics.get("profit_factor", 0)
            market_data["win_rate"] = edge_metrics.get("win_rate", 0)
            market_data["current_streak"] = edge_metrics.get("current_streak", 0)
            market_data["total_trades"] = edge_metrics.get("total_trades", 0)
            market_data["max_drawdown"] = edge_metrics.get("max_drawdown_pct", 0)
            market_data["sharpe_ratio"] = edge_metrics.get("sharpe_ratio", 0)

            # Log edge summary periodically
            if edge_metrics.get("total_trades", 0) >= 3:
                logger.info(f"📈 {self.perf_tracker.get_edge_summary()}")
        except Exception as e:
            logger.warning(f"Failed to get edge metrics: {e}")

        # === VISUAL CHART ANALYSIS (Claude Vision) - WITH CACHING TO SAVE $$$ ===
        if self.use_visual_analysis:
            try:
                # Check cache first to avoid expensive Vision API calls
                cache_entry = self.visual_analysis_cache.get(symbol)
                use_cached = False

                if cache_entry:
                    cache_age_min = (datetime.utcnow() - cache_entry["timestamp"]).total_seconds() / 60
                    if cache_age_min < self.visual_cache_ttl_minutes:
                        use_cached = True
                        visual_analysis = cache_entry["analysis"]

                if not use_cached:
                    candles_1h = self.hl.get_candles(symbol, interval="1h", limit=100)
                    if candles_1h and len(candles_1h) >= 50:
                        visual_analysis = self.chart_analyzer.analyze_trend(candles_1h, symbol, "1h")
                        self.visual_analysis_cache[symbol] = {"analysis": visual_analysis, "timestamp": datetime.utcnow()}
                        # Compact visual log - show source (DeepSeek=$0.0003 vs Vision=$0.02)
                        source = visual_analysis.get('source', 'unknown')
                        cost = visual_analysis.get('cost_estimate', '$?')
                        trend = visual_analysis.get('trend_direction', 'neutral')
                        strength = visual_analysis.get('trend_strength', 0)
                        pattern = visual_analysis.get('pattern', '')
                        logger.info(f"👁️ {symbol} [{source} {cost}]: {trend} (str:{strength}/10) {pattern}")
                    else:
                        visual_analysis = {}

                # Apply visual analysis to market data
                market_data["visual_trend"] = visual_analysis.get("trend_direction", "neutral")
                market_data["visual_trend_strength"] = visual_analysis.get("trend_strength", 5)
                market_data["visual_pattern"] = visual_analysis.get("pattern", "none")
                market_data["visual_pattern_stage"] = visual_analysis.get("pattern_stage", "none")
                market_data["visual_support"] = visual_analysis.get("key_support")
                market_data["visual_resistance"] = visual_analysis.get("key_resistance")
                market_data["visual_momentum"] = visual_analysis.get("momentum_signal", "neutral")
                market_data["visual_confidence"] = visual_analysis.get("confidence", 0)
                market_data["visual_divergence"] = visual_analysis.get("divergence_detected", "none")
                market_data["visual_volume_confirms"] = visual_analysis.get("volume_confirms", False)
                market_data["visual_reasoning"] = visual_analysis.get("reasoning", "")
                market_data["visual_trade_idea"] = visual_analysis.get("trade_idea", "")

                # Record thinking for meta-analysis
                if visual_analysis:
                    self.thinking_tracker.record_analysis(symbol, visual_analysis)

            except Exception as e:
                logger.warning(f"Visual analysis failed: {e}")
                market_data["visual_trend"] = "neutral"
                market_data["visual_confidence"] = 0

        # === SNIPER ANALYSIS (Trendlines + 5m + Confluence) ===
        if self.use_sniper:
            try:
                price = market_data["price"]

                # Get multi-timeframe candles for pattern analysis
                candles_5m = self.hl.get_candles(symbol, interval="5m", limit=60)  # Need 60 for trend detection
                candles_15m = self.hl.get_candles(symbol, interval="15m", limit=30)
                candles_30m = self.hl.get_candles(symbol, interval="30m", limit=30)

                # 5m momentum analysis
                momentum_5m = analyze_5m_momentum(candles_5m) if candles_5m else {"signal": "neutral"}
                market_data["momentum_5m"] = momentum_5m
                market_data["momentum_5m_signal"] = momentum_5m.get("signal", "neutral")

                # 5m TREND DETECTION (for scalp trading)
                trend_5m = detect_5m_trend(candles_5m) if candles_5m and len(candles_5m) >= 50 else {}
                market_data["trend_5m"] = trend_5m
                if trend_5m.get("scalp_signal"):
                    logger.info(f"📊 5m Trend: {trend_5m['trend'].upper()} ({trend_5m['score']}/100) → {trend_5m['scalp_signal'].upper()}")
                    logger.info(f"   Reasons: {', '.join(trend_5m.get('reasons', []))}")

                # === MULTI-TIMEFRAME CANDLE PATTERN ANALYSIS ===
                mtf_candles = analyze_multi_timeframe_candles(
                    candles_5m or [], candles_15m or [], candles_30m or []
                )
                market_data["candle_patterns"] = mtf_candles
                market_data["candle_confluence"] = mtf_candles.get("confluence_signal", "neutral")
                market_data["candle_recommendation"] = mtf_candles.get("recommendation", "WAIT")
                market_data["candle_patterns_summary"] = mtf_candles.get("patterns_summary", "")

                # Detect 3-candle patterns on each timeframe
                patterns_3c = {}
                for tf_name, candles in [("5m", candles_5m), ("15m", candles_15m), ("30m", candles_30m)]:
                    if candles and len(candles) >= 3:
                        pattern_3c = detect_3_candle_patterns(candles)
                        if pattern_3c.get("pattern"):
                            patterns_3c[tf_name] = pattern_3c
                market_data["three_candle_patterns"] = patterns_3c

                # Detect trendlines on 1h timeframe (for MICRO)
                candles_1h = self.hl.get_candles(symbol, interval="1h", limit=100)
                trendline_data = detect_trendlines(candles_1h) if candles_1h else {}
                market_data["trendline"] = trendline_data
                market_data["trendline_signal"] = trendline_data.get("signal", "neutral")

                # Store trendline prices for snipe orders
                if trendline_data.get("ascending_support"):
                    asc = trendline_data["ascending_support"]
                    market_data["ascending_trendline_price"] = asc.get('current_price', 0)
                if trendline_data.get("descending_resistance"):
                    desc = trendline_data["descending_resistance"]
                    market_data["descending_trendline_price"] = desc.get('current_price', 0)

                # === MACRO TRENDLINES (4H/1D for MACRO limit orders) ===
                # 4H Trendlines - primary MACRO timeframe
                candles_4h = market_data.get("candles_4h") or self.hl.get_candles(symbol, interval="4h", limit=100)
                trendline_4h = detect_trendlines(candles_4h, lookback=80, min_touches=2) if candles_4h else {}
                market_data["trendline_4h"] = trendline_4h

                if trendline_4h.get("ascending_support"):
                    asc_4h = trendline_4h["ascending_support"]
                    market_data["macro_ascending_trendline"] = asc_4h.get('current_price', 0)
                    market_data["macro_ascending_trendline_slope"] = asc_4h.get('slope_pct_per_candle', 0)
                    logger.debug(f"📈 MACRO 4H ascending trendline @ ${market_data['macro_ascending_trendline']:.0f}")

                if trendline_4h.get("descending_resistance"):
                    desc_4h = trendline_4h["descending_resistance"]
                    market_data["macro_descending_trendline"] = desc_4h.get('current_price', 0)
                    market_data["macro_descending_trendline_slope"] = desc_4h.get('slope_pct_per_candle', 0)
                    logger.debug(f"📉 MACRO 4H descending trendline @ ${market_data['macro_descending_trendline']:.0f}")

                # 1D Trendlines - highest timeframe for major levels
                candles_1d = self.hl.get_candles(symbol, interval="1d", limit=60)
                trendline_1d = detect_trendlines(candles_1d, lookback=50, min_touches=2) if candles_1d else {}
                market_data["trendline_1d"] = trendline_1d

                if trendline_1d.get("ascending_support"):
                    asc_1d = trendline_1d["ascending_support"]
                    market_data["daily_ascending_trendline"] = asc_1d.get('current_price', 0)
                    logger.debug(f"📈 MACRO 1D ascending trendline @ ${market_data['daily_ascending_trendline']:.0f}")

                if trendline_1d.get("descending_resistance"):
                    desc_1d = trendline_1d["descending_resistance"]
                    market_data["daily_descending_trendline"] = desc_1d.get('current_price', 0)
                    logger.debug(f"📉 MACRO 1D descending trendline @ ${market_data['daily_descending_trendline']:.0f}")

                # Get orderbook for absorption detection
                orderbook = {"bids": market_data.get("bids", []), "asks": market_data.get("asks", [])}

                # Get alpha data from market_data (already fetched above)
                alpha_data = market_data.get("alpha_signals", {}) or {}
                whale_data = alpha_data.get("whale_tracking", {})
                volume_data = alpha_data.get("volume", {})
                fear_greed = alpha_data.get("fear_greed", {})

                # Run sniper analysis
                sniper_analysis = self.sniper.analyze_entry(
                    symbol=symbol,
                    current_price=price,
                    orderbook=orderbook,
                    trendline_data=trendline_data,
                    momentum_5m=momentum_5m,
                    ema_1h_signal=market_data.get("ema_mid_signal", "neutral"),
                    ema_4h_signal=market_data.get("ema_macro_signal", "neutral"),
                    whale_data=whale_data,
                    volume_data=volume_data,
                    fear_greed=fear_greed
                )

                market_data["sniper_analysis"] = sniper_analysis
                market_data["confluence_score"] = sniper_analysis["confluence"]["score"]
                market_data["confluence_direction"] = sniper_analysis["confluence"]["direction"]
                market_data["confluence_recommendation"] = sniper_analysis["confluence"]["recommendation"]

            except Exception as e:
                logger.warning(f"Sniper analysis failed: {e}")
                market_data["sniper_analysis"] = None
                market_data["confluence_score"] = 0

        # === ADVANCED PATTERN ANALYSIS (Fib, Elliott, Harmonics, Wyckoff) ===
        try:
            candles_1h = self.hl.get_candles(symbol, interval="1h", limit=100)
            if candles_1h and len(candles_1h) >= 50:
                # Get advanced analysis
                advanced = get_advanced_analysis(
                    candles_1h,
                    order_book={"bids": market_data.get("bids", []), "asks": market_data.get("asks", [])}
                )

                # Fibonacci levels
                fib = advanced.get("fibonacci", {})
                market_data["fib_levels"] = fib.get("levels", {})
                market_data["fib_signal"] = fib.get("signal", "neutral")
                market_data["fib_nearest_level"] = fib.get("nearest_level", "")
                market_data["fib_golden_pocket"] = fib.get("golden_pocket", {})

                # Elliott Wave
                elliott = advanced.get("elliott_wave", {})
                market_data["elliott_pattern"] = elliott.get("pattern", "")
                market_data["elliott_wave_position"] = elliott.get("wave_position", "")
                market_data["elliott_signal"] = elliott.get("signal", "neutral")
                market_data["elliott_next_move"] = elliott.get("next_move", "")

                # Harmonic Patterns
                harmonic = advanced.get("harmonic", {})
                market_data["harmonic_pattern"] = harmonic.get("pattern", "")
                market_data["harmonic_direction"] = harmonic.get("direction", "")
                market_data["harmonic_completion"] = harmonic.get("completion_pct", 0)
                market_data["harmonic_prz"] = harmonic.get("prz", 0)  # Potential Reversal Zone
                market_data["harmonic_signal"] = harmonic.get("signal", "neutral")

                # Wyckoff Analysis
                wyckoff = advanced.get("wyckoff", {})
                market_data["wyckoff_phase"] = wyckoff.get("phase", "")
                market_data["wyckoff_signal"] = wyckoff.get("signal", "neutral")
                market_data["wyckoff_events"] = wyckoff.get("events", [])
                market_data["wyckoff_recommendation"] = wyckoff.get("recommendation", "")

                # Order Flow Heatmap
                orderflow = advanced.get("order_flow", {})
                market_data["orderflow_signal"] = orderflow.get("signal", "neutral")
                market_data["orderflow_imbalance"] = orderflow.get("imbalance_pct", "0%")
                market_data["orderflow_bid_walls"] = orderflow.get("bid_walls", [])
                market_data["orderflow_ask_walls"] = orderflow.get("ask_walls", [])

                # Combined signal from all advanced patterns
                market_data["advanced_signal"] = advanced.get("combined_signal", "NEUTRAL")
                market_data["advanced_confidence"] = advanced.get("confidence", 0)

                # Log significant findings
                if advanced.get("combined_signal") != "NEUTRAL":
                    logger.info(f"🔮 ADVANCED: {advanced['combined_signal']} ({advanced.get('confidence', 0):.0%} conf)")
                    for name, sig in advanced.get("signals_breakdown", []):
                        logger.info(f"   └─ {name}: {sig}")

                # Log specific patterns
                if harmonic.get("pattern"):
                    logger.info(f"   🦋 Harmonic: {harmonic['pattern']} {harmonic.get('direction', '')} @ PRZ ${harmonic.get('prz', 0):,.2f}")
                if elliott.get("pattern"):
                    logger.info(f"   🌊 Elliott: {elliott['pattern']} - Wave {elliott.get('wave_position', '?')} - Next: {elliott.get('next_move', '')}")
                if wyckoff.get("phase") not in ["unknown", "ranging"]:
                    logger.info(f"   📊 Wyckoff: {wyckoff['phase'].upper()} - {wyckoff.get('recommendation', '')[:50]}")
                if fib.get("signal") not in ["neutral", "unknown"]:
                    logger.info(f"   📐 Fib: {fib['signal']} near {fib.get('nearest_level', '')} (${fib.get('nearest_price', 0):,.2f})")

        except Exception as e:
            logger.warning(f"Advanced pattern analysis failed: {e}")
            market_data["advanced_signal"] = "NEUTRAL"
            market_data["advanced_confidence"] = 0

        # === OPPORTUNITY SCORING (Proactive Setup Detection) ===
        opportunity = self._score_opportunity(market_data)
        market_data["opportunity_score"] = opportunity["score"]
        market_data["opportunity_bias"] = opportunity["bias"]
        market_data["opportunity_setups"] = opportunity["setups"]
        market_data["opportunity_summary"] = opportunity["summary"]

        if opportunity["score"] >= 60:
            logger.info(f"🎯 OPPORTUNITY DETECTED: {opportunity['summary']}")
            logger.info(f"   Score: {opportunity['score']}/100 | Bias: {opportunity['bias'].upper()}")
            for setup in opportunity["setups"]:
                logger.info(f"   ✓ {setup}")

        # === SMART MONEY CONCEPTS (SMC) ANALYSIS ===
        try:
            candles_1h = market_data.get("candles_1h") or self.hl.get_candles(symbol, interval="1h", limit=100)
            if candles_1h and len(candles_1h) >= 50:
                smc = analyze_smart_money(candles_1h)
                if smc.get("valid"):
                    market_data["smc_analysis"] = smc
                    market_data["smc_bias"] = smc.get("bias", "neutral")
                    market_data["smc_confidence"] = smc.get("confidence", 0)
                    market_data["smc_structure"] = smc.get("structure", {})
                    market_data["smc_order_blocks"] = smc.get("order_blocks", [])
                    market_data["smc_fvgs"] = smc.get("fair_value_gaps", [])
                    market_data["smc_liquidity"] = smc.get("liquidity", {})

                    # Log SMC findings
                    if smc.get("confidence", 0) > 0.5:
                        logger.info(f"🏦 SMC: {smc['bias'].upper()} ({smc['confidence']:.0%}) | Structure: {smc['structure'].get('trend', 'unknown')}")
                        if smc.get("order_blocks"):
                            ob = smc["order_blocks"][0]
                            logger.info(f"   └─ Order Block: {'Bullish' if ob.get('is_bullish') else 'Bearish'} @ ${ob.get('price', 0):,.2f}")
                        if smc.get("liquidity", {}).get("swept"):
                            sweep = smc["liquidity"]["swept"][-1]
                            logger.info(f"   └─ Liquidity Sweep: {sweep.get('type', '')} → {sweep.get('implication', '')}")
        except Exception as e:
            logger.warning(f"SMC analysis failed: {e}")
            market_data["smc_analysis"] = None
            market_data["smc_bias"] = "neutral"

        # === VOLUME PROFILE ANALYSIS ===
        try:
            candles_1h = market_data.get("candles_1h") or self.hl.get_candles(symbol, interval="1h", limit=100)
            if candles_1h and len(candles_1h) >= 50:
                vp = analyze_volume_profile(candles_1h)
                if vp.get("valid"):
                    market_data["volume_profile"] = vp
                    market_data["vp_poc"] = vp.get("poc")
                    market_data["vp_vah"] = vp.get("vah")
                    market_data["vp_val"] = vp.get("val")
                    market_data["vp_position"] = vp.get("position")
                    market_data["vp_bias"] = vp.get("bias", "neutral")
                    market_data["vp_supports"] = vp.get("supports", [])
                    market_data["vp_resistances"] = vp.get("resistances", [])

                    # Log VP findings
                    logger.info(f"📊 VP: POC ${vp['poc']:,.2f} | VAH ${vp['vah']:,.2f} | VAL ${vp['val']:,.2f} | Position: {vp['position']}")
        except Exception as e:
            logger.warning(f"Volume Profile analysis failed: {e}")
            market_data["volume_profile"] = None
            market_data["vp_bias"] = "neutral"

        # === ADAPTIVE PARAMETERS (Regime-Based Thresholds) ===
        try:
            candles_1h = market_data.get("candles_1h") or self.hl.get_candles(symbol, interval="1h", limit=100)
            if candles_1h and len(candles_1h) >= 20:
                regime = detect_regime(candles_1h, adx=market_data.get("adx"))
                thresholds = get_adaptive_thresholds(candles_1h, regime, adx=market_data.get("adx"))

                market_data["adaptive_regime"] = regime.value
                market_data["adaptive_thresholds"] = {
                    "rsi_overbought": thresholds.rsi_overbought,
                    "rsi_oversold": thresholds.rsi_oversold,
                    "min_confidence": thresholds.min_confidence,
                    "size_multiplier": thresholds.size_multiplier,
                    "stop_atr_mult": thresholds.stop_loss_atr_mult,
                    "tp_atr_mult": thresholds.take_profit_atr_mult
                }

                logger.info(f"⚙️ REGIME: {regime.value} | RSI OB/OS: {thresholds.rsi_overbought:.0f}/{thresholds.rsi_oversold:.0f} | Size: {thresholds.size_multiplier:.1f}x")
        except Exception as e:
            logger.warning(f"Adaptive parameters failed: {e}")
            market_data["adaptive_regime"] = "ranging"
            market_data["adaptive_thresholds"] = {}

        # === BAYESIAN SIGNAL AGGREGATION ===
        try:
            aggregator = get_aggregator()

            # Gather all signals for aggregation
            bayesian_signal = aggregator.get_trading_signal(
                smc_analysis=market_data.get("smc_analysis"),
                volume_profile=market_data.get("volume_profile"),
                rsi=market_data.get("rsi"),
                ema_signal=market_data.get("ema_mid_signal"),
                macd_signal=market_data.get("macd_signal"),
                candle_pattern=market_data.get("candle_patterns"),
                whale_signal=market_data.get("alpha_signals", {}).get("whale_tracking"),
                funding_rate=market_data.get("funding_rate_8h"),
                fear_greed=market_data.get("alpha_signals", {}).get("fear_greed"),
                deepseek_analysis=market_data.get("regime_analysis"),
                regime={"regime": market_data.get("adaptive_regime")}
            )

            market_data["bayesian_signal"] = bayesian_signal
            market_data["bayesian_direction"] = bayesian_signal.get("direction", "neutral")
            market_data["bayesian_probability"] = bayesian_signal.get("probability", 0.5)
            market_data["bayesian_confidence"] = bayesian_signal.get("confidence", 0)
            market_data["bayesian_quality"] = bayesian_signal.get("quality", "low")
            market_data["bayesian_recommendation"] = bayesian_signal.get("recommendation", "WAIT")

            # Log Bayesian aggregation
            if bayesian_signal.get("confidence", 0) > 0.3:
                logger.info(f"🎲 BAYESIAN: {bayesian_signal['direction'].upper()} P={bayesian_signal['probability']:.1%} | Conf: {bayesian_signal['confidence']:.0%} | Quality: {bayesian_signal['quality']}")
                logger.info(f"   └─ {bayesian_signal['signals_bullish']} bullish / {bayesian_signal['signals_bearish']} bearish signals")
        except Exception as e:
            logger.warning(f"Bayesian aggregation failed: {e}")
            market_data["bayesian_signal"] = None
            market_data["bayesian_direction"] = "neutral"
            market_data["bayesian_confidence"] = 0

        # === UPDATE REALTIME MONITOR S/R LEVELS ===
        if self.realtime_monitor:
            try:
                supports = [
                    market_data.get("sr_support", 0),
                    market_data.get("vp_val", 0),
                    market_data.get("ichimoku_cloud_bottom", 0),
                ]
                resistances = [
                    market_data.get("sr_resistance", 0),
                    market_data.get("vp_vah", 0),
                    market_data.get("ichimoku_cloud_top", 0),
                ]
                # Filter out zeros and update
                supports = [s for s in supports if s and s > 0]
                resistances = [r for r in resistances if r and r > 0]
                if supports or resistances:
                    self.update_realtime_sr_levels(symbol, supports, resistances)
            except Exception as e:
                logger.debug(f"Failed to update realtime S/R: {e}")

        return market_data

    def _get_position_info(self, symbol: str) -> Dict[str, Any]:
        """Get current position info for a symbol including margin-based P&L."""
        state = self.hl.get_account_state()
        for pos in state.get("positions", []):
            p = pos.get("position") if isinstance(pos, dict) and isinstance(pos.get("position"), dict) else pos
            if isinstance(p, dict) and p.get("coin") == symbol:
                size = float(p.get("szi", 0) or 0)
                entry_px = float(p.get("entryPx", 0) or 0)
                unrealized_pnl = float(p.get("unrealizedPnl", 0) or 0)
                # Get margin used for this position (position value / leverage)
                position_value = float(p.get("positionValue", 0) or 0)
                margin_used = float(p.get("marginUsed", 0) or 0)
                leverage = float(p.get("leverage", {}).get("value", 1) if isinstance(p.get("leverage"), dict) else p.get("leverage", 1) or 1)

                # Calculate position P&L % based on margin (what you actually risked)
                # This is the TRUE P&L that matters for risk management
                if margin_used > 0:
                    position_pnl_pct = (unrealized_pnl / margin_used) * 100
                elif position_value > 0 and leverage > 0:
                    # Fallback: estimate margin from position value and leverage
                    estimated_margin = position_value / leverage
                    position_pnl_pct = (unrealized_pnl / estimated_margin) * 100 if estimated_margin > 0 else 0
                else:
                    position_pnl_pct = 0

                return {
                    "size": size,
                    "side": "long" if size > 0 else "short" if size < 0 else "none",
                    "entry_price": entry_px,
                    "unrealized_pnl": unrealized_pnl,
                    "abs_size": abs(size),
                    "margin_used": margin_used,
                    "position_value": position_value,
                    "leverage": leverage,
                    "position_pnl_pct": position_pnl_pct  # This is the leveraged P&L %
                }
        return {"size": 0, "side": "none", "entry_price": 0, "unrealized_pnl": 0, "abs_size": 0,
                "margin_used": 0, "position_value": 0, "leverage": 1, "position_pnl_pct": 0}

    # NOTE: Short-term methods (_check_stop_loss, _check_micro_trend_reversal) have been removed.
    # Position management is now handled entirely by _manage_position using thesis-based logic.

    def _score_opportunity(self, market_data: Dict) -> Dict[str, Any]:
        """Score trading opportunity - REVERSAL PREDICTION focused for scalping.

        KEY INSIGHT: Don't chase trends. Look for reversals at key levels.
        - Enter BEFORE the move happens, not after
        - Use divergence, exhaustion, and S/R levels to predict turns

        Returns:
            Dict with score (0-100), bias (long/short/neutral), setups (list), summary
        """
        setups = []
        bullish_points = 0
        bearish_points = 0

        price = market_data.get("price", 0)
        rsi = market_data.get("rsi", 50)

        # === REVERSAL SIGNALS (HIGHEST PRIORITY - up to 50 points) ===
        # These predict reversals BEFORE they happen
        reversal_setup = market_data.get("reversal_setup", "none")
        reversal_confidence = market_data.get("reversal_confidence", 0)
        reversal_signals = market_data.get("reversal_signals", [])

        if reversal_setup == "long_reversal":
            bullish_points += min(50, reversal_confidence)
            setups.append(f"🔄 REVERSAL LONG ({reversal_confidence:.0f}%)")
            for sig in reversal_signals[:3]:  # Top 3 reasons
                setups.append(f"  └─ {sig}")
        elif reversal_setup == "short_reversal":
            bearish_points += min(50, reversal_confidence)
            setups.append(f"🔄 REVERSAL SHORT ({reversal_confidence:.0f}%)")
            for sig in reversal_signals[:3]:
                setups.append(f"  └─ {sig}")

        # Individual reversal components (if no full setup)
        rsi_div = market_data.get("rsi_divergence", "none")
        rsi_div_strength = market_data.get("rsi_divergence_strength", 0)
        if rsi_div == "bullish" and reversal_setup != "long_reversal":
            bullish_points += 25 * rsi_div_strength
            setups.append(f"RSI bullish divergence ({rsi_div_strength:.0%})")
        elif rsi_div == "bearish" and reversal_setup != "short_reversal":
            bearish_points += 25 * rsi_div_strength
            setups.append(f"RSI bearish divergence ({rsi_div_strength:.0%})")

        vol_exhaustion = market_data.get("volume_exhaustion", "none")
        vol_ex_strength = market_data.get("volume_exhaustion_strength", 0)
        if vol_exhaustion == "bullish":
            bullish_points += 20 * vol_ex_strength
            setups.append(f"Selling exhaustion ({vol_ex_strength:.0%})")
        elif vol_exhaustion == "bearish":
            bearish_points += 20 * vol_ex_strength
            setups.append(f"Buying exhaustion ({vol_ex_strength:.0%})")

        # === SUPPORT/RESISTANCE LEVELS (up to 25 points) ===
        # Being AT a level = potential reversal point
        sr_signal = market_data.get("sr_signal", "mid_range")
        dist_support = market_data.get("dist_to_support_pct", 100)
        dist_resistance = market_data.get("dist_to_resistance_pct", 100)
        nearest_support = market_data.get("nearest_support", 0)
        nearest_resistance = market_data.get("nearest_resistance", 0)

        # NEW: Consolidation zone detection - CRITICAL for avoiding bad shorts at support
        is_building_support = market_data.get("is_building_support", False)
        is_building_resistance = market_data.get("is_building_resistance", False)
        consolidation_zone = market_data.get("consolidation_zone")

        if sr_signal == "near_support" or dist_support < 0.5:
            bullish_points += 25
            setups.append(f"📍 AT SUPPORT ${nearest_support:,.0f} ({dist_support:.1f}% away)")
        elif sr_signal == "near_resistance" or dist_resistance < 0.5:
            bearish_points += 25
            setups.append(f"📍 AT RESISTANCE ${nearest_resistance:,.0f} ({dist_resistance:.1f}% away)")

        # NEW: Consolidation zone gives EXTRA weight - prevents shorting into building support
        if is_building_support:
            bullish_points += 20  # Strong bullish bias when consolidating at lows
            bearish_points -= 15  # PENALIZE shorts when support is building
            consol_level = consolidation_zone.get("level", 0) if consolidation_zone else 0
            touches = consolidation_zone.get("touches", 0) if consolidation_zone else 0
            setups.append(f"🔨 SUPPORT BUILDING @ ${consol_level:,.0f} ({touches} touches) - NO SHORTS!")
        elif is_building_resistance:
            bearish_points += 20  # Strong bearish bias when consolidating at highs
            bullish_points -= 15  # PENALIZE longs when resistance is building
            consol_level = consolidation_zone.get("level", 0) if consolidation_zone else 0
            touches = consolidation_zone.get("touches", 0) if consolidation_zone else 0
            setups.append(f"🔨 RESISTANCE BUILDING @ ${consol_level:,.0f} ({touches} touches) - NO LONGS!")

        # Trendline levels
        trendline_signal = market_data.get("trendline_signal", "neutral")
        if trendline_signal == "at_ascending_support":
            bullish_points += 20
            setups.append("📈 At ascending trendline support")
        elif trendline_signal == "at_descending_resistance":
            bearish_points += 20
            setups.append("📉 At descending trendline resistance")

        # === BOLLINGER BAND EXTREMES (up to 15 points) ===
        bb_position = market_data.get("bb_position", 0.5)
        bb_signal = market_data.get("bb_signal", "neutral")

        if bb_position <= 0.1 or bb_signal == "oversold":
            bullish_points += 15
            setups.append(f"BB oversold ({bb_position:.0%} from bottom)")
        elif bb_position >= 0.9 or bb_signal == "overbought":
            bearish_points += 15
            setups.append(f"BB overbought ({bb_position:.0%} from bottom)")

        # === RSI EXTREMES (up to 15 points) ===
        # Extreme RSI = mean reversion opportunity
        if rsi <= 30:
            bullish_points += 15
            setups.append(f"RSI oversold ({rsi:.0f})")
        elif rsi >= 70:
            bearish_points += 15
            setups.append(f"RSI overbought ({rsi:.0f})")
        elif rsi <= 40:
            bullish_points += 5
            setups.append(f"RSI low ({rsi:.0f})")
        elif rsi >= 60:
            bearish_points += 5
            setups.append(f"RSI high ({rsi:.0f})")

        # === TREND CONTEXT (lower weight - we're fading, not following) ===
        # Only use trend as CONFIRMATION, not primary signal
        ema_1h = market_data.get("ema_macro_signal", "neutral")

        # If fading INTO a strong trend, reduce confidence (risky)
        # If fading at the END of a trend, increase confidence
        if reversal_setup == "long_reversal" and ema_1h == "bearish":
            # Fading downtrend - this is what we want
            bullish_points += 10
            setups.append("✓ Fading bearish trend (good)")
        elif reversal_setup == "short_reversal" and ema_1h == "bullish":
            # Fading uptrend - this is what we want
            bearish_points += 10
            setups.append("✓ Fading bullish trend (good)")

        # === ORDER BOOK SIGNALS (up to 25 points) - PROFESSIONAL EDGE ===
        ob_bias = market_data.get("ob_bias", "neutral")
        ob_confidence = market_data.get("ob_confidence", 0)
        ob_imbalance = market_data.get("ob_imbalance", 0)
        ob_signals = market_data.get("ob_signals", {})
        ob_absorption = market_data.get("ob_absorption")

        # Order book imbalance - shows real-time buying/selling pressure
        if ob_bias == "bullish" and ob_confidence > 60:
            bullish_points += min(25, ob_confidence * 0.4)
            setups.append(f"📗 OB bullish ({ob_imbalance*100:+.0f}% imbalance)")
        elif ob_bias == "bearish" and ob_confidence > 60:
            bearish_points += min(25, ob_confidence * 0.4)
            setups.append(f"📕 OB bearish ({ob_imbalance*100:+.0f}% imbalance)")

        # Absorption detection (smart money signal)
        if ob_absorption and ob_absorption.get("detected"):
            side = ob_absorption.get("side", "")
            strength = ob_absorption.get("strength", 0)
            if side == "ask_absorption":  # Asks being absorbed = bullish
                bullish_points += 20 * strength
                setups.append(f"⚡ Ask absorption (smart money buying)")
            elif side == "bid_absorption":  # Bids being absorbed = bearish
                bearish_points += 20 * strength
                setups.append(f"⚡ Bid absorption (smart money selling)")

        # Add order book reasons to setups
        ob_reasons = ob_signals.get("reasons", [])
        for reason in ob_reasons[:2]:
            setups.append(f"  └─ {reason}")

        # === 5M TREND MOMENTUM (up to 40 points) - HIGH WEIGHT FOR FAST SIGNALS ===
        # This is the key change: trust short-term momentum more
        trend_5m = market_data.get("trend_5m", {})
        trend_5m_direction = trend_5m.get("trend", "neutral")
        trend_5m_score = trend_5m.get("score", 0)
        trend_5m_reasons = trend_5m.get("reasons", [])
        momentum_5m_signal = market_data.get("momentum_5m_signal", "neutral")

        # Strong 5m trend = follow it (momentum trading)
        if trend_5m_direction == "bullish" and trend_5m_score >= 60:
            # Scale points based on trend score: 60→20pts, 80→30pts, 100→40pts
            momentum_points = min(40, 20 + (trend_5m_score - 60) * 0.5)
            bullish_points += momentum_points
            setups.append(f"📈 5m TREND BULLISH ({trend_5m_score}/100)")
            if trend_5m_reasons:
                setups.append(f"  └─ {trend_5m_reasons[0]}")
        elif trend_5m_direction == "bearish" and trend_5m_score >= 60:
            momentum_points = min(40, 20 + (trend_5m_score - 60) * 0.5)
            bearish_points += momentum_points
            setups.append(f"📉 5m TREND BEARISH ({trend_5m_score}/100)")
            if trend_5m_reasons:
                setups.append(f"  └─ {trend_5m_reasons[0]}")

        # Additional momentum confirmation from 5m signal
        if momentum_5m_signal == "bullish":
            bullish_points += 10
            setups.append("5m momentum bullish")
        elif momentum_5m_signal == "bearish":
            bearish_points += 10
            setups.append("5m momentum bearish")

        # OVERRIDE: Very strong 5m trend (score >= 80) can override support/resistance bias
        # This allows momentum trades even when "at support" (breakdown) or "at resistance" (breakout)
        if trend_5m_score >= 80:
            if trend_5m_direction == "bearish" and bullish_points > bearish_points:
                # Strong bearish momentum but bullish setup (e.g., at support)
                # This is a BREAKDOWN - bearish momentum wins
                override_points = min(30, trend_5m_score - 50)
                bearish_points += override_points
                setups.append(f"⚡ MOMENTUM OVERRIDE: Strong bearish ({trend_5m_score}/100) beats support")
            elif trend_5m_direction == "bullish" and bearish_points > bullish_points:
                # Strong bullish momentum but bearish setup (e.g., at resistance)
                # This is a BREAKOUT - bullish momentum wins
                override_points = min(30, trend_5m_score - 50)
                bullish_points += override_points
                setups.append(f"⚡ MOMENTUM OVERRIDE: Strong bullish ({trend_5m_score}/100) beats resistance")

        # === CONTRARIAN SIGNALS (up to 10 points) ===
        fear_greed = market_data.get("fear_greed_value", 50)
        funding_signal = market_data.get("funding_signal", "neutral")

        # Extreme fear/greed = contrarian opportunity
        if fear_greed < 25:
            bullish_points += 10
            setups.append(f"Extreme fear ({fear_greed}) → contrarian LONG")
        elif fear_greed > 75:
            bearish_points += 10
            setups.append(f"Extreme greed ({fear_greed}) → contrarian SHORT")

        # Funding rate edge (crowded trades)
        if funding_signal == "bullish":  # Negative funding = shorts crowded
            bullish_points += 5
            setups.append("Shorts crowded (funding negative)")
        elif funding_signal == "bearish":  # Positive funding = longs crowded
            bearish_points += 5
            setups.append("Longs crowded (funding positive)")

        # === VWAP (Institutional Level - up to 15 points) ===
        vwap_signal = market_data.get("vwap_signal", "neutral")
        vwap_dist_pct = market_data.get("vwap_distance_pct", 0)
        vwap_price = market_data.get("vwap_price", 0)

        if vwap_signal in ["oversold", "bullish"] and price and vwap_price:
            # Price below VWAP = institutional buying opportunity
            bullish_points += 15
            setups.append(f"📊 Below VWAP ${vwap_price:,.0f} ({vwap_dist_pct:.1f}% below) - Institutional buy zone")
        elif vwap_signal in ["overbought", "bearish"] and price and vwap_price:
            # Price above VWAP = institutional selling opportunity
            bearish_points += 15
            setups.append(f"📊 Above VWAP ${vwap_price:,.0f} ({vwap_dist_pct:.1f}% above) - Institutional sell zone")

        # === CVD - Cumulative Volume Delta (up to 15 points) ===
        cvd_signal = market_data.get("cvd_signal", "neutral")
        cvd_trend = market_data.get("cvd_trend", "neutral")

        if cvd_signal == "bullish" or cvd_trend == "rising":
            # Rising CVD = net buying pressure
            bullish_points += 12
            setups.append("📈 CVD rising (net buying pressure)")
        elif cvd_signal == "bearish" or cvd_trend == "falling":
            # Falling CVD = net selling pressure
            bearish_points += 12
            setups.append("📉 CVD falling (net selling pressure)")

        # CVD Divergence (price going one way, CVD going another)
        cvd_divergence = market_data.get("cvd_divergence", "none")
        if cvd_divergence == "bullish":  # Price falling but CVD rising = accumulation
            bullish_points += 10
            setups.append("🔀 CVD bullish divergence (hidden buying)")
        elif cvd_divergence == "bearish":  # Price rising but CVD falling = distribution
            bearish_points += 10
            setups.append("🔀 CVD bearish divergence (hidden selling)")

        # === ICHIMOKU CLOUD (up to 10 points) ===
        ichimoku_signal = market_data.get("ichimoku_signal", "neutral")
        ichimoku_cloud = market_data.get("ichimoku_cloud_position", "inside")

        if ichimoku_signal == "bullish":
            bullish_points += 8
            setups.append(f"☁️ Ichimoku bullish ({ichimoku_cloud})")
        elif ichimoku_signal == "bearish":
            bearish_points += 8
            setups.append(f"☁️ Ichimoku bearish ({ichimoku_cloud})")

        # === CALCULATE FINAL SCORE AND BIAS ===
        score = max(bullish_points, bearish_points)

        # Determine bias - need clear edge
        if bullish_points > bearish_points + 15:
            bias = "long"
        elif bearish_points > bullish_points + 15:
            bias = "short"
        else:
            bias = "neutral"

        # Quality based on reversal signal strength
        if reversal_setup != "none" and reversal_confidence >= 60:
            quality = "🎯 REVERSAL SETUP"
        elif score >= 60:
            quality = "A SETUP"
        elif score >= 40:
            quality = "B SETUP"
        else:
            quality = "NO CLEAR SETUP"

        summary = f"{quality}: {bias.upper()} ({score}/100) | Bull:{bullish_points} Bear:{bearish_points}"

        return {
            "score": score,
            "bias": bias,
            "setups": setups,
            "bullish_points": bullish_points,
            "bearish_points": bearish_points,
            "summary": summary,
            "is_reversal": reversal_setup != "none"
        }

    async def _execute_entry(self, signal: TradeSignal, market_data: Dict) -> None:
        """Execute a NEW trade entry with position scaling (1/3 initial, add on dips)."""
        symbol = market_data["symbol"]
        price = market_data["price"]

        if price <= 0:
            logger.error(f"Cannot execute {symbol}: invalid price {price}")
            return

        if self.config.position_size_usd < self.config.min_order_value_usd:
            logger.error(
                "Configured position_size_usd ($%.2f) is below Hyperliquid minimum ($%.2f). Skipping trade.",
                self.config.position_size_usd,
                self.config.min_order_value_usd,
            )
            return

        # === PORTFOLIO RISK CHECK (CRITICAL - RUNS FIRST) ===
        state = self.hl.get_account_state()
        current_equity = state.get("equity", 0)
        self.risk_manager.reset_daily_stats(current_equity)

        can_trade, risk_reason = self.risk_manager.can_trade(symbol, signal.action, current_equity)
        if not can_trade:
            logger.warning(f"🛑 RISK BLOCKED {symbol} {signal.action.upper()}: {risk_reason}")
            return

        # Log risk status
        risk_status = self.risk_manager.get_status()
        logger.info(f"📊 Risk: Daily P&L {risk_status['daily_pnl_pct']:+.1f}% | Positions: {risk_status['active_positions']} | Size mult: {risk_status['size_multiplier']:.2f}x")

        # === WHALE PATTERN ML CHECK ===
        if self.use_whale_ml_filter and self.whale_ml and self.whale_ml.trained:
            should_take, whale_reason, whale_score = self.whale_ml.should_take_trade(
                symbol=symbol,
                side=signal.action,
                market_data=market_data,
                hl_client=self.hl,
                min_score=self.whale_ml_min_score
            )
            if not should_take:
                logger.warning(f"🐋 WHALE ML BLOCKED {symbol} {signal.action.upper()}: {whale_reason}")
                return
            logger.info(f"🐋 {whale_reason}")

        # === ENTRY QUALITY VALIDATION (BEFORE entering) ===
        # All trades use swing strategy now
        strategy_type = 'swing'

        entry_validation = validate_entry_quality(
            candles_5m=market_data.get("candles_5m", []),
            candles_15m=market_data.get("candles_15m", []),
            candles_1h=market_data.get("candles_1h", []),
            candles_4h=market_data.get("candles_4h", []),
            trade_side=signal.action,
            strategy_type=strategy_type
        )

        # Log entry validation result
        if entry_validation["valid"]:
            logger.info(f"✅ ENTRY QUALITY: Score {entry_validation['score']}% - {entry_validation['recommendation']}")
            for reason in entry_validation["reasons"][:3]:
                logger.info(f"   └─ {reason}")
        else:
            logger.warning(f"⚠️ ENTRY QUALITY: Score {entry_validation['score']}% - {entry_validation['recommendation']}")
            for warning in entry_validation["warnings"][:3]:
                logger.warning(f"   └─ {warning}")
            # Only block if score is very low (< 25%)
            if entry_validation["score"] < 25:
                logger.warning(f"🛑 BLOCKED: Entry quality too low ({entry_validation['score']}%)")
                return

        # Adjust position size based on entry quality
        entry_quality_multiplier = 1.0
        if entry_validation["score"] >= 75:
            entry_quality_multiplier = 1.1  # Bonus for high quality
            logger.info(f"📈 Entry quality bonus: +10% size")
        elif entry_validation["score"] < 50:
            entry_quality_multiplier = 0.75  # Reduce size for low quality
            logger.info(f"📉 Entry quality penalty: -25% size")

        # === MARKET REGIME CHECK ===
        market_regime = market_data.get("market_regime", "unknown")
        regime_strategy = market_data.get("regime_strategy", "none")
        regime_size_mult = market_data.get("regime_size_multiplier", 1.0)

        # Log market regime
        regime_signals = market_data.get("regime_signals", [])
        logger.info(f"🌍 REGIME: {market_regime.upper()} | Strategy: {regime_strategy} | Size mult: {regime_size_mult}x")
        for sig in regime_signals[:2]:
            logger.info(f"   └─ {sig}")

        # Warn if strategy doesn't match regime
        if market_regime == "ranging" and strategy_type == "swing":
            logger.warning(f"⚠️ Swing trade in ranging market - consider mean reversion instead")
        elif market_regime == "volatile":
            logger.warning(f"⚠️ HIGH VOLATILITY - reducing position size")

        # === SESSION-BASED FILTERING ===
        session_name, session_mult, is_good_time = self._get_trading_session()

        if self.config.session_filter_enabled:
            if not is_good_time:
                logger.warning(f"🌙 {session_name}: Not optimal trading time (21:00-00:00 UTC)")
                logger.warning(f"   ⏰ Waiting for Asia session (00:00 UTC) or enable dead_zone trading")
                return  # Skip trade during dead zone

            logger.info(f"🕐 SESSION: {session_name} | Size mult: {session_mult:.1f}x")
        else:
            session_mult = 1.0

        # === LEARNING-BASED FILTER (pre-trade check with partial data) ===
        # NOTE: Full entry conditions with SL/TP captured AFTER trade succeeds (below)
        if self.use_learning:
            # Use preliminary conditions for filtering (without SL/TP since not calculated yet)
            prelim_conditions = self._capture_entry_conditions(
                symbol=symbol,
                market_data=market_data,
                strategy_type="swing",
                signal_confidence=signal.confidence
            )
            should_trade, reason = self.trade_analyzer.should_take_trade(signal.action, prelim_conditions)
            if not should_trade:
                logger.warning(f"🧠 LEARNING BLOCKED {symbol} {signal.action.upper()}: {reason}")
                return
            logger.info(f"🧠 Learning check passed: {reason}")

        # === COMPREHENSIVE CONFIDENCE SCORING ===
        # Uses all learning sources: charts, whales, patterns, recent trades
        confidence_result = self.get_setup_confidence(symbol, signal.action, market_data)
        confidence = confidence_result.get("confidence", 50)
        confidence_size_mult = confidence_result.get("size_multiplier", 1.0)

        if confidence < 40:
            logger.warning(f"🎯 LOW CONFIDENCE ({confidence:.0f}%): {confidence_result.get('action', 'Skip')}")
            for factor in confidence_result.get("factors", []):
                logger.info(f"   • {factor}")
            return  # Skip very low confidence trades

        logger.info(f"🎯 Confidence: {confidence:.0f}% | Size mult: {confidence_size_mult:.2f}x")
        for factor in confidence_result.get("factors", [])[:3]:  # Show top 3 factors
            logger.info(f"   • {factor}")

        def _ceil_to_decimals(value: float, decimals: int) -> float:
            q = Decimal("1").scaleb(-decimals)  # 10^-decimals
            return float(Decimal(str(value)).quantize(q, rounding=ROUND_UP))

        # USE MAXIMUM LEVERAGE available on Hyperliquid for each asset
        leverage = MAX_LEVERAGE_MAP.get(symbol, 20)

        # Calculate size: position_size_usd is MARGIN (before leverage)
        # With scaling: initial entry is 1/3 of total position
        margin_usd = self.config.position_size_usd

        # Apply performance-based sizing
        size_multiplier = self.risk_manager.get_position_size_multiplier()
        margin_usd *= size_multiplier

        # Apply entry quality multiplier (higher quality = larger size)
        margin_usd *= entry_quality_multiplier

        # Apply market regime multiplier (volatile = smaller size)
        margin_usd *= regime_size_mult

        # Apply session multiplier (US/EU overlap = larger, Asia = smaller)
        margin_usd *= session_mult

        # Apply confidence-based sizing (high confidence = full size, low = reduced)
        margin_usd *= confidence_size_mult

        if self.scaling_enabled:
            initial_margin = margin_usd / self.scale_tranches  # 1/3 of total
        else:
            initial_margin = margin_usd

        notional_usd = initial_margin * leverage
        raw_size = notional_usd / price

        # Get size decimals from centralized config (src/tickers.py)
        decimals = get_size_decimals(symbol)

        size = _ceil_to_decimals(raw_size, decimals)

        # Double-check minimum notional after rounding.
        notional = size * price
        if notional + 1e-9 < self.config.min_order_value_usd:
            # Bump by one increment.
            inc = 10 ** (-decimals)
            size = _ceil_to_decimals(size + inc, decimals)
            notional = size * price

        logger.info(f"\n>>> EXECUTING {signal.action.upper()} {symbol} (TRANCHE 1/{self.scale_tranches}) <<<")
        logger.info(f"Margin: ${initial_margin:.2f} x {leverage}x leverage = ${notional:.2f} notional")

        # Set leverage BEFORE order - retry if fails
        for attempt in range(3):
            lev_result = self.hl.set_leverage(symbol, leverage, is_cross=True)
            if lev_result.get("success"):
                logger.info(f">>> LEVERAGE SET: {leverage}x for {symbol} <<<")
                break
            else:
                logger.warning(f"Leverage attempt {attempt+1} failed: {lev_result.get('error')}")
                if attempt == 2:
                    logger.error(f"FAILED to set {leverage}x leverage after 3 attempts - proceeding anyway")

        logger.info(f"Size: {size:.6f} {symbol} (~${notional:.2f} notional, ${initial_margin:.2f} margin)")

        # === CLAUDE DECIDES SL/TP (leverage-aware) ===
        # Get adaptive regime and volatility for context
        regime = market_data.get("adaptive_regime", "ranging")
        atr = market_data.get("atr", price * 0.02)

        # Detect volatility regime from ATR ratio or market data
        atr_ratio = market_data.get("atr_ratio", 1.0)
        if atr_ratio > 1.5:
            volatility_regime = "high"
        elif atr_ratio < 0.7:
            volatility_regime = "low"
        else:
            volatility_regime = "normal"

        logger.info(f"   📊 VOLATILITY REGIME: {volatility_regime.upper()} (ATR ratio: {atr_ratio:.2f})")

        sltp_decision = self.llm.decide_sltp(
            symbol=symbol,
            side=signal.action,
            entry_price=price,
            leverage=leverage,
            market_data=market_data,
            signal_reasoning=signal.reasoning
        )

        stop_loss = sltp_decision.stop_loss
        take_profit = sltp_decision.take_profit

        # === APPLY VOLATILITY ADAPTATION (fallback if Claude doesn't adapt well) ===
        # Use our calculate_sltp as sanity check / fallback
        quant_sltp = self.calculate_sltp(symbol, price, signal.action, volatility_regime)

        # If Claude's SL is way too tight for high vol, widen it
        if volatility_regime == "high":
            min_sl_distance = price * 0.001  # At least 0.1% in high vol
            sl_distance = abs(stop_loss - price)
            if sl_distance < min_sl_distance:
                logger.warning(f"   ⚠️ SL too tight for high vol! Widening to {quant_sltp['sl_price_pct']:.3f}%")
                stop_loss = quant_sltp["stop_loss"]

        logger.info(f"   🧠 CLAUDE SL/TP: Regime={regime} | Volatility={volatility_regime} | Leverage={leverage}x")
        logger.info(f"   📐 SL=${stop_loss:,.2f} | TP=${take_profit:,.2f} | R:R={sltp_decision.risk_reward_ratio:.1f} | MaxLoss={sltp_decision.max_position_loss_pct:.0f}%")
        logger.info(f"   💡 {sltp_decision.reasoning[:100]}...")

        order_side = "buy" if signal.action == "long" else "sell"

        # Determine if we should use limit order (Claude specified entry price)
        use_limit_order = False
        entry_price = price  # Default to market price

        if signal.entry_price and signal.entry_price > 0:
            entry_price = signal.entry_price
            price_diff_pct = abs(entry_price - price) / price * 100

            # Use limit order if Claude wants a different price (> 0.05% difference)
            if price_diff_pct > 0.05:
                use_limit_order = True
                logger.info(f"🎯 LIMIT ORDER: Claude wants entry at ${entry_price:.2f} ({price_diff_pct:.2f}% from market)")

        if use_limit_order:
            # Place limit order with native SL/TP attached (all orders submitted together)
            logger.info(f"📋 Placing LIMIT {order_side.upper()} @ ${entry_price:.2f} with native SL/TP")
            result = self.hl.place_limit_order_with_sltp(
                symbol=symbol,
                side=order_side,
                size=size,
                price=entry_price,
                stop_loss_price=stop_loss,
                take_profit_price=take_profit
            )

            if result.get("success"):
                entry_status = result.get("entry_status", {})
                if entry_status.get("resting"):
                    order_oid = entry_status['resting'].get('oid')
                    logger.info(f"✅ LIMIT ORDER RESTING: {order_side.upper()} {size} {symbol} @ ${entry_price:.2f}")
                    logger.info(f"   SL/TP orders also placed! (entry oid: {order_oid})")
                    logger.info(f"   🛑 SL: ${stop_loss:,.2f} | 🎯 TP: ${take_profit:,.2f}")
                elif entry_status.get("filled"):
                    logger.info(f"✅ LIMIT ORDER FILLED IMMEDIATELY: {order_side.upper()} {size} {symbol}")
                    logger.info(f"   🛑 SL: ${stop_loss:,.2f} | 🎯 TP: ${take_profit:,.2f}")
        else:
            # Use market order with native exchange SL/TP - position runs without bot micromanagement!
            logger.info(f"🚀 Placing MARKET {order_side.upper()} @ ~${price:.2f} with native SL/TP")
            result = self.hl.place_market_order_with_sltp(
                symbol=symbol,
                side=order_side,
                size=size,
                stop_loss_price=stop_loss,
                take_profit_price=take_profit
            )

        if result.get("success"):
            fill_price = result.get("entry_price", price)
            logger.info(f"✅ Order filled @ ${fill_price:,.2f}")
            logger.info(f"   🔒 NATIVE SL/TP SET: Stop=${stop_loss:,.2f} | Target=${take_profit:,.2f}")
            logger.info(f"   ⚡ Exchange manages exits - position protected even if bot disconnects!")

            # === CAPTURE COMPREHENSIVE ENTRY CONDITIONS FOR LEARNING ===
            # Now we have all the info: SL/TP, confidence, fill price
            entry_conditions = self._capture_entry_conditions(
                symbol=symbol,
                market_data=market_data,
                strategy_type="swing",
                signal_confidence=signal.confidence,
                stop_loss=stop_loss,
                take_profit=take_profit,
                entry_price=fill_price
            )
            self.pending_entry_conditions[symbol] = entry_conditions
            logger.info(f"   🧠 Full entry conditions captured for learning")

            # === RECORD TRADE SIGNAL FOR OUTCOME LEARNING (SQLite) ===
            try:
                db = get_db()
                db.save_trade_signal(
                    symbol=symbol,
                    side=signal.action,
                    entry_price=fill_price,
                    confidence=signal.confidence,
                    support_levels=market_data.get("support_levels", []),
                    resistance_levels=market_data.get("resistance_levels", []),
                    stop_loss=stop_loss,
                    take_profit=take_profit,
                    metadata=entry_conditions
                )
                logger.info(f"   📀 Trade signal saved to database")
            except Exception as e:
                logger.warning(f"Failed to save trade signal: {e}")

            # Build and store comprehensive thesis with LLM reasoning AND thesis summary
            thesis = self._build_thesis(
                symbol, signal.action, market_data,
                llm_reasoning=signal.reasoning,
                thesis_summary=signal.thesis_summary
            )
            thesis["entry_time"] = datetime.utcnow()
            thesis["stop_loss"] = stop_loss
            thesis["take_profit"] = take_profit
            thesis["sl_oid"] = result.get("sl_oid")
            thesis["tp_oid"] = result.get("tp_oid")
            thesis["native_sltp"] = True
            self.active_thesis[symbol] = thesis

            # Update risk manager position tracking
            self.risk_manager.update_position(symbol, signal.action)

            # Setup pending scale-ins if scaling enabled
            if self.scaling_enabled:
                self.pending_scales[symbol] = {
                    "side": signal.action,
                    "entry_price": fill_price,
                    "tranches_remaining": self.scale_tranches - 1,
                    "tranche_size": size,
                    "next_scale_price": fill_price * (1 - self.scale_dip_pct / 100) if signal.action == "long" else fill_price * (1 + self.scale_dip_pct / 100),
                    "leverage": leverage,
                    "decimals": decimals
                }
                logger.info(f">>> SCALE-IN SETUP: {self.pending_scales[symbol]['tranches_remaining']} more tranches at {self.scale_dip_pct}% dips <<<")

            # Record trade to start cooldown
            self._record_trade(symbol, signal.action)
        else:
            logger.error(f"Order failed: {result.get('error')}")

    def get_status(self) -> Dict[str, Any]:
        """Get current bot status."""
        state = self.hl.get_account_state()

        # Backwards compatibility: older code used config.symbol (single symbol).
        symbol = getattr(self.config, "symbol", None) or (self.config.symbols[0] if self.config.symbols else None)
        price = self.hl.get_price(symbol) if symbol else None

        return {
            "is_running": self.is_running,
            "symbol": symbol,
            "price": price,
            "equity": state["equity"],
            "positions": state["positions"],
            "last_signal": {
                "action": self.last_signal.action,
                "confidence": self.last_signal.confidence,
                "reasoning": self.last_signal.reasoning
            } if self.last_signal else None
        }

    def get_performance_summary(self) -> Dict[str, Any]:
        """Get performance tracking summary."""
        return self.perf_tracker.get_overall_metrics()

    def get_performance_report(self) -> str:
        """Get human-readable performance report."""
        return self.perf_tracker.get_summary_report()

    def get_trade_history(self, limit: int = 20) -> list:
        """Get recent trade history."""
        return self.perf_tracker.trades[-limit:] if self.perf_tracker.trades else []

    def get_learning_report(self) -> str:
        """Get what the bot has learned from past trades."""
        return self.trade_analyzer.get_learning_summary()

    def get_learned_thresholds(self) -> Dict[str, Any]:
        """Get the dynamically adjusted thresholds based on learning."""
        return self.trade_analyzer.get_learned_thresholds()

    def get_pattern_analysis(self) -> Dict[str, Any]:
        """Get detailed pattern analysis from historical trades."""
        return self.trade_analyzer.analyze_patterns()

    def get_risk_status(self) -> Dict[str, Any]:
        """Get current risk management status."""
        status = self.risk_manager.get_status()
        status["daily_loss_limit"] = self.config.daily_loss_limit_pct
        status["circuit_breaker_losses_threshold"] = self.config.circuit_breaker_losses
        status["max_same_direction"] = self.config.max_same_direction_positions
        return status

    # ========== ADVANCED LEARNING SYSTEM ==========

    async def run_weekly_review(self, days_back: int = 7) -> Dict[str, Any]:
        """Run LLM-powered weekly trade review.

        Analyzes recent trades with Claude to identify:
        - Winning patterns to repeat
        - Losing patterns to avoid
        - Exit optimization recommendations
        - Confidence calibration
        """
        result = await self.llm_reviewer.run_review_async(days_back)
        if result.get("status") == "success":
            self.last_weekly_review = datetime.utcnow()
            logger.info("🧠 Weekly LLM review completed")
            logger.info(self.llm_reviewer.get_review_report())
        return result

    def get_llm_review_report(self) -> str:
        """Get the latest LLM trade review report."""
        return self.llm_reviewer.get_review_report()

    def get_parameter_optimization(self) -> str:
        """Get adaptive parameter optimization recommendations."""
        self.param_optimizer.generate_parameter_adjustments()
        return self.param_optimizer.get_adjustment_report()

    def get_regime_analysis(self) -> str:
        """Get performance analysis by market regime."""
        return self.regime_tracker.get_regime_report()

    async def _track_alpha_call_outcomes(self) -> None:
        """Track pending alpha calls and update their outcomes when price hits TP/SL.

        This enables LEARNING from Discord alpha calls:
        - Which trend conditions led to wins vs losses
        - Which patterns work for longs vs shorts
        - Builds data for AI to avoid repeating losing patterns
        """
        try:
            from src.database import get_db
            db = get_db()

            # Get pending alpha calls (last 24h, not yet resolved)
            pending_calls = db.get_pending_alpha_calls(max_age_hours=24)

            if not pending_calls:
                return

            for call in pending_calls:
                symbol = call.get("symbol")
                if not symbol:
                    continue

                # Get current price
                try:
                    price = self.hl.get_price(symbol) if self.hl else None
                    if not price:
                        continue
                except:
                    continue

                entry = call.get("entry_price") or 0
                tp = call.get("take_profit") or 0
                sl = call.get("stop_loss") or 0
                direction = (call.get("direction") or "").lower()
                alert_id = call.get("id")

                if not all([entry, tp, sl, direction, alert_id]):
                    continue

                outcome = None
                pnl_pct = None

                if direction == "long":
                    if price >= tp:
                        outcome = "hit_tp"
                        pnl_pct = (tp - entry) / entry * 100
                    elif price <= sl:
                        outcome = "hit_sl"
                        pnl_pct = (sl - entry) / entry * 100
                elif direction == "short":
                    if price <= tp:
                        outcome = "hit_tp"
                        pnl_pct = (entry - tp) / entry * 100
                    elif price >= sl:
                        outcome = "hit_sl"
                        pnl_pct = (entry - sl) / entry * 100

                if outcome:
                    db.update_alpha_call_outcome(
                        alert_id=alert_id,
                        outcome=outcome,
                        pnl_pct=pnl_pct,
                        exit_price=price
                    )
                    logger.info(f"📊 Alpha call {symbol} {direction.upper()} resolved: {outcome} ({pnl_pct:+.2f}%)")

        except Exception as e:
            logger.debug(f"Alpha call tracking error: {e}")

    def get_best_trading_conditions(self) -> Dict[str, Any]:
        """Get the best conditions to trade based on historical data."""
        return self.regime_tracker.get_best_conditions()

    async def _run_learning_validation(self) -> None:
        """Run learning validation cycle (hourly) to validate predictions and correlate outcomes."""
        now = datetime.utcnow()
        if now - self.last_learning_validation < self.learning_validation_interval:
            return  # Not time yet

        self.last_learning_validation = now

        try:
            logger.info("📚 Running learning validation cycle...")
            results = await self.learning_engine.run_validation_cycle()

            # Log summary
            chart_v = results.get("chart_validation", {})
            whale_v = results.get("whale_validation", {})

            if chart_v.get("validated", 0) > 0:
                logger.info(f"   📊 Charts: {chart_v.get('validated')} validated, "
                           f"{chart_v.get('accuracy', 0):.1f}% accurate")

            if whale_v.get("validated", 0) > 0:
                logger.info(f"   🐋 Whales: {whale_v.get('validated')} validated, "
                           f"{whale_v.get('follow_rate', 0):.1f}% profitable to follow")

        except Exception as e:
            logger.debug(f"Learning validation error: {e}")

    def get_setup_confidence(self, symbol: str, side: str, market_data: Dict) -> Dict[str, Any]:
        """Get AI confidence score for a trade setup using all learning sources.

        This integrates:
        - Chart prediction accuracy
        - Whale follow success rate
        - Pattern win rates
        - Recent symbol performance
        """
        # Capture current conditions
        conditions = self.learning_engine.capture_entry_conditions(symbol, market_data)

        # Get confidence from learning engine
        return self.learning_engine.get_setup_confidence(symbol, side, conditions)

    def get_learning_engine_context(self, symbol: str = None) -> Dict[str, Any]:
        """Get full learning context for AI prompts."""
        return self.learning_engine.get_full_learning_context(symbol)

    def get_comprehensive_learning_report(self) -> str:
        """Get a comprehensive report combining all learning insights."""
        lines = [
            "=" * 80,
            "🧠 COMPREHENSIVE LEARNING REPORT",
            "=" * 80,
            "",
            self.trade_analyzer.get_learning_summary(),
            "",
            self.regime_tracker.get_regime_report(),
            "",
            self.param_optimizer.get_adjustment_report(),
        ]

        if self.llm_reviewer.review_history:
            lines.append("")
            lines.append(self.llm_reviewer.get_review_report())

        # Add ML model report if available
        if self.ml_predictor.model:
            lines.append("")
            lines.append(self.ml_predictor.get_feature_importance_report())

        return "\n".join(lines)

    # ========== ML PREDICTION SYSTEM ==========

    def train_ml_model(self, min_trades: int = 30) -> Dict[str, Any]:
        """Train/retrain the ML trade predictor on historical trades.

        Args:
            min_trades: Minimum trades required to train

        Returns:
            Training result dict
        """
        return self.ml_predictor.train(self.perf_tracker.trades, min_trades)

    def get_ml_prediction(self, entry_conditions, side: str) -> Dict[str, Any]:
        """Get ML prediction for a trade setup.

        Args:
            entry_conditions: EntryConditions object
            side: "long" or "short"

        Returns:
            Prediction result dict
        """
        result = self.ml_predictor.predict(entry_conditions, side)
        return result.to_dict()

    def get_ml_report(self) -> str:
        """Get ML model status and feature importance report."""
        if not self.ml_predictor.model:
            return "🤖 ML Model: Not trained yet. Run 'ml-train' after 30+ trades."
        return self.ml_predictor.get_feature_importance_report()

    def set_ml_filter(self, enabled: bool, min_probability: float = 0.55):
        """Enable/disable ML filtering for trades.

        Args:
            enabled: Whether to use ML filter
            min_probability: Minimum win probability to take trade
        """
        self.use_ml_filter = enabled
        self.ml_min_probability = min_probability
        status = "ENABLED" if enabled else "DISABLED"
        logger.info(f"🤖 ML Filter {status} (min prob: {min_probability:.0%})")

    # ========== SIGNAL LEARNING FROM DISCORD ALERTS ==========

    def get_signal_learning_insights(self) -> Dict[str, Any]:
        """Get insights from signal learning (Discord alerts & charts).

        Returns performance stats on:
        - Chart signal accuracy by type (5m vs daily)
        - DeepSeek recommendation accuracy
        - Trendline signal reliability
        - Per-symbol performance
        """
        if not self.signal_learner:
            return {"status": "not_initialized", "message": "Signal learner not available"}

        return self.signal_learner.get_insights()

    def get_signal_training_data(self) -> List[Dict]:
        """Get signal data formatted for ML training.

        Returns list of signals with outcomes for training models.
        """
        if not self.signal_learner:
            return []

        return self.signal_learner.get_training_data()

    def print_signal_learning_report(self) -> str:
        """Generate human-readable signal learning report."""
        insights = self.get_signal_learning_insights()

        if insights.get("status") == "not_initialized":
            return "📚 Signal Learning: Not initialized"

        lines = ["📚 **Signal Learning Report**", ""]
        lines.append(f"Total signals tracked: {insights.get('total_signals_tracked', 0)}")

        # Signal type accuracy
        if insights.get("signal_types"):
            lines.append("\n**Accuracy by Signal Type:**")
            for sig_type, data in insights["signal_types"].items():
                lines.append(f"  • {sig_type}: {data['accuracy']:.0f}% ({data['correct']}/{data['total']})")

        # DeepSeek performance
        ds = insights.get("deepseek_performance", {})
        if ds:
            lines.append(f"\n**DeepSeek Accuracy:** {ds.get('accuracy', 0):.0f}% ({ds.get('total_predictions', 0)} predictions)")

        # Trendline performance
        tl = insights.get("trendline_performance", {})
        if tl:
            lines.append(f"**Trendline Accuracy:** {tl.get('accuracy', 0):.0f}% ({tl.get('total', 0)} signals)")

        # Symbol accuracy
        if insights.get("symbol_accuracy"):
            lines.append("\n**Per-Symbol Accuracy:**")
            for symbol, data in insights["symbol_accuracy"].items():
                lines.append(f"  • {symbol}: {data['accuracy']:.0f}%")

        # Recommendations
        if insights.get("recommendations"):
            lines.append("\n**Recommendations:**")
            for rec in insights["recommendations"]:
                lines.append(f"  {rec}")

        return "\n".join(lines)

    def get_trading_intelligence(self) -> Dict[str, Any]:
        """Get trading intelligence from historical database.

        Returns:
            Dict with best performing symbols, whale accuracy, chart signal accuracy
        """
        try:
            db = get_db()

            # Get overall stats
            stats = db.get_signal_accuracy_stats()

            # Get best performing symbols
            best_symbols = db.get_best_performing_symbols(limit=5)

            # Get whale accuracy
            whale_acc = db.get_whale_accuracy()

            # Get chart signal accuracy by type
            chart_5m = db.get_chart_signal_accuracy(signal_type="chart_5m")
            chart_daily = db.get_chart_signal_accuracy(signal_type="chart_daily")

            return {
                "overall_stats": stats,
                "best_symbols": best_symbols,
                "whale_follow_accuracy": whale_acc,
                "chart_signals": {
                    "5m": chart_5m,
                    "daily": chart_daily
                },
                "recommendations": self._generate_intelligence_recommendations(
                    best_symbols, whale_acc, chart_5m, chart_daily
                )
            }
        except Exception as e:
            logger.error(f"Failed to get trading intelligence: {e}")
            return {"error": str(e)}

    def _generate_intelligence_recommendations(self, best_symbols: List,
                                               whale_acc: Dict, chart_5m: Dict,
                                               chart_daily: Dict) -> List[str]:
        """Generate actionable recommendations from historical data."""
        recs = []

        # Best symbols recommendation
        if best_symbols:
            top = best_symbols[0]
            if top["win_rate"] > 0.6:
                recs.append(f"🎯 Focus on {top['symbol']} - {top['win_rate']:.0%} historical win rate")

        # Whale follow recommendation
        if whale_acc["total_trades"] >= 10:
            if whale_acc["win_rate"] > 0.55:
                recs.append(f"🐋 Whale signals are profitable ({whale_acc['win_rate']:.0%}) - weight them higher")
            elif whale_acc["win_rate"] < 0.45:
                recs.append(f"⚠️ Whale signals underperforming ({whale_acc['win_rate']:.0%}) - use with caution")

        # Chart signal recommendations
        if chart_5m["total"] >= 10:
            if chart_5m["win_rate"] > 0.55:
                recs.append(f"📊 5m charts are accurate ({chart_5m['win_rate']:.0%}) - trust breakout signals")
            elif chart_5m["win_rate"] < 0.45:
                recs.append(f"⚠️ 5m charts unreliable ({chart_5m['win_rate']:.0%}) - wait for confirmation")

        if chart_daily["total"] >= 5:
            if chart_daily["win_rate"] > 0.6:
                recs.append(f"📅 Daily charts highly accurate ({chart_daily['win_rate']:.0%}) - prioritize daily setups")

        if not recs:
            recs.append("📈 Collecting more data for recommendations...")

        return recs

    def print_trading_intelligence(self) -> str:
        """Print human-readable trading intelligence report."""
        intel = self.get_trading_intelligence()

        if "error" in intel:
            return f"❌ Intelligence Error: {intel['error']}"

        lines = ["📀 **Trading Intelligence Report**", ""]

        # Overall stats
        stats = intel.get("overall_stats", {})
        if stats:
            lines.append("**Overall Accuracy:**")
            if stats.get("whale_follow", {}).get("total", 0) > 0:
                wf = stats["whale_follow"]
                lines.append(f"  • Whale Follows: {wf['accuracy']:.0%} ({wf['total']} trades)")
            if stats.get("chart_signals", {}).get("total", 0) > 0:
                cs = stats["chart_signals"]
                lines.append(f"  • Chart Signals: {cs['accuracy']:.0%} ({cs['total']} signals)")
            if stats.get("trades", {}).get("total", 0) > 0:
                tr = stats["trades"]
                lines.append(f"  • Trade Win Rate: {tr['win_rate']:.0%} ({tr['total']} trades)")

        # Best symbols
        best = intel.get("best_symbols", [])
        if best:
            lines.append("\n**Best Performing Symbols:**")
            for s in best[:5]:
                emoji = "🟢" if s["win_rate"] > 0.55 else "🟡" if s["win_rate"] > 0.45 else "🔴"
                lines.append(f"  {emoji} {s['symbol']}: {s['win_rate']:.0%} ({s['total']} samples)")

        # Recommendations
        recs = intel.get("recommendations", [])
        if recs:
            lines.append("\n**Recommendations:**")
            for rec in recs:
                lines.append(f"  {rec}")

        return "\n".join(lines)

    def get_trading_intelligence(self) -> Dict[str, Any]:
        """Get trading intelligence from historical database."""
        try:
            db = get_db()
            stats = db.get_signal_accuracy_stats()
            best_symbols = db.get_best_performing_symbols(limit=5)
            whale_acc = db.get_whale_accuracy()
            chart_5m = db.get_chart_signal_accuracy(signal_type="chart_5m")
            chart_daily = db.get_chart_signal_accuracy(signal_type="chart_daily")

            return {
                "overall_stats": stats,
                "best_symbols": best_symbols,
                "whale_accuracy": whale_acc,
                "chart_signals": {"5m": chart_5m, "daily": chart_daily},
            }
        except Exception as e:
            logger.error(f"Failed to get trading intelligence: {e}")
            return {"error": str(e)}

    # ========== WHALE PATTERN ML SYSTEM ==========

    def train_whale_ml(self, download_first: bool = False) -> Dict[str, Any]:
        """Train the whale pattern ML model.

        Args:
            download_first: If True, download fresh whale data before training

        Returns:
            Training result dict
        """
        if self.whale_ml is None:
            return {"status": "error", "message": "Whale ML not available"}

        if download_first:
            from src.whale_data_collector import WhaleDataCollector
            collector = WhaleDataCollector()
            logger.info("🐋 Downloading whale trade history...")
            collector.download_all_whales(days_back=90)

        logger.info("🐋 Training whale pattern model...")
        stats = self.whale_ml.train()
        self.whale_ml.save()
        return stats

    def get_whale_ml_report(self) -> str:
        """Get whale ML model status report."""
        if self.whale_ml is None:
            return "🐋 Whale ML: Not available (import error)"
        return self.whale_ml.get_report()

    def set_whale_ml_filter(self, enabled: bool, min_score: float = 0.4):
        """Enable/disable whale ML filtering for trades.

        Args:
            enabled: Whether to use whale ML filter
            min_score: Minimum score to take trade (0-1)
        """
        self.use_whale_ml_filter = enabled
        self.whale_ml_min_score = min_score
        status = "ENABLED" if enabled else "DISABLED"
        logger.info(f"🐋 Whale ML Filter {status} (min score: {min_score:.0%})")

    def evaluate_with_whale_ml(self, symbol: str, side: str) -> Dict:
        """Evaluate a trade opportunity using whale ML.

        Args:
            symbol: Asset symbol (e.g., "SOL")
            side: "long" or "short"

        Returns:
            Evaluation result dict
        """
        if self.whale_ml is None or not self.whale_ml.trained:
            return {"error": "Whale ML not trained"}

        direction = "Open Long" if side == "long" else "Open Short"
        return self.whale_ml.evaluate_trade_opportunity(
            asset=symbol,
            direction=direction,
            hl_client=self.hl
        )

    # ========== DISCORD NOTIFICATIONS (Market Analysis Only) ==========

    async def _send_discord_updates(self, symbol: str, market_data: Dict[str, Any]) -> None:
        """Send EVENT-DRIVEN alerts to Discord. Only when something significant happens.

        Triggers:
        1. Price at support/resistance (within 0.3%)
        2. Trend flip detected (4h trend changed)
        3. Whale order detected (>$500K single order)
        4. High-confidence trade setup (quant score >= 75)

        NO periodic spam - only real-time quality alerts.
        """
        if not self.discord:
            return

        try:
            price = market_data.get("price", 0)
            if not price:
                return

            now = datetime.utcnow()

            # Initialize tracking for this symbol
            if symbol not in self.alerted_sr_levels:
                self.alerted_sr_levels[symbol] = set()

            # ===== 1. SUPPORT/RESISTANCE ALERT (price within 0.3% of level) =====
            support = market_data.get("nearest_support") or market_data.get("support_level")
            resistance = market_data.get("nearest_resistance") or market_data.get("resistance_level")

            sr_alert_threshold = 0.003  # 0.3% from level

            if support and abs(price - support) / price < sr_alert_threshold:
                level_key = f"support_{round(support, -1)}"  # Round to avoid duplicate alerts
                if level_key not in self.alerted_sr_levels[symbol]:
                    self.alerted_sr_levels[symbol].add(level_key)
                    await self.discord.send_sr_alert(symbol, "support", price, support)
                    logger.info(f"📢 Discord: {symbol} AT SUPPORT ${support:,.0f}")

            if resistance and abs(price - resistance) / price < sr_alert_threshold:
                level_key = f"resistance_{round(resistance, -1)}"
                if level_key not in self.alerted_sr_levels[symbol]:
                    self.alerted_sr_levels[symbol].add(level_key)
                    await self.discord.send_sr_alert(symbol, "resistance", price, resistance)
                    logger.info(f"📢 Discord: {symbol} AT RESISTANCE ${resistance:,.0f}")

            # Clear old S/R alerts every hour (allow re-alert if price returns)
            alert_key = f"{symbol}_sr_clear"
            last_clear = self.last_discord_alert.get(alert_key, datetime.min)
            if (now - last_clear).total_seconds() > 3600:
                self.alerted_sr_levels[symbol].clear()
                self.last_discord_alert[alert_key] = now

            # ===== 2. BREAKOUT ALERT (trendline breaking) =====
            trendline_signal = market_data.get("trendline_signal", "neutral")
            breakout_conf = market_data.get("breakout_confidence", 0)

            if trendline_signal in ["breaking_support", "breaking_resistance"]:
                alert_key = f"{symbol}_breakout_{trendline_signal}"
                last_alert = self.last_discord_alert.get(alert_key, datetime.min)

                # Alert once per breakout event (30 min cooldown)
                if (now - last_alert).total_seconds() > 1800:
                    self.last_discord_alert[alert_key] = now

                    # Get the level being broken
                    if trendline_signal == "breaking_support":
                        level = market_data.get("ascending_trendline_price") or support
                    else:
                        level = market_data.get("descending_trendline_price") or resistance

                    await self.discord.send_breakout_alert(
                        symbol, trendline_signal, price, level, breakout_conf
                    )
                    logger.info(f"📢 Discord: {symbol} BREAKOUT {trendline_signal.upper()} @ ${level:,.0f}")

            # ===== 3. TREND FLIP ALERT (4h macro trend changed) =====
            current_trend = market_data.get("ema_macro_signal", "neutral")
            last_trend = self.last_known_trend.get(symbol, "neutral")

            if current_trend != last_trend and current_trend in ["bullish", "bearish"]:
                alert_key = f"{symbol}_trend_flip"
                last_alert = self.last_discord_alert.get(alert_key, datetime.min)

                # Don't spam - min 30 min between trend alerts
                if (now - last_alert).total_seconds() > 1800:
                    self.last_discord_alert[alert_key] = now
                    self.last_known_trend[symbol] = current_trend

                    await self.discord.send_trend_update(symbol, {
                        "trend_5m": market_data.get("ema_micro_signal"),
                        "trend_1h": market_data.get("ema_mid_signal"),
                        "trend_4h": current_trend,
                        "rsi": market_data.get("rsi"),
                        "alert_type": "TREND_FLIP",
                        "previous_trend": last_trend,
                    })
                    logger.info(f"📢 Discord: {symbol} TREND FLIP {last_trend} → {current_trend}")
            else:
                self.last_known_trend[symbol] = current_trend

            # ===== 4. WHALE ORDER ALERT (large orders in orderbook) =====
            orderbook_data = market_data.get("orderbook_analysis", {})
            large_bids = orderbook_data.get("large_bids", [])
            large_asks = orderbook_data.get("large_asks", [])

            # Only alert for truly large orders ($500K+)
            whale_threshold = 500_000
            huge_bids = [b for b in large_bids if b.get("size_usd", 0) >= whale_threshold]
            huge_asks = [a for a in large_asks if a.get("size_usd", 0) >= whale_threshold]

            if huge_bids or huge_asks:
                alert_key = f"{symbol}_whale"
                last_alert = self.last_discord_alert.get(alert_key, datetime.min)

                # Don't spam - min 15 min between whale alerts
                if (now - last_alert).total_seconds() > 900:
                    self.last_discord_alert[alert_key] = now
                    await self.discord.send_whale_activity(symbol, {
                        "large_bids": huge_bids[:3],
                        "large_asks": huge_asks[:3],
                        "bid_depth_usd": orderbook_data.get("bid_depth_usd", 0),
                        "ask_depth_usd": orderbook_data.get("ask_depth_usd", 0),
                    })
                    logger.info(f"📢 Discord: {symbol} WHALE ORDER detected")

            # ===== 4. WHALE WALLET POSITION TRACKING =====
            # Alert when tracked whale wallets open or close positions
            alpha_signals = market_data.get("alpha_signals", {})
            whale_tracking = alpha_signals.get("whale_tracking", {}) or {}

            new_whale_positions = whale_tracking.get("new_positions", []) or []
            closed_whale_positions = whale_tracking.get("closed_positions", []) or []
            whale_consensus = whale_tracking.get("whale_consensus", {}) or {}

            # Alert for new whale positions (any symbol - whale moves are important)
            for pos in new_whale_positions:
                pos_symbol = pos.get("symbol", "?")
                whale_name = pos.get("whale", "Unknown")
                side = pos.get("side", "?")
                # Create unique key based on whale + symbol + side + entry time
                whale_key = f"whale_open_{whale_name}_{pos_symbol}_{side}"
                last_alert = self.last_discord_alert.get(whale_key, datetime.min)
                # Allow re-alerting after 30 min (in case whale adds to position)
                if (now - last_alert).total_seconds() > 1800:
                    self.last_discord_alert[whale_key] = now
                    await self.discord.send_whale_position_alert(pos, action="opened")
                    logger.info(f"📢 Discord: Whale {whale_name} OPENED {side} on {pos_symbol}")

            # Alert for closed whale positions (any symbol)
            for pos in closed_whale_positions:
                pos_symbol = pos.get("symbol", "?")
                whale_name = pos.get("whale", "Unknown")
                side = pos.get("side", "?")
                # Create unique key for close event
                whale_key = f"whale_close_{whale_name}_{pos_symbol}_{side}"
                last_alert = self.last_discord_alert.get(whale_key, datetime.min)
                # Allow re-alerting after 30 min
                if (now - last_alert).total_seconds() > 1800:
                    self.last_discord_alert[whale_key] = now
                    await self.discord.send_whale_position_alert(pos, action="closed")
                    logger.info(f"📢 Discord: Whale {whale_name} CLOSED {side} on {pos_symbol}")

            # Send whale consensus update if significant (3+ whales)
            sym_consensus = whale_consensus.get(symbol, {})
            longs = sym_consensus.get("longs", 0)
            shorts = sym_consensus.get("shorts", 0)
            if longs + shorts >= 3:
                consensus_key = f"{symbol}_whale_consensus"
                last_consensus = self.last_discord_alert.get(consensus_key, datetime.min)
                # Update every 4 hours
                if (now - last_consensus).total_seconds() > 14400:
                    self.last_discord_alert[consensus_key] = now
                    await self.discord.send_whale_consensus(symbol, longs, shorts)
                    logger.info(f"📢 Discord: {symbol} whale consensus {longs}L/{shorts}S")

            # ===== 5. HIGH-QUALITY TRADE SETUP (quant score >= 75) =====
            quant_score = market_data.get("quant_score", {})
            score = quant_score.get("score", 0)
            direction = quant_score.get("direction", "neutral")

            if score >= 75 and direction != "neutral":
                alert_key = f"{symbol}_setup"
                last_alert = self.last_discord_alert.get(alert_key, datetime.min)

                # Don't spam - min 1 hour between setup alerts
                if (now - last_alert).total_seconds() > 3600:
                    self.last_discord_alert[alert_key] = now
                    await self.discord.send_trade_setup(symbol, {
                        "action": "LONG" if direction == "bullish" else "SHORT",
                        "confidence": score / 100,
                        "entry_zone": price,
                        "stop_zone": price * (0.97 if direction == "bullish" else 1.03),
                        "target_zone": price * (1.05 if direction == "bullish" else 0.95),
                        "reasoning": ". ".join(quant_score.get("signals", [])[:3]),
                        "timeframe": "Short-term (15m-4h)",
                    })
                    logger.info(f"📢 Discord: {symbol} HIGH-QUALITY SETUP ({score}% {direction})")

            # ===== 6. CHART PATTERN DETECTION (High-quality patterns only) =====
            pattern_key = f"{symbol}_pattern_scan"
            last_pattern_scan = self.last_discord_alert.get(pattern_key, datetime.min)

            # Scan for patterns every 15 minutes
            if (now - last_pattern_scan).total_seconds() > 900:
                self.last_discord_alert[pattern_key] = now

                candles_5m = market_data.get("candles_5m", [])
                candles_15m = market_data.get("candles_15m", [])
                candles_1h = market_data.get("candles_1h", [])
                candles_4h = market_data.get("candles_4h", [])
                volume_profile = market_data.get("volume_profile", {})

                if candles_5m and candles_15m and candles_1h:
                    try:
                        patterns = self.pattern_detector.get_alert_patterns(
                            candles_5m=candles_5m,
                            candles_15m=candles_15m,
                            candles_1h=candles_1h,
                            candles_4h=candles_4h,
                            volume_profile=volume_profile,
                            min_score=65  # Only high-quality patterns
                        )

                        for pattern in patterns[:3]:  # Top 3 patterns only
                            pattern_alert_key = f"{symbol}_{pattern['name']}_{pattern['direction']}"
                            last_alert = self.last_pattern_alert.get(pattern_alert_key, datetime.min)

                            # Don't spam same pattern for 30 min
                            if (now - last_alert).total_seconds() > self.pattern_alert_cooldown_minutes * 60:
                                self.last_pattern_alert[pattern_alert_key] = now

                                # Liquidity patterns go to alpha channel (highest priority)
                                if pattern.get("type") == "liquidity" and pattern.get("score", 0) >= 75:
                                    await self.discord.send_liquidity_alert(symbol, pattern)
                                    logger.info(f"📢 Discord: {symbol} LIQUIDITY PATTERN {pattern['name']} ({pattern['score']}/100)")
                                else:
                                    await self.discord.send_pattern_alert(symbol, pattern)
                                    logger.info(f"📢 Discord: {symbol} pattern {pattern['name']} ({pattern['score']}/100)")
                    except Exception as pe:
                        logger.debug(f"Pattern detection failed: {pe}")

            # ===== 7. PERIODIC FULL TECHNICAL ANALYSIS (every 1 HOUR) =====
            update_key = f"{symbol}_market_update"
            last_update = self.last_discord_alert.get(update_key, datetime.min)

            if (now - last_update).total_seconds() > 3600:  # 1 hour
                self.last_discord_alert[update_key] = now

                # Send FULL technical analysis with all indicators
                await self.discord.send_full_technical_analysis(symbol, market_data)
                logger.info(f"📢 Discord: {symbol} full technical analysis sent")

                # Also send AI summary for interpretation
                summary = self.llm.generate_market_summary(market_data)
                if summary:
                    await self.discord.send_ai_market_summary(symbol, summary)

        except Exception as e:
            logger.warning(f"Discord alert failed: {e}")
