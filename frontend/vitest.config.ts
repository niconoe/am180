import { mergeConfig, defineConfig } from 'vitest/config'
import viteConfig from './vite.config'

export default mergeConfig(
  viteConfig,
  defineConfig({
    test: {
      // Store tests run in plain Node; no DOM environment needed.
      environment: 'node',
    },
  }),
)
