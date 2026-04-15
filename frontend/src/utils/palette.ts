/**
 * Pure helpers for palette manipulation. No Vue or store deps.
 */
import type { HexColor } from '@/types/palette'

/** Split a comma-separated hex string into normalized HexColor[]. */
export function parsePaletteString(value: string): HexColor[] {
  if (!value) return []
  return value
    .split(',')
    .map((s) => s.trim())
    .filter((s) => s.length > 0)
    .map(normalizeHex)
}

/** Join HexColor[] into a comma-separated string (no spaces). */
export function formatPaletteString(colors: HexColor[]): string {
  return colors.join(',')
}

/**
 * Normalize a hex string to lowercase '#rrggbb'.
 * Accepts '#rgb', 'rgb', '#rrggbb', 'rrggbb' (case-insensitive).
 * Returns '#000000' for unrecognized input - callers should validate
 * upstream when correctness matters.
 */
export function normalizeHex(raw: string): HexColor {
  let s = raw.trim().toLowerCase()
  if (s.startsWith('#')) s = s.slice(1)
  if (/^[0-9a-f]{3}$/.test(s)) {
    s = s.split('').map((c) => c + c).join('')
  }
  if (!/^[0-9a-f]{6}$/.test(s)) return '#000000'
  return `#${s}`
}

/**
 * Resize a color array to `size` slots.
 * - If source is empty: returns ['#000000'] repeated `size` times.
 * - If source.length === size: direct copy.
 * - If source.length > size: take first `size`.
 * - If source.length < size: cycle through source to fill `size` slots.
 *   Matches the backend's behavior of cycling colors through particles.
 */
export function resizeColors(source: HexColor[], size: number): HexColor[] {
  if (size <= 0) return []
  if (source.length === 0) return Array(size).fill('#000000')
  if (source.length === size) return source.slice()
  if (source.length > size) return source.slice(0, size)
  const out: HexColor[] = []
  for (let i = 0; i < size; i++) out.push(source[i % source.length]!)
  return out
}
