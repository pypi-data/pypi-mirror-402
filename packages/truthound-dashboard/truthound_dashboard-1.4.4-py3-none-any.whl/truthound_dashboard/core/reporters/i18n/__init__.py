"""Report internationalization (i18n) module.

This module provides localization support for report generation,
allowing reports to be generated in multiple languages.

Supports 15 languages as specified in truthound documentation:
en, ko, ja, zh, de, fr, es, pt, it, ru, ar, th, vi, id, tr

Example:
    from truthound_dashboard.core.reporters.i18n import get_localizer, SupportedLocale

    localizer = get_localizer(SupportedLocale.KOREAN)
    title = localizer.get("report.title")  # "검증 리포트"
"""

from .base import (
    ReportLocalizer,
    SupportedLocale,
    get_localizer,
    get_supported_locales,
    LocalizationRegistry,
)
from .catalogs import (
    ENGLISH_CATALOG,
    KOREAN_CATALOG,
    JAPANESE_CATALOG,
    CHINESE_CATALOG,
    GERMAN_CATALOG,
    FRENCH_CATALOG,
    SPANISH_CATALOG,
    PORTUGUESE_CATALOG,
    ITALIAN_CATALOG,
    RUSSIAN_CATALOG,
    ARABIC_CATALOG,
    THAI_CATALOG,
    VIETNAMESE_CATALOG,
    INDONESIAN_CATALOG,
    TURKISH_CATALOG,
)

__all__ = [
    # Core classes
    "ReportLocalizer",
    "SupportedLocale",
    "LocalizationRegistry",
    # Factory functions
    "get_localizer",
    "get_supported_locales",
    # Catalogs (for extension)
    "ENGLISH_CATALOG",
    "KOREAN_CATALOG",
    "JAPANESE_CATALOG",
    "CHINESE_CATALOG",
    "GERMAN_CATALOG",
    "FRENCH_CATALOG",
    "SPANISH_CATALOG",
    "PORTUGUESE_CATALOG",
    "ITALIAN_CATALOG",
    "RUSSIAN_CATALOG",
    "ARABIC_CATALOG",
    "THAI_CATALOG",
    "VIETNAMESE_CATALOG",
    "INDONESIAN_CATALOG",
    "TURKISH_CATALOG",
]
