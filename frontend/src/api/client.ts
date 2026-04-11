/**
 * Typed API client for the am180 backend.
 *
 * All functions use relative URLs (/api/...) so they go through the
 * Vite dev proxy in development. No CORS handling needed.
 */
import type { GeneratorInfo, GeneratorSchema, RenderRequest } from '@/types/schema'

const API_BASE = '/api'

export async function fetchGenerators(): Promise<GeneratorInfo[]> {
  const res = await fetch(`${API_BASE}/generators`)
  if (!res.ok) throw new Error(`Failed to fetch generators: ${res.status}`)
  return res.json()
}

export async function fetchSchema(generatorId: string): Promise<GeneratorSchema> {
  const res = await fetch(`${API_BASE}/generators/${generatorId}/schema`)
  if (!res.ok) throw new Error(`Failed to fetch schema: ${res.status}`)
  return res.json()
}

export async function fetchPreview(
  request: RenderRequest,
  size: number = 512,
  signal?: AbortSignal,
): Promise<Blob> {
  const res = await fetch(`${API_BASE}/preview?size=${size}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(request),
    signal,
  })
  if (!res.ok) throw new Error(`Preview failed: ${res.status}`)
  return res.blob()
}

export async function fetchRender(
  request: RenderRequest,
  size: number = 4096,
): Promise<Blob> {
  const res = await fetch(`${API_BASE}/render?size=${size}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(request),
  })
  if (!res.ok) throw new Error(`Render failed: ${res.status}`)
  return res.blob()
}
