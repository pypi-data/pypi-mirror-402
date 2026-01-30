"""
PJPS - Process Viewer on Steroids

A powerful process management utility with TUI and GUI interfaces.
Supports Linux, macOS, and WSL.

Copyright (c) 2026 Paige Julianne Sullivan
Licensed under the MIT License
"""

__version__ = "1.0.0"
__author__ = "Paige Julianne Sullivan"

from .core import ProcessManager, ProcessInfo
from .platform import CURRENT_PLATFORM, Platform, is_macos, is_wsl, is_linux

__all__ = [
    "ProcessManager", 
    "ProcessInfo", 
    "__version__",
    "CURRENT_PLATFORM",
    "Platform",
    "is_macos",
    "is_wsl", 
    "is_linux",
]
