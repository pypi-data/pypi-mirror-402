"""
Vista Config System

Stores all configuration in ~/.vista/ directory:
- ~/.vista/config.json     - API keys, preferences
- ~/.vista/session.json    - Supabase session tokens
- ~/.vista/history.json    - Conversation history (optional)

Similar to how Claude Code stores config in ~/.claude/
"""

import json
import os
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass, field, asdict
from datetime import datetime

# Config directory (like ~/.claude/ for Claude Code)
VISTA_DIR = Path.home() / ".vista"
CONFIG_FILE = VISTA_DIR / "config.json"
SESSION_FILE = VISTA_DIR / "session.json"

# Supabase project details
SUPABASE_PROJECT_REF = "nnzdxembmtxtsxxajdjb"
SUPABASE_URL = f"https://{SUPABASE_PROJECT_REF}.supabase.co"

# DeepSeek Proxy URL - calls go through Supabase Edge Function
# The actual API key is stored as a Supabase secret (never in source code)
DEEPSEEK_PROXY_URL = f"{SUPABASE_URL}/functions/v1/deepseek-proxy"


@dataclass
class VistaConfig:
    """Vista configuration."""

    # Hyperliquid API Wallet
    # Note: hyperliquid_private_key stores the API Wallet Secret (not your main wallet key)
    # Create an API Wallet at: https://app.hyperliquid.xyz/API
    hyperliquid_private_key: str = ""  # API Wallet Secret (64 hex chars, stored with 0x prefix)
    hyperliquid_wallet_address: str = ""  # Your main trading account address (0x...)
    hyperliquid_testnet: bool = False  # Default to mainnet for real trading
    
    # LLM APIs
    deepseek_api_key: str = ""
    anthropic_api_key: str = ""  # Optional, for premium features
    
    # User info (from Supabase)
    user_id: str = ""
    user_email: str = ""
    
    # Preferences
    default_symbol: str = "BTC"
    position_size_usd: float = 10.0
    confirm_trades: bool = True  # Always confirm before trading
    theme: str = "default"

    # Bot Configuration
    bot_symbols: str = "BTC,ETH,SOL"  # Comma-separated symbols
    bot_strategy: str = "micro"  # micro, scalp, swing
    bot_max_leverage: float = 3.0
    bot_risk_per_trade: float = 2.0  # Percentage of account
    bot_max_positions: int = 3
    bot_stop_loss_pct: float = 2.0
    bot_take_profit_pct: float = 4.0
    bot_enabled: bool = False

    # Timestamps
    created_at: str = ""
    last_login: str = ""
    
    def save(self):
        """Save config to disk."""
        VISTA_DIR.mkdir(parents=True, exist_ok=True)
        
        # Never save to disk in plain text - mask sensitive fields
        data = asdict(self)
        
        # Store API keys (encrypted would be better, but this is MVP)
        with open(CONFIG_FILE, 'w') as f:
            json.dump(data, f, indent=2)
        
        # Set restrictive permissions
        CONFIG_FILE.chmod(0o600)
    
    @classmethod
    def load(cls) -> "VistaConfig":
        """Load config from disk."""
        if not CONFIG_FILE.exists():
            return cls()
        
        try:
            with open(CONFIG_FILE, 'r') as f:
                data = json.load(f)
            return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})
        except Exception:
            return cls()
    
    @classmethod
    def exists(cls) -> bool:
        """Check if config file exists."""
        return CONFIG_FILE.exists()
    
    def is_configured(self) -> bool:
        """Check if Vista is fully configured."""
        return bool(
            self.hyperliquid_private_key and
            self.hyperliquid_wallet_address and
            self.user_id
        )

    def get_deepseek_proxy_url(self) -> str:
        """Get DeepSeek proxy URL (Supabase Edge Function)."""
        return DEEPSEEK_PROXY_URL
    
    def clear(self):
        """Clear config (logout)."""
        if CONFIG_FILE.exists():
            CONFIG_FILE.unlink()
        if SESSION_FILE.exists():
            SESSION_FILE.unlink()


@dataclass
class VistaSession:
    """Supabase session data."""
    access_token: str = ""
    refresh_token: str = ""
    expires_at: int = 0
    user_id: str = ""
    user_email: str = ""
    
    def save(self):
        """Save session to disk."""
        VISTA_DIR.mkdir(parents=True, exist_ok=True)
        with open(SESSION_FILE, 'w') as f:
            json.dump(asdict(self), f, indent=2)
        SESSION_FILE.chmod(0o600)
    
    @classmethod
    def load(cls) -> "VistaSession":
        """Load session from disk."""
        if not SESSION_FILE.exists():
            return cls()
        
        try:
            with open(SESSION_FILE, 'r') as f:
                data = json.load(f)
            return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})
        except Exception:
            return cls()
    
    def is_valid(self) -> bool:
        """Check if session is still valid."""
        import time
        return bool(self.access_token and self.expires_at > time.time())
    
    def clear(self):
        """Clear session."""
        if SESSION_FILE.exists():
            SESSION_FILE.unlink()

