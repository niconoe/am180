<script setup lang="ts">
import type { ParamSpec } from '@/types/schema'
import ParamControl from './ParamControl.vue'
import { computed } from 'vue'

const props = defineProps<{
  schema: ParamSpec[]
  modelValue: Record<string, number | string>
}>()

const emit = defineEmits<{
  'update:modelValue': [value: Record<string, number | string>]
}>()

const groupedParams = computed(() => {
  const groups: { name: string; params: ParamSpec[] }[] = []
  const seen = new Map<string, ParamSpec[]>()
  for (const spec of props.schema) {
    const name = spec.group ?? 'general'
    if (!seen.has(name)) {
      const params: ParamSpec[] = []
      seen.set(name, params)
      groups.push({ name, params })
    }
    seen.get(name)!.push(spec)
  }
  return groups
})

function onParamUpdate(id: string, value: number | string) {
  emit('update:modelValue', { ...props.modelValue, [id]: value })
}
</script>

<template>
  <div class="param-form">
    <div v-for="group in groupedParams" :key="group.name" class="param-group">
      <h3>{{ group.name }}</h3>
      <ParamControl
        v-for="spec in group.params"
        :key="spec.id"
        :spec="spec"
        :modelValue="modelValue[spec.id] ?? spec.default ?? ''"
        @update:modelValue="onParamUpdate(spec.id, $event)"
      />
    </div>
  </div>
</template>

<style scoped>
.param-group h3 {
  font-size: 0.75rem;
  font-weight: 600;
  letter-spacing: 0.05em;
  text-transform: uppercase;
  color: var(--p-text-muted-color);
  margin: 1.25rem 0 0.5rem;
  border-bottom: 1px solid var(--p-surface-200);
  padding-bottom: 0.25rem;
}
.param-group:first-child h3 {
  margin-top: 0;
}
</style>
