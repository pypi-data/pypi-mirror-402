"""
Unified Ticker Configuration - Single source of truth for all trading symbols.

To add a new ticker:
1. Add it to TRADING_TICKERS list
2. Add tick size to TICK_SIZES
3. Add max leverage to MAX_LEVERAGE
4. Add Discord channel env var to .env: DISCORD_CHANNEL_{SYMBOL}_SIGNALS=channel_id
"""

from typing import Dict, List

# =============================================================================
# MASTER TICKER LIST - Add new tickers here
# Note: Only add tickers that are actively listed on Hyperliquid MAINNET
# Check with: hl.info.meta() -> 'isDelisted' should be False
# =============================================================================
TRADING_TICKERS: List[str] = [
    "BTC",
    "ETH",
    "SOL",
    "ZEC",
    "SUI",
    "XRP",
    "ADA",
]

# =============================================================================
# TICK SIZES - Price precision for each asset (Hyperliquid requirements)
# Default is 0.01 for unknown assets
# =============================================================================
TICK_SIZES: Dict[str, float] = {
    "BTC": 1.0,
    "ETH": 0.1,
    "SOL": 0.01,
    "ZEC": 0.01,
    "SUI": 0.0001,
    "XRP": 0.0001,
    "ADA": 0.0001,
    # Other common assets (not actively traded but may appear)
    "AVAX": 0.01,
    "BNB": 0.01,
    "DOGE": 0.00001,
    "DOT": 0.001,
    "MATIC": 0.0001,
    "LINK": 0.01,
    "UNI": 0.01,
    "LTC": 0.01,
    "ARB": 0.0001,
    "OP": 0.001,
    "AAVE": 0.01,
}

DEFAULT_TICK_SIZE: float = 0.01

# =============================================================================
# MAX LEVERAGE - Per-asset leverage limits on Hyperliquid
# =============================================================================
MAX_LEVERAGE: Dict[str, int] = {
    "BTC": 40,
    "ETH": 25,
    "SOL": 20,
    "ZEC": 10,
    "SUI": 10,
    "XRP": 20,
    "ADA": 10,
    # Other assets
    "AVAX": 20,
    "BNB": 20,
    "DOGE": 10,
    "DOT": 10,
    "MATIC": 10,
}

DEFAULT_MAX_LEVERAGE: int = 10

# =============================================================================
# SIZE DECIMALS - Position size precision for each asset (Hyperliquid requirements)
# This is how many decimal places for position size (e.g., BTC: 5 = 0.00001 BTC)
# =============================================================================
SIZE_DECIMALS: Dict[str, int] = {
    "BTC": 5,    # 0.00001 BTC
    "ETH": 4,    # 0.0001 ETH
    "SOL": 2,    # 0.01 SOL
    "ZEC": 3,    # 0.001 ZEC
    "SUI": 1,    # 0.1 SUI
    "XRP": 1,    # 0.1 XRP
    "ADA": 0,    # 1 ADA (whole units)
    # Other assets
    "AVAX": 2,
    "BNB": 3,
    "DOGE": 0,
    "DOT": 2,
    "MATIC": 1,
}

DEFAULT_SIZE_DECIMALS: int = 2

# =============================================================================
# CORRELATION GROUPS - Assets that move together
# Used to prevent opposing positions in correlated assets
# =============================================================================
CORRELATION_GROUPS: Dict[str, List[str]] = {
    "crypto": TRADING_TICKERS + ["AVAX", "MATIC", "BNB", "DOGE", "DOT", "LINK"],
}

# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def get_tick_size(symbol: str) -> float:
    """Get tick size for a symbol."""
    return TICK_SIZES.get(symbol.upper(), DEFAULT_TICK_SIZE)


def get_max_leverage(symbol: str) -> int:
    """Get max leverage for a symbol."""
    return MAX_LEVERAGE.get(symbol.upper(), DEFAULT_MAX_LEVERAGE)


def round_price(symbol: str, price: float) -> float:
    """Round price to correct tick size for symbol."""
    tick = get_tick_size(symbol)
    return round(price / tick) * tick


def get_size_decimals(symbol: str) -> int:
    """Get size decimal precision for a symbol."""
    return SIZE_DECIMALS.get(symbol.upper(), DEFAULT_SIZE_DECIMALS)


def is_trading_ticker(symbol: str) -> bool:
    """Check if symbol is in active trading list."""
    return symbol.upper() in TRADING_TICKERS


def get_discord_channel_env(symbol: str) -> str:
    """Get env var name for a symbol's Discord channel."""
    return f"DISCORD_CHANNEL_{symbol.upper()}_SIGNALS"


def format_price(price: float, symbol: str = None) -> str:
    """Format price with appropriate decimal places based on price magnitude.

    This ensures prices display correctly for all assets:
    - BTC ($95,000) → $95,000
    - ETH ($3,300) → $3,300.00
    - XRP ($2.18) → $2.18
    - ADA ($0.42) → $0.4200
    - SUI ($1.87) → $1.87

    Args:
        price: The price to format
        symbol: Optional symbol for context (currently unused but reserved)

    Returns:
        Formatted price string with $ prefix
    """
    if price >= 1000:
        return f"${price:,.0f}"
    elif price >= 100:
        return f"${price:,.2f}"
    elif price >= 10:
        return f"${price:.2f}"
    elif price >= 1:
        return f"${price:.2f}"
    elif price >= 0.01:
        return f"${price:.4f}"
    else:
        return f"${price:.6f}"


def format_price_range(low: float, high: float, symbol: str = None) -> str:
    """Format a price range with consistent decimals."""
    # Use the smaller price to determine decimal places
    if min(low, high) >= 1000:
        return f"${low:,.0f} - ${high:,.0f}"
    elif min(low, high) >= 10:
        return f"${low:.2f} - ${high:.2f}"
    elif min(low, high) >= 1:
        return f"${low:.2f} - ${high:.2f}"
    else:
        return f"${low:.4f} - ${high:.4f}"

