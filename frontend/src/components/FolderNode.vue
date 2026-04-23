<template>
  <div>
    <button
      class="folder-item"
      :class="{ active: modelValue === node.path }"
      @click="$emit('update:modelValue', node.path)"
    >
      {{ node.name }} ({{ folderCount(node.path) }})
    </button>
    <div class="folder-children" v-if="node.children?.length">
      <FolderNode
        v-for="child in node.children"
        :key="child.path"
        :node="child"
        :model-value="modelValue"
        :count-map="countMap"
        @update:model-value="$emit('update:modelValue', $event)"
      />
    </div>
  </div>
</template>

<script setup>
const props = defineProps({
  node: { type: Object, required: true },
  modelValue: { type: String, required: true },
  countMap: { type: Object, default: () => ({}) },
});
defineEmits(["update:modelValue"]);

function folderCount(path) {
  return props.countMap[path] || 0;
}
</script>
