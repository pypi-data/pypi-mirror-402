/**
 * Safe Intlayer hook with English fallback support
 *
 * This hook wraps react-intlayer's useIntlayer and provides fallback values
 * when Intlayer fails to load dictionaries at runtime (e.g., in Vercel deployments).
 *
 * Usage:
 *   import { useSafeIntlayer } from '@/hooks/useSafeIntlayer'
 *   const common = useSafeIntlayer('common')
 */

import { useMemo } from 'react'
import { useIntlayer as useIntlayerOriginal } from 'react-intlayer'
import { fallbacks } from '@/lib/intlayer-fallbacks'

// Store whether we've already logged the fallback warning
let fallbackWarningShown = false

/**
 * Check if Intlayer content is valid (not empty/broken)
 * Returns true if the content has at least one valid property
 */
function isIntlayerContentValid(content: unknown): boolean {
  if (!content || typeof content !== 'object') {
    return false
  }

  const obj = content as Record<string, unknown>
  // Check if at least one property exists and has a value
  for (const key of Object.keys(obj)) {
    const value = obj[key]
    if (value !== undefined && value !== null) {
      return true
    }
  }
  return false
}

// Type alias for Intlayer dictionary keys from the registry
type IntlayerKey = Parameters<typeof useIntlayerOriginal>[0]

/**
 * Safe Intlayer hook that falls back to English defaults when
 * Intlayer fails to load dictionaries.
 *
 * @param key - The dictionary key
 * @returns Dictionary content with Intlayer types preserved
 */
export function useSafeIntlayer<K extends IntlayerKey>(
  key: K
): ReturnType<typeof useIntlayerOriginal<K>> {
  // Always try to get content from Intlayer first
  let intlayerContent: ReturnType<typeof useIntlayerOriginal<K>> | undefined
  let intlayerFailed = false

  try {
    intlayerContent = useIntlayerOriginal(key)
  } catch (error) {
    intlayerFailed = true
    if (!fallbackWarningShown) {
      console.warn('[useSafeIntlayer] Intlayer failed, using fallbacks:', error)
      fallbackWarningShown = true
    }
  }

  // Get fallback content if available
  const fallbackContent = fallbacks[key as keyof typeof fallbacks]

  // Determine which content to use
  return useMemo(() => {
    // If Intlayer loaded successfully and has valid content, use it
    if (!intlayerFailed && isIntlayerContentValid(intlayerContent)) {
      return intlayerContent as ReturnType<typeof useIntlayerOriginal<K>>
    }

    // Otherwise use fallback - cast to match Intlayer's expected return type
    // This works because fallback strings render identically to IntlayerNode in JSX
    if (fallbackContent) {
      return fallbackContent as unknown as ReturnType<typeof useIntlayerOriginal<K>>
    }

    // If no fallback available, return whatever Intlayer gave us (may be empty)
    return intlayerContent as ReturnType<typeof useIntlayerOriginal<K>>
  }, [intlayerFailed, intlayerContent, fallbackContent])
}

/**
 * Re-export useLocale for convenience
 */
export { useLocale } from 'react-intlayer'
