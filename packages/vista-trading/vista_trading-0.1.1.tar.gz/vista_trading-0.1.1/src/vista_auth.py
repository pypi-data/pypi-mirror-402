"""
Vista Auth - Supabase Authentication

Handles:
- Sign up with email/password
- Login with email/password
- Session management
- Token refresh
"""

import httpx
import time
from typing import Optional, Tuple, Dict, Any

from src.vista_config import VistaSession, VistaConfig

# Supabase project credentials
SUPABASE_URL = "https://nnzdxembmtxtsxxajdjb.supabase.co"
SUPABASE_ANON_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im5uemR4ZW1ibXR4dHN4eGFqZGpiIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjgzOTg3MTcsImV4cCI6MjA4Mzk3NDcxN30.9TPcASLAGpghSBNTL9Di5yjBO08iqg5rSuii9RQqMjk"


class VistaAuth:
    """Supabase authentication for Vista CLI."""
    
    def __init__(self):
        self.session = VistaSession.load()
        self.config = VistaConfig.load()
        
    def is_authenticated(self) -> bool:
        """Check if user is authenticated."""
        return self.session.is_valid()
    
    async def signup(self, email: str, password: str) -> Tuple[bool, str]:
        """Sign up with email and password."""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{SUPABASE_URL}/auth/v1/signup",
                headers={
                    "apikey": SUPABASE_ANON_KEY,
                    "Content-Type": "application/json"
                },
                json={
                    "email": email,
                    "password": password
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Check if email confirmation required
                if data.get("confirmation_sent_at"):
                    return True, "Check your email to confirm your account!"
                
                # Auto-login if no confirmation required
                if data.get("access_token"):
                    self._save_session(data)
                    return True, "Account created and logged in!"
                
                return True, "Account created! Please log in."
            
            error = response.json().get("error_description", response.json().get("msg", "Signup failed"))
            return False, error
    
    async def login(self, email: str, password: str) -> Tuple[bool, str]:
        """Login with email and password."""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{SUPABASE_URL}/auth/v1/token?grant_type=password",
                headers={
                    "apikey": SUPABASE_ANON_KEY,
                    "Content-Type": "application/json"
                },
                json={
                    "email": email,
                    "password": password
                }
            )

            if response.status_code == 200:
                data = response.json()
                self._save_session(data)

                # Sync settings from cloud (load saved wallet info)
                await self.sync_settings_from_cloud()

                return True, f"Welcome back, {email}!"

            error = response.json().get("error_description", "Login failed")
            return False, error
    
    async def refresh_session(self) -> bool:
        """Refresh the session token."""
        if not self.session.refresh_token:
            return False
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{SUPABASE_URL}/auth/v1/token?grant_type=refresh_token",
                headers={
                    "apikey": SUPABASE_ANON_KEY,
                    "Content-Type": "application/json"
                },
                json={"refresh_token": self.session.refresh_token}
            )
            
            if response.status_code == 200:
                data = response.json()
                self._save_session(data)
                return True
            
            return False
    
    def _save_session(self, data: Dict[str, Any]):
        """Save session data."""
        user = data.get("user", {})
        
        self.session = VistaSession(
            access_token=data.get("access_token", ""),
            refresh_token=data.get("refresh_token", ""),
            expires_at=int(time.time()) + data.get("expires_in", 3600),
            user_id=user.get("id", ""),
            user_email=user.get("email", "")
        )
        self.session.save()
        
        # Also update config with user info
        self.config.user_id = user.get("id", "")
        self.config.user_email = user.get("email", "")
        self.config.last_login = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        self.config.save()
    
    def logout(self):
        """Logout - clear session and optionally config."""
        self.session.clear()
        # Keep API keys, just clear auth
        self.config.user_id = ""
        self.config.user_email = ""
        self.config.save()

    def get_user_email(self) -> str:
        """Get current user email."""
        return self.session.user_email or self.config.user_email

    async def sync_settings_to_cloud(self) -> bool:
        """Save user settings to Supabase."""
        if not self.is_authenticated():
            return False

        async with httpx.AsyncClient() as client:
            # Check if settings exist
            response = await client.get(
                f"{SUPABASE_URL}/rest/v1/user_settings?user_id=eq.{self.session.user_id}&select=id",
                headers={
                    "apikey": SUPABASE_ANON_KEY,
                    "Authorization": f"Bearer {self.session.access_token}",
                }
            )

            settings_data = {
                "user_id": self.session.user_id,
                "hyperliquid_private_key": self.config.hyperliquid_private_key,
                "hyperliquid_wallet_address": self.config.hyperliquid_wallet_address,
                "hyperliquid_testnet": self.config.hyperliquid_testnet,
                "bot_symbols": self.config.bot_symbols,
                "bot_strategy": self.config.bot_strategy,
                "bot_max_leverage": self.config.bot_max_leverage,
                "bot_max_positions": self.config.bot_max_positions,
                "bot_stop_loss_pct": self.config.bot_stop_loss_pct,
                "bot_take_profit_pct": self.config.bot_take_profit_pct,
                "position_size_usd": self.config.position_size_usd,
            }

            if response.status_code == 200 and response.json():
                # Update existing
                response = await client.patch(
                    f"{SUPABASE_URL}/rest/v1/user_settings?user_id=eq.{self.session.user_id}",
                    headers={
                        "apikey": SUPABASE_ANON_KEY,
                        "Authorization": f"Bearer {self.session.access_token}",
                        "Content-Type": "application/json",
                        "Prefer": "return=minimal"
                    },
                    json=settings_data
                )
            else:
                # Insert new
                response = await client.post(
                    f"{SUPABASE_URL}/rest/v1/user_settings",
                    headers={
                        "apikey": SUPABASE_ANON_KEY,
                        "Authorization": f"Bearer {self.session.access_token}",
                        "Content-Type": "application/json",
                        "Prefer": "return=minimal"
                    },
                    json=settings_data
                )

            return response.status_code in (200, 201, 204)

    async def sync_settings_from_cloud(self) -> bool:
        """Load user settings from Supabase."""
        if not self.is_authenticated():
            return False

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{SUPABASE_URL}/rest/v1/user_settings?user_id=eq.{self.session.user_id}&select=*",
                    headers={
                        "apikey": SUPABASE_ANON_KEY,
                        "Authorization": f"Bearer {self.session.access_token}",
                    }
                )

                if response.status_code == 200:
                    data = response.json()
                    if data and len(data) > 0:
                        settings = data[0]
                        # Update local config
                        if settings.get("hyperliquid_private_key"):
                            self.config.hyperliquid_private_key = settings["hyperliquid_private_key"]
                        if settings.get("hyperliquid_wallet_address"):
                            self.config.hyperliquid_wallet_address = settings["hyperliquid_wallet_address"]
                        if settings.get("hyperliquid_testnet") is not None:
                            self.config.hyperliquid_testnet = settings["hyperliquid_testnet"]
                        if settings.get("bot_symbols"):
                            self.config.bot_symbols = settings["bot_symbols"]
                        if settings.get("bot_strategy"):
                            self.config.bot_strategy = settings["bot_strategy"]
                        if settings.get("bot_max_leverage"):
                            self.config.bot_max_leverage = settings["bot_max_leverage"]
                        if settings.get("bot_max_positions"):
                            self.config.bot_max_positions = settings["bot_max_positions"]
                        if settings.get("bot_stop_loss_pct"):
                            self.config.bot_stop_loss_pct = settings["bot_stop_loss_pct"]
                        if settings.get("bot_take_profit_pct"):
                            self.config.bot_take_profit_pct = settings["bot_take_profit_pct"]
                        if settings.get("position_size_usd"):
                            self.config.position_size_usd = settings["position_size_usd"]

                        self.config.save()
                        return True
                    # No settings found for this user - that's ok, they'll set up fresh
                    return False
                else:
                    # API error - continue without cloud sync
                    return False
        except Exception:
            # Network error - continue without cloud sync
            return False

