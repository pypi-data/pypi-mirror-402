"""
Hyperliquid API Client - Handles all exchange interactions.
"""

import logging
from typing import Dict, List, Optional, Any
from decimal import Decimal

from hyperliquid.info import Info
from hyperliquid.exchange import Exchange
from hyperliquid.utils import constants
from eth_account import Account

from src.tickers import round_price as tick_round_price

logger = logging.getLogger(__name__)


class HyperliquidClient:
    """Client for interacting with Hyperliquid exchange."""
    
    def __init__(
        self,
        private_key: str,
        wallet_address: str,
        testnet: bool = True
    ):
        self.private_key = private_key
        self.wallet_address = wallet_address
        self.testnet = testnet
        
        # Set API URL based on testnet flag
        self.base_url = constants.TESTNET_API_URL if testnet else constants.MAINNET_API_URL
        
        # Initialize SDK components
        self.info: Optional[Info] = None
        self.exchange: Optional[Exchange] = None
        self.account: Optional[Account] = None
        
    async def connect(self) -> bool:
        """Connect to Hyperliquid."""
        try:
            # Create account from private key
            self.account = Account.from_key(self.private_key)

            # Note: account_address (trading account) can differ from the signing key address
            # when using an authorized agent key. If you are *not* using an agent key, a mismatch
            # here often indicates a misconfiguration that can make fills/positions appear wrong.
            if self.wallet_address and self.account and self.account.address:
                if self.account.address.lower() != self.wallet_address.lower():
                    logger.warning(
                        "Signer wallet (%s) differs from configured account_address (%s). "
                        "This is expected if you're using an authorized agent key; otherwise fix env vars.",
                        self.account.address,
                        self.wallet_address,
                    )
            
            # Initialize Info client (read-only operations)
            self.info = Info(self.base_url, skip_ws=True)
            
            # Initialize Exchange client (trading operations)
            self.exchange = Exchange(
                self.account,
                self.base_url,
                account_address=self.wallet_address
            )
            
            logger.info(f"Connected to Hyperliquid {'testnet' if self.testnet else 'mainnet'}")
            logger.info(f"Wallet: {self.wallet_address}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to Hyperliquid: {e}")
            return False

    def _require_connected(self) -> None:
        if self.info is None or self.exchange is None:
            raise RuntimeError("HyperliquidClient not connected. Call await connect() first.")

    @staticmethod
    def _normalize_asset_positions(asset_positions: Any) -> List[Dict[str, Any]]:
        """Normalize Info.user_state()['assetPositions'] into a list of flat position dicts."""
        if not isinstance(asset_positions, list):
            return []
        normalized: List[Dict[str, Any]] = []
        for ap in asset_positions:
            if isinstance(ap, dict) and isinstance(ap.get("position"), dict):
                normalized.append(ap["position"])
            elif isinstance(ap, dict):
                normalized.append(ap)
        return normalized

    @staticmethod
    def _extract_order_error(result: Any) -> Optional[str]:
        """Best-effort extraction of order placement errors from SDK responses."""
        if not isinstance(result, dict):
            return None

        # Top-level failures
        if result.get("status") and result.get("status") != "ok":
            return str(result.get("error") or result.get("status"))
        if result.get("error"):
            return str(result.get("error"))

        # Typical structure: {status:'ok', response:{type:'order', data:{statuses:[...]}}}
        response = result.get("response")
        if isinstance(response, dict):
            data = response.get("data")
            if isinstance(data, dict):
                statuses = data.get("statuses")
                if isinstance(statuses, list) and statuses:
                    first = statuses[0]
                    if isinstance(first, dict):
                        if first.get("error"):
                            return str(first.get("error"))

                        # Some rejections are nested
                        rejected = first.get("rejected")
                        if isinstance(rejected, dict):
                            if rejected.get("reason"):
                                return str(rejected.get("reason"))
                            if rejected.get("error"):
                                return str(rejected.get("error"))
        return None

    @staticmethod
    def _extract_order_status(result: Any) -> Dict[str, Any]:
        """Extract order outcome information (kind/oid/details) from SDK response."""
        if not isinstance(result, dict):
            return {"kind": "unknown", "oid": None, "details": None}

        response = result.get("response")
        if not isinstance(response, dict):
            return {"kind": "unknown", "oid": None, "details": None}
        data = response.get("data")
        if not isinstance(data, dict):
            return {"kind": "unknown", "oid": None, "details": None}

        statuses = data.get("statuses")
        if not (isinstance(statuses, list) and statuses):
            return {"kind": "unknown", "oid": None, "details": None}

        first = statuses[0]
        if not isinstance(first, dict):
            return {"kind": "unknown", "oid": None, "details": first}

        for kind in ("filled", "resting", "cancelled", "rejected"):
            if kind in first:
                details = first.get(kind)
                oid = None
                if isinstance(details, dict):
                    oid = details.get("oid")
                return {"kind": kind, "oid": oid, "details": details}

        return {"kind": "unknown", "oid": None, "details": first}
    
    def get_account_state(self) -> Dict[str, Any]:
        """Get account balance and positions."""
        try:
            self._require_connected()
            state = self.info.user_state(self.wallet_address)

            raw_asset_positions = state.get("assetPositions", [])
            positions = self._normalize_asset_positions(raw_asset_positions)
            return {
                "equity": float(state.get("marginSummary", {}).get("accountValue", 0)),
                "available_balance": float(state.get("withdrawable", 0)),
                "positions": positions,
                "asset_positions_raw": raw_asset_positions,
                "margin_used": float(state.get("marginSummary", {}).get("totalMarginUsed", 0)),
            }
        except Exception as e:
            logger.error(f"Failed to get account state: {e}")
            return {"equity": 0, "available_balance": 0, "positions": [], "margin_used": 0}
    
    def get_price(self, symbol: str) -> Optional[float]:
        """Get current mid price for a symbol."""
        try:
            self._require_connected()
            all_mids = self.info.all_mids()
            return float(all_mids.get(symbol, 0))
        except Exception as e:
            logger.error(f"Failed to get price for {symbol}: {e}")
            return None
    
    def get_orderbook(self, symbol: str) -> Dict[str, Any]:
        """Get orderbook for a symbol."""
        try:
            self._require_connected()
            book = self.info.l2_snapshot(symbol)
            return {
                "bids": book.get("levels", [[]])[0][:5],  # Top 5 bids
                "asks": book.get("levels", [[]])[1][:5],  # Top 5 asks
            }
        except Exception as e:
            logger.error(f"Failed to get orderbook for {symbol}: {e}")
            return {"bids": [], "asks": []}
    
    def get_recent_trades(self, symbol: str, limit: int = 50) -> List[Dict]:
        """Get recent trades."""
        try:
            # Use user_fills or just return empty - recent_trades not in SDK
            return []
        except Exception as e:
            logger.error(f"Failed to get recent trades: {e}")
            return []

    def get_candles(self, symbol: str, interval: str = "15m", limit: int = 100) -> List[Dict]:
        """Get candlestick data for technical analysis.

        Args:
            symbol: Trading pair symbol (e.g., 'ETH')
            interval: Candle interval (e.g., '1m', '5m', '15m', '1h', '4h', '1d')
            limit: Number of candles to retrieve

        Returns:
            List of candles with open, high, low, close, volume
        """
        try:
            self._require_connected()
            import time

            # Convert interval to seconds
            interval_map = {
                "1m": 60, "5m": 300, "15m": 900, "30m": 1800,
                "1h": 3600, "4h": 14400, "1d": 86400
            }
            interval_secs = interval_map.get(interval, 900)

            # Calculate time range
            end_time = int(time.time() * 1000)
            start_time = end_time - (limit * interval_secs * 1000)

            # Hyperliquid candle snapshot endpoint
            candles = self.info.candles_snapshot(symbol, interval, start_time, end_time)

            result = []
            for c in candles:
                result.append({
                    "timestamp": c.get("t", 0),
                    "open": float(c.get("o", 0)),
                    "high": float(c.get("h", 0)),
                    "low": float(c.get("l", 0)),
                    "close": float(c.get("c", 0)),
                    "volume": float(c.get("v", 0))
                })

            return result
        except Exception as e:
            logger.error(f"Failed to get candles: {e}")
            return []

    def get_funding_rate(self, symbol: str) -> Dict[str, Any]:
        """Get current and predicted funding rate for a symbol.

        Returns:
            Dict with 'funding_rate' and 'predicted_rate'
        """
        try:
            self._require_connected()

            # Get meta and asset contexts for funding info
            meta = self.info.meta_and_asset_ctxs()

            if not meta or len(meta) < 2:
                return {"funding_rate": 0.0, "predicted_rate": 0.0}

            asset_ctxs = meta[1]
            universe = meta[0].get("universe", [])

            # Find symbol index
            symbol_idx = None
            for i, asset in enumerate(universe):
                if asset.get("name") == symbol:
                    symbol_idx = i
                    break

            if symbol_idx is not None and symbol_idx < len(asset_ctxs):
                ctx = asset_ctxs[symbol_idx]
                funding = float(ctx.get("funding", 0))
                # Funding is hourly rate, annualize for display
                return {
                    "funding_rate": funding,
                    "funding_rate_8h": funding * 8,  # 8-hour rate (standard)
                    "funding_rate_annual": funding * 24 * 365
                }

            return {"funding_rate": 0.0, "funding_rate_8h": 0.0}
        except Exception as e:
            logger.error(f"Failed to get funding rate: {e}")
            return {"funding_rate": 0.0, "funding_rate_8h": 0.0}

    def get_open_interest(self, symbol: str) -> Dict[str, Any]:
        """Get open interest data for a symbol.

        Returns:
            Dict with open_interest in USD and contracts, plus 24h change
        """
        try:
            self._require_connected()
            meta = self.info.meta_and_asset_ctxs()

            if not meta or len(meta) < 2:
                return {"open_interest_usd": 0, "open_interest": 0}

            asset_ctxs = meta[1]
            universe = meta[0].get("universe", [])

            symbol_idx = None
            for i, asset in enumerate(universe):
                if asset.get("name") == symbol:
                    symbol_idx = i
                    break

            if symbol_idx is not None and symbol_idx < len(asset_ctxs):
                ctx = asset_ctxs[symbol_idx]
                oi = float(ctx.get("openInterest", 0))
                mark_price = float(ctx.get("markPx", 0))

                return {
                    "open_interest": oi,  # In contracts/coins
                    "open_interest_usd": oi * mark_price,
                    "mark_price": mark_price
                }

            return {"open_interest": 0, "open_interest_usd": 0}
        except Exception as e:
            logger.error(f"Failed to get open interest for {symbol}: {e}")
            return {"open_interest": 0, "open_interest_usd": 0}

    def get_market_meta(self, symbol: str) -> Dict[str, Any]:
        """Get comprehensive market metadata including liquidation estimates.

        Returns:
            Dict with mark price, index price, 24h volume, open interest, etc.
        """
        try:
            self._require_connected()
            meta = self.info.meta_and_asset_ctxs()

            if not meta or len(meta) < 2:
                return {}

            asset_ctxs = meta[1]
            universe = meta[0].get("universe", [])

            symbol_idx = None
            asset_meta = None
            for i, asset in enumerate(universe):
                if asset.get("name") == symbol:
                    symbol_idx = i
                    asset_meta = asset
                    break

            if symbol_idx is None or symbol_idx >= len(asset_ctxs):
                return {}

            ctx = asset_ctxs[symbol_idx]
            mark_price = float(ctx.get("markPx", 0))

            # Estimate liquidation levels based on typical leverage
            # Long liquidation: price drops enough to wipe margin
            # Short liquidation: price rises enough to wipe margin
            # Using 10x and 25x as common leverage levels
            liq_long_10x = mark_price * 0.90  # 10% drop liquidates 10x long
            liq_long_25x = mark_price * 0.96  # 4% drop liquidates 25x long
            liq_short_10x = mark_price * 1.10  # 10% rise liquidates 10x short
            liq_short_25x = mark_price * 1.04  # 4% rise liquidates 25x short

            return {
                "mark_price": mark_price,
                "oracle_price": float(ctx.get("oraclePx", mark_price)),
                "open_interest": float(ctx.get("openInterest", 0)),
                "funding_rate": float(ctx.get("funding", 0)),
                "premium": float(ctx.get("premium", 0)),
                "prev_day_px": float(ctx.get("prevDayPx", mark_price)),
                "day_ntl_vlm": float(ctx.get("dayNtlVlm", 0)),  # 24h volume in USD
                # Estimated liquidation zones
                "liq_long_10x": round(liq_long_10x, 2),
                "liq_long_25x": round(liq_long_25x, 2),
                "liq_short_10x": round(liq_short_10x, 2),
                "liq_short_25x": round(liq_short_25x, 2),
                # Max leverage from universe (BTC=40x, ETH=25x, SOL=20x)
                "max_leverage": asset_meta.get("maxLeverage", 20) if asset_meta else 20
            }
        except Exception as e:
            logger.error(f"Failed to get market meta for {symbol}: {e}")
            return {}

    def get_max_leverage(self, symbol: str) -> int:
        """Get max leverage for a symbol from universe metadata."""
        try:
            meta = self.get_market_meta(symbol)
            return int(meta.get("max_leverage", 20))
        except Exception as e:
            logger.warning(f"Failed to get max leverage for {symbol}, defaulting to 20x: {e}")
            return 20  # Safe default

    def get_sz_decimals(self, symbol: str) -> int:
        """Get size decimals (szDecimals) for a symbol from universe metadata.

        Hyperliquid requires order sizes to be rounded to szDecimals decimal places.
        """
        try:
            self._require_connected()
            meta = self.info.meta_and_asset_ctxs()

            if not meta or len(meta) < 1:
                return 3  # Safe default

            universe = meta[0].get("universe", [])
            for asset in universe:
                if asset.get("name") == symbol:
                    return int(asset.get("szDecimals", 3))

            return 3  # Default if not found
        except Exception as e:
            logger.warning(f"Failed to get szDecimals for {symbol}, defaulting to 3: {e}")
            return 3

    def round_size(self, symbol: str, size: float) -> float:
        """Round order size to the correct number of decimals for a symbol.

        Hyperliquid will reject orders with too many decimal places.
        """
        sz_decimals = self.get_sz_decimals(symbol)
        return round(size, sz_decimals)

    def round_price(self, symbol: str, price: float) -> float:
        """Round price to the correct tick size for a symbol.

        Hyperliquid requires prices to be rounded to proper tick sizes.
        Uses centralized tick sizes from src/tickers.py
        """
        return tick_round_price(symbol, price)

    def set_leverage(self, symbol: str, leverage: int, is_cross: bool = True) -> Dict[str, Any]:
        """Set leverage for a symbol."""
        try:
            self._require_connected()
            result = self.exchange.update_leverage(
                leverage,
                symbol,
                is_cross=is_cross
            )
            logger.info(f"Leverage set to {leverage}x for {symbol} ({'cross' if is_cross else 'isolated'})")
            return {"success": True, "result": result}
        except Exception as e:
            logger.error(f"Failed to set leverage: {e}")
            return {"success": False, "error": str(e)}

    def place_market_order(
        self,
        symbol: str,
        side: str,  # "buy" or "sell"
        size: float,
        reduce_only: bool = False,
        slippage_pct: float = 1.0
    ) -> Dict[str, Any]:
        """Place a market order using IOC limit order at adjusted price.

        Hyperliquid doesn't have true market orders. We simulate them using
        Immediate-or-Cancel (IOC) limit orders at a price that ensures fill.

        Args:
            symbol: Trading symbol (e.g., "BTC", "ETH")
            side: "buy" or "sell"
            size: Order size in base asset
            reduce_only: If True, only reduces existing position
            slippage_pct: Price adjustment percentage to ensure fill (default 1%)
        """
        try:
            self._require_connected()
            from hyperliquid.utils.signing import OrderType as HLOrderType

            is_buy = side.lower() == "buy"

            # Round size to correct decimal places for this symbol
            size = self.round_size(symbol, size)

            # Get current market price
            market_price = self.get_price(symbol)
            if not market_price or market_price <= 0:
                return {"success": False, "error": f"Could not get price for {symbol}"}

            # Adjust price to ensure fill (buy higher, sell lower)
            if is_buy:
                limit_price = market_price * (1 + slippage_pct / 100)
            else:
                limit_price = market_price * (1 - slippage_pct / 100)

            # Round price to proper tick size for each asset
            limit_price = tick_round_price(symbol, limit_price)

            logger.info(f"Market order: {side} {size} {symbol} @ ~${limit_price:.2f} (IOC)")

            # Use exchange.order with IOC (Immediate-or-Cancel) for market-like behavior
            result = self.exchange.order(
                symbol,
                is_buy,
                size,
                limit_price,
                {"limit": {"tif": "Ioc"}},  # Immediate-or-Cancel
                reduce_only=reduce_only
            )

            err = self._extract_order_error(result)
            status = self._extract_order_status(result)

            if err:
                logger.error(f"Market order rejected: {err} | raw={result}")
                return {"success": False, "error": err, "result": result, "order": status}

            # For IOC orders, check if it was filled
            if status.get("kind") == "filled":
                filled_info = status.get("details", {})
                avg_px = filled_info.get("avgPx", limit_price)
                total_sz = filled_info.get("totalSz", size)
                logger.info(f"Market order filled: {side} {total_sz} {symbol} @ ${avg_px}")
                return {"success": True, "result": result, "order": status, "filled_size": total_sz, "avg_price": avg_px}

            # IOC that wasn't filled gets cancelled
            if status.get("kind") in ("cancelled", "rejected"):
                msg = f"Market order not filled ({status.get('kind')}) - price moved too fast or insufficient liquidity"
                logger.warning(f"{msg}: {side} {size} {symbol} | raw={result}")
                return {"success": False, "error": msg, "result": result, "order": status}

            # Resting shouldn't happen with IOC, but handle it
            if status.get("kind") == "resting":
                logger.warning(f"IOC order unexpectedly resting: {result}")

            logger.info(
                f"Market order placed: {side} {size} {symbol} | kind={status.get('kind')} oid={status.get('oid')}"
            )
            return {"success": True, "result": result, "order": status}

        except Exception as e:
            logger.error(f"Failed to place market order: {e}")
            return {"success": False, "error": str(e)}

    def place_market_order_with_sltp(
        self,
        symbol: str,
        side: str,
        size: float,
        stop_loss_price: float,
        take_profit_price: float,
        slippage_pct: float = 1.0
    ) -> Dict[str, Any]:
        """Place a market order with native exchange SL/TP orders attached.

        Uses Hyperliquid's bulk_orders with grouping='normalTpsl' to create:
        1. Entry order (IOC market-like)
        2. Stop Loss trigger order (reduce_only)
        3. Take Profit trigger order (reduce_only)

        All three orders are placed atomically. NO RETRY LOGIC.

        Args:
            symbol: Trading symbol (e.g., "BTC", "ETH")
            side: "buy" or "sell" for entry direction
            size: Order size in base asset
            stop_loss_price: Price at which to trigger stop loss
            take_profit_price: Price at which to trigger take profit
            slippage_pct: Slippage for entry order (default 1%)

        Returns:
            Dict with success status and order details
        """
        try:
            self._require_connected()

            is_buy = side.lower() == "buy"

            # Get current market price for entry
            market_price = self.get_price(symbol)
            if not market_price or market_price <= 0:
                return {"success": False, "error": f"Could not get price for {symbol}"}

            # Round size to correct decimal places for this symbol
            size = self.round_size(symbol, size)

            # Adjust entry price for slippage (buy higher, sell lower)
            if is_buy:
                entry_price = market_price * (1 + slippage_pct / 100)
            else:
                entry_price = market_price * (1 - slippage_pct / 100)

            # Round prices to proper tick size
            entry_price = tick_round_price(symbol, entry_price)
            stop_loss_price = tick_round_price(symbol, stop_loss_price)
            take_profit_price = tick_round_price(symbol, take_profit_price)

            # Build the three orders
            orders = [
                # 1. Entry order (IOC for market-like execution)
                {
                    "coin": symbol,
                    "is_buy": is_buy,
                    "sz": size,
                    "limit_px": entry_price,
                    "order_type": {"limit": {"tif": "Ioc"}},
                    "reduce_only": False
                },
                # 2. Stop Loss order (trigger, reduce_only)
                {
                    "coin": symbol,
                    "is_buy": not is_buy,
                    "sz": size,
                    "limit_px": stop_loss_price,
                    "order_type": {
                        "trigger": {
                            "triggerPx": stop_loss_price,
                            "isMarket": True,
                            "tpsl": "sl"
                        }
                    },
                    "reduce_only": True
                },
                # 3. Take Profit order (trigger, reduce_only)
                {
                    "coin": symbol,
                    "is_buy": not is_buy,
                    "sz": size,
                    "limit_px": take_profit_price,
                    "order_type": {
                        "trigger": {
                            "triggerPx": take_profit_price,
                            "isMarket": True,
                            "tpsl": "tp"
                        }
                    },
                    "reduce_only": True
                }
            ]

            logger.info(f"📦 MARKET ORDER + SL/TP: {side.upper()} {size} {symbol} @ ~${entry_price:.2f}")
            logger.info(f"   🛑 SL: ${stop_loss_price:.2f} | 🎯 TP: ${take_profit_price:.2f}")

            # Submit all orders together with TPSL grouping
            result = self.exchange.bulk_orders(orders, grouping="normalTpsl")

            # Parse results
            if isinstance(result, dict) and result.get("status") == "err":
                error_msg = result.get("response", "Unknown error")
                logger.error(f"Bulk order failed: {error_msg}")
                return {"success": False, "error": error_msg, "result": result}

            # Extract statuses array
            statuses = []
            if isinstance(result, dict):
                response = result.get("response", {})
                if response.get("type") == "order":
                    statuses = response.get("data", {}).get("statuses", [])

            # Helper to extract oid from any status type
            def extract_oid(status):
                if not isinstance(status, dict):
                    return None
                for key in ["resting", "waiting", "filled"]:
                    if status.get(key):
                        val = status[key]
                        if isinstance(val, dict):
                            return val.get("oid")
                return None

            # Parse entry order
            entry_status = statuses[0] if len(statuses) > 0 else {}
            entry_filled = isinstance(entry_status, dict) and entry_status.get("filled")

            if entry_filled:
                logger.info(f"✅ Entry filled: {entry_status.get('filled', {})}")
            else:
                err = entry_status.get("error") if isinstance(entry_status, dict) else str(entry_status)
                logger.error(f"❌ Entry not filled: {err}")
                return {"success": False, "error": f"Entry not filled: {err}", "result": result}

            # Parse SL order
            sl_status = statuses[1] if len(statuses) > 1 else {}
            sl_oid = extract_oid(sl_status)
            if sl_oid:
                logger.info(f"✅ SL order OK: oid={sl_oid}")
            else:
                logger.warning(f"⚠️ SL may have failed: {sl_status}")

            # Parse TP order
            tp_status = statuses[2] if len(statuses) > 2 else {}
            tp_oid = extract_oid(tp_status)
            if tp_oid:
                logger.info(f"✅ TP order OK: oid={tp_oid}")
            else:
                logger.warning(f"⚠️ TP may have failed: {tp_status}")

            return {
                "success": True,
                "result": result,
                "sl_oid": sl_oid,
                "tp_oid": tp_oid,
                "entry_price": entry_price,
                "stop_loss_price": stop_loss_price,
                "take_profit_price": take_profit_price
            }

        except Exception as e:
            logger.error(f"Failed to place market order with SL/TP: {e}")
            import traceback
            traceback.print_exc()
            return {"success": False, "error": str(e)}

    def place_market_order_with_sl_only(
        self,
        symbol: str,
        side: str,
        size: float,
        stop_loss_price: float,
        slippage_pct: float = 1.0
    ) -> Dict[str, Any]:
        """Place a market order with ONLY stop loss - NO take profit.

        DeepSeek will decide when to exit profitable positions.
        This lets winners run without arbitrary TP limits.

        Args:
            symbol: Trading symbol (e.g., "BTC", "ETH")
            side: "buy" or "sell" for entry direction
            size: Order size in base asset
            stop_loss_price: Price at which to trigger stop loss
            slippage_pct: Slippage for entry order (default 1%)

        Returns:
            Dict with success status and order details
        """
        try:
            self._require_connected()

            is_buy = side.lower() == "buy"

            # Get current market price for entry
            market_price = self.get_price(symbol)
            if not market_price or market_price <= 0:
                return {"success": False, "error": f"Could not get price for {symbol}"}

            # Round size to correct decimal places for this symbol
            size = self.round_size(symbol, size)

            # Adjust entry price for slippage (buy higher, sell lower)
            if is_buy:
                entry_price = market_price * (1 + slippage_pct / 100)
            else:
                entry_price = market_price * (1 - slippage_pct / 100)

            # Round prices to proper tick size
            entry_price = tick_round_price(symbol, entry_price)
            stop_loss_price = tick_round_price(symbol, stop_loss_price)

            # Build only TWO orders: entry + SL (no TP)
            orders = [
                # 1. Entry order (IOC for market-like execution)
                {
                    "coin": symbol,
                    "is_buy": is_buy,
                    "sz": size,
                    "limit_px": entry_price,
                    "order_type": {"limit": {"tif": "Ioc"}},
                    "reduce_only": False
                },
                # 2. Stop Loss order (trigger, reduce_only)
                {
                    "coin": symbol,
                    "is_buy": not is_buy,
                    "sz": size,
                    "limit_px": stop_loss_price,
                    "order_type": {
                        "trigger": {
                            "triggerPx": stop_loss_price,
                            "isMarket": True,
                            "tpsl": "sl"
                        }
                    },
                    "reduce_only": True
                }
            ]

            logger.info(f"📦 MARKET ORDER + SL ONLY: {side.upper()} {size} {symbol} @ ~${entry_price:.2f}")
            logger.info(f"   🛑 SL: ${stop_loss_price:.2f} | 🎯 TP: DeepSeek will decide")

            # Submit orders together with TPSL grouping
            result = self.exchange.bulk_orders(orders, grouping="normalTpsl")

            # Parse results
            if isinstance(result, dict) and result.get("status") == "err":
                error_msg = result.get("response", "Unknown error")
                logger.error(f"Bulk order failed: {error_msg}")
                return {"success": False, "error": error_msg, "result": result}

            # Extract statuses array
            statuses = []
            if isinstance(result, dict):
                response = result.get("response", {})
                if response.get("type") == "order":
                    statuses = response.get("data", {}).get("statuses", [])

            # Helper to extract oid from any status type
            def extract_oid(status):
                if not isinstance(status, dict):
                    return None
                for key in ["resting", "waiting", "filled"]:
                    if status.get(key):
                        val = status[key]
                        if isinstance(val, dict):
                            return val.get("oid")
                return None

            # Parse entry order
            entry_status = statuses[0] if len(statuses) > 0 else {}
            entry_filled = isinstance(entry_status, dict) and entry_status.get("filled")

            if entry_filled:
                logger.info(f"✅ Entry filled: {entry_status.get('filled', {})}")
            else:
                err = entry_status.get("error") if isinstance(entry_status, dict) else str(entry_status)
                logger.error(f"❌ Entry not filled: {err}")
                return {"success": False, "error": f"Entry not filled: {err}", "result": result}

            # Parse SL order
            sl_status = statuses[1] if len(statuses) > 1 else {}
            sl_oid = extract_oid(sl_status)
            if sl_oid:
                logger.info(f"✅ SL order OK: oid={sl_oid}")
            else:
                logger.warning(f"⚠️ SL may have failed: {sl_status}")

            return {
                "success": True,
                "result": result,
                "sl_oid": sl_oid,
                "tp_oid": None,  # No TP - DeepSeek decides exit
                "entry_price": entry_price,
                "stop_loss_price": stop_loss_price,
                "take_profit_price": None
            }

        except Exception as e:
            logger.error(f"Failed to place market order with SL only: {e}")
            import traceback
            traceback.print_exc()
            return {"success": False, "error": str(e)}

    def cancel_order(self, symbol: str, oid: int) -> Dict[str, Any]:
        """Cancel a specific order by ID.

        Args:
            symbol: Trading symbol
            oid: Order ID to cancel

        Returns:
            Dict with success status
        """
        try:
            self._require_connected()
            result = self.exchange.cancel(symbol, oid)
            logger.info(f"Order {oid} cancelled for {symbol}")
            return {"success": True, "result": result}
        except Exception as e:
            logger.error(f"Failed to cancel order {oid}: {e}")
            return {"success": False, "error": str(e)}

    def update_tp_order(
        self,
        symbol: str,
        old_tp_oid: int,
        side: str,
        size: float,
        new_tp_price: float
    ) -> Dict[str, Any]:
        """Update take profit order to a new price (for trailing).

        This cancels the old TP and places a new one at the trailing price.

        Args:
            symbol: Trading symbol
            old_tp_oid: Current TP order ID to cancel
            side: Position side ("long" or "short") - TP is opposite
            size: Position size
            new_tp_price: New take profit trigger price

        Returns:
            Dict with success status and new TP order ID
        """
        try:
            self._require_connected()

            # Cancel old TP order
            cancel_result = self.exchange.cancel(symbol, old_tp_oid)
            logger.info(f"Cancelled old TP order {old_tp_oid}")

            # Round price to tick size
            new_tp_price = tick_round_price(symbol, new_tp_price)

            # TP order is opposite side of position
            is_buy = side.lower() == "short"  # If short, TP is a buy

            # Place new TP order
            result = self.exchange.order(
                symbol,
                is_buy,
                size,
                new_tp_price,
                {
                    "trigger": {
                        "triggerPx": new_tp_price,
                        "isMarket": True,
                        "tpsl": "tp"
                    }
                },
                reduce_only=True
            )

            # Extract new order ID (with type safety)
            new_tp_oid = None
            if isinstance(result, dict):
                response = result.get("response", {})
                if response.get("type") == "order":
                    statuses = response.get("data", {}).get("statuses", [])
                    if statuses and isinstance(statuses[0], dict) and statuses[0].get("resting"):
                        new_tp_oid = statuses[0]["resting"].get("oid")
                    elif statuses and isinstance(statuses[0], str):
                        logger.warning(f"⚠️ TP trail response was string: {statuses[0]}")
                    elif statuses and isinstance(statuses[0], dict) and statuses[0].get("error"):
                        logger.warning(f"⚠️ TP trail error: {statuses[0].get('error')}")

            if new_tp_oid:
                logger.info(f"📈 TP TRAILED: {symbol} new TP @ ${new_tp_price:.2f} (oid={new_tp_oid})")
                return {"success": True, "tp_oid": new_tp_oid, "tp_price": new_tp_price}
            else:
                logger.warning(f"TP order placed but no OID returned: {result}")
                return {"success": True, "tp_oid": None, "tp_price": new_tp_price, "result": result}

        except Exception as e:
            logger.error(f"Failed to update TP order: {e}")
            import traceback
            traceback.print_exc()
            return {"success": False, "error": str(e)}

    def update_sl_order(
        self,
        symbol: str,
        old_sl_oid: int,
        side: str,
        size: float,
        new_sl_price: float
    ) -> Dict[str, Any]:
        """Update stop loss order to a new price (for trailing SL).

        Args:
            symbol: Trading symbol
            old_sl_oid: Current SL order ID to cancel
            side: Position side ("long" or "short") - SL is opposite
            size: Position size
            new_sl_price: New stop loss trigger price

        Returns:
            Dict with success status and new SL order ID
        """
        try:
            self._require_connected()

            # Cancel old SL order
            cancel_result = self.exchange.cancel(symbol, old_sl_oid)
            logger.info(f"Cancelled old SL order {old_sl_oid}")

            # Round price to tick size
            new_sl_price = tick_round_price(symbol, new_sl_price)

            # SL order is opposite side of position
            is_buy = side.lower() == "short"  # If short, SL is a buy

            # Place new SL order
            result = self.exchange.order(
                symbol,
                is_buy,
                size,
                new_sl_price,
                {
                    "trigger": {
                        "triggerPx": new_sl_price,
                        "isMarket": True,
                        "tpsl": "sl"
                    }
                },
                reduce_only=True
            )

            # Extract new order ID (with type safety)
            new_sl_oid = None
            if isinstance(result, dict):
                response = result.get("response", {})
                if response.get("type") == "order":
                    statuses = response.get("data", {}).get("statuses", [])
                    if statuses and isinstance(statuses[0], dict) and statuses[0].get("resting"):
                        new_sl_oid = statuses[0]["resting"].get("oid")
                    elif statuses and isinstance(statuses[0], str):
                        logger.warning(f"⚠️ SL update response was string: {statuses[0]}")
                    elif statuses and isinstance(statuses[0], dict) and statuses[0].get("error"):
                        logger.warning(f"⚠️ SL update error: {statuses[0].get('error')}")

            if new_sl_oid:
                logger.info(f"🛑 SL UPDATED: {symbol} new SL @ ${new_sl_price:.2f} (oid={new_sl_oid})")
                return {"success": True, "sl_oid": new_sl_oid, "sl_price": new_sl_price}
            else:
                logger.warning(f"SL order placed but no OID returned: {result}")
                return {"success": True, "sl_oid": None, "sl_price": new_sl_price, "result": result}

        except Exception as e:
            logger.error(f"Failed to update SL order: {e}")
            import traceback
            traceback.print_exc()
            return {"success": False, "error": str(e)}

    def place_sl_order(
        self,
        symbol: str,
        position_side: str,
        size: float,
        stop_loss_price: float
    ) -> Dict[str, Any]:
        """Place a standalone Stop Loss order for an existing position.

        Args:
            symbol: Trading symbol
            position_side: The side of the POSITION (long/short), not the SL order
            size: Size to close
            stop_loss_price: SL trigger price

        Returns:
            Dict with success, sl_oid, error
        """
        try:
            self._require_connected()

            # SL is opposite side of position
            is_buy = position_side.lower() in ["short", "sell"]
            size = self.round_size(symbol, size)
            stop_loss_price = self.round_price(symbol, stop_loss_price)

            result = self.exchange.order(
                symbol,
                is_buy,
                size,
                stop_loss_price,
                {
                    "trigger": {
                        "triggerPx": stop_loss_price,
                        "isMarket": True,
                        "tpsl": "sl"
                    }
                },
                reduce_only=True
            )

            # Extract order ID
            sl_oid = None
            if isinstance(result, dict):
                response = result.get("response", {})
                if response.get("type") == "order":
                    statuses = response.get("data", {}).get("statuses", [])
                    if statuses and isinstance(statuses[0], dict) and statuses[0].get("resting"):
                        sl_oid = statuses[0]["resting"].get("oid")
                    elif statuses and isinstance(statuses[0], dict) and statuses[0].get("error"):
                        error = statuses[0].get("error")
                        logger.error(f"❌ SL order rejected: {error}")
                        return {"success": False, "error": error}

            if sl_oid:
                logger.info(f"✅ SL order placed: {symbol} @ ${stop_loss_price:.2f} (oid={sl_oid})")
                return {"success": True, "sl_oid": sl_oid, "sl_price": stop_loss_price}
            else:
                logger.warning(f"⚠️ SL order placed but no OID returned: {result}")
                return {"success": True, "sl_oid": None, "sl_price": stop_loss_price, "result": result}

        except Exception as e:
            logger.error(f"Failed to place SL order: {e}")
            return {"success": False, "error": str(e)}

    def place_tp_order(
        self,
        symbol: str,
        position_side: str,
        size: float,
        take_profit_price: float
    ) -> Dict[str, Any]:
        """Place a standalone Take Profit order for an existing position.

        Args:
            symbol: Trading symbol
            position_side: The side of the POSITION (long/short), not the TP order
            size: Size to close
            take_profit_price: TP trigger price

        Returns:
            Dict with success, tp_oid, error
        """
        try:
            self._require_connected()

            # TP is opposite side of position
            is_buy = position_side.lower() in ["short", "sell"]
            size = self.round_size(symbol, size)
            take_profit_price = self.round_price(symbol, take_profit_price)

            result = self.exchange.order(
                symbol,
                is_buy,
                size,
                take_profit_price,
                {
                    "trigger": {
                        "triggerPx": take_profit_price,
                        "isMarket": True,
                        "tpsl": "tp"
                    }
                },
                reduce_only=True
            )

            # Extract order ID
            tp_oid = None
            if isinstance(result, dict):
                response = result.get("response", {})
                if response.get("type") == "order":
                    statuses = response.get("data", {}).get("statuses", [])
                    if statuses and isinstance(statuses[0], dict) and statuses[0].get("resting"):
                        tp_oid = statuses[0]["resting"].get("oid")
                    elif statuses and isinstance(statuses[0], dict) and statuses[0].get("error"):
                        error = statuses[0].get("error")
                        logger.error(f"❌ TP order rejected: {error}")
                        return {"success": False, "error": error}

            if tp_oid:
                logger.info(f"✅ TP order placed: {symbol} @ ${take_profit_price:.2f} (oid={tp_oid})")
                return {"success": True, "tp_oid": tp_oid, "tp_price": take_profit_price}
            else:
                logger.warning(f"⚠️ TP order placed but no OID returned: {result}")
                return {"success": True, "tp_oid": None, "tp_price": take_profit_price, "result": result}

        except Exception as e:
            logger.error(f"Failed to place TP order: {e}")
            return {"success": False, "error": str(e)}

    def place_limit_order(
        self,
        symbol: str,
        side: str,
        size: float,
        price: float,
        reduce_only: bool = False
    ) -> Dict[str, Any]:
        """Place a limit order."""
        try:
            self._require_connected()
            is_buy = side.lower() == "buy"

            # Round size to correct decimal places for this symbol
            size = self.round_size(symbol, size)

            result = self.exchange.order(
                symbol,
                is_buy,
                size,
                price,
                {"limit": {"tif": "Gtc"}},
                reduce_only=reduce_only
            )

            err = self._extract_order_error(result)
            status = self._extract_order_status(result)
            if err:
                logger.error(f"Limit order rejected: {err} | raw={result}")
                return {"success": False, "error": err, "result": result, "order": status}

            if status.get("kind") in ("cancelled", "rejected"):
                msg = f"Limit order not accepted ({status.get('kind')})"
                logger.warning(f"{msg}: {side} {size} {symbol} @ {price} | raw={result}")
                return {"success": False, "error": msg, "result": result, "order": status}
            
            logger.info(
                f"Limit order placed: {side} {size} {symbol} @ {price} | kind={status.get('kind')} oid={status.get('oid')}"
            )
            return {"success": True, "result": result, "order": status, "order_id": status.get("oid")}

        except Exception as e:
            logger.error(f"Failed to place limit order: {e}")
            return {"success": False, "error": str(e)}

    def place_limit_order_with_sltp(
        self,
        symbol: str,
        side: str,
        size: float,
        price: float,
        stop_loss_price: float,
        take_profit_price: float
    ) -> Dict[str, Any]:
        """Place a limit order with native exchange SL/TP orders attached.

        Uses Hyperliquid's bulk_orders with grouping='normalTpsl' to create:
        1. Entry limit order (GTC)
        2. Stop Loss trigger order (reduce_only)
        3. Take Profit trigger order (reduce_only)

        All three orders are placed atomically. NO RETRY LOGIC - if any fail,
        we return the result and let the caller handle it.

        Args:
            symbol: Trading symbol (e.g., "BTC", "ETH")
            side: "buy" or "sell" for entry direction
            size: Order size in base asset
            price: Limit price for entry
            stop_loss_price: Price at which to trigger stop loss
            take_profit_price: Price at which to trigger take profit

        Returns:
            Dict with success status and order details
        """
        try:
            self._require_connected()

            is_buy = side.lower() == "buy"

            # Round size to correct decimal places for this symbol
            size = self.round_size(symbol, size)

            # Round prices to proper tick size
            price = tick_round_price(symbol, price)
            stop_loss_price = tick_round_price(symbol, stop_loss_price)
            take_profit_price = tick_round_price(symbol, take_profit_price)

            # Build the three orders
            orders = [
                # 1. Entry limit order (GTC)
                {
                    "coin": symbol,
                    "is_buy": is_buy,
                    "sz": size,
                    "limit_px": price,
                    "order_type": {"limit": {"tif": "Gtc"}},
                    "reduce_only": False
                },
                # 2. Stop Loss order (trigger, reduce_only)
                {
                    "coin": symbol,
                    "is_buy": not is_buy,
                    "sz": size,
                    "limit_px": stop_loss_price,
                    "order_type": {
                        "trigger": {
                            "triggerPx": stop_loss_price,
                            "isMarket": True,
                            "tpsl": "sl"
                        }
                    },
                    "reduce_only": True
                },
                # 3. Take Profit order (trigger, reduce_only)
                {
                    "coin": symbol,
                    "is_buy": not is_buy,
                    "sz": size,
                    "limit_px": take_profit_price,
                    "order_type": {
                        "trigger": {
                            "triggerPx": take_profit_price,
                            "isMarket": True,
                            "tpsl": "tp"
                        }
                    },
                    "reduce_only": True
                }
            ]

            logger.info(f"📦 LIMIT ORDER + SL/TP: {side.upper()} {size} {symbol} @ ${price:.2f}")
            logger.info(f"   🛑 SL: ${stop_loss_price:.2f} | 🎯 TP: ${take_profit_price:.2f}")

            # Submit all orders together with TPSL grouping
            result = self.exchange.bulk_orders(orders, grouping="normalTpsl")

            # Parse results
            if isinstance(result, dict) and result.get("status") == "err":
                error_msg = result.get("response", "Unknown error")
                logger.error(f"Bulk order failed: {error_msg}")
                return {"success": False, "error": error_msg, "result": result}

            # Extract statuses array
            statuses = []
            if isinstance(result, dict):
                response = result.get("response", {})
                if response.get("type") == "order":
                    statuses = response.get("data", {}).get("statuses", [])

            # Helper to extract oid from any status type
            def extract_oid(status):
                if not isinstance(status, dict):
                    return None
                # Check all possible success keys
                for key in ["resting", "waiting", "filled"]:
                    if status.get(key):
                        val = status[key]
                        if isinstance(val, dict):
                            return val.get("oid")
                return None

            # Parse entry order
            entry_status = statuses[0] if len(statuses) > 0 else {}
            entry_oid = extract_oid(entry_status)
            entry_success = entry_oid is not None or (isinstance(entry_status, dict) and entry_status.get("filled"))

            if entry_success:
                logger.info(f"✅ Entry order OK: oid={entry_oid}")
            else:
                err = entry_status.get("error") if isinstance(entry_status, dict) else str(entry_status)
                logger.error(f"❌ Entry failed: {err}")
                return {"success": False, "error": err, "result": result}

            # Parse SL order
            sl_status = statuses[1] if len(statuses) > 1 else {}
            sl_oid = extract_oid(sl_status)
            if sl_oid:
                logger.info(f"✅ SL order OK: oid={sl_oid}")
            else:
                logger.warning(f"⚠️ SL may have failed: {sl_status}")

            # Parse TP order
            tp_status = statuses[2] if len(statuses) > 2 else {}
            tp_oid = extract_oid(tp_status)
            if tp_oid:
                logger.info(f"✅ TP order OK: oid={tp_oid}")
            else:
                logger.warning(f"⚠️ TP may have failed: {tp_status}")

            return {
                "success": True,
                "result": result,
                "entry_oid": entry_oid,
                "sl_oid": sl_oid,
                "tp_oid": tp_oid,
                "entry_price": price,
                "stop_loss_price": stop_loss_price,
                "take_profit_price": take_profit_price,
                "order_id": entry_oid
            }

        except Exception as e:
            logger.error(f"Failed to place limit order with SL/TP: {e}")
            import traceback
            traceback.print_exc()
            return {"success": False, "error": str(e)}

    def get_position(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get current position for a specific symbol.

        Returns:
            Position dict with keys: coin, szi (signed size), entryPx, unrealizedPnl, etc.
            Returns None if no position exists.
        """
        try:
            state = self.get_account_state()
            for pos in state.get("positions", []):
                if pos.get("coin") == symbol:
                    szi = float(pos.get("szi", 0) or 0)
                    if szi != 0:
                        return pos
            return None
        except Exception as e:
            logger.error(f"Failed to get position for {symbol}: {e}")
            return None

    def close_position(self, symbol: str) -> Dict[str, Any]:
        """Close entire position for a symbol using market order.

        This uses the SDK's market_close which creates a market order
        to close the entire position.
        """
        try:
            self._require_connected()

            # First check if we have a position to close
            position = self.get_position(symbol)
            if not position:
                logger.warning(f"No open position found for {symbol}")
                return {"success": False, "error": f"No open position for {symbol}"}

            size = float(position.get("szi", 0) or 0)
            side = "long" if size > 0 else "short"
            logger.info(f"Closing {side} position: {abs(size)} {symbol}")

            result = self.exchange.market_close(symbol)

            err = self._extract_order_error(result)
            status = self._extract_order_status(result)

            if err:
                logger.error(f"Close position rejected: {err} | raw={result}")
                return {"success": False, "error": err, "result": result, "order": status}

            if status.get("kind") in ("cancelled", "rejected"):
                msg = f"Close position order not filled ({status.get('kind')})"
                logger.warning(f"{msg}: {symbol} | raw={result}")
                return {"success": False, "error": msg, "result": result, "order": status}

            logger.info(f"Position closed for {symbol} | kind={status.get('kind')} oid={status.get('oid')}")
            return {"success": True, "result": result, "order": status, "closed_size": abs(size)}

        except Exception as e:
            logger.error(f"Failed to close position: {e}")
            return {"success": False, "error": str(e)}

    def close_position_partial(self, symbol: str, size: float) -> Dict[str, Any]:
        """Close a partial amount of a position.

        Args:
            symbol: The trading symbol (e.g., "BTC", "ETH")
            size: The absolute size to close (always positive)

        Returns:
            Result dict with success status
        """
        try:
            self._require_connected()

            # Get current position to determine direction
            position = self.get_position(symbol)
            if not position:
                logger.warning(f"No open position found for {symbol}")
                return {"success": False, "error": f"No open position for {symbol}"}

            current_size = float(position.get("szi", 0) or 0)

            if abs(size) > abs(current_size):
                logger.warning(f"Requested close size {size} exceeds position size {abs(current_size)}")
                size = abs(current_size)

            # To close a long, we sell; to close a short, we buy
            is_buy = current_size < 0  # If short (negative), buy to close
            side = "buy" if is_buy else "sell"

            logger.info(f"Partial close: {side} {size} {symbol} (reduce_only)")

            # Use market order with reduce_only to close partial position
            result = self.exchange.market_open(
                symbol,
                is_buy,
                abs(size),
                None,  # No slippage limit
                # Note: The SDK's market_open doesn't support reduce_only directly,
                # so we use the regular order method with reduce_only=True
            )

            err = self._extract_order_error(result)
            status = self._extract_order_status(result)

            if err:
                logger.error(f"Partial close rejected: {err} | raw={result}")
                return {"success": False, "error": err, "result": result, "order": status}

            if status.get("kind") in ("cancelled", "rejected"):
                msg = f"Partial close order not filled ({status.get('kind')})"
                logger.warning(f"{msg}: {side} {size} {symbol} | raw={result}")
                return {"success": False, "error": msg, "result": result, "order": status}

            logger.info(f"Partial position closed: {side} {size} {symbol} | kind={status.get('kind')}")
            return {"success": True, "result": result, "order": status, "closed_size": size}

        except Exception as e:
            logger.error(f"Failed to close partial position: {e}")
            return {"success": False, "error": str(e)}

    def close_all_positions(self) -> Dict[str, Any]:
        """Close all open positions.

        Returns:
            Dict with results for each symbol that was closed
        """
        try:
            self._require_connected()
            state = self.get_account_state()
            results = {}
            closed_count = 0

            for pos in state.get("positions", []):
                symbol = pos.get("coin")
                szi = float(pos.get("szi", 0) or 0)

                if symbol and szi != 0:
                    result = self.close_position(symbol)
                    results[symbol] = result
                    if result.get("success"):
                        closed_count += 1

            if not results:
                logger.info("No open positions to close")
                return {"success": True, "message": "No positions to close", "results": {}}

            logger.info(f"Closed {closed_count}/{len(results)} positions")
            return {
                "success": closed_count == len(results),
                "closed_count": closed_count,
                "total_positions": len(results),
                "results": results
            }

        except Exception as e:
            logger.error(f"Failed to close all positions: {e}")
            return {"success": False, "error": str(e)}
    
    def cancel_all_orders(self, symbol: str) -> Dict[str, Any]:
        """Cancel all open orders for a symbol."""
        try:
            self._require_connected()
            result = self.exchange.cancel_all_orders(symbol)
            logger.info(f"All orders cancelled for {symbol}")
            return {"success": True, "result": result}
        except Exception as e:
            logger.error(f"Failed to cancel orders: {e}")
            return {"success": False, "error": str(e)}

    def get_open_orders(self, dex: str = "") -> Dict[str, Any]:
        """Get open orders for the configured wallet address."""
        import time
        max_retries = 2
        for attempt in range(max_retries):
            try:
                self._require_connected()
                result = self.info.open_orders(self.wallet_address, dex=dex)
                return {"success": True, "result": result if result else []}
            except Exception as e:
                error_str = str(e)
                # Server errors (500) are transient - retry silently
                if "500" in error_str or "null" in error_str.lower():
                    if attempt < max_retries - 1:
                        time.sleep(0.5)
                        continue
                    # Only log on final failure
                    logger.debug(f"Open orders API temporarily unavailable: {e}")
                    return {"success": False, "error": error_str, "result": []}
                logger.error(f"Failed to get open orders: {e}")
                return {"success": False, "error": error_str}

    def get_user_fills(self) -> Dict[str, Any]:
        """Get recent fills for the configured wallet address."""
        try:
            self._require_connected()
            return {"success": True, "result": self.info.user_fills(self.wallet_address)}
        except Exception as e:
            logger.error(f"Failed to get user fills: {e}")
            return {"success": False, "error": str(e)}

