<script setup lang="ts">
import { onMounted, watch } from 'vue'
import { useGenartStore } from '@/stores/genart'
import Button from 'primevue/button'
import Checkbox from 'primevue/checkbox'
import ConfirmDialog from 'primevue/confirmdialog'
import GeneratorPicker from '@/components/GeneratorPicker.vue'
import ParamForm from '@/components/ParamForm.vue'
import SeedControls from '@/components/SeedControls.vue'
import PreviewPane from '@/components/PreviewPane.vue'
import ExportButton from '@/components/ExportButton.vue'
import PaletteEditor from '@/components/PaletteEditor.vue'

const store = useGenartStore()

onMounted(() => {
  store.loadGenerators()
})

// Debounced preview loop: when params, seed, or generator change,
// wait 150ms then request a new preview. If the user is still
// dragging a slider, the timer resets and only the final value fires.
let debounceTimer: ReturnType<typeof setTimeout> | null = null

watch(
  [() => store.params, () => store.seed, () => store.selectedGeneratorId],
  () => {
    if (!store.selectedGeneratorId || store.schema.length === 0) return
    if (debounceTimer) clearTimeout(debounceTimer)
    debounceTimer = setTimeout(() => {
      store.requestPreview()
    }, 150)
  },
  { deep: true },
)
</script>

<template>
  <div class="app-layout">
    <aside class="sidebar">
      <h1 class="app-title">am180</h1>

      <GeneratorPicker
        :generators="store.generators"
        :modelValue="store.selectedGeneratorId"
        @update:modelValue="store.selectGenerator($event)"
      />

      <ParamForm
        v-if="store.schema.length > 0"
        :schema="store.schema"
        :modelValue="store.params"
        @update:modelValue="store.params = $event"
      />

      <div class="randomize-option">
        <Checkbox
          v-model="store.paperFromPalette"
          inputId="paper-from-palette"
          binary
          size="small"
        />
        <label for="paper-from-palette">Paper color from palette</label>
      </div>

      <Button
        label="Randomize all"
        severity="secondary"
        size="small"
        @click="store.randomizeAll()"
        style="width: 100%"
      />

      <SeedControls
        :modelValue="store.seed"
        @update:modelValue="store.seed = $event"
        @randomize="store.randomizeSeed()"
      />

      <ExportButton
        :disabled="store.isRendering || !store.previewUrl"
        @export="store.exportFullRes()"
      />
    </aside>

    <main class="main-content">
      <PreviewPane
        :previewUrl="store.previewUrl"
        :isRendering="store.isRendering"
      />
    </main>

    <PaletteEditor />
    <ConfirmDialog />
  </div>
</template>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}
html, body, #app {
  height: 100%;
}
</style>

<style scoped>
.app-layout {
  display: flex;
  height: 100vh;
  background: var(--p-surface-0);
  color: var(--p-text-color);
}
.sidebar {
  width: 320px;
  padding: 1.5rem;
  overflow-y: auto;
  border-right: 1px solid var(--p-surface-200);
  display: flex;
  flex-direction: column;
  gap: 1rem;
}
.randomize-option {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.875rem;
  /* Pull the Randomize all button closer: this option belongs to it. */
  margin-bottom: -0.5rem;
}
.randomize-option label {
  cursor: pointer;
}
.app-title {
  font-size: 1.5rem;
  font-weight: 700;
  margin-bottom: 0.5rem;
}
.main-content {
  flex: 1;
  padding: 1.5rem;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--p-surface-50);
}
</style>
