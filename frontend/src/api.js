const API_URL = import.meta.env.VITE_API_URL ?? 'http://localhost:8000'

async function request(path, { token, ...options } = {}) {
  const headers = {
    'Content-Type': 'application/json',
    ...(options.headers ?? {}),
  }

  if (token) {
    headers.Authorization = `Bearer ${token}`
  }

  const response = await fetch(`${API_URL}${path}`, {
    ...options,
    headers,
  })

  const payload = await response.json().catch(() => ({}))
  if (!response.ok) {
    throw new Error(payload?.detail || 'Request failed')
  }

  return payload
}

export const api = {
  register: (body) => request('/api/auth/register', { method: 'POST', body: JSON.stringify(body) }),
  verifyEmail: (body) => request('/api/auth/verify-email', { method: 'POST', body: JSON.stringify(body) }),
  resendVerification: (email) => request('/api/auth/resend-verification', { method: 'POST', body: JSON.stringify({ email }) }),
  login: (body) => request('/api/auth/login', { method: 'POST', body: JSON.stringify(body) }),
  me: (token) => request('/api/auth/me', { token }),
  listProducts: () => request('/api/products'),
  createProduct: (token, body) => request('/api/products', { token, method: 'POST', body: JSON.stringify(body) }),
  updateProductStatus: (token, productId, status) =>
    request(`/api/products/${productId}/status`, {
      token,
      method: 'PATCH',
      body: JSON.stringify({ status }),
    }),
  listLostFound: (token) => request('/api/lost-found/items', { token }),
  listMatches: (token) => request('/api/lost-found/matches', { token }),
  createLostFound: (token, body) => request('/api/lost-found/items', { token, method: 'POST', body: JSON.stringify(body) }),
  requestLostFoundVerification: (token, itemId) =>
    request(`/api/lost-found/items/${itemId}/verification-request`, {
      token,
      method: 'POST',
    }),
  verifyLostFound: (token, itemId, body) =>
    request(`/api/lost-found/items/${itemId}/verify`, {
      token,
      method: 'POST',
      body: JSON.stringify(body),
    }),
  resolveLostFound: (token, itemId) =>
    request(`/api/lost-found/items/${itemId}/resolve`, {
      token,
      method: 'POST',
      body: JSON.stringify({ status: 'resolved' }),
    }),
  closeLostFound: (token, itemId) =>
    request(`/api/lost-found/items/${itemId}/close`, {
      token,
      method: 'POST',
    }),
  listChatMessages: (token, roomName) => request(`/api/chat/${roomName}`, { token }),
  sendChatMessage: (token, body) => request('/api/chat', { token, method: 'POST', body: JSON.stringify(body) }),
}
