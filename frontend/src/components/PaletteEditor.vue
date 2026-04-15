<script setup lang="ts">
import Dialog from 'primevue/dialog'
import ColorPicker from 'primevue/colorpicker'
import Button from 'primevue/button'
import { computed, watch } from 'vue'
import { usePaletteEditor } from '@/composables/usePaletteEditor'
import { usePalettesLibrary } from '@/stores/palettesLibrary'
import { formatPaletteString } from '@/utils/palette'
import type { Preset } from '@/types/palette'

const EDITOR_SIZE = 5

const props = defineProps<{ visible: boolean }>()

const emit = defineEmits<{ 'update:visible': [value: boolean] }>()

const library = usePalettesLibrary()
const initialValue = computed(() => {
  const first = library.presets[0]
  return first ? formatPaletteString(first.colors) : ''
})

const editor = usePaletteEditor(initialValue.value, EDITOR_SIZE)
let valueAtOpen = editor.toCommaString()

watch(
  () => props.visible,
  (now, prev) => {
    if (now && !prev) {
      valueAtOpen = editor.toCommaString()
    }
    if (!now && prev) {
      const current = editor.toCommaString()
      if (current !== valueAtOpen) {
        library.addRecent({
          colors: editor.slots.value.slice(),
          createdAt: Date.now(),
        })
      }
    }
  },
)

const slotPickerValues = computed(() =>
  editor.slots.value.map((c) => c.replace('#', '')),
)

function onSlotChange(index: number, raw: string | { hex?: string } | null) {
  // PrimeVue ColorPicker emits the hex without '#', or sometimes an
  // object depending on format. Normalize to the string form.
  const hex = typeof raw === 'string' ? raw : raw?.hex ?? ''
  if (!hex) return
  editor.setSlot(index, `#${hex}`)
}

function loadPreset(p: Preset) {
  editor.applyPreset(p)
}
</script>

<template>
  <Dialog
    :visible="visible"
    @update:visible="emit('update:visible', $event)"
    modal
    header="Palette editor"
    :style="{ width: '480px' }"
  >
    <section class="editor-section">
      <h4>Slots</h4>
      <div class="slot-row">
        <div v-for="(c, i) in editor.slots.value" :key="i" class="slot">
          <ColorPicker
            :modelValue="slotPickerValues[i]"
            @update:modelValue="onSlotChange(i, $event)"
          />
        </div>
      </div>
    </section>

    <section class="editor-section">
      <h4>Load preset</h4>
      <div class="preset-row">
        <Button
          v-for="p in library.presets"
          :key="p.id"
          :label="p.name"
          severity="secondary"
          size="small"
          @click="loadPreset(p)"
        />
      </div>
    </section>
  </Dialog>
</template>

<style scoped>
.editor-section {
  margin-bottom: 1rem;
}
.editor-section h4 {
  font-size: 0.7rem;
  font-weight: 600;
  letter-spacing: 0.05em;
  text-transform: uppercase;
  color: var(--p-text-muted-color);
  margin: 0 0 0.5rem;
}
.slot-row {
  display: flex;
  gap: 0.5rem;
}
.slot {
  flex: 0 0 auto;
}
.preset-row {
  display: flex;
  gap: 0.5rem;
  flex-wrap: wrap;
}
</style>
