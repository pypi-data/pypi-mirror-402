import platform
import sys


def is_windows_os() -> bool:
    """Return True if OS is Windows."""
    return platform.system().lower() == "windows"


def is_mac_os() -> bool:
    """Return True if OS is macOS."""
    return platform.system().lower() == "darwin"


def is_linux_os() -> bool:
    """Return True if OS is Linux."""
    return platform.system().lower() == "linux"


def is_nix_os() -> bool:
    """Return True if OS is Unix-like (Linux or macOS)."""
    return is_linux_os() or is_mac_os()


def get_kernel_info() -> str:
    """Return system name and release."""
    uname = platform.uname()
    return f"{uname.system} {uname.release}"


def get_python_info() -> str:
    """Return Python version string."""
    return f"Python {platform.python_version()}"


def get_python_docs_url() -> str:
    """Return URL for Python docs matching current version."""
    return f"https://docs.python.org/{sys.version_info.major}.{sys.version_info.minor}/"