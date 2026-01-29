"""Binary resolution for SCANOSS daemon.

The binary is bundled directly in the wheel for each platform.
pip automatically selects the correct wheel based on your OS and architecture.
"""

import shutil
import stat
import sys
from pathlib import Path


def get_binary_path() -> str:
    """
    Get the path to the SCANOSS binary.

    The binary is bundled in the wheel package under scanoss/bin/.
    pip automatically installs the correct platform-specific wheel.

    Returns:
        Path to the scanoss binary.

    Raises:
        RuntimeError: If the binary is not found.
    """
    # Determine binary name based on platform
    binary_name = "scanoss.exe" if sys.platform == "win32" else "scanoss"

    # Look for binary in package bin directory
    package_dir = Path(__file__).parent
    binary_path = package_dir / "bin" / binary_name

    if binary_path.exists():
        # Ensure executable on Unix
        if sys.platform != "win32":
            current_mode = binary_path.stat().st_mode
            if not (current_mode & stat.S_IXUSR):
                binary_path.chmod(current_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
        return str(binary_path)

    # Fallback: check if binary is in PATH
    path_binary = shutil.which("scanoss")
    if path_binary:
        return path_binary

    raise RuntimeError(
        "SCANOSS binary not found.\n"
        "This usually means you installed the wrong wheel for your platform.\n"
        "Try reinstalling: pip install --force-reinstall scanoss"
    )
