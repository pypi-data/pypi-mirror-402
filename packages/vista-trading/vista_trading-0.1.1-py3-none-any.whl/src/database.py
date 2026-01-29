"""
SQLite Database for Trading Bot Learning Data.

Centralized storage for all learning data:
- Whale events and outcomes
- Chart signals and outcomes
- Trade signals and results
- S/R breakout events
- Chart images for training

Usage:
    from src.database import get_db
    db = get_db()
    db.save_whale_event(...)
    db.get_whale_events(symbol="BTC", limit=100)
"""

import sqlite3
import logging
import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from contextlib import contextmanager

logger = logging.getLogger(__name__)

# Database path
DB_DIR = Path("data")
DB_PATH = DB_DIR / "trading_bot.db"

# Singleton instance
_db_instance = None


def get_db() -> "TradingDatabase":
    """Get singleton database instance."""
    global _db_instance
    if _db_instance is None:
        _db_instance = TradingDatabase()
    return _db_instance


class TradingDatabase:
    """SQLite database for all trading bot learning data."""

    def __init__(self, db_path: Path = None):
        self.db_path = db_path or DB_PATH
        DB_DIR.mkdir(parents=True, exist_ok=True)
        self._init_db()
        logger.info(f"📀 Database initialized: {self.db_path}")

    @contextmanager
    def _get_conn(self):
        """Get database connection with auto-commit."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

    def _init_db(self):
        """Initialize database schema."""
        with self._get_conn() as conn:
            # Whale events table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS whale_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    whale TEXT NOT NULL,
                    symbol TEXT NOT NULL,
                    action TEXT NOT NULL,
                    side TEXT NOT NULL,
                    size REAL,
                    entry_price REAL,
                    leverage REAL,
                    notional_usd REAL,
                    price_after_5m REAL,
                    price_after_1h REAL,
                    profitable_follow INTEGER,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Chart signals table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS chart_signals (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    signal_id TEXT UNIQUE NOT NULL,
                    signal_type TEXT NOT NULL,
                    symbol TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    price_at_signal REAL NOT NULL,
                    direction TEXT NOT NULL,
                    confidence REAL,
                    support_levels TEXT,
                    resistance_levels TEXT,
                    asc_support_price REAL,
                    desc_resistance_price REAL,
                    trendline_signal TEXT,
                    deepseek_bias TEXT,
                    deepseek_entry TEXT,
                    deepseek_stop TEXT,
                    deepseek_target TEXT,
                    -- Trend analysis fields
                    trend_direction TEXT,
                    trend_strength REAL,
                    ema_position TEXT,
                    rsi_value REAL,
                    macd_histogram REAL,
                    patterns_detected TEXT,
                    volume_trend TEXT,
                    volatility_regime TEXT,
                    -- Outcome tracking
                    outcome_checked INTEGER DEFAULT 0,
                    price_1h REAL,
                    price_4h REAL,
                    price_24h REAL,
                    outcome_direction TEXT,
                    outcome_pct_1h REAL,
                    outcome_pct_4h REAL,
                    outcome_pct_24h REAL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # S/R events table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS sr_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    symbol TEXT NOT NULL,
                    price_at_event REAL NOT NULL,
                    level REAL NOT NULL,
                    direction TEXT NOT NULL,
                    break_pct REAL,
                    price_after_5m REAL,
                    price_after_15m REAL,
                    price_after_1h REAL,
                    continued INTEGER,
                    reversal_pct REAL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Charts table (stores images)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS charts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol TEXT NOT NULL,
                    timeframe TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    price REAL NOT NULL,
                    signal TEXT,
                    direction TEXT,
                    image_data BLOB,
                    analysis_text TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Trade signals table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS trade_signals (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    signal_id TEXT UNIQUE NOT NULL,
                    symbol TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    side TEXT NOT NULL,
                    entry_price REAL NOT NULL,
                    confidence REAL,
                    support_levels TEXT,
                    resistance_levels TEXT,
                    stop_loss REAL,
                    take_profit REAL,
                    exit_price REAL,
                    exit_timestamp TEXT,
                    pnl_pct REAL,
                    outcome TEXT,
                    metadata TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Completed trades table (full trade records with entry conditions for learning)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS completed_trades (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol TEXT NOT NULL,
                    side TEXT NOT NULL,
                    entry_price REAL NOT NULL,
                    exit_price REAL NOT NULL,
                    size REAL NOT NULL,
                    entry_time TEXT NOT NULL,
                    exit_time TEXT NOT NULL,
                    pnl_pct REAL NOT NULL,
                    pnl_usd REAL NOT NULL,
                    exit_reason TEXT,
                    -- MFE/MAE for trade quality analysis
                    mfe_pct REAL DEFAULT 0.0,
                    mae_pct REAL DEFAULT 0.0,
                    time_to_mfe_minutes INTEGER DEFAULT 0,
                    time_to_mae_minutes INTEGER DEFAULT 0,
                    -- Entry conditions (JSON) for pattern learning
                    entry_conditions TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Pending outcomes table (tracks what needs outcome checking)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS pending_outcomes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_type TEXT NOT NULL,
                    event_id INTEGER NOT NULL,
                    symbol TEXT NOT NULL,
                    check_time TEXT NOT NULL,
                    check_type TEXT NOT NULL,
                    completed INTEGER DEFAULT 0,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Discord alerts table (all alerts sent to Discord)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS discord_alerts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    alert_type TEXT NOT NULL,
                    channel TEXT NOT NULL,
                    symbol TEXT,
                    timestamp TEXT NOT NULL,
                    direction TEXT,
                    entry_price REAL,
                    stop_loss REAL,
                    take_profit REAL,
                    confidence REAL,
                    reasoning TEXT,
                    pnl_pct REAL,
                    pnl_usd REAL,
                    liquidation_size REAL,
                    -- Trend context at time of alert
                    trend_direction TEXT,
                    trend_strength REAL,
                    ema_position TEXT,
                    rsi_value REAL,
                    patterns_detected TEXT,
                    trendline_signal TEXT,
                    metadata TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Price predictions table (for accuracy tracking)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS price_predictions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol TEXT NOT NULL,
                    timeframe TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    current_price REAL NOT NULL,
                    predicted_price REAL NOT NULL,
                    predicted_direction TEXT NOT NULL,
                    confidence REAL,
                    predicted_pct_change REAL,
                    reasoning TEXT,
                    patterns_used TEXT,
                    chart_id INTEGER,
                    -- Trend context at time of prediction
                    trend_direction TEXT,
                    trend_strength REAL,
                    ema_position TEXT,
                    rsi_value REAL,
                    macd_histogram REAL,
                    volatility_regime TEXT,
                    -- Outcome tracking (filled after 5 candles)
                    actual_price REAL,
                    actual_direction TEXT,
                    actual_pct_change REAL,
                    prediction_error_pct REAL,
                    direction_correct INTEGER,
                    outcome_checked INTEGER DEFAULT 0,
                    outcome_timestamp TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # =========== MIGRATION: Add missing columns to existing tables ===========
            # chart_signals migration
            chart_cols = {row[1] for row in conn.execute("PRAGMA table_info(chart_signals)").fetchall()}
            if "trend_direction" not in chart_cols:
                conn.execute("ALTER TABLE chart_signals ADD COLUMN trend_direction TEXT")
            if "trend_strength" not in chart_cols:
                conn.execute("ALTER TABLE chart_signals ADD COLUMN trend_strength REAL")
            if "ema_position" not in chart_cols:
                conn.execute("ALTER TABLE chart_signals ADD COLUMN ema_position TEXT")
            if "rsi_value" not in chart_cols:
                conn.execute("ALTER TABLE chart_signals ADD COLUMN rsi_value REAL")
            if "macd_histogram" not in chart_cols:
                conn.execute("ALTER TABLE chart_signals ADD COLUMN macd_histogram REAL")
            if "patterns_detected" not in chart_cols:
                conn.execute("ALTER TABLE chart_signals ADD COLUMN patterns_detected TEXT")
            if "volume_trend" not in chart_cols:
                conn.execute("ALTER TABLE chart_signals ADD COLUMN volume_trend TEXT")
            if "volatility_regime" not in chart_cols:
                conn.execute("ALTER TABLE chart_signals ADD COLUMN volatility_regime TEXT")

            # discord_alerts migration
            discord_cols = {row[1] for row in conn.execute("PRAGMA table_info(discord_alerts)").fetchall()}
            if "trend_direction" not in discord_cols:
                conn.execute("ALTER TABLE discord_alerts ADD COLUMN trend_direction TEXT")
            if "trend_strength" not in discord_cols:
                conn.execute("ALTER TABLE discord_alerts ADD COLUMN trend_strength REAL")
            if "ema_position" not in discord_cols:
                conn.execute("ALTER TABLE discord_alerts ADD COLUMN ema_position TEXT")
            if "rsi_value" not in discord_cols:
                conn.execute("ALTER TABLE discord_alerts ADD COLUMN rsi_value REAL")
            if "patterns_detected" not in discord_cols:
                conn.execute("ALTER TABLE discord_alerts ADD COLUMN patterns_detected TEXT")
            if "trendline_signal" not in discord_cols:
                conn.execute("ALTER TABLE discord_alerts ADD COLUMN trendline_signal TEXT")

            # price_predictions migration
            pred_cols = {row[1] for row in conn.execute("PRAGMA table_info(price_predictions)").fetchall()}
            if "trend_direction" not in pred_cols:
                conn.execute("ALTER TABLE price_predictions ADD COLUMN trend_direction TEXT")
            if "trend_strength" not in pred_cols:
                conn.execute("ALTER TABLE price_predictions ADD COLUMN trend_strength REAL")
            if "ema_position" not in pred_cols:
                conn.execute("ALTER TABLE price_predictions ADD COLUMN ema_position TEXT")
            if "rsi_value" not in pred_cols:
                conn.execute("ALTER TABLE price_predictions ADD COLUMN rsi_value REAL")
            if "macd_histogram" not in pred_cols:
                conn.execute("ALTER TABLE price_predictions ADD COLUMN macd_histogram REAL")
            if "volatility_regime" not in pred_cols:
                conn.execute("ALTER TABLE price_predictions ADD COLUMN volatility_regime TEXT")

            # Create indexes for fast queries
            conn.execute("CREATE INDEX IF NOT EXISTS idx_whale_symbol ON whale_events(symbol)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_whale_timestamp ON whale_events(timestamp)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_whale_profitable ON whale_events(profitable_follow)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_chart_symbol ON chart_signals(symbol)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_chart_timestamp ON chart_signals(timestamp)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_chart_outcome ON chart_signals(outcome_checked)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_sr_symbol ON sr_events(symbol)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_charts_symbol ON charts(symbol, timeframe)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_trade_symbol ON trade_signals(symbol)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_pending ON pending_outcomes(completed, check_time)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_discord_type ON discord_alerts(alert_type)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_discord_symbol ON discord_alerts(symbol)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_discord_timestamp ON discord_alerts(timestamp)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_predictions_symbol ON price_predictions(symbol, timeframe)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_predictions_unchecked ON price_predictions(outcome_checked, timestamp)")
            # Trend indexes for learning
            conn.execute("CREATE INDEX IF NOT EXISTS idx_chart_trend ON chart_signals(trend_direction, trend_strength)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_discord_trend ON discord_alerts(trend_direction)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_predictions_trend ON price_predictions(trend_direction, trend_strength)")
            # Completed trades indexes
            conn.execute("CREATE INDEX IF NOT EXISTS idx_completed_symbol ON completed_trades(symbol)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_completed_side ON completed_trades(side)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_completed_entry_time ON completed_trades(entry_time)")

    # =========================================================================
    # WHALE EVENTS
    # =========================================================================

    def save_whale_event(self, whale: str, symbol: str, action: str, side: str,
                         size: float = None, entry_price: float = None,
                         leverage: float = None, notional_usd: float = None,
                         timestamp: str = None) -> int:
        """Save a whale event. Returns the event ID."""
        timestamp = timestamp or datetime.utcnow().isoformat()

        with self._get_conn() as conn:
            cursor = conn.execute("""
                INSERT INTO whale_events
                (timestamp, whale, symbol, action, side, size, entry_price, leverage, notional_usd)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (timestamp, whale, symbol, action, side, size, entry_price, leverage, notional_usd))
            event_id = cursor.lastrowid

            # Schedule outcome checks
            check_5m = (datetime.fromisoformat(timestamp) + timedelta(minutes=5)).isoformat()
            check_1h = (datetime.fromisoformat(timestamp) + timedelta(hours=1)).isoformat()

            conn.execute("""
                INSERT INTO pending_outcomes (event_type, event_id, symbol, check_time, check_type)
                VALUES (?, ?, ?, ?, ?)
            """, ("whale", event_id, symbol, check_5m, "5m"))
            conn.execute("""
                INSERT INTO pending_outcomes (event_type, event_id, symbol, check_time, check_type)
                VALUES (?, ?, ?, ?, ?)
            """, ("whale", event_id, symbol, check_1h, "1h"))

            logger.info(f"📀 Saved whale event: {whale} {action} {side} {symbol}")
            return event_id

    def update_whale_outcome(self, event_id: int, price_after_5m: float = None,
                             price_after_1h: float = None, profitable_follow: bool = None):
        """Update whale event with outcome data."""
        updates = []
        values = []

        if price_after_5m is not None:
            updates.append("price_after_5m = ?")
            values.append(price_after_5m)
        if price_after_1h is not None:
            updates.append("price_after_1h = ?")
            values.append(price_after_1h)
        if profitable_follow is not None:
            updates.append("profitable_follow = ?")
            values.append(1 if profitable_follow else 0)

        if updates:
            values.append(event_id)
            with self._get_conn() as conn:
                conn.execute(f"UPDATE whale_events SET {', '.join(updates)} WHERE id = ?", values)

    def get_whale_events(self, symbol: str = None, limit: int = 1000,
                         profitable_only: bool = False) -> List[Dict]:
        """Get whale events with optional filters."""
        query = "SELECT * FROM whale_events WHERE 1=1"
        params = []

        if symbol:
            query += " AND symbol = ?"
            params.append(symbol)
        if profitable_only:
            query += " AND profitable_follow = 1"

        query += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)

        with self._get_conn() as conn:
            rows = conn.execute(query, params).fetchall()
            return [dict(row) for row in rows]

    # =========================================================================
    # CHART SIGNALS
    # =========================================================================

    def save_chart_signal(self, signal_id: str, signal_type: str, symbol: str,
                          price: float, direction: str, confidence: float = 0.5,
                          support_levels: List[float] = None,
                          resistance_levels: List[float] = None,
                          asc_support_price: float = None,
                          desc_resistance_price: float = None,
                          trendline_signal: str = None,
                          deepseek_bias: str = None,
                          deepseek_entry: str = None,
                          deepseek_stop: str = None,
                          deepseek_target: str = None,
                          # Trend context fields
                          trend_direction: str = None,
                          trend_strength: float = None,
                          ema_position: str = None,
                          rsi_value: float = None,
                          macd_histogram: float = None,
                          patterns_detected: List[str] = None,
                          volume_trend: str = None,
                          volatility_regime: str = None,
                          timestamp: str = None) -> int:
        """Save a chart signal with trend context. Returns the signal ID."""
        timestamp = timestamp or datetime.utcnow().isoformat()

        with self._get_conn() as conn:
            cursor = conn.execute("""
                INSERT OR REPLACE INTO chart_signals
                (signal_id, signal_type, symbol, timestamp, price_at_signal, direction,
                 confidence, support_levels, resistance_levels, asc_support_price,
                 desc_resistance_price, trendline_signal, deepseek_bias, deepseek_entry,
                 deepseek_stop, deepseek_target, trend_direction, trend_strength,
                 ema_position, rsi_value, macd_histogram, patterns_detected,
                 volume_trend, volatility_regime)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (signal_id, signal_type, symbol, timestamp, price, direction,
                  confidence, json.dumps(support_levels or []),
                  json.dumps(resistance_levels or []), asc_support_price,
                  desc_resistance_price, trendline_signal, deepseek_bias,
                  deepseek_entry, deepseek_stop, deepseek_target,
                  trend_direction, trend_strength, ema_position, rsi_value,
                  macd_histogram, json.dumps(patterns_detected or []),
                  volume_trend, volatility_regime))

            row_id = cursor.lastrowid

            # Schedule outcome checks (1h, 4h, 24h)
            base_time = datetime.fromisoformat(timestamp)
            for check_type, delta in [("1h", timedelta(hours=1)),
                                       ("4h", timedelta(hours=4)),
                                       ("24h", timedelta(hours=24))]:
                check_time = (base_time + delta).isoformat()
                conn.execute("""
                    INSERT INTO pending_outcomes (event_type, event_id, symbol, check_time, check_type)
                    VALUES (?, ?, ?, ?, ?)
                """, ("chart_signal", row_id, symbol, check_time, check_type))

            logger.info(f"📀 Saved chart signal: {symbol} {signal_type} {direction}")
            return row_id

    def update_chart_signal_outcome(self, signal_id: str, price_1h: float = None,
                                    price_4h: float = None, price_24h: float = None,
                                    outcome_direction: str = None):
        """Update chart signal with outcome data."""
        with self._get_conn() as conn:
            # Get original signal
            row = conn.execute(
                "SELECT price_at_signal, direction FROM chart_signals WHERE signal_id = ?",
                (signal_id,)
            ).fetchone()

            if not row:
                return

            original_price = row["price_at_signal"]
            original_direction = row["direction"]

            updates = ["outcome_checked = 1"]
            values = []

            if price_1h is not None:
                updates.append("price_1h = ?")
                values.append(price_1h)
                pct = (price_1h - original_price) / original_price * 100
                updates.append("outcome_pct_1h = ?")
                values.append(pct)

            if price_4h is not None:
                updates.append("price_4h = ?")
                values.append(price_4h)
                pct = (price_4h - original_price) / original_price * 100
                updates.append("outcome_pct_4h = ?")
                values.append(pct)

            if price_24h is not None:
                updates.append("price_24h = ?")
                values.append(price_24h)
                pct = (price_24h - original_price) / original_price * 100
                updates.append("outcome_pct_24h = ?")
                values.append(pct)

                # Determine if prediction was correct based on 24h outcome
                if original_direction == "bullish":
                    outcome = "correct" if pct > 0.5 else "incorrect" if pct < -0.5 else "neutral"
                elif original_direction == "bearish":
                    outcome = "correct" if pct < -0.5 else "incorrect" if pct > 0.5 else "neutral"
                else:
                    outcome = "neutral"
                updates.append("outcome_direction = ?")
                values.append(outcome)

            values.append(signal_id)
            conn.execute(f"UPDATE chart_signals SET {', '.join(updates)} WHERE signal_id = ?", values)

    def get_chart_signals(self, symbol: str = None, signal_type: str = None,
                          with_outcomes: bool = False, limit: int = 1000) -> List[Dict]:
        """Get chart signals with optional filters."""
        query = "SELECT * FROM chart_signals WHERE 1=1"
        params = []

        if symbol:
            query += " AND symbol = ?"
            params.append(symbol)
        if signal_type:
            query += " AND signal_type = ?"
            params.append(signal_type)
        if with_outcomes:
            query += " AND outcome_checked = 1"

        query += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)

        with self._get_conn() as conn:
            rows = conn.execute(query, params).fetchall()
            results = []
            for row in rows:
                d = dict(row)
                # Parse JSON fields
                d["support_levels"] = json.loads(d.get("support_levels") or "[]")
                d["resistance_levels"] = json.loads(d.get("resistance_levels") or "[]")
                results.append(d)
            return results

    # =========================================================================
    # CHARTS (Images)
    # =========================================================================

    def save_chart(self, symbol: str, timeframe: str, price: float,
                   image_data: bytes, signal: str = None, direction: str = None,
                   analysis_text: str = None, timestamp: str = None) -> int:
        """Save a chart image. Returns the chart ID."""
        timestamp = timestamp or datetime.utcnow().isoformat()

        with self._get_conn() as conn:
            cursor = conn.execute("""
                INSERT INTO charts
                (symbol, timeframe, timestamp, price, signal, direction, image_data, analysis_text)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (symbol, timeframe, timestamp, price, signal, direction, image_data, analysis_text))

            logger.info(f"📀 Saved chart: {symbol} {timeframe}")
            return cursor.lastrowid

    def get_charts(self, symbol: str = None, timeframe: str = None,
                   limit: int = 100, include_images: bool = False) -> List[Dict]:
        """Get charts with optional filters."""
        cols = "id, symbol, timeframe, timestamp, price, signal, direction, analysis_text, created_at"
        if include_images:
            cols = "*"

        query = f"SELECT {cols} FROM charts WHERE 1=1"
        params = []

        if symbol:
            query += " AND symbol = ?"
            params.append(symbol)
        if timeframe:
            query += " AND timeframe = ?"
            params.append(timeframe)

        query += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)

        with self._get_conn() as conn:
            rows = conn.execute(query, params).fetchall()
            return [dict(row) for row in rows]

    def get_chart_image(self, chart_id: int) -> Optional[bytes]:
        """Get chart image by ID."""
        with self._get_conn() as conn:
            row = conn.execute("SELECT image_data FROM charts WHERE id = ?", (chart_id,)).fetchone()
            return row["image_data"] if row else None

    # =========================================================================
    # S/R EVENTS
    # =========================================================================

    def save_sr_event(self, symbol: str, price: float, level: float,
                      direction: str, break_pct: float = None,
                      timestamp: str = None) -> int:
        """Save an S/R breakout event. Returns the event ID."""
        timestamp = timestamp or datetime.utcnow().isoformat()

        with self._get_conn() as conn:
            cursor = conn.execute("""
                INSERT INTO sr_events
                (timestamp, symbol, price_at_event, level, direction, break_pct)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (timestamp, symbol, price, level, direction, break_pct))

            event_id = cursor.lastrowid

            # Schedule outcome checks
            base_time = datetime.fromisoformat(timestamp)
            for check_type, delta in [("5m", timedelta(minutes=5)),
                                       ("15m", timedelta(minutes=15)),
                                       ("1h", timedelta(hours=1))]:
                check_time = (base_time + delta).isoformat()
                conn.execute("""
                    INSERT INTO pending_outcomes (event_type, event_id, symbol, check_time, check_type)
                    VALUES (?, ?, ?, ?, ?)
                """, ("sr_event", event_id, symbol, check_time, check_type))

            logger.info(f"📀 Saved S/R event: {symbol} {direction} @ ${level:,.0f}")
            return event_id

    def update_sr_outcome(self, event_id: int, price_after_5m: float = None,
                          price_after_15m: float = None, price_after_1h: float = None):
        """Update S/R event with outcome data."""
        with self._get_conn() as conn:
            # Get original event
            row = conn.execute(
                "SELECT price_at_event, direction FROM sr_events WHERE id = ?", (event_id,)
            ).fetchone()

            if not row:
                return

            original_price = row["price_at_event"]
            direction = row["direction"]

            updates = []
            values = []

            if price_after_5m is not None:
                updates.append("price_after_5m = ?")
                values.append(price_after_5m)
            if price_after_15m is not None:
                updates.append("price_after_15m = ?")
                values.append(price_after_15m)
            if price_after_1h is not None:
                updates.append("price_after_1h = ?")
                values.append(price_after_1h)

                # Calculate if breakout continued
                if direction == "bullish":
                    continued = price_after_1h > original_price
                else:
                    continued = price_after_1h < original_price
                updates.append("continued = ?")
                values.append(1 if continued else 0)

                reversal_pct = (price_after_1h - original_price) / original_price * 100
                updates.append("reversal_pct = ?")
                values.append(reversal_pct)

            if updates:
                values.append(event_id)
                conn.execute(f"UPDATE sr_events SET {', '.join(updates)} WHERE id = ?", values)

    # =========================================================================
    # TRADE SIGNALS
    # =========================================================================

    def save_trade_signal(self, symbol: str, side: str, entry_price: float,
                          confidence: float = 0.5, support_levels: List[float] = None,
                          resistance_levels: List[float] = None,
                          stop_loss: float = None, take_profit: float = None,
                          metadata: Dict = None, timestamp: str = None) -> int:
        """Save a trade signal. Returns the signal ID."""
        timestamp = timestamp or datetime.utcnow().isoformat()
        signal_id = f"{symbol}_{side}_{timestamp.replace(':', '').replace('-', '')}"

        with self._get_conn() as conn:
            cursor = conn.execute("""
                INSERT INTO trade_signals
                (signal_id, symbol, timestamp, side, entry_price, confidence,
                 support_levels, resistance_levels, stop_loss, take_profit, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (signal_id, symbol, timestamp, side, entry_price, confidence,
                  json.dumps(support_levels or []), json.dumps(resistance_levels or []),
                  stop_loss, take_profit, json.dumps(metadata or {})))

            logger.info(f"📀 Saved trade signal: {side.upper()} {symbol} @ ${entry_price:,.2f}")
            return cursor.lastrowid

    def update_trade_result(self, signal_id: str = None, symbol: str = None,
                            exit_price: float = None, pnl_pct: float = None,
                            outcome: str = None):
        """Update trade signal with exit/result data."""
        # Find by signal_id or most recent for symbol
        with self._get_conn() as conn:
            if signal_id:
                query = "SELECT id, entry_price FROM trade_signals WHERE signal_id = ?"
                row = conn.execute(query, (signal_id,)).fetchone()
            elif symbol:
                query = "SELECT id, entry_price, signal_id FROM trade_signals WHERE symbol = ? ORDER BY timestamp DESC LIMIT 1"
                row = conn.execute(query, (symbol,)).fetchone()
                if row:
                    signal_id = row["signal_id"]
            else:
                return

            if not row:
                return

            updates = ["exit_timestamp = ?"]
            values = [datetime.utcnow().isoformat()]

            if exit_price is not None:
                updates.append("exit_price = ?")
                values.append(exit_price)
                if pnl_pct is None:
                    pnl_pct = (exit_price - row["entry_price"]) / row["entry_price"] * 100

            if pnl_pct is not None:
                updates.append("pnl_pct = ?")
                values.append(pnl_pct)
                if outcome is None:
                    outcome = "profit" if pnl_pct > 0 else "loss" if pnl_pct < 0 else "breakeven"

            if outcome:
                updates.append("outcome = ?")
                values.append(outcome)

            values.append(signal_id)
            conn.execute(f"UPDATE trade_signals SET {', '.join(updates)} WHERE signal_id = ?", values)

    def get_recent_trades(self, limit: int = 10, symbol: str = None) -> List[Dict]:
        """Get recent trade signals with outcomes for display.

        Returns list of dicts with: timestamp, symbol, side, price, pnl, outcome
        """
        with self._get_conn() as conn:
            if symbol:
                rows = conn.execute("""
                    SELECT timestamp, symbol, side, entry_price as price,
                           exit_price, pnl_pct as pnl, outcome
                    FROM trade_signals
                    WHERE symbol = ? AND outcome IS NOT NULL
                    ORDER BY timestamp DESC LIMIT ?
                """, (symbol, limit)).fetchall()
            else:
                rows = conn.execute("""
                    SELECT timestamp, symbol, side, entry_price as price,
                           exit_price, pnl_pct as pnl, outcome
                    FROM trade_signals
                    WHERE outcome IS NOT NULL
                    ORDER BY timestamp DESC LIMIT ?
                """, (limit,)).fetchall()
            return [dict(row) for row in rows]

    # =========================================================================
    # COMPLETED TRADES (Full trade records for PerformanceTracker)
    # =========================================================================

    def save_completed_trade(self, symbol: str, side: str, entry_price: float,
                             exit_price: float, size: float, entry_time: str,
                             exit_time: str, pnl_pct: float, pnl_usd: float,
                             exit_reason: str = None, mfe_pct: float = 0.0,
                             mae_pct: float = 0.0, time_to_mfe_minutes: int = 0,
                             time_to_mae_minutes: int = 0,
                             entry_conditions: Dict = None) -> int:
        """Save a completed trade record. Returns the trade ID."""
        with self._get_conn() as conn:
            cursor = conn.execute("""
                INSERT INTO completed_trades
                (symbol, side, entry_price, exit_price, size, entry_time, exit_time,
                 pnl_pct, pnl_usd, exit_reason, mfe_pct, mae_pct, time_to_mfe_minutes,
                 time_to_mae_minutes, entry_conditions)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (symbol, side, entry_price, exit_price, size, entry_time, exit_time,
                  pnl_pct, pnl_usd, exit_reason, mfe_pct, mae_pct, time_to_mfe_minutes,
                  time_to_mae_minutes, json.dumps(entry_conditions) if entry_conditions else None))

            logger.info(f"📀 Saved completed trade: {side.upper()} {symbol} | P&L: {pnl_pct:+.2f}%")
            return cursor.lastrowid

    def get_completed_trades(self, symbol: str = None, limit: int = 1000,
                             days_back: int = None) -> List[Dict]:
        """Get completed trades with optional filters."""
        query = "SELECT * FROM completed_trades WHERE 1=1"
        params = []

        if symbol:
            query += " AND symbol = ?"
            params.append(symbol)

        if days_back:
            cutoff = (datetime.utcnow() - timedelta(days=days_back)).isoformat()
            query += " AND entry_time >= ?"
            params.append(cutoff)

        query += " ORDER BY entry_time DESC LIMIT ?"
        params.append(limit)

        with self._get_conn() as conn:
            rows = conn.execute(query, params).fetchall()
            results = []
            for row in rows:
                d = dict(row)
                # Parse entry_conditions JSON
                if d.get("entry_conditions"):
                    try:
                        d["entry_conditions"] = json.loads(d["entry_conditions"])
                    except:
                        d["entry_conditions"] = None
                results.append(d)
            return results

    def get_completed_trades_count(self) -> int:
        """Get total count of completed trades."""
        with self._get_conn() as conn:
            row = conn.execute("SELECT COUNT(*) as count FROM completed_trades").fetchone()
            return row["count"] if row else 0

    def get_completed_trades_stats(self, symbol: str = None, days_back: int = None) -> Dict:
        """Get aggregate stats for completed trades."""
        query = "SELECT * FROM completed_trades WHERE 1=1"
        params = []

        if symbol:
            query += " AND symbol = ?"
            params.append(symbol)

        if days_back:
            cutoff = (datetime.utcnow() - timedelta(days=days_back)).isoformat()
            query += " AND entry_time >= ?"
            params.append(cutoff)

        with self._get_conn() as conn:
            rows = conn.execute(query, params).fetchall()

            if not rows:
                return {"total": 0, "wins": 0, "losses": 0, "win_rate": 0, "total_pnl_pct": 0}

            trades = [dict(r) for r in rows]
            wins = [t for t in trades if t["pnl_pct"] > 0]
            losses = [t for t in trades if t["pnl_pct"] <= 0]

            return {
                "total": len(trades),
                "wins": len(wins),
                "losses": len(losses),
                "win_rate": len(wins) / len(trades) * 100 if trades else 0,
                "total_pnl_pct": sum(t["pnl_pct"] for t in trades),
                "total_pnl_usd": sum(t["pnl_usd"] for t in trades),
                "avg_win_pct": sum(t["pnl_pct"] for t in wins) / len(wins) if wins else 0,
                "avg_loss_pct": sum(t["pnl_pct"] for t in losses) / len(losses) if losses else 0,
            }

    # =========================================================================
    # OUTCOME TRACKING
    # =========================================================================

    def get_pending_outcomes(self, before_time: str = None) -> List[Dict]:
        """Get pending outcome checks that need processing."""
        before_time = before_time or datetime.utcnow().isoformat()

        with self._get_conn() as conn:
            rows = conn.execute("""
                SELECT * FROM pending_outcomes
                WHERE completed = 0 AND check_time <= ?
                ORDER BY check_time ASC
            """, (before_time,)).fetchall()
            return [dict(row) for row in rows]

    def mark_outcome_complete(self, pending_id: int):
        """Mark a pending outcome check as completed."""
        with self._get_conn() as conn:
            conn.execute("UPDATE pending_outcomes SET completed = 1 WHERE id = ?", (pending_id,))

    def process_pending_outcomes(self, get_price_fn) -> int:
        """Process all pending outcome checks.

        Args:
            get_price_fn: Function that takes symbol and returns current price

        Returns:
            Number of outcomes processed
        """
        pending = self.get_pending_outcomes()
        processed = 0

        for item in pending:
            try:
                symbol = item["symbol"]
                current_price = get_price_fn(symbol)

                if current_price is None:
                    continue

                event_type = item["event_type"]
                event_id = item["event_id"]
                check_type = item["check_type"]

                if event_type == "whale":
                    if check_type == "5m":
                        self.update_whale_outcome(event_id, price_after_5m=current_price)
                    elif check_type == "1h":
                        # Calculate if following would have been profitable
                        with self._get_conn() as conn:
                            row = conn.execute(
                                "SELECT entry_price, side FROM whale_events WHERE id = ?",
                                (event_id,)
                            ).fetchone()
                            if row:
                                entry = row["entry_price"]
                                side = row["side"]
                                if side == "long":
                                    profitable = current_price > entry
                                else:
                                    profitable = current_price < entry
                                self.update_whale_outcome(event_id, price_after_1h=current_price,
                                                          profitable_follow=profitable)

                elif event_type == "chart_signal":
                    with self._get_conn() as conn:
                        row = conn.execute(
                            "SELECT signal_id FROM chart_signals WHERE id = ?", (event_id,)
                        ).fetchone()
                        if row:
                            signal_id = row["signal_id"]
                            if check_type == "1h":
                                self.update_chart_signal_outcome(signal_id, price_1h=current_price)
                            elif check_type == "4h":
                                self.update_chart_signal_outcome(signal_id, price_4h=current_price)
                            elif check_type == "24h":
                                self.update_chart_signal_outcome(signal_id, price_24h=current_price)

                elif event_type == "sr_event":
                    if check_type == "5m":
                        self.update_sr_outcome(event_id, price_after_5m=current_price)
                    elif check_type == "15m":
                        self.update_sr_outcome(event_id, price_after_15m=current_price)
                    elif check_type == "1h":
                        self.update_sr_outcome(event_id, price_after_1h=current_price)

                self.mark_outcome_complete(item["id"])
                processed += 1

            except Exception as e:
                logger.error(f"Error processing outcome {item}: {e}")

        if processed > 0:
            logger.info(f"📀 Processed {processed} pending outcomes")

        return processed

    # =========================================================================
    # DISCORD ALERTS
    # =========================================================================

    def save_discord_alert(self, alert_type: str, channel: str, symbol: str = None,
                           direction: str = None, entry_price: float = None,
                           stop_loss: float = None, take_profit: float = None,
                           confidence: float = None, reasoning: str = None,
                           pnl_pct: float = None, pnl_usd: float = None,
                           liquidation_size: float = None,
                           # Trend context fields
                           trend_direction: str = None,
                           trend_strength: float = None,
                           ema_position: str = None,
                           rsi_value: float = None,
                           patterns_detected: List[str] = None,
                           trendline_signal: str = None,
                           metadata: Dict = None,
                           timestamp: str = None) -> int:
        """Save a Discord alert with trend context. Returns the alert ID."""
        timestamp = timestamp or datetime.utcnow().isoformat()

        with self._get_conn() as conn:
            cursor = conn.execute("""
                INSERT INTO discord_alerts
                (alert_type, channel, symbol, timestamp, direction, entry_price,
                 stop_loss, take_profit, confidence, reasoning, pnl_pct, pnl_usd,
                 liquidation_size, trend_direction, trend_strength, ema_position,
                 rsi_value, patterns_detected, trendline_signal, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (alert_type, channel, symbol, timestamp, direction, entry_price,
                  stop_loss, take_profit, confidence, reasoning, pnl_pct, pnl_usd,
                  liquidation_size, trend_direction, trend_strength, ema_position,
                  rsi_value, json.dumps(patterns_detected or []), trendline_signal,
                  json.dumps(metadata or {})))

            logger.debug(f"📀 Saved discord alert: {alert_type} {symbol or ''}")
            return cursor.lastrowid

    def get_discord_alerts(self, alert_type: str = None, symbol: str = None,
                           limit: int = 100) -> List[Dict]:
        """Get discord alerts with optional filters."""
        query = "SELECT * FROM discord_alerts WHERE 1=1"
        params = []

        if alert_type:
            query += " AND alert_type = ?"
            params.append(alert_type)
        if symbol:
            query += " AND symbol = ?"
            params.append(symbol)

        query += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)

        with self._get_conn() as conn:
            rows = conn.execute(query, params).fetchall()
            results = []
            for row in rows:
                d = dict(row)
                d["metadata"] = json.loads(d.get("metadata") or "{}")
                results.append(d)
            return results

    def get_alpha_call_stats(self) -> Dict:
        """Get statistics on alpha calls."""
        with self._get_conn() as conn:
            total = conn.execute(
                "SELECT COUNT(*) FROM discord_alerts WHERE alert_type = 'alpha_call'"
            ).fetchone()[0]

            # Count by direction
            longs = conn.execute(
                "SELECT COUNT(*) FROM discord_alerts WHERE alert_type = 'alpha_call' AND direction = 'long'"
            ).fetchone()[0]
            shorts = conn.execute(
                "SELECT COUNT(*) FROM discord_alerts WHERE alert_type = 'alpha_call' AND direction = 'short'"
            ).fetchone()[0]

            # Count by symbol
            by_symbol = conn.execute("""
                SELECT symbol, COUNT(*) as count
                FROM discord_alerts
                WHERE alert_type = 'alpha_call' AND symbol IS NOT NULL
                GROUP BY symbol
                ORDER BY count DESC
            """).fetchall()

            return {
                "total": total,
                "longs": longs,
                "shorts": shorts,
                "by_symbol": {row["symbol"]: row["count"] for row in by_symbol}
            }

    def update_alpha_call_outcome(self, alert_id: int, outcome: str, pnl_pct: float = None,
                                   pnl_usd: float = None, exit_price: float = None) -> None:
        """Update an alpha call with its outcome (hit_tp, hit_sl, expired, manual_close)."""
        with self._get_conn() as conn:
            conn.execute("""
                UPDATE discord_alerts
                SET pnl_pct = ?, pnl_usd = ?, metadata = json_set(COALESCE(metadata, '{}'),
                    '$.outcome', ?, '$.exit_price', ?, '$.resolved_at', ?)
                WHERE id = ?
            """, (pnl_pct, pnl_usd, outcome, exit_price,
                  datetime.utcnow().isoformat(), alert_id))
            logger.info(f"📊 Alpha call {alert_id} resolved: {outcome} ({pnl_pct:+.2f}%)" if pnl_pct else f"📊 Alpha call {alert_id} resolved: {outcome}")

    def get_pending_alpha_calls(self, symbol: str = None, max_age_hours: int = 24) -> List[Dict]:
        """Get alpha calls that haven't been resolved yet (for outcome tracking)."""
        cutoff = (datetime.utcnow() - timedelta(hours=max_age_hours)).isoformat()
        query = """
            SELECT * FROM discord_alerts
            WHERE alert_type = 'alpha_call'
            AND timestamp > ?
            AND (pnl_pct IS NULL OR pnl_pct = 0)
        """
        params = [cutoff]

        if symbol:
            query += " AND symbol = ?"
            params.append(symbol)

        query += " ORDER BY timestamp DESC"

        with self._get_conn() as conn:
            rows = conn.execute(query, params).fetchall()
            results = []
            for row in rows:
                d = dict(row)
                d["metadata"] = json.loads(d.get("metadata") or "{}")
                results.append(d)
            return results

    def get_alpha_call_performance(self, symbol: str = None, limit: int = 50) -> Dict:
        """Analyze alpha call performance - which patterns/conditions work best."""
        query = """
            SELECT * FROM discord_alerts
            WHERE alert_type = 'alpha_call' AND pnl_pct IS NOT NULL
        """
        params = []

        if symbol:
            query += " AND symbol = ?"
            params.append(symbol)

        query += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)

        with self._get_conn() as conn:
            rows = conn.execute(query, params).fetchall()

            if not rows:
                return {"total": 0, "win_rate": 0, "insights": []}

            alerts = [dict(row) for row in rows]
            wins = [a for a in alerts if (a.get("pnl_pct") or 0) > 0]
            losses = [a for a in alerts if (a.get("pnl_pct") or 0) <= 0]

            # Analyze by trend direction
            trend_stats = {}
            for a in alerts:
                trend = a.get("trend_direction") or "unknown"
                direction = a.get("direction") or "unknown"
                key = f"{direction}_in_{trend}"
                if key not in trend_stats:
                    trend_stats[key] = {"wins": 0, "losses": 0, "total_pnl": 0}
                if (a.get("pnl_pct") or 0) > 0:
                    trend_stats[key]["wins"] += 1
                else:
                    trend_stats[key]["losses"] += 1
                trend_stats[key]["total_pnl"] += a.get("pnl_pct") or 0

            # Generate insights
            insights = []
            for key, stats in trend_stats.items():
                total = stats["wins"] + stats["losses"]
                if total >= 3:  # Need enough samples
                    win_rate = stats["wins"] / total * 100
                    if win_rate >= 60:
                        insights.append(f"✅ {key}: {win_rate:.0f}% win rate ({total} trades)")
                    elif win_rate <= 40:
                        insights.append(f"❌ {key}: {win_rate:.0f}% win rate - AVOID")

            return {
                "total": len(alerts),
                "wins": len(wins),
                "losses": len(losses),
                "win_rate": len(wins) / len(alerts) * 100 if alerts else 0,
                "total_pnl_pct": sum(a.get("pnl_pct") or 0 for a in alerts),
                "trend_stats": trend_stats,
                "insights": insights
            }

    # =========================================================================
    # ML TRAINING DATA EXPORT
    # =========================================================================

    def get_training_data(self, include_charts: bool = False) -> Dict[str, List[Dict]]:
        """Export all data for ML training.

        Returns:
            Dict with keys: whale_events, chart_signals, sr_events, trade_signals
        """
        data = {
            "whale_events": self.get_whale_events(limit=10000),
            "chart_signals": self.get_chart_signals(with_outcomes=True, limit=10000),
            "sr_events": self._get_sr_events_for_training(),
            "trade_signals": self._get_trade_signals_for_training(),
        }

        if include_charts:
            data["charts"] = self.get_charts(limit=1000, include_images=False)

        # Add summary stats
        data["stats"] = {
            "total_whale_events": len(data["whale_events"]),
            "whale_with_outcomes": sum(1 for e in data["whale_events"] if e.get("profitable_follow") is not None),
            "total_chart_signals": len(data["chart_signals"]),
            "total_sr_events": len(data["sr_events"]),
            "total_trade_signals": len(data["trade_signals"]),
        }

        return data

    def _get_sr_events_for_training(self) -> List[Dict]:
        """Get S/R events with outcomes for training."""
        with self._get_conn() as conn:
            rows = conn.execute("""
                SELECT * FROM sr_events WHERE continued IS NOT NULL
                ORDER BY timestamp DESC LIMIT 10000
            """).fetchall()
            return [dict(row) for row in rows]

    def _get_trade_signals_for_training(self) -> List[Dict]:
        """Get trade signals with outcomes for training."""
        with self._get_conn() as conn:
            rows = conn.execute("""
                SELECT * FROM trade_signals WHERE outcome IS NOT NULL
                ORDER BY timestamp DESC LIMIT 10000
            """).fetchall()
            results = []
            for row in rows:
                d = dict(row)
                d["support_levels"] = json.loads(d.get("support_levels") or "[]")
                d["resistance_levels"] = json.loads(d.get("resistance_levels") or "[]")
                d["metadata"] = json.loads(d.get("metadata") or "{}")
                results.append(d)
            return results

    def get_signal_accuracy_stats(self) -> Dict[str, Any]:
        """Get accuracy statistics for signals."""
        with self._get_conn() as conn:
            stats = {}

            # Chart signal accuracy
            chart_total = conn.execute(
                "SELECT COUNT(*) as cnt FROM chart_signals WHERE outcome_direction IS NOT NULL"
            ).fetchone()["cnt"]
            chart_correct = conn.execute(
                "SELECT COUNT(*) as cnt FROM chart_signals WHERE outcome_direction = 'correct'"
            ).fetchone()["cnt"]
            stats["chart_signals"] = {
                "total": chart_total,
                "correct": chart_correct,
                "accuracy": chart_correct / chart_total if chart_total > 0 else 0
            }

            # Whale follow accuracy
            whale_total = conn.execute(
                "SELECT COUNT(*) as cnt FROM whale_events WHERE profitable_follow IS NOT NULL"
            ).fetchone()["cnt"]
            whale_profitable = conn.execute(
                "SELECT COUNT(*) as cnt FROM whale_events WHERE profitable_follow = 1"
            ).fetchone()["cnt"]
            stats["whale_follow"] = {
                "total": whale_total,
                "profitable": whale_profitable,
                "accuracy": whale_profitable / whale_total if whale_total > 0 else 0
            }

            # S/R continuation accuracy
            sr_total = conn.execute(
                "SELECT COUNT(*) as cnt FROM sr_events WHERE continued IS NOT NULL"
            ).fetchone()["cnt"]
            sr_continued = conn.execute(
                "SELECT COUNT(*) as cnt FROM sr_events WHERE continued = 1"
            ).fetchone()["cnt"]
            stats["sr_breakouts"] = {
                "total": sr_total,
                "continued": sr_continued,
                "continuation_rate": sr_continued / sr_total if sr_total > 0 else 0
            }

            # Trade outcome accuracy
            trade_total = conn.execute(
                "SELECT COUNT(*) as cnt FROM trade_signals WHERE outcome IS NOT NULL"
            ).fetchone()["cnt"]
            trade_profit = conn.execute(
                "SELECT COUNT(*) as cnt FROM trade_signals WHERE outcome = 'profit'"
            ).fetchone()["cnt"]
            stats["trades"] = {
                "total": trade_total,
                "profitable": trade_profit,
                "win_rate": trade_profit / trade_total if trade_total > 0 else 0
            }

            return stats

    # =========================================================================
    # DECISION INTELLIGENCE (used by trading bot for smarter decisions)
    # =========================================================================

    def get_whale_accuracy(self, whale_id: str = None) -> Dict[str, Any]:
        """Get historical accuracy for whale follows.

        Args:
            whale_id: Specific whale ID, or None for all whales

        Returns:
            Dict with win_rate, total_trades, avg_profit, and per-symbol breakdown
        """
        with self._get_conn() as conn:
            if whale_id:
                # Specific whale
                rows = conn.execute("""
                    SELECT
                        COUNT(*) as total,
                        SUM(CASE WHEN profitable_follow = 1 THEN 1 ELSE 0 END) as wins,
                        AVG(CASE WHEN price_after_1h IS NOT NULL AND entry_price > 0
                            THEN (price_after_1h - entry_price) / entry_price * 100
                            ELSE NULL END) as avg_pct_1h
                    FROM whale_events
                    WHERE whale = ? AND action = 'opened' AND profitable_follow IS NOT NULL
                """, (whale_id,)).fetchone()
            else:
                # All whales
                rows = conn.execute("""
                    SELECT
                        COUNT(*) as total,
                        SUM(CASE WHEN profitable_follow = 1 THEN 1 ELSE 0 END) as wins,
                        AVG(CASE WHEN price_after_1h IS NOT NULL AND entry_price > 0
                            THEN (price_after_1h - entry_price) / entry_price * 100
                            ELSE NULL END) as avg_pct_1h
                    FROM whale_events
                    WHERE action = 'opened' AND profitable_follow IS NOT NULL
                """).fetchone()

            total = rows["total"] or 0
            wins = rows["wins"] or 0

            result = {
                "whale_id": whale_id or "all",
                "total_trades": total,
                "wins": wins,
                "win_rate": wins / total if total > 0 else 0.5,  # Default 50% if no data
                "avg_pct_1h": rows["avg_pct_1h"] or 0,
                "confidence_multiplier": self._calculate_confidence_multiplier(wins, total)
            }

            # Per-symbol breakdown for this whale
            if whale_id:
                symbol_rows = conn.execute("""
                    SELECT symbol,
                        COUNT(*) as total,
                        SUM(CASE WHEN profitable_follow = 1 THEN 1 ELSE 0 END) as wins
                    FROM whale_events
                    WHERE whale = ? AND action = 'opened' AND profitable_follow IS NOT NULL
                    GROUP BY symbol
                """, (whale_id,)).fetchall()
                result["by_symbol"] = {
                    row["symbol"]: {
                        "total": row["total"],
                        "wins": row["wins"],
                        "win_rate": row["wins"] / row["total"] if row["total"] > 0 else 0.5
                    }
                    for row in symbol_rows
                }

            return result

    def get_symbol_accuracy(self, symbol: str) -> Dict[str, Any]:
        """Get historical trading accuracy for a specific symbol.

        Returns win rates from trades, whale follows, and chart signals for this symbol.
        """
        with self._get_conn() as conn:
            # Trade signals for this symbol
            trade_row = conn.execute("""
                SELECT
                    COUNT(*) as total,
                    SUM(CASE WHEN outcome = 'profit' THEN 1 ELSE 0 END) as wins,
                    AVG(pnl_pct) as avg_pnl
                FROM trade_signals
                WHERE symbol = ? AND outcome IS NOT NULL
            """, (symbol,)).fetchone()

            # Whale follows for this symbol
            whale_row = conn.execute("""
                SELECT
                    COUNT(*) as total,
                    SUM(CASE WHEN profitable_follow = 1 THEN 1 ELSE 0 END) as wins
                FROM whale_events
                WHERE symbol = ? AND action = 'opened' AND profitable_follow IS NOT NULL
            """, (symbol,)).fetchone()

            # Chart signals for this symbol
            chart_row = conn.execute("""
                SELECT
                    COUNT(*) as total,
                    SUM(CASE WHEN outcome_direction = 'correct' THEN 1 ELSE 0 END) as wins
                FROM chart_signals
                WHERE symbol = ? AND outcome_direction IS NOT NULL
            """, (symbol,)).fetchone()

            # Calculate combined score
            total_samples = (trade_row["total"] or 0) + (whale_row["total"] or 0) + (chart_row["total"] or 0)
            total_wins = (trade_row["wins"] or 0) + (whale_row["wins"] or 0) + (chart_row["wins"] or 0)

            return {
                "symbol": symbol,
                "overall": {
                    "total": total_samples,
                    "wins": total_wins,
                    "win_rate": total_wins / total_samples if total_samples > 0 else 0.5,
                    "confidence_multiplier": self._calculate_confidence_multiplier(total_wins, total_samples)
                },
                "trades": {
                    "total": trade_row["total"] or 0,
                    "wins": trade_row["wins"] or 0,
                    "win_rate": (trade_row["wins"] or 0) / trade_row["total"] if trade_row["total"] else 0.5,
                    "avg_pnl": trade_row["avg_pnl"] or 0
                },
                "whale_follows": {
                    "total": whale_row["total"] or 0,
                    "wins": whale_row["wins"] or 0,
                    "win_rate": (whale_row["wins"] or 0) / whale_row["total"] if whale_row["total"] else 0.5
                },
                "chart_signals": {
                    "total": chart_row["total"] or 0,
                    "wins": chart_row["wins"] or 0,
                    "win_rate": (chart_row["wins"] or 0) / chart_row["total"] if chart_row["total"] else 0.5
                }
            }

    def get_chart_signal_accuracy(self, signal_type: str = None, direction: str = None,
                                   symbol: str = None) -> Dict[str, Any]:
        """Get historical accuracy for chart signals.

        Args:
            signal_type: e.g., 'chart_5m', 'chart_daily'
            direction: 'bullish' or 'bearish'
            symbol: Specific symbol or None for all

        Returns:
            Win rate and confidence multiplier for similar signals
        """
        with self._get_conn() as conn:
            query = """
                SELECT
                    COUNT(*) as total,
                    SUM(CASE WHEN outcome_direction = 'correct' THEN 1 ELSE 0 END) as wins,
                    AVG(outcome_pct_1h) as avg_pct_1h,
                    AVG(outcome_pct_4h) as avg_pct_4h
                FROM chart_signals
                WHERE outcome_direction IS NOT NULL
            """
            params = []

            if signal_type:
                query += " AND signal_type = ?"
                params.append(signal_type)
            if direction:
                query += " AND direction = ?"
                params.append(direction)
            if symbol:
                query += " AND symbol = ?"
                params.append(symbol)

            row = conn.execute(query, params).fetchone()

            total = row["total"] or 0
            wins = row["wins"] or 0

            return {
                "signal_type": signal_type or "all",
                "direction": direction or "all",
                "symbol": symbol or "all",
                "total": total,
                "wins": wins,
                "win_rate": wins / total if total > 0 else 0.5,
                "avg_pct_1h": row["avg_pct_1h"] or 0,
                "avg_pct_4h": row["avg_pct_4h"] or 0,
                "confidence_multiplier": self._calculate_confidence_multiplier(wins, total)
            }

    def _calculate_confidence_multiplier(self, wins: int, total: int) -> float:
        """Calculate a confidence multiplier based on historical performance.

        Uses Bayesian-style adjustment:
        - With few samples, stay close to 1.0 (neutral)
        - With many samples, adjust more aggressively based on win rate

        Returns:
            Multiplier between 0.5 (halve confidence) and 1.5 (boost 50%)
        """
        if total < 5:
            # Not enough data, stay neutral
            return 1.0

        win_rate = wins / total

        # How much to trust the data (more samples = more trust)
        # Caps at 20 samples for full trust
        trust_factor = min(total / 20, 1.0)

        # Calculate adjustment from 50% baseline
        # win_rate of 70% -> +0.2 adjustment
        # win_rate of 30% -> -0.2 adjustment
        adjustment = (win_rate - 0.5) * trust_factor

        # Scale to multiplier range [0.5, 1.5]
        multiplier = 1.0 + adjustment

        return max(0.5, min(1.5, multiplier))

    def get_best_performing_symbols(self, limit: int = 10) -> List[Dict]:
        """Get symbols ranked by historical performance.

        Returns list of symbols with their win rates, useful for
        prioritizing which symbols to trade.
        """
        with self._get_conn() as conn:
            # Combine data from trades and whale follows
            rows = conn.execute("""
                SELECT symbol,
                    SUM(total) as total,
                    SUM(wins) as wins
                FROM (
                    SELECT symbol,
                        COUNT(*) as total,
                        SUM(CASE WHEN outcome = 'profit' THEN 1 ELSE 0 END) as wins
                    FROM trade_signals
                    WHERE outcome IS NOT NULL
                    GROUP BY symbol

                    UNION ALL

                    SELECT symbol,
                        COUNT(*) as total,
                        SUM(CASE WHEN profitable_follow = 1 THEN 1 ELSE 0 END) as wins
                    FROM whale_events
                    WHERE action = 'opened' AND profitable_follow IS NOT NULL
                    GROUP BY symbol
                )
                GROUP BY symbol
                HAVING total >= 3
                ORDER BY (CAST(wins AS FLOAT) / total) DESC
                LIMIT ?
            """, (limit,)).fetchall()

            return [
                {
                    "symbol": row["symbol"],
                    "total": row["total"],
                    "wins": row["wins"],
                    "win_rate": row["wins"] / row["total"] if row["total"] > 0 else 0,
                    "confidence_multiplier": self._calculate_confidence_multiplier(row["wins"], row["total"])
                }
                for row in rows
            ]

    # =========================================================================
    # DEEPSEEK LEARNING CONTEXT
    # =========================================================================

    def get_deepseek_accuracy(self, symbol: str = None, days: int = 30) -> Dict[str, Any]:
        """Get DeepSeek-specific accuracy for building smarter prompts.

        Returns detailed breakdown of when DeepSeek was right vs wrong,
        which can be fed back into prompts to help it self-correct.
        """
        cutoff = (datetime.utcnow() - timedelta(days=days)).isoformat()

        with self._get_conn() as conn:
            # Base query for signals where DeepSeek gave a bias
            base_where = "WHERE deepseek_bias IS NOT NULL AND deepseek_bias != 'NEUTRAL' AND outcome_direction IS NOT NULL AND timestamp >= ?"
            params = [cutoff]

            if symbol:
                base_where += " AND symbol = ?"
                params.append(symbol)

            # Overall DeepSeek accuracy
            overall = conn.execute(f"""
                SELECT
                    COUNT(*) as total,
                    SUM(CASE WHEN
                        (deepseek_bias = 'LONG' AND outcome_direction = 'correct' AND direction = 'bullish')
                        OR (deepseek_bias = 'SHORT' AND outcome_direction = 'correct' AND direction = 'bearish')
                        THEN 1 ELSE 0 END) as ds_correct,
                    SUM(CASE WHEN
                        (deepseek_bias = 'LONG' AND outcome_direction = 'incorrect')
                        OR (deepseek_bias = 'SHORT' AND outcome_direction = 'incorrect')
                        THEN 1 ELSE 0 END) as ds_incorrect
                FROM chart_signals
                {base_where}
            """, params).fetchone()

            # By symbol breakdown
            symbol_query = f"""
                SELECT symbol,
                    COUNT(*) as total,
                    SUM(CASE WHEN outcome_direction = 'correct' THEN 1 ELSE 0 END) as correct,
                    deepseek_bias,
                    AVG(outcome_pct_4h) as avg_move
                FROM chart_signals
                {base_where}
                GROUP BY symbol, deepseek_bias
                ORDER BY symbol, deepseek_bias
            """
            symbol_rows = conn.execute(symbol_query, params).fetchall()

            # Recent misses (last 10 wrong predictions)
            misses = conn.execute(f"""
                SELECT symbol, deepseek_bias, direction, outcome_pct_4h, timestamp,
                       price_at_signal, trendline_signal
                FROM chart_signals
                {base_where} AND outcome_direction = 'incorrect'
                ORDER BY timestamp DESC LIMIT 10
            """, params).fetchall()

            # Recent wins (last 10 correct predictions)
            wins = conn.execute(f"""
                SELECT symbol, deepseek_bias, direction, outcome_pct_4h, timestamp,
                       price_at_signal, trendline_signal
                FROM chart_signals
                {base_where} AND outcome_direction = 'correct'
                ORDER BY timestamp DESC LIMIT 10
            """, params).fetchall()

            total = overall["total"] or 0
            ds_correct = overall["ds_correct"] or 0
            ds_incorrect = overall["ds_incorrect"] or 0

            return {
                "total_predictions": total,
                "correct": ds_correct,
                "incorrect": ds_incorrect,
                "accuracy_pct": (ds_correct / max(1, ds_correct + ds_incorrect)) * 100,
                "by_symbol": [dict(r) for r in symbol_rows],
                "recent_misses": [dict(r) for r in misses],
                "recent_wins": [dict(r) for r in wins],
                "needs_improvement": ds_correct < ds_incorrect if total >= 5 else False
            }

    def get_deepseek_prompt_context(self, symbol: str, days: int = 14) -> str:
        """Build context string for DeepSeek prompts based on historical performance.

        This creates a learning context that can be prepended to prompts to help
        DeepSeek make better predictions based on what has worked.
        """
        stats = self.get_deepseek_accuracy(symbol, days)

        if stats["total_predictions"] < 3:
            return ""  # Not enough data yet

        context_lines = []

        # Overall performance
        context_lines.append(f"=== YOUR RECENT PERFORMANCE ({days}d) ===")
        context_lines.append(f"Accuracy: {stats['accuracy_pct']:.0f}% ({stats['correct']}/{stats['correct']+stats['incorrect']})")

        if stats['accuracy_pct'] < 50:
            context_lines.append("⚠️ Your recent calls are below 50%. Be more selective and conservative.")
        elif stats['accuracy_pct'] > 65:
            context_lines.append("✅ Your recent calls are performing well. Maintain your approach.")

        # Recent misses - what to avoid
        if stats['recent_misses']:
            context_lines.append("\n=== RECENT MISSES (learn from these) ===")
            for miss in stats['recent_misses'][:5]:
                move = miss.get('outcome_pct_4h', 0)
                context_lines.append(
                    f"- {miss['symbol']}: Called {miss['deepseek_bias']} but moved {move:+.2f}% "
                    f"(trendline: {miss.get('trendline_signal', 'unknown')})"
                )

        # Recent wins - what's working
        if stats['recent_wins']:
            context_lines.append("\n=== RECENT WINS (patterns that work) ===")
            for win in stats['recent_wins'][:5]:
                move = win.get('outcome_pct_4h', 0)
                context_lines.append(
                    f"- {win['symbol']}: Called {win['deepseek_bias']} → moved {move:+.2f}% "
                    f"(trendline: {win.get('trendline_signal', 'unknown')})"
                )

        # Symbol-specific guidance
        symbol_stats = [s for s in stats['by_symbol'] if s['symbol'] == symbol]
        if symbol_stats:
            context_lines.append(f"\n=== {symbol} SPECIFIC ===")
            for s in symbol_stats:
                acc = (s['correct'] / s['total'] * 100) if s['total'] > 0 else 0
                context_lines.append(f"- {s['deepseek_bias']} calls: {acc:.0f}% accurate ({s['correct']}/{s['total']})")

        return "\n".join(context_lines)

    def get_winning_patterns(self, symbol: str = None, min_samples: int = 3) -> Dict[str, Any]:
        """Identify patterns that have historically led to winning trades.

        Returns conditions that correlate with successful predictions,
        useful for building better signal filters.
        """
        with self._get_conn() as conn:
            base_where = "WHERE outcome_direction IS NOT NULL"
            params = []

            if symbol:
                base_where += " AND symbol = ?"
                params.append(symbol)

            # Accuracy by trendline signal type
            trendline_accuracy = conn.execute(f"""
                SELECT trendline_signal,
                    COUNT(*) as total,
                    SUM(CASE WHEN outcome_direction = 'correct' THEN 1 ELSE 0 END) as correct,
                    AVG(outcome_pct_4h) as avg_move
                FROM chart_signals
                {base_where} AND trendline_signal IS NOT NULL
                GROUP BY trendline_signal
                HAVING COUNT(*) >= ?
                ORDER BY (CAST(correct AS FLOAT) / total) DESC
            """, params + [min_samples]).fetchall()

            # Accuracy by confidence range
            confidence_accuracy = conn.execute(f"""
                SELECT
                    CASE
                        WHEN confidence >= 0.8 THEN 'high (0.8+)'
                        WHEN confidence >= 0.6 THEN 'medium (0.6-0.8)'
                        ELSE 'low (<0.6)'
                    END as confidence_level,
                    COUNT(*) as total,
                    SUM(CASE WHEN outcome_direction = 'correct' THEN 1 ELSE 0 END) as correct,
                    AVG(outcome_pct_4h) as avg_move
                FROM chart_signals
                {base_where}
                GROUP BY confidence_level
                HAVING COUNT(*) >= ?
            """, params + [min_samples]).fetchall()

            # Best performing symbol + direction combos
            best_combos = conn.execute(f"""
                SELECT symbol, direction,
                    COUNT(*) as total,
                    SUM(CASE WHEN outcome_direction = 'correct' THEN 1 ELSE 0 END) as correct,
                    AVG(outcome_pct_4h) as avg_move
                FROM chart_signals
                {base_where}
                GROUP BY symbol, direction
                HAVING COUNT(*) >= ?
                ORDER BY (CAST(correct AS FLOAT) / total) DESC
                LIMIT 10
            """, params + [min_samples]).fetchall()

            return {
                "by_trendline_signal": [dict(r) for r in trendline_accuracy],
                "by_confidence_level": [dict(r) for r in confidence_accuracy],
                "best_symbol_direction_combos": [dict(r) for r in best_combos]
            }

    # =========================================================================
    # DATA MIGRATION
    # =========================================================================

    def migrate_from_json(self) -> Dict[str, int]:
        """Migrate existing JSON data to SQLite.

        Returns:
            Dict with counts of migrated records per type
        """
        migrated = {"whale_events": 0, "sr_events": 0, "chart_signals": 0}

        # Migrate whale events
        whale_file = Path("data/learning/whale_events.json")
        if whale_file.exists():
            try:
                with open(whale_file, 'r') as f:
                    whale_events = json.load(f)

                with self._get_conn() as conn:
                    for event in whale_events:
                        try:
                            conn.execute("""
                                INSERT OR IGNORE INTO whale_events
                                (timestamp, whale, symbol, action, side, size, entry_price,
                                 leverage, notional_usd, price_after_5m, price_after_1h, profitable_follow)
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                            """, (
                                event.get("timestamp"),
                                event.get("whale"),
                                event.get("symbol"),
                                event.get("action"),
                                event.get("side"),
                                event.get("size"),
                                event.get("entry_price"),
                                event.get("leverage"),
                                event.get("notional_usd"),
                                event.get("price_after_5m"),
                                event.get("price_after_1h"),
                                1 if event.get("profitable_follow") else 0 if event.get("profitable_follow") is False else None
                            ))
                            migrated["whale_events"] += 1
                        except Exception as e:
                            logger.warning(f"Failed to migrate whale event: {e}")

                logger.info(f"📀 Migrated {migrated['whale_events']} whale events")
            except Exception as e:
                logger.error(f"Failed to load whale events JSON: {e}")

        # Migrate S/R events
        sr_file = Path("data/learning/sr_events.json")
        if sr_file.exists():
            try:
                with open(sr_file, 'r') as f:
                    sr_events = json.load(f)

                with self._get_conn() as conn:
                    for event in sr_events:
                        try:
                            conn.execute("""
                                INSERT OR IGNORE INTO sr_events
                                (timestamp, symbol, price_at_event, level, direction, break_pct,
                                 price_after_5m, price_after_15m, price_after_1h, continued, reversal_pct)
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                            """, (
                                event.get("timestamp"),
                                event.get("symbol"),
                                event.get("price_at_event"),
                                event.get("level"),
                                event.get("direction"),
                                event.get("break_pct"),
                                event.get("price_after_5m"),
                                event.get("price_after_15m"),
                                event.get("price_after_1h"),
                                1 if event.get("continued") else 0 if event.get("continued") is False else None,
                                event.get("reversal_pct")
                            ))
                            migrated["sr_events"] += 1
                        except Exception as e:
                            logger.warning(f"Failed to migrate S/R event: {e}")

                logger.info(f"📀 Migrated {migrated['sr_events']} S/R events")
            except Exception as e:
                logger.error(f"Failed to load S/R events JSON: {e}")

        # Migrate signal learning data
        signals_file = Path("data/signal_learning/signals.json")
        if signals_file.exists():
            try:
                with open(signals_file, 'r') as f:
                    signals = json.load(f)

                with self._get_conn() as conn:
                    for sig in signals:
                        try:
                            conn.execute("""
                                INSERT OR IGNORE INTO chart_signals
                                (signal_id, signal_type, symbol, timestamp, price_at_signal,
                                 direction, confidence, support_levels, resistance_levels,
                                 asc_support_price, desc_resistance_price, trendline_signal,
                                 deepseek_bias, outcome_checked, price_1h, price_4h, price_24h,
                                 outcome_direction, outcome_pct_1h, outcome_pct_4h, outcome_pct_24h)
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                            """, (
                                sig.get("signal_id"),
                                sig.get("signal_type"),
                                sig.get("symbol"),
                                sig.get("timestamp"),
                                sig.get("price_at_signal"),
                                sig.get("direction"),
                                sig.get("confidence"),
                                json.dumps(sig.get("support_levels", [])),
                                json.dumps(sig.get("resistance_levels", [])),
                                sig.get("asc_support_price"),
                                sig.get("desc_resistance_price"),
                                sig.get("trendline_signal"),
                                sig.get("deepseek_bias"),
                                1 if sig.get("outcome_checked") else 0,
                                sig.get("price_1h"),
                                sig.get("price_4h"),
                                sig.get("price_24h"),
                                sig.get("outcome_direction"),
                                sig.get("outcome_pct_1h"),
                                sig.get("outcome_pct_4h"),
                                sig.get("outcome_pct_24h")
                            ))
                            migrated["chart_signals"] += 1
                        except Exception as e:
                            logger.warning(f"Failed to migrate signal: {e}")

                logger.info(f"📀 Migrated {migrated['chart_signals']} chart signals")
            except Exception as e:
                logger.error(f"Failed to load signals JSON: {e}")

        return migrated

    # =========================================================================
    # PRICE PREDICTIONS
    # =========================================================================

    def save_prediction(self, symbol: str, timeframe: str, current_price: float,
                       predicted_price: float, predicted_direction: str,
                       confidence: float = None, predicted_pct_change: float = None,
                       reasoning: List[str] = None, patterns_used: List[str] = None,
                       chart_id: int = None,
                       # Trend context fields
                       trend_direction: str = None,
                       trend_strength: float = None,
                       ema_position: str = None,
                       rsi_value: float = None,
                       macd_histogram: float = None,
                       volatility_regime: str = None,
                       timestamp: str = None) -> int:
        """Save a price prediction with trend context. Returns the prediction ID."""
        timestamp = timestamp or datetime.utcnow().isoformat()

        with self._get_conn() as conn:
            cursor = conn.execute("""
                INSERT INTO price_predictions
                (symbol, timeframe, timestamp, current_price, predicted_price,
                 predicted_direction, confidence, predicted_pct_change,
                 reasoning, patterns_used, chart_id, trend_direction,
                 trend_strength, ema_position, rsi_value, macd_histogram, volatility_regime)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                symbol, timeframe, timestamp, current_price, predicted_price,
                predicted_direction, confidence, predicted_pct_change,
                json.dumps(reasoning or []), json.dumps(patterns_used or []), chart_id,
                trend_direction, trend_strength, ema_position, rsi_value,
                macd_histogram, volatility_regime
            ))

            logger.info(f"📊 Saved prediction: {symbol} {timeframe} → ${predicted_price:,.0f} ({predicted_direction})")
            return cursor.lastrowid

    def update_prediction_outcome(self, prediction_id: int, actual_price: float) -> Dict:
        """Update prediction with actual outcome after 5 candles."""
        with self._get_conn() as conn:
            # Get the prediction
            row = conn.execute(
                "SELECT * FROM price_predictions WHERE id = ?", (prediction_id,)
            ).fetchone()

            if not row:
                return {"error": "Prediction not found"}

            current_price = row["current_price"]
            predicted_price = row["predicted_price"]
            predicted_direction = row["predicted_direction"]

            # Calculate actual metrics
            actual_pct_change = ((actual_price - current_price) / current_price) * 100
            actual_direction = "up" if actual_price > current_price else "down" if actual_price < current_price else "neutral"

            # Calculate prediction error
            prediction_error = abs(predicted_price - actual_price) / current_price * 100
            direction_correct = 1 if predicted_direction == actual_direction else 0

            # Update the record
            conn.execute("""
                UPDATE price_predictions
                SET actual_price = ?, actual_direction = ?, actual_pct_change = ?,
                    prediction_error_pct = ?, direction_correct = ?,
                    outcome_checked = 1, outcome_timestamp = ?
                WHERE id = ?
            """, (
                actual_price, actual_direction, actual_pct_change,
                prediction_error, direction_correct,
                datetime.utcnow().isoformat(), prediction_id
            ))

            return {
                "prediction_id": prediction_id,
                "predicted_price": predicted_price,
                "actual_price": actual_price,
                "direction_correct": direction_correct,
                "error_pct": prediction_error
            }

    def get_pending_predictions(self, symbol: str = None, timeframe: str = None) -> List[Dict]:
        """Get predictions that need outcome checking."""
        with self._get_conn() as conn:
            query = "SELECT * FROM price_predictions WHERE outcome_checked = 0"
            params = []

            if symbol:
                query += " AND symbol = ?"
                params.append(symbol)
            if timeframe:
                query += " AND timeframe = ?"
                params.append(timeframe)

            query += " ORDER BY timestamp ASC"

            rows = conn.execute(query, params).fetchall()
            return [dict(r) for r in rows]

    def get_prediction_accuracy(self, symbol: str = None, timeframe: str = None,
                                days: int = 30) -> Dict[str, Any]:
        """Get prediction accuracy statistics."""
        with self._get_conn() as conn:
            cutoff = (datetime.utcnow() - timedelta(days=days)).isoformat()

            query = """
                SELECT
                    COUNT(*) as total,
                    SUM(CASE WHEN direction_correct = 1 THEN 1 ELSE 0 END) as correct,
                    AVG(prediction_error_pct) as avg_error,
                    AVG(CASE WHEN direction_correct = 1 THEN prediction_error_pct END) as avg_error_when_correct
                FROM price_predictions
                WHERE outcome_checked = 1 AND timestamp > ?
            """
            params = [cutoff]

            if symbol:
                query += " AND symbol = ?"
                params.append(symbol)
            if timeframe:
                query += " AND timeframe = ?"
                params.append(timeframe)

            row = conn.execute(query, params).fetchone()

            total = row["total"] or 0
            correct = row["correct"] or 0

            return {
                "total_predictions": total,
                "correct_direction": correct,
                "accuracy_pct": (correct / total * 100) if total > 0 else 0,
                "avg_error_pct": row["avg_error"] or 0,
                "avg_error_when_correct": row["avg_error_when_correct"] or 0,
                "timeframe": timeframe,
                "symbol": symbol,
                "days": days
            }

    # =========================================================================
    # TREND LEARNING & FILTERING
    # =========================================================================

    def get_signals_by_trend(self, trend_direction: str = None,
                              ema_position: str = None,
                              trendline_signal: str = None,
                              min_trend_strength: float = None,
                              with_outcomes: bool = True,
                              symbol: str = None,
                              limit: int = 500) -> List[Dict]:
        """Get chart signals filtered by trend conditions.

        Args:
            trend_direction: 'bullish', 'bearish', or 'neutral'
            ema_position: 'above_ema', 'below_ema', 'at_ema'
            trendline_signal: 'at_ascending_support', 'at_descending_resistance', etc.
            min_trend_strength: Minimum trend strength (0-100)
            with_outcomes: Only return signals with checked outcomes
            symbol: Filter by symbol
            limit: Max results
        """
        query = "SELECT * FROM chart_signals WHERE 1=1"
        params = []

        if trend_direction:
            query += " AND trend_direction = ?"
            params.append(trend_direction)
        if ema_position:
            query += " AND ema_position = ?"
            params.append(ema_position)
        if trendline_signal:
            query += " AND trendline_signal = ?"
            params.append(trendline_signal)
        if min_trend_strength is not None:
            query += " AND trend_strength >= ?"
            params.append(min_trend_strength)
        if with_outcomes:
            query += " AND outcome_checked = 1"
        if symbol:
            query += " AND symbol = ?"
            params.append(symbol)

        query += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)

        with self._get_conn() as conn:
            rows = conn.execute(query, params).fetchall()
            results = []
            for row in rows:
                d = dict(row)
                d["support_levels"] = json.loads(d.get("support_levels") or "[]")
                d["resistance_levels"] = json.loads(d.get("resistance_levels") or "[]")
                d["patterns_detected"] = json.loads(d.get("patterns_detected") or "[]")
                results.append(d)
            return results

    def get_trend_setup_performance(self, days: int = 30) -> Dict[str, Any]:
        """Analyze which trend setups have the best win rates.

        Returns breakdown by:
        - trend_direction (bullish/bearish)
        - trendline_signal type
        - EMA position
        - pattern combinations
        """
        cutoff = (datetime.utcnow() - timedelta(days=days)).isoformat()

        with self._get_conn() as conn:
            results = {
                "by_trend_direction": {},
                "by_trendline_signal": {},
                "by_ema_position": {},
                "by_volatility_regime": {},
                "top_setups": [],
                "days_analyzed": days
            }

            # Performance by trend direction
            rows = conn.execute("""
                SELECT trend_direction,
                    COUNT(*) as total,
                    SUM(CASE WHEN outcome_direction = 'correct' THEN 1 ELSE 0 END) as wins,
                    AVG(outcome_pct_1h) as avg_pct_1h,
                    AVG(outcome_pct_4h) as avg_pct_4h,
                    AVG(outcome_pct_24h) as avg_pct_24h
                FROM chart_signals
                WHERE outcome_checked = 1 AND timestamp > ? AND trend_direction IS NOT NULL
                GROUP BY trend_direction
            """, (cutoff,)).fetchall()

            for row in rows:
                td = row["trend_direction"] or "unknown"
                total = row["total"] or 0
                wins = row["wins"] or 0
                results["by_trend_direction"][td] = {
                    "total": total,
                    "wins": wins,
                    "win_rate": (wins / total * 100) if total > 0 else 0,
                    "avg_pct_1h": row["avg_pct_1h"] or 0,
                    "avg_pct_4h": row["avg_pct_4h"] or 0,
                    "avg_pct_24h": row["avg_pct_24h"] or 0
                }

            # Performance by trendline signal
            rows = conn.execute("""
                SELECT trendline_signal,
                    COUNT(*) as total,
                    SUM(CASE WHEN outcome_direction = 'correct' THEN 1 ELSE 0 END) as wins,
                    AVG(outcome_pct_4h) as avg_pct_4h
                FROM chart_signals
                WHERE outcome_checked = 1 AND timestamp > ? AND trendline_signal IS NOT NULL
                GROUP BY trendline_signal
                HAVING total >= 3
                ORDER BY (CAST(wins AS FLOAT) / total) DESC
            """, (cutoff,)).fetchall()

            for row in rows:
                sig = row["trendline_signal"] or "unknown"
                total = row["total"] or 0
                wins = row["wins"] or 0
                results["by_trendline_signal"][sig] = {
                    "total": total,
                    "wins": wins,
                    "win_rate": (wins / total * 100) if total > 0 else 0,
                    "avg_pct_4h": row["avg_pct_4h"] or 0
                }

            # Performance by EMA position
            rows = conn.execute("""
                SELECT ema_position,
                    COUNT(*) as total,
                    SUM(CASE WHEN outcome_direction = 'correct' THEN 1 ELSE 0 END) as wins,
                    AVG(outcome_pct_4h) as avg_pct_4h
                FROM chart_signals
                WHERE outcome_checked = 1 AND timestamp > ? AND ema_position IS NOT NULL
                GROUP BY ema_position
            """, (cutoff,)).fetchall()

            for row in rows:
                pos = row["ema_position"] or "unknown"
                total = row["total"] or 0
                wins = row["wins"] or 0
                results["by_ema_position"][pos] = {
                    "total": total,
                    "wins": wins,
                    "win_rate": (wins / total * 100) if total > 0 else 0,
                    "avg_pct_4h": row["avg_pct_4h"] or 0
                }

            # Top combined setups (trend + trendline + ema)
            rows = conn.execute("""
                SELECT
                    trend_direction || '_' || COALESCE(trendline_signal, 'none') || '_' || COALESCE(ema_position, 'unknown') as setup,
                    trend_direction,
                    trendline_signal,
                    ema_position,
                    COUNT(*) as total,
                    SUM(CASE WHEN outcome_direction = 'correct' THEN 1 ELSE 0 END) as wins,
                    AVG(outcome_pct_4h) as avg_pct_4h
                FROM chart_signals
                WHERE outcome_checked = 1 AND timestamp > ?
                GROUP BY trend_direction, trendline_signal, ema_position
                HAVING total >= 5
                ORDER BY (CAST(wins AS FLOAT) / total) DESC
                LIMIT 10
            """, (cutoff,)).fetchall()

            for row in rows:
                total = row["total"] or 0
                wins = row["wins"] or 0
                results["top_setups"].append({
                    "setup": row["setup"],
                    "trend_direction": row["trend_direction"],
                    "trendline_signal": row["trendline_signal"],
                    "ema_position": row["ema_position"],
                    "total": total,
                    "wins": wins,
                    "win_rate": (wins / total * 100) if total > 0 else 0,
                    "avg_pct_4h": row["avg_pct_4h"] or 0
                })

            return results

    def get_prediction_accuracy_by_trend(self, days: int = 30) -> Dict[str, Any]:
        """Get prediction accuracy broken down by trend conditions."""
        cutoff = (datetime.utcnow() - timedelta(days=days)).isoformat()

        with self._get_conn() as conn:
            results = {
                "by_trend_direction": {},
                "by_volatility": {},
                "overall": {}
            }

            # Overall
            row = conn.execute("""
                SELECT COUNT(*) as total,
                    SUM(CASE WHEN direction_correct = 1 THEN 1 ELSE 0 END) as correct,
                    AVG(prediction_error_pct) as avg_error
                FROM price_predictions
                WHERE outcome_checked = 1 AND timestamp > ?
            """, (cutoff,)).fetchone()

            total = row["total"] or 0
            correct = row["correct"] or 0
            results["overall"] = {
                "total": total,
                "correct": correct,
                "accuracy_pct": (correct / total * 100) if total > 0 else 0,
                "avg_error_pct": row["avg_error"] or 0
            }

            # By trend direction
            rows = conn.execute("""
                SELECT trend_direction,
                    COUNT(*) as total,
                    SUM(CASE WHEN direction_correct = 1 THEN 1 ELSE 0 END) as correct,
                    AVG(prediction_error_pct) as avg_error
                FROM price_predictions
                WHERE outcome_checked = 1 AND timestamp > ? AND trend_direction IS NOT NULL
                GROUP BY trend_direction
            """, (cutoff,)).fetchall()

            for row in rows:
                td = row["trend_direction"] or "unknown"
                total = row["total"] or 0
                correct = row["correct"] or 0
                results["by_trend_direction"][td] = {
                    "total": total,
                    "correct": correct,
                    "accuracy_pct": (correct / total * 100) if total > 0 else 0,
                    "avg_error_pct": row["avg_error"] or 0
                }

            # By volatility regime
            rows = conn.execute("""
                SELECT volatility_regime,
                    COUNT(*) as total,
                    SUM(CASE WHEN direction_correct = 1 THEN 1 ELSE 0 END) as correct,
                    AVG(prediction_error_pct) as avg_error
                FROM price_predictions
                WHERE outcome_checked = 1 AND timestamp > ? AND volatility_regime IS NOT NULL
                GROUP BY volatility_regime
            """, (cutoff,)).fetchall()

            for row in rows:
                vr = row["volatility_regime"] or "unknown"
                total = row["total"] or 0
                correct = row["correct"] or 0
                results["by_volatility"][vr] = {
                    "total": total,
                    "correct": correct,
                    "accuracy_pct": (correct / total * 100) if total > 0 else 0,
                    "avg_error_pct": row["avg_error"] or 0
                }

            return results

    def analyze_prediction_errors(self, symbol: str = None, timeframe: str = None,
                                   days: int = 30) -> Dict[str, Any]:
        """Analyze WHY predictions were wrong to learn from mistakes.

        Returns breakdown of errors by various factors like trend, volatility, patterns.
        """
        cutoff = (datetime.utcnow() - timedelta(days=days)).isoformat()

        with self._get_conn() as conn:
            results = {
                "total_errors": 0,
                "avg_error_pct": 0,
                "errors_by_trend": {},
                "errors_by_volatility": {},
                "errors_by_pattern": {},
                "worst_predictions": [],
                "common_failure_modes": [],
                "recommendations": []
            }

            # Build base query for wrong predictions
            base_query = """
                SELECT * FROM price_predictions
                WHERE outcome_checked = 1 AND direction_correct = 0 AND timestamp > ?
            """
            params = [cutoff]

            if symbol:
                base_query += " AND symbol = ?"
                params.append(symbol)
            if timeframe:
                base_query += " AND timeframe = ?"
                params.append(timeframe)

            wrong_predictions = conn.execute(base_query, params).fetchall()
            results["total_errors"] = len(wrong_predictions)

            if not wrong_predictions:
                results["recommendations"].append("No prediction errors found - great accuracy!")
                return results

            # Calculate average error
            errors = [abs(r["prediction_error_pct"]) for r in wrong_predictions]
            results["avg_error_pct"] = sum(errors) / len(errors)

            # Analyze by trend direction
            trend_errors = {}
            for row in wrong_predictions:
                td = row["trend_direction"] or "unknown"
                if td not in trend_errors:
                    trend_errors[td] = {"count": 0, "total_error": 0}
                trend_errors[td]["count"] += 1
                trend_errors[td]["total_error"] += abs(row["prediction_error_pct"])

            for td, data in trend_errors.items():
                results["errors_by_trend"][td] = {
                    "error_count": data["count"],
                    "avg_error_pct": data["total_error"] / data["count"],
                    "pct_of_errors": data["count"] / len(wrong_predictions) * 100
                }

            # Analyze by volatility regime
            vol_errors = {}
            for row in wrong_predictions:
                vr = row["volatility_regime"] or "unknown"
                if vr not in vol_errors:
                    vol_errors[vr] = {"count": 0, "total_error": 0}
                vol_errors[vr]["count"] += 1
                vol_errors[vr]["total_error"] += abs(row["prediction_error_pct"])

            for vr, data in vol_errors.items():
                results["errors_by_volatility"][vr] = {
                    "error_count": data["count"],
                    "avg_error_pct": data["total_error"] / data["count"],
                    "pct_of_errors": data["count"] / len(wrong_predictions) * 100
                }

            # Analyze by patterns used
            pattern_errors = {}
            for row in wrong_predictions:
                patterns = json.loads(row["patterns_used"] or "[]")
                for pattern in patterns:
                    if pattern not in pattern_errors:
                        pattern_errors[pattern] = {"count": 0, "total_error": 0}
                    pattern_errors[pattern]["count"] += 1
                    pattern_errors[pattern]["total_error"] += abs(row["prediction_error_pct"])

            for pattern, data in sorted(pattern_errors.items(), key=lambda x: -x[1]["count"])[:10]:
                results["errors_by_pattern"][pattern] = {
                    "error_count": data["count"],
                    "avg_error_pct": data["total_error"] / data["count"]
                }

            # Get worst predictions
            worst = conn.execute("""
                SELECT symbol, timeframe, timestamp, predicted_direction,
                       predicted_price, actual_price, prediction_error_pct,
                       trend_direction, volatility_regime, reasoning, patterns_used
                FROM price_predictions
                WHERE outcome_checked = 1 AND direction_correct = 0 AND timestamp > ?
                ORDER BY prediction_error_pct DESC
                LIMIT 5
            """, (cutoff,)).fetchall()

            for row in worst:
                results["worst_predictions"].append({
                    "symbol": row["symbol"],
                    "timeframe": row["timeframe"],
                    "timestamp": row["timestamp"],
                    "predicted": row["predicted_direction"],
                    "predicted_price": row["predicted_price"],
                    "actual_price": row["actual_price"],
                    "error_pct": row["prediction_error_pct"],
                    "trend": row["trend_direction"],
                    "volatility": row["volatility_regime"],
                    "reasoning": json.loads(row["reasoning"] or "[]"),
                    "patterns": json.loads(row["patterns_used"] or "[]")
                })

            # Generate failure mode analysis
            failure_modes = []

            # Check if high volatility causes more errors
            if "high" in results["errors_by_volatility"]:
                high_vol_pct = results["errors_by_volatility"]["high"]["pct_of_errors"]
                if high_vol_pct > 40:
                    failure_modes.append({
                        "mode": "high_volatility",
                        "description": f"{high_vol_pct:.0f}% of errors occur in high volatility",
                        "recommendation": "Reduce confidence or skip predictions in high volatility"
                    })

            # Check if certain trends are problematic
            for td, data in results["errors_by_trend"].items():
                if data["pct_of_errors"] > 50:
                    failure_modes.append({
                        "mode": f"{td}_trend",
                        "description": f"{data['pct_of_errors']:.0f}% of errors in {td} trends",
                        "recommendation": f"Review {td} trend detection logic"
                    })

            # Check if certain patterns fail often
            for pattern, data in results["errors_by_pattern"].items():
                if data["error_count"] >= 3 and data["avg_error_pct"] > 2:
                    failure_modes.append({
                        "mode": f"pattern_{pattern}",
                        "description": f"Pattern '{pattern}' has {data['avg_error_pct']:.1f}% avg error",
                        "recommendation": f"Reduce weight of '{pattern}' pattern in predictions"
                    })

            results["common_failure_modes"] = failure_modes

            # Generate recommendations
            recommendations = []
            if results["avg_error_pct"] > 3:
                recommendations.append("High average error - consider using wider prediction ranges")
            if len(failure_modes) > 0:
                recommendations.append(f"Found {len(failure_modes)} common failure patterns - review them")

            # Check for direction-specific issues
            up_errors = sum(1 for r in wrong_predictions if r["predicted_direction"] == "up")
            down_errors = sum(1 for r in wrong_predictions if r["predicted_direction"] == "down")
            if up_errors > down_errors * 1.5:
                recommendations.append("Tendency to over-predict upward moves - add bearish bias")
            elif down_errors > up_errors * 1.5:
                recommendations.append("Tendency to over-predict downward moves - add bullish bias")

            results["recommendations"] = recommendations

            return results

    def save_prediction_analysis(self, prediction_id: int, analysis: str,
                                  failure_mode: str = None, lesson_learned: str = None):
        """Save analysis of why a prediction was right or wrong."""
        with self._get_conn() as conn:
            # Check if analysis columns exist, add if not
            cols = {row[1] for row in conn.execute("PRAGMA table_info(price_predictions)").fetchall()}
            if "analysis" not in cols:
                conn.execute("ALTER TABLE price_predictions ADD COLUMN analysis TEXT")
            if "failure_mode" not in cols:
                conn.execute("ALTER TABLE price_predictions ADD COLUMN failure_mode TEXT")
            if "lesson_learned" not in cols:
                conn.execute("ALTER TABLE price_predictions ADD COLUMN lesson_learned TEXT")

            conn.execute("""
                UPDATE price_predictions
                SET analysis = ?, failure_mode = ?, lesson_learned = ?
                WHERE id = ?
            """, (analysis, failure_mode, lesson_learned, prediction_id))

    def get_prediction_lessons(self, limit: int = 50) -> List[Dict]:
        """Get predictions with lessons learned for training."""
        with self._get_conn() as conn:
            # Check if columns exist
            cols = {row[1] for row in conn.execute("PRAGMA table_info(price_predictions)").fetchall()}
            if "lesson_learned" not in cols:
                return []

            rows = conn.execute("""
                SELECT symbol, timeframe, timestamp, predicted_direction, actual_direction,
                       direction_correct, prediction_error_pct, trend_direction,
                       volatility_regime, patterns_used, analysis, failure_mode, lesson_learned
                FROM price_predictions
                WHERE outcome_checked = 1 AND lesson_learned IS NOT NULL
                ORDER BY timestamp DESC LIMIT ?
            """, (limit,)).fetchall()

            return [dict(r) for r in rows]

    def get_trend_confidence_multiplier(self, trend_direction: str,
                                         trendline_signal: str = None,
                                         ema_position: str = None) -> float:
        """Get a confidence multiplier based on historical trend setup performance.

        Returns a multiplier (0.5-1.5) that can be applied to signal confidence
        based on how well similar setups have performed historically.
        """
        with self._get_conn() as conn:
            # Get performance for this specific setup
            query = """
                SELECT COUNT(*) as total,
                    SUM(CASE WHEN outcome_direction = 'correct' THEN 1 ELSE 0 END) as wins
                FROM chart_signals
                WHERE outcome_checked = 1 AND trend_direction = ?
            """
            params = [trend_direction]

            if trendline_signal:
                query += " AND trendline_signal = ?"
                params.append(trendline_signal)
            if ema_position:
                query += " AND ema_position = ?"
                params.append(ema_position)

            row = conn.execute(query, params).fetchone()

            total = row["total"] or 0
            wins = row["wins"] or 0

            if total < 5:
                # Not enough data, return neutral
                return 1.0

            win_rate = wins / total

            # Convert win rate to multiplier:
            # - 70%+ win rate = 1.3-1.5x multiplier
            # - 50-70% = 1.0-1.3x
            # - 30-50% = 0.7-1.0x
            # - <30% = 0.5-0.7x
            if win_rate >= 0.7:
                return 1.3 + (win_rate - 0.7) * 0.67  # 1.3 to 1.5
            elif win_rate >= 0.5:
                return 1.0 + (win_rate - 0.5) * 1.5   # 1.0 to 1.3
            elif win_rate >= 0.3:
                return 0.7 + (win_rate - 0.3) * 1.5   # 0.7 to 1.0
            else:
                return 0.5 + win_rate * 0.67          # 0.5 to 0.7

    def get_db_stats(self) -> Dict[str, Any]:
        """Get database statistics."""
        with self._get_conn() as conn:
            stats = {
                "whale_events": conn.execute("SELECT COUNT(*) as cnt FROM whale_events").fetchone()["cnt"],
                "chart_signals": conn.execute("SELECT COUNT(*) as cnt FROM chart_signals").fetchone()["cnt"],
                "sr_events": conn.execute("SELECT COUNT(*) as cnt FROM sr_events").fetchone()["cnt"],
                "charts": conn.execute("SELECT COUNT(*) as cnt FROM charts").fetchone()["cnt"],
                "trade_signals": conn.execute("SELECT COUNT(*) as cnt FROM trade_signals").fetchone()["cnt"],
                "discord_alerts": conn.execute("SELECT COUNT(*) as cnt FROM discord_alerts").fetchone()["cnt"],
                "pending_outcomes": conn.execute("SELECT COUNT(*) as cnt FROM pending_outcomes WHERE completed = 0").fetchone()["cnt"],
            }

            # Add prediction stats
            try:
                stats["predictions_total"] = conn.execute("SELECT COUNT(*) as cnt FROM price_predictions").fetchone()["cnt"]
                stats["predictions_pending"] = conn.execute("SELECT COUNT(*) as cnt FROM price_predictions WHERE outcome_checked = 0").fetchone()["cnt"]
                stats["predictions_checked"] = stats["predictions_total"] - stats["predictions_pending"]

                # Get accuracy
                acc = conn.execute("""
                    SELECT AVG(CASE WHEN direction_correct = 1 THEN 100.0 ELSE 0 END) as acc
                    FROM price_predictions WHERE outcome_checked = 1
                """).fetchone()
                stats["prediction_accuracy_pct"] = round(acc["acc"] or 0, 1)
            except Exception:
                # Table might not exist yet
                pass

            # Database file size
            stats["db_size_mb"] = self.db_path.stat().st_size / (1024 * 1024) if self.db_path.exists() else 0

            return stats

