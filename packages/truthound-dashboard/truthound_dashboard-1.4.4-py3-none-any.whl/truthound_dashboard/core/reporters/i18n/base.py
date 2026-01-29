"""Base classes for report localization.

This module provides the core localization infrastructure including:
- SupportedLocale enum for supported languages
- ReportLocalizer class for accessing localized strings
- LocalizationRegistry for managing custom catalogs
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable


class SupportedLocale(str, Enum):
    """Supported languages for report generation.

    Based on truthound documentation:
    - 7 languages for validator error messages
    - 15 languages for reports (extended set)
    """

    # Core languages (validator error messages)
    ENGLISH = "en"
    KOREAN = "ko"
    JAPANESE = "ja"
    CHINESE = "zh"
    GERMAN = "de"
    FRENCH = "fr"
    SPANISH = "es"

    # Extended languages (reports only)
    PORTUGUESE = "pt"
    ITALIAN = "it"
    RUSSIAN = "ru"
    ARABIC = "ar"
    THAI = "th"
    VIETNAMESE = "vi"
    INDONESIAN = "id"
    TURKISH = "tr"

    @classmethod
    def from_string(cls, value: str) -> SupportedLocale:
        """Parse locale from string.

        Args:
            value: Locale code (case-insensitive, e.g., 'en', 'ko', 'EN-US')

        Returns:
            SupportedLocale enum value.

        Raises:
            ValueError: If locale is not supported.
        """
        # Normalize: take first part of locale code (e.g., 'en-US' -> 'en')
        normalized = value.lower().split("-")[0].split("_")[0]

        for locale in cls:
            if locale.value == normalized:
                return locale

        raise ValueError(
            f"Unsupported locale: {value}. "
            f"Supported locales: {[loc.value for loc in cls]}"
        )

    @property
    def native_name(self) -> str:
        """Get the native name of this locale."""
        native_names = {
            SupportedLocale.ENGLISH: "English",
            SupportedLocale.KOREAN: "한국어",
            SupportedLocale.JAPANESE: "日本語",
            SupportedLocale.CHINESE: "中文",
            SupportedLocale.GERMAN: "Deutsch",
            SupportedLocale.FRENCH: "Français",
            SupportedLocale.SPANISH: "Español",
            SupportedLocale.PORTUGUESE: "Português",
            SupportedLocale.ITALIAN: "Italiano",
            SupportedLocale.RUSSIAN: "Русский",
            SupportedLocale.ARABIC: "العربية",
            SupportedLocale.THAI: "ไทย",
            SupportedLocale.VIETNAMESE: "Tiếng Việt",
            SupportedLocale.INDONESIAN: "Bahasa Indonesia",
            SupportedLocale.TURKISH: "Türkçe",
        }
        return native_names.get(self, self.value)

    @property
    def english_name(self) -> str:
        """Get the English name of this locale."""
        english_names = {
            SupportedLocale.ENGLISH: "English",
            SupportedLocale.KOREAN: "Korean",
            SupportedLocale.JAPANESE: "Japanese",
            SupportedLocale.CHINESE: "Chinese",
            SupportedLocale.GERMAN: "German",
            SupportedLocale.FRENCH: "French",
            SupportedLocale.SPANISH: "Spanish",
            SupportedLocale.PORTUGUESE: "Portuguese",
            SupportedLocale.ITALIAN: "Italian",
            SupportedLocale.RUSSIAN: "Russian",
            SupportedLocale.ARABIC: "Arabic",
            SupportedLocale.THAI: "Thai",
            SupportedLocale.VIETNAMESE: "Vietnamese",
            SupportedLocale.INDONESIAN: "Indonesian",
            SupportedLocale.TURKISH: "Turkish",
        }
        return english_names.get(self, self.value)

    @property
    def flag_emoji(self) -> str:
        """Get the flag emoji for this locale."""
        flags = {
            SupportedLocale.ENGLISH: "🇺🇸",
            SupportedLocale.KOREAN: "🇰🇷",
            SupportedLocale.JAPANESE: "🇯🇵",
            SupportedLocale.CHINESE: "🇨🇳",
            SupportedLocale.GERMAN: "🇩🇪",
            SupportedLocale.FRENCH: "🇫🇷",
            SupportedLocale.SPANISH: "🇪🇸",
            SupportedLocale.PORTUGUESE: "🇧🇷",
            SupportedLocale.ITALIAN: "🇮🇹",
            SupportedLocale.RUSSIAN: "🇷🇺",
            SupportedLocale.ARABIC: "🇸🇦",
            SupportedLocale.THAI: "🇹🇭",
            SupportedLocale.VIETNAMESE: "🇻🇳",
            SupportedLocale.INDONESIAN: "🇮🇩",
            SupportedLocale.TURKISH: "🇹🇷",
        }
        return flags.get(self, "🌐")

    @property
    def is_rtl(self) -> bool:
        """Check if this locale uses right-to-left text direction."""
        return self == SupportedLocale.ARABIC


@dataclass
class LocaleCatalog:
    """A collection of localized strings for a specific locale.

    Attributes:
        locale: The locale this catalog is for.
        messages: Dictionary of message keys to localized strings.
        plurals: Dictionary of plural rules (optional).
        formatters: Dictionary of custom formatters (optional).
    """

    locale: SupportedLocale
    messages: dict[str, str]
    plurals: dict[str, Callable[[int], str]] = field(default_factory=dict)
    formatters: dict[str, Callable[[Any], str]] = field(default_factory=dict)

    def get(self, key: str, default: str | None = None) -> str:
        """Get a localized message by key.

        Args:
            key: Message key (dot-notation supported, e.g., 'report.title')
            default: Default value if key not found.

        Returns:
            Localized string or default.
        """
        return self.messages.get(key, default or key)

    def format(self, key: str, **kwargs: Any) -> str:
        """Get and format a localized message.

        Args:
            key: Message key.
            **kwargs: Format arguments.

        Returns:
            Formatted localized string.
        """
        message = self.get(key)
        try:
            return message.format(**kwargs)
        except (KeyError, IndexError):
            return message

    def plural(self, key: str, count: int, **kwargs: Any) -> str:
        """Get a pluralized message.

        Args:
            key: Message key base (will look for key.zero, key.one, key.other)
            count: Count for pluralization.
            **kwargs: Additional format arguments.

        Returns:
            Pluralized and formatted string.
        """
        if key in self.plurals:
            message = self.plurals[key](count)
        else:
            # Default plural rules
            if count == 0 and f"{key}.zero" in self.messages:
                message = self.messages[f"{key}.zero"]
            elif count == 1 and f"{key}.one" in self.messages:
                message = self.messages[f"{key}.one"]
            else:
                message = self.messages.get(f"{key}.other", self.get(key))

        try:
            return message.format(count=count, **kwargs)
        except (KeyError, IndexError):
            return message


class ReportLocalizer:
    """Main localization interface for report generation.

    Provides access to localized strings with fallback to English.

    Example:
        localizer = ReportLocalizer(SupportedLocale.KOREAN)
        title = localizer.t("report.title")  # "검증 리포트"
        issues = localizer.plural("report.issues", 5)  # "5개 이슈"
    """

    def __init__(
        self,
        locale: SupportedLocale,
        catalog: LocaleCatalog,
        fallback_catalog: LocaleCatalog | None = None,
    ) -> None:
        """Initialize the localizer.

        Args:
            locale: Target locale.
            catalog: Primary catalog for this locale.
            fallback_catalog: Fallback catalog (typically English).
        """
        self.locale = locale
        self._catalog = catalog
        self._fallback = fallback_catalog

    def t(self, key: str, default: str | None = None) -> str:
        """Translate a key to localized string.

        Args:
            key: Message key.
            default: Default value if not found.

        Returns:
            Localized string.
        """
        result = self._catalog.get(key)
        if result == key and self._fallback:
            result = self._fallback.get(key, default)
        return result if result != key else (default or key)

    def get(self, key: str, default: str | None = None) -> str:
        """Alias for t() method."""
        return self.t(key, default)

    def format(self, key: str, **kwargs: Any) -> str:
        """Get and format a localized message.

        Args:
            key: Message key.
            **kwargs: Format arguments.

        Returns:
            Formatted localized string.
        """
        message = self.t(key)
        try:
            return message.format(**kwargs)
        except (KeyError, IndexError):
            return message

    def plural(self, key: str, count: int, **kwargs: Any) -> str:
        """Get a pluralized message.

        Args:
            key: Message key base.
            count: Count for pluralization.
            **kwargs: Additional format arguments.

        Returns:
            Pluralized and formatted string.
        """
        return self._catalog.plural(key, count, **kwargs)

    def format_number(self, value: int | float) -> str:
        """Format a number according to locale conventions.

        Args:
            value: Number to format.

        Returns:
            Formatted number string.
        """
        # Use locale-specific formatting
        if self.locale in (SupportedLocale.GERMAN, SupportedLocale.FRENCH,
                           SupportedLocale.ITALIAN, SupportedLocale.SPANISH,
                           SupportedLocale.PORTUGUESE, SupportedLocale.RUSSIAN,
                           SupportedLocale.TURKISH):
            # European style: 1.234.567,89
            if isinstance(value, float):
                int_part = int(value)
                dec_part = f"{value - int_part:.2f}"[2:]
                return f"{int_part:,}".replace(",", ".") + "," + dec_part
            return f"{value:,}".replace(",", ".")
        else:
            # Standard style: 1,234,567.89
            if isinstance(value, float):
                return f"{value:,.2f}"
            return f"{value:,}"

    def format_percentage(self, value: float) -> str:
        """Format a percentage according to locale conventions.

        Args:
            value: Percentage value (0-100).

        Returns:
            Formatted percentage string.
        """
        return f"{value:.1f}%"

    def format_date(self, value: Any) -> str:
        """Format a date according to locale conventions.

        Args:
            value: Date/datetime object.

        Returns:
            Formatted date string.
        """
        from datetime import datetime

        if isinstance(value, datetime):
            # Use locale-appropriate format
            if self.locale in (SupportedLocale.ENGLISH,):
                return value.strftime("%m/%d/%Y %H:%M:%S")
            elif self.locale in (SupportedLocale.GERMAN, SupportedLocale.FRENCH,
                                 SupportedLocale.ITALIAN, SupportedLocale.SPANISH,
                                 SupportedLocale.PORTUGUESE, SupportedLocale.RUSSIAN):
                return value.strftime("%d/%m/%Y %H:%M:%S")
            elif self.locale in (SupportedLocale.JAPANESE, SupportedLocale.CHINESE,
                                 SupportedLocale.KOREAN):
                return value.strftime("%Y/%m/%d %H:%M:%S")
            else:
                return value.strftime("%Y-%m-%d %H:%M:%S")
        return str(value)

    @property
    def text_direction(self) -> str:
        """Get CSS text direction for this locale."""
        return "rtl" if self.locale.is_rtl else "ltr"


class LocalizationRegistry:
    """Registry for managing locale catalogs.

    Supports runtime registration of custom catalogs and
    lazy loading of built-in catalogs.
    """

    _instance: LocalizationRegistry | None = None
    _catalogs: dict[SupportedLocale, LocaleCatalog] = {}

    def __new__(cls) -> LocalizationRegistry:
        """Singleton pattern."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def register(self, catalog: LocaleCatalog) -> None:
        """Register a catalog for a locale.

        Args:
            catalog: LocaleCatalog to register.
        """
        self._catalogs[catalog.locale] = catalog

    def get_catalog(self, locale: SupportedLocale) -> LocaleCatalog | None:
        """Get the catalog for a locale.

        Args:
            locale: Target locale.

        Returns:
            LocaleCatalog or None if not registered.
        """
        return self._catalogs.get(locale)

    def get_or_load(self, locale: SupportedLocale) -> LocaleCatalog:
        """Get or lazily load a catalog for a locale.

        Args:
            locale: Target locale.

        Returns:
            LocaleCatalog for the locale.
        """
        if locale not in self._catalogs:
            self._load_builtin_catalog(locale)
        return self._catalogs.get(locale, self._get_english_fallback())

    def _load_builtin_catalog(self, locale: SupportedLocale) -> None:
        """Load a built-in catalog."""
        from . import catalogs

        catalog_map = {
            SupportedLocale.ENGLISH: catalogs.ENGLISH_CATALOG,
            SupportedLocale.KOREAN: catalogs.KOREAN_CATALOG,
            SupportedLocale.JAPANESE: catalogs.JAPANESE_CATALOG,
            SupportedLocale.CHINESE: catalogs.CHINESE_CATALOG,
            SupportedLocale.GERMAN: catalogs.GERMAN_CATALOG,
            SupportedLocale.FRENCH: catalogs.FRENCH_CATALOG,
            SupportedLocale.SPANISH: catalogs.SPANISH_CATALOG,
            SupportedLocale.PORTUGUESE: catalogs.PORTUGUESE_CATALOG,
            SupportedLocale.ITALIAN: catalogs.ITALIAN_CATALOG,
            SupportedLocale.RUSSIAN: catalogs.RUSSIAN_CATALOG,
            SupportedLocale.ARABIC: catalogs.ARABIC_CATALOG,
            SupportedLocale.THAI: catalogs.THAI_CATALOG,
            SupportedLocale.VIETNAMESE: catalogs.VIETNAMESE_CATALOG,
            SupportedLocale.INDONESIAN: catalogs.INDONESIAN_CATALOG,
            SupportedLocale.TURKISH: catalogs.TURKISH_CATALOG,
        }

        if locale in catalog_map:
            self._catalogs[locale] = catalog_map[locale]

    def _get_english_fallback(self) -> LocaleCatalog:
        """Get English catalog as fallback."""
        if SupportedLocale.ENGLISH not in self._catalogs:
            from . import catalogs
            self._catalogs[SupportedLocale.ENGLISH] = catalogs.ENGLISH_CATALOG
        return self._catalogs[SupportedLocale.ENGLISH]

    def list_locales(self) -> list[dict[str, str]]:
        """List all available locales with metadata.

        Returns:
            List of locale information dictionaries.
        """
        return [
            {
                "code": locale.value,
                "english_name": locale.english_name,
                "native_name": locale.native_name,
                "flag": locale.flag_emoji,
                "rtl": locale.is_rtl,
            }
            for locale in SupportedLocale
        ]


# Global registry instance
_registry = LocalizationRegistry()


def get_localizer(
    locale: SupportedLocale | str,
    fallback_to_english: bool = True,
) -> ReportLocalizer:
    """Get a localizer for the specified locale.

    Args:
        locale: Target locale (SupportedLocale or string code).
        fallback_to_english: Whether to fall back to English for missing keys.

    Returns:
        ReportLocalizer instance.

    Raises:
        ValueError: If locale is not supported.
    """
    if isinstance(locale, str):
        locale = SupportedLocale.from_string(locale)

    catalog = _registry.get_or_load(locale)
    fallback = (
        _registry.get_or_load(SupportedLocale.ENGLISH)
        if fallback_to_english and locale != SupportedLocale.ENGLISH
        else None
    )

    return ReportLocalizer(locale, catalog, fallback)


def get_supported_locales() -> list[dict[str, Any]]:
    """Get list of all supported locales.

    Returns:
        List of locale information dictionaries.
    """
    return _registry.list_locales()
