/**
 * Central state store for the generative art app.
 *
 * Holds the current generator, parameter values, seed, and preview URL.
 * All API calls go through this store. Components read state and call
 * actions - they never talk to the backend directly.
 */
import { ref } from 'vue'
import { defineStore } from 'pinia'
import type { GeneratorInfo, ParamSpec } from '@/types/schema'
import {
  fetchGenerators,
  fetchSchema,
  fetchPreview,
  fetchRender,
} from '@/api/client'
import { usePalettesLibrary } from '@/stores/palettesLibrary'
import { formatPaletteString, resizeColors } from '@/utils/palette'

export const useGenartStore = defineStore('genart', () => {
  // --- State ---
  const generators = ref<GeneratorInfo[]>([])
  const selectedGeneratorId = ref('')
  const schema = ref<ParamSpec[]>([])
  const params = ref<Record<string, number | string>>({})
  const seed = ref(Math.floor(Math.random() * 2 ** 32))
  const previewUrl = ref<string | null>(null)
  const isRendering = ref(false)

  // Abort controller for in-flight preview requests
  let abortController: AbortController | null = null

  // --- Actions ---

  async function loadGenerators() {
    generators.value = await fetchGenerators()
    if (generators.value.length > 0 && !selectedGeneratorId.value) {
      await selectGenerator(generators.value[0]!.id)
    }
  }

  async function selectGenerator(id: string) {
    selectedGeneratorId.value = id
    const genSchema = await fetchSchema(id)
    schema.value = genSchema.params
    const library = usePalettesLibrary()
    const defaults: Record<string, number | string> = {}
    for (const spec of genSchema.params) {
      if (spec.type === 'palette') {
        const size = spec.size ?? 5
        const preset = library.findPreset(spec.default_preset) ?? library.presets[0]
        if (!preset) {
          console.warn('No presets available for palette param', spec.id)
          continue
        }
        if (spec.default_preset && !library.findPreset(spec.default_preset)) {
          console.warn(
            'Unknown default_preset id, falling back to first preset:',
            spec.default_preset,
          )
        }
        defaults[spec.id] = formatPaletteString(resizeColors(preset.colors, size))
      } else if (spec.default !== undefined) {
        defaults[spec.id] = spec.default
      }
    }
    params.value = defaults
  }

  function updateParam(id: string, value: number | string) {
    params.value = { ...params.value, [id]: value }
  }

  function randomizeAll() {
    const library = usePalettesLibrary()
    const randomized: Record<string, number | string> = {}
    for (const spec of schema.value) {
      if ((spec.type === 'float' || spec.type === 'int') && spec.min !== undefined && spec.max !== undefined) {
        const val = spec.min + Math.random() * (spec.max - spec.min)
        randomized[spec.id] = spec.type === 'int' ? Math.round(val) : val
      } else if (spec.type === 'select' && spec.options && spec.options.length > 0) {
        randomized[spec.id] = spec.options[Math.floor(Math.random() * spec.options.length)]!.value
      } else if (spec.type === 'color') {
        const hex = Math.floor(Math.random() * 0xffffff).toString(16).padStart(6, '0')
        randomized[spec.id] = `#${hex}`
      } else if (spec.type === 'palette') {
        const size = spec.size ?? 5
        const pool = [...library.presets, ...library.saved]
        if (pool.length > 0) {
          const choice = pool[Math.floor(Math.random() * pool.length)]!
          randomized[spec.id] = formatPaletteString(resizeColors(choice.colors, size))
        }
      } else if (spec.default !== undefined) {
        randomized[spec.id] = spec.default
      }
    }
    params.value = randomized
    seed.value = Math.floor(Math.random() * 2 ** 32)
  }

  function randomizeSeed() {
    seed.value = Math.floor(Math.random() * 2 ** 32)
  }

  async function requestPreview() {
    if (!selectedGeneratorId.value) return

    // Abort any in-flight preview request
    if (abortController) {
      abortController.abort()
    }
    abortController = new AbortController()

    isRendering.value = true
    try {
      const blob = await fetchPreview(
        {
          generator: selectedGeneratorId.value,
          params: params.value,
          seed: seed.value,
        },
        1024,
        abortController.signal,
      )
      // Revoke old object URL to prevent memory leak
      if (previewUrl.value) {
        URL.revokeObjectURL(previewUrl.value)
      }
      previewUrl.value = URL.createObjectURL(blob)
    } catch (e: unknown) {
      if (e instanceof DOMException && e.name === 'AbortError') {
        // Superseded by a newer request - not an error
        return
      }
      console.error('Preview failed:', e)
    } finally {
      isRendering.value = false
    }
  }

  async function exportFullRes() {
    if (!selectedGeneratorId.value) return

    isRendering.value = true
    try {
      const blob = await fetchRender({
        generator: selectedGeneratorId.value,
        params: params.value,
        seed: seed.value,
      })
      // Trigger browser download via temporary anchor element
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `${selectedGeneratorId.value}-${seed.value}.png`
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      URL.revokeObjectURL(url)
    } catch (e: unknown) {
      console.error('Export failed:', e)
    } finally {
      isRendering.value = false
    }
  }

  return {
    // State
    generators,
    selectedGeneratorId,
    schema,
    params,
    seed,
    previewUrl,
    isRendering,
    // Actions
    loadGenerators,
    selectGenerator,
    updateParam,
    randomizeAll,
    randomizeSeed,
    requestPreview,
    exportFullRes,
  }
})
