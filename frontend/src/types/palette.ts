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

/** Generation modes for the procedural generator (phase 3). */
export type GenerationMode =
  | 'monochromatic'
  | 'analogous'
  | 'complementary'
  | 'triadic'
