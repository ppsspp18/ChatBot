import { PROVIDERS, PROVIDERS_MODELS } from "./config.js";
import {
  registerUser,
  loginUser,
  fetchCurrentUser,
  fetchConversations,
  fetchConversation,
  createConversation,
  updateConversation,
  fetchMessages,
  fetchModes,
  createMode,
  deleteMode,
  streamMessage,
  deleteConversation,
  checkBackendHealth
} from "./api.js";
import {
  state,
  setConversations,
  setModes,
  setSelectedConversation,
  setMessages,
  setStreaming
} from "./state.js";
import {
  isAuthenticated,
  getUser,
  setUser,
  setToken,
  logout
} from "./auth.js";
import {
  getElements,
  renderConversations,
  renderMessages,
  renderSelectedConversation,
  renderModeManagementList,
  appendMessage,
  createStreamingAssistantMessage,
  updateStreamingAssistantMessage,
  finalizeStreamingAssistantMessage,
  showToast
} from "./ui.js";

const DEFAULT_CONVERSATION_TITLE = "NEW CONVERSATION";

// ── Screen management ────────────────────────────────────────────────

function showScreen(screenId) {
  document.querySelectorAll(".screen").forEach((screen) => {
    screen.classList.add("hidden");
  });
  document.getElementById(screenId).classList.remove("hidden");
}

// ── DOM references ───────────────────────────────────────────────────

const el = getElements();

const conversationForm = document.getElementById("conversationForm");
const providerSelect = document.getElementById("providerSelect");
const modelSelect = document.getElementById("modelSelect");
const modeSelect = document.getElementById("modeSelect");
const refreshConversationsBtn = document.getElementById("refreshConversationsBtn");

const messageForm = document.getElementById("messageForm");
const messageInput = document.getElementById("messageInput");
const sendBtn = document.getElementById("sendBtn");

// Auth Elements
const authScreen = document.getElementById("authScreen");
const homeScreen = document.getElementById("homeScreen");
const showLoginTab = document.getElementById("showLoginTab");
const showRegisterTab = document.getElementById("showRegisterTab");
const loginForm = document.getElementById("loginForm");
const registerForm = document.getElementById("registerForm");
const loginBtn = document.getElementById("loginBtn");
const registerBtn = document.getElementById("registerBtn");
const authError = document.getElementById("authError");
const homeUsername = document.getElementById("homeUsername");
const logoutBtn = document.getElementById("logoutBtn");
const chatLogoutBtn = document.getElementById("chatLogoutBtn");
const backToHomeBtn = document.getElementById("backToHomeBtn");
const goToChatCard = document.getElementById("goToChatCard");

// Modal Elements
const openModesModalBtn = document.getElementById("openModesModalBtn");
const closeModesModalBtn = document.getElementById("closeModesModalBtn");
const modesModal = document.getElementById("modesModal");
const modesModalOverlay = document.getElementById("modesModalOverlay");

const openNewConversationBtn = document.getElementById("openNewConversationBtn");
const closeNewConversationModalBtn = document.getElementById("closeNewConversationModalBtn");
const newConversationModal = document.getElementById("newConversationModal");
const newConversationModalOverlay = document.getElementById("newConversationModalOverlay");

// Sidebar (mobile drawer) Elements
const sidebar = document.getElementById("sidebar");
const sidebarOverlay = document.getElementById("sidebarOverlay");
const openSidebarBtn = document.getElementById("openSidebarBtn");
const closeSidebarBtn = document.getElementById("closeSidebarBtn");

const modeForm = document.getElementById("modeForm");
const modeEditingId = document.getElementById("modeEditingId");
const modeTitleInput = document.getElementById("modeTitleInput");
const modeDescriptionInput = document.getElementById("modeDescriptionInput");
const modeSystemPromptInput = document.getElementById("modeSystemPromptInput");
const modeSubmitBtn = document.getElementById("modeSubmitBtn");
const modeCancelEditBtn = document.getElementById("modeCancelEditBtn");

function normalizeMessages(messages) {
  if (!Array.isArray(messages)) return [];
  return messages.map((m) => ({
    ...m,
    message: m.message ?? m.content ?? ""
  }));
}

function setLoadingSendState(isLoading) {
  sendBtn.disabled = isLoading;
  messageInput.disabled = isLoading;
  setStreaming(isLoading);
}

function autoResizeTextarea() {
  messageInput.style.height = "auto";
  messageInput.style.height = `${Math.min(messageInput.scrollHeight, 220)}px`;
}

function getRandomProviderModel() {
  const providers = Object.keys(PROVIDERS_MODELS);
  const provider = providers[Math.floor(Math.random() * providers.length)];
  const models = PROVIDERS_MODELS[provider] || [];
  const model = models[Math.floor(Math.random() * models.length)] || "";
  return { provider, model };
}

function populateProviderSelect() {
  providerSelect.innerHTML = PROVIDERS.map(
    (provider) => `<option value="${provider}">${provider}</option>`
  ).join("");

  if (!providerSelect.value && PROVIDERS.length > 0) {
    providerSelect.value = PROVIDERS[0];
  }

  populateModelSelect(providerSelect.value);
}

function populateModelSelect(provider) {
  const models = PROVIDERS_MODELS[provider] || [];
  modelSelect.innerHTML = models
    .map((model) => `<option value="${model}">${model}</option>`)
    .join("");

  if (models.length > 0) {
    modelSelect.value = models[0];
  }
}

function populateModeSelect(modes) {
  modeSelect.innerHTML = `
    <option value="">No mode</option>
    ${modes
      .map((mode) => {
        const modeId = mode.mode_id || mode.id || "";
        const title = mode.title || "Untitled mode";
        return `<option value="${modeId}">${title}</option>`;
      })
      .join("")}
  `;
}

function renderModesManagementUI() {
  renderModeManagementList(state.modes, {
    onDelete: handleDeleteMode
  });
}

async function loadModes() {
  try {
    const modes = await fetchModes();
    const normalized = Array.isArray(modes) ? modes : [];
    setModes(normalized);
    populateModeSelect(normalized);
    renderModesManagementUI();
  } catch (error) {
    console.error(error);
    showToast(`Failed to load modes: ${error.message}`, "error");
  }
}

async function loadConversations({ preserveSelection = true } = {}) {
  try {
    const conversations = await fetchConversations();
    const normalized = Array.isArray(conversations) ? conversations : [];

    setConversations(normalized);

    let nextSelectedId = preserveSelection ? state.selectedConversationId : null;

    if (nextSelectedId) {
      const stillExists = normalized.some((c) => c.conversation_id === nextSelectedId);
      if (!stillExists) {
        nextSelectedId = null;
      }
    }

    renderConversations(normalized, nextSelectedId, {
      onSelect: handleSelectConversation,
      onRename: handleRenameConversation,
      onDelete: handleDeleteConversation
    });
  } catch (error) {
    console.error(error);
    showToast(`Failed to load conversations: ${error.message}`, "error");
  }
}

async function loadConversationDetails(conversationId) {
  const conversation = await fetchConversation(conversationId);
  setSelectedConversation(conversation);
  renderSelectedConversation(conversation);
  renderConversations(state.conversations, state.selectedConversationId, {
    onSelect: handleSelectConversation,
    onRename: handleRenameConversation,
    onDelete: handleDeleteConversation
  });
  return conversation;
}

async function loadMessagesForConversation(conversationId) {
  try {
    const messages = await fetchMessages(conversationId);
    const normalized = normalizeMessages(messages);
    setMessages(normalized);
    renderMessages(normalized);
  } catch (error) {
    console.error(error);
    showToast(`Failed to load messages: ${error.message}`, "error");
  }
}

async function handleSelectConversation(conversationId) {
  if (!conversationId) return;
  if (conversationId === state.selectedConversationId) {
    messageInput.focus();
    return;
  }

  try {
    await loadConversationDetails(conversationId);
    await loadMessagesForConversation(conversationId);
    closeSidebar();
    messageInput.focus();
  } catch (error) {
    console.error(error);
    showToast(`Failed to load conversation: ${error.message}`, "error");
  }
}

async function handleCreateConversation(event) {
  event.preventDefault();

  const provider = providerSelect.value;
  const model = modelSelect.value;
  const modeId = modeSelect.value || null;

  if (!provider || !model) {
    showToast("Please select provider and model.", "error");
    return;
  }

  const payload = {
    title: DEFAULT_CONVERSATION_TITLE,
    provider,
    model
  };

  if (modeId) {
    payload.mode_id = modeId;
  }

  try {
    const created = await createConversation(payload);
    closeNewConversationModal();
    showToast("Conversation created.", "success");

    await loadConversations({ preserveSelection: false });

    const newConversationId =
      created?.conversation_id || created?.session_id || null;
    if (newConversationId) {
      await handleSelectConversation(newConversationId);
    }
  } catch (error) {
    console.error(error);
    showToast(`Failed to create conversation: ${error.message}`, "error");
  }
}

async function handleSendMessage(event) {
  event.preventDefault();

  const message = messageInput.value.trim();
  if (!message) return;

  if (state.isStreaming) {
    showToast("Please wait for the current response to finish.", "info");
    return;
  }

  setLoadingSendState(true);

  let assistantBubble = null;
  let fullAssistantText = "";

  try {
    let conversationId = state.selectedConversationId;

    if (!conversationId) {
      const { provider, model } = getRandomProviderModel();
      if (!provider || !model) {
        throw new Error("No models configured. Please check the backend.");
      }

      const created = await createConversation({
        title: DEFAULT_CONVERSATION_TITLE,
        provider,
        model
      });
      conversationId = created?.conversation_id || created?.session_id || null;
      if (!conversationId) {
        throw new Error("Failed to create a new conversation.");
      }

      setSelectedConversation(created);
      await loadConversations({ preserveSelection: false });
    }

    // Optimistically add user message
    appendMessage("user", message);
    state.messages.push({
      role: "user",
      message
    });

    messageInput.value = "";
    autoResizeTextarea();

    assistantBubble = createStreamingAssistantMessage();

    await streamMessage(
      {
        conversation_id: conversationId,
        message
      },
      {
        onChunk(chunk) {
          fullAssistantText += chunk;
          updateStreamingAssistantMessage(assistantBubble, fullAssistantText);
        },
        onDone(data) {
          finalizeStreamingAssistantMessage(assistantBubble, fullAssistantText);

          if (data?.latency_ms || data?.ttft_ms) {
            showToast(
              `Response complete • latency ${data.latency_ms ?? "-"} ms • ttft ${data.ttft_ms ?? "-"} ms`,
              "success"
            );
          }
        },
        onError(errorMessage) {
          finalizeStreamingAssistantMessage(
            assistantBubble,
            `Error: ${errorMessage}`
          );
          showToast(`Streaming error: ${errorMessage}`, "error");
        }
      }
    );

    // Re-sync from the server instead of trusting local optimistic state.
    await loadConversations();
    await loadConversationDetails(conversationId);
    await loadMessagesForConversation(conversationId);
    messageInput.focus();
  } catch (error) {
    console.error(error);
    if (assistantBubble) {
      finalizeStreamingAssistantMessage(
        assistantBubble,
        `Error: ${error.message}`
      );
    }
    showToast(`Failed to send message: ${error.message}`, "error");
  } finally {
    setLoadingSendState(false);
  }
}

async function handleRenameConversation(conversationId) {
  const targetId = conversationId || state.selectedConversationId;
  if (!targetId) return;

  const current = state.conversations.find(
    (c) => c.conversation_id === targetId
  );
  const currentTitle = current?.title || "Untitled Conversation";

  const newTitle = window.prompt("Enter a new name for this conversation:", currentTitle);
  if (newTitle === null) return; // cancelled

  const trimmed = newTitle.trim();
  if (!trimmed) {
    showToast("Conversation name cannot be empty.", "error");
    return;
  }
  if (trimmed === currentTitle) return;

  try {
    await updateConversation({
      conversation_id: targetId,
      title: trimmed
    });
    showToast("Conversation renamed.", "success");
    await loadConversations();
    if (targetId === state.selectedConversationId) {
      await loadConversationDetails(targetId);
    }
  } catch (error) {
    console.error(error);
    showToast(`Failed to rename conversation: ${error.message}`, "error");
  }
}

async function handleDeleteConversation(conversationId) {
  const targetId = conversationId || state.selectedConversationId;
  if (!targetId) return;

  const confirmed = window.confirm(
    "Delete this conversation permanently?"
  );
  if (!confirmed) return;

  try {
    await deleteConversation(targetId);
    showToast("Conversation deleted.", "success");

    if (targetId === state.selectedConversationId) {
      setSelectedConversation(null);
      setMessages([]);
      renderSelectedConversation(null);
      renderMessages([]);
    }

    await loadConversations({ preserveSelection: true });
  } catch (error) {
    console.error(error);
    showToast(`Failed to delete conversation: ${error.message}`, "error");
  }
}

// ── Auth ─────────────────────────────────────────────────────────────

function setAuthError(message) {
  if (!message) {
    authError.classList.add("hidden");
    authError.textContent = "";
    return;
  }
  authError.textContent = message;
  authError.classList.remove("hidden");
}

function setAuthBusy(isBusy, button) {
  if (!button) return;
  if (!button.dataset.label) {
    button.dataset.label = button.textContent.trim();
  }
  button.disabled = isBusy;
  button.textContent = isBusy ? "Please wait..." : button.dataset.label;
}

function switchAuthTab(tab) {
  const isLogin = tab === "login";
  showLoginTab.classList.toggle("active", isLogin);
  showRegisterTab.classList.toggle("active", !isLogin);
  loginForm.classList.toggle("hidden", !isLogin);
  registerForm.classList.toggle("hidden", isLogin);
  setAuthError(null);
}

async function handleLogin(event) {
  event.preventDefault();
  setAuthError("");

  const username = document.getElementById("loginUsername").value.trim();
  const password = document.getElementById("loginPassword").value;

  if (!username || !password) {
    setAuthError("Please enter your username and password.");
    return;
  }

  setAuthBusy(true, loginBtn);
  try {
    const data = await loginUser({ username, password });
    setToken(data.access_token);
    const user = await fetchCurrentUser();
    setUser(user);
    enterApp();
  } catch (error) {
    console.error(error);
    setAuthError(error.message || "Login failed. Please try again.");
  } finally {
    setAuthBusy(false, loginBtn);
  }
}

async function handleRegister(event) {
  event.preventDefault();

  const username = document.getElementById("registerUsername").value.trim();
  const password = document.getElementById("registerPassword").value;
  const confirmPassword = document.getElementById("registerConfirmPassword").value;

  if (!username || !password) {
    setAuthError("Please enter a username and password.");
    return;
  }
  if (password.length < 6) {
    setAuthError("Password must be at least 6 characters long.");
    return;
  }
  if (password !== confirmPassword) {
    setAuthError("Passwords do not match.");
    return;
  }

  setAuthBusy(true, registerBtn);
  try {
    await registerUser({ username, password });
    // Auto-login after successful registration.
    const data = await loginUser({ username, password });
    setToken(data.access_token);
    const user = await fetchCurrentUser();
    setUser(user);
    enterApp();
  } catch (error) {
    console.error(error);
    setAuthError(error.message || "Registration failed. Please try again.");
  } finally {
    setAuthBusy(false, registerBtn);
  }
}

function handleLogout() {
  logout();
  setSelectedConversation(null);
  setMessages([]);
  showScreen("authScreen");
}

function enterApp() {
  const user = getUser();
  homeUsername.textContent = user?.username || "there";
  showScreen("homeScreen");
}

function enterChat() {
  // Render empty defaults FIRST to prevent them from wiping out async responses
  renderSelectedConversation(null);
  renderMessages([]);

  showScreen("chatScreen");

  loadModes();
  loadConversations();
}

function goToHome() {
  setSelectedConversation(null);
  setMessages([]);
  enterApp();
}

// ── Modes Modal ──────────────────────────────────────────────────────

function openModesModal() {
  modesModal.classList.remove("hidden");
  closeSidebar();
}

function closeModesModal() {
  modesModal.classList.add("hidden");
  resetModeForm();
}

// ── New Conversation Modal ─────────────────────────────────────────

function openNewConversationModal() {
  newConversationModal.classList.remove("hidden");
  closeSidebar();
  setTimeout(() => providerSelect.focus(), 50);
}

function closeNewConversationModal() {
  newConversationModal.classList.add("hidden");
}

// ── Sidebar (mobile drawer) ────────────────────────────────────────

function openSidebar() {
  sidebar.classList.add("open");
  sidebarOverlay.classList.remove("hidden");
}

function closeSidebar() {
  sidebar.classList.remove("open");
  sidebarOverlay.classList.add("hidden");
}

function resetModeForm() {
  modeEditingId.value = "";
  modeTitleInput.value = "";
  modeDescriptionInput.value = "";
  modeSystemPromptInput.value = "";
  modeSubmitBtn.textContent = "Create Mode";
  modeCancelEditBtn.classList.add("hidden");
}

async function handleModeFormSubmit(event) {
  event.preventDefault();

  const title = modeTitleInput.value.trim();
  const description = modeDescriptionInput.value.trim();
  const systemPrompt = modeSystemPromptInput.value.trim();

  if (!title || !description || !systemPrompt) {
    showToast("Please fill in title, description, and system prompt.", "error");
    return;
  }

  const payload = {
    title,
    description,
    system_prompt: systemPrompt
  };

  try {
    await createMode(payload);
    showToast("Mode created.", "success");
    resetModeForm();
    await loadModes();
  } catch (error) {
    console.error(error);
    showToast(`Failed to save mode: ${error.message}`, "error");
  }
}

async function handleDeleteMode(modeId) {
  if (!modeId) return;

  const confirmed = window.confirm("Delete this mode permanently?");
  if (!confirmed) return;

  try {
    await deleteMode(modeId);
    showToast("Mode deleted.", "success");

    if (modeEditingId.value === modeId) {
      resetModeForm();
    }

    await loadModes();
  } catch (error) {
    console.error(error);
    showToast(`Failed to delete mode: ${error.message}`, "error");
  }
}

// ── Boot / Backend wake-up ─────────────────────────────────────────

async function waitForBackend() {
  const bootLoading = document.getElementById("bootLoading");
  bootLoading.classList.remove("hidden");

  while (true) {
    // Treat 401/404/etc. as "awake"; only a network failure means sleeping.
    const ready = await checkBackendHealth();
    if (ready) break;
    await new Promise((resolve) => setTimeout(resolve, 5000));
  }

  bootLoading.classList.add("hidden");
}

// ── Event binding ────────────────────────────────────────────────────

function bindEvents() {
  providerSelect.addEventListener("change", (event) => {
    populateModelSelect(event.target.value);
  });

  conversationForm.addEventListener("submit", handleCreateConversation);
  messageForm.addEventListener("submit", handleSendMessage);

  // Auth
  showLoginTab.addEventListener("click", () => switchAuthTab("login"));
  showRegisterTab.addEventListener("click", () => switchAuthTab("register"));
  loginForm.addEventListener("submit", handleLogin);
  registerForm.addEventListener("submit", handleRegister);
  logoutBtn.addEventListener("click", handleLogout);
  chatLogoutBtn.addEventListener("click", handleLogout);
  backToHomeBtn.addEventListener("click", goToHome);

  goToChatCard.addEventListener("click", (event) => {
    event.preventDefault();
    enterChat();
  });

  // Modal Buttons
  openModesModalBtn.addEventListener("click", openModesModal);
  closeModesModalBtn.addEventListener("click", closeModesModal);
  modesModalOverlay.addEventListener("click", closeModesModal);

  // New Conversation Modal
  openNewConversationBtn.addEventListener("click", openNewConversationModal);
  closeNewConversationModalBtn.addEventListener("click", closeNewConversationModal);
  newConversationModalOverlay.addEventListener("click", closeNewConversationModal);

  // Sidebar (mobile drawer)
  openSidebarBtn.addEventListener("click", openSidebar);
  closeSidebarBtn.addEventListener("click", closeSidebar);
  sidebarOverlay.addEventListener("click", closeSidebar);

  modeForm.addEventListener("submit", handleModeFormSubmit);
  modeCancelEditBtn.addEventListener("click", resetModeForm);

  refreshConversationsBtn.addEventListener("click", async () => {
    if (!isAuthenticated()) return;
    await loadConversations();
    await loadModes();
    showToast("Refreshed conversations.", "info");
  });

  messageInput.addEventListener("input", autoResizeTextarea);

  messageInput.addEventListener("keydown", (event) => {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      messageForm.requestSubmit();
    }
  });
}

async function init() {
  populateProviderSelect();
  bindEvents();

  // ensure default empty states for chat screen
  renderSelectedConversation(null);
  renderMessages([]);

  // Render free tier servers sleep after inactivity. Block the UI with a
  // "please wait" loading screen until the backend wakes back up.
  await waitForBackend();

  if (!isAuthenticated()) {
    showScreen("authScreen");
    switchAuthTab("login");
    return;
  }

  enterApp();
}

init();