"""Authentication module for Claude Max subscription support"""

from cosmux.auth.credentials import (
    AuthResult,
    get_credentials,
    save_credentials,
    load_cosmux_credentials,
    is_token_expired,
    refresh_oauth_token,
    get_auth_source_display,
)
from cosmux.auth.oauth import (
    generate_pkce_pair,
    generate_auth_url,
    exchange_code_for_tokens,
    open_browser_auth,
    CLAUDE_CLIENT_ID,
)

__all__ = [
    # Credentials
    "AuthResult",
    "get_credentials",
    "save_credentials",
    "load_cosmux_credentials",
    "is_token_expired",
    "refresh_oauth_token",
    "get_auth_source_display",
    # OAuth
    "generate_pkce_pair",
    "generate_auth_url",
    "exchange_code_for_tokens",
    "open_browser_auth",
    "CLAUDE_CLIENT_ID",
]
