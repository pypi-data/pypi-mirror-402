import sys
import subprocess
import importlib.resources
from pathlib import Path


def get_binary_path():
    """Returns the absolute path to the bundled Go binary."""
    # 'arkitekt_gateway.bin' is the python module path to the folder
    # 'arkitekt-sidecar.exe' or 'arkitekt-sidecar' is the file name
    exe_name = "arkitekt-sidecar.exe" if sys.platform == "win32" else "arkitekt-sidecar"

    # traversable is a Path-like object
    traversable = importlib.resources.files("arkitekt_gateway.bin") / exe_name

    return str(traversable)


def run_sidecar():
    bin_path = get_binary_path()
    print(f"Starting Go Sidecar from: {bin_path}")

    # Start the process
    process = subprocess.Popen([bin_path])
    return process
