#!/usr/bin/env python3
"""Download the platform-specific sidecar binary for local development."""

import os
import shutil
import urllib.request
import platform


sidecar_version = "v0.0.5"


def download_sidecar():
    print("🔧 Downloading sidecar binary for local development...")

    system = platform.system().lower()
    machine = platform.machine().lower()

    if system == "windows":
        ext = ".exe"
        os_name = "windows"
    elif system == "darwin":
        ext = ""
        os_name = "darwin"
    else:
        ext = ""
        os_name = "linux"

    arch = "arm64" if machine in ["arm64", "aarch64"] else "amd64"

    binary_name = f"arkitekt-sidecar-{os_name}-{arch}{ext}"
    download_url = f"https://github.com/jhnnsrs/arkitekt-sidecar/releases/download/{sidecar_version}/{binary_name}"

    # Place in the local package bin folder
    dest_dir = os.path.join(os.path.dirname(__file__), "arkitekt_gateway", "bin")
    os.makedirs(dest_dir, exist_ok=True)

    dest_path = os.path.join(dest_dir, f"arkitekt-sidecar{ext}")

    print(f"   Platform: {os_name}-{arch}")
    print(f"   Downloading from: {download_url}")

    try:
        with (
            urllib.request.urlopen(download_url) as response,
            open(dest_path, "wb") as out_file,
        ):
            shutil.copyfileobj(response, out_file)

        os.chmod(dest_path, 0o755)
        print(f"✅ Downloaded to {dest_path}")

    except Exception as e:
        print(f"❌ Failed to download binary: {e}")
        raise


if __name__ == "__main__":
    download_sidecar()
