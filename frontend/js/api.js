/* Shared API client for the CampusOne FastAPI service. */
const API_BASE = (import.meta.env.VITE_API_BASE || window.CAMPUSONE_API_BASE || "").replace(/\/$/, "");

const Auth = {
  getToken: () => localStorage.getItem("campusone_token"),
  setSession(token, user) {
    localStorage.setItem("campusone_token", token);
    localStorage.setItem("campusone_user", JSON.stringify(user));
  },
  getUser() {
    try {
      return JSON.parse(localStorage.getItem("campusone_user") || "null");
    } catch {
      return null;
    }
  },
  logout() {
    localStorage.removeItem("campusone_token");
    localStorage.removeItem("campusone_user");
    window.location.href = "index.html";
  },
  requireAuth() {
    if (!this.getToken()) window.location.href = "index.html";
  },
};

async function apiRequest(path, { method = "GET", body, auth = true } = {}) {
  const headers = { "Content-Type": "application/json" };
  if (auth && Auth.getToken()) headers.Authorization = `Bearer ${Auth.getToken()}`;

  let response;
  try {
    response = await fetch(`${API_BASE}${path}`, {
      method,
      headers,
      body: body === undefined ? undefined : JSON.stringify(body),
    });
  } catch {
    throw new Error("Couldn't reach the CampusOne server. Check the API configuration and try again.");
  }

  const text = await response.text();
  let data = null;
  try { data = text ? JSON.parse(text) : null; } catch { /* non-JSON response */ }

  if (!response.ok) {
    const detail = data?.detail;
    throw new Error(Array.isArray(detail) ? detail.map((item) => item.msg).join(", ") : detail || `Request failed (${response.status})`);
  }
  return data;
}

const Api = {
  register: (payload) => apiRequest("/auth/register", { method: "POST", body: payload, auth: false }),
  verifyEmail: (payload) => apiRequest("/auth/verify-email", { method: "POST", body: payload, auth: false }),
  resendVerification: (email) => apiRequest("/auth/resend-verification", { method: "POST", body: { email }, auth: false }),
  login: (payload) => apiRequest("/auth/login", { method: "POST", body: payload, auth: false }),
  me: () => apiRequest("/auth/me"),
  changePassword: (payload) => apiRequest("/auth/change-password", { method: "POST", body: payload }),

  adminListUsers: () => apiRequest("/admin/users"),
  adminDeleteUser: (id) => apiRequest(`/admin/users/${id}`, { method: "DELETE" }),

  listProducts: () => apiRequest("/products", { auth: false }),
  createProduct: (payload) => apiRequest("/products", { method: "POST", body: payload }),
  updateProductStatus: (id, status) => apiRequest(`/products/${id}/status`, { method: "PATCH", body: { status } }),

  myItems: () => apiRequest("/lost-found/items"),
  createItem: (payload) => apiRequest("/lost-found/items", { method: "POST", body: payload }),
  myMatches: () => apiRequest("/lost-found/matches"),
  requestVerification: (id) => apiRequest(`/lost-found/items/${id}/verification-request`, { method: "POST" }),

  getChatMessages: (roomName = "general") => apiRequest(`/chat/${encodeURIComponent(roomName)}`),
  postChatMessage: (message, roomName = "general") => apiRequest("/chat", { method: "POST", body: { room_name: roomName, message } }),
  connectChatSocket: (roomName = "general") => {
    const socketBase = API_BASE.replace(/^http/, "ws");
    const token = Auth.getToken();
    return new WebSocket(`${socketBase}/chat/ws/${encodeURIComponent(roomName)}?token=${encodeURIComponent(token || "")}`);
  },
};

function avatarUrl(seed) {
  return `https://api.dicebear.com/7.x/thumbs/svg?seed=${encodeURIComponent(seed)}&backgroundColor=C9962C`;
}

function timeAgo(dateStr) {
  const seconds = Math.max(0, Math.floor((Date.now() - new Date(dateStr).getTime()) / 1000));
  if (seconds < 60) return "just now";
  if (seconds < 3600) return `${Math.floor(seconds / 60)}m ago`;
  if (seconds < 86400) return `${Math.floor(seconds / 3600)}h ago`;
  return `${Math.floor(seconds / 86400)}d ago`;
}

function escapeHtml(value) {
  const div = document.createElement("div");
  div.textContent = String(value ?? "");
  return div.innerHTML;
}

window.Auth = Auth;
window.Api = Api;
window.avatarUrl = avatarUrl;
window.timeAgo = timeAgo;
window.escapeHtml = escapeHtml;

export { Auth, Api, avatarUrl, timeAgo, escapeHtml };

