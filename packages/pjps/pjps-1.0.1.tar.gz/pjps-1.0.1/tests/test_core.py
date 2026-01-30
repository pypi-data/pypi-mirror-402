"""
Unit tests for pjps.core module.

Copyright (c) 2026 Paige Julianne Sullivan
Licensed under the MIT License
"""

import os
import unittest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

from pjps.core import (
    ProcessInfo, ProcessManager, SortColumn,
    format_bytes, get_signal_descriptions, get_signal_list
)


class TestFormatBytes(unittest.TestCase):
    """Tests for format_bytes function."""
    
    def test_bytes(self):
        self.assertEqual(format_bytes(0), "0.0B")
        self.assertEqual(format_bytes(512), "512.0B")
        self.assertEqual(format_bytes(1023), "1023.0B")
    
    def test_kilobytes(self):
        self.assertEqual(format_bytes(1024), "1.0K")
        self.assertEqual(format_bytes(1536), "1.5K")
        self.assertEqual(format_bytes(1024 * 100), "100.0K")
    
    def test_megabytes(self):
        self.assertEqual(format_bytes(1024 * 1024), "1.0M")
        self.assertEqual(format_bytes(1024 * 1024 * 50), "50.0M")
    
    def test_gigabytes(self):
        self.assertEqual(format_bytes(1024 ** 3), "1.0G")
        self.assertEqual(format_bytes(1024 ** 3 * 8), "8.0G")
    
    def test_terabytes(self):
        self.assertEqual(format_bytes(1024 ** 4), "1.0T")


class TestProcessInfo(unittest.TestCase):
    """Tests for ProcessInfo dataclass."""
    
    def setUp(self):
        """Create a sample ProcessInfo for testing."""
        self.proc = ProcessInfo(
            pid=1234,
            ppid=1,
            name="test_process",
            username="testuser",
            cpu_percent=25.5,
            memory_percent=10.2,
            memory_rss=1024 * 1024 * 100,  # 100 MB
            memory_vms=1024 * 1024 * 500,  # 500 MB
            status="running",
            create_time=datetime.now().timestamp() - 3600,  # 1 hour ago
            cmdline="/usr/bin/test_process --flag",
            num_threads=4,
            nice=0,
        )
    
    def test_basic_attributes(self):
        """Test basic attribute access."""
        self.assertEqual(self.proc.pid, 1234)
        self.assertEqual(self.proc.ppid, 1)
        self.assertEqual(self.proc.name, "test_process")
        self.assertEqual(self.proc.username, "testuser")
        self.assertEqual(self.proc.cpu_percent, 25.5)
        self.assertEqual(self.proc.memory_percent, 10.2)
        self.assertEqual(self.proc.status, "running")
        self.assertEqual(self.proc.num_threads, 4)
        self.assertEqual(self.proc.nice, 0)
    
    def test_memory_rss_str(self):
        """Test human-readable RSS memory."""
        self.assertEqual(self.proc.memory_rss_str, "100.0M")
    
    def test_memory_vms_str(self):
        """Test human-readable VMS memory."""
        self.assertEqual(self.proc.memory_vms_str, "500.0M")
    
    def test_start_time_str_today(self):
        """Test start time formatting for today."""
        # Process started today should show HH:MM:SS
        self.proc.create_time = datetime.now().timestamp() - 60
        result = self.proc.start_time_str
        self.assertRegex(result, r'\d{2}:\d{2}:\d{2}')
    
    def test_start_time_str_this_year(self):
        """Test start time formatting for earlier this year."""
        # Set to Jan 1 of current year
        jan1 = datetime(datetime.now().year, 1, 1, 12, 0, 0)
        self.proc.create_time = jan1.timestamp()
        result = self.proc.start_time_str
        # Should be like "Jan 01 12:00"
        self.assertIn("Jan", result)
    
    def test_default_children(self):
        """Test that children defaults to empty list."""
        self.assertEqual(self.proc.children, [])
    
    def test_default_expanded(self):
        """Test that expanded defaults to True."""
        self.assertTrue(self.proc.expanded)
    
    def test_default_depth(self):
        """Test that depth defaults to 0."""
        self.assertEqual(self.proc.depth, 0)
    
    def test_matches_filter_simple_name(self):
        """Test simple filter matching on name."""
        self.assertTrue(self.proc.matches_filter("test"))
        self.assertTrue(self.proc.matches_filter("TEST"))  # Case insensitive
        self.assertTrue(self.proc.matches_filter("process"))
        self.assertFalse(self.proc.matches_filter("notfound"))
    
    def test_matches_filter_simple_pid(self):
        """Test simple filter matching on PID."""
        self.assertTrue(self.proc.matches_filter("1234"))
        self.assertFalse(self.proc.matches_filter("9999"))
    
    def test_matches_filter_simple_user(self):
        """Test simple filter matching on username."""
        self.assertTrue(self.proc.matches_filter("testuser"))
        self.assertTrue(self.proc.matches_filter("USER"))
    
    def test_matches_filter_simple_cmdline(self):
        """Test simple filter matching on command line."""
        self.assertTrue(self.proc.matches_filter("--flag"))
        self.assertTrue(self.proc.matches_filter("/usr/bin"))
    
    def test_matches_filter_regex(self):
        """Test regex filter matching."""
        self.assertTrue(self.proc.matches_filter(r"test_\w+", use_regex=True))
        self.assertTrue(self.proc.matches_filter(r"\b1234\b", use_regex=True))  # Matches PID
        self.assertTrue(self.proc.matches_filter(r"--\w+", use_regex=True))
        self.assertFalse(self.proc.matches_filter(r"^notfound", use_regex=True))
    
    def test_matches_filter_invalid_regex(self):
        """Test that invalid regex returns False."""
        self.assertFalse(self.proc.matches_filter(r"[invalid", use_regex=True))


class TestProcessManager(unittest.TestCase):
    """Tests for ProcessManager class."""
    
    def setUp(self):
        """Create ProcessManager instance."""
        self.pm = ProcessManager()
    
    def test_initial_state(self):
        """Test initial state of ProcessManager."""
        self.assertEqual(self.pm.processes, {})
        self.assertEqual(self.pm.tree_roots, [])
        self.assertEqual(self.pm.flat_list, [])
        self.assertEqual(self.pm.sort_column, SortColumn.CPU)
        self.assertTrue(self.pm.sort_reverse)
        self.assertEqual(self.pm.filter_pattern, "")
        self.assertFalse(self.pm.filter_regex)
    
    def test_refresh_populates_processes(self):
        """Test that refresh populates the process list."""
        self.pm.refresh()
        # Should have at least some processes
        self.assertGreater(len(self.pm.processes), 0)
        self.assertGreater(len(self.pm.flat_list), 0)
    
    def test_refresh_includes_current_process(self):
        """Test that refresh includes the current Python process."""
        self.pm.refresh()
        current_pid = os.getpid()
        self.assertIn(current_pid, self.pm.processes)
    
    def test_set_sort_column(self):
        """Test setting sort column."""
        self.pm.refresh()
        
        # Change to PID sorting
        self.pm.set_sort(SortColumn.PID)
        self.assertEqual(self.pm.sort_column, SortColumn.PID)
        self.assertFalse(self.pm.sort_reverse)  # PID defaults to ascending
        
        # Change to MEMORY sorting
        self.pm.set_sort(SortColumn.MEMORY)
        self.assertEqual(self.pm.sort_column, SortColumn.MEMORY)
        self.assertTrue(self.pm.sort_reverse)  # Memory defaults to descending
    
    def test_set_sort_toggle(self):
        """Test that setting same column toggles direction."""
        self.pm.refresh()
        
        self.pm.set_sort(SortColumn.NAME)
        initial_reverse = self.pm.sort_reverse
        
        self.pm.set_sort(SortColumn.NAME)  # Same column
        self.assertEqual(self.pm.sort_reverse, not initial_reverse)
    
    def test_set_sort_explicit_direction(self):
        """Test setting explicit sort direction."""
        self.pm.refresh()
        
        self.pm.set_sort(SortColumn.PID, reverse=True)
        self.assertTrue(self.pm.sort_reverse)
        
        self.pm.set_sort(SortColumn.PID, reverse=False)
        self.assertFalse(self.pm.sort_reverse)
    
    def test_set_filter(self):
        """Test setting filter pattern."""
        self.pm.refresh()
        total_count = len(self.pm.flat_list)
        
        # Filter should reduce visible processes
        self.pm.set_filter("python")
        self.assertLessEqual(len(self.pm.flat_list), total_count)
        
        # Clear filter
        self.pm.set_filter("")
        self.assertEqual(len(self.pm.flat_list), total_count)
    
    def test_set_filter_regex(self):
        """Test setting regex filter."""
        self.pm.refresh()
        
        self.pm.set_filter(r"python\d*", use_regex=True)
        self.assertTrue(self.pm.filter_regex)
    
    def test_expand_collapse_all(self):
        """Test expand/collapse all functionality."""
        self.pm.refresh()
        
        # Collapse all
        self.pm.collapse_all()
        for pinfo in self.pm.processes.values():
            self.assertFalse(pinfo.expanded)
        
        # Expand all
        self.pm.expand_all()
        for pinfo in self.pm.processes.values():
            self.assertTrue(pinfo.expanded)
    
    def test_toggle_expansion(self):
        """Test toggling expansion of a single node."""
        self.pm.refresh()
        
        if self.pm.flat_list:
            proc = self.pm.flat_list[0]
            initial_state = proc.expanded
            
            self.pm.toggle_expansion(proc)
            self.assertEqual(proc.expanded, not initial_state)
            
            self.pm.toggle_expansion(proc)
            self.assertEqual(proc.expanded, initial_state)
    
    def test_can_signal_without_sudo_own_process(self):
        """Test that we can signal our own process without sudo."""
        self.pm.refresh()
        current_pid = os.getpid()
        
        if current_pid in self.pm.processes:
            pinfo = self.pm.processes[current_pid]
            self.assertTrue(self.pm.can_signal_without_sudo(pinfo))
    
    def test_get_process_details(self):
        """Test getting detailed process info."""
        self.pm.refresh()
        current_pid = os.getpid()
        
        if current_pid in self.pm.processes:
            pinfo = self.pm.processes[current_pid]
            details = self.pm.get_process_details(pinfo)
            
            # Should contain basic info
            self.assertIn("PID", details)
            self.assertIn("Name", details)


class TestSignalFunctions(unittest.TestCase):
    """Tests for signal-related functions."""
    
    def test_get_signal_descriptions(self):
        """Test that signal descriptions are returned."""
        signals = get_signal_descriptions()
        
        # Should have common signals
        self.assertIn(9, signals)   # SIGKILL
        self.assertIn(15, signals)  # SIGTERM
        self.assertIn(1, signals)   # SIGHUP
        
        # Each entry should be (name, description) tuple
        for num, (name, desc) in signals.items():
            self.assertIsInstance(name, str)
            self.assertIsInstance(desc, str)
            self.assertTrue(name.startswith("SIG"))
    
    def test_get_signal_list(self):
        """Test getting signal list."""
        sig_list = get_signal_list()
        
        # Should be a list of tuples
        self.assertIsInstance(sig_list, list)
        self.assertGreater(len(sig_list), 0)
        
        # Each item should be (num, name, desc)
        for num, name, desc in sig_list:
            self.assertIsInstance(num, int)
            self.assertIsInstance(name, str)
            self.assertIsInstance(desc, str)
        
        # Should be sorted by signal number
        nums = [num for num, _, _ in sig_list]
        self.assertEqual(nums, sorted(nums))


class TestSortColumn(unittest.TestCase):
    """Tests for SortColumn enum."""
    
    def test_all_columns(self):
        """Test all sort columns exist."""
        self.assertEqual(SortColumn.PID.value, "pid")
        self.assertEqual(SortColumn.NAME.value, "name")
        self.assertEqual(SortColumn.USER.value, "user")
        self.assertEqual(SortColumn.CPU.value, "cpu")
        self.assertEqual(SortColumn.MEMORY.value, "memory")
        self.assertEqual(SortColumn.START_TIME.value, "start_time")


if __name__ == '__main__':
    unittest.main()
