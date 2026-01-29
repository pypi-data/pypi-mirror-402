import sys
import subprocess
import importlib.resources
from pathlib import Path


def get_binary_path():
    """Returns the absolute path to the bundled Go binary."""
    # 'my_package.bin' is the python module path to the folder
    # 'proxy-helper.exe' or 'proxy-helper' is the file name
    exe_name = "proxy-helper.exe" if sys.platform == "win32" else "proxy-helper"

    # traversable is a Path-like object
    traversable = importlib.resources.files("my_package.bin") / exe_name

    return str(traversable)


def run_sidecar():
    bin_path = get_binary_path()
    print(f"Starting Go Sidecar from: {bin_path}")

    # Start the process
    process = subprocess.Popen([bin_path])
    return process
