/// <reference types="vitest" />
import { defineConfig } from 'vitest/config'
import react from '@vitejs/plugin-react'
import path from 'path'

export default defineConfig({
  plugins: [react()],
  test: {
    // Test environment
    environment: 'jsdom',

    // Setup files run before each test file
    setupFiles: ['./src/test/setup.ts'],

    // Global test utilities (describe, it, expect, etc.)
    globals: true,

    // Include patterns
    include: ['src/**/*.{test,spec}.{ts,tsx}'],

    // Exclude patterns
    exclude: ['node_modules', 'dist', '.idea', '.git', '.cache'],

    // Coverage configuration
    coverage: {
      provider: 'v8',
      reporter: ['text', 'json', 'html', 'lcov'],
      reportsDirectory: './coverage',
      include: ['src/**/*.{ts,tsx}'],
      exclude: [
        'src/test/**',
        'src/mocks/**',
        'src/**/*.d.ts',
        'src/main.tsx',
        'src/vite-env.d.ts',
        'src/content/**', // i18n content files
        '**/*.config.{ts,js}',
      ],
      thresholds: {
        // Recommended starting thresholds
        lines: 50,
        functions: 50,
        branches: 50,
        statements: 50,
      },
    },

    // Test timeout
    testTimeout: 10000,

    // Hook timeout
    hookTimeout: 10000,

    // Reporter configuration
    reporters: ['verbose'],

    // CSS handling
    css: {
      modules: {
        classNameStrategy: 'non-scoped',
      },
    },

    // Mock reset behavior
    mockReset: true,
    restoreMocks: true,

    // Path aliases for test environment
    alias: {
      // Replace all intlayer-related modules with mocks to avoid esbuild issues
      'react-intlayer': path.resolve(__dirname, './src/test/mocks/react-intlayer.ts'),
      intlayer: path.resolve(__dirname, './src/test/mocks/intlayer.ts'),
      '@intlayer/config': path.resolve(__dirname, './src/test/mocks/intlayer-config.ts'),
    },

    // Pool configuration - use threads for better isolation between test files
    pool: 'threads',
    poolOptions: {
      threads: {
        singleThread: false,
        isolate: true,
      },
    },

    // Sequence configuration
    sequence: {
      shuffle: false,
    },
  },

  // Path aliases matching vite.config.ts
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
})
