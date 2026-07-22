import { beforeEach, describe, expect, it, vi } from 'vitest'
import { createPinia, setActivePinia } from 'pinia'
import { useGenartStore } from '@/stores/genart'
import { parsePaletteString } from '@/utils/palette'
import type { ParamSpec } from '@/types/schema'

// palettesLibrary reads localStorage at store init; provide an in-memory
// stub since these tests run in plain Node.
vi.stubGlobal('localStorage', {
  getItem: () => null,
  setItem: () => {},
})

// Minimal schema mirroring the real generators: a color param declared
// BEFORE the palette param, as in the backend schemas. Order matters -
// the paper color must come from the palette even though the palette
// slot is resolved later in the schema list.
const SCHEMA: ParamSpec[] = [
  { id: 'background', label: 'Paper', type: 'color', default: '#f2e8d5' },
  {
    id: 'colors',
    label: 'Palette',
    type: 'palette',
    size: 5,
    default_preset: 'sepia',
  },
]

const HEX_RE = /^#[0-9a-f]{6}$/

describe('randomizeAll paper-from-palette', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
  })

  it('defaults paperFromPalette to true', () => {
    const store = useGenartStore()
    expect(store.paperFromPalette).toBe(true)
  })

  it('picks color params from the chosen palette when enabled', () => {
    const store = useGenartStore()
    store.schema = SCHEMA
    // Randomization is non-deterministic; repeat to cover many draws.
    for (let i = 0; i < 20; i++) {
      store.randomizeAll()
      const palette = parsePaletteString(store.params.colors as string)
      expect(palette).toContain(store.params.background)
    }
  })

  it('keeps random color params when disabled', () => {
    const store = useGenartStore()
    store.schema = SCHEMA
    store.paperFromPalette = false
    store.randomizeAll()
    expect(store.params.background).toMatch(HEX_RE)
  })

  it('falls back to a random color when the schema has no palette', () => {
    const store = useGenartStore()
    store.schema = [SCHEMA[0]!]
    store.randomizeAll()
    expect(store.params.background).toMatch(HEX_RE)
  })
})
