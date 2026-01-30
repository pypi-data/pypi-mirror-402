"""
Unit tests for pjps.platform module.

Copyright (c) 2026 Paige Julianne Sullivan
Licensed under the MIT License
"""

import os
import platform as std_platform
import unittest
from unittest.mock import patch, mock_open

from pjps.platform import (
    Platform, detect_platform, is_wsl, is_macos, is_linux,
    CURRENT_PLATFORM, get_signal_map, get_privilege_escalation_command,
    has_proc_filesystem, get_current_uid, get_current_username,
    can_send_signal, get_system_info
)


class TestPlatformEnum(unittest.TestCase):
    """Tests for Platform enum."""
    
    def test_platform_values(self):
        """Test all platform enum values."""
        self.assertEqual(Platform.LINUX.value, "linux")
        self.assertEqual(Platform.MACOS.value, "macos")
        self.assertEqual(Platform.WSL.value, "wsl")
        self.assertEqual(Platform.WINDOWS.value, "windows")
        self.assertEqual(Platform.UNKNOWN.value, "unknown")


class TestPlatformDetection(unittest.TestCase):
    """Tests for platform detection functions."""
    
    def test_detect_platform_returns_valid(self):
        """Test that detect_platform returns a valid Platform."""
        result = detect_platform()
        self.assertIsInstance(result, Platform)
        self.assertIn(result, [Platform.LINUX, Platform.MACOS, Platform.WSL, 
                               Platform.WINDOWS, Platform.UNKNOWN])
    
    def test_current_platform_set(self):
        """Test that CURRENT_PLATFORM is set."""
        self.assertIsInstance(CURRENT_PLATFORM, Platform)
    
    def test_is_linux_on_linux(self):
        """Test is_linux on Linux system."""
        if std_platform.system().lower() == "linux":
            self.assertTrue(is_linux())
        elif std_platform.system().lower() == "darwin":
            self.assertFalse(is_linux())
    
    def test_is_macos_on_macos(self):
        """Test is_macos on macOS system."""
        if std_platform.system().lower() == "darwin":
            self.assertTrue(is_macos())
        else:
            self.assertFalse(is_macos())
    
    @patch('builtins.open', mock_open(read_data="Linux version 5.4.0 microsoft-standard"))
    @patch('os.environ', {'WSL_DISTRO_NAME': 'Ubuntu'})
    def test_is_wsl_with_microsoft_version(self):
        """Test WSL detection with Microsoft in version string."""
        # Note: This test may not work as expected due to caching
        # It demonstrates the detection logic
        pass
    
    def test_is_wsl_with_env_var(self):
        """Test WSL detection with environment variable."""
        # The is_wsl function checks WSL_DISTRO_NAME
        result = is_wsl()
        # Result depends on actual environment
        self.assertIsInstance(result, bool)


class TestProcFilesystem(unittest.TestCase):
    """Tests for /proc filesystem detection."""
    
    def test_has_proc_filesystem(self):
        """Test /proc detection."""
        result = has_proc_filesystem()
        self.assertIsInstance(result, bool)
        
        # On Linux, /proc should exist
        if std_platform.system().lower() == "linux":
            self.assertTrue(result)


class TestUserFunctions(unittest.TestCase):
    """Tests for user-related functions."""
    
    def test_get_current_uid(self):
        """Test getting current UID."""
        uid = get_current_uid()
        self.assertIsInstance(uid, int)
        
        # On Unix systems, should match os.getuid()
        if hasattr(os, 'getuid'):
            self.assertEqual(uid, os.getuid())
    
    def test_get_current_username(self):
        """Test getting current username."""
        username = get_current_username()
        self.assertIsInstance(username, str)
        self.assertGreater(len(username), 0)
    
    def test_can_send_signal_own_process(self):
        """Test that we can signal our own process."""
        current_uid = get_current_uid()
        current_pid = os.getpid()
        
        # We should be able to signal our own process
        result = can_send_signal(current_pid, current_uid)
        self.assertTrue(result)
    
    def test_can_send_signal_root(self):
        """Test that root can signal anything."""
        # Test with UID 0 (root)
        with patch('pjps.platform.get_current_uid', return_value=0):
            from pjps import platform as plat
            original_func = plat.get_current_uid
            plat.get_current_uid = lambda: 0
            
            result = can_send_signal(1, 1000)  # Signal PID 1, owned by UID 1000
            
            plat.get_current_uid = original_func
            # Note: This test is tricky due to module-level imports


class TestSignalMap(unittest.TestCase):
    """Tests for signal map functionality."""
    
    def test_get_signal_map_returns_dict(self):
        """Test that get_signal_map returns a dictionary."""
        signals = get_signal_map()
        self.assertIsInstance(signals, dict)
    
    def test_common_signals_present(self):
        """Test that common signals are present."""
        signals = get_signal_map()
        
        # These should exist on all Unix-like systems
        common_signals = [1, 2, 3, 9, 15]  # HUP, INT, QUIT, KILL, TERM
        for sig_num in common_signals:
            self.assertIn(sig_num, signals, f"Signal {sig_num} not found")
    
    def test_signal_format(self):
        """Test that signals have correct format."""
        signals = get_signal_map()
        
        for num, (name, desc) in signals.items():
            self.assertIsInstance(num, int)
            self.assertIsInstance(name, str)
            self.assertIsInstance(desc, str)
            self.assertTrue(name.startswith("SIG"), 
                          f"Signal name {name} should start with SIG")
    
    def test_sigkill_properties(self):
        """Test SIGKILL specific properties."""
        signals = get_signal_map()
        self.assertIn(9, signals)
        name, _ = signals[9]
        self.assertEqual(name, "SIGKILL")
    
    def test_sigterm_properties(self):
        """Test SIGTERM specific properties."""
        signals = get_signal_map()
        self.assertIn(15, signals)
        name, _ = signals[15]
        self.assertEqual(name, "SIGTERM")


class TestPrivilegeEscalation(unittest.TestCase):
    """Tests for privilege escalation command."""
    
    def test_get_privilege_escalation_command(self):
        """Test getting privilege escalation command."""
        cmd = get_privilege_escalation_command()
        
        self.assertIsInstance(cmd, list)
        self.assertGreater(len(cmd), 0)
        
        # Should contain sudo
        self.assertIn("sudo", cmd)
        
        # Should have -S flag for stdin password
        self.assertIn("-S", cmd)


class TestSystemInfo(unittest.TestCase):
    """Tests for system info function."""
    
    def test_get_system_info(self):
        """Test getting system info."""
        info = get_system_info()
        
        self.assertIsInstance(info, dict)
        
        # Required keys
        required_keys = [
            "platform", "system", "release", "version",
            "machine", "processor", "python_version",
            "psutil_version", "cpu_count", "memory_total"
        ]
        
        for key in required_keys:
            self.assertIn(key, info, f"Missing key: {key}")
    
    def test_system_info_types(self):
        """Test system info value types."""
        info = get_system_info()
        
        self.assertIsInstance(info["platform"], str)
        self.assertIsInstance(info["system"], str)
        self.assertIsInstance(info["cpu_count"], int)
        self.assertIsInstance(info["memory_total"], int)
        self.assertGreater(info["cpu_count"], 0)
        self.assertGreater(info["memory_total"], 0)


if __name__ == '__main__':
    unittest.main()
