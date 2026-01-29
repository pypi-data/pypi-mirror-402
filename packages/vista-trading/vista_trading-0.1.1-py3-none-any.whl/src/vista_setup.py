"""
Vista Setup Wizard

First-run onboarding experience:
1. Welcome screen
2. Sign up / Login
3. API key configuration
4. Test connection
5. Ready to trade!
"""

import asyncio
import re
from typing import Optional, Tuple

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.markdown import Markdown
from rich.table import Table

from src.vista_config import VistaConfig, VistaSession, VISTA_DIR
from src.vista_auth import VistaAuth


class VistaSetup:
    """First-run setup wizard for Vista CLI."""
    
    def __init__(self, console: Console):
        self.console = console
        self.config = VistaConfig.load()
        self.auth = VistaAuth()
        
    async def run_if_needed(self) -> bool:
        """Run setup if needed. Returns True if ready to use."""
        
        # Check if already configured
        if self.config.is_configured() and self.auth.is_authenticated():
            return True
        
        # Need setup
        return await self.run_setup()
    
    async def run_setup(self) -> bool:
        """Run the full setup wizard."""

        # Welcome screen
        self._show_welcome()

        # Step 1: Authentication
        if not self.auth.is_authenticated():
            if not await self._auth_step():
                return False
            # Reload config after auth - cloud sync may have restored settings
            self.config = VistaConfig.load()
        else:
            self.console.print(f"[green]✓ Logged in as {self.auth.get_user_email()}[/]")

        # Step 2: API Keys (only check Hyperliquid - DeepSeek has built-in key)
        if not self.config.hyperliquid_private_key or not self.config.hyperliquid_wallet_address:
            if not await self._api_keys_step():
                return False
        else:
            self.console.print("[green]✓ Wallet connected[/]")
        
        # Step 3: Test connection
        if not await self._test_connection():
            return False
        
        # Done!
        self._show_ready()
        return True
    
    def _show_welcome(self):
        """Show welcome screen with gradient logo."""
        self.console.clear()

        # Two slanted bars \\ with cyan-to-orange gradient (Vista logo)
        self.console.print()
        self.console.print("[bright_cyan]                 ██╗      ██╗[/]")
        self.console.print("[cyan]                 ╚██╗    ██╔╝[/]")
        self.console.print("[blue]                  ╚██╗  ██╔╝[/]")
        self.console.print("[yellow]                   ╚██╗██╔╝[/]")
        self.console.print("[orange1]                    ╚███╔╝[/]")
        self.console.print("[dark_orange]                     ╚══╝[/]")
        self.console.print()
        self.console.print("[bold bright_cyan]              V I S T A[/]")
        self.console.print()
        self.console.print("[dim]           AI-Powered Trading Terminal[/]")
        self.console.print()
        self.console.print(Panel(
            "Let's get you set up:\n\n"
            "  [bright_cyan]1.[/] Create account or login\n"
            "  [cyan]2.[/] Connect your Hyperliquid wallet\n"
            "  [yellow]3.[/] Start trading!\n",
            border_style="dim",
            padding=(0, 2)
        ))
        self.console.print()
    
    async def _auth_step(self) -> bool:
        """Handle authentication step."""
        self.console.print("[bold]Step 1: Authentication[/]\n")
        
        choice = Prompt.ask(
            "Do you have a Vista account?",
            choices=["login", "signup", "quit"],
            default="signup"
        )
        
        if choice == "quit":
            return False
        
        email = Prompt.ask("[cyan]Email[/]")
        if not self._validate_email(email):
            self.console.print("[red]Invalid email address[/]")
            return await self._auth_step()
        
        password = Prompt.ask("[cyan]Password[/]", password=True)
        if len(password) < 6:
            self.console.print("[red]Password must be at least 6 characters[/]")
            return await self._auth_step()
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[cyan]Authenticating...[/]"),
            console=self.console,
            transient=True
        ) as progress:
            progress.add_task("", total=None)
            
            if choice == "signup":
                success, message = await self.auth.signup(email, password)
            else:
                success, message = await self.auth.login(email, password)
        
        if success:
            self.console.print(f"[green]✓ {message}[/]\n")
            self.config = VistaConfig.load()  # Reload with user info
            return True
        else:
            self.console.print(f"[red]✗ {message}[/]\n")
            return await self._auth_step()
    
    def _validate_email(self, email: str) -> bool:
        """Validate email format."""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))

    async def _api_keys_step(self) -> bool:
        """Handle API keys configuration."""
        self.console.print("[bold]Step 2: Connect Your Hyperliquid API Wallet[/]\n")

        self.console.print(Panel(
            "[bold yellow]⚠️  You need an API Wallet (NOT your main wallet private key)[/]\n\n"
            "[cyan]How to create an API Wallet:[/]\n"
            "  1. Go to [link=https://app.hyperliquid.xyz/API]app.hyperliquid.xyz/API[/link]\n"
            "  2. Click 'Create API Wallet'\n"
            "  3. Copy the [bold]API Wallet Secret[/] (64 hex characters)\n"
            "  4. Your [bold]Wallet Address[/] is your main account (0x...)\n\n"
            "[dim]The API Wallet Secret is stored locally in ~/.vista/[/]",
            title="🔑 API Wallet Setup",
            border_style="yellow"
        ))
        self.console.print()

        # Hyperliquid API Wallet Secret (visible so paste works)
        self.console.print("[dim]Paste your API Wallet Secret (it will be visible):[/]")
        private_key = Prompt.ask("[cyan]API Wallet Secret[/]")

        # Strip 0x prefix if present, validate 64 hex chars
        private_key = private_key.strip()
        if private_key.startswith("0x"):
            private_key = private_key[2:]

        # Validate it's 64 hex characters
        if len(private_key) != 64 or not all(c in '0123456789abcdefABCDEF' for c in private_key):
            self.console.print("[red]Invalid API Wallet Secret (should be 64 hex characters)[/]")
            return await self._api_keys_step()

        # Wallet Address (the main account address, not the API wallet address)
        self.console.print("[dim]Your main Hyperliquid wallet address (the account you trade with):[/]")
        wallet = Prompt.ask("[cyan]Wallet Address[/]")
        if not wallet.startswith("0x") or len(wallet) != 42:
            self.console.print("[red]Invalid wallet address (should be 0x... followed by 40 hex chars)[/]")
            return await self._api_keys_step()

        # Network selection
        testnet = Confirm.ask(
            "[cyan]Use testnet?[/] (recommended for testing)",
            default=False
        )

        # Save config - store with 0x prefix for consistency with eth libs
        self.config.hyperliquid_private_key = "0x" + private_key
        self.config.hyperliquid_wallet_address = wallet
        self.config.hyperliquid_testnet = testnet
        self.config.save()

        # Sync to cloud so settings persist across devices
        await self.auth.sync_settings_to_cloud()

        self.console.print("[green]✓ Wallet connected and synced to your account[/]\n")
        return True

    async def _test_connection(self) -> bool:
        """Test the Hyperliquid connection."""
        self.console.print("[bold]Step 3: Testing Connection[/]\n")

        with Progress(
            SpinnerColumn(),
            TextColumn("[cyan]Connecting to Hyperliquid...[/]"),
            console=self.console,
            transient=True
        ) as progress:
            progress.add_task("", total=None)

            try:
                from src.hyperliquid_client import HyperliquidClient

                client = HyperliquidClient(
                    private_key=self.config.hyperliquid_private_key,
                    wallet_address=self.config.hyperliquid_wallet_address,
                    testnet=self.config.hyperliquid_testnet
                )

                connected = await client.connect()

                if connected:
                    # Get account info
                    state = client.get_account_state()
                    equity = state.get('equity', 0)
                    network = "Testnet" if self.config.hyperliquid_testnet else "Mainnet"

                    self.console.print(f"[green]✓ Connected to {network}[/]")
                    self.console.print(f"[green]✓ Account equity: ${equity:,.2f}[/]\n")
                    return True
                else:
                    self.console.print("[red]✗ Failed to connect[/]")
                    return False

            except Exception as e:
                self.console.print(f"[red]✗ Connection error: {e}[/]")
                if Confirm.ask("Re-enter API keys?", default=True):
                    return await self._api_keys_step() and await self._test_connection()
                return False

    def _show_ready(self):
        """Show ready screen."""
        self.console.print(Panel.fit(
            "[bold green]You're all set![/]\n\n"
            "Try these commands:\n"
            "  [cyan]prices[/]         Show current prices\n"
            "  [cyan]analyze BTC[/]    Technical analysis\n"
            "  [cyan]positions[/]      Your open positions\n"
            "  [cyan]help[/]           All commands\n\n"
            "Or just chat naturally:\n"
            "  [dim]\"what do you think about ETH right now?\"[/]\n"
            "  [dim]\"should I go long on SOL?\"[/]\n\n"
            "[yellow]Happy vibe trading! 🔮[/]",
            title="✨ Ready",
            border_style="green",
            padding=(1, 2)
        ))
        self.console.print()
