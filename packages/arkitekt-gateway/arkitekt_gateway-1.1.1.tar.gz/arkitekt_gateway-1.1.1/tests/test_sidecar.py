import pytest
import asyncio
import signal
import sys

from arkitekt_gateway.sidecar import (
    Sidecar,
    SidecarConfig,
    LogLine,
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

    def test_config_custom_values(self):
        config = SidecarConfig(
            authkey="test-key",
            coordserver="https://example.com",
            hostname="my-host",
            port="9090",
            statedir="/tmp/state",
        )
        assert config.hostname == "my-host"
        assert config.port == "9090"
        assert config.statedir == "/tmp/state"


class TestLogLine:
    def test_log_line(self):
        log = LogLine(stream="stdout", line="test message")
        assert log.stream == "stdout"
        assert log.line == "test message"


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
