/**
 * Utility functions for working with Intlayer translations.
 *
 * These helpers solve type compatibility issues between IntlayerNode
 * and components that expect plain strings (e.g., toast, aria-label).
 */
import type { ReactNode } from 'react'

/**
 * IntlayerNode is ReactNode & { value: T }.
 * This type represents the structure for type-safe extraction.
 */
type IntlayerNodeLike<T = string> = ReactNode & { value?: T }

/**
 * Extracts the string value from an IntlayerNode for use in
 * contexts that require plain strings (toast titles, aria-labels, etc.)
 *
 * @example
 * const common = useIntlayer('common')
 * toast({ title: str(common.error) })
 *
 * @param node - IntlayerNode or string value
 * @returns The underlying string value
 */
export function str(node: IntlayerNodeLike<string> | string | undefined): string {
  if (node === undefined || node === null) {
    return ''
  }
  if (typeof node === 'string') {
    return node
  }
  if (typeof node === 'number') {
    return String(node)
  }
  // IntlayerNode has a value property containing the raw string
  if (typeof node === 'object' && node !== null) {
    const obj = node as unknown as Record<string, unknown>
    // Direct value property (IntlayerNode structure)
    if ('value' in obj) {
      const value = obj.value
      if (typeof value === 'string') {
        return value
      }
      if (typeof value === 'number') {
        return String(value)
      }
    }
    // React element with props.value (IntlayerNode wrapped in JSX)
    if ('props' in obj && typeof obj.props === 'object' && obj.props !== null) {
      const props = obj.props as Record<string, unknown>
      if ('value' in props) {
        const value = props.value
        if (typeof value === 'string') {
          return value
        }
      }
      // Check for children as string
      if ('children' in props && typeof props.children === 'string') {
        return props.children
      }
    }
  }
  // Fallback: This shouldn't happen for valid IntlayerNode
  // Log warning in development for debugging
  if (import.meta.env.DEV) {
    console.warn('[intlayer-utils] str() received unexpected value:', node)
  }
  return String(node)
}

/**
 * Type assertion helper for IntlayerNode to ReactNode.
 * Use when you know the value is safe to use as ReactNode but TypeScript complains.
 *
 * @example
 * <Badge>{asNode(validation.status)}</Badge>
 */
export function asNode(node: IntlayerNodeLike | string | undefined): ReactNode {
  return node as ReactNode
}
