/* CampusOne application UI, backed by the current FastAPI routes. */
Auth.requireAuth();

let currentUser = Auth.getUser();
let products = [];
let communityPollTimer = null;
const CATEGORIES = ["Books", "Hostel Items", "Electronics", "Cycles & Mobility", "Clothing & Accessories", "Other"];

function initUser() {
  if (!currentUser) return;
  document.getElementById("sidebar-name").textContent = currentUser.full_name.split(" ")[0];
  document.getElementById("sidebar-branch").textContent = currentUser.branch;
  document.getElementById("sidebar-avatar").src = avatarUrl(currentUser.email);
  if (currentUser.role === "admin") {
    const navAdmin = document.getElementById("nav-admin");
    if (navAdmin) navAdmin.classList.remove("hidden");
  }
}

function showView(view) {
  ["marketplace", "lostfound", "community", "admin"].forEach((name) => {
    const el = document.getElementById(`view-${name}`);
    if (el) el.classList.toggle("hidden", name !== view);
  });
  document.querySelectorAll(".nav-item[data-view]").forEach((element) => {
    element.classList.toggle("active", element.dataset.view === view);
  });
  clearInterval(communityPollTimer);
  if (view === "marketplace") loadProducts();
  if (view === "lostfound") loadMyItems();
  if (view === "community") {
    loadCommunityMessages();
    communityPollTimer = setInterval(loadCommunityMessages, 5000);
  }
  if (view === "admin") loadAdminUsers();
}

function openModal(id) { document.getElementById(id).classList.remove("hidden"); }
function closeModal(id) { document.getElementById(id).classList.add("hidden"); }

function populateCategories() {
  ["market-category", "cp-category"].forEach((id) => {
    const select = document.getElementById(id);
    const includeAll = id === "market-category";
    select.innerHTML = includeAll ? '<option value="">All categories</option>' : "";
    CATEGORIES.forEach((category) => {
      const option = document.createElement("option");
      option.value = category;
      option.textContent = category;
      select.appendChild(option);
    });
  });
}

let searchDebounce;
function debouncedLoadProducts() {
  clearTimeout(searchDebounce);
  searchDebounce = setTimeout(renderProducts, 200);
}

async function loadProducts() {
  const grid = document.getElementById("market-grid");
  grid.innerHTML = '<div class="empty-state">Loading listings…</div>';
  try {
    products = await Api.listProducts();
    renderProducts();
  } catch (error) {
    grid.innerHTML = `<div class="empty-state"><h3>Couldn't load listings</h3><p>${escapeHtml(error.message)}</p></div>`;
  }
}

function renderProducts() {
  const grid = document.getElementById("market-grid");
  const search = document.getElementById("market-search").value.trim().toLowerCase();
  const category = document.getElementById("market-category").value;
  const filtered = products.filter((product) => {
    const haystack = `${product.title} ${product.description} ${product.category}`.toLowerCase();
    return (!search || haystack.includes(search)) && (!category || product.category === category);
  });
  grid.innerHTML = filtered.length
    ? filtered.map(renderProductCard).join("")
    : '<div class="empty-state"><h3>Nothing pinned yet</h3><p>Be the first to list an item.</p></div>';
}

function statusTag(status) {
  const labels = { available: "Available", sold: "Sold" };
  const classes = { available: "tag-sage", sold: "tag-rust" };
  return `<span class="tag ${classes[status] || "tag-muted"}">${labels[status] || escapeHtml(status)}</span>`;
}

function renderProductCard(product) {
  return `<div class="pin-card" onclick="openProductDetail(${product.id})" style="cursor:pointer;">
    <div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:8px;">
      <span class="tag tag-navy">${escapeHtml(product.category)}</span>${statusTag(product.status)}
    </div>
    <h3 style="font-size:17px;margin-bottom:4px;">${escapeHtml(product.title)}</h3>
    <p style="font-size:13px;color:var(--ink-soft);margin:0 0 12px;max-height:38px;overflow:hidden;">${escapeHtml(product.description)}</p>
    <div style="display:flex;justify-content:space-between;align-items:center;">
      <span class="mono" style="font-weight:600;font-size:16px;color:var(--navy-900);">₹${product.price}${product.negotiable ? ' <span style="font-weight:400;font-size:11px;color:var(--ink-soft);">(negotiable)</span>' : ""}</span>
      <span style="font-size:11.5px;color:var(--ink-soft);">${escapeHtml(product.seller_name)} · ${escapeHtml(product.seller_branch)}</span>
    </div>
  </div>`;
}

function openCreateProductModal() {
  document.getElementById("create-product-alert").innerHTML = "";
  document.getElementById("create-product-form").reset();
  openModal("modal-create-product");
}

document.getElementById("create-product-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  try {
    await Api.createProduct({
      title: document.getElementById("cp-title").value.trim(),
      description: document.getElementById("cp-description").value.trim(),
      category: document.getElementById("cp-category").value,
      price: Number(document.getElementById("cp-price").value),
      negotiable: document.getElementById("cp-negotiable").checked,
    });
    closeModal("modal-create-product");
    await loadProducts();
  } catch (error) {
    document.getElementById("create-product-alert").innerHTML = `<div class="alert alert-error">${escapeHtml(error.message)}</div>`;
  }
});

function openProductDetail(id) {
  const product = products.find((item) => item.id === id);
  if (!product) return;
  const isOwner = product.seller_id === currentUser.id;
  document.getElementById("product-detail-body").innerHTML = `
    <div style="display:flex;justify-content:space-between;align-items:flex-start;"> <span class="tag tag-navy">${escapeHtml(product.category)}</span>${statusTag(product.status)} </div>
    <h2 style="margin-top:12px;">${escapeHtml(product.title)}</h2>
    <p style="color:var(--ink-soft);font-size:14px;">${escapeHtml(product.description)}</p>
    <div class="mono" style="font-size:22px;font-weight:600;color:var(--navy-900);margin:10px 0;">₹${product.price}${product.negotiable ? " (negotiable)" : ""}</div>
    <div style="font-size:13px;color:var(--ink-soft);margin-bottom:16px;">Seller: <strong>${escapeHtml(product.seller_name)}</strong> · ${escapeHtml(product.seller_branch)}</div>
    ${isOwner && product.status === "available" ? `<button class="btn btn-danger btn-sm" onclick="markSold(${product.id})">Mark as sold</button>` : ""}
  `;
  openModal("modal-product-detail");
}

async function markSold(id) {
  if (!confirm("Mark this item as sold?")) return;
  try {
    await Api.updateProductStatus(id, "sold");
    closeModal("modal-product-detail");
    await loadProducts();
  } catch (error) {
    alert(error.message);
  }
}

function switchLfTab(tab) {
  document.getElementById("lf-tab-items").classList.toggle("active", tab === "items");
  document.getElementById("lf-tab-matches").classList.toggle("active", tab === "matches");
  document.getElementById("lf-items-panel").classList.toggle("hidden", tab !== "items");
  document.getElementById("lf-matches-panel").classList.toggle("hidden", tab !== "matches");
  if (tab === "items") loadMyItems(); else loadMyMatches();
}

async function loadMyItems() {
  const panel = document.getElementById("lf-items-panel");
  panel.innerHTML = '<div class="empty-state">Loading…</div>';
  try {
    const items = await Api.myItems();
    panel.innerHTML = items.length ? items.map(renderItemCard).join("") : '<div class="empty-state"><h3>No reports yet</h3><p>Lost or found something? Report it and we will look for matches.</p></div>';
  } catch (error) {
    panel.innerHTML = `<div class="empty-state">${escapeHtml(error.message)}</div>`;
  }
}

function renderItemCard(item) {
  return `<div class="pin-card">
    <div style="display:flex;justify-content:space-between;margin-bottom:8px;">
      <span class="tag ${item.kind === "lost" ? "tag-rust" : "tag-sage"}">${escapeHtml(item.kind)}</span>
      <span class="tag tag-muted">${escapeHtml(item.status)}</span>
    </div>
    <h3 style="font-size:16px;">${escapeHtml(item.title)}</h3>
    <p style="font-size:13px;color:var(--ink-soft);margin:0 0 10px;">${escapeHtml(item.description)}</p>
    <div style="font-size:12px;color:var(--ink-soft);">📍 ${escapeHtml(item.location)}</div>
    ${item.status === "open" ? `<button class="btn btn-ghost btn-sm" style="margin-top:12px;" onclick="requestVerification(${item.id})">Request desk verification</button>` : ""}
  </div>`;
}

async function requestVerification(itemId) {
  try {
    const result = await Api.requestVerification(itemId);
    alert(`Show this one-time verification code at the desk: ${result.verification_code}`);
    await loadMyItems();
  } catch (error) {
    alert(error.message);
  }
}

async function loadMyMatches() {
  const panel = document.getElementById("lf-matches-panel");
  panel.innerHTML = '<div class="empty-state">Loading…</div>';
  try {
    const matches = await Api.myMatches();
    panel.innerHTML = matches.length ? matches.map((match) => `<div class="pin-card"><span class="tag tag-gold">Match · ${Math.round(match.score * 100)}%</span><h3 style="margin-top:12px;">Possible match</h3><p style="font-size:13px;color:var(--ink-soft);">Report #${match.source_item_id} is similar to report #${match.candidate_item_id}. Status: ${escapeHtml(match.status)}.</p></div>`).join("") : '<div class="empty-state"><h3>No matches yet</h3><p>Likely matches appear here automatically.</p></div>';
  } catch (error) {
    panel.innerHTML = `<div class="empty-state">${escapeHtml(error.message)}</div>`;
  }
}

function openCreateItemModal() {
  document.getElementById("create-item-alert").innerHTML = "";
  document.getElementById("create-item-form").reset();
  openModal("modal-create-item");
}

document.getElementById("create-item-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  try {
    await Api.createItem({
      kind: document.getElementById("ci-type").value.toLowerCase(),
      title: document.getElementById("ci-name").value.trim(),
      description: document.getElementById("ci-description").value.trim(),
      location: document.getElementById("ci-location").value.trim(),
    });
    closeModal("modal-create-item");
    switchLfTab("items");
  } catch (error) {
    document.getElementById("create-item-alert").innerHTML = `<div class="alert alert-error">${escapeHtml(error.message)}</div>`;
  }
});

async function loadCommunityMessages() {
  const element = document.getElementById("community-messages");
  try {
    const messages = await Api.getChatMessages();
    element.innerHTML = messages.map((message) => {
      const isMine = (message.author_id && message.author_id === currentUser.id) ||
        message.display_name.startsWith(currentUser.full_name.split(" ")[0] + " (");
      return `<div class="chat-bubble ${isMine ? "mine" : "theirs"}"><div style="font-family:var(--font-mono);font-size:10px;opacity:.75;margin-bottom:3px;">${escapeHtml(message.display_name)}</div>${escapeHtml(message.message)}<div class="chat-meta">${timeAgo(message.created_at)}</div></div>`;
    }).join("");
    element.scrollTop = element.scrollHeight;
  } catch (error) {
    element.innerHTML = `<div class="empty-state">${escapeHtml(error.message)}</div>`;
  }
}

document.getElementById("community-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const input = document.getElementById("community-input");
  try {
    await Api.postChatMessage(input.value.trim());
    input.value = "";
    await loadCommunityMessages();
  } catch (error) {
    alert(error.message);
  }
});

async function loadAdminUsers() {
  const tbody = document.getElementById("admin-user-list");
  if (!tbody) return;
  tbody.innerHTML = '<tr><td colspan="7" class="empty-state">Loading campus users…</td></tr>';
  try {
    const users = await Api.adminListUsers();
    tbody.innerHTML = users.length ? users.map((user) => `
      <tr>
        <td class="mono">#${user.id}</td>
        <td><strong>${escapeHtml(user.full_name)}</strong></td>
        <td>${escapeHtml(user.email)}</td>
        <td class="mono">${escapeHtml(user.scholar_id)}</td>
        <td>${escapeHtml(user.branch)}</td>
        <td><span class="tag ${user.role === 'admin' ? 'tag-gold' : 'tag-navy'}">${escapeHtml(user.role)}</span></td>
        <td>
          ${user.id === currentUser.id
            ? '<span style="font-size:12px;color:var(--ink-soft);">(You)</span>'
            : `<button class="btn btn-danger btn-sm" onclick="deleteUser(${user.id}, '${escapeHtml(user.full_name)}')">Delete</button>`
          }
        </td>
      </tr>
    `).join("") : '<tr><td colspan="7" class="empty-state">No users found.</td></tr>';
  } catch (error) {
    tbody.innerHTML = `<tr><td colspan="7" class="empty-state">${escapeHtml(error.message)}</td></tr>`;
  }
}

async function deleteUser(userId, userName) {
  if (!confirm(`Are you sure you want to delete user ${userName || '#' + userId}? This action cannot be undone.`)) return;
  try {
    await Api.adminDeleteUser(userId);
    await loadAdminUsers();
  } catch (error) {
    alert(error.message);
  }
}

function openChangePasswordModal() {
  document.getElementById("change-password-alert").innerHTML = "";
  document.getElementById("change-password-form").reset();
  openModal("modal-change-password");
}

document.getElementById("change-password-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const currentPassword = document.getElementById("cp-current").value;
  const newPassword = document.getElementById("cp-new").value;
  const confirmPassword = document.getElementById("cp-confirm").value;

  if (newPassword !== confirmPassword) {
    document.getElementById("change-password-alert").innerHTML = '<div class="alert alert-error">New passwords do not match.</div>';
    return;
  }

  try {
    await Api.changePassword({
      current_password: currentPassword,
      new_password: newPassword,
    });
    alert("Password updated successfully!");
    closeModal("modal-change-password");
  } catch (error) {
    document.getElementById("change-password-alert").innerHTML = `<div class="alert alert-error">${escapeHtml(error.message)}</div>`;
  }
});

// Bind UI handlers to window for module script compatibility
Object.assign(window, {
  showView,
  openModal,
  closeModal,
  populateCategories,
  debouncedLoadProducts,
  loadProducts,
  openCreateProductModal,
  openProductDetail,
  markSold,
  switchLfTab,
  loadMyItems,
  requestVerification,
  loadMyMatches,
  openCreateItemModal,
  loadCommunityMessages,
  loadAdminUsers,
  deleteUser,
  openChangePasswordModal,
});

async function start() {
  try {
    currentUser = await Api.me();
    Auth.setSession(Auth.getToken(), currentUser);
  } catch {
    Auth.logout();
    return;
  }
  initUser();
  populateCategories();
  loadProducts();
}
start();


