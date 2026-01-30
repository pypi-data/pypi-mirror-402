"""
Terminal User Interface for PJPS.

Midnight Commander-style TUI with mouse support and keyboard navigation.

Copyright (c) 2026 Paige Julianne Sullivan
Licensed under the MIT License
"""

import urwid
from typing import Optional, List, Callable, Any

from .core import ProcessManager, ProcessInfo, SortColumn, get_signal_descriptions, get_signal_list
from .locale import _


# Midnight Commander-inspired color palette (improved contrast)
PALETTE = [
    # Name, foreground, background, mono, foreground_high, background_high
    ('body', 'white', 'black'),
    ('header', 'white', 'dark blue', 'bold'),
    ('footer', 'black', 'light gray'),
    ('footer_key', 'white', 'dark blue', 'bold'),
    ('footer_text', 'black', 'light gray'),
    ('selected', 'white', 'dark blue', 'bold'),
    ('selected_focus', 'white', 'dark cyan', 'bold'),
    ('tree_line', 'light gray', 'black'),
    ('process_name', 'light cyan', 'black', 'bold'),
    ('process_name_focus', 'white', 'dark cyan', 'bold'),
    ('cpu_high', 'light red', 'black', 'bold'),
    ('cpu_high_focus', 'light red', 'dark cyan', 'bold'),
    ('mem_high', 'yellow', 'black'),
    ('mem_high_focus', 'yellow', 'dark cyan'),
    ('frame', 'light cyan', 'black'),
    ('frame_title', 'white', 'dark blue', 'bold'),
    ('dialog', 'black', 'light gray'),
    ('dialog_title', 'white', 'dark red', 'bold'),
    ('dialog_button', 'black', 'light gray'),
    ('dialog_button_focus', 'white', 'dark blue', 'bold'),
    ('edit', 'white', 'dark gray'),
    ('edit_focus', 'white', 'dark blue'),
    ('error', 'white', 'dark red', 'bold'),
    ('success', 'white', 'dark green', 'bold'),
    ('info', 'light cyan', 'black'),
    ('status_bar', 'white', 'dark blue'),
    ('autorefresh_on', 'light green', 'black'),
    ('autorefresh_off', 'light red', 'black'),
]


class ProcessWidget(urwid.WidgetWrap):
    """Widget representing a single process in the tree."""
    
    signals = ['select', 'toggle']
    
    def __init__(self, pinfo: ProcessInfo, manager: ProcessManager):
        self.pinfo = pinfo
        self.manager = manager
        
        self._selectable = True
        
        # Build the display
        widget = self._build_widget()
        super().__init__(widget)
    
    def _build_widget(self) -> urwid.Widget:
        """Build the process row widget."""
        depth = self.pinfo.depth
        has_children = len(self.pinfo.children) > 0
        
        # Tree structure indicator
        if depth > 0:
            prefix = "  " * (depth - 1)
            if has_children:
                if self.pinfo.expanded:
                    prefix += "[-]"
                else:
                    prefix += "[+]"
            else:
                prefix += " |- "
        else:
            if has_children:
                if self.pinfo.expanded:
                    prefix = "[-]"
                else:
                    prefix = "[+]"
            else:
                prefix = " "
        
        # Column widths
        pid_w = 7
        user_w = 10
        cpu_w = 6
        mem_w = 6
        status_w = 8
        ports_w = 18
        time_w = 12
        
        # Format fields
        pid_str = f"{self.pinfo.pid:>{pid_w}}"
        user_str = f"{self.pinfo.username[:user_w]:<{user_w}}"
        
        cpu_str = f"{self.pinfo.cpu_percent:>{cpu_w-1}.1f}%"
        mem_str = f"{self.pinfo.memory_percent:>{mem_w-1}.1f}%"
        status_str = f"{self.pinfo.status[:status_w]:<{status_w}}"
        ports_str = self.pinfo.listening_ports_str[:ports_w] if self.pinfo.listening_ports_str else ""
        ports_str = f"{ports_str:<{ports_w}}"
        time_str = f"{self.pinfo.start_time_str:>{time_w}}"
        
        # Remaining space for name (with tree prefix)
        name_display = prefix + self.pinfo.name
        
        # Build text with attributes
        text_parts = []
        
        # Add tree prefix
        text_parts.append(('tree_line', prefix))
        
        # Add process name
        name_attr = 'process_name'
        text_parts.append((name_attr, self.pinfo.name))
        
        # Calculate padding needed
        current_len = len(prefix) + len(self.pinfo.name)
        fixed_cols = pid_w + user_w + cpu_w + mem_w + status_w + time_w + 5  # 5 for separators
        # We'll use columns for better layout
        
        # CPU color
        cpu_attr = 'body'
        if self.pinfo.cpu_percent > 50:
            cpu_attr = 'cpu_high'
        elif self.pinfo.cpu_percent > 20:
            cpu_attr = 'mem_high'
        
        # Memory color
        mem_attr = 'body'
        if self.pinfo.memory_percent > 50:
            mem_attr = 'cpu_high'
        elif self.pinfo.memory_percent > 20:
            mem_attr = 'mem_high'
        
        # Ports color (highlight if has listening ports)
        ports_attr = 'info' if self.pinfo.listening_ports else 'body'
        
        # Create columns
        cols = urwid.Columns([
            ('weight', 1, urwid.Text([('tree_line', prefix), ('process_name', self.pinfo.name)])),
            (pid_w, urwid.Text(('body', pid_str))),
            (user_w, urwid.Text(('body', user_str))),
            (cpu_w, urwid.Text((cpu_attr, cpu_str))),
            (mem_w, urwid.Text((mem_attr, mem_str))),
            (status_w, urwid.Text(('body', status_str))),
            (ports_w, urwid.Text((ports_attr, ports_str))),
            (time_w, urwid.Text(('body', time_str))),
        ], dividechars=1)
        
        return urwid.AttrMap(cols, 'body', focus_map={
            'body': 'selected_focus',
            'tree_line': 'selected_focus',
            'process_name': 'process_name_focus',
            'cpu_high': 'cpu_high_focus',
            'mem_high': 'mem_high_focus',
            'info': 'selected_focus',
        })
    
    def selectable(self):
        return True
    
    def keypress(self, size, key):
        if key in ('enter', ' '):
            if self.pinfo.children:
                self._emit('toggle', self.pinfo)
            return None
        return key
    
    def mouse_event(self, size, event, button, col, row, focus):
        if event == 'mouse press' and button == 1:
            # Check if click is in the tree expand/collapse area
            depth = self.pinfo.depth
            prefix_len = depth * 2 + (3 if self.pinfo.children else 4)
            
            if col < prefix_len and self.pinfo.children:
                self._emit('toggle', self.pinfo)
                return True
            else:
                self._emit('select', self.pinfo)
                return True
        return False


class ProcessListBox(urwid.ListBox):
    """ListBox containing process widgets with custom key handling."""
    
    signals = ['process_selected', 'process_action']
    
    def __init__(self, manager: ProcessManager):
        self.manager = manager
        self.process_widgets: List[ProcessWidget] = []
        
        walker = urwid.SimpleFocusListWalker([])
        super().__init__(walker)
        
        self.refresh()
    
    def refresh(self):
        """Refresh the process list."""
        self.manager.refresh()
        self._rebuild_widgets()
    
    def _rebuild_widgets(self):
        """Rebuild widget list from manager's flat list."""
        # Save current focus position
        try:
            old_focus = self.focus_position
        except IndexError:
            old_focus = 0
        
        self.process_widgets.clear()
        self.body.clear()
        
        for pinfo in self.manager.flat_list:
            widget = ProcessWidget(pinfo, self.manager)
            urwid.connect_signal(widget, 'toggle', self._on_toggle)
            urwid.connect_signal(widget, 'select', self._on_select)
            self.process_widgets.append(widget)
            self.body.append(widget)
        
        # Restore focus
        if self.body:
            self.focus_position = min(old_focus, len(self.body) - 1)
    
    def _on_toggle(self, widget, pinfo):
        """Handle toggle expand/collapse."""
        self.manager.toggle_expansion(pinfo)
        self._rebuild_widgets()
    
    def _on_select(self, widget, pinfo):
        """Handle process selection."""
        self._emit('process_selected', pinfo)
    
    def get_focused_process(self) -> Optional[ProcessInfo]:
        """Get currently focused process."""
        try:
            focus_widget = self.focus
            if isinstance(focus_widget, ProcessWidget):
                return focus_widget.pinfo
        except (IndexError, AttributeError):
            pass
        return None
    
    def keypress(self, size, key):
        if key == 'enter':
            pinfo = self.get_focused_process()
            if pinfo and pinfo.children:
                self.manager.toggle_expansion(pinfo)
                self._rebuild_widgets()
                return None
        return super().keypress(size, key)


class ClickableHeader(urwid.Text):
    """Clickable header column for sorting."""
    
    signals = ['click']
    
    def __init__(self, markup, sort_column: Optional[SortColumn] = None, align='left'):
        super().__init__(markup, align=align)
        self.sort_column = sort_column
        self._selectable = sort_column is not None
    
    def selectable(self):
        return self._selectable
    
    def mouse_event(self, size, event, button, col, row, focus):
        if event == 'mouse press' and button == 1 and self.sort_column is not None:
            self._emit('click', self.sort_column)
            return True
        return False
    
    def keypress(self, size, key):
        return key


class HeaderWidget(urwid.WidgetWrap):
    """Column headers with sort indicators - clickable for sorting."""
    
    signals = ['sort_changed']
    
    def __init__(self, manager: ProcessManager):
        self.manager = manager
        self._headers = {}
        widget = self._build_widget()
        super().__init__(widget)
    
    def _build_widget(self) -> urwid.Widget:
        """Build header row."""
        def sort_indicator(col: SortColumn) -> str:
            if self.manager.sort_column == col:
                return " v" if self.manager.sort_reverse else " ^"
            return ""
        
        pid_w = 7
        user_w = 10
        cpu_w = 6
        mem_w = 6
        status_w = 8
        ports_w = 18
        time_w = 12
        
        # Create clickable headers
        name_h = ClickableHeader(('header', f"{_('NAME')}{sort_indicator(SortColumn.NAME)}"), SortColumn.NAME)
        pid_h = ClickableHeader(('header', f"{_('PID')}{sort_indicator(SortColumn.PID)}"), SortColumn.PID)
        user_h = ClickableHeader(('header', f"{_('USER')}{sort_indicator(SortColumn.USER)}"), SortColumn.USER)
        cpu_h = ClickableHeader(('header', f"{_('CPU%')}{sort_indicator(SortColumn.CPU)}"), SortColumn.CPU)
        mem_h = ClickableHeader(('header', f"{_('MEM%')}{sort_indicator(SortColumn.MEMORY)}"), SortColumn.MEMORY)
        status_h = ClickableHeader(('header', _("STATUS")), None)  # Not sortable
        ports_h = ClickableHeader(('header', _("PORTS")), None)  # Not sortable
        time_h = ClickableHeader(('header', f"{_('STARTED')}{sort_indicator(SortColumn.START_TIME)}"), SortColumn.START_TIME)
        
        # Connect signals
        for h in [name_h, pid_h, user_h, cpu_h, mem_h, time_h]:
            if h.sort_column is not None:
                urwid.connect_signal(h, 'click', self._on_header_click)
        
        cols = urwid.Columns([
            ('weight', 1, name_h),
            (pid_w, pid_h),
            (user_w, user_h),
            (cpu_w, cpu_h),
            (mem_w, mem_h),
            (status_w, status_h),
            (ports_w, ports_h),
            (time_w, time_h),
        ], dividechars=1)
        
        return urwid.AttrMap(cols, 'header')
    
    def _on_header_click(self, widget, sort_column):
        """Handle header click for sorting."""
        self._emit('sort_changed', sort_column)
    
    def update(self):
        """Update header to reflect current sort."""
        self._w = self._build_widget()


class ClickableText(urwid.Text):
    """Text widget that responds to mouse clicks."""
    
    signals = ['click']
    
    def __init__(self, markup, action_key: str, align='left'):
        super().__init__(markup, align=align)
        self.action_key = action_key
        self._selectable = True
    
    def selectable(self):
        return True
    
    def mouse_event(self, size, event, button, col, row, focus):
        if event == 'mouse press' and button == 1:
            self._emit('click', self.action_key)
            return True
        return False
    
    def keypress(self, size, key):
        return key


class FooterWidget(urwid.WidgetWrap):
    """Function key bar at the bottom - clickable."""
    
    signals = ['action']
    
    def __init__(self, auto_refresh: bool = True):
        self._buttons = {}
        self._auto_refresh = auto_refresh
        widget = self._build_widget()
        super().__init__(widget)
    
    def _build_widget(self) -> urwid.Widget:
        keys = [
            ("F1", _("Help"), "f1"),
            ("F2", _("Details"), "f2"),
            ("F3", _("Search"), "f3"),
            ("F4", _("Filter"), "f4"),
            ("F5", _("Refresh"), "f5"),
            ("F6", _("Sort"), "f6"),
            ("F7", _("Kill"), "f7"),
            ("F8", _("Signal"), "f8"),
            ("F9", _("Tree+-"), "f9"),
            ("F10", _("Quit"), "f10"),
        ]
        
        cols = []
        for key, label, action in keys:
            key_widget = ClickableText(('footer_key', f" {key} "), action)
            label_widget = ClickableText(('footer_text', f"{label} "), action)
            
            urwid.connect_signal(key_widget, 'click', self._on_click)
            urwid.connect_signal(label_widget, 'click', self._on_click)
            
            self._buttons[action] = (key_widget, label_widget)
            cols.append(('pack', key_widget))
            cols.append(('pack', label_widget))
        
        # Add auto-refresh toggle button
        auto_key = ClickableText(('footer_key', " a "), "auto")
        if self._auto_refresh:
            auto_label = ClickableText(('autorefresh_on', _("Auto:ON ")), "auto")
        else:
            auto_label = ClickableText(('autorefresh_off', _("Auto:OFF")), "auto")
        
        urwid.connect_signal(auto_key, 'click', self._on_click)
        urwid.connect_signal(auto_label, 'click', self._on_click)
        
        self._buttons['auto'] = (auto_key, auto_label)
        cols.append(('pack', auto_key))
        cols.append(('pack', auto_label))
        
        return urwid.AttrMap(urwid.Columns(cols), 'footer')
    
    def set_auto_refresh(self, enabled: bool):
        """Update auto-refresh button state."""
        self._auto_refresh = enabled
        self._w = self._build_widget()
    
    def _on_click(self, widget, action_key):
        """Handle button click."""
        self._emit('action', action_key)


class StatusBar(urwid.WidgetWrap):
    """Status bar showing current state."""
    
    def __init__(self, manager: ProcessManager):
        self.manager = manager
        self._message = ""
        self._message_attr = "status_bar"
        self._auto_refresh = True
        widget = self._build_widget()
        super().__init__(widget)
    
    def _build_widget(self) -> urwid.Widget:
        total = len(self.manager.processes)
        shown = len(self.manager.flat_list)
        
        parts = []
        
        # Auto-refresh indicator
        if self._auto_refresh:
            parts.append(('autorefresh_on', " [Auto] "))
        else:
            parts.append(('autorefresh_off', " [Paused] "))
        
        status = _("Processes: {shown}/{total}").format(shown=shown, total=total)
        if self.manager.filter_pattern:
            mode = _("regex") if self.manager.filter_regex else _("simple")
            status += " | " + _("Filter ({mode}): {pattern}").format(mode=mode, pattern=self.manager.filter_pattern)
        
        if self._message:
            parts.append((self._message_attr, f" {self._message} "))
            parts.append(('status_bar', " | " + status))
        else:
            parts.append(('status_bar', status))
        
        text = urwid.Text(parts)
        return urwid.AttrMap(text, 'status_bar')
    
    def set_auto_refresh(self, enabled: bool):
        """Set auto-refresh state."""
        self._auto_refresh = enabled
        self._w = self._build_widget()
    
    def set_message(self, message: str, attr: str = 'status_bar'):
        """Set a temporary message."""
        self._message = message
        self._message_attr = attr
        self._w = self._build_widget()
    
    def clear_message(self):
        """Clear the message."""
        self._message = ""
        self._w = self._build_widget()
    
    def update(self):
        """Update status bar."""
        self._w = self._build_widget()


class DialogBase(urwid.WidgetWrap):
    """Base class for dialog boxes."""
    
    signals = ['close']
    
    def __init__(self, title: str, body: urwid.Widget, buttons: List[tuple]):
        self.title = title
        
        # Create button row
        button_widgets = []
        for label, callback in buttons:
            btn = urwid.Button(label)
            urwid.connect_signal(btn, 'click', callback)
            btn = urwid.AttrMap(btn, 'dialog_button', focus_map='dialog_button_focus')
            button_widgets.append(btn)
        
        button_row = urwid.Columns([('pack', b) for b in button_widgets], dividechars=2)
        button_row = urwid.Padding(button_row, align='center', width='pack')
        
        # Combine body and buttons
        pile = urwid.Pile([
            body,
            urwid.Divider(),
            button_row,
        ])
        
        # Add padding
        padded = urwid.Padding(pile, left=2, right=2)
        filled = urwid.Filler(padded, valign='top')
        
        # Add frame
        frame = urwid.LineBox(filled, title=title)
        frame = urwid.AttrMap(frame, 'dialog')
        
        super().__init__(frame)


class SearchDialog(DialogBase):
    """Search/filter dialog."""
    
    signals = ['search', 'close']
    
    def __init__(self, current_pattern: str = "", is_regex: bool = False):
        self.edit = urwid.Edit(('dialog', _("Pattern: ")), current_pattern)
        self.regex_cb = urwid.CheckBox(_("Use Regex"), state=is_regex)
        
        body = urwid.Pile([
            urwid.AttrMap(self.edit, 'edit', focus_map='edit_focus'),
            urwid.Divider(),
            self.regex_cb,
        ])
        
        super().__init__(
            _("Search / Filter"),
            body,
            [(_("OK"), self._on_ok), (_("Clear"), self._on_clear), (_("Cancel"), self._on_cancel)]
        )
    
    def _on_ok(self, button):
        pattern = self.edit.edit_text
        is_regex = self.regex_cb.state
        self._emit('search', pattern, is_regex)
        self._emit('close')
    
    def _on_clear(self, button):
        self._emit('search', "", False)
        self._emit('close')
    
    def _on_cancel(self, button):
        self._emit('close')
    
    def keypress(self, size, key):
        if key == 'esc':
            self._emit('close')
            return None
        if key == 'enter':
            self._on_ok(None)
            return None
        return super().keypress(size, key)


class SortDialog(DialogBase):
    """Sort column selection dialog."""
    
    signals = ['sort', 'close']
    
    def __init__(self, current: SortColumn, reverse: bool):
        self.current = current
        self.reverse = reverse
        
        options = [
            (SortColumn.CPU, _("CPU Usage")),
            (SortColumn.MEMORY, _("Memory Usage")),
            (SortColumn.PID, _("Process ID")),
            (SortColumn.NAME, _("Process Name")),
            (SortColumn.USER, _("User")),
            (SortColumn.START_TIME, _("Start Time")),
        ]
        
        self.radio_group = []
        radio_buttons = []
        for col, label in options:
            rb = urwid.RadioButton(self.radio_group, label, state=(col == current))
            rb._sort_column = col
            radio_buttons.append(rb)
        
        self.reverse_cb = urwid.CheckBox(_("Descending order"), state=reverse)
        
        body = urwid.Pile(radio_buttons + [urwid.Divider(), self.reverse_cb])
        
        super().__init__(
            _("Sort By"),
            body,
            [(_("OK"), self._on_ok), (_("Cancel"), self._on_cancel)]
        )
    
    def _on_ok(self, button):
        for rb in self.radio_group:
            if rb.state:
                self._emit('sort', rb._sort_column, self.reverse_cb.state)
                break
        self._emit('close')
    
    def _on_cancel(self, button):
        self._emit('close')
    
    def keypress(self, size, key):
        if key == 'esc':
            self._emit('close')
            return None
        return super().keypress(size, key)


class SignalDialog(DialogBase):
    """Signal selection dialog."""
    
    signals = ['signal', 'close']
    
    def __init__(self, pinfo: ProcessInfo):
        self.pinfo = pinfo
        
        signal_list = get_signal_list()
        
        self.radio_group = []
        radio_buttons = []
        for sig_num, sig_name, sig_desc in signal_list:
            label = f"{sig_num:2d} {sig_name:<10} - {sig_desc}"
            rb = urwid.RadioButton(self.radio_group, label, state=(sig_num == 15))
            rb._signal_num = sig_num
            radio_buttons.append(rb)
        
        # Create scrollable list
        walker = urwid.SimpleFocusListWalker(radio_buttons)
        listbox = urwid.ListBox(walker)
        listbox = urwid.BoxAdapter(listbox, height=15)
        
        title_text = urwid.Text(('dialog', _("Send signal to: {name} (PID {pid})").format(
            name=pinfo.name, pid=pinfo.pid)))
        
        body = urwid.Pile([
            title_text,
            urwid.Divider(),
            listbox,
        ])
        
        super().__init__(
            _("Send Signal"),
            body,
            [(_("Send"), self._on_send), (_("Cancel"), self._on_cancel)]
        )
    
    def _on_send(self, button):
        for rb in self.radio_group:
            if rb.state:
                self._emit('signal', self.pinfo, rb._signal_num)
                break
        self._emit('close')
    
    def _on_cancel(self, button):
        self._emit('close')
    
    def keypress(self, size, key):
        if key == 'esc':
            self._emit('close')
            return None
        return super().keypress(size, key)


class PasswordDialog(DialogBase):
    """Password prompt dialog for sudo."""
    
    signals = ['password', 'close']
    
    def __init__(self, pinfo: ProcessInfo, signal_num: int):
        self.pinfo = pinfo
        self.signal_num = signal_num
        
        signals = get_signal_descriptions()
        sig_name = signals.get(signal_num, ("?", "?"))[0]
        
        info_text = urwid.Text([
            ('dialog', _("Sending {sig_name} to ").format(sig_name=sig_name)),
            ('dialog_title', f"{pinfo.name} (PID {pinfo.pid})"),
            ('dialog', "\n" + _("owned by ")),
            ('dialog_title', pinfo.username),
            ('dialog', " " + _("requires elevated privileges.") + "\n"),
        ])
        
        self.edit = urwid.Edit(('dialog', _("Password: ")), mask='*')
        
        body = urwid.Pile([
            info_text,
            urwid.Divider(),
            urwid.AttrMap(self.edit, 'edit', focus_map='edit_focus'),
        ])
        
        super().__init__(
            _("Authentication Required"),
            body,
            [(_("OK"), self._on_ok), (_("Cancel"), self._on_cancel)]
        )
    
    def _on_ok(self, button):
        password = self.edit.edit_text
        self._emit('password', self.pinfo, self.signal_num, password)
        self._emit('close')
    
    def _on_cancel(self, button):
        self._emit('close')
    
    def keypress(self, size, key):
        if key == 'esc':
            self._emit('close')
            return None
        if key == 'enter':
            self._on_ok(None)
            return None
        return super().keypress(size, key)


class DetailsDialog(DialogBase):
    """Process details dialog."""
    
    signals = ['close']
    
    def __init__(self, pinfo: ProcessInfo, manager: ProcessManager):
        details = manager.get_process_details(pinfo)
        
        lines = []
        for key, value in details.items():
            lines.append(urwid.Text([
                ('dialog_title', f"{key}: "),
                ('dialog', str(value)),
            ]))
        
        walker = urwid.SimpleFocusListWalker(lines)
        listbox = urwid.ListBox(walker)
        listbox = urwid.BoxAdapter(listbox, height=min(len(lines) + 2, 20))
        
        super().__init__(
            _("Process Details - {name} (PID {pid})").format(name=pinfo.name, pid=pinfo.pid),
            listbox,
            [(_("Close"), self._on_close)]
        )
    
    def _on_close(self, button):
        self._emit('close')
    
    def keypress(self, size, key):
        if key in ('esc', 'enter', 'q'):
            self._emit('close')
            return None
        return super().keypress(size, key)


class HelpDialog(DialogBase):
    """Help dialog."""
    
    signals = ['close']
    
    def __init__(self):
        help_text = _("""
 PJPS - Process Viewer on Steroids
 
 KEYBOARD SHORTCUTS:
   F1, h, ?     Show this help
   F2, d        Show process details
   F3, /        Search/filter processes
   F4           Toggle regex filter
   F5, r        Refresh process list
   F6, s        Sort by column
   F7, k        Kill process (SIGKILL)
   F8, K        Send signal to process
   F9, +/-      Expand/collapse all
   F10, q       Quit
   
   a            Toggle auto-refresh
   Enter/Space  Toggle tree expand/collapse
   Arrow keys   Navigate
   Page Up/Down Scroll page
   Home/End     Go to first/last
 
 MOUSE:
   Click on function keys (F1-F10) to activate
   Click column headers to sort
   Click [+]/[-] to expand/collapse
   Click process to select
 
 SORTING:
   1  Sort by CPU
   2  Sort by Memory
   3  Sort by PID
   4  Sort by Name
   5  Sort by User
   6  Sort by Start Time
 
 Copyright (c) 2026 Paige Julianne Sullivan
 Licensed under the MIT License
 """)
        text = urwid.Text(('dialog', help_text.strip()))
        
        super().__init__(
            _("Help"),
            text,
            [(_("Close"), self._on_close)]
        )
    
    def _on_close(self, button):
        self._emit('close')
    
    def keypress(self, size, key):
        if key in ('esc', 'enter', 'q', 'f1', 'h', '?'):
            self._emit('close')
            return None
        return super().keypress(size, key)


class PJPSTUI:
    """Main TUI application."""
    
    def __init__(self):
        self.manager = ProcessManager()
        self.manager.refresh()
        
        # Auto-refresh state
        self._auto_refresh = True
        
        # Build UI components
        self.header = HeaderWidget(self.manager)
        self.process_list = ProcessListBox(self.manager)
        self.status_bar = StatusBar(self.manager)
        self.footer = FooterWidget(auto_refresh=self._auto_refresh)
        
        # Connect signals
        urwid.connect_signal(self.process_list, 'process_selected', self._on_process_selected)
        urwid.connect_signal(self.footer, 'action', self._on_footer_action)
        urwid.connect_signal(self.header, 'sort_changed', self._on_header_sort)
        
        # Main frame
        title = urwid.Text(('frame_title', " " + _("PJPS - Process Viewer") + " "), align='center')
        title = urwid.AttrMap(title, 'frame_title')
        
        body = urwid.Frame(
            body=self.process_list,
            header=self.header,
        )
        
        # Add frame border
        framed = urwid.LineBox(body, title=_("PJPS - Process Viewer"))
        framed = urwid.AttrMap(framed, 'frame')
        
        self.main_frame = urwid.Frame(
            body=framed,
            header=title,
            footer=urwid.Pile([self.status_bar, self.footer]),
        )
        
        # Overlay for dialogs
        self.overlay = None
        self.top_widget = self.main_frame
        
        # Create main loop
        self.loop = urwid.MainLoop(
            self.top_widget,
            palette=PALETTE,
            unhandled_input=self._handle_input,
            handle_mouse=True,
        )
        
        # Set up periodic refresh
        self._refresh_alarm = None
        self._schedule_refresh()
    
    def _schedule_refresh(self):
        """Schedule next auto-refresh."""
        if not self._auto_refresh:
            return
        
        def callback(loop, data):
            if self._auto_refresh:
                self._do_refresh()
            self._schedule_refresh()
        
        self._refresh_alarm = self.loop.set_alarm_in(2.0, callback)
    
    def _toggle_auto_refresh(self):
        """Toggle auto-refresh on/off."""
        self._auto_refresh = not self._auto_refresh
        self.status_bar.set_auto_refresh(self._auto_refresh)
        self.footer.set_auto_refresh(self._auto_refresh)
        
        if self._auto_refresh:
            self.status_bar.set_message(_("Auto-refresh enabled"), 'success')
            self._schedule_refresh()
        else:
            self.status_bar.set_message(_("Auto-refresh paused"), 'info')
            # Cancel existing alarm
            if self._refresh_alarm:
                self.loop.remove_alarm(self._refresh_alarm)
                self._refresh_alarm = None
    
    def _on_footer_action(self, widget, action_key):
        """Handle footer button click."""
        # Map action keys to the same handlers as keyboard
        action_map = {
            'f1': lambda: self._show_help(),
            'f2': lambda: self._show_details(),
            'f3': lambda: self._show_search(),
            'f4': lambda: self._toggle_filter_mode(),
            'f5': lambda: (self._do_refresh(), self.status_bar.set_message(_("Refreshed"), 'success')),
            'f6': lambda: self._show_sort(),
            'f7': lambda: self._kill_process(),
            'f8': lambda: self._show_signal(),
            'f9': lambda: self._toggle_all_expansion(),
            'f10': lambda: (_ for _ in ()).throw(urwid.ExitMainLoop()),
            'auto': lambda: self._toggle_auto_refresh(),
        }
        
        handler = action_map.get(action_key)
        if handler:
            handler()
    
    def _on_header_sort(self, widget, sort_column):
        """Handle header column click for sorting."""
        self._set_sort(sort_column)
    
    def _toggle_filter_mode(self):
        """Toggle regex mode for filter."""
        self.manager.filter_regex = not self.manager.filter_regex
        self.manager.set_filter(self.manager.filter_pattern, self.manager.filter_regex)
        self.process_list._rebuild_widgets()
        self.status_bar.update()
    
    def _toggle_all_expansion(self):
        """Toggle all tree expansion."""
        if any(p.expanded for p in self.manager.processes.values()):
            self.manager.collapse_all()
        else:
            self.manager.expand_all()
        self.process_list._rebuild_widgets()
    
    def _do_refresh(self):
        """Perform refresh."""
        self.process_list.refresh()
        self.header.update()
        self.status_bar.update()
    
    def _on_process_selected(self, widget, pinfo: ProcessInfo):
        """Handle process selection."""
        self.status_bar.set_message(_("Selected: {name} (PID {pid})").format(name=pinfo.name, pid=pinfo.pid))
    
    def _show_dialog(self, dialog: urwid.Widget):
        """Show a dialog overlay."""
        urwid.connect_signal(dialog, 'close', self._close_dialog)
        
        overlay = urwid.Overlay(
            dialog,
            self.main_frame,
            align='center',
            width=('relative', 60),
            valign='middle',
            height='pack',
            min_width=40,
            min_height=10,
        )
        
        self.overlay = overlay
        self.loop.widget = overlay
    
    def _close_dialog(self, *args):
        """Close the current dialog."""
        self.overlay = None
        self.loop.widget = self.main_frame
    
    def _handle_input(self, key):
        """Handle unhandled input."""
        if key in ('q', 'Q', 'f10'):
            raise urwid.ExitMainLoop()
        
        elif key in ('f1', 'h', '?'):
            self._show_help()
        
        elif key in ('f2', 'd'):
            self._show_details()
        
        elif key in ('f3', '/'):
            self._show_search()
        
        elif key == 'f4':
            self._toggle_filter_mode()
        
        elif key in ('f5', 'r'):
            self._do_refresh()
            self.status_bar.set_message(_("Refreshed"), 'success')
        
        elif key in ('f6', 's'):
            self._show_sort()
        
        elif key in ('f7', 'k'):
            self._kill_process()
        
        elif key in ('f8', 'K'):
            self._show_signal()
        
        elif key == 'f9':
            self._toggle_all_expansion()
        
        elif key in ('a', 'A'):
            self._toggle_auto_refresh()
        
        elif key == '+':
            self.manager.expand_all()
            self.process_list._rebuild_widgets()
        
        elif key == '-':
            self.manager.collapse_all()
            self.process_list._rebuild_widgets()
        
        elif key == '1':
            self._set_sort(SortColumn.CPU)
        elif key == '2':
            self._set_sort(SortColumn.MEMORY)
        elif key == '3':
            self._set_sort(SortColumn.PID)
        elif key == '4':
            self._set_sort(SortColumn.NAME)
        elif key == '5':
            self._set_sort(SortColumn.USER)
        elif key == '6':
            self._set_sort(SortColumn.START_TIME)
    
    def _set_sort(self, column: SortColumn):
        """Set sort column."""
        self.manager.set_sort(column)
        self.header.update()
        self.process_list._rebuild_widgets()
    
    def _show_help(self):
        """Show help dialog."""
        dialog = HelpDialog()
        self._show_dialog(dialog)
    
    def _show_details(self):
        """Show process details dialog."""
        pinfo = self.process_list.get_focused_process()
        if pinfo:
            dialog = DetailsDialog(pinfo, self.manager)
            self._show_dialog(dialog)
    
    def _show_search(self):
        """Show search dialog."""
        dialog = SearchDialog(self.manager.filter_pattern, self.manager.filter_regex)
        urwid.connect_signal(dialog, 'search', self._on_search)
        self._show_dialog(dialog)
    
    def _on_search(self, dialog, pattern: str, is_regex: bool):
        """Handle search."""
        self.manager.set_filter(pattern, is_regex)
        self.process_list._rebuild_widgets()
        self.status_bar.update()
    
    def _show_sort(self):
        """Show sort dialog."""
        dialog = SortDialog(self.manager.sort_column, self.manager.sort_reverse)
        urwid.connect_signal(dialog, 'sort', self._on_sort)
        self._show_dialog(dialog)
    
    def _on_sort(self, dialog, column: SortColumn, reverse: bool):
        """Handle sort selection."""
        self.manager.set_sort(column, reverse)
        self.header.update()
        self.process_list._rebuild_widgets()
    
    def _kill_process(self):
        """Kill focused process (SIGKILL)."""
        pinfo = self.process_list.get_focused_process()
        if not pinfo:
            return
        
        if self.manager.can_signal_without_sudo(pinfo):
            success, message = self.manager.kill_process(pinfo)
            attr = 'success' if success else 'error'
            self.status_bar.set_message(message, attr)
        else:
            # Need password
            dialog = PasswordDialog(pinfo, 9)
            urwid.connect_signal(dialog, 'password', self._on_password)
            self._show_dialog(dialog)
    
    def _show_signal(self):
        """Show signal selection dialog."""
        pinfo = self.process_list.get_focused_process()
        if not pinfo:
            return
        
        dialog = SignalDialog(pinfo)
        urwid.connect_signal(dialog, 'signal', self._on_signal_selected)
        self._show_dialog(dialog)
    
    def _on_signal_selected(self, dialog, pinfo: ProcessInfo, signal_num: int):
        """Handle signal selection."""
        if self.manager.can_signal_without_sudo(pinfo):
            success, message = self.manager.send_signal(pinfo, signal_num)
            attr = 'success' if success else 'error'
            self.status_bar.set_message(message, attr)
        else:
            # Need password
            dialog = PasswordDialog(pinfo, signal_num)
            urwid.connect_signal(dialog, 'password', self._on_password)
            self._show_dialog(dialog)
    
    def _on_password(self, dialog, pinfo: ProcessInfo, signal_num: int, password: str):
        """Handle password entry."""
        success, message = self.manager.send_signal(pinfo, signal_num, password)
        attr = 'success' if success else 'error'
        self.status_bar.set_message(message, attr)
    
    def run(self):
        """Run the TUI."""
        try:
            self.loop.run()
        except KeyboardInterrupt:
            pass


def main():
    """Entry point for TUI."""
    app = PJPSTUI()
    app.run()


if __name__ == "__main__":
    main()
