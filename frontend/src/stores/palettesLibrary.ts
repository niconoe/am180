/**
 * Library of palette presets and recently-edited palettes.
 *
 * Phase 1: presets (hardcoded seed) + recent (in-memory only, capped).
 * Phase 2 will add `saved` (user library, persisted to localStorage).
 */
import { ref } from 'vue'
import { defineStore } from 'pinia'
import type { Preset, RecentPalette } from '@/types/palette'

const RECENT_CAP = 10

const SEED_PRESETS: Preset[] = [
  {
    id: 'warm',
    name: 'Warm',
    colors: ['#ff6b35', '#f7931e', '#fcbf49', '#f77f00', '#d62828'],
  },
  {
    id: 'cool',
    name: 'Cool',
    colors: ['#4cc9f0', '#4361ee', '#3a0ca3', '#7209b7', '#560bad'],
  },
  {
    id: 'mono',
    name: 'Mono',
    colors: ['#ffffff', '#c0c0c0', '#808080', '#d0d0d0', '#e8e8e8'],
  },
]

function colorsEqual(a: string[], b: string[]): boolean {
  if (a.length !== b.length) return false
  for (let i = 0; i < a.length; i++) if (a[i] !== b[i]) return false
  return true
}

export const usePalettesLibrary = defineStore('palettesLibrary', () => {
  const presets = ref<Preset[]>(SEED_PRESETS)
  const recent = ref<RecentPalette[]>([])

  function findPreset(id: string | undefined): Preset | undefined {
    if (!id) return undefined
    return presets.value.find((p) => p.id === id)
  }

  /**
   * Add a palette to the recent list. If colors match an existing
   * recent entry, that entry is bumped to the top instead of duplicated.
   * The list is capped at RECENT_CAP entries.
   */
  function addRecent(palette: RecentPalette): void {
    const existingIdx = recent.value.findIndex((r) =>
      colorsEqual(r.colors, palette.colors),
    )
    if (existingIdx >= 0) {
      const [existing] = recent.value.splice(existingIdx, 1)
      recent.value.unshift({ ...existing!, createdAt: palette.createdAt })
    } else {
      recent.value.unshift(palette)
      if (recent.value.length > RECENT_CAP) {
        recent.value.length = RECENT_CAP
      }
    }
  }

  return { presets, recent, findPreset, addRecent }
})
