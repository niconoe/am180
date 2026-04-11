/**
 * Describes one UI control for a generator parameter.
 * Sent by GET /api/generators/{id}/schema.
 */
export interface ParamSpec {
  id: string
  label: string
  type: 'float' | 'int' | 'color' | 'select'
  min?: number
  max?: number
  step?: number
  default?: number | string
  group?: string
  options?: { value: string; label: string }[]
}

/** Summary of a generator, from GET /api/generators. */
export interface GeneratorInfo {
  id: string
  name: string
  description: string
}

/** Full schema for one generator, from GET /api/generators/{id}/schema. */
export interface GeneratorSchema {
  id: string
  name: string
  params: ParamSpec[]
}

/** Request body for POST /api/preview and POST /api/render. */
export interface RenderRequest {
  generator: string
  params: Record<string, number | string>
  seed: number
}
