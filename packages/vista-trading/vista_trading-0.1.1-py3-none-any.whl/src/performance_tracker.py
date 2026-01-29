"""
Performance Tracking Module - Track trading metrics and performance.
"""

import json
import logging
import os
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Dict, List, Optional, Any
import math

logger = logging.getLogger(__name__)


@dataclass
class EntryConditions:
    """Market conditions at trade entry - used for comprehensive learning."""
    # === BASIC INDICATORS (original) ===
    rsi: float = 50.0
    bb_position: float = 0.5  # 0=lower band, 1=upper band
    vwap_distance_pct: float = 0.0  # % above/below VWAP
    trend_5m_score: int = 0
    trend_15m_score: int = 0
    trend_1h_signal: str = "neutral"  # bullish/bearish/neutral
    atr_pct: float = 0.0  # ATR as % of price (volatility)
    hour_of_day: int = 12  # UTC hour
    day_of_week: int = 0  # 0=Monday
    funding_rate: float = 0.0
    volume_ratio: float = 1.0  # Current vol / avg vol

    # === ENHANCED INDICATORS (new) ===
    macd_signal: str = "neutral"  # bullish/bearish/neutral
    ema_fast_signal: str = "neutral"  # 5m EMA crossover signal
    ema_mid_signal: str = "neutral"  # 15m EMA signal
    ema_macro_signal: str = "neutral"  # 1h EMA signal

    # === MARKET REGIME (new) ===
    market_regime: str = "unknown"  # trending_up, trending_down, ranging, volatile
    adaptive_regime: str = "ranging"  # From adaptive_parameters module
    volatility_regime: str = "normal"  # low, normal, high, extreme
    regime_strength: float = 0.0  # 0-100 strength of current regime

    # === SMART MONEY CONCEPTS (new) ===
    smc_bias: str = "neutral"  # bullish/bearish/neutral from SMC analysis
    smc_confidence: float = 0.0  # 0-100 SMC confidence
    near_order_block: bool = False  # Is price near an order block?
    in_fair_value_gap: bool = False  # Is price in a FVG?

    # === ORDERBOOK (new) ===
    orderbook_imbalance: float = 0.0  # -1 (sell heavy) to +1 (buy heavy)
    bid_wall_distance_pct: float = 0.0  # Distance to nearest bid wall
    ask_wall_distance_pct: float = 0.0  # Distance to nearest ask wall

    # === SL/TP TRACKING (new) - for learning optimal distances ===
    sl_distance_pct: float = 0.0  # Stop loss distance as % from entry
    tp_distance_pct: float = 0.0  # Take profit distance as % from entry
    risk_reward_ratio: float = 0.0  # TP distance / SL distance

    # === CONFIDENCE CALIBRATION (new) ===
    signal_confidence: float = 0.5  # Claude's confidence (0-1)

    # === STRATEGY TRACKING (new) ===
    strategy_type: str = "swing"  # swing, micro, macro, snipe

    # === ADDITIONAL CONTEXT (new) ===
    adx: float = 0.0  # Trend strength indicator
    cvd_signal: str = "neutral"  # Cumulative Volume Delta signal
    volume_profile_zone: str = "neutral"  # high_volume, low_volume, poc_area

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "EntryConditions":
        if data is None:
            return cls()
        # Handle missing fields gracefully (backwards compatible)
        valid_fields = {f.name for f in cls.__dataclass_fields__.values()}
        filtered = {k: v for k, v in data.items() if k in valid_fields}
        return cls(**filtered)


@dataclass
class Trade:
    """Record of a completed trade with entry conditions for learning."""
    symbol: str
    side: str  # "long" or "short"
    entry_price: float
    exit_price: float
    size: float
    entry_time: datetime
    exit_time: datetime
    pnl_pct: float
    pnl_usd: float
    exit_reason: str
    # NEW: Entry conditions for pattern learning
    entry_conditions: Optional[EntryConditions] = None
    # NEW: MFE/MAE for trade quality analysis
    mfe_pct: float = 0.0  # Max Favorable Excursion - best P&L during trade
    mae_pct: float = 0.0  # Max Adverse Excursion - worst P&L during trade
    time_to_mfe_minutes: int = 0  # Time from entry to best price
    time_to_mae_minutes: int = 0  # Time from entry to worst price

    @property
    def trade_efficiency(self) -> float:
        """Calculate trade efficiency: how much of MFE was captured.

        Returns 0-1 where 1 = captured all MFE, 0 = captured none.
        """
        if self.mfe_pct <= 0:
            return 0.0
        # For winning trades: pnl / mfe
        # For losing trades: efficiency is 0 (didn't capture any of the favorable move)
        if self.pnl_pct <= 0:
            return 0.0
        return min(1.0, self.pnl_pct / self.mfe_pct)

    def to_dict(self) -> dict:
        d = {
            "symbol": self.symbol,
            "side": self.side,
            "entry_price": self.entry_price,
            "exit_price": self.exit_price,
            "size": self.size,
            "entry_time": self.entry_time.isoformat(),
            "exit_time": self.exit_time.isoformat(),
            "pnl_pct": self.pnl_pct,
            "pnl_usd": self.pnl_usd,
            "exit_reason": self.exit_reason,
            "entry_conditions": self.entry_conditions.to_dict() if self.entry_conditions else None,
            "mfe_pct": self.mfe_pct,
            "mae_pct": self.mae_pct,
            "time_to_mfe_minutes": self.time_to_mfe_minutes,
            "time_to_mae_minutes": self.time_to_mae_minutes
        }
        return d

    @classmethod
    def from_dict(cls, data: dict) -> "Trade":
        data["entry_time"] = datetime.fromisoformat(data["entry_time"])
        data["exit_time"] = datetime.fromisoformat(data["exit_time"])
        # Handle entry_conditions
        ec_data = data.pop("entry_conditions", None)
        data["entry_conditions"] = EntryConditions.from_dict(ec_data) if ec_data else None
        # Handle MFE/MAE fields (backwards compatible)
        data.setdefault("mfe_pct", 0.0)
        data.setdefault("mae_pct", 0.0)
        data.setdefault("time_to_mfe_minutes", 0)
        data.setdefault("time_to_mae_minutes", 0)
        return cls(**data)

    @property
    def trade_efficiency(self) -> float:
        """How much of the MFE was captured. 1.0 = exited at best price."""
        if self.mfe_pct <= 0:
            return 0.0
        return min(1.0, self.pnl_pct / self.mfe_pct) if self.mfe_pct > 0 else 0.0

    @property
    def heat_ratio(self) -> float:
        """Risk taken vs reward achieved. Lower is better (less heat for same gain)."""
        if abs(self.mae_pct) < 0.01:
            return float('inf') if self.pnl_pct > 0 else 0.0
        return self.pnl_pct / abs(self.mae_pct)


@dataclass
class AssetMetrics:
    """Performance metrics for a single asset."""
    symbol: str
    total_trades: int = 0
    wins: int = 0
    losses: int = 0
    total_pnl_pct: float = 0.0
    total_pnl_usd: float = 0.0
    avg_win_pct: float = 0.0
    avg_loss_pct: float = 0.0
    max_win_pct: float = 0.0
    max_loss_pct: float = 0.0
    avg_trade_duration_hours: float = 0.0
    # Professional metrics
    gross_profit: float = 0.0
    gross_loss: float = 0.0
    max_consecutive_wins: int = 0
    max_consecutive_losses: int = 0
    current_streak: int = 0  # Positive = wins, negative = losses

    @property
    def win_rate(self) -> float:
        return (self.wins / self.total_trades * 100) if self.total_trades > 0 else 0.0

    @property
    def profit_factor(self) -> float:
        """Ratio of gross profit to gross loss. >1.5 is good, >2.0 is excellent."""
        if self.gross_loss == 0:
            return float('inf') if self.gross_profit > 0 else 0
        return abs(self.gross_profit / self.gross_loss)

    @property
    def expected_value(self) -> float:
        """Expected value per trade in %. Positive = profitable strategy."""
        if self.total_trades == 0:
            return 0.0
        win_rate_dec = self.wins / self.total_trades
        loss_rate_dec = self.losses / self.total_trades
        return (win_rate_dec * self.avg_win_pct) + (loss_rate_dec * self.avg_loss_pct)

    @property
    def risk_reward_ratio(self) -> float:
        """Average win / average loss. >1.5 is good for scalping."""
        if self.avg_loss_pct == 0:
            return float('inf') if self.avg_win_pct > 0 else 0
        return abs(self.avg_win_pct / self.avg_loss_pct)

    @property
    def edge_quality(self) -> str:
        """Qualitative assessment of edge quality."""
        ev = self.expected_value
        pf = self.profit_factor if self.profit_factor != float('inf') else 10
        wr = self.win_rate

        if self.total_trades < 10:
            return "INSUFFICIENT_DATA"
        elif ev > 0.5 and pf > 2.0 and wr > 55:
            return "EXCELLENT"
        elif ev > 0.2 and pf > 1.5 and wr > 50:
            return "GOOD"
        elif ev > 0 and pf > 1.0:
            return "MARGINAL"
        else:
            return "NO_EDGE"


class PerformanceTracker:
    """Track and analyze trading performance using SQLite database."""

    def __init__(self, data_file: str = "performance_data.json"):
        """Initialize tracker. data_file is kept for backwards compatibility but SQLite is primary."""
        self.data_file = data_file  # Legacy - kept for equity curve only
        self.trades: List[Trade] = []
        self.equity_curve: List[Dict] = []  # [{timestamp, equity}]
        self.starting_equity: float = 0.0
        self.peak_equity: float = 0.0
        self.current_equity: float = 0.0
        self._db = None
        self._load_data()

    def _get_db(self):
        """Get database connection (lazy initialization)."""
        if self._db is None:
            try:
                from src.database import get_db
                self._db = get_db()
            except Exception as e:
                logger.warning(f"Could not connect to database: {e}")
        return self._db

    def _load_data(self) -> None:
        """Load historical trades from SQLite database."""
        # First try to load from SQLite
        db = self._get_db()
        if db:
            try:
                rows = db.get_completed_trades(limit=5000)
                self.trades = []
                for row in rows:
                    try:
                        # Convert database row to Trade object
                        ec_data = row.get("entry_conditions")
                        trade = Trade(
                            symbol=row["symbol"],
                            side=row["side"],
                            entry_price=row["entry_price"],
                            exit_price=row["exit_price"],
                            size=row["size"],
                            entry_time=datetime.fromisoformat(row["entry_time"]) if isinstance(row["entry_time"], str) else row["entry_time"],
                            exit_time=datetime.fromisoformat(row["exit_time"]) if isinstance(row["exit_time"], str) else row["exit_time"],
                            pnl_pct=row["pnl_pct"],
                            pnl_usd=row["pnl_usd"],
                            exit_reason=row.get("exit_reason", "unknown"),
                            entry_conditions=EntryConditions.from_dict(ec_data) if ec_data else None,
                            mfe_pct=row.get("mfe_pct", 0.0),
                            mae_pct=row.get("mae_pct", 0.0),
                            time_to_mfe_minutes=row.get("time_to_mfe_minutes", 0),
                            time_to_mae_minutes=row.get("time_to_mae_minutes", 0),
                        )
                        self.trades.append(trade)
                    except Exception as e:
                        logger.debug(f"Error loading trade row: {e}")
                        continue

                logger.info(f"📀 Loaded {len(self.trades)} trades from SQLite database")
            except Exception as e:
                logger.warning(f"Error loading from SQLite: {e}")

        # If no trades from SQLite, try legacy JSON (migration)
        if not self.trades and os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r') as f:
                    data = json.load(f)
                legacy_trades = [Trade.from_dict(t) for t in data.get("trades", [])]
                self.equity_curve = data.get("equity_curve", [])
                self.starting_equity = data.get("starting_equity", 0.0)
                self.peak_equity = data.get("peak_equity", 0.0)

                # Migrate legacy trades to SQLite
                if legacy_trades and db:
                    logger.info(f"📀 Migrating {len(legacy_trades)} trades from JSON to SQLite...")
                    for trade in legacy_trades:
                        self._save_trade_to_db(trade)
                    self.trades = legacy_trades
                    logger.info(f"📀 Migration complete!")
                else:
                    self.trades = legacy_trades
                    logger.info(f"Loaded {len(self.trades)} historical trades from JSON (legacy)")
            except Exception as e:
                logger.error(f"Error loading performance data: {e}")

        # Load equity curve from JSON (still using JSON for this)
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r') as f:
                    data = json.load(f)
                self.equity_curve = data.get("equity_curve", [])
                self.starting_equity = data.get("starting_equity", 0.0)
                self.peak_equity = data.get("peak_equity", 0.0)
            except:
                pass

    def _save_trade_to_db(self, trade: Trade) -> None:
        """Save a single trade to SQLite database."""
        db = self._get_db()
        if db:
            try:
                db.save_completed_trade(
                    symbol=trade.symbol,
                    side=trade.side,
                    entry_price=trade.entry_price,
                    exit_price=trade.exit_price,
                    size=trade.size,
                    entry_time=trade.entry_time.isoformat() if isinstance(trade.entry_time, datetime) else trade.entry_time,
                    exit_time=trade.exit_time.isoformat() if isinstance(trade.exit_time, datetime) else trade.exit_time,
                    pnl_pct=trade.pnl_pct,
                    pnl_usd=trade.pnl_usd,
                    exit_reason=trade.exit_reason,
                    mfe_pct=trade.mfe_pct,
                    mae_pct=trade.mae_pct,
                    time_to_mfe_minutes=trade.time_to_mfe_minutes,
                    time_to_mae_minutes=trade.time_to_mae_minutes,
                    entry_conditions=trade.entry_conditions.to_dict() if trade.entry_conditions else None
                )
            except Exception as e:
                logger.warning(f"Failed to save trade to SQLite: {e}")

    def _save_data(self) -> None:
        """Save equity curve to JSON file (trades are in SQLite now)."""
        try:
            data = {
                "trades": [],  # Trades now in SQLite - keep empty for legacy compatibility
                "equity_curve": self.equity_curve,
                "starting_equity": self.starting_equity,
                "peak_equity": self.peak_equity
            }
            with open(self.data_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving performance data: {e}")
    
    def set_starting_equity(self, equity: float) -> None:
        """Set initial equity for tracking."""
        if self.starting_equity == 0:
            self.starting_equity = equity
            self.peak_equity = equity
        self.current_equity = equity
    
    def update_equity(self, equity: float) -> None:
        """Update current equity and track curve."""
        self.current_equity = equity
        self.peak_equity = max(self.peak_equity, equity)
        self.equity_curve.append({
            "timestamp": datetime.utcnow().isoformat(),
            "equity": equity
        })
        # Keep last 1000 points
        if len(self.equity_curve) > 1000:
            self.equity_curve = self.equity_curve[-1000:]
        self._save_data()
    
    def record_trade(self, symbol: str, side: str, entry_price: float, exit_price: float,
                     size: float, entry_time: datetime, exit_reason: str,
                     entry_conditions: Optional[EntryConditions] = None,
                     mfe_pct: float = 0.0, mae_pct: float = 0.0,
                     time_to_mfe_minutes: int = 0, time_to_mae_minutes: int = 0) -> Trade:
        """Record a completed trade with entry conditions and MFE/MAE for learning.

        Args:
            mfe_pct: Max Favorable Excursion - the best P&L% achieved during the trade
            mae_pct: Max Adverse Excursion - the worst P&L% during the trade (negative)
            time_to_mfe_minutes: Minutes from entry until MFE was reached
            time_to_mae_minutes: Minutes from entry until MAE was reached
        """
        exit_time = datetime.utcnow()

        # Calculate P&L
        if side == "long":
            pnl_pct = ((exit_price - entry_price) / entry_price) * 100
        else:
            pnl_pct = ((entry_price - exit_price) / entry_price) * 100

        pnl_usd = size * entry_price * (pnl_pct / 100)

        trade = Trade(
            symbol=symbol, side=side, entry_price=entry_price, exit_price=exit_price,
            size=size, entry_time=entry_time, exit_time=exit_time,
            pnl_pct=pnl_pct, pnl_usd=pnl_usd, exit_reason=exit_reason,
            entry_conditions=entry_conditions,
            mfe_pct=mfe_pct, mae_pct=mae_pct,
            time_to_mfe_minutes=time_to_mfe_minutes, time_to_mae_minutes=time_to_mae_minutes
        )
        self.trades.append(trade)

        # Save to SQLite database
        self._save_trade_to_db(trade)

        # Save equity curve to JSON
        self._save_data()

        # Enhanced logging with MFE/MAE
        efficiency = trade.trade_efficiency * 100 if mfe_pct > 0 else 0
        logger.info(f"📊 Trade recorded: {symbol} {side} | P&L: {pnl_pct:+.2f}% (${pnl_usd:+.2f}) | MFE: {mfe_pct:+.2f}% MAE: {mae_pct:+.2f}% | Efficiency: {efficiency:.0f}%")
        return trade

    def get_asset_metrics(self, symbol: str) -> AssetMetrics:
        """Get performance metrics for a specific asset."""
        asset_trades = [t for t in self.trades if t.symbol == symbol]
        metrics = AssetMetrics(symbol=symbol)

        if not asset_trades:
            return metrics

        wins = [t for t in asset_trades if t.pnl_pct > 0]
        losses = [t for t in asset_trades if t.pnl_pct <= 0]

        metrics.total_trades = len(asset_trades)
        metrics.wins = len(wins)
        metrics.losses = len(losses)
        metrics.total_pnl_pct = sum(t.pnl_pct for t in asset_trades)
        metrics.total_pnl_usd = sum(t.pnl_usd for t in asset_trades)

        # Gross profit/loss for profit factor calculation
        metrics.gross_profit = sum(t.pnl_pct for t in wins) if wins else 0
        metrics.gross_loss = abs(sum(t.pnl_pct for t in losses)) if losses else 0

        if wins:
            metrics.avg_win_pct = sum(t.pnl_pct for t in wins) / len(wins)
            metrics.max_win_pct = max(t.pnl_pct for t in wins)

        if losses:
            metrics.avg_loss_pct = sum(t.pnl_pct for t in losses) / len(losses)
            metrics.max_loss_pct = min(t.pnl_pct for t in losses)

        # Calculate consecutive wins/losses
        metrics.max_consecutive_wins, metrics.max_consecutive_losses, metrics.current_streak = \
            self._calculate_streaks(asset_trades)

        # Average trade duration
        durations = [(t.exit_time - t.entry_time).total_seconds() / 3600 for t in asset_trades]
        metrics.avg_trade_duration_hours = sum(durations) / len(durations)

        return metrics

    def _calculate_streaks(self, trades: List[Trade]) -> tuple:
        """Calculate max consecutive wins, losses, and current streak."""
        if not trades:
            return 0, 0, 0

        max_wins = 0
        max_losses = 0
        current_wins = 0
        current_losses = 0
        current_streak = 0

        # Sort by exit time
        sorted_trades = sorted(trades, key=lambda t: t.exit_time)

        for trade in sorted_trades:
            if trade.pnl_pct > 0:
                current_wins += 1
                current_losses = 0
                max_wins = max(max_wins, current_wins)
                current_streak = current_wins
            else:
                current_losses += 1
                current_wins = 0
                max_losses = max(max_losses, current_losses)
                current_streak = -current_losses

        return max_wins, max_losses, current_streak

    def get_overall_metrics(self) -> Dict:
        """Get overall portfolio metrics with professional edge analysis."""
        empty_metrics = {
            "total_trades": 0, "win_rate": 0, "sharpe_ratio": 0, "max_drawdown_pct": 0,
            "total_pnl_pct": 0, "avg_trade_duration_hours": 0, "expected_value": 0,
            "profit_factor": 0, "risk_reward_ratio": 0, "edge_quality": "INSUFFICIENT_DATA",
            "max_consecutive_wins": 0, "max_consecutive_losses": 0, "current_streak": 0,
            "calmar_ratio": 0, "recovery_factor": 0
        }
        if not self.trades:
            return empty_metrics

        wins = [t for t in self.trades if t.pnl_pct > 0]
        losses = [t for t in self.trades if t.pnl_pct <= 0]

        total_pnl_pct = sum(t.pnl_pct for t in self.trades)
        gross_profit = sum(t.pnl_pct for t in wins) if wins else 0
        gross_loss = abs(sum(t.pnl_pct for t in losses)) if losses else 0
        avg_win = gross_profit / len(wins) if wins else 0
        avg_loss = -gross_loss / len(losses) if losses else 0

        # === PROFESSIONAL EDGE METRICS ===
        win_rate = (len(wins) / len(self.trades) * 100) if self.trades else 0
        win_rate_dec = len(wins) / len(self.trades) if self.trades else 0
        loss_rate_dec = len(losses) / len(self.trades) if self.trades else 0

        # Expected Value per trade (the core metric)
        expected_value = (win_rate_dec * avg_win) + (loss_rate_dec * avg_loss)

        # Profit Factor: Gross Profit / Gross Loss (>1.5 good, >2.0 excellent)
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else (10 if gross_profit > 0 else 0)

        # Risk Reward Ratio: Avg Win / Avg Loss (for scalping, >1.0 is acceptable)
        risk_reward = abs(avg_win / avg_loss) if avg_loss != 0 else (10 if avg_win > 0 else 0)

        # Sharpe ratio (annualized)
        returns = [t.pnl_pct for t in self.trades]
        if len(returns) > 1:
            mean_return = sum(returns) / len(returns)
            variance = sum((r - mean_return) ** 2 for r in returns) / len(returns)
            std_dev = math.sqrt(variance) if variance > 0 else 0.001
            sharpe = (mean_return / std_dev) * math.sqrt(252)
        else:
            sharpe = 0

        # Max drawdown
        max_drawdown = self._calculate_max_drawdown()

        # Calmar Ratio: Annual Return / Max Drawdown (>1.0 good, >2.0 excellent)
        annual_return = total_pnl_pct * (252 / max(len(self.trades), 1))  # Rough annualization
        calmar = annual_return / max_drawdown if max_drawdown > 0 else 0

        # Recovery Factor: Net Profit / Max Drawdown (>2.0 good)
        recovery = total_pnl_pct / max_drawdown if max_drawdown > 0 else 0

        # Consecutive wins/losses
        max_wins, max_losses, current_streak = self._calculate_streaks(self.trades)

        # Average trade duration
        durations = [(t.exit_time - t.entry_time).total_seconds() / 3600 for t in self.trades]
        avg_duration = sum(durations) / len(durations)

        # Edge quality assessment
        if len(self.trades) < 10:
            edge_quality = "INSUFFICIENT_DATA"
        elif expected_value > 0.5 and profit_factor > 2.0 and win_rate > 55:
            edge_quality = "EXCELLENT"
        elif expected_value > 0.2 and profit_factor > 1.5 and win_rate > 50:
            edge_quality = "GOOD"
        elif expected_value > 0 and profit_factor > 1.0:
            edge_quality = "MARGINAL"
        else:
            edge_quality = "NO_EDGE"

        return {
            "total_trades": len(self.trades),
            "wins": len(wins),
            "losses": len(losses),
            "win_rate": round(win_rate, 1),
            "avg_win_pct": round(avg_win, 2),
            "avg_loss_pct": round(avg_loss, 2),
            "total_pnl_pct": round(total_pnl_pct, 2),
            # Professional metrics
            "expected_value": round(expected_value, 3),
            "profit_factor": round(min(profit_factor, 99), 2),
            "risk_reward_ratio": round(min(risk_reward, 99), 2),
            "sharpe_ratio": round(sharpe, 2),
            "calmar_ratio": round(calmar, 2),
            "recovery_factor": round(recovery, 2),
            "max_drawdown_pct": round(max_drawdown, 2),
            "max_consecutive_wins": max_wins,
            "max_consecutive_losses": max_losses,
            "current_streak": current_streak,
            "edge_quality": edge_quality,
            "avg_trade_duration_hours": round(avg_duration, 2)
        }

    def _calculate_max_drawdown(self) -> float:
        """Calculate maximum drawdown from equity curve."""
        if not self.equity_curve:
            return 0.0

        peak = self.equity_curve[0]["equity"]
        max_dd = 0.0

        for point in self.equity_curve:
            equity = point["equity"]
            peak = max(peak, equity)
            drawdown = ((peak - equity) / peak) * 100 if peak > 0 else 0
            max_dd = max(max_dd, drawdown)

        return round(max_dd, 2)

    def get_summary_report(self) -> str:
        """Generate a human-readable performance summary with professional metrics."""
        o = self.get_overall_metrics()

        # Edge quality indicator
        eq = o['edge_quality']
        edge_emoji = {"EXCELLENT": "🟢", "GOOD": "🟡", "MARGINAL": "🟠", "NO_EDGE": "🔴", "INSUFFICIENT_DATA": "⚪"}.get(eq, "⚪")

        report = [
            "\n" + "=" * 70,
            f"📊 PERFORMANCE REPORT | EDGE: {edge_emoji} {eq}",
            "=" * 70,
            "",
            "📈 TRADE STATISTICS",
            f"  Trades: {o['total_trades']} | Wins: {o['wins']} | Losses: {o['losses']}",
            f"  Win Rate: {o['win_rate']:.1f}% | Avg Duration: {o['avg_trade_duration_hours']:.1f}h",
            f"  Streaks: {o['max_consecutive_wins']} max wins | {o['max_consecutive_losses']} max losses | Current: {o['current_streak']:+d}",
            "",
            "💰 P&L ANALYSIS",
            f"  Total P&L: {o['total_pnl_pct']:+.2f}%",
            f"  Avg Win: +{o['avg_win_pct']:.2f}% | Avg Loss: {o['avg_loss_pct']:.2f}%",
            "",
            "🎯 EDGE METRICS (Professional)",
            f"  Expected Value: {o['expected_value']:+.3f}% per trade {'✓' if o['expected_value'] > 0 else '✗'}",
            f"  Profit Factor: {o['profit_factor']:.2f} {'(>1.5 good, >2.0 excellent)' if o['profit_factor'] < 1.5 else '✓'}",
            f"  Risk/Reward: {o['risk_reward_ratio']:.2f} {'(>1.0 acceptable for scalping)' if o['risk_reward_ratio'] < 1.0 else '✓'}",
            "",
            "📉 RISK METRICS",
            f"  Sharpe Ratio: {o['sharpe_ratio']:.2f} {'(>1.0 good, >2.0 excellent)' if o['sharpe_ratio'] < 1.0 else '✓'}",
            f"  Calmar Ratio: {o['calmar_ratio']:.2f} {'(>1.0 good)' if o['calmar_ratio'] < 1.0 else '✓'}",
            f"  Recovery Factor: {o['recovery_factor']:.2f}",
            f"  Max Drawdown: {o['max_drawdown_pct']:.2f}%",
            ""
        ]

        # Per-asset breakdown
        symbols = set(t.symbol for t in self.trades)
        if symbols:
            report.append("📋 PER-ASSET BREAKDOWN")
            for symbol in symbols:
                m = self.get_asset_metrics(symbol)
                report.append(f"  {symbol}: {m.total_trades} trades | WR: {m.win_rate:.0f}% | EV: {m.expected_value:+.2f}% | PF: {m.profit_factor:.1f} | P&L: {m.total_pnl_pct:+.2f}%")
            report.append("")

        report.append("=" * 70)
        return "\n".join(report)

    def get_edge_summary(self) -> str:
        """Get a compact edge summary for logging."""
        o = self.get_overall_metrics()
        if o['total_trades'] < 3:
            return "Edge: Insufficient data"
        return f"Edge: {o['edge_quality']} | EV:{o['expected_value']:+.2f}% | PF:{o['profit_factor']:.1f} | WR:{o['win_rate']:.0f}% | {o['total_trades']} trades"

    def get_trades_with_conditions(self) -> List[Trade]:
        """Get trades that have entry conditions recorded (for learning)."""
        return [t for t in self.trades if t.entry_conditions is not None]


class TradeAnalyzer:
    """
    Analyzes historical trades to identify patterns and learn optimal thresholds.

    KEY INSIGHT: We don't need ML - simple statistical analysis of what worked.
    """

    def __init__(self, perf_tracker: PerformanceTracker):
        self.perf_tracker = perf_tracker
        self.min_trades_for_learning = 10  # Need at least this many trades to learn
        self._learned_thresholds: Dict = {}
        self._pattern_insights: Dict = {}

    def analyze_patterns(self) -> Dict[str, Any]:
        """
        Analyze all trades with entry conditions to find winning patterns.

        Returns dict with:
        - optimal_rsi_ranges: RSI ranges that led to wins
        - optimal_bb_positions: BB positions that worked
        - best_hours: Hours of day with best win rate
        - losing_patterns: Patterns to avoid
        """
        trades = self.perf_tracker.get_trades_with_conditions()

        if len(trades) < self.min_trades_for_learning:
            return {"status": "insufficient_data", "trades_analyzed": len(trades)}

        # Separate wins and losses
        wins = [t for t in trades if t.pnl_pct > 0]
        losses = [t for t in trades if t.pnl_pct <= 0]

        analysis = {
            "status": "analyzed",
            "trades_analyzed": len(trades),
            "wins": len(wins),
            "losses": len(losses),
            "win_rate": len(wins) / len(trades) * 100 if trades else 0,
        }

        # === RSI ANALYSIS ===
        analysis["rsi_analysis"] = self._analyze_rsi_patterns(wins, losses)

        # === BOLLINGER BAND ANALYSIS ===
        analysis["bb_analysis"] = self._analyze_bb_patterns(wins, losses)

        # === TREND SCORE ANALYSIS ===
        analysis["trend_analysis"] = self._analyze_trend_patterns(wins, losses)

        # === TIME OF DAY ANALYSIS ===
        analysis["time_analysis"] = self._analyze_time_patterns(wins, losses)

        # === SIDE ANALYSIS (long vs short) ===
        analysis["side_analysis"] = self._analyze_side_patterns(trades)

        # === NEW: REGIME ANALYSIS ===
        analysis["regime_analysis"] = self._analyze_regime_patterns(trades)

        # === NEW: STRATEGY ANALYSIS ===
        analysis["strategy_analysis"] = self._analyze_strategy_patterns(trades)

        # === NEW: CONFIDENCE CALIBRATION ===
        analysis["confidence_analysis"] = self._analyze_confidence_calibration(trades)

        # === NEW: SL/TP DISTANCE ANALYSIS ===
        analysis["sltp_analysis"] = self._analyze_sltp_patterns(wins, losses)

        # === GENERATE RECOMMENDATIONS ===
        analysis["recommendations"] = self._generate_recommendations(analysis)

        self._pattern_insights = analysis
        return analysis

    def _analyze_rsi_patterns(self, wins: List[Trade], losses: List[Trade]) -> Dict:
        """Analyze which RSI values led to wins vs losses."""
        # Define RSI buckets
        buckets = {
            "oversold_20_30": (20, 30),
            "low_30_40": (30, 40),
            "neutral_40_60": (40, 60),
            "high_60_70": (60, 70),
            "overbought_70_80": (70, 80),
        }

        results = {}
        for bucket_name, (low, high) in buckets.items():
            wins_in_bucket = [t for t in wins if t.entry_conditions and low <= t.entry_conditions.rsi < high]
            losses_in_bucket = [t for t in losses if t.entry_conditions and low <= t.entry_conditions.rsi < high]
            total = len(wins_in_bucket) + len(losses_in_bucket)

            if total >= 3:  # Need at least 3 trades in bucket
                results[bucket_name] = {
                    "wins": len(wins_in_bucket),
                    "losses": len(losses_in_bucket),
                    "total": total,
                    "win_rate": len(wins_in_bucket) / total * 100,
                    "avg_pnl": (sum(t.pnl_pct for t in wins_in_bucket + losses_in_bucket) / total) if total > 0 else 0
                }

        # Find best and worst RSI ranges
        if results:
            best_bucket = max(results.items(), key=lambda x: x[1]["win_rate"])
            worst_bucket = min(results.items(), key=lambda x: x[1]["win_rate"])
            return {
                "buckets": results,
                "best_range": best_bucket[0],
                "best_win_rate": best_bucket[1]["win_rate"],
                "worst_range": worst_bucket[0],
                "worst_win_rate": worst_bucket[1]["win_rate"],
            }
        return {"buckets": {}, "best_range": None, "worst_range": None}

    def _analyze_bb_patterns(self, wins: List[Trade], losses: List[Trade]) -> Dict:
        """Analyze which Bollinger Band positions led to wins vs losses."""
        buckets = {
            "lower_band_0_20": (0.0, 0.2),
            "lower_half_20_40": (0.2, 0.4),
            "middle_40_60": (0.4, 0.6),
            "upper_half_60_80": (0.6, 0.8),
            "upper_band_80_100": (0.8, 1.0),
        }

        results = {}
        for bucket_name, (low, high) in buckets.items():
            wins_in_bucket = [t for t in wins if t.entry_conditions and low <= t.entry_conditions.bb_position < high]
            losses_in_bucket = [t for t in losses if t.entry_conditions and low <= t.entry_conditions.bb_position < high]
            total = len(wins_in_bucket) + len(losses_in_bucket)

            if total >= 3:
                results[bucket_name] = {
                    "wins": len(wins_in_bucket),
                    "losses": len(losses_in_bucket),
                    "total": total,
                    "win_rate": len(wins_in_bucket) / total * 100,
                }

        if results:
            best_bucket = max(results.items(), key=lambda x: x[1]["win_rate"])
            worst_bucket = min(results.items(), key=lambda x: x[1]["win_rate"])
            return {
                "buckets": results,
                "best_position": best_bucket[0],
                "best_win_rate": best_bucket[1]["win_rate"],
                "worst_position": worst_bucket[0],
                "worst_win_rate": worst_bucket[1]["win_rate"],
            }
        return {"buckets": {}, "best_position": None, "worst_position": None}

    def _analyze_trend_patterns(self, wins: List[Trade], losses: List[Trade]) -> Dict:
        """Analyze which trend scores led to wins vs losses."""
        buckets = {
            "weak_50_60": (50, 60),
            "moderate_60_70": (60, 70),
            "strong_70_80": (70, 80),
            "very_strong_80_100": (80, 100),
        }

        results = {}
        for bucket_name, (low, high) in buckets.items():
            wins_in_bucket = [t for t in wins if t.entry_conditions and low <= t.entry_conditions.trend_5m_score < high]
            losses_in_bucket = [t for t in losses if t.entry_conditions and low <= t.entry_conditions.trend_5m_score < high]
            total = len(wins_in_bucket) + len(losses_in_bucket)

            if total >= 3:
                results[bucket_name] = {
                    "wins": len(wins_in_bucket),
                    "losses": len(losses_in_bucket),
                    "total": total,
                    "win_rate": len(wins_in_bucket) / total * 100,
                }

        if results:
            best_bucket = max(results.items(), key=lambda x: x[1]["win_rate"])
            return {
                "buckets": results,
                "best_score_range": best_bucket[0],
                "best_win_rate": best_bucket[1]["win_rate"],
            }
        return {"buckets": {}, "best_score_range": None}

    def _analyze_time_patterns(self, wins: List[Trade], losses: List[Trade]) -> Dict:
        """Analyze which hours of day led to wins vs losses."""
        # Group into time periods (UTC)
        periods = {
            "asia_0_8": range(0, 8),
            "europe_8_16": range(8, 16),
            "us_16_24": range(16, 24),
        }

        results = {}
        for period_name, hours in periods.items():
            wins_in_period = [t for t in wins if t.entry_conditions and t.entry_conditions.hour_of_day in hours]
            losses_in_period = [t for t in losses if t.entry_conditions and t.entry_conditions.hour_of_day in hours]
            total = len(wins_in_period) + len(losses_in_period)

            if total >= 3:
                results[period_name] = {
                    "wins": len(wins_in_period),
                    "losses": len(losses_in_period),
                    "total": total,
                    "win_rate": len(wins_in_period) / total * 100,
                }

        if results:
            best_period = max(results.items(), key=lambda x: x[1]["win_rate"])
            worst_period = min(results.items(), key=lambda x: x[1]["win_rate"])
            return {
                "periods": results,
                "best_period": best_period[0],
                "best_win_rate": best_period[1]["win_rate"],
                "worst_period": worst_period[0],
                "worst_win_rate": worst_period[1]["win_rate"],
            }
        return {"periods": {}, "best_period": None, "worst_period": None}

    def _analyze_side_patterns(self, trades: List[Trade]) -> Dict:
        """Analyze long vs short performance."""
        longs = [t for t in trades if t.side == "long"]
        shorts = [t for t in trades if t.side == "short"]

        long_wins = len([t for t in longs if t.pnl_pct > 0])
        short_wins = len([t for t in shorts if t.pnl_pct > 0])

        return {
            "long": {
                "total": len(longs),
                "wins": long_wins,
                "win_rate": (long_wins / len(longs) * 100) if longs else 0,
                "avg_pnl": sum(t.pnl_pct for t in longs) / len(longs) if longs else 0,
            },
            "short": {
                "total": len(shorts),
                "wins": short_wins,
                "win_rate": (short_wins / len(shorts) * 100) if shorts else 0,
                "avg_pnl": sum(t.pnl_pct for t in shorts) / len(shorts) if shorts else 0,
            }
        }

    def _analyze_regime_patterns(self, trades: List[Trade]) -> Dict:
        """Analyze performance by market regime."""
        regimes = {}
        for t in trades:
            if not t.entry_conditions:
                continue
            regime = t.entry_conditions.adaptive_regime or "unknown"
            if regime not in regimes:
                regimes[regime] = {"wins": 0, "losses": 0, "total_pnl": 0.0}

            if t.pnl_pct > 0:
                regimes[regime]["wins"] += 1
            else:
                regimes[regime]["losses"] += 1
            regimes[regime]["total_pnl"] += t.pnl_pct

        # Calculate win rates and find best/worst
        results = {}
        best_regime = None
        worst_regime = None
        best_wr = 0
        worst_wr = 100

        for regime, data in regimes.items():
            total = data["wins"] + data["losses"]
            if total >= 3:  # Need at least 3 trades
                wr = data["wins"] / total * 100
                results[regime] = {
                    "total": total,
                    "wins": data["wins"],
                    "losses": data["losses"],
                    "win_rate": wr,
                    "avg_pnl": data["total_pnl"] / total,
                }
                if wr > best_wr:
                    best_wr = wr
                    best_regime = regime
                if wr < worst_wr:
                    worst_wr = wr
                    worst_regime = regime

        return {
            "regimes": results,
            "best_regime": best_regime,
            "best_win_rate": best_wr,
            "worst_regime": worst_regime,
            "worst_win_rate": worst_wr,
        }

    def _analyze_strategy_patterns(self, trades: List[Trade]) -> Dict:
        """Analyze performance by strategy type (swing/micro/macro/snipe)."""
        strategies = {}
        for t in trades:
            if not t.entry_conditions:
                continue
            strategy = t.entry_conditions.strategy_type or "unknown"
            if strategy not in strategies:
                strategies[strategy] = {"wins": 0, "losses": 0, "total_pnl": 0.0}

            if t.pnl_pct > 0:
                strategies[strategy]["wins"] += 1
            else:
                strategies[strategy]["losses"] += 1
            strategies[strategy]["total_pnl"] += t.pnl_pct

        results = {}
        best_strategy = None
        best_wr = 0

        for strategy, data in strategies.items():
            total = data["wins"] + data["losses"]
            if total >= 2:  # Lower threshold for strategies
                wr = data["wins"] / total * 100
                results[strategy] = {
                    "total": total,
                    "wins": data["wins"],
                    "win_rate": wr,
                    "avg_pnl": data["total_pnl"] / total,
                }
                if wr > best_wr:
                    best_wr = wr
                    best_strategy = strategy

        return {
            "strategies": results,
            "best_strategy": best_strategy,
            "best_win_rate": best_wr,
        }

    def _analyze_confidence_calibration(self, trades: List[Trade]) -> Dict:
        """Analyze if Claude's confidence correlates with actual win rate."""
        # Bucket by confidence level
        confidence_buckets = {
            "low_50_60": (0.5, 0.6),
            "medium_60_70": (0.6, 0.7),
            "high_70_80": (0.7, 0.8),
            "very_high_80_90": (0.8, 0.9),
            "extreme_90_100": (0.9, 1.0),
        }

        results = {}
        for bucket_name, (low, high) in confidence_buckets.items():
            bucket_trades = [t for t in trades
                          if t.entry_conditions and low <= t.entry_conditions.signal_confidence < high]
            if len(bucket_trades) >= 2:
                wins = len([t for t in bucket_trades if t.pnl_pct > 0])
                expected_wr = (low + high) / 2 * 100  # Expected win rate based on confidence
                actual_wr = wins / len(bucket_trades) * 100
                results[bucket_name] = {
                    "trades": len(bucket_trades),
                    "wins": wins,
                    "expected_win_rate": expected_wr,
                    "actual_win_rate": actual_wr,
                    "calibration_error": actual_wr - expected_wr,  # + = overperforming, - = overconfident
                }

        # Calculate overall calibration
        total_calibration_error = 0
        total_buckets = 0
        for data in results.values():
            total_calibration_error += abs(data["calibration_error"])
            total_buckets += 1

        avg_error = total_calibration_error / total_buckets if total_buckets > 0 else 0

        return {
            "buckets": results,
            "avg_calibration_error": avg_error,
            "is_well_calibrated": avg_error < 15,  # <15% error is good
            "is_overconfident": any(d["calibration_error"] < -20 for d in results.values()),
        }

    def _analyze_sltp_patterns(self, wins: List[Trade], losses: List[Trade]) -> Dict:
        """Analyze which SL/TP distances led to wins vs losses."""
        # Analyze SL distance
        sl_distances = {"wins": [], "losses": []}
        tp_distances = {"wins": [], "losses": []}
        rr_ratios = {"wins": [], "losses": []}

        for t in wins:
            if t.entry_conditions and t.entry_conditions.sl_distance_pct > 0:
                sl_distances["wins"].append(t.entry_conditions.sl_distance_pct)
                tp_distances["wins"].append(t.entry_conditions.tp_distance_pct)
                if t.entry_conditions.risk_reward_ratio > 0:
                    rr_ratios["wins"].append(t.entry_conditions.risk_reward_ratio)

        for t in losses:
            if t.entry_conditions and t.entry_conditions.sl_distance_pct > 0:
                sl_distances["losses"].append(t.entry_conditions.sl_distance_pct)
                tp_distances["losses"].append(t.entry_conditions.tp_distance_pct)
                if t.entry_conditions.risk_reward_ratio > 0:
                    rr_ratios["losses"].append(t.entry_conditions.risk_reward_ratio)

        def calc_stats(values: List[float]) -> Dict:
            if not values:
                return {"avg": 0, "min": 0, "max": 0}
            return {
                "avg": sum(values) / len(values),
                "min": min(values),
                "max": max(values),
            }

        # Find optimal ranges
        optimal_sl = None
        optimal_tp = None
        optimal_rr = None

        if sl_distances["wins"]:
            avg_win_sl = sum(sl_distances["wins"]) / len(sl_distances["wins"])
            avg_loss_sl = sum(sl_distances["losses"]) / len(sl_distances["losses"]) if sl_distances["losses"] else avg_win_sl
            # If winning trades have different SL than losing trades, note the pattern
            if abs(avg_win_sl - avg_loss_sl) > 0.5:
                optimal_sl = avg_win_sl

        if rr_ratios["wins"]:
            avg_win_rr = sum(rr_ratios["wins"]) / len(rr_ratios["wins"])
            optimal_rr = avg_win_rr

        return {
            "sl_distance": {
                "wins": calc_stats(sl_distances["wins"]),
                "losses": calc_stats(sl_distances["losses"]),
                "optimal": optimal_sl,
            },
            "tp_distance": {
                "wins": calc_stats(tp_distances["wins"]),
                "losses": calc_stats(tp_distances["losses"]),
            },
            "risk_reward": {
                "wins": calc_stats(rr_ratios["wins"]),
                "losses": calc_stats(rr_ratios["losses"]),
                "optimal": optimal_rr,
            },
        }

    def _generate_recommendations(self, analysis: Dict) -> List[str]:
        """Generate actionable recommendations based on analysis."""
        recommendations = []

        # RSI recommendations
        rsi = analysis.get("rsi_analysis", {})
        if rsi.get("worst_win_rate", 100) < 40 and rsi.get("worst_range"):
            recommendations.append(f"AVOID trades when RSI in {rsi['worst_range']} (win rate: {rsi['worst_win_rate']:.0f}%)")
        if rsi.get("best_win_rate", 0) > 60 and rsi.get("best_range"):
            recommendations.append(f"PREFER trades when RSI in {rsi['best_range']} (win rate: {rsi['best_win_rate']:.0f}%)")

        # BB recommendations
        bb = analysis.get("bb_analysis", {})
        if bb.get("worst_win_rate", 100) < 40 and bb.get("worst_position"):
            recommendations.append(f"AVOID trades when BB position in {bb['worst_position']} (win rate: {bb['worst_win_rate']:.0f}%)")

        # Time recommendations
        time = analysis.get("time_analysis", {})
        if time.get("worst_win_rate", 100) < 40 and time.get("worst_period"):
            recommendations.append(f"AVOID trading during {time['worst_period']} (win rate: {time['worst_win_rate']:.0f}%)")
        if time.get("best_win_rate", 0) > 60 and time.get("best_period"):
            recommendations.append(f"PREFER trading during {time['best_period']} (win rate: {time['best_win_rate']:.0f}%)")

        # Side recommendations
        side = analysis.get("side_analysis", {})
        if side.get("long", {}).get("win_rate", 50) > side.get("short", {}).get("win_rate", 50) + 15:
            recommendations.append(f"LONG trades performing better ({side['long']['win_rate']:.0f}% vs {side['short']['win_rate']:.0f}%)")
        elif side.get("short", {}).get("win_rate", 50) > side.get("long", {}).get("win_rate", 50) + 15:
            recommendations.append(f"SHORT trades performing better ({side['short']['win_rate']:.0f}% vs {side['long']['win_rate']:.0f}%)")

        # NEW: Regime recommendations
        regime = analysis.get("regime_analysis", {})
        if regime.get("best_regime") and regime.get("best_win_rate", 0) > 60:
            recommendations.append(f"BEST REGIME: {regime['best_regime']} ({regime['best_win_rate']:.0f}% win rate)")
        if regime.get("worst_regime") and regime.get("worst_win_rate", 100) < 40:
            recommendations.append(f"AVOID REGIME: {regime['worst_regime']} ({regime['worst_win_rate']:.0f}% win rate)")

        # NEW: Strategy recommendations
        strategy = analysis.get("strategy_analysis", {})
        if strategy.get("best_strategy") and strategy.get("best_win_rate", 0) > 55:
            recommendations.append(f"BEST STRATEGY: {strategy['best_strategy']} ({strategy['best_win_rate']:.0f}% win rate)")

        # NEW: Confidence calibration recommendations
        confidence = analysis.get("confidence_analysis", {})
        if confidence.get("is_overconfident"):
            recommendations.append("⚠️ OVERCONFIDENT: High-confidence trades underperforming expectations")
        if confidence.get("is_well_calibrated"):
            recommendations.append("✅ WELL CALIBRATED: Confidence correlates with actual win rate")

        # NEW: SL/TP recommendations
        sltp = analysis.get("sltp_analysis", {})
        if sltp.get("risk_reward", {}).get("optimal"):
            optimal_rr = sltp["risk_reward"]["optimal"]
            recommendations.append(f"OPTIMAL R:R RATIO: {optimal_rr:.1f}:1 (based on winning trades)")
        if sltp.get("sl_distance", {}).get("optimal"):
            optimal_sl = sltp["sl_distance"]["optimal"]
            recommendations.append(f"OPTIMAL SL DISTANCE: {optimal_sl:.2f}% from entry")

        return recommendations

    def get_learned_thresholds(self) -> Dict[str, Any]:
        """
        Get dynamically adjusted thresholds based on what historically worked.

        Returns thresholds that should be used for filtering trades.
        """
        if not self._pattern_insights:
            self.analyze_patterns()

        analysis = self._pattern_insights
        if analysis.get("status") != "analyzed":
            # Not enough data - return default thresholds
            return {
                "status": "using_defaults",
                "rsi_short_max": 35,  # Don't short below this RSI
                "rsi_long_min": 65,   # Don't long above this RSI
                "bb_short_min": 0.15, # Don't short below this BB position
                "bb_long_max": 0.85,  # Don't long above this BB position
                "min_trend_score": 60,
                "avoid_hours": [],
                "prefer_side": None,
            }

        thresholds = {
            "status": "learned",
            "trades_analyzed": analysis["trades_analyzed"],
        }

        # === RSI THRESHOLDS ===
        rsi = analysis.get("rsi_analysis", {})
        # If shorting when RSI < 30 loses, raise the threshold
        if "oversold_20_30" in rsi.get("buckets", {}) and rsi["buckets"]["oversold_20_30"]["win_rate"] < 40:
            thresholds["rsi_short_max"] = 40  # More conservative
        elif "low_30_40" in rsi.get("buckets", {}) and rsi["buckets"]["low_30_40"]["win_rate"] < 40:
            thresholds["rsi_short_max"] = 45
        else:
            thresholds["rsi_short_max"] = 35  # Default

        # If longing when RSI > 70 loses, lower the threshold
        if "overbought_70_80" in rsi.get("buckets", {}) and rsi["buckets"]["overbought_70_80"]["win_rate"] < 40:
            thresholds["rsi_long_min"] = 60  # More conservative
        elif "high_60_70" in rsi.get("buckets", {}) and rsi["buckets"]["high_60_70"]["win_rate"] < 40:
            thresholds["rsi_long_min"] = 55
        else:
            thresholds["rsi_long_min"] = 65  # Default

        # === BB THRESHOLDS ===
        bb = analysis.get("bb_analysis", {})
        # If shorting at lower band loses
        if "lower_band_0_20" in bb.get("buckets", {}) and bb["buckets"]["lower_band_0_20"]["win_rate"] < 40:
            thresholds["bb_short_min"] = 0.25
        else:
            thresholds["bb_short_min"] = 0.15

        # If longing at upper band loses
        if "upper_band_80_100" in bb.get("buckets", {}) and bb["buckets"]["upper_band_80_100"]["win_rate"] < 40:
            thresholds["bb_long_max"] = 0.75
        else:
            thresholds["bb_long_max"] = 0.85

        # === TREND SCORE THRESHOLD ===
        trend = analysis.get("trend_analysis", {})
        best_range = trend.get("best_score_range") or ""
        if "very_strong" in best_range:
            thresholds["min_trend_score"] = 75  # Require stronger trends
        elif "strong" in best_range:
            thresholds["min_trend_score"] = 65
        else:
            thresholds["min_trend_score"] = 60

        # === TIME AVOIDANCE ===
        time = analysis.get("time_analysis", {})
        avoid_hours = []
        if time.get("worst_win_rate", 100) < 35:
            worst = time.get("worst_period") or ""
            if "asia" in worst:
                avoid_hours = list(range(0, 8))
            elif "europe" in worst:
                avoid_hours = list(range(8, 16))
            elif "us" in worst:
                avoid_hours = list(range(16, 24))
        thresholds["avoid_hours"] = avoid_hours

        # === SIDE PREFERENCE ===
        side = analysis.get("side_analysis", {})
        long_wr = side.get("long", {}).get("win_rate", 50)
        short_wr = side.get("short", {}).get("win_rate", 50)
        if long_wr > short_wr + 20:
            thresholds["prefer_side"] = "long"
        elif short_wr > long_wr + 20:
            thresholds["prefer_side"] = "short"
        else:
            thresholds["prefer_side"] = None

        # === NEW: REGIME PREFERENCES ===
        regime = analysis.get("regime_analysis", {})
        if regime.get("worst_regime") and regime.get("worst_win_rate", 100) < 35:
            thresholds["avoid_regime"] = regime["worst_regime"]
        else:
            thresholds["avoid_regime"] = None

        if regime.get("best_regime") and regime.get("best_win_rate", 0) > 65:
            thresholds["prefer_regime"] = regime["best_regime"]
        else:
            thresholds["prefer_regime"] = None

        # === NEW: STRATEGY PREFERENCES ===
        strategy = analysis.get("strategy_analysis", {})
        thresholds["best_strategy"] = strategy.get("best_strategy")

        # === NEW: CONFIDENCE CALIBRATION ===
        confidence = analysis.get("confidence_analysis", {})
        thresholds["is_overconfident"] = confidence.get("is_overconfident", False)
        thresholds["min_confidence_for_high_size"] = 0.75 if not confidence.get("is_overconfident") else 0.85

        # === NEW: SL/TP OPTIMAL VALUES ===
        sltp = analysis.get("sltp_analysis", {})
        thresholds["optimal_rr_ratio"] = sltp.get("risk_reward", {}).get("optimal")
        thresholds["optimal_sl_distance"] = sltp.get("sl_distance", {}).get("optimal")

        self._learned_thresholds = thresholds
        return thresholds

    def should_take_trade(self, side: str, entry_conditions: EntryConditions) -> tuple:
        """
        Use learned patterns to decide if a trade should be taken.

        Returns (should_trade: bool, reason: str)
        """
        thresholds = self.get_learned_thresholds()

        if thresholds.get("status") == "using_defaults":
            return True, "Using default thresholds (insufficient historical data)"

        reasons_to_skip = []

        # Check RSI
        if side == "short" and entry_conditions.rsi < thresholds.get("rsi_short_max", 35):
            reasons_to_skip.append(f"RSI {entry_conditions.rsi:.0f} < {thresholds['rsi_short_max']} (learned: shorts fail when RSI low)")
        if side == "long" and entry_conditions.rsi > thresholds.get("rsi_long_min", 65):
            reasons_to_skip.append(f"RSI {entry_conditions.rsi:.0f} > {thresholds['rsi_long_min']} (learned: longs fail when RSI high)")

        # Check BB position
        if side == "short" and entry_conditions.bb_position < thresholds.get("bb_short_min", 0.15):
            reasons_to_skip.append(f"BB position {entry_conditions.bb_position:.0%} < {thresholds['bb_short_min']:.0%} (learned: shorts fail at lower band)")
        if side == "long" and entry_conditions.bb_position > thresholds.get("bb_long_max", 0.85):
            reasons_to_skip.append(f"BB position {entry_conditions.bb_position:.0%} > {thresholds['bb_long_max']:.0%} (learned: longs fail at upper band)")

        # Check time of day
        if entry_conditions.hour_of_day in thresholds.get("avoid_hours", []):
            reasons_to_skip.append(f"Hour {entry_conditions.hour_of_day} is in avoid list (learned: poor performance this time)")

        # Check side preference
        prefer_side = thresholds.get("prefer_side")
        if prefer_side and side != prefer_side:
            reasons_to_skip.append(f"Learned preference is {prefer_side}, not {side}")

        # NEW: Check regime
        avoid_regime = thresholds.get("avoid_regime")
        if avoid_regime and entry_conditions.adaptive_regime == avoid_regime:
            reasons_to_skip.append(f"Current regime '{avoid_regime}' has poor historical performance")

        if reasons_to_skip:
            return False, "; ".join(reasons_to_skip)

        return True, "Trade passes all learned filters"

    def get_learning_summary(self) -> str:
        """Get a human-readable summary of what the system has learned."""
        if not self._pattern_insights:
            self.analyze_patterns()

        analysis = self._pattern_insights
        if analysis.get("status") != "analyzed":
            return "📚 Learning: Insufficient data (need 10+ trades with conditions)"

        thresholds = self.get_learned_thresholds()
        recommendations = analysis.get("recommendations", [])

        lines = [
            "\n" + "=" * 70,
            "🧠 COMPREHENSIVE LEARNING SUMMARY",
            "=" * 70,
            f"Trades Analyzed: {analysis['trades_analyzed']} | Win Rate: {analysis['win_rate']:.1f}%",
            "",
            "📊 LEARNED THRESHOLDS:",
            f"  • RSI: Don't SHORT below {thresholds.get('rsi_short_max', 35)} | Don't LONG above {thresholds.get('rsi_long_min', 65)}",
            f"  • BB: Don't SHORT below {thresholds.get('bb_short_min', 0.15):.0%} | Don't LONG above {thresholds.get('bb_long_max', 0.85):.0%}",
            f"  • Min Trend Score: {thresholds.get('min_trend_score', 60)}",
            f"  • Avoid Hours (UTC): {thresholds.get('avoid_hours', []) or 'None'}",
            f"  • Side Preference: {thresholds.get('prefer_side') or 'None'}",
            "",
            "🌍 REGIME PERFORMANCE:",
        ]

        # Add regime analysis
        regime = analysis.get("regime_analysis", {})
        for regime_name, data in regime.get("regimes", {}).items():
            lines.append(f"  • {regime_name}: {data['win_rate']:.0f}% WR ({data['total']} trades)")
        if thresholds.get("avoid_regime"):
            lines.append(f"  ⚠️ AVOID: {thresholds['avoid_regime']}")

        lines.append("")
        lines.append("📈 STRATEGY PERFORMANCE:")

        # Add strategy analysis
        strategy = analysis.get("strategy_analysis", {})
        for strat_name, data in strategy.get("strategies", {}).items():
            lines.append(f"  • {strat_name}: {data['win_rate']:.0f}% WR | Avg P&L: {data['avg_pnl']:+.2f}%")

        lines.append("")
        lines.append("🎯 CONFIDENCE CALIBRATION:")

        # Add confidence calibration
        confidence = analysis.get("confidence_analysis", {})
        if confidence.get("is_well_calibrated"):
            lines.append("  ✅ Model is well-calibrated")
        elif confidence.get("is_overconfident"):
            lines.append("  ⚠️ Model is OVERCONFIDENT - high-confidence trades underperforming")
        for bucket, data in confidence.get("buckets", {}).items():
            lines.append(f"  • {bucket}: Expected {data['expected_win_rate']:.0f}% → Actual {data['actual_win_rate']:.0f}%")

        lines.append("")
        lines.append("📐 OPTIMAL SL/TP:")

        # Add SL/TP analysis
        sltp = analysis.get("sltp_analysis", {})
        if thresholds.get("optimal_rr_ratio"):
            lines.append(f"  • Optimal R:R Ratio: {thresholds['optimal_rr_ratio']:.1f}:1")
        if thresholds.get("optimal_sl_distance"):
            lines.append(f"  • Optimal SL Distance: {thresholds['optimal_sl_distance']:.2f}%")

        sl_wins = sltp.get("sl_distance", {}).get("wins", {})
        if sl_wins.get("avg"):
            lines.append(f"  • Winning Trades SL: avg {sl_wins['avg']:.2f}%")

        lines.append("")
        lines.append("💡 RECOMMENDATIONS:")

        for rec in recommendations:
            lines.append(f"  • {rec}")

        if not recommendations:
            lines.append("  • No specific recommendations yet")

        lines.append("=" * 70)
        return "\n".join(lines)


class LLMTradeReviewer:
    """Uses LLM to analyze trade history and identify patterns for improvement.

    This provides deeper, more nuanced insights than statistical analysis alone.
    Run weekly or after significant trading activity.
    """

    def __init__(self, perf_tracker: PerformanceTracker, llm_client=None):
        self.perf_tracker = perf_tracker
        self.llm_client = llm_client  # Anthropic or OpenAI client
        self.review_history: List[Dict] = []
        self._load_reviews()

    def _load_reviews(self):
        """Load previous review history."""
        review_file = "trade_reviews.json"
        if os.path.exists(review_file):
            try:
                with open(review_file, 'r') as f:
                    self.review_history = json.load(f)
            except Exception as e:
                logger.error(f"Error loading reviews: {e}")

    def _save_reviews(self):
        """Save review history."""
        try:
            with open("trade_reviews.json", 'w') as f:
                json.dump(self.review_history[-50:], f, indent=2)  # Keep last 50 reviews
        except Exception as e:
            logger.error(f"Error saving reviews: {e}")

    def format_trades_for_llm(self, trades: List[Trade], max_trades: int = 30) -> str:
        """Format trades into a structured summary for LLM analysis."""
        if not trades:
            return "No trades available."

        # Take most recent trades
        recent = trades[-max_trades:]

        lines = []
        for i, t in enumerate(recent, 1):
            ec = t.entry_conditions
            lines.append(f"Trade {i}:")
            lines.append(f"  Symbol: {t.symbol} | Side: {t.side.upper()}")
            lines.append(f"  P&L: {t.pnl_pct:+.2f}% (${t.pnl_usd:+.2f})")
            lines.append(f"  MFE: {t.mfe_pct:+.2f}% | MAE: {t.mae_pct:+.2f}%")
            lines.append(f"  Efficiency: {t.trade_efficiency*100:.0f}% (of MFE captured)")
            lines.append(f"  Duration: {(t.exit_time - t.entry_time).total_seconds()/60:.0f} min")
            lines.append(f"  Exit Reason: {t.exit_reason}")

            if ec:
                lines.append(f"  Entry Conditions:")
                lines.append(f"    RSI: {ec.rsi:.1f} | BB Position: {ec.bb_position:.2f}")
                lines.append(f"    Regime: {ec.adaptive_regime} | ADX: {ec.adx:.1f}")
                lines.append(f"    EMA Signals: 5m={ec.ema_fast_signal}, 15m={ec.ema_mid_signal}, 1h={ec.ema_macro_signal}")
                lines.append(f"    Orderbook Imbalance: {ec.orderbook_imbalance:+.2f}")
                lines.append(f"    Volume Ratio: {ec.volume_ratio:.2f}x")
                lines.append(f"    Confidence: {ec.signal_confidence:.0%}")
                lines.append(f"    Strategy: {ec.strategy_type}")
            lines.append("")

        return "\n".join(lines)

    def generate_review_prompt(self, trades: List[Trade]) -> str:
        """Generate the analysis prompt for the LLM."""
        wins = [t for t in trades if t.pnl_pct > 0]
        losses = [t for t in trades if t.pnl_pct < 0]

        win_rate = len(wins) / len(trades) * 100 if trades else 0
        avg_win = sum(t.pnl_pct for t in wins) / len(wins) if wins else 0
        avg_loss = sum(t.pnl_pct for t in losses) / len(losses) if losses else 0

        # MFE/MAE analysis
        avg_mfe = sum(t.mfe_pct for t in trades) / len(trades) if trades else 0
        avg_mae = sum(t.mae_pct for t in trades) / len(trades) if trades else 0
        avg_efficiency = sum(t.trade_efficiency for t in trades) / len(trades) if trades else 0

        summary = f"""TRADE REVIEW REQUEST

SUMMARY STATISTICS:
- Total Trades: {len(trades)}
- Win Rate: {win_rate:.1f}%
- Average Win: {avg_win:+.2f}%
- Average Loss: {avg_loss:+.2f}%
- Average MFE: {avg_mfe:+.2f}%
- Average MAE: {avg_mae:+.2f}%
- Average Efficiency: {avg_efficiency*100:.0f}% (% of MFE captured)

WINNING TRADES ({len(wins)}):
{self.format_trades_for_llm(wins, max_trades=15)}

LOSING TRADES ({len(losses)}):
{self.format_trades_for_llm(losses, max_trades=15)}
"""
        return summary

    def get_analysis_prompt(self) -> str:
        """System prompt for trade analysis."""
        return """You are an expert trading coach analyzing a crypto scalping bot's performance.

Analyze the provided trades and identify:

1. **WINNING PATTERNS**: What conditions appear consistently in winning trades?
   - Entry conditions (RSI ranges, regime types, EMA alignment)
   - Time of day patterns
   - Orderbook conditions that preceded wins

2. **LOSING PATTERNS**: What conditions led to losses?
   - Were losses from bad entries or poor exits?
   - Common MAE patterns (how much drawdown before loss?)
   - Regime/conditions to avoid

3. **EXIT OPTIMIZATION**: Based on MFE/MAE data:
   - Are exits too early (low efficiency, lots of MFE left on table)?
   - Are stops too tight (MAE close to entry, then reversal)?
   - Optimal trailing strategy recommendations

4. **CONFIDENCE CALIBRATION**:
   - Are high-confidence trades actually winning more?
   - Should confidence thresholds be adjusted?

5. **ACTIONABLE RECOMMENDATIONS**: Provide 3-5 specific, quantitative rules to improve.
   Example: "Avoid longs when RSI > 65 AND regime is 'ranging' (0% win rate in data)"

Respond with JSON:
{
    "winning_patterns": ["pattern1", "pattern2"],
    "losing_patterns": ["pattern1", "pattern2"],
    "exit_recommendations": {
        "current_efficiency": "...",
        "recommendation": "..."
    },
    "confidence_calibration": {
        "is_calibrated": true/false,
        "adjustment": "..."
    },
    "actionable_rules": [
        {"rule": "...", "expected_impact": "..."},
        ...
    ],
    "summary": "One paragraph summary of key insights"
}"""

    async def run_review_async(self, days_back: int = 7) -> Dict[str, Any]:
        """Run LLM trade review on recent trades (async version)."""
        from datetime import timedelta

        # Get trades from last N days
        cutoff = datetime.utcnow() - timedelta(days=days_back)
        recent_trades = [t for t in self.perf_tracker.trades
                        if t.entry_time >= cutoff]

        if len(recent_trades) < 5:
            return {
                "status": "insufficient_data",
                "message": f"Need at least 5 trades for review. Found {len(recent_trades)} in last {days_back} days."
            }

        if not self.llm_client:
            return {
                "status": "no_client",
                "message": "LLM client not configured. Call with llm_client parameter."
            }

        # Generate prompt
        trade_data = self.generate_review_prompt(recent_trades)
        system_prompt = self.get_analysis_prompt()

        try:
            # Try Anthropic first
            if hasattr(self.llm_client, 'messages'):
                response = self.llm_client.messages.create(
                    model="claude-sonnet-4-20250514",
                    max_tokens=2000,
                    system=system_prompt,
                    messages=[{"role": "user", "content": trade_data}]
                )
                result_text = response.content[0].text
            # Fall back to OpenAI-style
            elif hasattr(self.llm_client, 'chat'):
                response = self.llm_client.chat.completions.create(
                    model="deepseek-chat",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": trade_data}
                    ],
                    max_tokens=2000
                )
                result_text = response.choices[0].message.content
            else:
                return {"status": "error", "message": "Unknown LLM client type"}

            # Parse JSON response
            import re
            json_match = re.search(r'\{[\s\S]*\}', result_text)
            if json_match:
                analysis = json.loads(json_match.group())
            else:
                analysis = {"raw_response": result_text}

            # Save review
            review = {
                "timestamp": datetime.utcnow().isoformat(),
                "trades_analyzed": len(recent_trades),
                "days_back": days_back,
                "analysis": analysis
            }
            self.review_history.append(review)
            self._save_reviews()

            logger.info(f"🧠 LLM Trade Review complete: {len(recent_trades)} trades analyzed")
            return {"status": "success", "review": review}

        except Exception as e:
            logger.error(f"LLM review failed: {e}")
            return {"status": "error", "message": str(e)}

    def run_review(self, days_back: int = 7) -> Dict[str, Any]:
        """Synchronous wrapper for review (uses event loop)."""
        import asyncio
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # If already in async context, create task
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as pool:
                    future = pool.submit(asyncio.run, self.run_review_async(days_back))
                    return future.result()
            else:
                return loop.run_until_complete(self.run_review_async(days_back))
        except Exception as e:
            # Fallback for when no event loop exists
            return asyncio.run(self.run_review_async(days_back))

    def get_latest_recommendations(self) -> List[str]:
        """Get actionable rules from the most recent review."""
        if not self.review_history:
            return ["No reviews available yet. Run review first."]

        latest = self.review_history[-1]
        analysis = latest.get("analysis", {})
        rules = analysis.get("actionable_rules", [])

        if not rules:
            return [analysis.get("summary", "No specific recommendations.")]

        return [r.get("rule", str(r)) for r in rules]

    def get_review_report(self) -> str:
        """Get human-readable report from latest review."""
        if not self.review_history:
            return "No LLM reviews available. Run run_review() first."

        latest = self.review_history[-1]
        analysis = latest.get("analysis", {})

        lines = [
            "=" * 70,
            "🧠 LLM TRADE REVIEW",
            f"   Date: {latest.get('timestamp', 'Unknown')[:10]}",
            f"   Trades Analyzed: {latest.get('trades_analyzed', 0)}",
            "=" * 70,
            "",
            "📈 WINNING PATTERNS:"
        ]

        for p in analysis.get("winning_patterns", ["None identified"]):
            lines.append(f"  ✅ {p}")

        lines.append("")
        lines.append("📉 LOSING PATTERNS:")
        for p in analysis.get("losing_patterns", ["None identified"]):
            lines.append(f"  ❌ {p}")

        lines.append("")
        exit_rec = analysis.get("exit_recommendations", {})
        lines.append("🎯 EXIT OPTIMIZATION:")
        lines.append(f"  • Current Efficiency: {exit_rec.get('current_efficiency', 'N/A')}")
        lines.append(f"  • Recommendation: {exit_rec.get('recommendation', 'N/A')}")

        lines.append("")
        lines.append("📊 ACTIONABLE RULES:")
        for rule in analysis.get("actionable_rules", [{"rule": "Run review to generate"}]):
            lines.append(f"  • {rule.get('rule', rule)}")
            if rule.get("expected_impact"):
                lines.append(f"    Expected Impact: {rule['expected_impact']}")

        lines.append("")
        lines.append("💡 SUMMARY:")
        lines.append(f"  {analysis.get('summary', 'No summary available')}")

        lines.append("=" * 70)
        return "\n".join(lines)


class AdaptiveParameterOptimizer:
    """Automatically adjusts trading parameters based on performance data.

    Uses statistical analysis of trade outcomes to optimize:
    - Stop loss distances
    - Take profit targets
    - Confidence thresholds
    - Entry condition filters
    """

    def __init__(self, perf_tracker: PerformanceTracker):
        self.perf_tracker = perf_tracker
        self.adjustments: Dict[str, Any] = {}
        self.adjustment_history: List[Dict] = []
        self._load_adjustments()

    def _load_adjustments(self):
        """Load previous adjustments."""
        adj_file = "adaptive_params.json"
        if os.path.exists(adj_file):
            try:
                with open(adj_file, 'r') as f:
                    data = json.load(f)
                    self.adjustments = data.get("current", {})
                    self.adjustment_history = data.get("history", [])
            except Exception as e:
                logger.error(f"Error loading adjustments: {e}")

    def _save_adjustments(self):
        """Save adjustments."""
        try:
            with open("adaptive_params.json", 'w') as f:
                json.dump({
                    "current": self.adjustments,
                    "history": self.adjustment_history[-100:]
                }, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving adjustments: {e}")

    def analyze_optimal_sl_distance(self, min_trades: int = 20) -> Dict[str, float]:
        """Analyze MAE data to find optimal stop loss distance."""
        trades = self.perf_tracker.trades
        if len(trades) < min_trades:
            return {"status": "insufficient_data", "trades": len(trades)}

        wins = [t for t in trades if t.pnl_pct > 0]
        losses = [t for t in trades if t.pnl_pct < 0]

        if not wins or not losses:
            return {"status": "need_both_wins_and_losses"}

        # Analyze MAE of winning trades - this is the drawdown we should tolerate
        win_maes = [abs(t.mae_pct) for t in wins if t.mae_pct != 0]
        loss_maes = [abs(t.mae_pct) for t in losses if t.mae_pct != 0]

        if not win_maes:
            return {"status": "no_mae_data"}

        # Optimal SL should be wider than most winning trade MAEs
        # but not so wide that losses become catastrophic
        win_mae_90th = sorted(win_maes)[int(len(win_maes) * 0.9)] if win_maes else 0
        avg_loss_mae = sum(loss_maes) / len(loss_maes) if loss_maes else 0

        # Recommendation: SL at 90th percentile of winning MAE + small buffer
        optimal_sl = win_mae_90th * 1.1

        return {
            "status": "success",
            "optimal_sl_pct": optimal_sl,
            "win_mae_90th": win_mae_90th,
            "avg_loss_mae": avg_loss_mae,
            "current_too_tight": avg_loss_mae < win_mae_90th,
            "recommendation": f"Set SL at {optimal_sl:.2f}% to avoid stopping out winners"
        }

    def analyze_optimal_tp_distance(self, min_trades: int = 20) -> Dict[str, float]:
        """Analyze MFE data to find optimal take profit distance."""
        trades = self.perf_tracker.trades
        if len(trades) < min_trades:
            return {"status": "insufficient_data"}

        wins = [t for t in trades if t.pnl_pct > 0]

        if not wins:
            return {"status": "no_winning_trades"}

        # Analyze MFE of winning trades
        win_mfes = [t.mfe_pct for t in wins if t.mfe_pct > 0]
        win_pnls = [t.pnl_pct for t in wins]
        efficiencies = [t.trade_efficiency for t in wins]

        if not win_mfes:
            return {"status": "no_mfe_data"}

        avg_mfe = sum(win_mfes) / len(win_mfes)
        avg_pnl = sum(win_pnls) / len(win_pnls)
        avg_efficiency = sum(efficiencies) / len(efficiencies)

        # How much MFE are we leaving on the table?
        left_on_table = avg_mfe - avg_pnl

        # If efficiency is low, we're exiting too early
        # If efficiency is very high but MFE is low, TP might be too tight

        return {
            "status": "success",
            "avg_mfe": avg_mfe,
            "avg_pnl": avg_pnl,
            "avg_efficiency": avg_efficiency,
            "left_on_table": left_on_table,
            "recommendation": self._get_tp_recommendation(avg_efficiency, left_on_table)
        }

    def _get_tp_recommendation(self, efficiency: float, left_on_table: float) -> str:
        """Generate TP recommendation based on efficiency."""
        if efficiency < 0.5:
            return f"Exits too early. Leaving {left_on_table:.2f}% on table. Consider trailing TP."
        elif efficiency > 0.8:
            return "Good efficiency. Current TP strategy working well."
        else:
            return f"Moderate efficiency ({efficiency:.0%}). Consider tighter trailing after {left_on_table:.2f}% profit."

    def analyze_confidence_calibration(self, min_trades: int = 30) -> Dict[str, Any]:
        """Check if confidence scores correlate with actual win rates."""
        trades = self.perf_tracker.trades
        if len(trades) < min_trades:
            return {"status": "insufficient_data"}

        # Group trades by confidence level
        high_conf = [t for t in trades if t.entry_conditions and t.entry_conditions.signal_confidence >= 0.7]
        med_conf = [t for t in trades if t.entry_conditions and 0.5 <= t.entry_conditions.signal_confidence < 0.7]
        low_conf = [t for t in trades if t.entry_conditions and t.entry_conditions.signal_confidence < 0.5]

        def win_rate(trade_list):
            if not trade_list:
                return 0
            return len([t for t in trade_list if t.pnl_pct > 0]) / len(trade_list)

        high_wr = win_rate(high_conf)
        med_wr = win_rate(med_conf)
        low_wr = win_rate(low_conf)

        # Confidence is calibrated if high > med > low
        is_calibrated = high_wr >= med_wr >= low_wr and high_wr > low_wr

        return {
            "status": "success",
            "high_confidence": {"count": len(high_conf), "win_rate": high_wr},
            "medium_confidence": {"count": len(med_conf), "win_rate": med_wr},
            "low_confidence": {"count": len(low_conf), "win_rate": low_wr},
            "is_calibrated": is_calibrated,
            "recommendation": self._get_confidence_recommendation(high_wr, med_wr, low_wr, is_calibrated)
        }

    def _get_confidence_recommendation(self, high_wr, med_wr, low_wr, is_calibrated) -> str:
        """Generate confidence calibration recommendation."""
        if is_calibrated:
            if low_wr < 0.4:
                return f"Well calibrated. Consider filtering out low-confidence trades (WR: {low_wr:.0%})"
            return "Confidence well calibrated with win rates."
        else:
            if high_wr < med_wr:
                return "High confidence trades underperforming. Review confidence calculation."
            return "Confidence not predictive. Consider recalibrating signal scoring."

    def generate_parameter_adjustments(self) -> Dict[str, Any]:
        """Generate all parameter adjustment recommendations."""
        sl_analysis = self.analyze_optimal_sl_distance()
        tp_analysis = self.analyze_optimal_tp_distance()
        conf_analysis = self.analyze_confidence_calibration()

        adjustments = {
            "timestamp": datetime.utcnow().isoformat(),
            "stop_loss": sl_analysis,
            "take_profit": tp_analysis,
            "confidence": conf_analysis,
            "suggested_params": {}
        }

        # Generate specific parameter suggestions
        if sl_analysis.get("status") == "success":
            adjustments["suggested_params"]["sl_atr_multiplier"] = sl_analysis["optimal_sl_pct"] / 0.5  # Assuming 0.5% base

        if tp_analysis.get("status") == "success":
            if tp_analysis["avg_efficiency"] < 0.5:
                adjustments["suggested_params"]["use_trailing_tp"] = True
                adjustments["suggested_params"]["trail_activation_pct"] = tp_analysis["avg_mfe"] * 0.5

        if conf_analysis.get("status") == "success":
            if not conf_analysis["is_calibrated"]:
                adjustments["suggested_params"]["min_confidence"] = 0.6  # Raise threshold

        # Save to history
        self.adjustments = adjustments
        self.adjustment_history.append(adjustments)
        self._save_adjustments()

        return adjustments

    def get_adjustment_report(self) -> str:
        """Get human-readable adjustment report."""
        if not self.adjustments:
            self.generate_parameter_adjustments()

        adj = self.adjustments
        lines = [
            "=" * 70,
            "🔧 ADAPTIVE PARAMETER OPTIMIZATION",
            f"   Generated: {adj.get('timestamp', 'Unknown')[:19]}",
            "=" * 70,
            "",
            "📉 STOP LOSS ANALYSIS:"
        ]

        sl = adj.get("stop_loss", {})
        if sl.get("status") == "success":
            lines.append(f"  • Optimal SL: {sl['optimal_sl_pct']:.2f}%")
            lines.append(f"  • 90th percentile winning MAE: {sl['win_mae_90th']:.2f}%")
            lines.append(f"  • Avg losing MAE: {sl['avg_loss_mae']:.2f}%")
            lines.append(f"  • {sl['recommendation']}")
        else:
            lines.append(f"  • Status: {sl.get('status', 'unknown')}")

        lines.append("")
        lines.append("📈 TAKE PROFIT ANALYSIS:")

        tp = adj.get("take_profit", {})
        if tp.get("status") == "success":
            lines.append(f"  • Avg MFE: {tp['avg_mfe']:.2f}%")
            lines.append(f"  • Avg P&L: {tp['avg_pnl']:.2f}%")
            lines.append(f"  • Efficiency: {tp['avg_efficiency']:.0%}")
            lines.append(f"  • Left on table: {tp['left_on_table']:.2f}%")
            lines.append(f"  • {tp['recommendation']}")
        else:
            lines.append(f"  • Status: {tp.get('status', 'unknown')}")

        lines.append("")
        lines.append("🎯 CONFIDENCE CALIBRATION:")

        conf = adj.get("confidence", {})
        if conf.get("status") == "success":
            lines.append(f"  • High conf WR: {conf['high_confidence']['win_rate']:.0%} ({conf['high_confidence']['count']} trades)")
            lines.append(f"  • Med conf WR: {conf['medium_confidence']['win_rate']:.0%} ({conf['medium_confidence']['count']} trades)")
            lines.append(f"  • Low conf WR: {conf['low_confidence']['win_rate']:.0%} ({conf['low_confidence']['count']} trades)")
            lines.append(f"  • Calibrated: {'✅ Yes' if conf['is_calibrated'] else '❌ No'}")
            lines.append(f"  • {conf['recommendation']}")
        else:
            lines.append(f"  • Status: {conf.get('status', 'unknown')}")

        lines.append("")
        lines.append("💡 SUGGESTED PARAMETERS:")

        params = adj.get("suggested_params", {})
        if params:
            for k, v in params.items():
                lines.append(f"  • {k}: {v}")
        else:
            lines.append("  • No specific adjustments suggested")

        lines.append("=" * 70)
        return "\n".join(lines)


class RegimePerformanceTracker:
    """Track performance by market regime to identify optimal trading conditions.

    Analyzes win rates, P&L, and efficiency across different:
    - Volatility regimes (low, normal, high, extreme)
    - Trend regimes (trending, ranging, choppy)
    - Time periods (session, day of week, hour)
    """

    def __init__(self, perf_tracker: PerformanceTracker):
        self.perf_tracker = perf_tracker
        self.regime_stats: Dict[str, Dict] = {}

    def analyze_by_regime(self) -> Dict[str, Any]:
        """Analyze performance by adaptive regime."""
        trades = self.perf_tracker.trades
        if not trades:
            return {"status": "no_trades"}

        # Group by regime
        regime_groups: Dict[str, List[Trade]] = {}
        for t in trades:
            if t.entry_conditions:
                regime = t.entry_conditions.adaptive_regime or "unknown"
            else:
                regime = "unknown"

            if regime not in regime_groups:
                regime_groups[regime] = []
            regime_groups[regime].append(t)

        # Calculate stats per regime
        results = {}
        for regime, regime_trades in regime_groups.items():
            wins = [t for t in regime_trades if t.pnl_pct > 0]
            losses = [t for t in regime_trades if t.pnl_pct < 0]

            total_pnl = sum(t.pnl_pct for t in regime_trades)
            avg_pnl = total_pnl / len(regime_trades) if regime_trades else 0
            win_rate = len(wins) / len(regime_trades) if regime_trades else 0

            avg_mfe = sum(t.mfe_pct for t in regime_trades) / len(regime_trades) if regime_trades else 0
            avg_mae = sum(t.mae_pct for t in regime_trades) / len(regime_trades) if regime_trades else 0
            avg_efficiency = sum(t.trade_efficiency for t in regime_trades) / len(regime_trades) if regime_trades else 0

            results[regime] = {
                "count": len(regime_trades),
                "win_rate": win_rate,
                "total_pnl": total_pnl,
                "avg_pnl": avg_pnl,
                "avg_mfe": avg_mfe,
                "avg_mae": avg_mae,
                "avg_efficiency": avg_efficiency,
                "best_trade": max(t.pnl_pct for t in regime_trades) if regime_trades else 0,
                "worst_trade": min(t.pnl_pct for t in regime_trades) if regime_trades else 0
            }

        self.regime_stats["by_regime"] = results
        return results

    def analyze_by_volatility(self) -> Dict[str, Any]:
        """Analyze performance by volatility regime."""
        trades = self.perf_tracker.trades
        if not trades:
            return {"status": "no_trades"}

        vol_groups: Dict[str, List[Trade]] = {
            "low": [], "normal": [], "high": [], "extreme": [], "unknown": []
        }

        for t in trades:
            if t.entry_conditions:
                vol = t.entry_conditions.volatility_regime or "unknown"
            else:
                vol = "unknown"

            if vol in vol_groups:
                vol_groups[vol].append(t)
            else:
                vol_groups["unknown"].append(t)

        results = {}
        for vol, vol_trades in vol_groups.items():
            if not vol_trades:
                continue

            wins = [t for t in vol_trades if t.pnl_pct > 0]
            total_pnl = sum(t.pnl_pct for t in vol_trades)

            results[vol] = {
                "count": len(vol_trades),
                "win_rate": len(wins) / len(vol_trades),
                "total_pnl": total_pnl,
                "avg_pnl": total_pnl / len(vol_trades),
                "avg_efficiency": sum(t.trade_efficiency for t in vol_trades) / len(vol_trades)
            }

        self.regime_stats["by_volatility"] = results
        return results

    def analyze_by_hour(self) -> Dict[str, Any]:
        """Analyze performance by hour of day (UTC)."""
        trades = self.perf_tracker.trades
        if not trades:
            return {"status": "no_trades"}

        hour_groups: Dict[int, List[Trade]] = {h: [] for h in range(24)}

        for t in trades:
            hour = t.entry_time.hour
            hour_groups[hour].append(t)

        results = {}
        for hour, hour_trades in hour_groups.items():
            if not hour_trades:
                continue

            wins = [t for t in hour_trades if t.pnl_pct > 0]
            total_pnl = sum(t.pnl_pct for t in hour_trades)

            results[hour] = {
                "count": len(hour_trades),
                "win_rate": len(wins) / len(hour_trades),
                "total_pnl": total_pnl,
                "avg_pnl": total_pnl / len(hour_trades)
            }

        self.regime_stats["by_hour"] = results
        return results

    def get_best_conditions(self) -> Dict[str, Any]:
        """Identify the best trading conditions based on historical data."""
        if not self.regime_stats:
            self.analyze_by_regime()
            self.analyze_by_volatility()
            self.analyze_by_hour()

        best = {
            "best_regime": None,
            "best_volatility": None,
            "best_hours": [],
            "avoid_regime": None,
            "avoid_volatility": None,
            "avoid_hours": []
        }

        # Find best regime
        by_regime = self.regime_stats.get("by_regime", {})
        if by_regime:
            valid_regimes = {k: v for k, v in by_regime.items() if v["count"] >= 5}
            if valid_regimes:
                best["best_regime"] = max(valid_regimes.items(), key=lambda x: x[1]["avg_pnl"])
                worst = min(valid_regimes.items(), key=lambda x: x[1]["avg_pnl"])
                if worst[1]["avg_pnl"] < 0:
                    best["avoid_regime"] = worst

        # Find best volatility
        by_vol = self.regime_stats.get("by_volatility", {})
        if by_vol:
            valid_vols = {k: v for k, v in by_vol.items() if v["count"] >= 5}
            if valid_vols:
                best["best_volatility"] = max(valid_vols.items(), key=lambda x: x[1]["avg_pnl"])
                worst = min(valid_vols.items(), key=lambda x: x[1]["avg_pnl"])
                if worst[1]["avg_pnl"] < 0:
                    best["avoid_volatility"] = worst

        # Find best hours
        by_hour = self.regime_stats.get("by_hour", {})
        if by_hour:
            valid_hours = {k: v for k, v in by_hour.items() if v["count"] >= 3}
            if valid_hours:
                sorted_hours = sorted(valid_hours.items(), key=lambda x: x[1]["avg_pnl"], reverse=True)
                best["best_hours"] = sorted_hours[:3]  # Top 3 hours
                worst_hours = [h for h in sorted_hours if h[1]["avg_pnl"] < 0]
                best["avoid_hours"] = worst_hours[:3] if worst_hours else []

        return best

    def get_regime_report(self) -> str:
        """Get human-readable regime performance report."""
        self.analyze_by_regime()
        self.analyze_by_volatility()
        self.analyze_by_hour()
        best = self.get_best_conditions()

        lines = [
            "=" * 70,
            "📊 REGIME PERFORMANCE ANALYSIS",
            "=" * 70,
            "",
            "🎯 BY ADAPTIVE REGIME:"
        ]

        for regime, stats in self.regime_stats.get("by_regime", {}).items():
            emoji = "✅" if stats["avg_pnl"] > 0 else "❌"
            lines.append(f"  {emoji} {regime.upper()}: {stats['count']} trades | WR: {stats['win_rate']:.0%} | Avg: {stats['avg_pnl']:+.2f}%")

        lines.append("")
        lines.append("📈 BY VOLATILITY:")

        for vol, stats in self.regime_stats.get("by_volatility", {}).items():
            emoji = "✅" if stats["avg_pnl"] > 0 else "❌"
            lines.append(f"  {emoji} {vol.upper()}: {stats['count']} trades | WR: {stats['win_rate']:.0%} | Avg: {stats['avg_pnl']:+.2f}%")

        lines.append("")
        lines.append("⏰ BEST HOURS (UTC):")

        for hour, stats in best.get("best_hours", []):
            lines.append(f"  ✅ {hour:02d}:00: {stats['count']} trades | WR: {stats['win_rate']:.0%} | Avg: {stats['avg_pnl']:+.2f}%")

        if best.get("avoid_hours"):
            lines.append("")
            lines.append("⚠️ AVOID HOURS (UTC):")
            for hour, stats in best["avoid_hours"]:
                lines.append(f"  ❌ {hour:02d}:00: {stats['count']} trades | WR: {stats['win_rate']:.0%} | Avg: {stats['avg_pnl']:+.2f}%")

        lines.append("")
        lines.append("💡 RECOMMENDATIONS:")

        if best.get("best_regime"):
            regime, stats = best["best_regime"]
            lines.append(f"  • Best regime: {regime.upper()} ({stats['avg_pnl']:+.2f}% avg)")

        if best.get("avoid_regime"):
            regime, stats = best["avoid_regime"]
            lines.append(f"  • Avoid regime: {regime.upper()} ({stats['avg_pnl']:+.2f}% avg)")

        if best.get("best_volatility"):
            vol, stats = best["best_volatility"]
            lines.append(f"  • Best volatility: {vol.upper()} ({stats['avg_pnl']:+.2f}% avg)")

        lines.append("=" * 70)
        return "\n".join(lines)
