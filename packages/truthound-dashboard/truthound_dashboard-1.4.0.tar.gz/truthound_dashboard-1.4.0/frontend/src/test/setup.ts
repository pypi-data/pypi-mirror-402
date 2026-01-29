/**
 * Vitest setup file - configures testing environment
 *
 * Note: intlayer-related modules (react-intlayer, intlayer, @intlayer/config)
 * are aliased to mock files in vitest.config.ts to avoid esbuild issues.
 */

import '@testing-library/jest-dom'
import { afterEach, vi } from 'vitest'
import { cleanup } from '@testing-library/react'

// Cleanup after each test
afterEach(() => {
  cleanup()
})

// ============================================================================
// Module Mocks
// ============================================================================

// Mock @/providers module which re-exports from react-intlayer
// The actual mock implementations come from the aliased modules
vi.mock('@/providers', async () => {
  const reactIntlayer = await import('react-intlayer')
  return {
    ...reactIntlayer,
    LOCALE_INFO: [
      { code: 'en', name: 'English', nativeName: 'English', flag: '🇺🇸' },
      { code: 'ko', name: 'Korean', nativeName: '한국어', flag: '🇰🇷' },
    ],
    SUPPORTED_LOCALES: ['en', 'ko'],
    DEFAULT_LOCALE: 'en',
  }
})

// Mock @/lib/intlayer-utils
vi.mock('@/lib/intlayer-utils', () => ({
  str: (value: unknown) => (typeof value === 'string' ? value : String(value ?? '')),
}))

// Mock @/hooks/useWebSocket for components using WebSocket
vi.mock('@/hooks/useWebSocket', () => ({
  useWebSocket: () => ({
    status: 'disconnected' as const,
    isConnected: false,
    lastMessage: null,
    reconnectAttempts: 0,
    send: vi.fn(() => false),
    connect: vi.fn(),
    disconnect: vi.fn(),
    connectionInfo: {
      url: '',
      connectedAt: null,
      lastPingAt: null,
      lastPongAt: null,
    },
  }),
}))

// Mock @/hooks/use-toast
vi.mock('@/hooks/use-toast', () => ({
  useToast: () => ({
    toast: vi.fn(),
    toasts: [],
    dismiss: vi.fn(),
  }),
}))

// ============================================================================
// Browser API Mocks
// ============================================================================

// Mock window.matchMedia for components using media queries
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: (query: string) => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: vi.fn(),
    removeListener: vi.fn(),
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    dispatchEvent: vi.fn(() => false),
  }),
})

// Mock ResizeObserver for components using it
global.ResizeObserver = class ResizeObserver {
  observe() {}
  unobserve() {}
  disconnect() {}
}

// Mock IntersectionObserver for infinite scroll, lazy loading, etc.
global.IntersectionObserver = class IntersectionObserver {
  root = null
  rootMargin = ''
  thresholds: number[] = []

  constructor() {}
  observe() {}
  unobserve() {}
  disconnect() {}
  takeRecords(): IntersectionObserverEntry[] {
    return []
  }
}

// Mock window.scrollTo
window.scrollTo = vi.fn()

// Mock window.URL.createObjectURL
window.URL.createObjectURL = vi.fn(() => 'blob:mock-url')
window.URL.revokeObjectURL = vi.fn()

// Mock localStorage
const localStorageMock = {
  getItem: vi.fn(),
  setItem: vi.fn(),
  removeItem: vi.fn(),
  clear: vi.fn(),
  length: 0,
  key: vi.fn(),
}
Object.defineProperty(window, 'localStorage', { value: localStorageMock })

// Mock sessionStorage
const sessionStorageMock = {
  getItem: vi.fn(),
  setItem: vi.fn(),
  removeItem: vi.fn(),
  clear: vi.fn(),
  length: 0,
  key: vi.fn(),
}
Object.defineProperty(window, 'sessionStorage', { value: sessionStorageMock })

// ============================================================================
// MSW Server Export (for tests that need it)
// ============================================================================

// Export the MSW server setup for tests that want to use it
// Tests can import this and call server.listen() / server.close() themselves
export { setupMswServer } from './msw-server'
