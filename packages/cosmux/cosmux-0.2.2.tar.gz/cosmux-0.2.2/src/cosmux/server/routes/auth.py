"""Authentication endpoints for OAuth login"""

import secrets
from typing import Optional

from fastapi import APIRouter
from pydantic import BaseModel

from cosmux.auth.credentials import get_credentials, save_credentials, get_auth_source_display
from cosmux.auth.oauth import (
    generate_pkce_pair,
    generate_auth_url,
    exchange_code_for_tokens,
)

router = APIRouter()

# Store PKCE state temporarily (in memory)
# Note: In production with multiple workers, use Redis or similar
_pending_logins: dict[str, tuple[str, str]] = {}  # state -> (code_verifier, state)


class AuthStatusResponse(BaseModel):
    """Response for auth status check"""
    authenticated: bool
    source: Optional[str] = None
    message: Optional[str] = None


class InitLoginResponse(BaseModel):
    """Response for login initialization"""
    authUrl: str
    state: str


class CompleteLoginRequest(BaseModel):
    """Request to complete login with authorization code"""
    code: str
    state: str


class CompleteLoginResponse(BaseModel):
    """Response for login completion"""
    success: bool
    message: str


@router.get("/status", response_model=AuthStatusResponse)
async def auth_status() -> AuthStatusResponse:
    """Check if server has valid credentials"""
    creds = get_credentials()
    if creds:
        message, _ = get_auth_source_display(creds.source)
        return AuthStatusResponse(
            authenticated=True,
            source=creds.source,
            message=message,
        )
    return AuthStatusResponse(authenticated=False)


@router.post("/init-login", response_model=InitLoginResponse)
async def init_login() -> InitLoginResponse:
    """
    Start OAuth login flow.

    Returns URL to open in browser and state for verification.
    """
    code_verifier, code_challenge = generate_pkce_pair()
    state = secrets.token_urlsafe(32)

    # Store code_verifier and state for later verification
    _pending_logins[state] = (code_verifier, state)

    auth_url = generate_auth_url(code_challenge, state)

    return InitLoginResponse(authUrl=auth_url, state=state)


@router.post("/complete-login", response_model=CompleteLoginResponse)
async def complete_login(request: CompleteLoginRequest) -> CompleteLoginResponse:
    """
    Complete OAuth login by exchanging code for tokens.

    The user should have pasted the authorization code from their browser.
    """
    # Get stored code_verifier and state
    stored = _pending_logins.pop(request.state, None)
    if not stored:
        return CompleteLoginResponse(
            success=False,
            message="Invalid or expired state. Please try again.",
        )

    code_verifier, state = stored

    try:
        tokens = await exchange_code_for_tokens(request.code, code_verifier, state)
        save_credentials({
            "accessToken": tokens["accessToken"],
            "refreshToken": tokens.get("refreshToken", ""),
            "expiresAt": tokens.get("expiresAt", 0),
        })
        return CompleteLoginResponse(
            success=True,
            message="Login successful! You can now use Cosmux with your Claude Max subscription.",
        )
    except Exception as e:
        return CompleteLoginResponse(
            success=False,
            message=f"Login failed: {str(e)}",
        )


@router.post("/logout", response_model=CompleteLoginResponse)
async def logout() -> CompleteLoginResponse:
    """
    Logout by removing stored credentials.

    Note: This only removes Cosmux credentials, not Claude Code credentials.
    """
    from pathlib import Path
    credentials_path = Path.home() / ".cosmux" / "credentials.json"

    if credentials_path.exists():
        credentials_path.unlink()
        return CompleteLoginResponse(
            success=True,
            message="Logged out successfully.",
        )

    return CompleteLoginResponse(
        success=True,
        message="No credentials to remove.",
    )
