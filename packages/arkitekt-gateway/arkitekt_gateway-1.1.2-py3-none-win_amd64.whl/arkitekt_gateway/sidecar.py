import sys
import asyncio
import importlib.resources
import signal
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional, Callable, Awaitable
from collections.abc import AsyncIterator
import logging

logger = logging.getLogger(__name__)


def get_binary_path() -> str:
    """Returns the absolute path to the bundled Go binary."""
    exe_name = "arkitekt-sidecar.exe" if sys.platform == "win32" else "arkitekt-sidecar"
    traversable = importlib.resources.files("arkitekt_gateway.bin") / exe_name
    return str(traversable)


@dataclass
class SidecarConfig:
    """Configuration for the sidecar process."""

    authkey: str
    coordserver: str
    hostname: str = "ts-proxy"
    port: str = "8080"
    statedir: str = ""


@dataclass
class LogLine:
    """Represents a log line from the sidecar."""

    stream: str  # "stdout" or "stderr"
    line: str


class Sidecar:
    """
    Async wrapper for the Go sidecar binary.

    Manages the lifecycle of the sidecar process, allows sending signals,
    and provides async streaming of logs.
    """

    def __init__(self, config: SidecarConfig):
        self.config = config
        self._process: Optional[asyncio.subprocess.Process] = None
        self._stdout_task: Optional[asyncio.Task] = None
        self._stderr_task: Optional[asyncio.Task] = None
        self._log_queue: asyncio.Queue[LogLine] = asyncio.Queue()
        self._running = False
        self._exit_code: Optional[int] = None
        self._log_callbacks: list[Callable[[LogLine], Awaitable[None]]] = []

    @property
    def is_running(self) -> bool:
        """Check if the sidecar process is running."""
        return (
            self._running
            and self._process is not None
            and self._process.returncode is None
        )

    @property
    def pid(self) -> Optional[int]:
        """Get the process ID of the sidecar."""
        return self._process.pid if self._process else None

    @property
    def exit_code(self) -> Optional[int]:
        """Get the exit code if the process has terminated."""
        return self._exit_code

    def _build_args(self) -> list[str]:
        """Build command line arguments for the sidecar."""
        args = [get_binary_path()]

        if self.config.authkey:
            args.extend(["-authkey", self.config.authkey])
        if self.config.coordserver:
            args.extend(["-coordserver", self.config.coordserver])
        if self.config.hostname:
            args.extend(["-hostname", self.config.hostname])
        if self.config.port:
            args.extend(["-port", self.config.port])
        if self.config.statedir:
            args.extend(["-statedir", self.config.statedir])

        return args

    async def _read_stream(self, stream: asyncio.StreamReader, stream_name: str):
        """Read lines from a stream and put them in the log queue."""
        try:
            while True:
                line = await stream.readline()
                if not line:
                    break
                decoded = line.decode("utf-8", errors="replace").rstrip()
                log_line = LogLine(stream=stream_name, line=decoded)
                await self._log_queue.put(log_line)

                # Call registered callbacks
                for callback in self._log_callbacks:
                    try:
                        await callback(log_line)
                    except Exception as e:
                        logger.warning(f"Log callback error: {e}")
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"Error reading {stream_name}: {e}")

    async def start(self) -> None:
        """Start the sidecar process."""
        if self._running:
            raise RuntimeError("Sidecar is already running")

        args = self._build_args()
        logger.info(f"Starting sidecar: {' '.join(args)}")

        self._process = await asyncio.create_subprocess_exec(
            *args,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        self._running = True

        # Start log reading tasks
        if self._process.stdout:
            self._stdout_task = asyncio.create_task(
                self._read_stream(self._process.stdout, "stdout")
            )
        if self._process.stderr:
            self._stderr_task = asyncio.create_task(
                self._read_stream(self._process.stderr, "stderr")
            )

        logger.info(f"Sidecar started with PID: {self._process.pid}")

    async def stop(self, timeout: float = 5.0) -> int:
        """
        Stop the sidecar process gracefully.

        Sends SIGTERM first, then SIGKILL if timeout expires.
        Returns the exit code.
        """
        if not self._process or not self._running:
            raise RuntimeError("Sidecar is not running")

        logger.info("Stopping sidecar...")

        # Send SIGTERM (or equivalent on Windows)
        try:
            self._process.terminate()
        except ProcessLookupError:
            pass

        try:
            await asyncio.wait_for(self._process.wait(), timeout=timeout)
        except asyncio.TimeoutError:
            logger.warning("Sidecar did not terminate in time, sending SIGKILL")
            try:
                self._process.kill()
            except ProcessLookupError:
                pass
            await self._process.wait()

        self._exit_code = self._process.returncode
        self._running = False

        # Cancel log reading tasks
        for task in [self._stdout_task, self._stderr_task]:
            if task and not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass

        logger.info(f"Sidecar stopped with exit code: {self._exit_code}")
        return self._exit_code

    async def send_signal(self, sig: signal.Signals) -> None:
        """Send a signal to the sidecar process."""
        if not self._process or not self._running:
            raise RuntimeError("Sidecar is not running")

        logger.info(f"Sending signal {sig.name} to sidecar")
        self._process.send_signal(sig)

    async def interrupt(self) -> None:
        """Send SIGINT to the sidecar process."""
        await self.send_signal(signal.SIGINT)

    async def wait(self) -> int:
        """Wait for the sidecar process to exit and return the exit code."""
        if not self._process:
            raise RuntimeError("Sidecar has not been started")

        await self._process.wait()
        self._exit_code = self._process.returncode
        self._running = False
        return self._exit_code

    async def logs(self) -> AsyncIterator[LogLine]:
        """
        Async iterator that yields log lines from the sidecar.

        Usage:
            async for log in sidecar.logs():
                print(f"[{log.stream}] {log.line}")
        """
        while self.is_running or not self._log_queue.empty():
            try:
                log_line = await asyncio.wait_for(self._log_queue.get(), timeout=0.5)
                yield log_line
            except asyncio.TimeoutError:
                continue

    def on_log(self, callback: Callable[[LogLine], Awaitable[None]]) -> None:
        """Register a callback to be called for each log line."""
        self._log_callbacks.append(callback)

    async def __aenter__(self) -> "Sidecar":
        """Context manager entry - starts the sidecar."""
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit - stops the sidecar."""
        if self.is_running:
            await self.stop()


async def run_sidecar_async(config: SidecarConfig) -> Sidecar:
    """
    Create and start a sidecar with the given configuration.

    Returns the running Sidecar instance.
    """
    sidecar = Sidecar(config)
    await sidecar.start()
    return sidecar
