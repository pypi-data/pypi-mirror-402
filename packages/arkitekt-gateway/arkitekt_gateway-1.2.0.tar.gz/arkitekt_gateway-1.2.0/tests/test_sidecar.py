import pytest
import asyncio
import signal
import sys

from arkitekt_gateway.sidecar import (
    Sidecar,
    SidecarConfig,
    SidecarSignal,
    SidecarEvent,
    SidecarError,
    SidecarTimeoutError,
    LogLine,
    PeerInfo,
    SelfInfo,
    SidecarStatus,
    ProxyMode,
    get_binary_path,
)


class TestSidecarConfig:
    def test_config_defaults(self):
        config = SidecarConfig(authkey="test-key", coordserver="https://example.com")
        assert config.authkey == "test-key"
        assert config.coordserver == "https://example.com"
        assert config.hostname == "ts-proxy"
        assert config.port == "8080"
        assert config.statedir == ""
        assert config.mode == ProxyMode.HTTP
        assert config.statusport == ""

    def test_config_custom_values(self):
        config = SidecarConfig(
            authkey="test-key",
            coordserver="https://example.com",
            hostname="my-host",
            port="9090",
            statedir="/tmp/state",
            mode=ProxyMode.SOCKS5,
            statusport="9091",
        )
        assert config.hostname == "my-host"
        assert config.port == "9090"
        assert config.statedir == "/tmp/state"
        assert config.mode == ProxyMode.SOCKS5
        assert config.statusport == "9091"


class TestLogLine:
    def test_log_line(self):
        log = LogLine(stream="stdout", line="test message")
        assert log.stream == "stdout"
        assert log.line == "test message"
        assert log.event is None

    def test_log_line_with_signal(self):
        log = LogLine(stream="stdout", line="@@SIDECAR:READY@@ http://127.0.0.1:8080")
        assert log.stream == "stdout"
        assert log.event is not None
        assert log.event.signal == SidecarSignal.READY
        assert log.event.data == "http://127.0.0.1:8080"

    def test_log_line_with_error_signal(self):
        log = LogLine(stream="stderr", line="@@SIDECAR:ERROR@@ connection failed")
        assert log.event is not None
        assert log.event.signal == SidecarSignal.ERROR
        assert log.event.data == "connection failed"


class TestSidecarEvent:
    def test_parse_ready_signal(self):
        event = SidecarEvent.parse("@@SIDECAR:READY@@ http://127.0.0.1:8080")
        assert event is not None
        assert event.signal == SidecarSignal.READY
        assert event.data == "http://127.0.0.1:8080"

    def test_parse_starting_signal(self):
        event = SidecarEvent.parse("@@SIDECAR:STARTING@@ v0.1.0")
        assert event is not None
        assert event.signal == SidecarSignal.STARTING
        assert event.data == "v0.1.0"

    def test_parse_connecting_signal(self):
        event = SidecarEvent.parse("@@SIDECAR:CONNECTING@@ my-proxy")
        assert event is not None
        assert event.signal == SidecarSignal.CONNECTING
        assert event.data == "my-proxy"

    def test_parse_connected_signal(self):
        event = SidecarEvent.parse("@@SIDECAR:CONNECTED@@ ips=[100.64.0.1]")
        assert event is not None
        assert event.signal == SidecarSignal.CONNECTED
        assert event.data == "ips=[100.64.0.1]"

    def test_parse_listening_signal(self):
        event = SidecarEvent.parse(
            "@@SIDECAR:LISTENING@@ mode=http addr=127.0.0.1:8080"
        )
        assert event is not None
        assert event.signal == SidecarSignal.LISTENING
        assert event.data == "mode=http addr=127.0.0.1:8080"

    def test_parse_error_signal(self):
        event = SidecarEvent.parse("@@SIDECAR:ERROR@@ auth failed")
        assert event is not None
        assert event.signal == SidecarSignal.ERROR
        assert event.data == "auth failed"

    def test_parse_shutdown_signal(self):
        event = SidecarEvent.parse("@@SIDECAR:SHUTDOWN@@")
        assert event is not None
        assert event.signal == SidecarSignal.SHUTDOWN
        assert event.data == ""

    def test_parse_auth_required_signal(self):
        event = SidecarEvent.parse("@@SIDECAR:AUTH_REQUIRED@@")
        assert event is not None
        assert event.signal == SidecarSignal.AUTH_REQUIRED

    def test_parse_non_signal_returns_none(self):
        event = SidecarEvent.parse(">>> Starting Tailscale Node...")
        assert event is None

    def test_parse_invalid_signal_returns_none(self):
        event = SidecarEvent.parse("@@SIDECAR:UNKNOWN@@")
        assert event is None

    def test_parse_empty_line_returns_none(self):
        event = SidecarEvent.parse("")
        assert event is None


class TestSidecarSignal:
    def test_all_signals_exist(self):
        assert SidecarSignal.STARTING.value == "STARTING"
        assert SidecarSignal.CONNECTING.value == "CONNECTING"
        assert SidecarSignal.CONNECTED.value == "CONNECTED"
        assert SidecarSignal.LISTENING.value == "LISTENING"
        assert SidecarSignal.READY.value == "READY"
        assert SidecarSignal.ERROR.value == "ERROR"
        assert SidecarSignal.SHUTDOWN.value == "SHUTDOWN"
        assert SidecarSignal.AUTH_REQUIRED.value == "AUTH_REQUIRED"


class TestProxyMode:
    def test_http_mode(self):
        assert ProxyMode.HTTP.value == "http"

    def test_socks5_mode(self):
        assert ProxyMode.SOCKS5.value == "socks5"


class TestPeerInfo:
    def test_peer_info(self):
        peer = PeerInfo(
            name="server.tailnet.ts.net",
            hostname="server",
            tailscale_ips=["100.64.0.10"],
            online=True,
            direct=True,
            relayed_via="",
            current_address="192.168.1.100:41641",
            rx_bytes=12345,
            tx_bytes=67890,
            last_seen="2026-01-19T20:30:00Z",
            last_handshake="2026-01-19T20:29:55Z",
        )
        assert peer.name == "server.tailnet.ts.net"
        assert peer.hostname == "server"
        assert peer.tailscale_ips == ["100.64.0.10"]
        assert peer.online is True
        assert peer.direct is True
        assert peer.rx_bytes == 12345


class TestSelfInfo:
    def test_self_info(self):
        info = SelfInfo(
            name="my-proxy.tailnet.ts.net",
            hostname="my-proxy",
            tailscale_ips=["100.64.0.1"],
            online=True,
        )
        assert info.name == "my-proxy.tailnet.ts.net"
        assert info.hostname == "my-proxy"
        assert info.tailscale_ips == ["100.64.0.1"]
        assert info.online is True


class TestSidecarStatus:
    def test_sidecar_status(self):
        self_info = SelfInfo(
            name="my-proxy.tailnet.ts.net",
            hostname="my-proxy",
            tailscale_ips=["100.64.0.1"],
            online=True,
        )
        peer = PeerInfo(
            name="server.tailnet.ts.net",
            hostname="server",
            tailscale_ips=["100.64.0.10"],
            online=True,
            direct=True,
            relayed_via="",
            current_address="192.168.1.100:41641",
            rx_bytes=12345,
            tx_bytes=67890,
            last_seen=None,
            last_handshake=None,
        )
        status = SidecarStatus(
            self_info=self_info,
            peers=[peer],
            backend_state="Running",
        )
        assert status.self_info == self_info
        assert len(status.peers) == 1
        assert status.peers[0].hostname == "server"
        assert status.backend_state == "Running"


class TestGetBinaryPath:
    def test_binary_path_returns_string(self):
        path = get_binary_path()
        assert isinstance(path, str)
        assert "arkitekt-sidecar" in path

    def test_binary_path_windows_extension(self):
        path = get_binary_path()
        if sys.platform == "win32":
            assert path.endswith(".exe")
        else:
            assert not path.endswith(".exe")


class TestSidecar:
    def test_sidecar_init(self):
        config = SidecarConfig(authkey="key", coordserver="https://example.com")
        sidecar = Sidecar(config)
        assert sidecar.config == config
        assert sidecar.is_running is False
        assert sidecar.pid is None
        assert sidecar.exit_code is None

    def test_build_args(self):
        config = SidecarConfig(
            authkey="my-auth-key",
            coordserver="https://coord.example.com",
            hostname="test-host",
            port="9000",
            statedir="/tmp/state",
        )
        sidecar = Sidecar(config)
        args = sidecar._build_args()

        assert "-authkey" in args
        assert "my-auth-key" in args
        assert "-coordserver" in args
        assert "https://coord.example.com" in args
        assert "-hostname" in args
        assert "test-host" in args
        assert "-port" in args
        assert "9000" in args
        assert "-statedir" in args
        assert "/tmp/state" in args

    def test_build_args_empty_statedir(self):
        config = SidecarConfig(
            authkey="key",
            coordserver="https://example.com",
            statedir="",
        )
        sidecar = Sidecar(config)
        args = sidecar._build_args()

        # Empty statedir should not be included
        assert "-statedir" not in args

    def test_on_log_callback(self):
        config = SidecarConfig(authkey="key", coordserver="https://example.com")
        sidecar = Sidecar(config)

        async def callback(log: LogLine):
            pass

        sidecar.on_log(callback)
        assert callback in sidecar._log_callbacks

    @pytest.mark.asyncio
    async def test_stop_not_running_raises(self):
        config = SidecarConfig(authkey="key", coordserver="https://example.com")
        sidecar = Sidecar(config)

        with pytest.raises(RuntimeError, match="not running"):
            await sidecar.stop()

    @pytest.mark.asyncio
    async def test_send_signal_not_running_raises(self):
        config = SidecarConfig(authkey="key", coordserver="https://example.com")
        sidecar = Sidecar(config)

        with pytest.raises(RuntimeError, match="not running"):
            await sidecar.send_signal(signal.SIGTERM)

    @pytest.mark.asyncio
    async def test_wait_not_started_raises(self):
        config = SidecarConfig(authkey="key", coordserver="https://example.com")
        sidecar = Sidecar(config)

        with pytest.raises(RuntimeError, match="not been started"):
            await sidecar.wait()

    @pytest.mark.asyncio
    async def test_start_already_running_raises(self):
        config = SidecarConfig(authkey="key", coordserver="https://example.com")
        sidecar = Sidecar(config)
        sidecar._running = True  # Simulate running state

        with pytest.raises(RuntimeError, match="already running"):
            await sidecar.start()

    def test_build_args_with_mode_and_statusport(self):
        config = SidecarConfig(
            authkey="key",
            coordserver="https://example.com",
            mode=ProxyMode.SOCKS5,
            statusport="9091",
        )
        sidecar = Sidecar(config)
        args = sidecar._build_args()

        assert "-mode" in args
        assert "socks5" in args
        assert "-statusport" in args
        assert "9091" in args

    @pytest.mark.asyncio
    async def test_wait_for_signal_not_running_raises(self):
        config = SidecarConfig(authkey="key", coordserver="https://example.com")
        sidecar = Sidecar(config)

        with pytest.raises(RuntimeError, match="not running"):
            await sidecar.wait_for_signal(SidecarSignal.READY)

    @pytest.mark.asyncio
    async def test_get_status_without_statusport_raises(self):
        config = SidecarConfig(authkey="key", coordserver="https://example.com")
        sidecar = Sidecar(config)

        with pytest.raises(RuntimeError, match="statusport not configured"):
            await sidecar.get_status()

    @pytest.mark.asyncio
    async def test_health_check_without_statusport_raises(self):
        config = SidecarConfig(authkey="key", coordserver="https://example.com")
        sidecar = Sidecar(config)

        with pytest.raises(RuntimeError, match="statusport not configured"):
            await sidecar.health_check()
