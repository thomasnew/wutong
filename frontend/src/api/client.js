import { authStore } from "../stores/auth";

async function request(path, options = {}) {
  const headers = {
    "Content-Type": "application/json",
    ...(options.headers || {}),
  };
  if (authStore.token) {
    headers.Authorization = `Bearer ${authStore.token}`;
  }

  const res = await fetch(path, { ...options, headers });
  if (!res.ok) {
    const payload = await res.json().catch(() => ({}));
    throw new Error(payload.detail || `HTTP ${res.status}`);
  }
  if (res.status === 204) {
    return null;
  }
  return res.json();
}

export const postLogin = (username, password) =>
  request("/api/auth/login", {
    method: "POST",
    body: JSON.stringify({ username, password }),
  });

export const postLogout = () => request("/api/auth/logout", { method: "POST" });
export const getMe = () => request("/api/auth/me");
export const getFolderTree = () => request("/api/folders/tree");
export const getPhotos = (folder = "") =>
  request(`/api/photos${folder ? `?folder=${encodeURIComponent(folder)}` : ""}`);
export const getPhotoDetail = (photoId) => request(`/api/photos/${photoId}`);
export const getTopStats = () => request("/api/stats/top");
export const getSettings = () => request("/api/settings");
export const postLike = (photoId) => request(`/api/photos/${photoId}/like`, { method: "POST" });
export const deleteLike = (photoId) =>
  request(`/api/photos/${photoId}/like`, { method: "DELETE" });
export const postComment = (photoId, content) =>
  request(`/api/photos/${photoId}/comments`, {
    method: "POST",
    body: JSON.stringify({ content }),
  });
export const deleteComment = (commentId) =>
  request(`/api/comments/${commentId}`, { method: "DELETE" });
export const adminScan = () => request("/api/admin/scan", { method: "POST" });
export const adminUsers = () => request("/api/admin/users");
export const adminCreateUser = (payload) =>
  request("/api/admin/users", { method: "POST", body: JSON.stringify(payload) });
export const adminUpdateUser = (userId, payload) =>
  request(`/api/admin/users/${userId}`, { method: "PATCH", body: JSON.stringify(payload) });
export const adminDeleteUser = (userId) =>
  request(`/api/admin/users/${userId}`, { method: "DELETE" });
export const adminUpdateMetadata = (photoId, payload) =>
  request(`/api/admin/photos/${photoId}/metadata`, {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
export const adminUpdateMarqueeSpeed = (marquee_speed_seconds) =>
  request("/api/admin/settings/marquee-speed", {
    method: "PATCH",
    body: JSON.stringify({ marquee_speed_seconds }),
  });
