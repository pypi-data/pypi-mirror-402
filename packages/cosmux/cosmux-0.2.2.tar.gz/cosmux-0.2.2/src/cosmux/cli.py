"""CLI entry point for Cosmux"""

import asyncio
import os
import secrets
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel

app = typer.Typer(
    name="cosmux",
    help="AI Coding Agent Widget for Web Development",
    no_args_is_help=True,
)
console = Console()


def _show_auth_status() -> None:
    """Display current authentication status"""
    from cosmux.auth.credentials import get_credentials, get_auth_source_display

    auth = get_credentials()
    if auth:
        message, style = get_auth_source_display(auth.source)
        console.print(f"[{style}]{message}[/{style}]")
    else:
        console.print(
            "[yellow]No credentials found. Run 'cosmux login' or set ANTHROPIC_API_KEY.[/yellow]"
        )


@app.command()
def serve(
    port: int = typer.Option(3333, "--port", "-p", help="Server port"),
    host: str = typer.Option("127.0.0.1", "--host", "-h", help="Server host"),
    workspace: Optional[Path] = typer.Option(
        None,
        "--workspace",
        "-w",
        help="Workspace directory (default: current directory)",
    ),
    reload: bool = typer.Option(False, "--reload", "-r", help="Enable hot reload"),
) -> None:
    """Start the Cosmux server in the specified workspace"""
    import uvicorn

    # Resolve workspace
    workspace_path = (workspace or Path.cwd()).resolve()

    if not workspace_path.exists():
        console.print(f"[red]Error: Workspace directory does not exist: {workspace_path}[/red]")
        raise typer.Exit(1)

    if not workspace_path.is_dir():
        console.print(f"[red]Error: Workspace path is not a directory: {workspace_path}[/red]")
        raise typer.Exit(1)

    # Set workspace in environment for the app
    os.environ["COSMUX_WORKSPACE"] = str(workspace_path)

    # Display startup info
    console.print(
        Panel.fit(
            f"[bold green]Cosmux Server Starting[/bold green]\n\n"
            f"[dim]Workspace:[/dim] [cyan]{workspace_path}[/cyan]\n"
            f"[dim]Chat:[/dim]      [link=http://{host}:{port}/cosmux]http://{host}:{port}/cosmux[/link]\n"
            f"[dim]API:[/dim]       [link=http://{host}:{port}/api/health]http://{host}:{port}/api/health[/link]",
            title="[bold]Cosmux[/bold]",
            border_style="bright_blue",
        )
    )

    # Show authentication status
    _show_auth_status()
    console.print()

    # Start server
    uvicorn.run(
        "cosmux.server.app:app",
        host=host,
        port=port,
        reload=reload,
        reload_dirs=[str(workspace_path / "src")] if reload else None,
    )


@app.command()
def init(
    workspace: Path = typer.Argument(
        default=None,
        help="Workspace to initialize (default: current directory)",
    ),
) -> None:
    """Initialize CLAUDE.md in the workspace"""
    workspace_path = (workspace or Path.cwd()).resolve()

    if not workspace_path.exists():
        workspace_path.mkdir(parents=True)
        console.print(f"[green]Created directory: {workspace_path}[/green]")

    claude_md = workspace_path / "CLAUDE.md"
    if claude_md.exists():
        console.print("[yellow]CLAUDE.md already exists, skipping...[/yellow]")
    else:
        template = """# Project Context for Claude

## Project Overview
[Describe your project here]

## Tech Stack
[List your technologies]

## Code Style
[Define your coding preferences and conventions]

## Important Files
[List key files and their purposes]

## Development Commands
```bash
# Start development server
npm run dev

# Run tests
npm test
```
"""
        claude_md.write_text(template)
        console.print(f"[green]Created CLAUDE.md in {workspace_path}[/green]")

    # Create .cosmux directory for database
    cosmux_dir = workspace_path / ".cosmux"
    if not cosmux_dir.exists():
        cosmux_dir.mkdir()
        console.print(f"[green]Created .cosmux directory[/green]")

    # Create .env.example if it doesn't exist
    env_example = workspace_path / ".env.example"
    if not env_example.exists():
        env_example.write_text(
            "# Anthropic API Key\nANTHROPIC_API_KEY=sk-ant-...\n"
        )
        console.print(f"[green]Created .env.example[/green]")

    console.print("\n[bold green]Workspace initialized![/bold green]")
    console.print(f"\nRun [cyan]cosmux serve[/cyan] to start the server.")


@app.command()
def version() -> None:
    """Show Cosmux version"""
    from cosmux import __version__

    console.print(f"Cosmux v{__version__}")


@app.command()
def login() -> None:
    """Login to Claude Max subscription via OAuth"""
    from cosmux.auth.oauth import generate_pkce_pair, open_browser_auth, exchange_code_for_tokens
    from cosmux.auth.credentials import save_credentials, get_credentials

    console.print(Panel.fit(
        "[bold]Cosmux Login[/bold]\n\n"
        "Login with your Claude Max subscription to use Cosmux\n"
        "without pay-per-token API billing.",
        border_style="bright_blue",
    ))
    console.print()

    # Check if already authenticated
    existing = get_credentials()
    if existing and existing.source in ("oauth_cosmux", "oauth_env"):
        console.print("[yellow]You are already logged in.[/yellow]")
        console.print(f"[dim]Source: {existing.source}[/dim]")
        console.print()
        if not typer.confirm("Do you want to re-authenticate?"):
            raise typer.Exit(0)
        console.print()

    # Generate PKCE parameters
    code_verifier, code_challenge = generate_pkce_pair()
    state = secrets.token_urlsafe(32)

    # Open browser
    console.print("[cyan]Opening browser for authentication...[/cyan]")
    open_browser_auth(code_challenge, state)

    console.print()
    console.print("[yellow]After logging in, you'll see an authorization code on the page.[/yellow]")
    console.print("[yellow]Copy and paste it here:[/yellow]")
    console.print()

    # Get code from user
    code = console.input("[bold green]Authorization code: [/bold green]").strip()

    if not code:
        console.print("[red]No code provided. Aborting.[/red]")
        raise typer.Exit(1)

    # Exchange code for tokens
    console.print()
    console.print("[cyan]Exchanging code for tokens...[/cyan]")

    try:
        tokens = asyncio.run(exchange_code_for_tokens(code, code_verifier, state))

        # Save credentials
        save_credentials({
            "accessToken": tokens["accessToken"],
            "refreshToken": tokens.get("refreshToken", ""),
            "expiresAt": tokens.get("expiresAt", 0),
        })

        console.print()
        console.print("[bold green]Login successful![/bold green]")
        console.print("[dim]Credentials saved to ~/.cosmux/credentials.json[/dim]")
        console.print()
        console.print("Run [cyan]cosmux serve[/cyan] to start the server with your Claude Max subscription.")

    except Exception as e:
        console.print(f"[red]Login failed: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def logout() -> None:
    """Logout and remove stored credentials"""
    from cosmux.auth.credentials import COSMUX_CREDENTIALS_PATH

    if COSMUX_CREDENTIALS_PATH.exists():
        COSMUX_CREDENTIALS_PATH.unlink()
        console.print("[green]Logged out successfully.[/green]")
        console.print("[dim]Credentials removed from ~/.cosmux/credentials.json[/dim]")
    else:
        console.print("[yellow]No credentials to remove.[/yellow]")


@app.command()
def status() -> None:
    """Show current authentication status"""
    _show_auth_status()


if __name__ == "__main__":
    app()
