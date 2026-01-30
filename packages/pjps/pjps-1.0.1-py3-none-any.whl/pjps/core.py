"""
Core process management module.

Provides process data collection, tree building, sorting, filtering, and signal handling.
Supports Linux, macOS, and WSL.

Copyright (c) 2026 Paige Julianne Sullivan
Licensed under the MIT License
"""

import os
import re
import signal
import subprocess
import getpass
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Dict, Callable, Any, Tuple
from enum import Enum

import psutil

from .locale import _, ngettext
from .platform import (
    CURRENT_PLATFORM, Platform, get_signal_map, is_macos, is_wsl,
    get_current_uid, get_current_username, run_privileged_command
)


class SortColumn(Enum):
    """Available columns for sorting."""
    PID = "pid"
    NAME = "name"
    USER = "user"
    CPU = "cpu"
    MEMORY = "memory"
    START_TIME = "start_time"


def get_signal_descriptions() -> Dict[int, tuple]:
    """Get signal descriptions (translated, platform-specific)."""
    return get_signal_map()


# For backward compatibility
SIGNALS = get_signal_descriptions()


@dataclass(eq=True, frozen=True)
class ListeningPort:
    """Information about a listening port."""
    port: int  # Port number (0 for Unix sockets)
    protocol: str  # 'tcp', 'tcp6', 'udp', 'udp6', 'unix'
    address: str  # Bind address or socket path
    
    def __str__(self) -> str:
        if self.protocol == 'unix':
            return f"unix:{self.address}"
        elif self.protocol in ('tcp6', 'udp6'):
            return f"{self.protocol[:-1]}6:{self.port}"
        else:
            return f"{self.protocol}:{self.port}"


@dataclass
class ProcessInfo:
    """Information about a single process."""
    pid: int
    ppid: int
    name: str
    username: str
    cpu_percent: float
    memory_percent: float
    memory_rss: int  # Resident Set Size in bytes
    memory_vms: int  # Virtual Memory Size in bytes
    status: str
    create_time: float
    cmdline: str
    num_threads: int
    nice: int
    listening_ports: List[ListeningPort] = field(default_factory=list)
    children: List['ProcessInfo'] = field(default_factory=list)
    expanded: bool = True
    depth: int = 0
    
    @property
    def start_time_str(self) -> str:
        """Return formatted start time string."""
        try:
            dt = datetime.fromtimestamp(self.create_time)
            now = datetime.now()
            if dt.date() == now.date():
                return dt.strftime("%H:%M:%S")
            elif dt.year == now.year:
                return dt.strftime("%b %d %H:%M")
            else:
                return dt.strftime("%Y-%m-%d")
        except (ValueError, OSError):
            return _("N/A")
    
    @property
    def memory_rss_str(self) -> str:
        """Return human-readable RSS memory."""
        return format_bytes(self.memory_rss)
    
    @property
    def memory_vms_str(self) -> str:
        """Return human-readable VMS memory."""
        return format_bytes(self.memory_vms)
    
    @property
    def listening_ports_str(self) -> str:
        """Return compact string of listening ports."""
        if not self.listening_ports:
            return ""
        # Group by protocol for compact display
        ports_by_proto: Dict[str, List[str]] = {}
        for lp in self.listening_ports:
            proto = lp.protocol
            if proto in ('tcp', 'tcp6'):
                key = 'tcp'
            elif proto in ('udp', 'udp6'):
                key = 'udp'
            else:
                key = 'unix'
            
            if key not in ports_by_proto:
                ports_by_proto[key] = []
            
            if key == 'unix':
                # Just show socket name, not full path
                name = lp.address.split('/')[-1] if '/' in lp.address else lp.address
                if name and name not in ports_by_proto[key]:
                    ports_by_proto[key].append(name[:12])
            else:
                port_str = str(lp.port)
                if port_str not in ports_by_proto[key]:
                    ports_by_proto[key].append(port_str)
        
        parts = []
        for proto in ['tcp', 'udp', 'unix']:
            if proto in ports_by_proto:
                ports = ports_by_proto[proto]
                if len(ports) > 3:
                    parts.append(f"{proto}:{','.join(ports[:3])}+{len(ports)-3}")
                else:
                    parts.append(f"{proto}:{','.join(ports)}")
        
        return ' '.join(parts)
    
    def matches_filter(self, pattern: str, use_regex: bool = False) -> bool:
        """Check if this process matches the filter pattern."""
        # Include listening ports in searchable string
        ports_str = ' '.join(str(lp) for lp in self.listening_ports)
        searchable = f"{self.pid} {self.name} {self.username} {self.cmdline} {self.status} {ports_str}"
        
        if use_regex:
            try:
                return bool(re.search(pattern, searchable, re.IGNORECASE))
            except re.error:
                return False
        else:
            return pattern.lower() in searchable.lower()


def format_bytes(num_bytes: int) -> str:
    """Format bytes to human-readable string."""
    for unit in ['B', 'K', 'M', 'G', 'T']:
        if abs(num_bytes) < 1024.0:
            return f"{num_bytes:.1f}{unit}"
        num_bytes /= 1024.0
    return f"{num_bytes:.1f}P"


class ProcessManager:
    """
    Manages process data collection, tree building, sorting, and signals.
    """
    
    def __init__(self):
        self.processes: Dict[int, ProcessInfo] = {}
        self.tree_roots: List[ProcessInfo] = []
        self.flat_list: List[ProcessInfo] = []  # Flattened tree for display
        self.sort_column: SortColumn = SortColumn.CPU
        self.sort_reverse: bool = True
        self.filter_pattern: str = ""
        self.filter_regex: bool = False
        self.current_user: str = get_current_username()
        self.current_uid: int = get_current_uid()
    
    def refresh(self) -> None:
        """Refresh process data from the system."""
        self.processes.clear()
        self.tree_roots.clear()
        
        # Collect system-wide listening ports first (more reliable than per-process)
        # This helps detect ports for processes we don't have permission to query directly
        pid_to_ports = self._collect_system_listening_ports()
        
        # Collect all process info
        for proc in psutil.process_iter():
            try:
                pinfo = self._get_process_info(proc, pid_to_ports)
                if pinfo:
                    self.processes[pinfo.pid] = pinfo
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue
        
        # Build tree structure
        self._build_tree()
        
        # Apply sorting
        self._sort_tree()
        
        # Flatten for display
        self._flatten_tree()
    
    def _collect_system_listening_ports(self) -> Dict[int, List[ListeningPort]]:
        """
        Collect listening ports system-wide.
        
        Uses psutil.net_connections() first, then falls back to parsing `ss` output
        for better visibility into ports owned by other users (like Apache on port 80).
        """
        pid_to_ports: Dict[int, List[ListeningPort]] = {}
        
        # First, try psutil.net_connections()
        try:
            for conn in psutil.net_connections(kind='all'):
                if conn.pid is None:
                    continue
                
                is_listening = False
                if hasattr(conn, 'status'):
                    is_listening = conn.status == 'LISTEN'
                
                if conn.type == 2:  # SOCK_DGRAM (UDP)
                    if conn.laddr:
                        if hasattr(conn.laddr, 'port') and conn.laddr.port:
                            is_listening = True
                        elif isinstance(conn.laddr, str):
                            is_listening = True
                
                if not is_listening or not conn.laddr:
                    continue
                
                try:
                    if conn.family == 1:  # AF_UNIX
                        proto = 'unix'
                        addr = conn.laddr if isinstance(conn.laddr, str) else str(conn.laddr)
                        port = 0
                    elif conn.family == 2:  # AF_INET
                        proto = 'udp' if conn.type == 2 else 'tcp'
                        addr = conn.laddr.ip
                        port = conn.laddr.port
                    elif conn.family == 10:  # AF_INET6
                        proto = 'udp6' if conn.type == 2 else 'tcp6'
                        addr = conn.laddr.ip
                        port = conn.laddr.port
                    else:
                        continue
                    
                    lp = ListeningPort(port=port, protocol=proto, address=addr)
                    
                    if conn.pid not in pid_to_ports:
                        pid_to_ports[conn.pid] = []
                    if lp not in pid_to_ports[conn.pid]:
                        pid_to_ports[conn.pid].append(lp)
                        
                except (AttributeError, TypeError):
                    continue
                    
        except (psutil.AccessDenied, psutil.NoSuchProcess, OSError):
            pass
        
        # Fallback: use `ss` command to get additional port mappings
        # This can discover ports for processes owned by other users
        self._collect_ports_from_ss(pid_to_ports)
        
        return pid_to_ports
    
    def _collect_ports_from_ss(self, pid_to_ports: Dict[int, List[ListeningPort]]) -> None:
        """
        Collect listening ports using the `ss` command.
        
        This provides better visibility into ports for processes owned by other users.
        On Linux, `ss -tlnp` and `ss -ulnp` can show PIDs with proper permissions.
        """
        import shutil
        
        # Check if ss is available
        if not shutil.which('ss'):
            return
        
        try:
            # Get TCP listening ports
            result = subprocess.run(
                ['ss', '-tlnpH'],  # -H for no header
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                self._parse_ss_output(result.stdout, 'tcp', pid_to_ports)
            
            # Get UDP listening ports
            result = subprocess.run(
                ['ss', '-ulnpH'],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                self._parse_ss_output(result.stdout, 'udp', pid_to_ports)
                
        except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
            pass
    
    def _parse_ss_output(self, output: str, proto_base: str, 
                         pid_to_ports: Dict[int, List[ListeningPort]]) -> None:
        """Parse `ss` command output to extract port-to-pid mappings."""
        # ss output format: State Recv-Q Send-Q Local Address:Port Peer Address:Port Process
        # Example: LISTEN 0 511 *:80 *:* users:(("apache2",pid=3215,fd=4))
        
        pid_pattern = re.compile(r'pid=(\d+)')
        
        for line in output.strip().split('\n'):
            if not line:
                continue
            
            parts = line.split()
            if len(parts) < 5:
                continue
            
            # Find local address:port (typically 4th column)
            local_addr = parts[3] if len(parts) > 3 else ''
            
            # Extract port from address
            if ':' in local_addr:
                addr_part, port_str = local_addr.rsplit(':', 1)
                try:
                    port = int(port_str)
                except ValueError:
                    continue
                
                # Determine if IPv6
                is_v6 = addr_part.startswith('[') or addr_part == '*' and '::' in local_addr
                # Check if the address itself suggests v6
                if addr_part in ('::', '[::]', '*'):
                    # Could be v4 or v6 wildcard, check full line for hints
                    is_v6 = '::' in local_addr or '[::' in local_addr
                
                proto = f'{proto_base}6' if is_v6 else proto_base
                addr = addr_part.strip('[]') if addr_part not in ('*', '') else ('::' if is_v6 else '0.0.0.0')
                
                # Find PIDs in the process info (last part)
                process_info = parts[-1] if len(parts) > 5 else ''
                pids = pid_pattern.findall(line)
                
                for pid_str in pids:
                    try:
                        pid = int(pid_str)
                        lp = ListeningPort(port=port, protocol=proto, address=addr)
                        
                        if pid not in pid_to_ports:
                            pid_to_ports[pid] = []
                        if lp not in pid_to_ports[pid]:
                            pid_to_ports[pid].append(lp)
                    except ValueError:
                        continue
    
    def _get_process_info(self, proc: psutil.Process, 
                          pid_to_ports: Optional[Dict[int, List[ListeningPort]]] = None) -> Optional[ProcessInfo]:
        """Extract process information safely."""
        try:
            with proc.oneshot():
                pid = proc.pid
                ppid = proc.ppid()
                name = proc.name()
                
                try:
                    username = proc.username()
                except (psutil.AccessDenied, KeyError):
                    username = "?"
                
                try:
                    cpu_percent = proc.cpu_percent()
                except psutil.AccessDenied:
                    cpu_percent = 0.0
                
                try:
                    mem_info = proc.memory_info()
                    memory_rss = mem_info.rss
                    memory_vms = mem_info.vms
                except psutil.AccessDenied:
                    memory_rss = 0
                    memory_vms = 0
                
                try:
                    memory_percent = proc.memory_percent()
                except psutil.AccessDenied:
                    memory_percent = 0.0
                
                try:
                    status = proc.status()
                except psutil.AccessDenied:
                    status = "?"
                
                try:
                    create_time = proc.create_time()
                except psutil.AccessDenied:
                    create_time = 0.0
                
                try:
                    cmdline = " ".join(proc.cmdline()) or name
                except (psutil.AccessDenied, psutil.ZombieProcess):
                    cmdline = name
                
                try:
                    num_threads = proc.num_threads()
                except psutil.AccessDenied:
                    num_threads = 0
                
                try:
                    nice = proc.nice()
                except psutil.AccessDenied:
                    nice = 0
                
                # Get listening ports from pre-collected system-wide data
                listening_ports: List[ListeningPort] = []
                if pid_to_ports and pid in pid_to_ports:
                    listening_ports = pid_to_ports[pid]
                
                return ProcessInfo(
                    pid=pid,
                    ppid=ppid,
                    name=name,
                    username=username,
                    cpu_percent=cpu_percent,
                    memory_percent=memory_percent,
                    memory_rss=memory_rss,
                    memory_vms=memory_vms,
                    status=status,
                    create_time=create_time,
                    cmdline=cmdline,
                    num_threads=num_threads,
                    nice=nice,
                    listening_ports=listening_ports,
                )
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            return None
    
    def _build_tree(self) -> None:
        """Build process tree from flat process list."""
        # First pass: link children to parents
        for pid, pinfo in self.processes.items():
            if pinfo.ppid in self.processes:
                parent = self.processes[pinfo.ppid]
                parent.children.append(pinfo)
            else:
                # Root process (parent not in our list)
                self.tree_roots.append(pinfo)
    
    def _sort_tree(self) -> None:
        """Sort tree at all levels."""
        key_func = self._get_sort_key()
        
        # Sort roots
        self.tree_roots.sort(key=key_func, reverse=self.sort_reverse)
        
        # Recursively sort children
        def sort_children(node: ProcessInfo):
            node.children.sort(key=key_func, reverse=self.sort_reverse)
            for child in node.children:
                sort_children(child)
        
        for root in self.tree_roots:
            sort_children(root)
    
    def _get_sort_key(self) -> Callable[[ProcessInfo], Any]:
        """Get the sort key function for current column."""
        if self.sort_column == SortColumn.PID:
            return lambda p: p.pid
        elif self.sort_column == SortColumn.NAME:
            return lambda p: p.name.lower()
        elif self.sort_column == SortColumn.USER:
            return lambda p: p.username.lower()
        elif self.sort_column == SortColumn.CPU:
            return lambda p: p.cpu_percent
        elif self.sort_column == SortColumn.MEMORY:
            return lambda p: p.memory_percent
        elif self.sort_column == SortColumn.START_TIME:
            return lambda p: p.create_time
        else:
            return lambda p: p.pid
    
    def _flatten_tree(self) -> None:
        """Flatten tree to list for display, respecting expansion state and filters."""
        self.flat_list.clear()
        
        def flatten_node(node: ProcessInfo, depth: int):
            node.depth = depth
            
            # Apply filter
            if self.filter_pattern:
                # Check if this node or any descendant matches
                if not self._node_or_descendant_matches(node):
                    return
            
            self.flat_list.append(node)
            
            if node.expanded:
                for child in node.children:
                    flatten_node(child, depth + 1)
        
        for root in self.tree_roots:
            flatten_node(root, 0)
    
    def _node_or_descendant_matches(self, node: ProcessInfo) -> bool:
        """Check if node or any descendant matches current filter."""
        if node.matches_filter(self.filter_pattern, self.filter_regex):
            return True
        
        for child in node.children:
            if self._node_or_descendant_matches(child):
                return True
        
        return False
    
    def set_sort(self, column: SortColumn, reverse: Optional[bool] = None) -> None:
        """Set sorting column and direction."""
        if self.sort_column == column and reverse is None:
            # Toggle direction if same column
            self.sort_reverse = not self.sort_reverse
        else:
            self.sort_column = column
            if reverse is not None:
                self.sort_reverse = reverse
            else:
                # Default direction based on column
                if column in (SortColumn.CPU, SortColumn.MEMORY, SortColumn.START_TIME):
                    self.sort_reverse = True
                else:
                    self.sort_reverse = False
        
        self._sort_tree()
        self._flatten_tree()
    
    def set_filter(self, pattern: str, use_regex: bool = False) -> None:
        """Set filter pattern."""
        self.filter_pattern = pattern
        self.filter_regex = use_regex
        self._flatten_tree()
    
    def toggle_expansion(self, pinfo: ProcessInfo) -> None:
        """Toggle expanded state of a process node."""
        pinfo.expanded = not pinfo.expanded
        self._flatten_tree()
    
    def expand_all(self) -> None:
        """Expand all nodes."""
        for pinfo in self.processes.values():
            pinfo.expanded = True
        self._flatten_tree()
    
    def collapse_all(self) -> None:
        """Collapse all nodes."""
        for pinfo in self.processes.values():
            pinfo.expanded = False
        self._flatten_tree()
    
    def can_signal_without_sudo(self, pinfo: ProcessInfo) -> bool:
        """Check if we can send signal without sudo."""
        if self.current_uid == 0:
            return True  # Root can signal anything
        
        try:
            proc = psutil.Process(pinfo.pid)
            proc_uids = proc.uids()
            return proc_uids.real == self.current_uid or proc_uids.effective == self.current_uid
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            return False
    
    def send_signal(self, pinfo: ProcessInfo, sig: int, sudo_password: Optional[str] = None) -> Tuple[bool, str]:
        """
        Send a signal to a process.
        
        Returns (success, message) tuple.
        """
        signals = get_signal_descriptions()
        if sig not in signals:
            return False, _("Invalid signal number: {sig}").format(sig=sig)
        
        sig_name, sig_desc = signals[sig]
        
        try:
            if self.can_signal_without_sudo(pinfo):
                # Direct signal
                os.kill(pinfo.pid, sig)
                return True, _("Sent {sig_name} to PID {pid}").format(sig_name=sig_name, pid=pinfo.pid)
            else:
                # Need privilege escalation
                if sudo_password is None:
                    return False, _("Requires elevated privileges")
                
                # Use platform-specific privilege escalation
                kill_cmd = ["kill", f"-{sig}", str(pinfo.pid)]
                success, result = run_privileged_command(kill_cmd, sudo_password)
                
                if success:
                    return True, _("Sent {sig_name} to PID {pid} (via sudo)").format(sig_name=sig_name, pid=pinfo.pid)
                else:
                    return False, _("Failed: {error}").format(error=result)
        
        except ProcessLookupError:
            return False, _("Process {pid} no longer exists").format(pid=pinfo.pid)
        except PermissionError:
            return False, _("Permission denied")
        except Exception as e:
            return False, _("Error: {error}").format(error=str(e))
    
    def kill_process(self, pinfo: ProcessInfo, sudo_password: Optional[str] = None) -> Tuple[bool, str]:
        """Send SIGKILL (9) to process."""
        return self.send_signal(pinfo, 9, sudo_password)
    
    def terminate_process(self, pinfo: ProcessInfo, sudo_password: Optional[str] = None) -> Tuple[bool, str]:
        """Send SIGTERM (15) to process."""
        return self.send_signal(pinfo, 15, sudo_password)
    
    def get_process_details(self, pinfo: ProcessInfo) -> Dict[str, Any]:
        """Get detailed information about a process."""
        try:
            proc = psutil.Process(pinfo.pid)
            
            details = {
                _("PID"): pinfo.pid,
                _("Parent PID"): pinfo.ppid,
                _("Name"): pinfo.name,
                _("Command"): pinfo.cmdline,
                _("User"): pinfo.username,
                _("Status"): pinfo.status,
                _("CPU %"): f"{pinfo.cpu_percent:.1f}%",
                _("Memory %"): f"{pinfo.memory_percent:.1f}%",
                _("Memory RSS"): pinfo.memory_rss_str,
                _("Memory VMS"): pinfo.memory_vms_str,
                _("Threads"): pinfo.num_threads,
                _("Nice"): pinfo.nice,
                _("Started"): pinfo.start_time_str,
            }
            
            try:
                details[_("Working Dir")] = proc.cwd()
            except (psutil.AccessDenied, psutil.NoSuchProcess):
                details[_("Working Dir")] = _("N/A")
            
            # io_counters is not available on macOS
            if not is_macos():
                try:
                    io = proc.io_counters()
                    details[_("Read Bytes")] = format_bytes(io.read_bytes)
                    details[_("Write Bytes")] = format_bytes(io.write_bytes)
                except (psutil.AccessDenied, psutil.NoSuchProcess, AttributeError):
                    pass
            
            try:
                fds = proc.num_fds()
                details[_("Open FDs")] = fds
            except (psutil.AccessDenied, psutil.NoSuchProcess, AttributeError):
                pass
            
            try:
                conns = proc.net_connections()
                details[_("Connections")] = len(conns)
            except (psutil.AccessDenied, psutil.NoSuchProcess):
                pass
            
            # Add listening ports details
            if pinfo.listening_ports:
                tcp_ports = []
                udp_ports = []
                unix_sockets = []
                
                for lp in pinfo.listening_ports:
                    if lp.protocol in ('tcp', 'tcp6'):
                        addr = f"{lp.address}:{lp.port}" if lp.address not in ('0.0.0.0', '::') else str(lp.port)
                        if lp.protocol == 'tcp6':
                            addr += ' (v6)'
                        tcp_ports.append(addr)
                    elif lp.protocol in ('udp', 'udp6'):
                        addr = f"{lp.address}:{lp.port}" if lp.address not in ('0.0.0.0', '::') else str(lp.port)
                        if lp.protocol == 'udp6':
                            addr += ' (v6)'
                        udp_ports.append(addr)
                    elif lp.protocol == 'unix':
                        unix_sockets.append(lp.address)
                
                if tcp_ports:
                    details[_("TCP Ports")] = ', '.join(tcp_ports)
                if udp_ports:
                    details[_("UDP Ports")] = ', '.join(udp_ports)
                if unix_sockets:
                    # Show abbreviated socket paths
                    abbrev = [s if len(s) <= 40 else '...' + s[-37:] for s in unix_sockets]
                    details[_("Unix Sockets")] = ', '.join(abbrev)
            
            return details
        
        except psutil.NoSuchProcess:
            return {_("Error"): _("Process no longer exists")}
        except Exception as e:
            return {_("Error"): str(e)}


def get_signal_list() -> List[Tuple[int, str, str]]:
    """Return list of (signal_num, name, description) tuples."""
    signals = get_signal_descriptions()
    return [(num, name, desc) for num, (name, desc) in sorted(signals.items())]
