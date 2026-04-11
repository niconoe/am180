<script setup lang="ts">
import type { ParamSpec } from '@/types/schema'
import Slider from 'primevue/slider'
import InputNumber from 'primevue/inputnumber'
import ColorPicker from 'primevue/colorpicker'
import Select from 'primevue/select'
import { computed } from 'vue'

const props = defineProps<{
  spec: ParamSpec
  modelValue: number | string
}>()

const emit = defineEmits<{
  'update:modelValue': [value: number | string]
}>()

// PrimeVue ColorPicker uses hex WITHOUT '#', our store uses WITH '#'
const colorValue = computed({
  get: () => String(props.modelValue).replace('#', ''),
  set: (v: string) => emit('update:modelValue', `#${v}`),
})
</script>

<template>
  <div class="param-control">
    <label>{{ spec.label }}</label>

    <template v-if="spec.type === 'float' || spec.type === 'int'">
      <div style="display: flex; align-items: center; gap: 0.75rem">
        <Slider
          :modelValue="Number(modelValue)"
          @update:modelValue="emit('update:modelValue', Array.isArray($event) ? ($event[0] ?? 0) : $event)"
          :min="spec.min"
          :max="spec.max"
          :step="spec.step"
          style="flex: 1"
        />
        <InputNumber
          :modelValue="Number(modelValue)"
          @update:modelValue="emit('update:modelValue', $event ?? spec.default ?? 0)"
          :min="spec.min"
          :max="spec.max"
          :step="spec.step"
          :minFractionDigits="spec.type === 'float' ? 1 : 0"
          :maxFractionDigits="spec.type === 'float' ? 4 : 0"
          style="width: 6rem"
        />
      </div>
    </template>

    <ColorPicker
      v-else-if="spec.type === 'color'"
      v-model="colorValue"
    />

    <Select
      v-else-if="spec.type === 'select'"
      :modelValue="modelValue"
      @update:modelValue="emit('update:modelValue', $event)"
      :options="spec.options"
      optionLabel="label"
      optionValue="value"
      style="width: 100%"
    />
  </div>
</template>

<style scoped>
.param-control {
  margin-bottom: 1rem;
}
.param-control label {
  display: block;
  margin-bottom: 0.25rem;
  font-size: 0.875rem;
  color: var(--p-text-muted-color);
}
</style>
