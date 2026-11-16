/* CampusOne application UI, backed by the current FastAPI routes. */
import { Auth, Api, avatarUrl, timeAgo, escapeHtml } from './api.js';
Auth.requireAuth();

let currentUser = Auth.getUser();
let products = [];
let communityPollTimer = null;
let communitySocket = null;
let communitySocketCloseRequested = false;
let communityMessages = [];
let activeChatRoom = "general";
let placementQuestions = [];
let placementMetadata = null;
let placementCurriculum = null;
let selectedPlacementCategory = null;
let selectedPlacementTopic = null;
let placementQuizState = null;
const CATEGORIES = ["Books", "Hostel Items", "Electronics", "Cycles & Mobility", "Clothing & Accessories", "Other"];

function initUser() {
  if (!currentUser) return;
  document.getElementById("sidebar-name").textContent = currentUser.full_name.split(" ")[0];
  document.getElementById("sidebar-branch").textContent = currentUser.branch;
  document.getElementById("sidebar-avatar").src = avatarUrl(currentUser.email);
  document.getElementById("profile-full-name").textContent = currentUser.full_name;
  document.getElementById("profile-email").textContent = currentUser.email;
  document.getElementById("profile-scholar").textContent = currentUser.scholar_id;
  document.getElementById("profile-branch").textContent = currentUser.branch;
  if (currentUser.role === "admin") {
    const navAdmin = document.getElementById("nav-admin");
    if (navAdmin) navAdmin.classList.remove("hidden");
  }
}

function toggleProfile() {
  const menu = document.getElementById('profile-menu');
  const button = document.querySelector('.app-profile');
  const open = menu.classList.toggle('hidden') === false;
  button.setAttribute('aria-expanded', String(open));

}

function showView(view) {
  ["home", "services", "noticeboard", "marketplace", "lostfound", "community", "placement", "admin"].forEach((name) => {
    const el = document.getElementById(`view-${name}`);
    if (el) el.classList.toggle("hidden", name !== view);
  });
  document.querySelectorAll(".nav-item[data-view]").forEach((element) => {
    element.classList.toggle("active", element.dataset.view === view || (element.dataset.view === 'services' && ['marketplace', 'lostfound', 'community'].includes(view)));
  });
  document.querySelectorAll(".module-card[data-view]").forEach((element) => {
    element.classList.toggle("active", element.dataset.view === view);
  });
  document.querySelectorAll(".app-page-nav [data-view]").forEach((element) => {
    element.classList.toggle("active", element.dataset.view === view);
  });
  stopCommunityChat();
  if (view === "marketplace") loadProducts();
  if (view === "lostfound") loadMyItems();
  if (view === "community") {
    startCommunityChat();
  }
  if (view === "placement") loadPlacementModule();
  if (view === "admin") loadAdminUsers();
}

async function loadPlacementModule() {
  try {
    if (!placementCurriculum) placementCurriculum = await Api.placementCurriculum();
    renderPlacementCategories();
    showPlacementCategories();
  } catch (error) {
    document.getElementById("placement-category-panel").innerHTML = `<div class="empty-state">${escapeHtml(error.message)}</div>`;
  }
}

function renderPlacementCategories() {
  const panel = document.getElementById("placement-category-panel");
  panel.innerHTML = placementCurriculum.categories.map((category, index) => `
    <button class="module-card" style="text-align:left;" onclick="showPlacementTopics(${index})">
      <span class="module-card-icon" aria-hidden="true">${["◈", "⌘", "◇", "Aa", "∑"][index] || "•"}</span>
      <span><strong>${escapeHtml(category.category)}</strong><small>${escapeHtml(category.description)}</small><small>${category.subjects.length} subject${category.subjects.length === 1 ? "" : "s"} · ${category.subjects.reduce((count, subject) => count + subject.topics.length, 0)} topics</small></span>
      <span class="module-card-arrow" aria-hidden="true">↗</span>
    </button>`).join("");
}

function showPlacementCategories() {
  selectedPlacementCategory = null;
  selectedPlacementTopic = null;
  document.getElementById("placement-breadcrumb").textContent = "Placement Prep / Categories";
  document.getElementById("placement-category-panel").classList.remove("hidden");
  document.getElementById("placement-topic-panel").classList.add("hidden");
  document.getElementById("placement-resource-panel").classList.add("hidden");
}

function showPlacementTopics(categoryIndex) {
  if (categoryIndex === undefined) return showPlacementCategories();
  selectedPlacementCategory = placementCurriculum.categories[categoryIndex];
  document.getElementById("placement-breadcrumb").textContent = `Placement Prep / ${selectedPlacementCategory.category} / Topics`;
  document.getElementById("placement-category-panel").classList.add("hidden");
  const panel = document.getElementById("placement-topic-panel");
  panel.classList.remove("hidden");
  panel.innerHTML = selectedPlacementCategory.subjects.flatMap((subject) => subject.topics.map((topic) => `
    <button class="module-card" style="text-align:left;" onclick="showPlacementResources('${escapeHtml(topic).replaceAll("'", "&#39;")}', '${escapeHtml(subject.name).replaceAll("'", "&#39;")}')">
      <span class="module-card-icon" aria-hidden="true">▧</span>
      <span><strong>${escapeHtml(topic)}</strong><small>${escapeHtml(subject.name)}</small><small>Open syllabus, cheat sheet, quiz, and Top 50 questions</small></span>
      <span class="module-card-arrow" aria-hidden="true">↗</span>
    </button>`)).join("");
  panel.innerHTML = panel.innerHTML || '<div class="empty-state">No topics available.</div>';
}

function showPlacementResources(topic, subject) {
  selectedPlacementTopic = { topic, subject };
  document.getElementById("placement-breadcrumb").textContent = `Placement Prep / ${selectedPlacementCategory.category} / ${topic}`;
  document.getElementById("placement-topic-panel").classList.add("hidden");
  const panel = document.getElementById("placement-resource-panel");
  panel.classList.remove("hidden");
  document.getElementById("placement-resource-content").classList.add("hidden");
  document.getElementById("placement-resource-cards").innerHTML = `
    <button class="module-card" style="text-align:left;" onclick="openPlacementResource('syllabus')"><span class="module-card-icon">▤</span><span><strong>Detailed syllabus</strong><small>What to study in ${escapeHtml(topic)}</small></span><span class="module-card-arrow">↗</span></button>
    <button class="module-card" style="text-align:left;" onclick="openPlacementResource('cheatsheet')"><span class="module-card-icon">⌑</span><span><strong>Cheat sheet</strong><small>Formulas, patterns, and shortcuts</small></span><span class="module-card-arrow">↗</span></button>
    <button class="module-card" style="text-align:left;" onclick="openPlacementResource('quiz')"><span class="module-card-icon">?</span><span><strong>Quiz &amp; practice</strong><small>Practice questions for this topic</small></span><span class="module-card-arrow">↗</span></button>
    <button class="module-card" style="text-align:left;" onclick="openPlacementResource('top')"><span class="module-card-icon">★</span><span><strong>Top 50 questions</strong><small>Frequently asked ${escapeHtml(topic)} questions</small></span><span class="module-card-arrow">↗</span></button>`;
}

async function openPlacementResource(resource) {
  const content = document.getElementById("placement-resource-content");
  content.classList.remove("hidden");
  content.innerHTML = '<div class="empty-state">Loading topic resources…</div>';
  const { topic, subject } = selectedPlacementTopic;
  if (resource === "syllabus") {
    content.innerHTML = `<article class="pin-card"><div class="eyebrow">${escapeHtml(subject)}</div><h2>${escapeHtml(topic)} syllabus</h2><p>Study the definitions, standard patterns, formulas, edge cases, and company-style variations for this topic. Revise the cheat sheet, then complete the quiz and Top 50 set.</p><button class="btn btn-ghost btn-sm" onclick="showPlacementTopics(placementCurriculum.categories.indexOf(selectedPlacementCategory))">Back to topics</button></article>`;
    return;
  }
  if (resource === "cheatsheet") {
    const sheets = placementCurriculum.cheatsheets.filter((sheet) => sheet.category === selectedPlacementCategory.category || sheet.title.toLowerCase().includes(topic.toLowerCase().split(" ")[0]));
    content.innerHTML = `<div class="grid">${(sheets.length ? sheets : [{ category: selectedPlacementCategory.category, title: `${topic} quick sheet`, items: ["Review core definitions and formulas.", "Practice the common patterns before attempting timed questions.", "Track mistakes and mark this topic for revision."] }]).map((sheet) => `<article class="pin-card"><div class="eyebrow">${escapeHtml(sheet.category)}</div><h3>${escapeHtml(sheet.title)}</h3><ul>${sheet.items.map((item) => `<li>${escapeHtml(item)}</li>`).join("")}</ul></article>`).join("")}</div>`;
    return;
  }
  if (resource === "quiz") {
    await loadTopicQuestions(topic, content, false);
    return;
  }
  await loadTopicQuestions(topic, content, true);
}

function placementQuery() {
  const params = new URLSearchParams();
  [["pillar", "placement-pillar"], ["topic", "placement-topic"], ["difficulty", "placement-difficulty"], ["company", "placement-company"], ["format", "placement-format"]].forEach(([key, id]) => {
    const value = document.getElementById(id).value;
    if (value) params.set(key, value);
  });
  return params.toString() ? `?${params}` : "";
}

async function loadTopicQuestions(topic, content, topOnly) {
  try {
    const questions = topOnly
      ? await Api.placementTopQuestions(topic)
      : await Api.placementQuizQuestions(topic);
    placementQuestions = questions;
    if (!questions.length) {
      content.innerHTML = '<div class="empty-state"><h3>No questions available yet</h3><p>This topic is ready for content to be added.</p></div>';
      return;
    }
    if (topOnly) {
      content.innerHTML = `<div class="placement-resource-heading"><strong>${escapeHtml(topic)} · Top 50 Questions</strong><span>${questions.length}/50 questions</span></div><div class="placement-top-list">${questions.map(renderTopPlacementQuestion).join("")}</div>`;
      return;
    }
    placementQuizState = { topic, questions, index: 0, answers: {}, score: 0, submitted: false };
    renderPlacementQuiz(content);
  } catch (error) {
    content.innerHTML = `<div class="empty-state">${escapeHtml(error.message)}</div>`;
  }
}

function renderTopPlacementQuestion(question) {
  return `<article class="placement-top-question">
    <div class="placement-top-number">Top #${question.top_rank}</div>
    <div class="hint">${escapeHtml(question.difficulty)} · ${escapeHtml(question.topic)}</div>
    <h3>${escapeHtml(question.prompt)}</h3>
    ${question.options?.length ? `<ul>${question.options.map((option) => `<li>${escapeHtml(option)}</li>`).join("")}</ul>` : ""}
    <p class="placement-answer"><strong>Answer:</strong> ${escapeHtml(question.correct_answer)}</p>
    ${question.explanation ? `<p class="placement-explanation">${escapeHtml(question.explanation)}</p>` : ""}
  </article>`;
}

function renderPlacementQuiz(content) {
  const state = placementQuizState;
  const question = state.questions[state.index];
  const selected = state.answers[question.id];
  const isLast = state.index === state.questions.length - 1;
  content.innerHTML = `<section class="placement-quiz">
    <header class="placement-quiz-header">
      <div><div class="eyebrow">Quiz · ${escapeHtml(state.topic)}</div><h2>Question ${state.index + 1} of ${state.questions.length}</h2></div>
      <div class="placement-quiz-progress"><span style="width:${((state.index + 1) / state.questions.length) * 100}%"></span></div>
    </header>
    <div class="placement-quiz-body">
      <div class="hint">${escapeHtml(question.difficulty)} · ${question.format === "mcq" ? "Multiple choice" : "Coding question"}</div>
      <h3>${escapeHtml(question.prompt)}</h3>
      ${question.options?.length ? `<div class="placement-quiz-options">${question.options.map((option) => `<label class="${selected === option ? "selected" : ""}"><input type="radio" name="placement-quiz-answer" value="${escapeHtml(option)}" ${selected === option ? "checked" : ""} onchange="selectPlacementQuizAnswer(this.value)"><span>${escapeHtml(option)}</span></label>`).join("")}</div>` : `<textarea class="placement-quiz-textarea" onchange="selectPlacementQuizAnswer(this.value)" placeholder="Write your answer or approach…">${escapeHtml(selected || "")}</textarea>`}
    </div>
    <footer class="placement-quiz-footer"><span>${Object.keys(state.answers).length} answered</span><div><button class="btn btn-ghost btn-sm" onclick="movePlacementQuiz(-1)" ${state.index === 0 ? "disabled" : ""}>Previous</button><button class="btn btn-primary btn-sm" onclick="${isLast ? "finishPlacementQuiz()" : "movePlacementQuiz(1)"}">${isLast ? "Submit quiz" : "Next question"}</button></div></footer>
  </section>`;
}

function selectPlacementQuizAnswer(answer) {
  if (!placementQuizState) return;
  placementQuizState.answers[placementQuizState.questions[placementQuizState.index].id] = answer;
  renderPlacementQuiz(document.getElementById("placement-resource-content"));
}

function movePlacementQuiz(direction) {
  if (!placementQuizState) return;
  placementQuizState.index = Math.max(0, Math.min(placementQuizState.questions.length - 1, placementQuizState.index + direction));
  renderPlacementQuiz(document.getElementById("placement-resource-content"));
}

async function finishPlacementQuiz() {
  const state = placementQuizState;
  if (!state || state.submitted) return;
  state.submitted = true;
  state.score = state.questions.reduce((score, question) => score + (state.answers[question.id]?.trim().toLowerCase() === question.correct_answer.trim().toLowerCase() ? 1 : 0), 0);
  for (const question of state.questions) {
    const answer = state.answers[question.id];
    if (answer) await Api.placementAnswer(question.id, answer);
  }
  const content = document.getElementById("placement-resource-content");
  content.innerHTML = `<section class="placement-quiz-result"><div class="eyebrow">Quiz complete</div><h2>${state.score} / ${state.questions.length}</h2><p>${state.score === state.questions.length ? "Excellent work." : "Review the answers and retry this topic to improve your score."}</p><button class="btn btn-primary btn-sm" onclick="openPlacementResource('quiz')">Retry quiz</button></section>`;
  await loadPlacementReadiness();
}

async function loadPlacementQuestions() {
  const grid = document.getElementById("placement-question-grid");
  if (!grid) return;
  grid.innerHTML = '<div class="empty-state">Loading practice questions…</div>';
  try {
    placementQuestions = await Api.placementQuestions(placementQuery());
    grid.innerHTML = placementQuestions.length ? placementQuestions.map(renderPlacementQuestion).join("") : '<div class="empty-state"><h3>No matching questions</h3><p>Try clearing one of the filters.</p></div>';
  } catch (error) {
    grid.innerHTML = `<div class="empty-state">${escapeHtml(error.message)}</div>`;
  }
}

function renderPlacementQuestion(question) {
  const options = question.format === "mcq" ? `<div class="placement-options">${question.options.map((option) => `<button class="btn btn-ghost btn-sm" onclick="answerPlacementQuestion(${question.id}, '${escapeHtml(option).replaceAll("'", "&#39;")}')">${escapeHtml(option)}</button>`).join("")}</div>` : `<pre class="placement-code">${escapeHtml(question.sample_input || "Write your solution using the prompt and constraints.")}</pre><details><summary>Hints &amp; optimal approach</summary><p>${escapeHtml((question.hints || []).join(" "))}</p><p>${escapeHtml(question.optimal_approach || "")}</p><p class="hint">${escapeHtml(question.time_complexity || "")} time · ${escapeHtml(question.space_complexity || "")} space</p></details>`;
  return `<article class="pin-card placement-question" id="placement-question-${question.id}">
    <div style="display:flex;justify-content:space-between;gap:8px;"><span class="tag tag-navy">${question.top_rank ? `Top #${question.top_rank}` : escapeHtml(question.pillar)}</span><span class="tag tag-muted">${escapeHtml(question.difficulty)}</span></div>
    <div class="hint" style="margin-top:10px;">${escapeHtml(question.topic)} · ${question.format === "mcq" ? "MCQ" : "Coding"}</div>
    <h3>${escapeHtml(question.prompt)}</h3>${question.constraints ? `<p class="hint">${escapeHtml(question.constraints)}</p>` : ""}${options}
    <div style="display:flex;gap:8px;margin-top:12px;align-items:center;"><button class="btn btn-ghost btn-sm" onclick="togglePlacementBookmark(${question.id}, ${!question.bookmarked})">${question.bookmarked ? "★ Bookmarked" : "☆ Bookmark"}</button><select onchange="setPlacementStatus(${question.id}, this.value)"><option value="unsolved" ${question.status === "unsolved" ? "selected" : ""}>Unsolved</option><option value="needs_revision" ${question.status === "needs_revision" ? "selected" : ""}>Needs revision</option><option value="solved" ${question.status === "solved" ? "selected" : ""}>Solved</option></select></div>
    <div class="placement-feedback" role="status"></div>
  </article>`;
}

async function answerPlacementQuestion(id, answer) {
  const card = document.getElementById(`placement-question-${id}`);
  try {
    const result = await Api.placementAnswer(id, answer);
    card.querySelector(".placement-feedback").innerHTML = `<div class="alert ${result.correct ? "alert-success" : "alert-error"}">${result.correct ? "Correct!" : `Not quite. Correct answer: ${escapeHtml(result.correct_answer)}`}<br>${escapeHtml(result.explanation || "")}</div>`;
    if (selectedPlacementTopic) {
      await loadTopicQuestions(selectedPlacementTopic.topic, document.getElementById("placement-resource-content"), false);
    } else {
      await loadPlacementQuestions();
    }
    await loadPlacementReadiness();
  } catch (error) { card.querySelector(".placement-feedback").textContent = error.message; }
}

async function togglePlacementBookmark(id, bookmarked) {
  await Api.placementProgress(id, { status: placementQuestions.find((item) => item.id === id)?.status || "unsolved", bookmarked });
  await loadPlacementQuestions();
}

async function setPlacementStatus(id, status) {
  await Api.placementProgress(id, { status });
  await loadPlacementReadiness();
}

async function loadPlacementReadiness() {
  const panel = document.getElementById("placement-readiness");
  if (!panel) return;
  const data = await Api.placementReadiness();
  panel.innerHTML = Object.entries(data.summary).map(([pillar, value]) => `<div class="pin-card"><div class="eyebrow">${escapeHtml(pillar)}</div><h3>${value.solved}/${value.total} solved</h3><p class="hint">${value.needs_revision} need revision · ${value.unsolved} unsolved</p></div>`).join("");
}

async function loadPlacementTests() {
  const panel = document.getElementById("placement-tests-panel");
  panel.classList.remove("hidden");
  panel.innerHTML = '<div class="empty-state">Loading simulators…</div>';
  const tests = await Api.placementTests();
  panel.innerHTML = tests.map((test) => `<div class="pin-card"><span class="tag tag-gold">${escapeHtml(test.company)}</span><h3>${escapeHtml(test.title)}</h3><p class="hint">${test.question_count} questions · ${test.duration_minutes} minutes · ${test.negative_marking ? "negative marking" : "no negative marking"}</p><button class="btn btn-primary btn-sm" onclick="startPlacementTest(${test.id})">Start test</button></div>`).join("") + `<div class="pin-card"><h3>Custom simulator</h3><button class="btn btn-ghost btn-sm" onclick="generateAndStartPlacementTest()">Generate balanced test</button></div>`;
}

async function startPlacementTest(id) {
  const attempt = await Api.startPlacementAttempt(id);
  const panel = document.getElementById("placement-tests-panel");
  panel.classList.remove("hidden");
  const started = Date.now();
  const deadline = started + attempt.test.duration_minutes * 60 * 1000;
  panel.innerHTML = `<article class="pin-card" style="grid-column:1/-1;"><div style="display:flex;justify-content:space-between;align-items:center;"><div><div class="eyebrow">${escapeHtml(attempt.test.title)}</div><h2>Timed assessment</h2></div><strong class="mono" id="placement-countdown"></strong></div><form id="placement-test-form">${attempt.questions.map((question, index) => `<fieldset style="border:0;border-top:1px solid var(--line);padding:18px 0;margin-top:12px;"><legend><strong>${index + 1}. ${escapeHtml(question.prompt)}</strong><div class="hint">${escapeHtml(question.pillar)} · ${escapeHtml(question.topic)} · ${escapeHtml(question.difficulty)}</div></legend>${question.options ? `<div class="placement-options">${question.options.map((option) => `<label><input type="radio" name="question-${question.id}" value="${escapeHtml(option)}"> ${escapeHtml(option)}</label>`).join("")}</div>` : `<textarea name="question-${question.id}" rows="3" placeholder="Write your approach or answer…"></textarea>`}</fieldset>`).join("")}<button class="btn btn-primary" type="submit">Submit OA</button></form></article>`;
  const countdown = panel.querySelector("#placement-countdown");
  const form = panel.querySelector("#placement-test-form");
  let submitted = false;
  const timer = setInterval(() => {
    const remaining = Math.max(0, deadline - Date.now());
    const minutes = Math.floor(remaining / 60000);
    const seconds = Math.floor((remaining % 60000) / 1000);
    countdown.textContent = `${minutes}:${String(seconds).padStart(2, "0")} remaining`;
    if (!remaining && !submitted) form.requestSubmit();
  }, 1000);
  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    if (submitted) return;
    submitted = true;
    clearInterval(timer);
    form.querySelector("button").disabled = true;
    for (const question of attempt.questions) {
      const field = form.elements[`question-${question.id}`];
      const answer = field?.value?.trim();
      if (answer) await Api.savePlacementAnswer(attempt.attempt_id, { question_id: question.id, answer, time_spent_seconds: Math.round((Date.now() - started) / 1000) });
    }
    const result = await Api.completePlacementAttempt(attempt.attempt_id);
    panel.innerHTML = `<article class="pin-card"><div class="eyebrow">OA complete</div><h2>Score: ${result.score ?? 0}/${result.total_questions}</h2><p>${result.correct_answers} correct · ${result.wrong_answers} incorrect · ${result.time_spent_seconds}s spent</p><h3>Weak topics</h3><p class="hint">${result.weak_topics?.length ? result.weak_topics.map((item) => `${escapeHtml(item.topic)} (${item.wrong_answers} wrong)`).join(" · ") : "No weak topics recorded."}</p><button class="btn btn-ghost btn-sm" onclick="loadPlacementTests()">Back to simulators</button></article>`;
  });
}

async function generateAndStartPlacementTest() {
  const test = await Api.generatePlacementTest({ company: "Campus Practice", duration_minutes: 60, questions_per_pillar: 2, negative_marking: true, section_switching: true });
  await startPlacementTest(test.id);
}

function toggleSidebar() {
  const shell = document.querySelector('.app-shell');
  const button = document.getElementById('sidebar-toggle');
  const collapsed = shell.classList.toggle('sidebar-collapsed');
  button.setAttribute('aria-pressed', String(collapsed));
  button.setAttribute('aria-expanded', String(!collapsed));
  button.setAttribute('aria-label', collapsed ? 'Show sidebar' : 'Hide sidebar');
}

function toggleTheme() {
  const shell = document.querySelector('.app-shell');
  const button = document.getElementById('theme-toggle');
  const light = shell.classList.toggle('light-theme');
  localStorage.setItem('campusone_theme', light ? 'light' : 'dark');
  button.setAttribute('aria-pressed', String(light));
  button.querySelector('.theme-icon').textContent = light ? '☾' : '☼';
  button.querySelector('.theme-label').textContent = light ? 'Dark theme' : 'Light theme';
}

function initAppTheme() {
  if (localStorage.getItem('campusone_theme') !== 'light') return;
  const shell = document.querySelector('.app-shell');
  shell.classList.add('light-theme');
  const button = document.getElementById('theme-toggle');
  button.setAttribute('aria-pressed', 'true');
  button.querySelector('.theme-icon').textContent = '☾';
  button.querySelector('.theme-label').textContent = 'Dark theme';
}

function openModal(id) { document.getElementById(id).classList.remove("hidden"); }
function closeModal(id) { document.getElementById(id).classList.add("hidden"); if (id === "modal-product-detail") stopProductChat(); }

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
  const isOwner = product.seller_id === currentUser.id;
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
    ${isOwner ? `<div style="display:flex;gap:8px;margin-top:12px;" onclick="event.stopPropagation()">
      <button class="btn btn-ghost btn-sm" onclick="openEditProductModal(${product.id})">Edit</button>
      <button class="btn btn-danger btn-sm" onclick="deleteProduct(${product.id})">Delete</button>
    </div>` : ""}
  </div>`;
}

function openCreateProductModal() {
  document.getElementById("product-modal-title").textContent = "List an item";
  document.getElementById("product-form-submit").textContent = "Post listing";
  document.getElementById("create-product-alert").innerHTML = "";
  document.getElementById("create-product-form").reset();
  document.getElementById("create-product-form").dataset.productId = "";
  openModal("modal-create-product");
}

function openEditProductModal(id) {
  const product = products.find((item) => item.id === id);
  if (!product || product.seller_id !== currentUser.id) return;

  document.getElementById("product-modal-title").textContent = "Edit listing";
  document.getElementById("product-form-submit").textContent = "Save changes";
  document.getElementById("create-product-alert").innerHTML = "";
  document.getElementById("create-product-form").dataset.productId = String(id);
  document.getElementById("cp-title").value = product.title;
  document.getElementById("cp-description").value = product.description;
  document.getElementById("cp-category").value = product.category;
  document.getElementById("cp-price").value = product.price;
  document.getElementById("cp-negotiable").checked = product.negotiable;
  openModal("modal-create-product");
}

document.getElementById("create-product-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const form = event.currentTarget;
  const productId = form.dataset.productId;
  const payload = {
    title: document.getElementById("cp-title").value.trim(),
    description: document.getElementById("cp-description").value.trim(),
    category: document.getElementById("cp-category").value,
    price: Number(document.getElementById("cp-price").value),
    negotiable: document.getElementById("cp-negotiable").checked,
  };
  try {
    if (productId) await Api.updateProduct(productId, payload);
    else await Api.createProduct(payload);
    closeModal("modal-create-product");
    form.dataset.productId = "";
    await loadProducts();
  } catch (error) {
    document.getElementById("create-product-alert").innerHTML = `<div class="alert alert-error">${escapeHtml(error.message)}</div>`;
  }
});

async function deleteProduct(id) {
  const product = products.find((item) => item.id === id);
  if (!product || product.seller_id !== currentUser.id) return;
  if (!confirm(`Delete "${product.title}"? This action cannot be undone.`)) return;

  try {
    await Api.deleteProduct(id);
    closeModal("modal-product-detail");
    await loadProducts();
  } catch (error) {
    alert(error.message);
  }
}

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

    ${isOwner ? `<div style="display:flex;gap:8px;flex-wrap:wrap;">
      ${product.status === "available" ? `<button class="btn btn-danger btn-sm" onclick="markSold(${product.id})">Mark as sold</button>` : ""}
      <button class="btn btn-ghost btn-sm" onclick="openEditProductModal(${product.id})">Edit listing</button>
      <button class="btn btn-danger btn-sm" onclick="deleteProduct(${product.id})">Delete listing</button>
    </div>` : ""}
  `;
  openModal("modal-product-detail");
  mountProductChat(product);
}

let productChat = null;
function stopProductChat() {
  if (productChat) clearInterval(productChat.timer);
  productChat = null;
}
function mountProductChat(product) {
  stopProductChat();
  const owner = product.seller_id === currentUser.id;
  const panel = document.createElement('section');
  panel.innerHTML = `<hr><h3>Product messages</h3><p class="hint">${owner ? 'Select a buyer to reply privately about this product.' : 'Chat privately with the seller about this product.'}</p><div class="product-conversations"></div><h4 class="product-chat-title"></h4><div class="chat-messages product-history" style="max-height:260px;overflow-y:auto" aria-live="polite"></div><form class="chat-input-row product-message-form"><input aria-label="Message about this product" placeholder="Write a message…" maxlength="1000" required><button class="btn btn-primary" type="submit">Send</button></form><p class="product-chat-error" role="status"></p>`;
  document.getElementById('product-detail-body').append(panel);
  const state = { product, panel, room: owner ? null : `product-${product.id}-buyer-${currentUser.id}`, timer: null, loading: false };
  productChat = state;
  const form = panel.querySelector('form');
  form.classList.toggle('hidden', owner);
  panel.querySelector('.product-chat-title').textContent = owner ? '' : `Chat with ${product.seller_name}`;
  form.addEventListener('submit', async event => {
    event.preventDefault();
    const input = form.querySelector('input');
    const text = input.value.trim();
    if (!text || !state.room) return;
    const button = form.querySelector('button');
    button.disabled = true;
    try {
      await Api.postChatMessage(text, state.room);
      input.value = '';
      await refreshProductChat(state);
    } catch (error) { panel.querySelector('.product-chat-error').textContent = error.message; }
    finally { button.disabled = false; }
  });
  refreshProductChat(state);
  state.timer = setInterval(() => {
    if (document.getElementById('modal-product-detail').classList.contains('hidden')) stopProductChat();
    else if (!document.hidden) refreshProductChat(state);
  }, 3000);
}
async function refreshProductChat(state) {
  if (state !== productChat || state.loading) return;
  state.loading = true;
  const panel = state.panel;
  try {
    if (state.product.seller_id === currentUser.id) {
      const conversations = await Api.getConversations(state.product.id);
      if (state !== productChat) return;
      const list = panel.querySelector('.product-conversations');
      list.replaceChildren();
      if (!conversations.length) list.textContent = 'No buyer messages for this product yet.';
      for (const conversation of conversations) {
        const button = document.createElement('button');
        button.type = 'button';
        button.className = 'conversation-item';
        button.textContent = `${conversation.other_user_name}: ${conversation.last_message}`;
        button.setAttribute('aria-pressed', String(state.room === conversation.room_name));
        button.addEventListener('click', () => {
          state.room = conversation.room_name;
          panel.querySelector('.product-chat-title').textContent = `Chat with ${conversation.other_user_name}`;
          panel.querySelector('form').classList.remove('hidden');
          panel.querySelector('.product-history').replaceChildren();
          refreshProductChat(state);
        });
        list.append(button);
      }
    }
    const room = state.room;
    if (room) {
      const messages = await Api.getChatMessages(room);
      if (state !== productChat || state.room !== room) return;
      const history = panel.querySelector('.product-history');
      const signature = messages.map(message => message.id).join(',');
      if (history.dataset.signature !== `${room}:${signature}`) {
        history.dataset.signature = `${room}:${signature}`;
        history.replaceChildren();
        if (!messages.length) history.textContent = 'Start the conversation about this product.';
        for (const message of messages) {
          const bubble = document.createElement('div');
          bubble.className = `chat-bubble ${message.author_id === currentUser.id ? 'mine' : 'theirs'}`;
          bubble.textContent = `${message.author_id === currentUser.id ? 'You' : message.display_name}: ${message.message}`;
          history.append(bubble);
        }
        history.scrollTop = history.scrollHeight;
      }
    }
    panel.querySelector('.product-chat-error').textContent = '';
  } catch (error) {
    if (state === productChat) panel.querySelector('.product-chat-error').textContent = error.message;
  } finally { state.loading = false; }
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

function renderCommunityMessages(messages) {
  const element = document.getElementById("community-messages");
  element.innerHTML = messages.map((message) => {
    const isMine = message.author_id === currentUser.id;
    return `<div class="chat-bubble ${isMine ? "mine" : "theirs"}"><div style="font-family:var(--font-mono);font-size:10px;opacity:.75;margin-bottom:3px;">${escapeHtml(message.display_name)}</div>${escapeHtml(message.message)}<div class="chat-meta">${timeAgo(message.created_at)}</div></div>`;
  }).join("");
  element.scrollTop = element.scrollHeight;
}

async function loadCommunityMessages() {
  try {
    communityMessages = await Api.getChatMessages(activeChatRoom);
    renderCommunityMessages(communityMessages);
  } catch (error) {
    document.getElementById("community-messages").innerHTML = `<div class="empty-state">${escapeHtml(error.message)}</div>`;
  }
}

function startCommunityFallback() {
  if (communityPollTimer || communitySocketCloseRequested) return;
  loadCommunityMessages();
  communityPollTimer = setInterval(loadCommunityMessages, 5000);
}

function startCommunityChat() {
  communitySocketCloseRequested = false;
  communityMessages = [];
  renderCommunityMessages([]);
  try {
    communitySocket = Api.connectChatSocket(activeChatRoom);
    const socket = communitySocket;
    communitySocket.onmessage = (event) => {
      if (communitySocket !== socket) return;
      const payload = JSON.parse(event.data);
      if (payload.type === "history") {
        communityMessages = payload.messages;
        renderCommunityMessages(communityMessages);
      }
      if (payload.type === "message") {
        communityMessages.push(payload.message);
        renderCommunityMessages(communityMessages);
      }
    };
    communitySocket.onerror = () => {
      if (communitySocket !== socket) return;
      startCommunityFallback();
    };
    communitySocket.onclose = () => {
      if (communitySocket !== socket) return;
      communitySocket = null;
      if (!communitySocketCloseRequested) startCommunityFallback();
    };
  } catch {
    startCommunityFallback();
  }
}

function stopCommunityChat() {
  clearInterval(communityPollTimer);
  communityPollTimer = null;
  communitySocketCloseRequested = true;
  if (communitySocket) {
    communitySocket.close();
    communitySocket = null;
  }
}

document.getElementById("community-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const input = document.getElementById("community-input");
  try {
    const message = input.value.trim();
    if (!message) return;
    if (communitySocket?.readyState === WebSocket.OPEN) {
      communitySocket.send(JSON.stringify({ message }));
    } else {
      await Api.postChatMessage(message, activeChatRoom);
      await loadCommunityMessages();
    }
    input.value = "";
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
  openEditProductModal,
  openProductDetail,
  markSold,
  deleteProduct,
  switchLfTab,
  loadMyItems,
  requestVerification,
  loadMyMatches,
  openCreateItemModal,
  loadCommunityMessages,
  loadAdminUsers,
  deleteUser,
  openChangePasswordModal,
  toggleSidebar,
  toggleTheme,
  toggleProfile,
  loadPlacementModule,
  showPlacementCategories,
  showPlacementTopics,
  showPlacementResources,
  openPlacementResource,
  selectPlacementQuizAnswer,
  movePlacementQuiz,
  finishPlacementQuiz,
  loadPlacementQuestions,
  answerPlacementQuestion,
  togglePlacementBookmark,
  setPlacementStatus,
  loadPlacementReadiness,
  loadPlacementTests,
  startPlacementTest,
  generateAndStartPlacementTest,
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
  initAppTheme();
  populateCategories();
  showView("home");
}
start();
