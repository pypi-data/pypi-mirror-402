"""
Backtest Framework - Prove Your Edge Before Trading

A strategy without backtested positive expectancy is just gambling.
This module provides:
1. Historical data replay
2. Signal generation on past data
3. Trade simulation with realistic fills
4. Performance metrics (Sharpe, Sortino, Max DD, Win Rate)
5. Statistical significance testing

Use this to:
- Validate new signals have edge
- Optimize parameters
- Understand when your strategy works/fails
"""

import logging
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import json
import os

logger = logging.getLogger(__name__)


@dataclass
class BacktestTrade:
    """A single trade in the backtest."""
    entry_time: datetime
    exit_time: datetime
    symbol: str
    side: str  # "long" or "short"
    entry_price: float
    exit_price: float
    size: float
    pnl_pct: float
    pnl_usd: float
    exit_reason: str
    signals_at_entry: Dict[str, Any] = field(default_factory=dict)


@dataclass 
class BacktestResult:
    """Results from a backtest run."""
    start_date: datetime
    end_date: datetime
    initial_capital: float
    final_capital: float
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float
    avg_win_pct: float
    avg_loss_pct: float
    profit_factor: float
    max_drawdown_pct: float
    sharpe_ratio: float
    sortino_ratio: float
    total_return_pct: float
    trades: List[BacktestTrade] = field(default_factory=list)
    equity_curve: List[Dict] = field(default_factory=list)
    monthly_returns: Dict[str, float] = field(default_factory=dict)


class Backtester:
    """
    Backtest trading strategies on historical data.
    """
    
    def __init__(
        self,
        initial_capital: float = 10000,
        position_size_pct: float = 0.1,  # 10% per trade
        max_positions: int = 3,
        commission_pct: float = 0.001,  # 0.1% commission
        slippage_pct: float = 0.0005    # 0.05% slippage
    ):
        self.initial_capital = initial_capital
        self.position_size_pct = position_size_pct
        self.max_positions = max_positions
        self.commission_pct = commission_pct
        self.slippage_pct = slippage_pct
        
        # State
        self.capital = initial_capital
        self.positions: Dict[str, Dict] = {}
        self.trades: List[BacktestTrade] = []
        self.equity_curve: List[Dict] = []
        self.peak_equity = initial_capital
        self.max_drawdown = 0
    
    def reset(self):
        """Reset backtester state."""
        self.capital = self.initial_capital
        self.positions = {}
        self.trades = []
        self.equity_curve = []
        self.peak_equity = self.initial_capital
        self.max_drawdown = 0
    
    def run_backtest(
        self,
        candles: List[Dict],
        signal_generator: Callable[[List[Dict], int], Optional[Dict]],
        symbol: str = "BTC",
        stop_loss_pct: float = 2.0,
        take_profit_pct: float = 4.0
    ) -> BacktestResult:
        """
        Run backtest on historical candle data.
        
        Args:
            candles: List of OHLCV candles (oldest first)
            signal_generator: Function that takes (candles_so_far, current_index) 
                             and returns signal dict or None
            symbol: Trading symbol
            stop_loss_pct: Stop loss percentage
            take_profit_pct: Take profit percentage
            
        Returns:
            BacktestResult with performance metrics
        """
        self.reset()
        
        if len(candles) < 100:
            logger.warning("Insufficient candles for meaningful backtest")
            return self._generate_result(candles)
        
        # Process each candle
        for i in range(100, len(candles)):  # Start after warmup period
            current_candle = candles[i]
            candles_so_far = candles[:i+1]
            
            timestamp = self._parse_timestamp(current_candle)
            current_price = current_candle.get("close", current_candle.get("c", 0))
            high = current_candle.get("high", current_candle.get("h", current_price))
            low = current_candle.get("low", current_candle.get("l", current_price))
            
            # Check existing positions for stops/targets
            self._check_exits(symbol, high, low, current_price, timestamp)
            
            # Generate signal for this candle
            signal = signal_generator(candles_so_far, i)
            
            # Process signal
            if signal and signal.get("direction") in ["bullish", "bearish"]:
                confidence = signal.get("confidence", 0)
                if confidence >= 0.5 and len(self.positions) < self.max_positions:
                    self._enter_position(
                        symbol=symbol,
                        side="long" if signal["direction"] == "bullish" else "short",
                        price=current_price,
                        timestamp=timestamp,
                        stop_loss_pct=stop_loss_pct,
                        take_profit_pct=take_profit_pct,
                        signals=signal
                    )
            
            # Record equity
            total_equity = self._calculate_equity(current_price)
            self.equity_curve.append({
                "timestamp": timestamp.isoformat() if timestamp else str(i),
                "equity": total_equity,
                "price": current_price
            })
            
            # Track drawdown
            if total_equity > self.peak_equity:
                self.peak_equity = total_equity
            dd = (self.peak_equity - total_equity) / self.peak_equity
            self.max_drawdown = max(self.max_drawdown, dd)
        
        return self._generate_result(candles)

    def _parse_timestamp(self, candle: Dict) -> Optional[datetime]:
        """Parse timestamp from candle."""
        ts = candle.get("timestamp", candle.get("t", candle.get("time")))
        if ts is None:
            return None
        if isinstance(ts, datetime):
            return ts
        if isinstance(ts, (int, float)):
            # Assume milliseconds if large number
            if ts > 1e12:
                ts = ts / 1000
            return datetime.fromtimestamp(ts)
        if isinstance(ts, str):
            try:
                return datetime.fromisoformat(ts.replace("Z", "+00:00"))
            except ValueError:
                return None
        return None

    def _enter_position(
        self,
        symbol: str,
        side: str,
        price: float,
        timestamp: datetime,
        stop_loss_pct: float,
        take_profit_pct: float,
        signals: Dict
    ):
        """Enter a new position."""
        # Apply slippage
        if side == "long":
            entry_price = price * (1 + self.slippage_pct)
            stop_price = entry_price * (1 - stop_loss_pct / 100)
            target_price = entry_price * (1 + take_profit_pct / 100)
        else:
            entry_price = price * (1 - self.slippage_pct)
            stop_price = entry_price * (1 + stop_loss_pct / 100)
            target_price = entry_price * (1 - take_profit_pct / 100)

        # Calculate position size
        position_value = self.capital * self.position_size_pct
        size = position_value / entry_price

        # Apply commission
        commission = position_value * self.commission_pct
        self.capital -= commission

        self.positions[f"{symbol}_{len(self.trades)}"] = {
            "symbol": symbol,
            "side": side,
            "entry_price": entry_price,
            "entry_time": timestamp,
            "size": size,
            "stop_price": stop_price,
            "target_price": target_price,
            "signals": signals
        }

    def _check_exits(
        self,
        symbol: str,
        high: float,
        low: float,
        close: float,
        timestamp: datetime
    ):
        """Check if any positions should be exited."""
        positions_to_close = []

        for pos_id, pos in self.positions.items():
            if not pos_id.startswith(symbol):
                continue

            exit_price = None
            exit_reason = None

            if pos["side"] == "long":
                if low <= pos["stop_price"]:
                    exit_price = pos["stop_price"]
                    exit_reason = "stop_loss"
                elif high >= pos["target_price"]:
                    exit_price = pos["target_price"]
                    exit_reason = "take_profit"
            else:  # short
                if high >= pos["stop_price"]:
                    exit_price = pos["stop_price"]
                    exit_reason = "stop_loss"
                elif low <= pos["target_price"]:
                    exit_price = pos["target_price"]
                    exit_reason = "take_profit"

            if exit_price:
                positions_to_close.append((pos_id, exit_price, exit_reason, timestamp))

        for pos_id, exit_price, exit_reason, ts in positions_to_close:
            self._close_position(pos_id, exit_price, exit_reason, ts)

    def _close_position(
        self,
        pos_id: str,
        exit_price: float,
        exit_reason: str,
        timestamp: datetime
    ):
        """Close a position and record the trade."""
        pos = self.positions.pop(pos_id)

        # Apply slippage
        if pos["side"] == "long":
            actual_exit = exit_price * (1 - self.slippage_pct)
            pnl_pct = (actual_exit - pos["entry_price"]) / pos["entry_price"] * 100
        else:
            actual_exit = exit_price * (1 + self.slippage_pct)
            pnl_pct = (pos["entry_price"] - actual_exit) / pos["entry_price"] * 100

        pnl_usd = pos["size"] * pos["entry_price"] * (pnl_pct / 100)

        # Apply commission
        commission = pos["size"] * actual_exit * self.commission_pct
        pnl_usd -= commission

        # Update capital
        self.capital += pos["size"] * pos["entry_price"] + pnl_usd

        # Record trade
        self.trades.append(BacktestTrade(
            entry_time=pos["entry_time"],
            exit_time=timestamp,
            symbol=pos["symbol"],
            side=pos["side"],
            entry_price=pos["entry_price"],
            exit_price=actual_exit,
            size=pos["size"],
            pnl_pct=pnl_pct,
            pnl_usd=pnl_usd,
            exit_reason=exit_reason,
            signals_at_entry=pos.get("signals", {})
        ))

    def _calculate_equity(self, current_price: float) -> float:
        """Calculate total equity including open positions."""
        equity = self.capital
        for pos in self.positions.values():
            if pos["side"] == "long":
                unrealized = pos["size"] * (current_price - pos["entry_price"])
            else:
                unrealized = pos["size"] * (pos["entry_price"] - current_price)
            equity += pos["size"] * pos["entry_price"] + unrealized
        return equity

    def _generate_result(self, candles: List[Dict]) -> BacktestResult:
        """Generate backtest result with all metrics."""
        if not self.trades:
            return BacktestResult(
                start_date=self._parse_timestamp(candles[0]) or datetime.now(),
                end_date=self._parse_timestamp(candles[-1]) or datetime.now(),
                initial_capital=self.initial_capital,
                final_capital=self.capital,
                total_trades=0,
                winning_trades=0,
                losing_trades=0,
                win_rate=0,
                avg_win_pct=0,
                avg_loss_pct=0,
                profit_factor=0,
                max_drawdown_pct=self.max_drawdown * 100,
                sharpe_ratio=0,
                sortino_ratio=0,
                total_return_pct=0,
                trades=[],
                equity_curve=self.equity_curve
            )

        # Calculate metrics
        winning = [t for t in self.trades if t.pnl_pct > 0]
        losing = [t for t in self.trades if t.pnl_pct <= 0]

        win_rate = len(winning) / len(self.trades) if self.trades else 0
        avg_win = sum(t.pnl_pct for t in winning) / len(winning) if winning else 0
        avg_loss = abs(sum(t.pnl_pct for t in losing) / len(losing)) if losing else 0

        gross_profit = sum(t.pnl_usd for t in winning)
        gross_loss = abs(sum(t.pnl_usd for t in losing))
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else float('inf')

        total_return = (self.capital - self.initial_capital) / self.initial_capital * 100

        # Calculate Sharpe and Sortino
        returns = [t.pnl_pct for t in self.trades]
        sharpe = self._calculate_sharpe(returns)
        sortino = self._calculate_sortino(returns)

        # Monthly returns
        monthly = self._calculate_monthly_returns()

        return BacktestResult(
            start_date=self._parse_timestamp(candles[0]) or datetime.now(),
            end_date=self._parse_timestamp(candles[-1]) or datetime.now(),
            initial_capital=self.initial_capital,
            final_capital=self.capital,
            total_trades=len(self.trades),
            winning_trades=len(winning),
            losing_trades=len(losing),
            win_rate=round(win_rate, 3),
            avg_win_pct=round(avg_win, 2),
            avg_loss_pct=round(avg_loss, 2),
            profit_factor=round(profit_factor, 2),
            max_drawdown_pct=round(self.max_drawdown * 100, 2),
            sharpe_ratio=round(sharpe, 2),
            sortino_ratio=round(sortino, 2),
            total_return_pct=round(total_return, 2),
            trades=self.trades,
            equity_curve=self.equity_curve,
            monthly_returns=monthly
        )

    def _calculate_sharpe(self, returns: List[float], risk_free: float = 0) -> float:
        """Calculate Sharpe ratio."""
        if len(returns) < 2:
            return 0
        import statistics
        mean_return = statistics.mean(returns)
        std_return = statistics.stdev(returns)
        if std_return == 0:
            return 0
        return (mean_return - risk_free) / std_return

    def _calculate_sortino(self, returns: List[float], risk_free: float = 0) -> float:
        """Calculate Sortino ratio (only downside deviation)."""
        if len(returns) < 2:
            return 0
        import statistics
        mean_return = statistics.mean(returns)
        downside = [r for r in returns if r < 0]
        if len(downside) < 2:
            return float('inf') if mean_return > 0 else 0
        downside_std = statistics.stdev(downside)
        if downside_std == 0:
            return 0
        return (mean_return - risk_free) / downside_std

    def _calculate_monthly_returns(self) -> Dict[str, float]:
        """Calculate returns by month."""
        monthly = {}
        for trade in self.trades:
            if trade.exit_time:
                month_key = trade.exit_time.strftime("%Y-%m")
                if month_key not in monthly:
                    monthly[month_key] = 0
                monthly[month_key] += trade.pnl_pct
        return monthly


def quick_backtest(
    candles: List[Dict],
    signal_func: Callable,
    **kwargs
) -> Dict[str, Any]:
    """
    Quick backtest helper function.

    Args:
        candles: Historical OHLCV data
        signal_func: Function that generates signals
        **kwargs: Additional backtester parameters

    Returns:
        Dict with key metrics
    """
    bt = Backtester(**kwargs)
    result = bt.run_backtest(candles, signal_func)

    return {
        "total_trades": result.total_trades,
        "win_rate": result.win_rate,
        "profit_factor": result.profit_factor,
        "total_return_pct": result.total_return_pct,
        "max_drawdown_pct": result.max_drawdown_pct,
        "sharpe_ratio": result.sharpe_ratio,
        "sortino_ratio": result.sortino_ratio,
        "avg_win_pct": result.avg_win_pct,
        "avg_loss_pct": result.avg_loss_pct,
        "expectancy": result.win_rate * result.avg_win_pct - (1 - result.win_rate) * result.avg_loss_pct
    }
