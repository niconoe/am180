<script setup lang="ts">
defineProps<{
  previewUrl: string | null
  isRendering: boolean
}>()
</script>

<template>
  <div class="preview-pane">
    <img
      v-if="previewUrl"
      :src="previewUrl"
      alt="Preview"
      class="preview-image"
    />
    <div v-else class="preview-placeholder">
      No preview yet
    </div>
    <div v-if="isRendering" class="rendering-indicator">
      Rendering...
    </div>
  </div>
</template>

<style scoped>
.preview-pane {
  position: relative;
  background: #111;
  border-radius: 8px;
  overflow: hidden;
  aspect-ratio: 1;
  max-width: 100%;
  max-height: 100%;
}
.preview-image {
  width: 100%;
  height: 100%;
  object-fit: contain;
  display: block;
}
.preview-placeholder {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  height: 100%;
  color: #666;
  min-height: 400px;
}
.rendering-indicator {
  position: absolute;
  top: 0.5rem;
  right: 0.5rem;
  background: rgba(0, 0, 0, 0.7);
  color: #fff;
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
  font-size: 0.75rem;
}
</style>
