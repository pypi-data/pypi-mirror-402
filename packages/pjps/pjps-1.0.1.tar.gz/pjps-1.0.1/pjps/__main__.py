#!/usr/bin/env python3
"""
PJPS - Process Viewer on Steroids

Main entry point with CLI argument parsing.

Copyright (c) 2026 Paige Julianne Sullivan
Licensed under the MIT License
"""

import argparse
import sys

# Initialize locale early
from .locale import _


def main():
    """Main entry point - parse arguments and launch appropriate interface."""
    parser = argparse.ArgumentParser(
        prog='pjps',
        description=_('PJPS - A powerful process viewer with TUI and GUI interfaces'),
        epilog=_('Copyright (c) 2026 Paige Julianne Sullivan - MIT License')
    )
    
    parser.add_argument(
        '-v', '--version',
        action='version',
        version='%(prog)s 1.0.0'
    )
    
    interface_group = parser.add_mutually_exclusive_group()
    interface_group.add_argument(
        '-t', '--tui',
        action='store_true',
        help=_('Launch terminal user interface (default)')
    )
    interface_group.add_argument(
        '-g', '--gui',
        action='store_true',
        help=_('Launch graphical user interface')
    )
    
    parser.add_argument(
        '--no-refresh',
        action='store_true',
        help=_('Disable auto-refresh (useful for debugging)')
    )
    
    args = parser.parse_args()
    
    if args.gui:
        main_gui()
    else:
        main_tui()


def main_tui():
    """Launch TUI interface."""
    try:
        from .tui import main as tui_main
        tui_main()
    except ImportError as e:
        print(_("Error: Could not import TUI module: {error}").format(error=e), file=sys.stderr)
        print(_("Make sure urwid is installed: pip install urwid"), file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(_("Error launching TUI: {error}").format(error=e), file=sys.stderr)
        sys.exit(1)


def main_gui():
    """Launch GUI interface."""
    try:
        from .gui import main as gui_main
        gui_main()
    except ImportError as e:
        print(_("Error: Could not import GUI module: {error}").format(error=e), file=sys.stderr)
        print(_("Make sure tkinter is available."), file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(_("Error launching GUI: {error}").format(error=e), file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
