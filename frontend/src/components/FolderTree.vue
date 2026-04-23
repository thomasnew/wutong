<template>
  <div class="folder-tree">
    <button
      class="folder-item"
      :class="{ active: modelValue === '' }"
      @click="$emit('update:modelValue', '')"
    >
      全部照片 ({{ totalCount }})
    </button>
    <div v-for="node in tree.children || []" :key="node.path" class="folder-node">
      <FolderNode
        :node="node"
        :model-value="modelValue"
        :count-map="countMap"
        @update:model-value="$emit('update:modelValue', $event)"
      />
    </div>
  </div>
</template>

<script setup>
import FolderNode from "./FolderNode.vue";
defineProps({
  tree: { type: Object, required: true },
  modelValue: { type: String, required: true },
  countMap: { type: Object, default: () => ({}) },
  totalCount: { type: Number, default: 0 },
});
defineEmits(["update:modelValue"]);
</script>
