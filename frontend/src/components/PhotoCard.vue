<template>
  <article
    class="photo-card"
    :class="`photo-card--${size}`"
    @click="$emit('open', photo.id)"
    @mouseenter="$emit('hover', photo.id)"
    @mouseleave="$emit('leave', photo.id)"
  >
    <div class="photo-thumb" :class="`photo-thumb--${size}`">
      <img :src="photoUrl(photo.relative_path)" :alt="photo.filename" />
    </div>
    <div class="photo-meta">
      <h4>{{ photo.title || photo.filename }}</h4>
      <p>{{ photo.captured_at ? new Date(photo.captured_at).toLocaleString() : "无时间" }}</p>
      <p>👍 {{ photo.like_count }} · 💬 {{ photo.comment_count }}</p>
      <button v-if="isAdmin" class="admin-edit-btn" @click.stop="$emit('edit', photo)">编辑</button>
    </div>
    <div class="hover-preview">
      <p v-if="hoverLoading" class="hover-loading">加载中...</p>
      <template v-else>
        <p class="hover-title">点赞用户</p>
        <p class="hover-text">
          {{ hoverData?.liked_users?.length ? hoverData.liked_users.map((u) => u.username).join("、") : "暂无点赞" }}
        </p>
        <p class="hover-title">最新评论</p>
        <ul class="hover-comments">
          <li v-for="c in (hoverData?.comments || []).slice(0, 3)" :key="c.id">
            <strong>{{ c.username || "unknown" }}：</strong>{{ c.content }}
            <small class="hover-comment-time">{{ formatTime(c.created_at) }}</small>
          </li>
          <li v-if="!(hoverData?.comments || []).length">暂无评论</li>
        </ul>
      </template>
    </div>
  </article>
</template>

<script setup>
defineProps({
  photo: { type: Object, required: true },
  isAdmin: { type: Boolean, default: false },
  size: { type: String, default: "small" },
  hoverData: { type: Object, default: null },
  hoverLoading: { type: Boolean, default: false },
});
defineEmits(["open", "edit", "hover", "leave"]);

function photoUrl(relativePath) {
  return `/photos/${relativePath}`;
}

function formatTime(value) {
  if (!value) return "";
  const d = new Date(value);
  if (Number.isNaN(d.getTime())) return "";
  return d.toLocaleString();
}
</script>
