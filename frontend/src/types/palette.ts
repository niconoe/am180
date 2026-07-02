/**
 * Types for the palette editor system.
 *
 * Conventions:
 * - HexColor is always lowercase '#rrggbb' (7 chars).
 * - Slot count is per-palette (`colors.length`); editor rendering uses
 *   the target field's `size` and the resize-on-load rule from utils.
 */

export type HexColor = string

/** Built-in preset shipped with the app. */
export interface Preset {
  id: string
  name: string
  colors: HexColor[]
}

/** User-saved palette in the local library, persisted to localStorage. */
export interface SavedPalette {
  id: string
  name: string
  colors: HexColor[]
  createdAt: number
  updatedAt: number
}

/** Generation modes for the procedural palette generator. */
export type GenerationMode =
  | 'random'
  | 'monochromatic'
  | 'analogous'
  | 'complementary'
  | 'split-complementary'
  | 'triadic'
  | 'tetradic'
  | 'muted'
  | 'pastel'

export const GENERATION_MODES: { value: GenerationMode; label: string }[] = [
  { value: 'random', label: 'Random' },
  { value: 'monochromatic', label: 'Monochromatic' },
  { value: 'analogous', label: 'Analogous' },
  { value: 'complementary', label: 'Complementary' },
  { value: 'split-complementary', label: 'Split-complementary' },
  { value: 'triadic', label: 'Triadic' },
  { value: 'tetradic', label: 'Tetradic' },
  { value: 'muted', label: 'Muted' },
  { value: 'pastel', label: 'Pastel' },
]
