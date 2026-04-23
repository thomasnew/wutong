<template>
  <div class="layout">
    <section class="panel main-panel">
      <div class="toolbar">
        <h3>管理后台</h3>
        <button @click="scanNow">手动扫描</button>
      </div>
      <p v-if="scanResult">扫描结果：新增 {{ scanResult.created }}，更新 {{ scanResult.updated }}，删除 {{ scanResult.deleted }}</p>
      <p class="error" v-if="error">{{ error }}</p>
    </section>
  </div>

  <div class="layout">
    <section class="panel">
      <h4>首页跑马灯速度</h4>
      <form @submit.prevent="saveMarqueeSpeed">
        <input
          v-model.number="marqueeSpeed"
          type="number"
          min="4"
          max="60"
          placeholder="速度(秒)"
          required
        />
        <button type="submit">保存速度</button>
      </form>
      <p class="hint" v-if="settingsMsg">{{ settingsMsg }}</p>
    </section>
  </div>

  <div class="layout">
    <section class="panel">
      <h4>创建用户</h4>
      <form @submit.prevent="createUser">
        <input v-model="newUser.username" placeholder="用户名" required />
        <input v-model="newUser.password" placeholder="密码" type="password" required />
        <select v-model="newUser.role">
          <option value="user">user</option>
          <option value="admin">admin</option>
        </select>
        <button type="submit">创建</button>
      </form>
    </section>

    <section class="panel">
      <h4>用户列表</h4>
      <ul class="comments">
        <li v-for="u in users" :key="u.id">
          <span>{{ u.username }} ({{ u.role }})</span>
          <span class="user-actions">
            <button class="icon-btn" :title="`重置 ${u.username} 的密码`" @click="resetPassword(u)">↻</button>
            <button class="icon-btn danger" :title="`删除用户 ${u.username}`" @click="deleteUser(u)">×</button>
          </span>
        </li>
      </ul>
      <p class="hint" v-if="userOpMsg">{{ userOpMsg }}</p>
    </section>
  </div>

</template>

<script setup>
import { ref } from "vue";
import {
  adminCreateUser,
  adminDeleteUser,
  adminUpdateMarqueeSpeed,
  adminUpdateUser,
  adminScan,
  adminUsers,
  getSettings,
} from "../api/client";

const users = ref([]);
const scanResult = ref(null);
const error = ref("");
const settingsMsg = ref("");
const userOpMsg = ref("");
const newUser = ref({ username: "", password: "", role: "user" });
const marqueeSpeed = ref(12);

async function loadUsers() {
  users.value = await adminUsers();
}

async function scanNow() {
  scanResult.value = await adminScan();
}

async function loadSettings() {
  const data = await getSettings();
  marqueeSpeed.value = data.marquee_speed_seconds || 12;
}

async function createUser() {
  error.value = "";
  try {
    await adminCreateUser(newUser.value);
    newUser.value = { username: "", password: "", role: "user" };
    await loadUsers();
  } catch (e) {
    error.value = e.message;
  }
}

async function resetPassword(user) {
  error.value = "";
  userOpMsg.value = "";
  try {
    const pwd = window.prompt(`为用户 ${user.username} 设置新密码（至少4位）`);
    if (pwd === null) return;
    if (!pwd.trim()) throw new Error("新密码不能为空");
    await adminUpdateUser(user.id, { password: pwd });
    userOpMsg.value = `用户 ${user.username} 密码已重置`;
    await loadUsers();
  } catch (e) {
    error.value = e.message;
  }
}

async function deleteUser(user) {
  error.value = "";
  userOpMsg.value = "";
  try {
    const ok = window.confirm(`确认删除用户 ${user.username} 吗？`);
    if (!ok) return;
    await adminDeleteUser(user.id);
    userOpMsg.value = `用户 ${user.username} 已删除`;
    await loadUsers();
  } catch (e) {
    error.value = e.message;
  }
}

async function saveMarqueeSpeed() {
  error.value = "";
  settingsMsg.value = "";
  try {
    const data = await adminUpdateMarqueeSpeed(Number(marqueeSpeed.value));
    marqueeSpeed.value = data.marquee_speed_seconds;
    settingsMsg.value = "跑马灯速度已保存";
  } catch (e) {
    error.value = e.message;
  }
}

loadUsers();
loadSettings();
</script>
