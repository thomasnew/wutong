import { createRouter, createWebHistory } from "vue-router";
import { authStore } from "../stores/auth";
import LoginView from "../views/LoginView.vue";
import HomeView from "../views/HomeView.vue";
import GalleryView from "../views/GalleryView.vue";
import AdminView from "../views/AdminView.vue";

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: "/login", component: LoginView },
    { path: "/", component: HomeView },
    { path: "/gallery", component: GalleryView },
    { path: "/admin", component: AdminView },
  ],
});

router.beforeEach((to) => {
  if (to.path !== "/login" && !authStore.token) {
    return "/login";
  }
  if (to.path === "/admin" && authStore.user?.role !== "admin") {
    return "/";
  }
  if (to.path === "/login" && authStore.token) {
    return "/";
  }
  return true;
});

export default router;
