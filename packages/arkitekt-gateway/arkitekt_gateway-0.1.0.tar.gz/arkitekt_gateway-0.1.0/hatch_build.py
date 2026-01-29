import os
import sys
import shutil
import urllib.request
import platform
from hatchling.builders.hooks.plugin.interface import BuildHookInterface


class CustomBuildHook(BuildHookInterface):
    def initialize(self, version, build_data):
        """
        This runs BEFORE the build starts.
        We download the Go binary here.
        """
        print("🪝  Running Custom Build Hook: Downloading Go Sidecar...")

        # 1. Detect Platform
        system = platform.system().lower()  # 'linux', 'darwin', 'windows'
        machine = platform.machine().lower()  # 'amd64', 'x86_64', 'arm64'

        # Map to your Go release naming convention
        # Example: proxy-helper-linux-amd64
        if system == "windows":
            ext = ".exe"
            os_name = "win"
        elif system == "darwin":
            ext = ""
            os_name = "mac"
        else:
            ext = ""
            os_name = "linux"

        # Handle Arch (simplistic example)
        arch = "arm64" if machine in ["arm64", "aarch64"] else "amd64"

        binary_name = f"arkitekt-sidecar-{os_name}-{arch}{ext}"
        download_url = f"https://github.com/jhnnsrs/arkitekt-sidecar/releases/download/v0.0.2/{binary_name}"

        # 2. Prepare Destination
        # IMPORTANT: We place it inside the package so it's importable
        dest_dir = os.path.join(self.root, "src", "arkitekt_gateway", "bin")
        os.makedirs(dest_dir, exist_ok=True)

        dest_path = os.path.join(dest_dir, f"arkitekt-sidecar{ext}")

        # 3. Download
        print(f"   Downloading from: {download_url}")
        try:
            with (
                urllib.request.urlopen(download_url) as response,
                open(dest_path, "wb") as out_file,
            ):
                shutil.copyfileobj(response, out_file)

            # Make executable
            os.chmod(dest_path, 0o755)
            print(f"✅  Downloaded to {dest_path}")

        except Exception as e:
            print(f"❌  Failed to download binary: {e}")
            # If you are in local dev and want to skip this, you can pass.
            # But for a release build, you should probably raise e.
            if os.environ.get("CI"):
                raise e
