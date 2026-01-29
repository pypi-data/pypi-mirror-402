"""Internationalization module for truthound-dashboard.

This module provides unified i18n support for:
- API error messages
- Validation result messages
- User-facing content

It reuses the SupportedLocale enum from reporters/i18n for consistency.

Example:
    from truthound_dashboard.core.i18n import (
        get_message,
        detect_locale,
        SupportedLocale,
        SUPPORTED_LOCALES,
    )

    # Get error message in detected locale
    locale = detect_locale(request)
    message = get_message("error.source_not_found", locale)
"""

from truthound_dashboard.core.reporters.i18n.base import SupportedLocale

from .detector import detect_locale, parse_accept_language
from .messages import ERROR_MESSAGES, get_all_messages, get_message

# All supported locale codes
SUPPORTED_LOCALES = [locale.value for locale in SupportedLocale]

__all__ = [
    # Core classes
    "SupportedLocale",
    # Functions
    "get_message",
    "get_all_messages",
    "detect_locale",
    "parse_accept_language",
    # Constants
    "SUPPORTED_LOCALES",
    "ERROR_MESSAGES",
]
