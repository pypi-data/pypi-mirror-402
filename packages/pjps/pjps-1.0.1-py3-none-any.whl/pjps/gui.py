"""
Tkinter GUI for PJPS.

A graphical process viewer with tree view, sorting, filtering, and signal support.

Copyright (c) 2026 Paige Julianne Sullivan
Licensed under the MIT License
"""

import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, font as tkfont
import re
from typing import Optional, Dict, Set
import subprocess

from .core import ProcessManager, ProcessInfo, SortColumn, get_signal_descriptions, get_signal_list
from .locale import _


class PasswordDialog(simpledialog.Dialog):
    """Password entry dialog for sudo operations."""
    
    def __init__(self, parent, title, message):
        self.message = message
        self.password = None
        super().__init__(parent, title)
    
    def body(self, master):
        ttk.Label(master, text=self.message, wraplength=300).grid(row=0, column=0, columnspan=2, pady=10)
        ttk.Label(master, text=_("Password:")).grid(row=1, column=0, sticky='e', padx=5)
        
        self.entry = ttk.Entry(master, show='*', width=30)
        self.entry.grid(row=1, column=1, padx=5, pady=5)
        
        return self.entry
    
    def apply(self):
        self.password = self.entry.get()


class SignalDialog(simpledialog.Dialog):
    """Signal selection dialog."""
    
    def __init__(self, parent, pinfo: ProcessInfo):
        self.pinfo = pinfo
        self.selected_signal = None
        super().__init__(parent, _("Send Signal to {name} (PID {pid})").format(name=pinfo.name, pid=pinfo.pid))
    
    def body(self, master):
        ttk.Label(master, text=_("Select signal to send:")).pack(pady=5)
        
        # Create listbox with scrollbar
        frame = ttk.Frame(master)
        frame.pack(fill='both', expand=True, padx=5, pady=5)
        
        scrollbar = ttk.Scrollbar(frame)
        scrollbar.pack(side='right', fill='y')
        
        self.listbox = tk.Listbox(frame, height=15, width=40, yscrollcommand=scrollbar.set)
        self.listbox.pack(side='left', fill='both', expand=True)
        scrollbar.config(command=self.listbox.yview)
        
        # Populate signals
        self.signals = []
        for sig_num, sig_name, sig_desc in get_signal_list():
            self.signals.append(sig_num)
            self.listbox.insert('end', f"{sig_num:2d}  {sig_name:<10} - {sig_desc}")
        
        # Select SIGTERM by default
        try:
            idx = self.signals.index(15)
            self.listbox.selection_set(idx)
            self.listbox.see(idx)
        except ValueError:
            pass
        
        self.listbox.bind('<Double-1>', lambda e: self.ok())
        
        return self.listbox
    
    def apply(self):
        selection = self.listbox.curselection()
        if selection:
            self.selected_signal = self.signals[selection[0]]


class DetailsDialog(simpledialog.Dialog):
    """Process details dialog."""
    
    def __init__(self, parent, pinfo: ProcessInfo, manager: ProcessManager):
        self.pinfo = pinfo
        self.details = manager.get_process_details(pinfo)
        super().__init__(parent, _("Details - {name} (PID {pid})").format(name=pinfo.name, pid=pinfo.pid))
    
    def body(self, master):
        # Create text widget with scrollbar
        frame = ttk.Frame(master)
        frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        scrollbar = ttk.Scrollbar(frame)
        scrollbar.pack(side='right', fill='y')
        
        text = tk.Text(frame, height=20, width=50, yscrollcommand=scrollbar.set, wrap='word')
        text.pack(side='left', fill='both', expand=True)
        scrollbar.config(command=text.yview)
        
        # Insert details
        for key, value in self.details.items():
            text.insert('end', f"{key}: ", 'bold')
            text.insert('end', f"{value}\n")
        
        text.tag_configure('bold', font=('TkDefaultFont', 10, 'bold'))
        text.config(state='disabled')
        
        return text
    
    def buttonbox(self):
        box = ttk.Frame(self)
        box.pack(pady=5)
        ttk.Button(box, text=_("Close"), command=self.ok, width=10).pack()
        self.bind("<Return>", lambda e: self.ok())
        self.bind("<Escape>", lambda e: self.ok())


class SearchBar(ttk.Frame):
    """Search/filter bar widget."""
    
    def __init__(self, parent, on_search):
        super().__init__(parent)
        self.on_search = on_search
        
        ttk.Label(self, text=_("Filter:")).pack(side='left', padx=(0, 5))
        
        self.entry = ttk.Entry(self, width=30)
        self.entry.pack(side='left', padx=(0, 5))
        self.entry.bind('<KeyRelease>', self._on_key)
        self.entry.bind('<Return>', self._on_search)
        
        self.regex_var = tk.BooleanVar(value=False)
        self.regex_cb = ttk.Checkbutton(self, text=_("Regex"), variable=self.regex_var,
                                         command=self._on_search)
        self.regex_cb.pack(side='left', padx=(0, 5))
        
        ttk.Button(self, text=_("Clear"), command=self._clear).pack(side='left')
    
    def _on_key(self, event):
        # Live search on typing
        self._on_search()
    
    def _on_search(self, event=None):
        pattern = self.entry.get()
        is_regex = self.regex_var.get()
        self.on_search(pattern, is_regex)
    
    def _clear(self):
        self.entry.delete(0, 'end')
        self.regex_var.set(False)
        self.on_search("", False)


class ProcessTreeView(ttk.Frame):
    """Tree view widget for displaying processes."""
    
    def __init__(self, parent, manager: ProcessManager):
        super().__init__(parent)
        self.manager = manager
        self.item_to_pinfo: Dict[str, ProcessInfo] = {}
        self.pinfo_to_item: Dict[int, str] = {}
        self.expanded_pids: Set[int] = set()
        
        # Configure style
        style = ttk.Style()
        default_font = tkfont.nametofont('TkDefaultFont')
        row_height = default_font.metrics('linespace')
        style.configure("Treeview", rowheight=row_height)
        style.configure("Treeview.Heading", font=('TkDefaultFont', 9, 'bold'))
        
        # Create treeview with scrollbars
        self.tree = ttk.Treeview(self, columns=('pid', 'user', 'cpu', 'mem', 'status', 'ports', 'started'),
                                  show='tree headings', selectmode='browse')
        
        # Scrollbars
        vsb = ttk.Scrollbar(self, orient='vertical', command=self.tree.yview)
        hsb = ttk.Scrollbar(self, orient='horizontal', command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        
        # Grid layout
        self.tree.grid(row=0, column=0, sticky='nsew')
        vsb.grid(row=0, column=1, sticky='ns')
        hsb.grid(row=1, column=0, sticky='ew')
        
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        
        # Configure columns
        self.tree.heading('#0', text=_('Process Name'), command=lambda: self._sort_by(SortColumn.NAME))
        self.tree.heading('pid', text=_('PID'), command=lambda: self._sort_by(SortColumn.PID))
        self.tree.heading('user', text=_('User'), command=lambda: self._sort_by(SortColumn.USER))
        self.tree.heading('cpu', text=_('CPU %'), command=lambda: self._sort_by(SortColumn.CPU))
        self.tree.heading('mem', text=_('Mem %'), command=lambda: self._sort_by(SortColumn.MEMORY))
        self.tree.heading('status', text=_('Status'))
        self.tree.heading('ports', text=_('Ports'))
        self.tree.heading('started', text=_('Started'), command=lambda: self._sort_by(SortColumn.START_TIME))
        
        # Column widths
        self.tree.column('#0', width=250, minwidth=150)
        self.tree.column('pid', width=70, minwidth=50, anchor='e')
        self.tree.column('user', width=90, minwidth=60)
        self.tree.column('cpu', width=60, minwidth=50, anchor='e')
        self.tree.column('mem', width=60, minwidth=50, anchor='e')
        self.tree.column('status', width=70, minwidth=60)
        self.tree.column('ports', width=140, minwidth=80)
        self.tree.column('started', width=100, minwidth=80)
        
        # Tags for coloring
        self.tree.tag_configure('high_cpu', foreground='#cc0000')
        self.tree.tag_configure('med_cpu', foreground='#cc6600')
        self.tree.tag_configure('high_mem', foreground='#0066cc')
        
        # Context menu
        self.context_menu = tk.Menu(self, tearoff=0)
        self.context_menu.add_command(label=_("Details"), command=self._show_details)
        self.context_menu.add_separator()
        self.context_menu.add_command(label=_("Send Signal..."), command=self._send_signal)
        self.context_menu.add_command(label=_("Terminate (SIGTERM)"), command=lambda: self._quick_signal(15))
        self.context_menu.add_command(label=_("Kill (SIGKILL)"), command=lambda: self._quick_signal(9))
        self.context_menu.add_separator()
        self.context_menu.add_command(label=_("Expand All"), command=self._expand_all)
        self.context_menu.add_command(label=_("Collapse All"), command=self._collapse_all)
        
        # Bindings
        self.tree.bind('<Button-3>', self._on_right_click)
        self.tree.bind('<Double-1>', self._on_double_click)
        self.tree.bind('<Return>', self._on_double_click)
        self.tree.bind('<<TreeviewOpen>>', self._on_open)
        self.tree.bind('<<TreeviewClose>>', self._on_close)
        
        # Callback for external handlers
        self.on_signal_sent = None
    
    def _sort_by(self, column: SortColumn):
        """Sort by column."""
        self.manager.set_sort(column)
        self.refresh()
    
    def refresh(self):
        """Refresh the tree view."""
        # Save expansion state
        self._save_expansion_state()
        
        # Clear tree
        for item in self.tree.get_children():
            self.tree.delete(item)
        self.item_to_pinfo.clear()
        self.pinfo_to_item.clear()
        
        # Rebuild tree
        self._build_tree()
        
        # Restore expansion
        self._restore_expansion_state()
    
    def _save_expansion_state(self):
        """Save which items are expanded."""
        self.expanded_pids.clear()
        for item in self.item_to_pinfo:
            if self.tree.item(item, 'open'):
                pinfo = self.item_to_pinfo.get(item)
                if pinfo:
                    self.expanded_pids.add(pinfo.pid)
    
    def _restore_expansion_state(self):
        """Restore expansion state."""
        for pid in self.expanded_pids:
            item = self.pinfo_to_item.get(pid)
            if item:
                self.tree.item(item, open=True)
    
    def _build_tree(self):
        """Build tree from manager data."""
        def add_node(pinfo: ProcessInfo, parent: str = ''):
            # Determine tags
            tags = []
            if pinfo.cpu_percent > 50:
                tags.append('high_cpu')
            elif pinfo.cpu_percent > 20:
                tags.append('med_cpu')
            if pinfo.memory_percent > 50:
                tags.append('high_mem')
            
            values = (
                str(pinfo.pid),
                pinfo.username,
                f"{pinfo.cpu_percent:.1f}",
                f"{pinfo.memory_percent:.1f}",
                pinfo.status,
                pinfo.listening_ports_str,
                pinfo.start_time_str,
            )
            
            item = self.tree.insert(parent, 'end', text=pinfo.name, values=values, tags=tags)
            self.item_to_pinfo[item] = pinfo
            self.pinfo_to_item[pinfo.pid] = item
            
            # Add children
            for child in pinfo.children:
                add_node(child, item)
        
        # Add root nodes
        for root in self.manager.tree_roots:
            add_node(root)
    
    def _on_right_click(self, event):
        """Handle right-click context menu."""
        item = self.tree.identify_row(event.y)
        if item:
            self.tree.selection_set(item)
            self.context_menu.post(event.x_root, event.y_root)
    
    def _on_double_click(self, event):
        """Handle double-click to show details."""
        self._show_details()
    
    def _on_open(self, event):
        """Handle tree node expansion."""
        item = self.tree.focus()
        pinfo = self.item_to_pinfo.get(item)
        if pinfo:
            self.expanded_pids.add(pinfo.pid)
    
    def _on_close(self, event):
        """Handle tree node collapse."""
        item = self.tree.focus()
        pinfo = self.item_to_pinfo.get(item)
        if pinfo:
            self.expanded_pids.discard(pinfo.pid)
    
    def get_selected_process(self) -> Optional[ProcessInfo]:
        """Get currently selected process."""
        selection = self.tree.selection()
        if selection:
            return self.item_to_pinfo.get(selection[0])
        return None
    
    def _show_details(self):
        """Show details dialog for selected process."""
        pinfo = self.get_selected_process()
        if pinfo:
            DetailsDialog(self.winfo_toplevel(), pinfo, self.manager)
    
    def _send_signal(self):
        """Show signal dialog for selected process."""
        pinfo = self.get_selected_process()
        if not pinfo:
            return
        
        dialog = SignalDialog(self.winfo_toplevel(), pinfo)
        if dialog.selected_signal is not None:
            self._do_send_signal(pinfo, dialog.selected_signal)
    
    def _quick_signal(self, sig: int):
        """Send a signal quickly."""
        pinfo = self.get_selected_process()
        if pinfo:
            self._do_send_signal(pinfo, sig)
    
    def _do_send_signal(self, pinfo: ProcessInfo, signal_num: int):
        """Actually send the signal."""
        signals = get_signal_descriptions()
        sig_name = signals.get(signal_num, ("?", "?"))[0]
        
        if self.manager.can_signal_without_sudo(pinfo):
            success, message = self.manager.send_signal(pinfo, signal_num)
        else:
            # Need sudo password
            msg = _("Sending {sig_name} to {name} (PID {pid})\n"
                    "owned by {user} requires elevated privileges.").format(
                sig_name=sig_name, name=pinfo.name, pid=pinfo.pid, user=pinfo.username)
            
            dialog = PasswordDialog(self.winfo_toplevel(), _("Authentication Required"), msg)
            if dialog.password:
                success, message = self.manager.send_signal(pinfo, signal_num, dialog.password)
            else:
                return
        
        if success:
            messagebox.showinfo(_("Success"), message)
            if self.on_signal_sent:
                self.on_signal_sent()
        else:
            messagebox.showerror(_("Error"), message)
    
    def _expand_all(self):
        """Expand all tree nodes."""
        def expand(item):
            self.tree.item(item, open=True)
            for child in self.tree.get_children(item):
                expand(child)
        
        for item in self.tree.get_children():
            expand(item)
    
    def _collapse_all(self):
        """Collapse all tree nodes."""
        def collapse(item):
            for child in self.tree.get_children(item):
                collapse(child)
            self.tree.item(item, open=False)
        
        for item in self.tree.get_children():
            collapse(item)


class StatusBar(ttk.Frame):
    """Status bar showing process counts and messages."""
    
    def __init__(self, parent, manager: ProcessManager):
        super().__init__(parent)
        self.manager = manager
        
        self.status_label = ttk.Label(self, text="")
        self.status_label.pack(side='left', padx=5)
        
        self.message_label = ttk.Label(self, text="")
        self.message_label.pack(side='right', padx=5)
        
        self.update_status()
    
    def update_status(self):
        """Update status display."""
        total = len(self.manager.processes)
        shown = len(self.manager.flat_list)
        
        text = _("Processes: {shown}/{total}").format(shown=shown, total=total)
        if self.manager.filter_pattern:
            mode = _("regex") if self.manager.filter_regex else _("simple")
            text += " | " + _("Filter ({mode}): {pattern}").format(mode=mode, pattern=self.manager.filter_pattern)
        
        self.status_label.config(text=text)
    
    def set_message(self, message: str):
        """Set a temporary message."""
        self.message_label.config(text=message)
        # Clear after 3 seconds
        self.after(3000, lambda: self.message_label.config(text=""))


class PJPSGUI:
    """Main GUI application."""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title(_("PJPS - Process Viewer"))
        self.root.geometry("1000x600")
        
        # Set icon (if available)
        try:
            self.root.iconname("PJPS")
        except:
            pass
        
        # Initialize manager
        self.manager = ProcessManager()
        self.manager.refresh()
        
        # Build UI
        self._build_ui()
        
        # Set up auto-refresh
        self._schedule_refresh()
        
        # Keyboard shortcuts
        self._bind_shortcuts()
    
    def _build_ui(self):
        """Build the user interface."""
        # Main container
        main_frame = ttk.Frame(self.root, padding=5)
        main_frame.pack(fill='both', expand=True)
        
        # Toolbar
        toolbar = ttk.Frame(main_frame)
        toolbar.pack(fill='x', pady=(0, 5))
        
        ttk.Button(toolbar, text=_("Refresh"), command=self._refresh).pack(side='left', padx=2)
        ttk.Button(toolbar, text=_("Expand All"), command=self._expand_all).pack(side='left', padx=2)
        ttk.Button(toolbar, text=_("Collapse All"), command=self._collapse_all).pack(side='left', padx=2)
        
        ttk.Separator(toolbar, orient='vertical').pack(side='left', fill='y', padx=10)
        
        ttk.Button(toolbar, text=_("Details"), command=self._show_details).pack(side='left', padx=2)
        ttk.Button(toolbar, text=_("Signal"), command=self._send_signal).pack(side='left', padx=2)
        ttk.Button(toolbar, text=_("Terminate"), command=lambda: self._quick_signal(15)).pack(side='left', padx=2)
        ttk.Button(toolbar, text=_("Kill"), command=lambda: self._quick_signal(9)).pack(side='left', padx=2)
        
        # Search bar
        self.search_bar = SearchBar(toolbar, self._on_search)
        self.search_bar.pack(side='right')
        
        # Tree view
        self.tree_view = ProcessTreeView(main_frame, self.manager)
        self.tree_view.pack(fill='both', expand=True)
        self.tree_view.on_signal_sent = self._refresh
        
        # Status bar
        self.status_bar = StatusBar(main_frame, self.manager)
        self.status_bar.pack(fill='x', pady=(5, 0))
        
        # Menu bar
        self._build_menu()
    
    def _build_menu(self):
        """Build menu bar."""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label=_("File"), menu=file_menu)
        file_menu.add_command(label=_("Refresh"), command=self._refresh, accelerator="F5")
        file_menu.add_separator()
        file_menu.add_command(label=_("Quit"), command=self.root.quit, accelerator="Ctrl+Q")
        
        # View menu
        view_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label=_("View"), menu=view_menu)
        view_menu.add_command(label=_("Expand All"), command=self._expand_all, accelerator="+")
        view_menu.add_command(label=_("Collapse All"), command=self._collapse_all, accelerator="-")
        view_menu.add_separator()
        
        # Sort submenu
        sort_menu = tk.Menu(view_menu, tearoff=0)
        view_menu.add_cascade(label=_("Sort By"), menu=sort_menu)
        sort_menu.add_command(label=_("CPU Usage"), command=lambda: self._sort_by(SortColumn.CPU), accelerator="1")
        sort_menu.add_command(label=_("Memory Usage"), command=lambda: self._sort_by(SortColumn.MEMORY), accelerator="2")
        sort_menu.add_command(label=_("PID"), command=lambda: self._sort_by(SortColumn.PID), accelerator="3")
        sort_menu.add_command(label=_("Name"), command=lambda: self._sort_by(SortColumn.NAME), accelerator="4")
        sort_menu.add_command(label=_("User"), command=lambda: self._sort_by(SortColumn.USER), accelerator="5")
        sort_menu.add_command(label=_("Start Time"), command=lambda: self._sort_by(SortColumn.START_TIME), accelerator="6")
        
        # Process menu
        proc_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label=_("Process"), menu=proc_menu)
        proc_menu.add_command(label=_("Details"), command=self._show_details, accelerator="Enter")
        proc_menu.add_separator()
        proc_menu.add_command(label=_("Send Signal..."), command=self._send_signal, accelerator="S")
        proc_menu.add_command(label=_("Terminate (SIGTERM)"), command=lambda: self._quick_signal(15), accelerator="T")
        proc_menu.add_command(label=_("Kill (SIGKILL)"), command=lambda: self._quick_signal(9), accelerator="K")
        
        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label=_("Help"), menu=help_menu)
        help_menu.add_command(label=_("About"), command=self._show_about)
    
    def _bind_shortcuts(self):
        """Bind keyboard shortcuts."""
        self.root.bind('<F5>', lambda e: self._refresh())
        self.root.bind('<Control-q>', lambda e: self.root.quit())
        self.root.bind('<Control-f>', lambda e: self.search_bar.entry.focus_set())
        self.root.bind('<Escape>', lambda e: self._clear_search())
        
        self.root.bind('+', lambda e: self._expand_all())
        self.root.bind('-', lambda e: self._collapse_all())
        
        self.root.bind('1', lambda e: self._sort_by(SortColumn.CPU))
        self.root.bind('2', lambda e: self._sort_by(SortColumn.MEMORY))
        self.root.bind('3', lambda e: self._sort_by(SortColumn.PID))
        self.root.bind('4', lambda e: self._sort_by(SortColumn.NAME))
        self.root.bind('5', lambda e: self._sort_by(SortColumn.USER))
        self.root.bind('6', lambda e: self._sort_by(SortColumn.START_TIME))
        
        self.root.bind('s', lambda e: self._send_signal())
        self.root.bind('S', lambda e: self._send_signal())
        self.root.bind('t', lambda e: self._quick_signal(15))
        self.root.bind('T', lambda e: self._quick_signal(15))
        self.root.bind('k', lambda e: self._quick_signal(9))
        self.root.bind('K', lambda e: self._quick_signal(9))
    
    def _schedule_refresh(self):
        """Schedule auto-refresh."""
        def do_refresh():
            self.manager.refresh()
            self.tree_view.refresh()
            self.status_bar.update_status()
            self._schedule_refresh()
        
        self.root.after(2000, do_refresh)
    
    def _refresh(self):
        """Manual refresh."""
        self.manager.refresh()
        self.tree_view.refresh()
        self.status_bar.update_status()
        self.status_bar.set_message(_("Refreshed"))
    
    def _on_search(self, pattern: str, is_regex: bool):
        """Handle search/filter."""
        self.manager.set_filter(pattern, is_regex)
        self.tree_view.refresh()
        self.status_bar.update_status()
    
    def _clear_search(self):
        """Clear search."""
        self.search_bar._clear()
    
    def _expand_all(self):
        """Expand all nodes."""
        self.tree_view._expand_all()
    
    def _collapse_all(self):
        """Collapse all nodes."""
        self.tree_view._collapse_all()
    
    def _sort_by(self, column: SortColumn):
        """Sort by column."""
        self.manager.set_sort(column)
        self.tree_view.refresh()
    
    def _show_details(self):
        """Show process details."""
        self.tree_view._show_details()
    
    def _send_signal(self):
        """Show signal dialog."""
        self.tree_view._send_signal()
    
    def _quick_signal(self, sig: int):
        """Send quick signal."""
        self.tree_view._quick_signal(sig)
    
    def _show_about(self):
        """Show about dialog."""
        messagebox.showinfo(
            _("About PJPS"),
            _("PJPS - Process Viewer on Steroids") + "\n\n"
            + _("Version {version}").format(version="1.0.0") + "\n\n"
            + _("A powerful process management utility\n"
                "with TUI and GUI interfaces.") + "\n\n"
            + _("Copyright (c) 2026 Paige Julianne Sullivan\n"
                "Licensed under the MIT License")
        )
    
    def run(self):
        """Run the GUI."""
        self.root.mainloop()


def main():
    """Entry point for GUI."""
    app = PJPSGUI()
    app.run()


if __name__ == "__main__":
    main()
