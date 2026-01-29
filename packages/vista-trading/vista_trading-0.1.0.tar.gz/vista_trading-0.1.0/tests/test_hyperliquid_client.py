import unittest


class TestHyperliquidClientHelpers(unittest.TestCase):
    def test_normalize_asset_positions_nested(self):
        from src.hyperliquid_client import HyperliquidClient

        raw = [
            {"position": {"coin": "ETH", "szi": "1", "entryPx": "2000"}, "type": "oneWay"}
        ]
        out = HyperliquidClient._normalize_asset_positions(raw)
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0]["coin"], "ETH")
        self.assertEqual(out[0]["szi"], "1")

    def test_normalize_asset_positions_passthrough(self):
        from src.hyperliquid_client import HyperliquidClient

        raw = [{"coin": "BTC", "szi": "-0.01"}]
        out = HyperliquidClient._normalize_asset_positions(raw)
        self.assertEqual(out, raw)

    def test_normalize_asset_positions_bad_input(self):
        from src.hyperliquid_client import HyperliquidClient

        self.assertEqual(HyperliquidClient._normalize_asset_positions(None), [])
        self.assertEqual(HyperliquidClient._normalize_asset_positions({}), [])

    def test_extract_order_error_top_level(self):
        from src.hyperliquid_client import HyperliquidClient

        res = {"status": "err", "error": "bad"}
        self.assertEqual(HyperliquidClient._extract_order_error(res), "bad")

    def test_extract_order_error_nested_statuses(self):
        from src.hyperliquid_client import HyperliquidClient

        res = {
            "status": "ok",
            "response": {"data": {"statuses": [{"error": "Insufficient margin"}]}}
        }
        self.assertEqual(HyperliquidClient._extract_order_error(res), "Insufficient margin")

    def test_extract_order_error_none_for_success(self):
        from src.hyperliquid_client import HyperliquidClient

        res = {
            "status": "ok",
            "response": {"data": {"statuses": [{"resting": {"oid": 123}}]}},
        }
        self.assertIsNone(HyperliquidClient._extract_order_error(res))


class TestTradingBotSizing(unittest.TestCase):
    def test_rounding_up_does_not_reduce_notional_below_min(self):
        import asyncio
        from src.trading_bot import BotConfig, TradingBot
        from src.llm_service import TradeSignal

        class _DummyHL:
            def __init__(self):
                self.last_order = None

            def place_market_order(self, symbol: str, side: str, size: float, reduce_only: bool = False):
                self.last_order = {"symbol": symbol, "side": side, "size": size, "reduce_only": reduce_only}
                return {"success": True, "result": {"status": "ok"}}

        bot = TradingBot(_DummyHL(), object(), BotConfig(position_size_usd=10.0, min_order_value_usd=10.0))

        symbol = "SOL"
        price = 99.99
        signal = TradeSignal(action="long", confidence=1.0, reasoning="test")
        market_data = {"symbol": symbol, "price": price}

        asyncio.run(bot._execute_signal(signal, market_data))

        self.assertIsNotNone(bot.hl.last_order)
        self.assertEqual(bot.hl.last_order["symbol"], symbol)
        self.assertEqual(bot.hl.last_order["side"], "buy")
        # With 2 decimals, ceil(10/99.99) -> 0.11
        self.assertAlmostEqual(bot.hl.last_order["size"], 0.11, places=8)
        self.assertGreaterEqual(bot.hl.last_order["size"] * price, 10.0)


if __name__ == "__main__":
    unittest.main()

