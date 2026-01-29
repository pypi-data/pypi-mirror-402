"""Locale detection utilities.

This module provides functions to detect the user's preferred locale
from HTTP headers (Accept-Language) following RFC 7231.

Example:
    from fastapi import Request
    from truthound_dashboard.core.i18n import detect_locale

    @app.get("/api/v1/example")
    async def example(request: Request):
        locale = detect_locale(request)
        # Use locale for localized responses
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

from truthound_dashboard.core.reporters.i18n.base import SupportedLocale

if TYPE_CHECKING:
    from fastapi import Request

# Regex pattern for parsing Accept-Language header
# Matches: en-US, en;q=0.9, zh-Hans;q=0.8, etc.
ACCEPT_LANGUAGE_PATTERN = re.compile(
    r"([a-zA-Z]{1,8}(?:-[a-zA-Z0-9]{1,8})?)\s*(?:;\s*q\s*=\s*([\d.]+))?"
)


def parse_accept_language(header: str | None) -> list[tuple[str, float]]:
    """Parse Accept-Language header into list of (locale, quality) tuples.

    Follows RFC 7231 Section 5.3.5 for quality value parsing.

    Args:
        header: Accept-Language header value (e.g., "en-US,en;q=0.9,ko;q=0.8")

    Returns:
        List of (locale_code, quality) tuples, sorted by quality descending.

    Example:
        >>> parse_accept_language("en-US,en;q=0.9,ko;q=0.8")
        [('en-US', 1.0), ('en', 0.9), ('ko', 0.8)]
    """
    if not header:
        return []

    results: list[tuple[str, float]] = []

    for match in ACCEPT_LANGUAGE_PATTERN.finditer(header):
        locale = match.group(1)
        quality_str = match.group(2)

        # Default quality is 1.0 if not specified
        try:
            quality = float(quality_str) if quality_str else 1.0
            # Clamp quality to valid range [0, 1]
            quality = max(0.0, min(1.0, quality))
        except ValueError:
            quality = 1.0

        results.append((locale, quality))

    # Sort by quality descending
    results.sort(key=lambda x: x[1], reverse=True)
    return results


def normalize_locale_code(code: str) -> str:
    """Normalize locale code to base language code.

    Extracts the primary language subtag from a locale code.

    Args:
        code: Locale code (e.g., "en-US", "zh-Hans", "ko")

    Returns:
        Normalized locale code (e.g., "en", "zh", "ko")

    Example:
        >>> normalize_locale_code("en-US")
        'en'
        >>> normalize_locale_code("zh-Hans")
        'zh'
    """
    return code.lower().split("-")[0].split("_")[0]


def find_best_locale(
    preferred_locales: list[tuple[str, float]],
    default: SupportedLocale = SupportedLocale.ENGLISH,
) -> SupportedLocale:
    """Find the best matching supported locale from a list of preferences.

    Args:
        preferred_locales: List of (locale_code, quality) tuples.
        default: Default locale if no match found.

    Returns:
        Best matching SupportedLocale.
    """
    supported_codes = {locale.value for locale in SupportedLocale}

    for locale_code, _ in preferred_locales:
        normalized = normalize_locale_code(locale_code)

        if normalized in supported_codes:
            return SupportedLocale(normalized)

    return default


def detect_locale(
    request: Request,
    default: SupportedLocale = SupportedLocale.ENGLISH,
) -> SupportedLocale:
    """Detect locale from FastAPI request.

    Checks in order:
    1. Query parameter: ?lang=ko
    2. Accept-Language header
    3. Default locale

    Args:
        request: FastAPI Request object.
        default: Default locale if detection fails.

    Returns:
        Detected SupportedLocale.

    Example:
        @app.get("/api/v1/example")
        async def example(request: Request):
            locale = detect_locale(request)
            return {"locale": locale.value}
    """
    # 1. Check query parameter
    lang_param = request.query_params.get("lang")
    if lang_param:
        normalized = normalize_locale_code(lang_param)
        try:
            return SupportedLocale(normalized)
        except ValueError:
            pass  # Invalid locale, continue to next method

    # 2. Check Accept-Language header
    accept_language = request.headers.get("Accept-Language")
    if accept_language:
        preferred_locales = parse_accept_language(accept_language)
        if preferred_locales:
            return find_best_locale(preferred_locales, default)

    # 3. Return default
    return default


def get_locale_from_state(
    request: Request,
    default: SupportedLocale = SupportedLocale.ENGLISH,
) -> SupportedLocale:
    """Get locale from request state (set by middleware).

    Args:
        request: FastAPI Request object.
        default: Default locale if not set in state.

    Returns:
        SupportedLocale from request state or default.
    """
    return getattr(request.state, "locale", default)
