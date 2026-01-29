/**
 * Mock for intlayer module
 * Provides mock implementations for Locales and t function
 */

export const Locales = {
  ENGLISH: 'en',
  KOREAN: 'ko',
} as const

export type LocaleType = (typeof Locales)[keyof typeof Locales]

/**
 * Mock t function - returns English translation by default
 */
export function t(translations: Record<string, string>): string {
  return translations.en || Object.values(translations)[0] || ''
}

/**
 * Mock Dictionary type
 */
export interface Dictionary {
  key: string
  content: Record<string, unknown>
}

export default {
  Locales,
  t,
}
