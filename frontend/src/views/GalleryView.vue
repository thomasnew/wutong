<template>
  <div class="layout">
    <aside class="panel sidebar">
      <h3>目录</h3>
      <FolderTree
        v-if="tree"
        v-model="selectedFolder"
        :tree="tree"
        :count-map="folderCountMap"
        :total-count="allPhotos.length"
      />
    </aside>
    <section class="panel main-panel">
      <div class="toolbar">
        <h3>照片墙</h3>
        <button @click="loadAll">刷新</button>
      </div>
      <p v-if="error" class="error">{{ error }}</p>
      <div class="grid">
        <PhotoCard
          v-for="(photo, idx) in photos"
          :key="photo.id"
          :photo="photo"
          :is-admin="authStore.user?.role === 'admin'"
          :size="cardSize(idx)"
          :hover-data="hoverDetails[photo.id]"
          :hover-loading="hoverLoading[photo.id]"
          @open="openDetail"
          @edit="openEdit"
          @hover="scheduleHoverLoad"
          @leave="clearHoverTimer"
        />
      </div>
    </section>
  </div>

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
      <video
        v-else
        class="detail-video"
        :src="photoUrl(detail.relative_path)"
        :type="videoMime(detail.relative_path)"
        controls
        preload="metadata"
      ></video>
      <p>{{ detail.description || "暂无描述" }}</p>
      <p>地点：{{ detail.location_text || "未知" }}</p>
      <div class="actions">
        <button @click="toggleLike">{{ detail.liked_by_me ? "取消喜欢" : "喜欢" }} ({{ detail.like_count }})</button>
      </div>
      <p class="hint" v-if="detail.liked_users?.length">
        点赞用户：{{ detail.liked_users.map((u) => u.username).join("、") }}
      </p>
      <section>
        <h4>评论</h4>
        <form @submit.prevent="addComment">
          <input v-model="commentText" placeholder="写下评论..." />
          <button type="submit">发送</button>
        </form>
        <ul class="comments">
          <li v-for="c in detail.comments" :key="c.id">
            <span>
              <strong>{{ c.username || "unknown" }}：</strong>{{ c.content }}
              <small class="comment-time">{{ formatTime(c.created_at) }}</small>
            </span>
            <button v-if="canDelete(c)" @click="removeComment(c)">删除</button>
          </li>
        </ul>
      </section>
    </div>
  </div>

  <div class="modal-mask" v-if="editMeta" @click.self="editMeta = null">
    <div class="modal">
      <header class="modal-header">
        <h3>编辑元数据</h3>
        <button @click="editMeta = null">关闭</button>
      </header>
      <div class="edit-preview" v-if="editMeta">
        <img
          class="edit-preview-thumb"
          :src="photoUrl(editMeta.relative_path)"
          :alt="editMeta.filename"
        />
        <div class="edit-preview-meta">
          <strong>{{ editMeta.title || editMeta.filename }}</strong>
          <small>{{ editMeta.filename }}</small>
        </div>
      </div>
      <form @submit.prevent="saveMetaFromGallery">
        <input v-model="editForm.title" placeholder="标题" />
        <input v-model="editForm.location_text" placeholder="地点" />
        <input v-model="editForm.tagsText" placeholder="标签(逗号分隔)" />
        <textarea v-model="editForm.description" placeholder="描述"></textarea>
        <button type="submit">保存</button>
      </form>
    </div>
  </div>
</template>

<script setup>
import { ref, watch } from "vue";
import { useRoute, useRouter } from "vue-router";
import FolderTree from "../components/FolderTree.vue";
import PhotoCard from "../components/PhotoCard.vue";
import {
  deleteComment,
  deleteLike,
  getFolderTree,
  getPhotoDetail,
  getPhotos,
  adminUpdateMetadata,
  postComment,
  postLike,
} from "../api/client";
import { authStore } from "../stores/auth";

const tree = ref(null);
const photos = ref([]);
const allPhotos = ref([]);
const folderCountMap = ref({});
const selectedFolder = ref("");
const detail = ref(null);
const commentText = ref("");
const error = ref("");
const editMeta = ref(null);
const hoverDetails = ref({});
const hoverLoading = ref({});
const hoverTimers = new Map();
const hoverInflight = new Map();
const editForm = ref({
  title: "",
  description: "",
  location_text: "",
  tagsText: "",
});
const route = useRoute();
const router = useRouter();

watch(selectedFolder, async () => {
  await loadPhotos();
});

async function loadAll() {
  error.value = "";
  try {
    tree.value = await getFolderTree();
    await loadAllPhotosForCounts();
    await loadPhotos();
  } catch (e) {
    error.value = e.message;
  }
}

async function loadPhotos() {
  photos.value = await getPhotos(selectedFolder.value);
}

async function loadAllPhotosForCounts() {
  allPhotos.value = await getPhotos("");
  const countMap = {};
  for (const photo of allPhotos.value) {
    const folder = photo.folder_path || "";
    if (!folder) continue;
    const parts = folder.split("/").filter(Boolean);
    let current = "";
    for (const part of parts) {
      current = current ? `${current}/${part}` : part;
      countMap[current] = (countMap[current] || 0) + 1;
    }
  }
  folderCountMap.value = countMap;
}

function scheduleHoverLoad(photoId) {
  if (hoverDetails.value[photoId] || hoverInflight.has(photoId)) return;
  clearHoverTimer(photoId);
  const t = setTimeout(() => {
    loadHoverDetail(photoId);
  }, 180);
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

async function openDetail(photoId) {
  detail.value = await getPhotoDetail(photoId);
}

async function openDetailFromRoute() {
  const photoId = route.query.photo_id;
  if (!photoId || typeof photoId !== "string") return;
  await openDetail(photoId);
  router.replace({ path: "/gallery", query: {} });
}

async function toggleLike() {
  if (!detail.value) return;
  if (detail.value.liked_by_me) {
    await deleteLike(detail.value.id);
  } else {
    await postLike(detail.value.id);
  }
  detail.value = await getPhotoDetail(detail.value.id);
  await loadPhotos();
}

async function addComment() {
  if (!detail.value || !commentText.value.trim()) return;
  await postComment(detail.value.id, commentText.value);
  commentText.value = "";
  detail.value = await getPhotoDetail(detail.value.id);
  await loadPhotos();
}

async function removeComment(comment) {
  const isAdmin = authStore.user?.role === "admin";
  const ok = window.confirm(
    isAdmin
      ? `确认删除该评论吗？\n用户：${comment.username || "unknown"}\n内容：${comment.content}`
      : `确认删除你的这条评论吗？\n内容：${comment.content}`
  );
  if (!ok) return;
  await deleteComment(comment.id);
  detail.value = await getPhotoDetail(detail.value.id);
  await loadPhotos();
}

function openEdit(photo) {
  if (authStore.user?.role !== "admin") return;
  editMeta.value = photo;
  editForm.value = {
    title: photo.title || "",
    description: photo.description || "",
    location_text: photo.location_text || "",
    tagsText: (photo.tags || []).join(", "),
  };
}

async function saveMetaFromGallery() {
  if (!editMeta.value || authStore.user?.role !== "admin") return;
  await adminUpdateMetadata(editMeta.value.id, {
    title: editForm.value.title || null,
    description: editForm.value.description || null,
    location_text: editForm.value.location_text || null,
    tags: editForm.value.tagsText
      ? editForm.value.tagsText.split(",").map((s) => s.trim()).filter(Boolean)
      : null,
  });
  editMeta.value = null;
  await loadPhotos();
  if (detail.value) {
    detail.value = await getPhotoDetail(detail.value.id);
  }
}

function canDelete(comment) {
  return authStore.user?.role === "admin" || comment.user_id === authStore.user?.id;
}

function photoUrl(relativePath) {
  return `/photos/${relativePath}`;
}

function videoMime(relativePath) {
  const ext = (relativePath.split(".").pop() || "").toLowerCase();
  const map = {
    mp4: "video/mp4",
    mov: "video/quicktime",
    webm: "video/webm",
    m4v: "video/mp4",
    avi: "video/x-msvideo",
    mkv: "video/x-matroska",
    flv: "video/x-flv",
    wmv: "video/x-ms-wmv",
    "3gp": "video/3gpp",
    ogv: "video/ogg",
    ts: "video/mp2t",
    m2ts: "video/mp2t",
    mts: "video/mp2t",
    mpg: "video/mpeg",
    mpeg: "video/mpeg",
  };
  return map[ext] || "video/mp4";
}

function cardSize(idx) {
  return idx % 5 === 0 || idx % 7 === 0 ? "large" : "small";
}

function formatTime(value) {
  if (!value) return "";
  const d = new Date(value);
  if (Number.isNaN(d.getTime())) return "";
  return d.toLocaleString();
}

watch(
  () => route.query.photo_id,
  async () => {
    await openDetailFromRoute();
  }
);

loadAll().then(openDetailFromRoute);
</script>
