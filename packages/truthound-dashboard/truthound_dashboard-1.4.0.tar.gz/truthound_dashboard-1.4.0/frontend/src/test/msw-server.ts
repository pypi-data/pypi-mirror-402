/**
 * MSW Server Setup for Tests
 *
 * Provides a configurable MSW server for tests that need API mocking.
 * Tests can import and use this to mock API responses.
 */

import { setupServer, SetupServerApi } from 'msw/node'
import { handlers } from '@/mocks/handlers'

// Create the server instance
let server: SetupServerApi | null = null

/**
 * Setup and get the MSW server instance
 *
 * @example
 * ```ts
 * import { setupMswServer } from '@/test/msw-server'
 *
 * const server = setupMswServer()
 *
 * beforeAll(() => server.listen())
 * afterEach(() => server.resetHandlers())
 * afterAll(() => server.close())
 * ```
 */
export function setupMswServer(): SetupServerApi {
  if (!server) {
    server = setupServer(...handlers)
  }
  return server
}

/**
 * Get the MSW server instance (creates if not exists)
 */
export function getMswServer(): SetupServerApi {
  return setupMswServer()
}

/**
 * Reset the MSW server (useful for test isolation)
 */
export function resetMswServer(): void {
  if (server) {
    server.resetHandlers()
  }
}

/**
 * Close the MSW server
 */
export function closeMswServer(): void {
  if (server) {
    server.close()
    server = null
  }
}

export { server }
