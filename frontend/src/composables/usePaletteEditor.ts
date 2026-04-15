/**
 * State machine for one open palette editor instance.
 *
 * Phase 1 surface: slots, setSlot, applyPreset, toCommaString.
 * Phase 2 will add: loadFromLibrary.
 * Phase 3 will add: locks, mode, saturation, regenerateUnlocked.
 */
import { ref } from 'vue'
import type { HexColor, Preset } from '@/types/palette'
import {
  formatPaletteString,
  normalizeHex,
  parsePaletteString,
  resizeColors,
} from '@/utils/palette'

export function usePaletteEditor(initialValue: string, size: number) {
  const slots = ref<HexColor[]>(resizeColors(parsePaletteString(initialValue), size))

  function setSlot(index: number, color: HexColor): void {
    if (index < 0 || index >= slots.value.length) return
    const next = slots.value.slice()
    next[index] = normalizeHex(color)
    slots.value = next
  }

  function applyPreset(preset: Preset): void {
    slots.value = resizeColors(preset.colors, size)
  }

  function toCommaString(): string {
    return formatPaletteString(slots.value)
  }

  return { slots, setSlot, applyPreset, toCommaString }
}
