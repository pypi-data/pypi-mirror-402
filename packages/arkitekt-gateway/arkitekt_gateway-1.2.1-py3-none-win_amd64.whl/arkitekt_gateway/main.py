import asyncio
import signal
import sys
from typing import Optional

import typer

from .sidecar import Sidecar, SidecarConfig, LogLine, get_binary_path

app = typer.Typer(
    name="arkitekt-gateway",
    help="Arkitekt Gateway - Tailscale sidecar manager",
)


async def _run_sidecar(
    authkey: str,
    coordserver: str,
    hostname: str,
    port: str,
    statedir: str,
    show_logs: bool,
) -> int:
    """Run the sidecar and handle signals."""
    config = SidecarConfig(
        authkey=authkey,
        coordserver=coordserver,
        hostname=hostname,
        port=port,
        statedir=statedir,
    )

    sidecar = Sidecar(config)

    # Set up signal handlers
    loop = asyncio.get_running_loop()
    stop_event = asyncio.Event()

    def signal_handler():
        typer.echo("\nReceived interrupt signal, stopping sidecar...")
        stop_event.set()

    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, signal_handler)

    async def log_printer(log: LogLine):
        prefix = typer.style(
            f"[{log.stream}]",
            fg=typer.colors.CYAN if log.stream == "stdout" else typer.colors.YELLOW,
        )
        typer.echo(f"{prefix} {log.line}")

    if show_logs:
        sidecar.on_log(log_printer)

    try:
        async with sidecar:
            typer.echo(f"Sidecar started with PID: {sidecar.pid}")
            typer.echo("Press Ctrl+C to stop...")

            # Wait for either process exit or stop signal
            wait_task = asyncio.create_task(sidecar.wait())
            stop_task = asyncio.create_task(stop_event.wait())

            done, pending = await asyncio.wait(
                [wait_task, stop_task],
                return_when=asyncio.FIRST_COMPLETED,
            )

            for task in pending:
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass

            if stop_event.is_set() and sidecar.is_running:
                await sidecar.stop()

            return sidecar.exit_code or 0
    finally:
        for sig in (signal.SIGINT, signal.SIGTERM):
            loop.remove_signal_handler(sig)


@app.command()
def run(
    authkey: str = typer.Option(
        ..., "--authkey", "-a", help="Tailscale Auth Key", envvar="TS_AUTHKEY"
    ),
    coordserver: str = typer.Option(
        ...,
        "--coordserver",
        "-c",
        help="Coordination Server URL",
        envvar="TS_COORDSERVER",
    ),
    hostname: str = typer.Option(
        "ts-proxy", "--hostname", "-h", help="Hostname in the Tailnet"
    ),
    port: str = typer.Option("8080", "--port", "-p", help="Port to listen on"),
    statedir: str = typer.Option(
        "", "--statedir", "-s", help="State directory for Tailscale data"
    ),
    show_logs: bool = typer.Option(True, "--logs/--no-logs", help="Show sidecar logs"),
):
    """Run the sidecar proxy."""
    exit_code = asyncio.run(
        _run_sidecar(
            authkey=authkey,
            coordserver=coordserver,
            hostname=hostname,
            port=port,
            statedir=statedir,
            show_logs=show_logs,
        )
    )
    raise typer.Exit(code=exit_code)


@app.command()
def info():
    """Show information about the bundled sidecar binary."""
    binary_path = get_binary_path()
    typer.echo(f"Binary path: {binary_path}")

    import os

    if os.path.exists(binary_path):
        size = os.path.getsize(binary_path)
        typer.echo(f"Binary size: {size / 1024 / 1024:.2f} MB")
        typer.echo(typer.style("✓ Binary found", fg=typer.colors.GREEN))
    else:
        typer.echo(typer.style("✗ Binary not found", fg=typer.colors.RED))
        raise typer.Exit(code=1)


def main():
    """Entry point for the CLI."""
    app()


if __name__ == "__main__":
    main()
