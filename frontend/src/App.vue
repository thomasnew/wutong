<template>
  <div class="app-shell" :class="`client-${deviceType}`">
    <header class="topbar">
      <div class="brand">Family Photo Gallery</div>
      <nav class="nav" v-if="token">
        <RouterLink to="/">首页</RouterLink>
        <RouterLink to="/gallery">照片墙</RouterLink>
        <RouterLink to="/admin" v-if="user?.role === 'admin'">管理后台</RouterLink>
        <span class="user-badge" v-if="user?.username">当前用户：{{ user.username }}</span>
        <button class="link-btn" @click="onLogout">退出</button>
      </nav>
    </header>
    <main class="content">
      <RouterView />
    </main>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from "vue";
import { RouterLink, RouterView, useRouter } from "vue-router";
import { authStore } from "./stores/auth";
import { getClientProfile, postLogout } from "./api/client";

const router = useRouter();
const token = computed(() => authStore.token);
const user = computed(() => authStore.user);
const deviceType = ref("pc");

async function onLogout() {
  try {
    await postLogout();
  } catch (_) {
    // ignore
  }
  authStore.clear();
  router.push("/login");
}

function detectDeviceFromScreen() {
  if (typeof window === "undefined") return "pc";
  return window.matchMedia("(max-width: 768px)").matches ? "mobile" : "pc";
}

async function loadClientProfile() {
  try {
    const data = await getClientProfile();
    deviceType.value = data?.is_mobile ? "mobile" : detectDeviceFromScreen();
  } catch (_) {
    deviceType.value = detectDeviceFromScreen();
  }
}

onMounted(loadClientProfile);
</script>
