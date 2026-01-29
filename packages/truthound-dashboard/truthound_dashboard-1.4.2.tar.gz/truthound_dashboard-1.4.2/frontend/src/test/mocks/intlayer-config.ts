/**
 * Mock for @intlayer/config module
 * Avoids esbuild issues in test environment
 */

export const getConfiguration = () => ({
  internationalization: {
    locales: ['en', 'ko'],
    defaultLocale: 'en',
  },
  content: {
    baseDir: './src',
    contentDirName: 'content',
  },
})

export default {
  getConfiguration,
}
