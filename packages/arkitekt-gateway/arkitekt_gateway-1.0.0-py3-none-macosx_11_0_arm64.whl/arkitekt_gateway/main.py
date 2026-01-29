from .sidecar import get_binary_path, run_sidecar


def main():
    process = run_sidecar()
    return f"Started sidecar with PID: {process.pid}"


if __name__ == "__main__":
    main()
