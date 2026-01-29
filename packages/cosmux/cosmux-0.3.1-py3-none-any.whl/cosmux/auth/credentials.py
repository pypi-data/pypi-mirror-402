"""Claude credentials handling for Max subscription support"""

import json
import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Tuple

import httpx

# Path for credentials storage
COSMUX_CREDENTIALS_PATH = Path.home() / ".cosmux" / "credentials.json"

# Official Claude Code client ID (for token refresh)
# Source: https://github.com/RavenStorm-bit/claude-token-refresh
CLAUDE_CLIENT_ID = "9d1c250a-e61b-44d9-88ed-5944d1962f5e"
OAUTH_TOKEN_URL = "https://console.anthropic.com/v1/oauth/token"


@dataclass
class AuthResult:
    """Authentication result with token and source info"""
    token: str
    source: str  # "api_key", "oauth_env", "oauth_cosmux", "oauth_refreshed"
    refresh_token: Optional[str] = None
    expires_at: Optional[int] = None  # Unix timestamp in milliseconds


def get_credentials() -> Optional[AuthResult]:
    """
    Get API credentials with priority:
    1. ANTHROPIC_API_KEY (pay-per-token)
    2. ~/.cosmux/credentials.json (cosmux login)
    3. CLAUDE_OAUTH_TOKEN env (manually copied)

    Returns:
        AuthResult with token and source info, or None if no credentials found
    """
    # Priority 1: Standard API key
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if api_key:
        return AuthResult(token=api_key, source="api_key")

    # Priority 2: Cosmux own credentials (from cosmux login)
    cosmux_creds = load_cosmux_credentials()
    if cosmux_creds:
        return cosmux_creds

    # Priority 3: OAuth token from environment (manually copied)
    oauth_token = os.environ.get("CLAUDE_OAUTH_TOKEN")
    if oauth_token:
        refresh = os.environ.get("CLAUDE_REFRESH_TOKEN")
        return AuthResult(token=oauth_token, source="oauth_env", refresh_token=refresh)

    return None


def load_cosmux_credentials() -> Optional[AuthResult]:
    """
    Load credentials from ~/.cosmux/credentials.json

    Returns:
        AuthResult if credentials exist and are valid, None otherwise
    """
    if not COSMUX_CREDENTIALS_PATH.exists():
        return None

    try:
        data = json.loads(COSMUX_CREDENTIALS_PATH.read_text())
        access_token = data.get("accessToken")
        if access_token:
            return AuthResult(
                token=access_token,
                source="oauth_cosmux",
                refresh_token=data.get("refreshToken"),
                expires_at=data.get("expiresAt"),
            )
    except (json.JSONDecodeError, KeyError):
        pass

    return None


def save_credentials(tokens: dict) -> None:
    """
    Save OAuth credentials to ~/.cosmux/credentials.json

    Args:
        tokens: Dict with accessToken, refreshToken, expiresAt
    """
    COSMUX_CREDENTIALS_PATH.parent.mkdir(parents=True, exist_ok=True)
    COSMUX_CREDENTIALS_PATH.write_text(json.dumps(tokens, indent=2))


def is_token_expired(expires_at: Optional[int], buffer_seconds: int = 300) -> bool:
    """
    Check if token is expired or will expire soon.

    Args:
        expires_at: Token expiration timestamp in milliseconds
        buffer_seconds: Buffer time before expiration (default 5 minutes)

    Returns:
        True if token is expired or will expire within buffer time
    """
    if not expires_at:
        return False  # Can't determine, assume valid
    current_ms = int(time.time() * 1000)
    buffer_ms = buffer_seconds * 1000
    return current_ms > (expires_at - buffer_ms)


async def refresh_oauth_token(refresh_token: str) -> Optional[AuthResult]:
    """
    Refresh an expired OAuth access token using the refresh token.

    Endpoint: POST https://console.anthropic.com/v1/oauth/token

    Source: https://github.com/RavenStorm-bit/claude-token-refresh

    Args:
        refresh_token: The OAuth refresh token

    Returns:
        New AuthResult with refreshed token, or None if refresh failed
    """
    async with httpx.AsyncClient() as client:
        try:
            print(f"[DEBUG Refresh] Attempting token refresh...")
            print(f"[DEBUG Refresh] URL: {OAUTH_TOKEN_URL}")
            print(f"[DEBUG Refresh] refresh_token: {refresh_token[:20]}...")

            # OAuth token endpoint requires browser-like headers
            response = await client.post(
                OAUTH_TOKEN_URL,
                json={
                    "grant_type": "refresh_token",
                    "refresh_token": refresh_token,
                    "client_id": CLAUDE_CLIENT_ID,
                },
                headers={
                    "Content-Type": "application/json",
                    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
                    "Accept": "application/json, text/plain, */*",
                    "Accept-Language": "en-US,en;q=0.9",
                    "Referer": "https://claude.ai/",
                    "Origin": "https://claude.ai",
                },
                timeout=10.0,
            )

            print(f"[DEBUG Refresh] Response status: {response.status_code}")
            print(f"[DEBUG Refresh] Response body: {response.text[:500]}")

            if response.status_code == 200:
                data = response.json()
                # Handle both camelCase and snake_case responses
                access_token = data.get("accessToken") or data.get("access_token")
                new_refresh = data.get("refreshToken") or data.get("refresh_token") or refresh_token
                expires_at = data.get("expiresAt")
                if not expires_at and data.get("expires_in"):
                    expires_at = int((time.time() + data["expires_in"]) * 1000)

                new_auth = AuthResult(
                    token=access_token,
                    source="oauth_refreshed",
                    refresh_token=new_refresh,
                    expires_at=expires_at,
                )

                # Update stored credentials
                save_credentials({
                    "accessToken": new_auth.token,
                    "refreshToken": new_auth.refresh_token,
                    "expiresAt": new_auth.expires_at,
                })

                print(f"[DEBUG Refresh] Success! New token: {access_token[:20]}...")
                return new_auth
            else:
                print(f"[Warning] Token refresh failed with status {response.status_code}")
        except Exception as e:
            print(f"[Warning] Failed to refresh OAuth token: {e}")
            import traceback
            traceback.print_exc()

    return None


def get_auth_source_display(source: str) -> Tuple[str, str]:
    """
    Get display info for auth source.

    Args:
        source: The auth source identifier

    Returns:
        Tuple of (message, rich_style)
    """
    if source == "api_key":
        return "Using API key (pay-per-token)", "blue"
    elif source in ("oauth_env", "oauth_refreshed"):
        return "Using Claude Max (CLAUDE_OAUTH_TOKEN)", "green"
    elif source == "oauth_cosmux":
        return "Using Claude Max (cosmux login)", "green"
    return "Unknown auth source", "yellow"
