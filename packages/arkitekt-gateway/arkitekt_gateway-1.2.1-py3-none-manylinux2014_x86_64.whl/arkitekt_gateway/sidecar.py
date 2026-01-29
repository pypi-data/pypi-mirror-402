import sys
import asyncio
import importlib.resources
import signal
import re
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional, Callable, Awaitable
from collections.abc import AsyncIterator
from enum import Enum
import logging

logger = logging.getLogger(__name__)


def get_binary_path() -> str:
    """Returns the absolute path to the bundled Go binary."""
    exe_name = "arkitekt-sidecar.exe" if sys.platform == "win32" else "arkitekt-sidecar"
    traversable = importlib.resources.files("arkitekt_gateway.bin") / exe_name
    return str(traversable)


class SidecarSignal(Enum):
    """IPC signals emitted by the sidecar."""

    STARTING = "STARTING"
    CONNECTING = "CONNECTING"
    CONNECTED = "CONNECTED"
    LISTENING = "LISTENING"
    READY = "READY"
    ERROR = "ERROR"
    SHUTDOWN = "SHUTDOWN"
    AUTH_REQUIRED = "AUTH_REQUIRED"


@dataclass
class SidecarEvent:
    """Represents a parsed IPC signal from the sidecar."""

    signal: SidecarSignal
    data: str  # The data portion after the signal name

    @classmethod
    def parse(cls, line: str) -> Optional["SidecarEvent"]:
        """Parse an IPC signal from a log line. Returns None if not a signal."""
        match = re.match(r"@@SIDECAR:(\w+)@@\s*(.*)", line)
        if not match:
            return None
        try:
            sig = SidecarSignal(match.group(1))
            return cls(signal=sig, data=match.group(2).strip())
        except ValueError:
            return None


class ProxyMode(Enum):
    """Proxy mode for the sidecar."""

    HTTP = "http"
    SOCKS5 = "socks5"


@dataclass
class SidecarConfig:
    """Configuration for the sidecar process."""

    authkey: str
    coordserver: str
    hostname: str = "ts-proxy"
    port: str = "8080"
    statedir: str = ""
    mode: ProxyMode = field(default=ProxyMode.HTTP)
    statusport: str = "9090"  # If set, enables the status API
    verbose: bool = False  # If True, enables verbose logging


@dataclass
class PeerInfo:
    """Information about a peer in the Tailnet."""

    name: str
    hostname: str
    tailscale_ips: list[str]
    online: bool
    direct: bool
    relayed_via: str
    current_address: str
    rx_bytes: int
    tx_bytes: int
    last_seen: Optional[str]
    last_handshake: Optional[str]


@dataclass
class SelfInfo:
    """Information about the sidecar's own node."""

    name: str
    hostname: str
    tailscale_ips: list[str]
    online: bool


@dataclass
class SidecarStatus:
    """Status information from the sidecar's status API."""

    self_info: SelfInfo
    peers: list[PeerInfo]
    backend_state: str


@dataclass
class LogLine:
    """Represents a log line from the sidecar."""

    stream: str  # "stdout" or "stderr"
    line: str
    event: Optional[SidecarEvent] = None

    def __post_init__(self):
        """Parse event from line if present."""
        if self.event is None:
            self.event = SidecarEvent.parse(self.line)


class SidecarError(Exception):
    """Error from the sidecar process."""

    pass


class SidecarTimeoutError(SidecarError):
    """Timeout waiting for sidecar to become ready."""

    pass


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
        if self.config.mode:
            args.extend(["-mode", self.config.mode.value])
        if self.config.statusport:
            args.extend(["-statusport", self.config.statusport])
        if self.config.verbose:
            args.append("-verbose")

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

    async def wait_for_signal(
        self, target_signal: SidecarSignal, timeout: float = 30.0
    ) -> SidecarEvent:
        """
        Wait for a specific IPC signal from the sidecar.

        Args:
            target_signal: The signal to wait for (e.g., SidecarSignal.READY)
            timeout: Maximum time to wait in seconds

        Returns:
            The SidecarEvent when the signal is received

        Raises:
            SidecarTimeoutError: If the timeout expires before the signal is received
            SidecarError: If an ERROR signal is received while waiting
        """
        if not self._running:
            raise RuntimeError("Sidecar is not running")

        event_received: asyncio.Future[SidecarEvent] = asyncio.Future()

        async def signal_callback(log: LogLine):
            if log.event:
                if log.event.signal == SidecarSignal.ERROR:
                    if not event_received.done():
                        event_received.set_exception(
                            SidecarError(f"Sidecar error: {log.event.data}")
                        )
                elif log.event.signal == target_signal:
                    if not event_received.done():
                        event_received.set_result(log.event)

        self._log_callbacks.append(signal_callback)
        try:
            return await asyncio.wait_for(event_received, timeout=timeout)
        except asyncio.TimeoutError:
            raise SidecarTimeoutError(
                f"Timeout waiting for {target_signal.value} signal after {timeout}s"
            )
        finally:
            self._log_callbacks.remove(signal_callback)

    async def wait_ready(self, timeout: float = 30.0) -> str:
        """
        Wait for the sidecar to become ready.

        Returns:
            The proxy URL (e.g., "http://127.0.0.1:8080")

        Raises:
            SidecarTimeoutError: If the timeout expires
            SidecarError: If an error occurs during startup
        """
        event = await self.wait_for_signal(SidecarSignal.READY, timeout=timeout)
        return event.data

    async def get_status(self) -> SidecarStatus:
        """
        Get the current status from the sidecar's status API.

        Requires statusport to be configured.

        Returns:
            SidecarStatus with self info, peers, and backend state

        Raises:
            RuntimeError: If statusport is not configured
            SidecarError: If the status API request fails
        """
        if not self.config.statusport:
            raise RuntimeError("Status API not available - statusport not configured")

        import aiohttp

        url = f"http://127.0.0.1:{self.config.statusport}/status"
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    url, timeout=aiohttp.ClientTimeout(total=5)
                ) as resp:
                    if resp.status != 200:
                        raise SidecarError(f"Status API returned {resp.status}")
                    data = await resp.json()
        except aiohttp.ClientError as e:
            raise SidecarError(f"Failed to fetch status: {e}")

        # Parse self info
        self_data = data.get("self", {})
        self_info = SelfInfo(
            name=self_data.get("name", ""),
            hostname=self_data.get("hostname", ""),
            tailscale_ips=self_data.get("tailscale_ips", []),
            online=self_data.get("online", False),
        )

        # Parse peers
        peers = []
        for peer_data in data.get("peers", []):
            peers.append(
                PeerInfo(
                    name=peer_data.get("name", ""),
                    hostname=peer_data.get("hostname", ""),
                    tailscale_ips=peer_data.get("tailscale_ips", []),
                    online=peer_data.get("online", False),
                    direct=peer_data.get("direct", False),
                    relayed_via=peer_data.get("relayed_via", ""),
                    current_address=peer_data.get("current_address", ""),
                    rx_bytes=peer_data.get("rx_bytes", 0),
                    tx_bytes=peer_data.get("tx_bytes", 0),
                    last_seen=peer_data.get("last_seen"),
                    last_handshake=peer_data.get("last_handshake"),
                )
            )

        return SidecarStatus(
            self_info=self_info,
            peers=peers,
            backend_state=data.get("backend_state", ""),
        )

    async def health_check(self) -> bool:
        """
        Check if the sidecar's status API is healthy.

        Requires statusport to be configured.

        Returns:
            True if healthy, False otherwise
        """
        if not self.config.statusport:
            raise RuntimeError("Health check not available - statusport not configured")

        import aiohttp

        url = f"http://127.0.0.1:{self.config.statusport}/health"
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    url, timeout=aiohttp.ClientTimeout(total=5)
                ) as resp:
                    return resp.status == 200
        except aiohttp.ClientError:
            return False

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
