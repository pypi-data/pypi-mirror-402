"""OAuth 2.0 + PKCE login flow for Claude Max subscription"""

import base64
import hashlib
import secrets
import time
import webbrowser
from urllib.parse import urlencode

import httpx

# Official Claude Code OAuth configuration
# Source: https://github.com/sst/opencode (provider.ts, auth/anthropic.ts)
# Key insight: Use claude.ai for Max subscription, not console.anthropic.com
CLAUDE_CLIENT_ID = "9d1c250a-e61b-44d9-88ed-5944d1962f5e"

# IMPORTANT: For Claude Max subscription, use claude.ai NOT console.anthropic.com!
# console.anthropic.com/oauth/authorize is for API key creation
# claude.ai/oauth/authorize is for Max subscription inference
OAUTH_AUTHORIZE_URL_MAX = "https://claude.ai/oauth/authorize"
OAUTH_AUTHORIZE_URL_CONSOLE = "https://console.anthropic.com/oauth/authorize"
OAUTH_TOKEN_URL = "https://console.anthropic.com/v1/oauth/token"
REDIRECT_URI = "https://console.anthropic.com/oauth/code/callback"

# IMPORTANT: Include org:create_api_key for full access
SCOPES = "org:create_api_key user:profile user:inference"


def generate_pkce_pair() -> tuple[str, str]:
    """
    Generate PKCE code_verifier and code_challenge.

    Returns:
        Tuple of (code_verifier, code_challenge)
    """
    # code_verifier: 43-128 chars, URL-safe random string
    code_verifier = secrets.token_urlsafe(32)

    # code_challenge: base64url(SHA256(code_verifier))
    digest = hashlib.sha256(code_verifier.encode()).digest()
    code_challenge = base64.urlsafe_b64encode(digest).rstrip(b"=").decode()

    return code_verifier, code_challenge


def generate_auth_url(code_challenge: str, state: str, mode: str = "max") -> str:
    """
    Generate the OAuth authorization URL.

    Args:
        code_challenge: PKCE code challenge
        state: Random state for CSRF protection
        mode: "max" for Claude Max subscription, "console" for API key creation

    Returns:
        Full authorization URL to redirect user to
    """
    # Use claude.ai for Max subscription (inference access)
    # Use console.anthropic.com for API key creation
    base_url = OAUTH_AUTHORIZE_URL_MAX if mode == "max" else OAUTH_AUTHORIZE_URL_CONSOLE

    params = {
        "client_id": CLAUDE_CLIENT_ID,
        "response_type": "code",
        "redirect_uri": REDIRECT_URI,
        "scope": SCOPES,
        "code_challenge": code_challenge,
        "code_challenge_method": "S256",
        "state": state,
    }
    return f"{base_url}?{urlencode(params)}"


def open_browser_auth(code_challenge: str, state: str, mode: str = "max") -> None:
    """
    Open browser with authorization URL.

    Args:
        code_challenge: PKCE code challenge
        state: Random state for CSRF protection
        mode: "max" for Claude Max subscription, "console" for API key creation
    """
    url = generate_auth_url(code_challenge, state, mode)
    webbrowser.open(url)


async def exchange_code_for_tokens(code: str, code_verifier: str, state: str) -> dict:
    """
    Exchange authorization code for access/refresh tokens.

    Args:
        code: Authorization code from OAuth callback
        code_verifier: Original PKCE code verifier
        state: Original state value for CSRF protection

    Returns:
        Token response dict with accessToken, refreshToken, expiresAt

    Raises:
        Exception: If token exchange fails
    """
    # Clean the code (remove any URL fragments or extra params)
    # Source: https://github.com/grll/claude-code-login
    clean_code = code.split("#")[0].split("&")[0].strip()

    async with httpx.AsyncClient() as client:
        # OAuth token endpoint requires browser-like headers
        # Source: https://github.com/grll/claude-code-login
        response = await client.post(
            OAUTH_TOKEN_URL,
            json={
                "grant_type": "authorization_code",
                "client_id": CLAUDE_CLIENT_ID,
                "code": clean_code,
                "redirect_uri": REDIRECT_URI,
                "code_verifier": code_verifier,
                "state": state,
            },
            headers={
                "Content-Type": "application/json",
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
                "Accept": "application/json, text/plain, */*",
                "Accept-Language": "en-US,en;q=0.9",
                "Referer": "https://claude.ai/",
                "Origin": "https://claude.ai",
            },
            timeout=30.0,
        )

        if response.status_code != 200:
            raise Exception(f"Token exchange failed: {response.text}")

        # Response uses snake_case, convert to camelCase for consistency
        data = response.json()
        return {
            "accessToken": data.get("access_token"),
            "refreshToken": data.get("refresh_token"),
            "expiresAt": (int(time.time()) + data.get("expires_in", 3600)) * 1000,
        }
