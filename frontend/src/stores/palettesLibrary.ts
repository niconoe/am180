/**
 * Library of palette presets and user-saved palettes.
 *
 * Presets are hardcoded and read-only.
 * Saved palettes are persisted to localStorage (per-browser).
 */
import { ref, watch } from 'vue'
import { defineStore } from 'pinia'
import type { HexColor, Preset, SavedPalette } from '@/types/palette'

const STORAGE_KEY = 'am180.palettes.saved.v1'

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

function loadSaved(): SavedPalette[] {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    if (!raw) return []
    const parsed = JSON.parse(raw)
    if (!Array.isArray(parsed)) return []
    return parsed
  } catch (e) {
    console.warn('Failed to load saved palettes from localStorage:', e)
    return []
  }
}

function persistSaved(saved: SavedPalette[]): void {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(saved))
  } catch (e) {
    console.warn('Failed to persist saved palettes:', e)
  }
}

function newId(): string {
  // crypto.randomUUID is available in modern browsers; fall back to a
  // timestamp+random string if not.
  if (typeof crypto !== 'undefined' && 'randomUUID' in crypto) {
    return crypto.randomUUID()
  }
  return `${Date.now()}-${Math.random().toString(36).slice(2, 10)}`
}

export const usePalettesLibrary = defineStore('palettesLibrary', () => {
  const presets = ref<Preset[]>(SEED_PRESETS)
  const saved = ref<SavedPalette[]>(loadSaved())

  // UI state: which saved palette is currently being edited, if any.
  // The editor dialog mounts once at app root and opens when this is set.
  const editingId = ref<string | null>(null)
  // True when the palette being edited was just created by the editor flow
  // (New blank). Cancel deletes such palettes instead of just discarding
  // draft edits.
  const editingIsNew = ref(false)
  // Counter bumped whenever the editor closes (Save or Cancel) and wants
  // the opener (the palette picker) to reopen. Currently assumes a single
  // PaletteField - if multiple are added, this needs to track which field
  // should reopen.
  const reopenPickerSignal = ref(0)

  watch(saved, (value) => persistSaved(value), { deep: true })

  function findPreset(id: string | undefined): Preset | undefined {
    if (!id) return undefined
    return presets.value.find((p) => p.id === id)
  }

  function findSaved(id: string): SavedPalette | undefined {
    return saved.value.find((p) => p.id === id)
  }

  function nextAutoName(): string {
    let max = 0
    for (const p of saved.value) {
      const m = p.name.match(/^Palette (\d+)$/)
      if (m) {
        const n = parseInt(m[1]!, 10)
        if (n > max) max = n
      }
    }
    return `Palette ${max + 1}`
  }

  function createBlank(size: number): SavedPalette {
    const now = Date.now()
    const colors: HexColor[] = Array(Math.max(1, size)).fill('#000000')
    const palette: SavedPalette = {
      id: newId(),
      name: nextAutoName(),
      colors,
      createdAt: now,
      updatedAt: now,
    }
    saved.value = [...saved.value, palette]
    return palette
  }

  function clonePreset(preset: Preset): SavedPalette {
    const now = Date.now()
    const palette: SavedPalette = {
      id: newId(),
      name: nextAutoName(),
      colors: preset.colors.slice(),
      createdAt: now,
      updatedAt: now,
    }
    saved.value = [...saved.value, palette]
    return palette
  }

  function cloneSaved(id: string): SavedPalette | undefined {
    const source = findSaved(id)
    if (!source) return undefined
    const now = Date.now()
    const palette: SavedPalette = {
      id: newId(),
      name: nextAutoName(),
      colors: source.colors.slice(),
      createdAt: now,
      updatedAt: now,
    }
    saved.value = [...saved.value, palette]
    return palette
  }

  function deleteSaved(id: string): void {
    saved.value = saved.value.filter((p) => p.id !== id)
  }

  function rename(id: string, name: string): void {
    const trimmed = name.trim()
    if (!trimmed) return
    saved.value = saved.value.map((p) =>
      p.id === id ? { ...p, name: trimmed, updatedAt: Date.now() } : p,
    )
  }

  function updateColors(id: string, colors: HexColor[]): void {
    saved.value = saved.value.map((p) =>
      p.id === id ? { ...p, colors: colors.slice(), updatedAt: Date.now() } : p,
    )
  }

  function openEditor(id: string, isNew = false): void {
    editingId.value = id
    editingIsNew.value = isNew
  }

  function saveEdit(name: string, colors: HexColor[]): void {
    if (!editingId.value) return
    rename(editingId.value, name)
    updateColors(editingId.value, colors)
    editingId.value = null
    editingIsNew.value = false
    reopenPickerSignal.value++
  }

  function cancelEdit(): void {
    if (!editingId.value) return
    if (editingIsNew.value) {
      deleteSaved(editingId.value)
    }
    editingId.value = null
    editingIsNew.value = false
    reopenPickerSignal.value++
  }

  return {
    presets,
    saved,
    editingId,
    editingIsNew,
    reopenPickerSignal,
    findPreset,
    findSaved,
    createBlank,
    clonePreset,
    cloneSaved,
    deleteSaved,
    rename,
    updateColors,
    openEditor,
    saveEdit,
    cancelEdit,
  }
})
