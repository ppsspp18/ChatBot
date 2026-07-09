import { PROVIDERS, PROVIDERS_MODELS } from "./config.js";
import {
  fetchConversations,
  fetchConversation,
  createConversation,
  fetchMessages,
  fetchModes,
  createMode,
  updateMode,
  deleteMode,
  streamMessage,
  deleteConversation,
  activateConversation,
  cancelConversation,
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
  getElements,
  renderConversations,
  renderMessages,
  renderSelectedConversation,
  renderModeManagementList,
  appendMessage,
  createStreamingAssistantMessage,
  updateStreamingAssistantMessage,
  finalizeStreamingAssistantMessage,
  showToast,
  setBackendStatus,
  setStreamingStatus
} from "./ui.js";

const DEFAULT_CONVERSATION_TITLE = "NEW CONVERSATION";

const el = getElements();

const conversationForm = document.getElementById("conversationForm");
const providerSelect = document.getElementById("providerSelect");
const modelSelect = document.getElementById("modelSelect");
const modeSelect = document.getElementById("modeSelect");
const refreshConversationsBtn = document.getElementById("refreshConversationsBtn");

const messageForm = document.getElementById("messageForm");
const messageInput = document.getElementById("messageInput");
const sendBtn = document.getElementById("sendBtn");

// Modal Elements
const openModesModalBtn = document.getElementById("openModesModalBtn");
const closeModesModalBtn = document.getElementById("closeModesModalBtn");
const modesModal = document.getElementById("modesModal");
const modesModalOverlay = document.getElementById("modesModalOverlay");

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
  setStreamingStatus(isLoading);
}

function autoResizeTextarea() {
  messageInput.style.height = "auto";
  messageInput.style.height = `${Math.min(messageInput.scrollHeight, 220)}px`;
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
    onEdit: handleEditModeClick,
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
      const stillExists = normalized.some((c) => c.session_id === nextSelectedId);
      if (!stillExists) {
        nextSelectedId = null;
      }
    }

    renderConversations(normalized, nextSelectedId, {
      onSelect: handleSelectConversation,
      onActivate: handleActivateConversation,
      onCancel: handleCancelConversation,
      onDelete: handleDeleteConversation
    });
  } catch (error) {
    console.error(error);
    showToast(`Failed to load conversations: ${error.message}`, "error");
  }
}

async function loadConversationDetails(sessionId) {
  const conversation = await fetchConversation(sessionId);
  setSelectedConversation(conversation);
  renderSelectedConversation(conversation);
  renderConversations(state.conversations, state.selectedConversationId, {
    onSelect: handleSelectConversation,
    onActivate: handleActivateConversation,
    onCancel: handleCancelConversation,
    onDelete: handleDeleteConversation
  });
  return conversation;
}

async function loadMessagesForConversation(sessionId) {
  try {
    const messages = await fetchMessages(sessionId);
    const normalized = normalizeMessages(messages);
    setMessages(normalized);
    renderMessages(normalized);
  } catch (error) {
    console.error(error);
    showToast(`Failed to load messages: ${error.message}`, "error");
  }
}

async function handleSelectConversation(sessionId) {
  if (!sessionId) return;
  if (sessionId === state.selectedConversationId) {
    messageInput.focus();
    return;
  }

  try {
    await loadConversationDetails(sessionId);
    await loadMessagesForConversation(sessionId);
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
    showToast("Conversation created.", "success");

    await loadConversations({ preserveSelection: false });

    const newSessionId = created?.session_id || created?.data?.session_id || null;
    if (newSessionId) {
      await handleSelectConversation(newSessionId);
    }
  } catch (error) {
    console.error(error);
    showToast(`Failed to create conversation: ${error.message}`, "error");
  }
}

async function handleSendMessage(event) {
  event.preventDefault();

  const message = messageInput.value.trim();
  const sessionId = state.selectedConversationId;

  if (!sessionId) {
    showToast("Please select or create a conversation first.", "error");
    return;
  }

  if (!message) {
    return;
  }

  if (state.isStreaming) {
    showToast("Please wait for the current response to finish.", "info");
    return;
  }

  // Optimistically add user message
  appendMessage("user", message);
  state.messages.push({
    role: "user",
    message
  });

  messageInput.value = "";
  autoResizeTextarea();
  setLoadingSendState(true);

  const assistantBubble = createStreamingAssistantMessage();
  let fullAssistantText = "";

  try {
    await streamMessage(
      {
        session_id: sessionId,
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
    // This is what fixes messages not loading/staying consistent: the
    // backend is always the source of truth for history and sequence order.
    await loadConversations();
    await loadConversationDetails(sessionId);
    await loadMessagesForConversation(sessionId);
    messageInput.focus();
  } catch (error) {
    console.error(error);
    finalizeStreamingAssistantMessage(
      assistantBubble,
      `Error: ${error.message}`
    );
    showToast(`Failed to send message: ${error.message}`, "error");
  } finally {
    setLoadingSendState(false);
  }
}

async function handleDeleteConversation(sessionId) {
  const targetId = sessionId || state.selectedConversationId;
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

async function handleActivateConversation(sessionId) {
  const targetId = sessionId || state.selectedConversationId;
  if (!targetId) return;

  try {
    await activateConversation(targetId);
    showToast("Conversation activated.", "success");
    await loadConversations();
    if (targetId === state.selectedConversationId) {
      await loadConversationDetails(targetId);
    }
  } catch (error) {
    console.error(error);
    showToast(`Failed to activate conversation: ${error.message}`, "error");
  }
}

async function handleCancelConversation(sessionId) {
  const targetId = sessionId || state.selectedConversationId;
  if (!targetId) return;

  try {
    await cancelConversation(targetId);
    showToast("Conversation cancelled.", "success");
    await loadConversations();
    if (targetId === state.selectedConversationId) {
      await loadConversationDetails(targetId);
    }
  } catch (error) {
    console.error(error);
    showToast(`Failed to cancel conversation: ${error.message}`, "error");
  }
}

// Modal Toggle Logic
function openModesModal() {
  modesModal.classList.remove("hidden");
}

function closeModesModal() {
  modesModal.classList.add("hidden");
  resetModeForm(); // Clean form automatically when hiding
}

function resetModeForm() {
  modeEditingId.value = "";
  modeTitleInput.value = "";
  modeDescriptionInput.value = "";
  modeSystemPromptInput.value = "";
  modeSubmitBtn.textContent = "Create Mode";
  modeCancelEditBtn.classList.add("hidden");
}

function handleEditModeClick(mode) {
  modeEditingId.value = mode.mode_id || mode.id || "";
  modeTitleInput.value = mode.title || "";
  modeDescriptionInput.value = mode.description || "";
  modeSystemPromptInput.value = mode.system_prompt || "";
  modeSubmitBtn.textContent = "Update Mode";
  modeCancelEditBtn.classList.remove("hidden");
  modeTitleInput.focus();
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

  const editingId = modeEditingId.value;

  try {
    if (editingId) {
      await updateMode(editingId, payload);
      showToast("Mode updated.", "success");
    } else {
      await createMode(payload);
      showToast("Mode created.", "success");
    }

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

async function checkStatus() {
  const online = await checkBackendHealth();
  setBackendStatus(online);
}

function bindEvents() {
  providerSelect.addEventListener("change", (event) => {
    populateModelSelect(event.target.value);
  });

  conversationForm.addEventListener("submit", handleCreateConversation);
  messageForm.addEventListener("submit", handleSendMessage);
  
  // Modal Buttons
  openModesModalBtn.addEventListener("click", openModesModal);
  closeModesModalBtn.addEventListener("click", closeModesModal);
  modesModalOverlay.addEventListener("click", closeModesModal);

  modeForm.addEventListener("submit", handleModeFormSubmit);
  modeCancelEditBtn.addEventListener("click", resetModeForm);

  refreshConversationsBtn.addEventListener("click", async () => {
    await loadConversations();
    await loadModes();
    await checkStatus();
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
  
  // Render empty defaults FIRST to prevent them from wiping out async responses
  renderSelectedConversation(null);
  renderMessages([]);
  
  // Initialize Real Data sequentially
  await loadModes();
  await loadConversations();
  await checkStatus();
}

init();