let quizData = null;
let allQuizzes = [];

const topicInput = document.getElementById("topic");
const conceptInput = document.getElementById("concept");
const difficultySelect = document.getElementById("difficulty");
const numQuestionsInput = document.getElementById("numQuestions");
const additionalDescriptionInput = document.getElementById("additionalDescription");

const generateQuizBtn = document.getElementById("generateQuizBtn");
const savedQuizzesSelect = document.getElementById("savedQuizzesSelect");
const loadSavedQuizBtn = document.getElementById("loadSavedQuizBtn");

const quizContainer = document.getElementById("quiz");
const submitArea = document.getElementById("submitArea");
const result = document.getElementById("result");

const API_BASE = "http://localhost:8000";

// Event listeners
generateQuizBtn.addEventListener("click", handleGenerate);
loadSavedQuizBtn.addEventListener("click", handleLoadSaved);

// Load saved quizzes on startup
window.addEventListener("DOMContentLoaded", fetchSavedQuizzes);

async function fetchSavedQuizzes() {
  try {
    const response = await fetch(`${API_BASE}/quiz/`);
    if (!response.ok) {
      throw new Error("Failed to fetch quizzes");
    }
    allQuizzes = await response.json();
    populateSavedQuizzesDropdown();
  } catch (error) {
    console.error("Error fetching saved quizzes:", error);
    if (error.message.includes("Failed to fetch")) {
      console.warn("Could not connect to backend at http://localhost:8000. Ensure backend is running and CORS is enabled.");
    }
  }
}

function populateSavedQuizzesDropdown() {
  savedQuizzesSelect.innerHTML = `<option value="">-- Select a previously generated quiz (${allQuizzes.length}) --</option>`;
  allQuizzes.forEach((quiz, index) => {
    const title = quiz.title || `${quiz.topic} - ${quiz.concept}`;
    const date = quiz.created_at ? new Date(quiz.created_at).toLocaleString() : '';
    const option = document.createElement("option");
    option.value = quiz._id || index;
    option.textContent = `${title} (${quiz.difficulty}, ${quiz.questions ? quiz.questions.length : 0} Qs) — ${date}`;
    savedQuizzesSelect.appendChild(option);
  });
}

async function handleGenerate() {
  const topic = topicInput.value.trim();
  const concept = conceptInput.value.trim();
  const difficulty = difficultySelect.value;
  const number_of_questions = parseInt(numQuestionsInput.value, 10);
  const additional_description = additionalDescriptionInput.value.trim();

  if (!topic) {
    alert("Please enter a topic.");
    topicInput.focus();
    return;
  }
  if (!concept) {
    alert("Please enter a concept.");
    conceptInput.focus();
    return;
  }
  if (isNaN(number_of_questions) || number_of_questions < 1 || number_of_questions > 100) {
    alert("Number of questions must be between 1 and 100.");
    numQuestionsInput.focus();
    return;
  }

  const payload = {
    topic,
    concept,
    difficulty,
    number_of_questions
  };
  if (additional_description) {
    payload.additional_description = additional_description;
  }

  generateQuizBtn.disabled = true;
  generateQuizBtn.textContent = "⚡ Generating Quiz with AI...";

  try {
    const response = await fetch(`${API_BASE}/quiz/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });

    if (!response.ok) {
      const errData = await response.json().catch(() => ({}));
      throw new Error(errData.detail || `Server error: ${response.status}`);
    }

    const quiz = await response.json();
    quizData = quiz;
    renderQuiz();
    await fetchSavedQuizzes();
    if (quiz._id) {
      savedQuizzesSelect.value = quiz._id;
    }
  } catch (error) {
    console.error("Generation error:", error);
    if (error.message.includes("Failed to fetch")) {
      alert("Failed to fetch: Could not connect to backend at http://localhost:8000.\n\nPlease ensure:\n1. The FastAPI backend server is running.\n2. CORS middleware is enabled on the backend (allowing requests from browser frontend).");
    } else {
      alert(`Error generating quiz: ${error.message}`);
    }
  } finally {
    generateQuizBtn.disabled = false;
    generateQuizBtn.textContent = "⚡ Generate Quiz with AI";
  }
}

function handleLoadSaved() {
  const selectedId = savedQuizzesSelect.value;
  if (!selectedId) {
    alert("Please select a quiz from the dropdown.");
    return;
  }

  const found = allQuizzes.find(q => q._id === selectedId || allQuizzes.indexOf(q).toString() === selectedId);
  if (found) {
    quizData = found;
    if (found.topic) topicInput.value = found.topic;
    if (found.concept) conceptInput.value = found.concept;
    if (found.difficulty) difficultySelect.value = found.difficulty;
    if (found.questions) numQuestionsInput.value = found.questions.length;
    renderQuiz();
  } else {
    alert("Quiz not found.");
  }
}

function renderQuiz() {
  if (!quizData || !Array.isArray(quizData.questions)) {
    alert("Invalid quiz data.");
    return;
  }

  result.innerHTML = "";
  quizContainer.innerHTML = `<h2>${escapeHtml(quizData.title || "Quiz")}</h2><p style="color: var(--text-secondary); margin-bottom: 20px;">Topic: <b>${escapeHtml(quizData.topic)}</b> | Concept: <b>${escapeHtml(quizData.concept)}</b> | Difficulty: <b>${escapeHtml(quizData.difficulty)}</b></p>`;

  quizData.questions.forEach((q, i) => {
    let html = `<div class="question">
      <h3>Question ${q.questionNo || (i + 1)}</h3>
      <div class="question-text">${escapeHtml(q.question)}</div>`;

    if (!Array.isArray(q.options)) {
      html += `<p class="wrong">Invalid options data.</p></div>`;
      quizContainer.innerHTML += html;
      return;
    }

    q.options.forEach((option, j) => {
      html += `
        <label class="option">
          <input type="radio" name="q${i}" value="${j + 1}">
          <span class="option-content"><b>${String.fromCharCode(65 + j)}.</b> <span class="option-text">${escapeHtml(option)}</span></span>
        </label>
      `;
    });

    html += `<div class="feedback"></div></div>`;
    quizContainer.innerHTML += html;
  });

  submitArea.innerHTML = `<button id="submitQuizBtn">Submit Quiz</button>`;
  document.getElementById("submitQuizBtn").addEventListener("click", submitQuiz);
  
  quizContainer.scrollIntoView({ behavior: 'smooth' });
}

function submitQuiz() {
  let score = 0;

  document.querySelectorAll(".question").forEach((div, i) => {
    const q = quizData.questions[i];
    const labels = div.querySelectorAll(".option");
    const feedback = div.querySelector(".feedback");

    labels.forEach((label) => {
      label.classList.remove("correct-option", "wrong-option");
    });

    feedback.innerHTML = "";

    const selected = document.querySelector(`input[name="q${i}"]:checked`);

    if (selected) {
      const selectedValue = Number(selected.value);

      if (selectedValue === q.correctOption) {
        score++;
        labels[selectedValue - 1].classList.add("correct-option");
        feedback.innerHTML = `<p class="correct">✔ Correct</p>`;
      } else {
        labels[selectedValue - 1].classList.add("wrong-option");
        if (labels[q.correctOption - 1]) {
          labels[q.correctOption - 1].classList.add("correct-option");
        }
        feedback.innerHTML = `
          <p class="wrong">✘ Wrong</p>
          <p class="correct">Correct Answer: ${escapeHtml(q.options[q.correctOption - 1] || "")}</p>
        `;
      }
    } else {
      if (labels[q.correctOption - 1]) {
        labels[q.correctOption - 1].classList.add("correct-option");
      }
      feedback.innerHTML = `
        <p class="wrong">Not Attempted</p>
        <p class="correct">Correct Answer: ${escapeHtml(q.options[q.correctOption - 1] || "")}</p>
      `;
    }

    div.querySelectorAll("input").forEach((input) => {
      input.disabled = true;
    });
  });

  result.innerHTML = `🎯 Final Score: ${score} / ${quizData.questions.length}`;
  submitArea.innerHTML = `
    <div class="action-buttons">
      <button id="copyKnowledgeGapBtn">📋 Copy Response for Knowledge Gap</button>
      <button id="reloadQuizBtn">Generate New Quiz</button>
    </div>
  `;

  document.getElementById("copyKnowledgeGapBtn").addEventListener("click", copyKnowledgeGapPrompt);
  document.getElementById("reloadQuizBtn").addEventListener("click", () => {
    window.scrollTo({ top: 0, behavior: 'smooth' });
  });
}

function copyKnowledgeGapPrompt() {
  if (!quizData || !Array.isArray(quizData.questions)) return;

  const t = quizData.topic || topicInput.value.trim() || "the topic";
  const c = quizData.concept || conceptInput.value.trim() || "the core concepts";

  const missedQuestions = [];

  quizData.questions.forEach((q, i) => {
    const selected = document.querySelector(`input[name="q${i}"]:checked`);
    let userAnswer = "Not Attempted";
    let wasCorrect = false;

    if (selected) {
      const selectedValue = Number(selected.value);
      userAnswer = q.options[selectedValue - 1];
      wasCorrect = selectedValue === q.correctOption;
    }

    if (!wasCorrect) {
      missedQuestions.push({
        questionNo: q.questionNo || (i + 1),
        question: q.question,
        userAnswer,
        correctAnswer: q.options[q.correctOption - 1]
      });
    }
  });

  if (missedQuestions.length === 0) {
    const prompt = `I just took a multiple-choice quiz on ${t} - ${c} and answered every question correctly. Please give me a short, encouraging summary of the key concepts this quiz covered, and suggest 2-3 slightly more advanced or related topics I could explore next to deepen my understanding.`;
    navigator.clipboard.writeText(prompt);
    alert("Prompt copied! (You got a perfect score, so this asks for next-step topics instead.)");
    return;
  }

  let resultsText = `I just took a multiple-choice quiz on ${t} - ${c}. Below are ONLY the questions I got wrong or did not attempt, out of ${quizData.questions.length} total questions.\n\n`;

  missedQuestions.forEach((item) => {
    resultsText += `Q${item.questionNo}: ${item.question}\n`;
    resultsText += `My Answer: ${item.userAnswer}\n`;
    resultsText += `Correct Answer: ${item.correctAnswer}\n\n`;
  });

  resultsText += `Based on these mistakes, please act as an expert tutor and help me close my knowledge gaps. For each question above:
1. Explain the underlying theory/concept in simple, clear terms.
2. Explain specifically why my answer was wrong (if I attempted it) and why the correct answer is right.
3. Walk through any relevant code or logic step by step where applicable.
4. Point out common misconceptions that lead to this kind of mistake.

Then, at the end, give a short summary of the overall concepts I should review to master this topic.`;

  navigator.clipboard.writeText(resultsTest);
  alert("Knowledge gap prompt copied! Paste this into the LLM to get an explanation focused on your mistakes.");
}

function escapeHtml(value) {
  return String(value)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}
