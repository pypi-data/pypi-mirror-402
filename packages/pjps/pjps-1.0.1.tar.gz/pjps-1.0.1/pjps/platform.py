"""
Platform detection and compatibility utilities.

Provides cross-platform support for Linux, macOS, and WSL.

Copyright (c) 2026 Paige Julianne Sullivan
Licensed under the MIT License
"""

import os
import sys
import platform
import subprocess
from typing import Optional, Tuple
from enum import Enum


class Platform(Enum):
    """Supported platforms."""
    LINUX = "linux"
    MACOS = "macos"
    WSL = "wsl"
    WINDOWS = "windows"
    UNKNOWN = "unknown"


def detect_platform() -> Platform:
    """Detect the current platform."""
    system = platform.system().lower()
    
    if system == "darwin":
        return Platform.MACOS
    elif system == "linux":
        # Check if running under WSL
        if is_wsl():
            return Platform.WSL
        return Platform.LINUX
    elif system == "windows":
        return Platform.WINDOWS
    else:
        return Platform.UNKNOWN


def is_wsl() -> bool:
    """Check if running under Windows Subsystem for Linux."""
    # Check for WSL1 or WSL2
    try:
        with open("/proc/version", "r") as f:
            version_info = f.read().lower()
            return "microsoft" in version_info or "wsl" in version_info
    except (FileNotFoundError, PermissionError):
        pass
    
    # Alternative check via environment
    if "WSL_DISTRO_NAME" in os.environ:
        return True
    if "WSL_INTEROP" in os.environ:
        return True
    
    return False


def is_macos() -> bool:
    """Check if running on macOS."""
    return platform.system().lower() == "darwin"


def is_linux() -> bool:
    """Check if running on Linux (including WSL)."""
    return platform.system().lower() == "linux"


# Current platform (cached)
CURRENT_PLATFORM = detect_platform()


def get_signal_map() -> dict:
    """
    Get platform-specific signal number mapping.
    
    Signal numbers differ between Linux and macOS.
    Returns a dict mapping signal numbers to (name, description) tuples.
    """
    from .locale import _
    
    # Common signals (same on all Unix-like systems)
    signals = {
        1: ("SIGHUP", _("Hangup")),
        2: ("SIGINT", _("Interrupt")),
        3: ("SIGQUIT", _("Quit")),
        4: ("SIGILL", _("Illegal instruction")),
        5: ("SIGTRAP", _("Trace/breakpoint trap")),
        6: ("SIGABRT", _("Aborted")),
        8: ("SIGFPE", _("Floating point exception")),
        9: ("SIGKILL", _("Killed")),
        10: ("SIGBUS", _("Bus error")) if is_macos() else ("SIGUSR1", _("User defined signal 1")),
        11: ("SIGSEGV", _("Segmentation fault")),
        13: ("SIGPIPE", _("Broken pipe")),
        14: ("SIGALRM", _("Alarm clock")),
        15: ("SIGTERM", _("Terminated")),
    }
    
    if is_macos():
        # macOS-specific signal numbers
        signals.update({
            7: ("SIGEMT", _("EMT instruction")),
            10: ("SIGBUS", _("Bus error")),
            12: ("SIGSYS", _("Bad system call")),
            16: ("SIGURG", _("Urgent I/O condition")),
            17: ("SIGSTOP", _("Stopped (signal)")),
            18: ("SIGTSTP", _("Stopped")),
            19: ("SIGCONT", _("Continued")),
            20: ("SIGCHLD", _("Child exited")),
            21: ("SIGTTIN", _("Stopped (tty input)")),
            22: ("SIGTTOU", _("Stopped (tty output)")),
            23: ("SIGIO", _("I/O possible")),
            24: ("SIGXCPU", _("CPU time limit exceeded")),
            25: ("SIGXFSZ", _("File size limit exceeded")),
            26: ("SIGVTALRM", _("Virtual timer expired")),
            27: ("SIGPROF", _("Profiling timer expired")),
            28: ("SIGWINCH", _("Window changed")),
            29: ("SIGINFO", _("Information request")),
            30: ("SIGUSR1", _("User defined signal 1")),
            31: ("SIGUSR2", _("User defined signal 2")),
        })
    else:
        # Linux signal numbers
        signals.update({
            7: ("SIGBUS", _("Bus error")),
            10: ("SIGUSR1", _("User defined signal 1")),
            12: ("SIGUSR2", _("User defined signal 2")),
            16: ("SIGSTKFLT", _("Stack fault")),
            17: ("SIGCHLD", _("Child exited")),
            18: ("SIGCONT", _("Continued")),
            19: ("SIGSTOP", _("Stopped (signal)")),
            20: ("SIGTSTP", _("Stopped")),
            21: ("SIGTTIN", _("Stopped (tty input)")),
            22: ("SIGTTOU", _("Stopped (tty output)")),
            23: ("SIGURG", _("Urgent I/O condition")),
            24: ("SIGXCPU", _("CPU time limit exceeded")),
            25: ("SIGXFSZ", _("File size limit exceeded")),
            26: ("SIGVTALRM", _("Virtual timer expired")),
            27: ("SIGPROF", _("Profiling timer expired")),
            28: ("SIGWINCH", _("Window changed")),
            29: ("SIGIO", _("I/O possible")),
            30: ("SIGPWR", _("Power failure")),
            31: ("SIGSYS", _("Bad system call")),
        })
    
    return signals


def get_privilege_escalation_command() -> list:
    """
    Get the appropriate privilege escalation command for the platform.
    
    Returns a list of command components (e.g., ["sudo", "-S"]).
    """
    if CURRENT_PLATFORM == Platform.MACOS:
        # macOS uses sudo
        return ["sudo", "-S"]
    elif CURRENT_PLATFORM == Platform.WSL:
        # WSL uses sudo (Linux-style)
        return ["sudo", "-S"]
    else:
        # Standard Linux sudo
        return ["sudo", "-S"]


def has_proc_filesystem() -> bool:
    """Check if /proc filesystem is available."""
    return os.path.isdir("/proc")


def get_current_uid() -> int:
    """Get current user ID, cross-platform."""
    try:
        return os.getuid()
    except AttributeError:
        # Windows doesn't have getuid
        return -1


def get_current_username() -> str:
    """Get current username, cross-platform."""
    import getpass
    try:
        return getpass.getuser()
    except Exception:
        return os.environ.get("USER", os.environ.get("USERNAME", "unknown"))


def can_send_signal(pid: int, uid: int) -> bool:
    """
    Check if the current user can send a signal to a process.
    
    Args:
        pid: Process ID
        uid: UID of the process owner
        
    Returns:
        True if signal can be sent without privilege escalation
    """
    current_uid = get_current_uid()
    
    # Root can signal anything
    if current_uid == 0:
        return True
    
    # Same user can signal own processes
    return current_uid == uid


def run_privileged_command(cmd: list, password: Optional[str] = None) -> Tuple[bool, str]:
    """
    Run a command with privilege escalation.
    
    Args:
        cmd: Command to run (without sudo prefix)
        password: Optional password for sudo
        
    Returns:
        Tuple of (success, output/error message)
    """
    from .locale import _
    
    full_cmd = get_privilege_escalation_command() + cmd
    
    try:
        proc = subprocess.Popen(
            full_cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        
        stdin_data = (password + "\n").encode() if password else None
        stdout, stderr = proc.communicate(input=stdin_data, timeout=30)
        
        if proc.returncode == 0:
            return True, stdout.decode().strip()
        else:
            error = stderr.decode().strip()
            if "incorrect password" in error.lower() or "sorry" in error.lower():
                return False, _("Incorrect password")
            if "not in the sudoers file" in error.lower():
                return False, _("User not in sudoers file")
            return False, error
            
    except subprocess.TimeoutExpired:
        proc.kill()
        return False, _("Command timed out")
    except FileNotFoundError:
        return False, _("sudo command not found")
    except Exception as e:
        return False, str(e)


def get_system_info() -> dict:
    """Get system information for debugging."""
    import psutil
    
    info = {
        "platform": CURRENT_PLATFORM.value,
        "system": platform.system(),
        "release": platform.release(),
        "version": platform.version(),
        "machine": platform.machine(),
        "processor": platform.processor(),
        "python_version": sys.version,
        "psutil_version": psutil.__version__,
        "cpu_count": psutil.cpu_count(),
        "memory_total": psutil.virtual_memory().total,
    }
    
    if is_wsl():
        info["wsl_distro"] = os.environ.get("WSL_DISTRO_NAME", "unknown")
    
    return info
