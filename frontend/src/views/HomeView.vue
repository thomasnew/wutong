<template>
  <section class="panel">
    <div class="toolbar">
      <h3>数据看板</h3>
      <button @click="loadStats">刷新</button>
    </div>
    <p class="error" v-if="error">{{ error }}</p>
    <div class="rank-grid">
      <article class="rank-card">
        <h4>最多点赞 Top 10</h4>
        <ol>
          <li v-for="item in stats.top_liked" :key="item.photo_id" @click="openDetail(item.photo_id)">
            <div
              class="rank-thumb-wrap"
              @mouseenter.stop="scheduleHoverLoad(item.photo_id)"
              @mouseleave.stop="clearHoverTimer(item.photo_id)"
            >
              <img class="rank-thumb" :src="photoUrl(item.relative_path)" :alt="item.filename" />
              <div class="rank-hover-preview">
                <p v-if="hoverLoading[item.photo_id]" class="hover-loading">加载中...</p>
                <template v-else>
                  <p class="hover-title">点赞用户</p>
                  <p class="hover-text">
                    {{
                      hoverDetails[item.photo_id]?.liked_users?.length
                        ? hoverDetails[item.photo_id].liked_users.map((u) => u.username).join("、")
                        : "暂无点赞"
                    }}
                  </p>
                  <p class="hover-title">最新评论</p>
                  <ul class="hover-comments">
                    <li v-for="c in (hoverDetails[item.photo_id]?.comments || []).slice(0, 3)" :key="c.id">
                      <strong>{{ c.username || "unknown" }}：</strong>{{ c.content }}
                    </li>
                    <li v-if="!(hoverDetails[item.photo_id]?.comments || []).length">暂无评论</li>
                  </ul>
                </template>
              </div>
            </div>
            <div class="rank-main">
              <div class="rank-head">
                <span class="rank-title">{{ item.title }}</span>
                <span>👍 {{ item.like_count }}</span>
              </div>
              <div class="rank-marquee">
                <span class="rank-marquee-track" :style="marqueeStyle()">{{ likedMarquee(item.photo_id) }}</span>
              </div>
            </div>
          </li>
        </ol>
      </article>
      <article class="rank-card">
        <h4>最多评论 Top 10</h4>
        <ol>
          <li v-for="item in stats.top_commented" :key="item.photo_id" @click="openDetail(item.photo_id)">
            <div
              class="rank-thumb-wrap"
              @mouseenter.stop="scheduleHoverLoad(item.photo_id)"
              @mouseleave.stop="clearHoverTimer(item.photo_id)"
            >
              <img class="rank-thumb" :src="photoUrl(item.relative_path)" :alt="item.filename" />
              <div class="rank-hover-preview">
                <p v-if="hoverLoading[item.photo_id]" class="hover-loading">加载中...</p>
                <template v-else>
                  <p class="hover-title">点赞用户</p>
                  <p class="hover-text">
                    {{
                      hoverDetails[item.photo_id]?.liked_users?.length
                        ? hoverDetails[item.photo_id].liked_users.map((u) => u.username).join("、")
                        : "暂无点赞"
                    }}
                  </p>
                  <p class="hover-title">最新评论</p>
                  <ul class="hover-comments">
                    <li v-for="c in (hoverDetails[item.photo_id]?.comments || []).slice(0, 3)" :key="c.id">
                      <strong>{{ c.username || "unknown" }}：</strong>{{ c.content }}
                    </li>
                    <li v-if="!(hoverDetails[item.photo_id]?.comments || []).length">暂无评论</li>
                  </ul>
                </template>
              </div>
            </div>
            <div class="rank-main">
              <div class="rank-head">
                <span class="rank-title">{{ item.title }}</span>
                <span>💬 {{ item.comment_count }}</span>
              </div>
              <div class="rank-marquee">
                <span class="rank-marquee-track" :style="marqueeStyle()">{{ commentMarquee(item.photo_id) }}</span>
              </div>
            </div>
          </li>
        </ol>
      </article>
      <article class="rank-card">
        <h4>最新更新 Top 10</h4>
        <ol>
          <li v-for="item in stats.latest_updated" :key="item.photo_id" @click="openDetail(item.photo_id)">
            <div
              class="rank-thumb-wrap"
              @mouseenter.stop="scheduleHoverLoad(item.photo_id)"
              @mouseleave.stop="clearHoverTimer(item.photo_id)"
            >
              <img class="rank-thumb" :src="photoUrl(item.relative_path)" :alt="item.filename" />
              <div class="rank-hover-preview">
                <p v-if="hoverLoading[item.photo_id]" class="hover-loading">加载中...</p>
                <template v-else>
                  <p class="hover-title">点赞用户</p>
                  <p class="hover-text">
                    {{
                      hoverDetails[item.photo_id]?.liked_users?.length
                        ? hoverDetails[item.photo_id].liked_users.map((u) => u.username).join("、")
                        : "暂无点赞"
                    }}
                  </p>
                  <p class="hover-title">最新评论</p>
                  <ul class="hover-comments">
                    <li v-for="c in (hoverDetails[item.photo_id]?.comments || []).slice(0, 3)" :key="c.id">
                      <strong>{{ c.username || "unknown" }}：</strong>{{ c.content }}
                    </li>
                    <li v-if="!(hoverDetails[item.photo_id]?.comments || []).length">暂无评论</li>
                  </ul>
                </template>
              </div>
            </div>
            <div class="rank-main">
              <div class="rank-head">
                <span class="rank-title">{{ item.title }}</span>
                <span>{{ formatTime(item.updated_at) }}</span>
              </div>
              <div class="rank-marquee">
                <span class="rank-marquee-track" :style="marqueeStyle()">{{ updatedMarquee(item.photo_id, item.updated_at) }}</span>
              </div>
            </div>
          </li>
        </ol>
      </article>
    </div>
  </section>

  <div class="modal-mask" v-if="detail" @click.self="detail = null">
    <div class="modal">
      <header class="modal-header">
        <h3>{{ detail.title || detail.filename }}</h3>
        <button @click="detail = null">关闭</button>
      </header>
      <img
        v-if="detail.media_type !== 'video'"
        class="detail-image"
        :src="photoUrl(detail.relative_path)"
        :alt="detail.filename"
      />
      <video v-else class="detail-video" :src="photoUrl(detail.relative_path)" controls preload="metadata"></video>
      <p>{{ detail.description || "暂无描述" }}</p>
      <p>地点：{{ detail.location_text || "未知" }}</p>
      <div class="actions">
        <button @click="toggleLikeInHome">
          {{ detail.liked_by_me ? "取消喜欢" : "喜欢" }} ({{ detail.like_count || 0 }})
        </button>
      </div>
      <p class="hint" v-if="detail.liked_users?.length">
        点赞用户：{{ detail.liked_users.map((u) => u.username).join("、") }}
      </p>
      <form @submit.prevent="addCommentInHome">
        <input v-model="commentText" placeholder="写下评论..." />
        <button type="submit">发送</button>
      </form>
      <ul class="comments">
        <li v-for="c in detail.comments || []" :key="c.id">
          <span>
            <strong>{{ c.username || "unknown" }}：</strong>{{ c.content }}
          </span>
        </li>
      </ul>
    </div>
  </div>
</template>

<script setup>
import { ref } from "vue";
import {
  deleteLike,
  getPhotoDetail,
  getSettings,
  getTopStats,
  postComment,
  postLike,
} from "../api/client";

const stats = ref({
  top_liked: [],
  top_commented: [],
  latest_updated: [],
});
const error = ref("");
const detail = ref(null);
const hoverDetails = ref({});
const hoverLoading = ref({});
const hoverTimers = new Map();
const hoverInflight = new Map();
const marqueeSpeedSeconds = ref(12);
const commentText = ref("");

async function loadStats() {
  error.value = "";
  try {
    stats.value = await getTopStats();
    const settings = await getSettings();
    marqueeSpeedSeconds.value = settings.marquee_speed_seconds || 12;
    preloadTopDetails();
  } catch (e) {
    error.value = e.message;
  }
}

function formatTime(value) {
  if (!value) return "";
  const d = new Date(value);
  if (Number.isNaN(d.getTime())) return "";
  return d.toLocaleString();
}

async function openDetail(photoId) {
  detail.value = await getPhotoDetail(photoId);
  commentText.value = "";
}

function photoUrl(relativePath) {
  return `/photos/${relativePath}`;
}

function scheduleHoverLoad(photoId) {
  if (hoverDetails.value[photoId] || hoverInflight.has(photoId)) return;
  clearHoverTimer(photoId);
  const t = setTimeout(() => loadHoverDetail(photoId), 180);
  hoverTimers.set(photoId, t);
}

function clearHoverTimer(photoId) {
  const t = hoverTimers.get(photoId);
  if (!t) return;
  clearTimeout(t);
  hoverTimers.delete(photoId);
}

async function loadHoverDetail(photoId) {
  if (hoverDetails.value[photoId]) return;
  if (hoverInflight.has(photoId)) return hoverInflight.get(photoId);
  hoverLoading.value = { ...hoverLoading.value, [photoId]: true };
  const task = getPhotoDetail(photoId)
    .then((d) => {
      hoverDetails.value = {
        ...hoverDetails.value,
        [photoId]: {
          liked_users: d.liked_users || [],
          comments: d.comments || [],
        },
      };
    })
    .finally(() => {
      hoverInflight.delete(photoId);
      hoverLoading.value = { ...hoverLoading.value, [photoId]: false };
    });
  hoverInflight.set(photoId, task);
  return task;
}

function preloadTopDetails() {
  const ids = new Set([
    ...stats.value.top_liked.map((x) => x.photo_id),
    ...stats.value.top_commented.map((x) => x.photo_id),
    ...stats.value.latest_updated.map((x) => x.photo_id),
  ]);
  ids.forEach((id) => {
    if (!hoverDetails.value[id]) {
      loadHoverDetail(id);
    }
  });
}

function likedMarquee(photoId) {
  const users = hoverDetails.value[photoId]?.liked_users || [];
  if (!users.length) return "点赞用户：暂无";
  return `点赞用户：${users.map((u) => u.username).join("、")}  •  `;
}

function commentMarquee(photoId) {
  const comments = hoverDetails.value[photoId]?.comments || [];
  if (!comments.length) return "评论内容：暂无";
  return (
    "评论内容：" +
    comments
      .slice(0, 5)
      .map((c) => `${c.username || "unknown"}: ${c.content}`)
      .join("  |  ") +
    "  •  "
  );
}

function updatedMarquee(photoId, updatedAt) {
  const liked = hoverDetails.value[photoId]?.liked_users?.length || 0;
  const comments = hoverDetails.value[photoId]?.comments?.length || 0;
  return `最近更新：${formatTime(updatedAt)}，累计点赞 ${liked}，累计评论 ${comments}  •  `;
}

function marqueeStyle() {
  return { animationDuration: `${marqueeSpeedSeconds.value}s` };
}

async function toggleLikeInHome() {
  if (!detail.value) return;
  if (detail.value.liked_by_me) {
    await deleteLike(detail.value.id);
  } else {
    await postLike(detail.value.id);
  }
  detail.value = await getPhotoDetail(detail.value.id);
  await loadStats();
}

async function addCommentInHome() {
  if (!detail.value || !commentText.value.trim()) return;
  await postComment(detail.value.id, commentText.value);
  commentText.value = "";
  detail.value = await getPhotoDetail(detail.value.id);
  await loadStats();
}

loadStats();
</script>
