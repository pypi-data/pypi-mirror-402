/**
 * Intlayer locale configuration
 *
 * Centralized configuration for supported locales and related settings.
 * This file serves as the single source of truth for locale-related constants.
 *
 * Built-in languages: English (en), Korean (ko)
 * Additional languages can be added via AI translation CLI (see docs/internationalization.md)
 */
import { Locales } from 'intlayer'

/**
 * Built-in supported locales (2 languages with complete translations)
 * Additional languages require AI translation via `truthound translate` CLI
 */
export const SUPPORTED_LOCALES = [
  Locales.ENGLISH,
  Locales.KOREAN,
] as const

export type SupportedLocale = (typeof SUPPORTED_LOCALES)[number]

/**
 * Default locale when no preference is detected
 */
export const DEFAULT_LOCALE: SupportedLocale = Locales.ENGLISH

/**
 * Storage key for persisting locale preference
 */
export const LOCALE_STORAGE_KEY = 'truthound-locale'

/**
 * Locale metadata for UI display
 */
export interface LocaleInfo {
  code: SupportedLocale
  name: string
  nativeName: string
  flag: string
  rtl?: boolean
}

/**
 * Available locales with display information (2 built-in languages)
 * Used for language selector UI components
 *
 * Note: Additional languages can be added by:
 * 1. Running `truthound translate -l <locale> -p <provider>`
 * 2. Updating this array with the new locale info
 */
export const LOCALE_INFO: readonly LocaleInfo[] = [
  {
    code: Locales.ENGLISH,
    name: 'English',
    nativeName: 'English',
    flag: '🇺🇸',
  },
  {
    code: Locales.KOREAN,
    name: 'Korean',
    nativeName: '한국어',
    flag: '🇰🇷',
  },
] as const

/**
 * RTL (Right-to-Left) locales
 * Currently no RTL languages are built-in (Arabic requires AI translation)
 */
export const RTL_LOCALES: readonly SupportedLocale[] = []

/**
 * Check if a locale uses RTL direction
 */
export function isRtlLocale(locale: SupportedLocale): boolean {
  return RTL_LOCALES.includes(locale)
}

/**
 * Get locale info by code
 */
export function getLocaleInfo(locale: SupportedLocale): LocaleInfo | undefined {
  return LOCALE_INFO.find((info) => info.code === locale)
}

/**
 * Check if a locale is supported
 */
export function isSupportedLocale(locale: string): locale is SupportedLocale {
  return SUPPORTED_LOCALES.includes(locale as SupportedLocale)
}

/**
 * Get browser's preferred locale if supported, otherwise return default
 */
export function getBrowserLocale(): SupportedLocale {
  if (typeof navigator === 'undefined') {
    return DEFAULT_LOCALE
  }

  // Check navigator.languages first (preferred)
  const browserLocales = navigator.languages || [navigator.language]

  for (const browserLocale of browserLocales) {
    // Extract language code (e.g., 'en-US' -> 'en')
    const langCode = browserLocale.split('-')[0].toLowerCase()

    // Map language codes to supported locales (only built-in languages)
    const localeMap: Record<string, SupportedLocale> = {
      en: Locales.ENGLISH,
      ko: Locales.KOREAN,
    }

    if (langCode in localeMap) {
      return localeMap[langCode]
    }
  }

  return DEFAULT_LOCALE
}
