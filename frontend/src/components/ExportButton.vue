<script setup lang="ts">
import Button from 'primevue/button'

defineProps<{
  disabled: boolean
}>()

const emit = defineEmits<{
  export: []
}>()
</script>

<template>
  <Button
    label="Export 4K PNG"
    @click="emit('export')"
    :disabled="disabled"
    style="width: 100%"
  />
</template>
