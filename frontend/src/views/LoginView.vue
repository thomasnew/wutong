<template>
  <section class="panel auth-panel">
    <h2>登录</h2>
    <form @submit.prevent="onSubmit">
      <label>
        用户名
        <input v-model="username" required />
      </label>
      <label>
        密码
        <input v-model="password" type="password" required />
      </label>
      <button type="submit" :disabled="loading">{{ loading ? "登录中..." : "登录" }}</button>
      <p class="error" v-if="error">{{ error }}</p>
    </form>
    <p class="hint">默认管理员：admin / admin123</p>
  </section>
</template>

<script setup>
import { ref } from "vue";
import { useRouter } from "vue-router";
import { postLogin } from "../api/client";
import { authStore } from "../stores/auth";

const router = useRouter();
const username = ref("admin");
const password = ref("admin123");
const loading = ref(false);
const error = ref("");

async function onSubmit() {
  loading.value = true;
  error.value = "";
  try {
    const data = await postLogin(username.value, password.value);
    authStore.setAuth(data.token, data.user);
    router.push("/");
  } catch (e) {
    error.value = e.message;
  } finally {
    loading.value = false;
  }
}
</script>
