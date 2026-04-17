<script setup lang="ts">
import Dialog from 'primevue/dialog'
import Button from 'primevue/button'
import { useConfirm } from 'primevue/useconfirm'
import { computed } from 'vue'
import { usePalettesLibrary } from '@/stores/palettesLibrary'
import { formatPaletteString, resizeColors } from '@/utils/palette'
import type { HexColor, Preset, SavedPalette } from '@/types/palette'

const props = defineProps<{
  visible: boolean
  targetSize: number
}>()

const emit = defineEmits<{
  'update:visible': [value: boolean]
  select: [commaString: string]
}>()

const library = usePalettesLibrary()
const confirm = useConfirm()
const presets = computed(() => library.presets)
const saved = computed(() => library.saved)

function assignColors(colors: HexColor[]) {
  emit('select', formatPaletteString(resizeColors(colors, props.targetSize)))
  emit('update:visible', false)
}

function onNewBlank() {
  const palette = library.createBlank(props.targetSize)
  library.openEditor(palette.id, true)
  emit('update:visible', false)
}

function onClonePreset(preset: Preset) {
  library.clonePreset(preset)
}

function onCloneSaved(palette: SavedPalette) {
  library.cloneSaved(palette.id)
}

function onEdit(palette: SavedPalette) {
  library.openEditor(palette.id)
  emit('update:visible', false)
}

function onDelete(palette: SavedPalette) {
  confirm.require({
    message: `Delete "${palette.name}"?`,
    header: 'Delete palette',
    icon: 'pi pi-exclamation-triangle',
    rejectLabel: 'Cancel',
    acceptLabel: 'Delete',
    acceptProps: { severity: 'danger' },
    accept: () => library.deleteSaved(palette.id),
  })
}
</script>

<template>
  <Dialog
    :visible="visible"
    @update:visible="emit('update:visible', $event)"
    modal
    header="Choose a palette"
    :style="{ width: '460px' }"
  >
    <section class="picker-section">
      <h4>Presets</h4>
      <ul class="palette-list">
        <li
          v-for="preset in presets"
          :key="preset.id"
          class="palette-row"
        >
          <button class="row-main" type="button" @click="assignColors(preset.colors)">
            <span class="name">{{ preset.name }}</span>
            <span class="swatch-strip">
              <span
                v-for="(c, i) in preset.colors"
                :key="i"
                class="swatch"
                :style="{ background: c }"
              />
            </span>
          </button>
          <div class="row-actions">
            <Button
              icon="pi pi-copy"
              severity="secondary"
              text
              size="small"
              aria-label="Clone preset"
              @click.stop="onClonePreset(preset)"
            />
          </div>
        </li>
      </ul>
    </section>

    <section class="picker-section">
      <div class="section-header">
        <h4>My palettes</h4>
        <Button
          icon="pi pi-plus"
          label="New blank"
          severity="secondary"
          size="small"
          @click="onNewBlank"
        />
      </div>
      <p v-if="saved.length === 0" class="empty">
        No saved palettes yet. Click "New blank" or clone a preset.
      </p>
      <ul v-else class="palette-list">
        <li
          v-for="palette in saved"
          :key="palette.id"
          class="palette-row"
        >
          <button class="row-main" type="button" @click="assignColors(palette.colors)">
            <span class="name">{{ palette.name }}</span>
            <span class="swatch-strip">
              <span
                v-for="(c, i) in palette.colors"
                :key="i"
                class="swatch"
                :style="{ background: c }"
              />
            </span>
          </button>
          <div class="row-actions">
            <Button
              icon="pi pi-pencil"
              severity="secondary"
              text
              size="small"
              aria-label="Edit palette"
              @click.stop="onEdit(palette)"
            />
            <Button
              icon="pi pi-copy"
              severity="secondary"
              text
              size="small"
              aria-label="Clone palette"
              @click.stop="onCloneSaved(palette)"
            />
            <Button
              icon="pi pi-trash"
              severity="danger"
              text
              size="small"
              aria-label="Delete palette"
              @click.stop="onDelete(palette)"
            />
          </div>
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
  margin: 0;
}
.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 0.5rem;
}
.empty {
  font-size: 0.8rem;
  color: var(--p-text-muted-color);
  padding: 0.5rem 0.6rem;
  margin: 0;
}
.palette-list {
  list-style: none;
  padding: 0;
  margin: 0;
}
.palette-row {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.25rem 0.25rem 0.25rem 0.6rem;
  border-radius: 4px;
}
.palette-row:hover {
  background: var(--p-surface-100);
}
.row-main {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.75rem;
  background: none;
  border: none;
  padding: 0.25rem 0;
  cursor: pointer;
  color: inherit;
  text-align: left;
  font: inherit;
}
.row-actions {
  display: flex;
  gap: 0.1rem;
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
