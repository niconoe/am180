<script setup lang="ts">
import Dialog from 'primevue/dialog'
import { computed } from 'vue'
import { usePalettesLibrary } from '@/stores/palettesLibrary'
import { formatPaletteString, resizeColors } from '@/utils/palette'
import type { HexColor } from '@/types/palette'

const props = defineProps<{
  visible: boolean
  targetSize: number
}>()

const emit = defineEmits<{
  'update:visible': [value: boolean]
  select: [commaString: string]
}>()

const library = usePalettesLibrary()
const presets = computed(() => library.presets)
const recent = computed(() => library.recent)

function pickColors(colors: HexColor[]) {
  emit('select', formatPaletteString(resizeColors(colors, props.targetSize)))
  emit('update:visible', false)
}
</script>

<template>
  <Dialog
    :visible="visible"
    @update:visible="emit('update:visible', $event)"
    modal
    header="Choose a palette"
    :style="{ width: '420px' }"
  >
    <section class="picker-section">
      <h4>Presets</h4>
      <ul class="palette-list">
        <li
          v-for="preset in presets"
          :key="preset.id"
          class="palette-row"
          @click="pickColors(preset.colors)"
        >
          <span class="name">{{ preset.name }}</span>
          <span class="swatch-strip">
            <span
              v-for="(c, i) in preset.colors"
              :key="i"
              class="swatch"
              :style="{ background: c }"
            />
          </span>
        </li>
      </ul>
    </section>

    <section v-if="recent.length > 0" class="picker-section">
      <h4>Recent</h4>
      <ul class="palette-list">
        <li
          v-for="(r, idx) in recent"
          :key="idx"
          class="palette-row"
          @click="pickColors(r.colors)"
        >
          <span class="name">Edit #{{ recent.length - idx }}</span>
          <span class="swatch-strip">
            <span
              v-for="(c, i) in r.colors"
              :key="i"
              class="swatch"
              :style="{ background: c }"
            />
          </span>
        </li>
      </ul>
    </section>
  </Dialog>
</template>

<style scoped>
.picker-section {
  margin-bottom: 1rem;
}
.picker-section h4 {
  font-size: 0.7rem;
  font-weight: 600;
  letter-spacing: 0.05em;
  text-transform: uppercase;
  color: var(--p-text-muted-color);
  margin: 0 0 0.5rem;
}
.palette-list {
  list-style: none;
  padding: 0;
  margin: 0;
}
.palette-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.5rem 0.6rem;
  border-radius: 4px;
  cursor: pointer;
  gap: 0.75rem;
}
.palette-row:hover {
  background: var(--p-surface-100);
}
.name {
  font-size: 0.85rem;
}
.swatch-strip {
  display: flex;
  gap: 2px;
}
.swatch {
  width: 18px;
  height: 18px;
  border-radius: 3px;
  border: 1px solid var(--p-surface-300);
}
</style>
