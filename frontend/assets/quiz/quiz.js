import { isAuthenticated, getUser, logout } from "../js/auth.js";
import { createQuiz, fetchQuizzes } from "../js/api.js";

// Require authentication before showing the quiz page.
if (!isAuthenticated()) {
  window.location.href = "../../index.html";
  throw new Error("Not authenticated");
}

const MAX_QUESTIONS = 10;

let quizzes = [];
let currentQuiz = null;

// ── DOM references ───────────────────────────────────────────────────

const listView = document.getElementById("listView");
const detailView = document.getElementById("detailView");
const quizList = document.getElementById("quizList");
const quizCount = document.getElementById("quizCount");
const quizDetail = document.getElementById("quizDetail");

const newQuizModal = document.getElementById("newQuizModal");
const newQuizOverlay = document.getElementById("newQuizOverlay");
const quizFormError = document.getElementById("quizFormError");

const topicInput = document.getElementById("topicInput");
const conceptInput = document.getElementById("conceptInput");
const difficultyInput = document.getElementById("difficultyInput");
const numQuestionsInput = document.getElementById("numQuestionsInput");
const additionalInput = document.getElementById("additionalInput");

const generateQuizBtn = document.getElementById("generateQuizBtn");
const cancelNewQuizBtn = document.getElementById("cancelNewQuizBtn");
const newQuizBtn = document.getElementById("newQuizBtn");
const backToListBtn = document.getElementById("backToListBtn");
const logoutBtn = document.getElementById("logoutBtn");

const loadingOverlay = document.getElementById("loadingOverlay");

// ── Helpers ──────────────────────────────────────────────────────────

function escapeHtml(value) {
  return String(value == null ? "" : value)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

function formatDate(value) {
  if (!value) return "";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "";
  return date.toLocaleString();
}

function handleUnauthorized(message) {
  console.error(message);
  logout();
  alert("Session expired or invalid. Please log in again.");
  window.location.href = "../../index.html";
}

function showError(message) {
  quizFormError.textContent = message;
  quizFormError.classList.remove("hidden");
}

function clearError() {
  quizFormError.textContent = "";
  quizFormError.classList.add("hidden");
}

// ── Views ────────────────────────────────────────────────────────────

function showList() {
  listView.classList.remove("hidden");
  detailView.classList.add("hidden");
  renderQuizList();
}

function showDetail() {
  listView.classList.add("hidden");
  detailView.classList.remove("hidden");
}

function setLoading(isLoading) {
  loadingOverlay.classList.toggle("hidden", !isLoading);
}

// ── Quiz list ────────────────────────────────────────────────────────

function renderQuizList() {
  if (!Array.isArray(quizzes) || quizzes.length === 0) {
    quizList.innerHTML = `
      <div class="q-empty">
        <p>No quizzes yet.</p>
        <p class="q-muted">Tap “New Quiz” to generate your first quiz.</p>
      </div>
    `;
    quizCount.textContent = "0 quizzes";
    return;
  }

  quizCount.textContent = `${quizzes.length} quiz${quizzes.length === 1 ? "" : "zes"}`;

  quizList.innerHTML = quizzes
    .map((quiz) => {
      const title = quiz.topic || quiz.concept || "Quiz";
      const concept = quiz.concept || "—";
      const count = Array.isArray(quiz.questions) ? quiz.questions.length : 0;

      return `
        <button type="button" class="q-card" data-quiz-index="${quizzes.indexOf(quiz)}">
          <div class="q-card-top">
            <span class="q-card-title">${escapeHtml(title)}</span>
            <span class="q-badge q-badge-${escapeHtml((quiz.difficulty || "medium").toLowerCase())}">${escapeHtml(quiz.difficulty || "Medium")}</span>
          </div>
          <div class="q-card-sub">Concept · <b>${escapeHtml(concept)}</b></div>
          <div class="q-card-foot">
            <span>${count} question${count === 1 ? "" : "s"}</span>
            <span class="q-muted">${escapeHtml(formatDate(quiz.created_at))}</span>
          </div>
        </button>
      `;
    })
    .join("");

  quizList.querySelectorAll(".q-card").forEach((card) => {
    card.addEventListener("click", () => {
      const quiz = quizzes[Number(card.dataset.quizIndex)];
      if (quiz) openQuiz(quiz);
    });
  });
}

async function loadQuizzes() {
  try {
    quizzes = await fetchQuizzes();
    renderQuizList();
  } catch (error) {
    console.error("Failed to load quizzes:", error);
    if (/unauthorized|401/i.test(error.message)) {
      handleUnauthorized(error.message);
      return;
    }
    quizList.innerHTML = `<div class="q-empty"><p>Failed to load quizzes.</p><p class="q-muted">${escapeHtml(error.message)}</p></div>`;
  }
}

// ── New quiz modal ───────────────────────────────────────────────────

function openNewQuizModal() {
  clearError();
  newQuizModal.classList.remove("hidden");
  setTimeout(() => topicInput.focus(), 30);
}

function closeNewQuizModal() {
  newQuizModal.classList.add("hidden");
  clearError();
}

async function handleGenerate() {
  const topic = topicInput.value.trim();
  const concept = conceptInput.value.trim();
  const difficulty = difficultyInput.value;
  const number_of_questions = parseInt(numQuestionsInput.value, 10);
  const additional_description = additionalInput.value.trim();

  if (!topic) {
    showError("Please enter a topic.");
    topicInput.focus();
    return;
  }
  if (!concept) {
    showError("Please enter a concept.");
    conceptInput.focus();
    return;
  }
  if (!Number.isInteger(number_of_questions) || number_of_questions < 1 || number_of_questions > MAX_QUESTIONS) {
    showError(`Number of questions must be between 1 and ${MAX_QUESTIONS}.`);
    numQuestionsInput.focus();
    return;
  }

  const payload = { topic, concept, difficulty, number_of_questions };
  if (additional_description) {
    payload.additional_description = additional_description;
  }

  closeNewQuizModal();
  setLoading(true);
  generateQuizBtn.disabled = true;

  try {
    const quiz = await createQuiz(payload);
    await loadQuizzes();
    openQuiz(quiz);
    resetModalFields();
  } catch (error) {
    console.error("Generation error:", error);
    if (/unauthorized|401/i.test(error.message)) {
      handleUnauthorized(error.message);
    } else {
      alert(`Error generating quiz: ${error.message}`);
      openNewQuizModal();
    }
  } finally {
    setLoading(false);
    generateQuizBtn.disabled = false;
  }
}

function resetModalFields() {
  topicInput.value = "";
  conceptInput.value = "";
  difficultyInput.value = "Medium";
  numQuestionsInput.value = "5";
  additionalInput.value = "";
}

// ── Taking a quiz ────────────────────────────────────────────────────

function openQuiz(quiz) {
  if (!quiz || !Array.isArray(quiz.questions)) {
    alert("Invalid quiz data.");
    return;
  }

  currentQuiz = quiz;
  renderQuizDetail();
  showDetail();
  window.scrollTo({ top: 0 });
}

function renderQuizDetail() {
  const quiz = currentQuiz;
  const count = quiz.questions.length;
  const concept = quiz.concept || "—";

  let html = `
    <div class="q-quiz-header">
      <h1>${escapeHtml(quiz.topic || "Quiz")}</h1>
      <p class="q-muted">Concept: <b>${escapeHtml(concept)}</b> · Difficulty: <b>${escapeHtml(quiz.difficulty || "Medium")}</b> · ${count} questions</p>
    </div>
  `;

  quiz.questions.forEach((q, i) => {
    const options = Array.isArray(q.options) ? q.options : [];
    let optionsHtml = "";

    options.forEach((option, j) => {
      optionsHtml += `
        <label class="q-option">
          <input type="radio" name="q${i}" value="${j + 1}" />
          <span class="q-option-content"><b>${String.fromCharCode(65 + j)}.</b> <span class="q-option-text">${escapeHtml(option)}</span></span>
        </label>
      `;
    });

    html += `
      <div class="q-question" data-index="${i}">
        <h3>Question ${q.questionNo || (i + 1)}</h3>
        <p class="q-question-text">${escapeHtml(q.question || "")}</p>
        ${optionsHtml}
        <div class="q-feedback"></div>
      </div>
    `;
  });

  html += `
    <div class="q-submit-row">
      <button id="submitQuizBtn" class="q-btn q-btn-primary" type="button">Submit Quiz</button>
    </div>
    <div id="qResult" class="hidden"></div>
  `;

  quizDetail.innerHTML = html;

  document.getElementById("submitQuizBtn").addEventListener("click", submitQuiz);
}

function submitQuiz() {
  let score = 0;

  document.querySelectorAll(".q-question").forEach((div, i) => {
    const q = currentQuiz.questions[i];
    const labels = div.querySelectorAll(".q-option");
    const feedback = div.querySelector(".q-feedback");

    labels.forEach((label) => {
      label.classList.remove("correct-option", "wrong-option");
    });

    feedback.innerHTML = "";

    const selected = document.querySelector(`input[name="q${i}"]:checked`);
    let selectedValue = 0;
    if (selected) selectedValue = Number(selected.value);

    if (selectedValue && selectedValue === q.correctOption) {
      score++;
      labels[selectedValue - 1].classList.add("correct-option");
      feedback.innerHTML = `<p class="q-correct">✔ Correct</p>`;
    } else {
      if (selectedValue) {
        labels[selectedValue - 1].classList.add("wrong-option");
      }
      if (labels[q.correctOption - 1]) {
        labels[q.correctOption - 1].classList.add("correct-option");
      }
      feedback.innerHTML = `
        <p class="q-wrong">${selectedValue ? "✘ Wrong" : "Not Attempted"}</p>
        <p class="q-correct">Correct Answer: ${escapeHtml(q.options[q.correctOption - 1] || "")}</p>
      `;
    }

    div.querySelectorAll("input").forEach((input) => {
      input.disabled = true;
    });
  });

  const result = document.getElementById("qResult");
  result.classList.remove("hidden");
  result.innerHTML = `<p class="q-score">🎯 ${score} / ${currentQuiz.questions.length}</p>`;

  result.scrollIntoView({ behavior: "smooth" });
}

// ── Event listeners ──────────────────────────────────────────────────

newQuizBtn.addEventListener("click", openNewQuizModal);
cancelNewQuizBtn.addEventListener("click", closeNewQuizModal);
newQuizOverlay.addEventListener("click", closeNewQuizModal);
generateQuizBtn.addEventListener("click", handleGenerate);
backToListBtn.addEventListener("click", () => {
  currentQuiz = null;
  showList();
});

if (logoutBtn) {
  logoutBtn.addEventListener("click", () => {
    logout();
    window.location.href = "../../index.html";
  });
}

document.getElementById("backHomeBtn").addEventListener("click", (event) => {
  event.preventDefault();
  window.location.href = "../../index.html";
});

// ── Init ─────────────────────────────────────────────────────────────

loadQuizzes();
console.log(`Logged in as: ${(getUser() || {}).username || "unknown"}`);