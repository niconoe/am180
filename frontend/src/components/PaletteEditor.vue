<script setup lang="ts">
import Dialog from 'primevue/dialog'
import ColorPicker from 'primevue/colorpicker'
import InputText from 'primevue/inputtext'
import Select from 'primevue/select'
import Button from 'primevue/button'
import { computed, ref, watch, onMounted, onBeforeUnmount } from 'vue'
import { usePalettesLibrary } from '@/stores/palettesLibrary'
import { normalizeHex } from '@/utils/palette'
import { generatePalette } from '@/utils/paletteGen'
import { GENERATION_MODES } from '@/types/palette'
import type { GenerationMode, HexColor } from '@/types/palette'

const library = usePalettesLibrary()

const palette = computed(() =>
  library.editingId ? library.findSaved(library.editingId) : undefined,
)

// Draft state - applied to the store only when the user clicks Save.
const nameDraft = ref('')
const colorsDraft = ref<HexColor[]>([])
// Per-slot lock mask. Resets whenever a different palette is opened.
const locked = ref<boolean[]>([])
// Generation mode. Resets to default each time the editor opens.
const mode = ref<GenerationMode>('random')

watch(
  () => library.editingId,
  (id) => {
    const p = id ? library.findSaved(id) : undefined
    nameDraft.value = p?.name ?? ''
    colorsDraft.value = p?.colors.slice() ?? []
    locked.value = Array(colorsDraft.value.length).fill(false)
    mode.value = 'random'
  },
  { immediate: true },
)

const visible = computed({
  get: () => library.editingId !== null,
  set: (value) => {
    if (!value) library.cancelEdit()
  },
})

const slotPickerValues = computed(() =>
  colorsDraft.value.map((c) => c.replace('#', '')),
)

function onSlotChange(index: number, raw: string | { hex?: string } | null) {
  const hex = typeof raw === 'string' ? raw : raw?.hex ?? ''
  if (!hex) return
  const next = colorsDraft.value.slice()
  next[index] = normalizeHex(`#${hex}`)
  colorsDraft.value = next
}

function toggleLock(index: number) {
  const next = locked.value.slice()
  next[index] = !next[index]
  locked.value = next
}

function regenerate() {
  // Silent no-op if every slot is locked.
  if (locked.value.every((v) => v)) return
  colorsDraft.value = generatePalette(mode.value, colorsDraft.value, locked.value)
}

function onSave() {
  if (!palette.value) return
  const name = nameDraft.value.trim() || palette.value.name
  library.saveEdit(name, colorsDraft.value)
}

function onCancel() {
  library.cancelEdit()
}

// Space shortcut for regenerate. Only when the editor is open and focus is
// NOT inside a text input (so typing a space in the name field works).
function onKeydown(e: KeyboardEvent) {
  if (library.editingId === null) return
  if (e.code !== 'Space' && e.key !== ' ') return
  const target = e.target as HTMLElement | null
  const tag = target?.tagName
  const isEditable =
    tag === 'INPUT' ||
    tag === 'TEXTAREA' ||
    tag === 'SELECT' ||
    target?.isContentEditable === true
  // Also skip PrimeVue comboboxes/listboxes so space opens/selects as usual.
  const isComboboxContext = target?.closest(
    '[role="combobox"],[role="listbox"],[role="option"]',
  )
  if (isEditable || isComboboxContext) return
  e.preventDefault()
  regenerate()
}

onMounted(() => {
  window.addEventListener('keydown', onKeydown)
})
onBeforeUnmount(() => {
  window.removeEventListener('keydown', onKeydown)
})
</script>

<template>
  <Dialog
    v-model:visible="visible"
    modal
    :style="{ width: '520px' }"
  >
    <template #header>
      <InputText
        v-if="palette"
        v-model="nameDraft"
        class="name-input"
      />
      <span v-else>Palette editor</span>
    </template>

    <div v-if="!palette" class="empty">Palette not found.</div>
    <template v-else>
      <section class="editor-section">
        <h4>Slots</h4>
        <div class="slot-row">
          <div v-for="(c, i) in colorsDraft" :key="i" class="slot">
            <ColorPicker
              :modelValue="slotPickerValues[i]"
              @update:modelValue="onSlotChange(i, $event)"
            />
            <Button
              :icon="locked[i] ? 'pi pi-lock' : 'pi pi-lock-open'"
              :severity="locked[i] ? 'primary' : 'secondary'"
              text
              size="small"
              :aria-label="locked[i] ? 'Unlock slot' : 'Lock slot'"
              @click="toggleLock(i)"
            />
          </div>
        </div>
      </section>

      <section class="editor-section">
        <h4>Generate</h4>
        <div class="generate-row">
          <Select
            v-model="mode"
            :options="GENERATION_MODES"
            optionLabel="label"
            optionValue="value"
            class="mode-select"
          />
          <Button
            icon="pi pi-refresh"
            label="Regenerate"
            severity="secondary"
            @click="regenerate"
          />
          <span class="hint">or press space</span>
        </div>
      </section>
    </template>

    <template #footer>
      <Button
        label="Cancel"
        severity="secondary"
        text
        @click="onCancel"
      />
      <Button
        label="Save"
        :disabled="!palette"
        @click="onSave"
      />
    </template>
  </Dialog>
</template>

<style scoped>
.name-input {
  font-size: 1rem;
  font-weight: 600;
  min-width: 240px;
}
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
  gap: 0.75rem;
}
.slot {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.25rem;
  flex: 0 0 auto;
}
.generate-row {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}
.mode-select {
  min-width: 200px;
}
.hint {
  font-size: 0.75rem;
  color: var(--p-text-muted-color);
}
.empty {
  font-size: 0.85rem;
  color: var(--p-text-muted-color);
}
</style>
