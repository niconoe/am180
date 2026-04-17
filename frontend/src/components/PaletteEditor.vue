<script setup lang="ts">
import Dialog from 'primevue/dialog'
import ColorPicker from 'primevue/colorpicker'
import InputText from 'primevue/inputtext'
import Button from 'primevue/button'
import { computed, ref, watch } from 'vue'
import { usePalettesLibrary } from '@/stores/palettesLibrary'
import { normalizeHex } from '@/utils/palette'
import type { HexColor } from '@/types/palette'

const library = usePalettesLibrary()

const palette = computed(() =>
  library.editingId ? library.findSaved(library.editingId) : undefined,
)

// Draft state - applied to the store only when the user clicks Save.
const nameDraft = ref('')
const colorsDraft = ref<HexColor[]>([])

watch(
  () => library.editingId,
  (id) => {
    const p = id ? library.findSaved(id) : undefined
    nameDraft.value = p?.name ?? ''
    colorsDraft.value = p?.colors.slice() ?? []
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

function onSave() {
  if (!palette.value) return
  // Fall back to existing name if the user cleared it.
  const name = nameDraft.value.trim() || palette.value.name
  library.saveEdit(name, colorsDraft.value)
}

function onCancel() {
  library.cancelEdit()
}
</script>

<template>
  <Dialog
    v-model:visible="visible"
    modal
    :style="{ width: '480px' }"
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
          </div>
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
  gap: 0.5rem;
}
.slot {
  flex: 0 0 auto;
}
.empty {
  font-size: 0.85rem;
  color: var(--p-text-muted-color);
}
</style>
