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

// PrimeVue Slider breaks with very small float ranges (e.g. 0.0001-0.01).
// Workaround: map the slider to integer steps (0..N) and convert back to the
// real float value. The InputNumber keeps the original range for fine control.
const sliderSteps = computed(() => {
  if (props.spec.min !== undefined && props.spec.max !== undefined && props.spec.step) {
    return Math.round((props.spec.max - props.spec.min) / props.spec.step)
  }
  return 100
})

const sliderIntValue = computed({
  get: () => {
    if (props.spec.min !== undefined && props.spec.step) {
      return Math.round((Number(props.modelValue) - props.spec.min) / props.spec.step)
    }
    return Number(props.modelValue)
  },
  set: (v: number | number[]) => {
    const raw = Array.isArray(v) ? (v[0] ?? 0) : v
    if (props.spec.min !== undefined && props.spec.step) {
      emit('update:modelValue', props.spec.min + raw * props.spec.step)
    } else {
      emit('update:modelValue', raw)
    }
  },
})

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
          v-model="sliderIntValue"
          :min="0"
          :max="sliderSteps"
          :step="1"
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
