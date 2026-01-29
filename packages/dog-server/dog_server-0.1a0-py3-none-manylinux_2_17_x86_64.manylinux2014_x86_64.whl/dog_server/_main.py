"""Main entry point that locates and executes the bundled dog binary."""

import os
import subprocess
import sys
from pathlib import Path


def find_binary() -> Path:
    """Find the dog binary bundled with this package."""
    # The binary is in the same directory as this module
    pkg_dir = Path(__file__).parent

    # Platform-specific binary names
    if sys.platform == "win32":
        binary_name = "dog.exe"
    else:
        binary_name = "dog"

    binary_path = pkg_dir / binary_name

    if not binary_path.exists():
        raise FileNotFoundError(
            f"Dog binary not found at {binary_path}. "
            f"This may be a packaging issue or unsupported platform."
        )

    return binary_path


def main() -> int:
    """Execute the dog binary with the given arguments."""
    try:
        binary = find_binary()
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    # Make sure the binary is executable (on Unix-like systems)
    if sys.platform != "win32":
        os.chmod(binary, 0o755)

    # Execute the binary, passing through all arguments
    # Using execvp would replace the process, but subprocess allows us to
    # capture the return code properly
    try:
        result = subprocess.run(
            [str(binary)] + sys.argv[1:],
            stdin=sys.stdin,
            stdout=sys.stdout,
            stderr=sys.stderr,
        )
        return result.returncode
    except KeyboardInterrupt:
        return 130  # Standard exit code for SIGINT


if __name__ == "__main__":
    sys.exit(main())
