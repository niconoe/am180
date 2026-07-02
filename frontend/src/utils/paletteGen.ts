/**
 * Procedural palette generation.
 *
 * Given a mode, current colors, and a per-slot lock mask, produce a new
 * list of colors. Locked slots are preserved; unlocked slots are rewritten.
 *
 * If any slot is locked, its hue seeds the generation (so the new palette
 * harmonizes with the anchor). Otherwise a random anchor hue is chosen.
 */
import type { GenerationMode, HexColor } from '@/types/palette'
import { normalizeHex } from './palette'

type HSL = [number, number, number]

function clamp01(v: number): number {
  return Math.max(0, Math.min(1, v))
}

function hexToRgb(hex: string): [number, number, number] {
  const h = normalizeHex(hex).slice(1)
  const r = parseInt(h.slice(0, 2), 16) / 255
  const g = parseInt(h.slice(2, 4), 16) / 255
  const b = parseInt(h.slice(4, 6), 16) / 255
  return [r, g, b]
}

function rgbToHex(r: number, g: number, b: number): HexColor {
  const toByte = (v: number) =>
    Math.round(clamp01(v) * 255)
      .toString(16)
      .padStart(2, '0')
  return `#${toByte(r)}${toByte(g)}${toByte(b)}`
}

export function hexToHsl(hex: string): HSL {
  const [r, g, b] = hexToRgb(hex)
  const max = Math.max(r, g, b)
  const min = Math.min(r, g, b)
  const l = (max + min) / 2
  if (max === min) return [0, 0, l]
  const d = max - min
  const s = l > 0.5 ? d / (2 - max - min) : d / (max + min)
  let h: number
  if (max === r) h = ((g - b) / d + (g < b ? 6 : 0)) * 60
  else if (max === g) h = ((b - r) / d + 2) * 60
  else h = ((r - g) / d + 4) * 60
  return [h, s, l]
}

export function hslToHex([h, s, l]: HSL): HexColor {
  const hue = ((h % 360) + 360) % 360
  const sat = clamp01(s)
  const light = clamp01(l)
  if (sat === 0) return rgbToHex(light, light, light)
  const q = light < 0.5 ? light * (1 + sat) : light + sat - light * sat
  const p = 2 * light - q
  const hk = hue / 360
  const tc = (t: number) => {
    let tt = t
    if (tt < 0) tt += 1
    if (tt > 1) tt -= 1
    if (tt < 1 / 6) return p + (q - p) * 6 * tt
    if (tt < 1 / 2) return q
    if (tt < 2 / 3) return p + (q - p) * (2 / 3 - tt) * 6
    return p
  }
  return rgbToHex(tc(hk + 1 / 3), tc(hk), tc(hk - 1 / 3))
}

function rand(min: number, max: number): number {
  return min + Math.random() * (max - min)
}

function randHue(): number {
  return Math.random() * 360
}

/** Return the hue set for a mode relative to an anchor hue. */
function modeHues(mode: GenerationMode, anchor: number): number[] {
  switch (mode) {
    case 'monochromatic':
      return [anchor]
    case 'analogous':
      return [anchor - 30, anchor - 15, anchor, anchor + 15, anchor + 30]
    case 'complementary':
      return [anchor, anchor + 180]
    case 'split-complementary':
      return [anchor, anchor + 150, anchor + 210]
    case 'triadic':
      return [anchor, anchor + 120, anchor + 240]
    case 'tetradic':
      return [anchor, anchor + 90, anchor + 180, anchor + 270]
    case 'random':
    case 'muted':
    case 'pastel':
      // Each slot gets its own hue; see slotColor below.
      return []
  }
}

/** Produce a color for one unlocked slot. */
function slotColor(
  mode: GenerationMode,
  index: number,
  total: number,
  hueSet: number[],
): HexColor {
  switch (mode) {
    case 'random': {
      return hslToHex([randHue(), rand(0.5, 0.9), rand(0.35, 0.7)])
    }
    case 'muted': {
      return hslToHex([randHue(), rand(0.15, 0.4), rand(0.3, 0.6)])
    }
    case 'pastel': {
      return hslToHex([randHue(), rand(0.3, 0.55), rand(0.75, 0.9)])
    }
    case 'monochromatic': {
      // Vary lightness across slots, small saturation jitter.
      const l = total === 1 ? 0.5 : 0.25 + (index / (total - 1)) * 0.5
      return hslToHex([hueSet[0]!, rand(0.55, 0.85), l + rand(-0.05, 0.05)])
    }
    default: {
      // analogous, complementary, split-complementary, triadic, tetradic:
      // cycle through the mode's hues, jitter S/L per slot.
      const hue = hueSet[index % hueSet.length]!
      return hslToHex([hue, rand(0.55, 0.85), rand(0.4, 0.7)])
    }
  }
}

/**
 * Generate a new palette. Locked slots (locked[i] === true) are preserved
 * exactly; unlocked slots are rewritten according to the mode. If at least
 * one slot is locked, its hue seeds the mode; otherwise a fresh random hue.
 */
export function generatePalette(
  mode: GenerationMode,
  currentColors: HexColor[],
  locked: boolean[],
): HexColor[] {
  const firstLockedIdx = locked.findIndex((v) => v)
  const anchor =
    firstLockedIdx >= 0 ? hexToHsl(currentColors[firstLockedIdx]!)[0] : randHue()
  const hueSet = modeHues(mode, anchor)
  const out = currentColors.slice()
  for (let i = 0; i < out.length; i++) {
    if (locked[i]) continue
    out[i] = slotColor(mode, i, out.length, hueSet)
  }
  return out
}
