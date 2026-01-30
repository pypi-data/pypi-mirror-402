"""
Internationalization support for PJPS.

Copyright (c) 2026 Paige Julianne Sullivan
Licensed under the MIT License
"""

import gettext
import locale
import os
from pathlib import Path

# Domain name for translations
DOMAIN = "pjps"

# Find the locale directory
_locale_dir = None

def _find_locale_dir():
    """Find the locale directory."""
    global _locale_dir
    if _locale_dir is not None:
        return _locale_dir
    
    # Check various locations
    candidates = [
        # Development: package/locale
        Path(__file__).parent / "locale",
        # Installed: share/locale
        Path(__file__).parent.parent / "share" / "locale",
        # System-wide
        Path("/usr/share/locale"),
        Path("/usr/local/share/locale"),
    ]
    
    for candidate in candidates:
        if candidate.exists():
            _locale_dir = str(candidate)
            return _locale_dir
    
    # Fallback to package directory (will use null translations)
    _locale_dir = str(Path(__file__).parent / "locale")
    return _locale_dir


def setup_locale():
    """Set up locale and gettext."""
    try:
        locale.setlocale(locale.LC_ALL, '')
    except locale.Error:
        pass
    
    locale_dir = _find_locale_dir()
    
    # Install gettext
    try:
        translation = gettext.translation(DOMAIN, locale_dir, fallback=True)
        translation.install()
        return translation.gettext
    except Exception:
        # Return identity function if translation fails
        return lambda s: s


def get_translator():
    """Get the translation function."""
    return setup_locale()


# Initialize and export the translation function
_ = setup_locale()

# Also export ngettext for plural forms
def _find_ngettext():
    """Get ngettext function."""
    locale_dir = _find_locale_dir()
    try:
        translation = gettext.translation(DOMAIN, locale_dir, fallback=True)
        return translation.ngettext
    except Exception:
        return lambda s, p, n: s if n == 1 else p

ngettext = _find_ngettext()
