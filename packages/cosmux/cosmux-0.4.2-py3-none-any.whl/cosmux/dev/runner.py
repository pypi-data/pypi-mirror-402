"""Process manager for running Backend and Vite dev server concurrently."""

import asyncio
import os
import signal
import sys
from pathlib import Path
from typing import Optional

from rich.console import Console

console = Console()


class DevRunner:
    """
    Manages concurrent Backend and Vite dev server processes.

    Coordinates startup, log streaming, and graceful shutdown.
    """

    def __init__(
        self,
        workspace: Path,
        vite_config_path: Path,
        backend_port: int = 3333,
        vite_port: int = 5174,
        backend_host: str = "127.0.0.1",
    ):
        self.workspace = workspace.resolve()
        self.vite_config_path = vite_config_path
        self.backend_port = backend_port
        self.vite_port = vite_port
        self.backend_host = backend_host

        self._backend_process: Optional[asyncio.subprocess.Process] = None
        self._vite_process: Optional[asyncio.subprocess.Process] = None
        self._shutdown_event = asyncio.Event()

    async def _stream_output(
        self,
        stream: asyncio.StreamReader,
        prefix: str,
        style: str,
    ) -> None:
        """Stream process output with colored prefix."""
        while True:
            line = await stream.readline()
            if not line:
                break
            text = line.decode("utf-8", errors="replace").rstrip()
            if text:
                console.print(f"[{style}][{prefix}][/{style}] {text}")

    async def _wait_for_backend(self, timeout: float = 30.0) -> bool:
        """Wait for backend to be ready by checking health endpoint."""
        import httpx

        url = f"http://{self.backend_host}:{self.backend_port}/api/health"
        start_time = asyncio.get_event_loop().time()

        while asyncio.get_event_loop().time() - start_time < timeout:
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.get(url, timeout=2.0)
                    if response.status_code == 200:
                        return True
            except Exception:
                pass
            await asyncio.sleep(0.5)

        return False

    async def _start_backend(self) -> asyncio.subprocess.Process:
        """Start the Cosmux backend server."""
        env = os.environ.copy()
        env["COSMUX_WORKSPACE"] = str(self.workspace)

        cmd = [
            sys.executable,
            "-m",
            "uvicorn",
            "cosmux.server.app:app",
            "--host",
            self.backend_host,
            "--port",
            str(self.backend_port),
        ]

        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
            env=env,
        )

        return process

    async def _start_vite(self) -> asyncio.subprocess.Process:
        """Start the Vite dev server."""
        # Check if npx is available
        npx_cmd = "npx.cmd" if sys.platform == "win32" else "npx"

        cmd = [
            npx_cmd,
            "vite",
            "--config",
            str(self.vite_config_path),
        ]

        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
            cwd=str(self.workspace),
        )

        return process

    async def _shutdown(self) -> None:
        """Gracefully shutdown all processes."""
        self._shutdown_event.set()

        processes = [
            (self._vite_process, "vite"),
            (self._backend_process, "backend"),
        ]

        for process, name in processes:
            if process and process.returncode is None:
                console.print(f"[dim]Stopping {name}...[/dim]")
                try:
                    process.terminate()
                    try:
                        await asyncio.wait_for(process.wait(), timeout=5.0)
                    except asyncio.TimeoutError:
                        process.kill()
                        await process.wait()
                except ProcessLookupError:
                    pass

    def _setup_signal_handlers(self) -> None:
        """Setup signal handlers for graceful shutdown."""
        loop = asyncio.get_event_loop()

        def signal_handler():
            console.print("\n[yellow]Shutting down...[/yellow]")
            asyncio.create_task(self._shutdown())

        for sig in (signal.SIGINT, signal.SIGTERM):
            try:
                loop.add_signal_handler(sig, signal_handler)
            except NotImplementedError:
                # Windows doesn't support add_signal_handler
                pass

    async def run(self) -> int:
        """
        Run the development environment.

        Returns:
            Exit code (0 for success, non-zero for errors)
        """
        self._setup_signal_handlers()

        try:
            # Start backend
            console.print("[blue]Starting backend...[/blue]")
            self._backend_process = await self._start_backend()

            # Stream backend output in background
            backend_task = asyncio.create_task(
                self._stream_output(
                    self._backend_process.stdout,
                    "backend",
                    "blue",
                )
            )

            # Wait for backend to be ready
            console.print("[dim]Waiting for backend to be ready...[/dim]")
            if not await self._wait_for_backend():
                console.print("[red]Backend failed to start within timeout[/red]")
                await self._shutdown()
                return 1

            console.print("[green]Backend ready![/green]")

            # Start Vite
            console.print("[green]Starting Vite dev server...[/green]")
            self._vite_process = await self._start_vite()

            # Stream Vite output in background
            vite_task = asyncio.create_task(
                self._stream_output(
                    self._vite_process.stdout,
                    "vite",
                    "green",
                )
            )

            # Wait for either process to exit or shutdown event
            done, pending = await asyncio.wait(
                [
                    asyncio.create_task(self._backend_process.wait()),
                    asyncio.create_task(self._vite_process.wait()),
                    asyncio.create_task(self._shutdown_event.wait()),
                ],
                return_when=asyncio.FIRST_COMPLETED,
            )

            # Cancel pending tasks
            for task in pending:
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass

            # Cleanup output streaming tasks
            backend_task.cancel()
            vite_task.cancel()

            await self._shutdown()
            return 0

        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")
            await self._shutdown()
            return 1
