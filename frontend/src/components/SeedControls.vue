<script setup lang="ts">
import InputNumber from 'primevue/inputnumber'
import Button from 'primevue/button'

defineProps<{
  modelValue: number
}>()

const emit = defineEmits<{
  'update:modelValue': [value: number]
  randomize: []
}>()
</script>

<template>
  <div class="seed-controls">
    <label>Seed</label>
    <div style="display: flex; gap: 0.5rem; align-items: center">
      <InputNumber
        :modelValue="modelValue"
        @update:modelValue="emit('update:modelValue', $event ?? 0)"
        :useGrouping="false"
        style="flex: 1"
      />
      <Button
        label="Randomize"
        severity="secondary"
        size="small"
        @click="emit('randomize')"
      />
    </div>
  </div>
</template>

<style scoped>
.seed-controls label {
  display: block;
  margin-bottom: 0.25rem;
  font-size: 0.875rem;
  color: var(--p-text-muted-color);
}
</style>
