<script setup lang="ts">
import type { GeneratorInfo } from '@/types/schema'
import Select from 'primevue/select'

defineProps<{
  generators: GeneratorInfo[]
  modelValue: string
}>()

const emit = defineEmits<{
  'update:modelValue': [value: string]
}>()
</script>

<template>
  <Select
    :modelValue="modelValue"
    @update:modelValue="emit('update:modelValue', $event)"
    :options="generators"
    optionLabel="name"
    optionValue="id"
    placeholder="Select a generator"
    style="width: 100%"
  />
</template>
