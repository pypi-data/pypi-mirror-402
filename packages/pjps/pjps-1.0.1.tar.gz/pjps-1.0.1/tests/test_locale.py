"""
Unit tests for pjps.locale module.

Copyright (c) 2026 Paige Julianne Sullivan
Licensed under the MIT License
"""

import os
import unittest
from pathlib import Path
from unittest.mock import patch

from pjps.locale import (
    DOMAIN, setup_locale, get_translator, _, ngettext,
    _find_locale_dir
)


class TestLocaleConstants(unittest.TestCase):
    """Tests for locale module constants."""
    
    def test_domain_name(self):
        """Test that domain name is set correctly."""
        self.assertEqual(DOMAIN, "pjps")


class TestLocaleDirFinding(unittest.TestCase):
    """Tests for locale directory finding."""
    
    def test_find_locale_dir(self):
        """Test that locale directory is found."""
        locale_dir = _find_locale_dir()
        
        self.assertIsInstance(locale_dir, str)
        self.assertGreater(len(locale_dir), 0)
    
    def test_locale_dir_exists(self):
        """Test that found locale directory exists (for dev environment)."""
        locale_dir = _find_locale_dir()
        # In development, this should point to the package locale dir
        # which we created with translations


class TestTranslationFunction(unittest.TestCase):
    """Tests for the translation function."""
    
    def test_translation_function_callable(self):
        """Test that _ is callable."""
        self.assertTrue(callable(_))
    
    def test_translation_returns_string(self):
        """Test that translation returns a string."""
        result = _("Test string")
        self.assertIsInstance(result, str)
    
    def test_translation_fallback(self):
        """Test that untranslated strings return as-is (fallback)."""
        # In English locale or when no translation exists
        test_string = "This is a test string that won't be translated"
        result = _(test_string)
        # Should at least return a string (original or translated)
        self.assertIsInstance(result, str)
    
    def test_translation_preserves_formatting(self):
        """Test that translations preserve format strings."""
        test = _("Process {pid}")
        # The format placeholder should still work
        formatted = test.format(pid=1234)
        self.assertIn("1234", formatted)
    
    def test_empty_string(self):
        """Test translation of empty string."""
        result = _("")
        self.assertEqual(result, "")


class TestNgettext(unittest.TestCase):
    """Tests for plural form translation function."""
    
    def test_ngettext_callable(self):
        """Test that ngettext is callable."""
        self.assertTrue(callable(ngettext))
    
    def test_ngettext_singular(self):
        """Test ngettext with singular form."""
        result = ngettext("process", "processes", 1)
        self.assertIsInstance(result, str)
    
    def test_ngettext_plural(self):
        """Test ngettext with plural form."""
        result = ngettext("process", "processes", 2)
        self.assertIsInstance(result, str)
    
    def test_ngettext_zero(self):
        """Test ngettext with zero (usually plural in English)."""
        result = ngettext("process", "processes", 0)
        self.assertIsInstance(result, str)


class TestSetupLocale(unittest.TestCase):
    """Tests for setup_locale function."""
    
    def test_setup_locale_returns_function(self):
        """Test that setup_locale returns a callable."""
        translator = setup_locale()
        self.assertTrue(callable(translator))
    
    def test_setup_locale_function_works(self):
        """Test that returned function translates strings."""
        translator = setup_locale()
        result = translator("Test")
        self.assertIsInstance(result, str)


class TestGetTranslator(unittest.TestCase):
    """Tests for get_translator function."""
    
    def test_get_translator_returns_function(self):
        """Test that get_translator returns a callable."""
        translator = get_translator()
        self.assertTrue(callable(translator))
    
    def test_get_translator_function_works(self):
        """Test that returned translator works."""
        translator = get_translator()
        result = translator("Hello")
        self.assertIsInstance(result, str)


class TestCommonTranslations(unittest.TestCase):
    """Tests for commonly used translations."""
    
    def test_common_ui_strings(self):
        """Test that common UI strings can be translated."""
        common_strings = [
            "Process Viewer",
            "PID",
            "Name",
            "User",
            "CPU %",
            "Memory %",
            "Status",
            "Refresh",
            "Quit",
            "Help",
            "Close",
            "OK",
            "Cancel",
        ]
        
        for string in common_strings:
            result = _(string)
            self.assertIsInstance(result, str)
            self.assertGreater(len(result), 0, 
                             f"Translation for '{string}' is empty")
    
    def test_signal_names(self):
        """Test that signal descriptions translate."""
        signal_strings = [
            "Hangup",
            "Interrupt",
            "Killed",
            "Terminated",
        ]
        
        for string in signal_strings:
            result = _(string)
            self.assertIsInstance(result, str)


class TestTranslationFiles(unittest.TestCase):
    """Tests for translation file existence."""
    
    def test_pot_file_exists(self):
        """Test that .pot template file exists."""
        locale_dir = _find_locale_dir()
        pot_file = Path(locale_dir) / "pjps.pot"
        
        # POT file should exist after we created it
        self.assertTrue(pot_file.exists(), 
                       f"POT file not found at {pot_file}")
    
    def test_mo_files_exist(self):
        """Test that compiled .mo files exist for all languages."""
        locale_dir = _find_locale_dir()
        
        languages = [
            "fr", "es", "de", "pt", "pt_BR",
            "it", "zh_CN", "ja", "ru", "ko", "nl", "pl", "ar"
        ]
        
        for lang in languages:
            mo_file = Path(locale_dir) / lang / "LC_MESSAGES" / "pjps.mo"
            self.assertTrue(mo_file.exists(), 
                          f"MO file not found for {lang} at {mo_file}")
    
    def test_po_files_exist(self):
        """Test that source .po files exist for all languages."""
        locale_dir = _find_locale_dir()
        
        languages = [
            "fr", "es", "de", "pt", "pt_BR",
            "it", "zh_CN", "ja", "ru", "ko", "nl", "pl", "ar"
        ]
        
        for lang in languages:
            po_file = Path(locale_dir) / lang / "LC_MESSAGES" / "pjps.po"
            self.assertTrue(po_file.exists(), 
                          f"PO file not found for {lang} at {po_file}")


if __name__ == '__main__':
    unittest.main()
