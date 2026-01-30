"""Configuration management for Lyceum CLI"""

import json
import os
import time
from pathlib import Path

import jwt
import typer
from rich.console import Console
from supabase import create_client

console = Console()

# Configuration
CONFIG_DIR = Path.home() / ".lyceum"
CONFIG_FILE = CONFIG_DIR / "config.json"

# Supabase configuration - these are public anon keys safe for client-side use
SUPABASE_URL = os.getenv("SUPABASE_URL", "https://tqcebgbexyszvqhnwnhh.supabase.co")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InRxY2ViZ2JleHlzenZxaG53bmhoIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDcxNTQ0NzEsImV4cCI6MjA2MjczMDQ3MX0.VvPV8oRJUSGadaPf9RwTn6URuC_5oL7KulsJgE2vpH4")


class _Config:
    """Configuration management for Lyceum CLI (private - use the global 'config' instance)"""

    def __init__(self):
        """Initialize configuration with default values"""
        self.api_key: str | None = None
        self.base_url: str = "https://api.lyceum.technology"  # Production API URL
        self.refresh_token: str | None = None
        self.dashboard_url: str = "https://dashboard.lyceum.technology"
        self.load()

    def load(self):
        """Load configuration from file"""
        if CONFIG_FILE.exists():
            try:
                with open(CONFIG_FILE) as f:
                    data = json.load(f)
                    self.api_key = data.get("api_key")
                    self.base_url = data.get("base_url", self.base_url)
                    self.refresh_token = data.get("refresh_token")
                    self.dashboard_url = data.get("dashboard_url", self.dashboard_url)
            except Exception as e:
                console.print(f"[yellow]Warning: Could not load config: {e}[/yellow]")

    def save(self):
        """Save configuration to file"""
        CONFIG_DIR.mkdir(exist_ok=True)
        with open(CONFIG_FILE, "w") as f:
            json.dump({
                "api_key": self.api_key,
                "base_url": self.base_url,
                "refresh_token": self.refresh_token,
                "dashboard_url": self.dashboard_url,
            }, f, indent=2)

    def is_token_expired(self) -> bool:
        """Check if the current token is expired or will expire soon (within 5 minutes)"""
        if not self.api_key:
            return True

        # Legacy API keys (starting with lk_) don't expire
        if self.api_key.startswith('lk_'):
            return False

        try:
            # Decode without verification to get expiration
            decoded = jwt.decode(self.api_key, options={"verify_signature": False})
            exp = decoded.get('exp', 0)

            # Check if token expires within 5 minutes (300 seconds)
            current_time = time.time()
            return (exp - current_time) <= 300

        except Exception:
            # If we can't decode the token, assume it's expired
            return True

    def refresh_access_token(self) -> bool:
        """Attempt to refresh the access token using Supabase refresh token"""
        if not self.refresh_token:
            return False

        # Only refresh JWT tokens, not legacy API keys
        if self.api_key and self.api_key.startswith('lk_'):
            return False

        try:
            # Check if Supabase credentials are configured
            if not SUPABASE_URL or not SUPABASE_ANON_KEY:
                console.print(
                    "[red]Error: SUPABASE_URL and SUPABASE_ANON_KEY environment variables must be set[/red]"
                )
                return False

            # Use Supabase's refresh_session method with the public anon key
            # This is safe for client-side use and properly scoped for user token refresh
            supabase = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)

            # Use refresh_session method
            response = supabase.auth.refresh_session(refresh_token=self.refresh_token)

            if response.session and response.session.access_token:
                # Successfully refreshed
                self.api_key = response.session.access_token
                if response.session.refresh_token:
                    self.refresh_token = response.session.refresh_token
                self.save()
                console.print("[dim]Token refreshed automatically[/dim]")
                return True
            else:
                # Refresh failed
                error_msg = getattr(response, 'error', None)
                if error_msg:
                    console.print(f"[yellow]Token refresh failed: {error_msg.message}[/yellow]")
                else:
                    console.print("[yellow]Token refresh failed: No session returned[/yellow]")
                return False

        except Exception as e:
            console.print(f"[yellow]Token refresh error: {e}[/yellow]")
            return False

    def get_client(self):
        """Get authenticated API client with automatic token refresh"""
        if not self.api_key:
            console.print("[red]Error: Not authenticated. Run 'lyceum auth login' first.[/red]")
            raise typer.Exit(1)

        # Check if token is expired and try to refresh
        if self.is_token_expired():
            console.print("[dim]Token expired, attempting refresh...[/dim]")
            if not self.refresh_access_token():
                console.print("[red]Token refresh failed. Please run 'lyceum login' again.[/red]")
                raise typer.Exit(1)

        # Return config instance - commands use httpx directly
        return self


# Global config instance
config = _Config()
