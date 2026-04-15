<script setup lang="ts">
import { computed, ref } from 'vue'
import type { ParamSpec } from '@/types/schema'
import { parsePaletteString, resizeColors } from '@/utils/palette'
import PalettePicker from './PalettePicker.vue'

const props = defineProps<{
  spec: ParamSpec
  modelValue: string
}>()

const emit = defineEmits<{
  'update:modelValue': [value: string]
}>()

const open = ref(false)
const size = computed(() => props.spec.size ?? 5)
const swatches = computed(() =>
  resizeColors(parsePaletteString(props.modelValue), size.value),
)

function onSelect(commaString: string) {
  emit('update:modelValue', commaString)
}
</script>

<template>
  <div>
    <button class="palette-field" type="button" @click="open = true">
      <span
        v-for="(c, i) in swatches"
        :key="i"
        class="swatch"
        :style="{ background: c }"
      />
    </button>
    <PalettePicker
      v-model:visible="open"
      :targetSize="size"
      @select="onSelect"
    />
  </div>
</template>

<style scoped>
.palette-field {
  display: flex;
  gap: 3px;
  padding: 4px;
  background: var(--p-surface-50);
  border: 1px solid var(--p-surface-200);
  border-radius: 4px;
  cursor: pointer;
  width: 100%;
}
.palette-field:hover {
  border-color: var(--p-primary-color);
}
.swatch {
  flex: 1;
  height: 24px;
  border-radius: 3px;
  border: 1px solid var(--p-surface-300);
}
</style>
