import { state } from "./state.js";

const elements = {
  conversationList: document.getElementById("conversationList"),
  messagesContainer: document.getElementById("messagesContainer"),
  emptyChatState: document.getElementById("emptyChatState"),
  chatTitle: document.getElementById("chatTitle"),
  chatMeta: document.getElementById("chatMeta"),
  selectedConversationDetails: document.getElementById("selectedConversationDetails"),
  backendStatus: document.getElementById("backendStatus"),
  streamingStatus: document.getElementById("streamingStatus"),
  toastContainer: document.getElementById("toastContainer"),
  modeManagementList: document.getElementById("modeManagementList")
};

export function getElements() {
  return elements;
}

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function formatDate(value) {
  if (!value) return "—";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleString();
}

function truncate(text, max = 80) {
  if (!text) return "";
  return text.length > max ? `${text.slice(0, max)}…` : text;
}

function normalizeConversationStatus(conversation) {
  if (conversation?.status) return conversation.status;
  if (conversation?.is_active === false) return "cancelled";
  return "active";
}

/**
 * Renders markdown content to sanitized HTML.
 * Falls back to plain escaped text if marked/DOMPurify are unavailable.
 */
function renderMarkdown(content) {
  const text = content ?? "";

  if (typeof window.marked === "undefined") {
    return `<p>${escapeHtml(text).replaceAll("\n", "<br />")}</p>`;
  }

  const rawHtml = window.marked.parse(text, { breaks: true, gfm: true });

  if (typeof window.DOMPurify !== "undefined") {
    return window.DOMPurify.sanitize(rawHtml);
  }

  return rawHtml;
}

function renderMessageHtml(role, content) {
  const safeRole = role === "user" ? "user" : "assistant";

  if (safeRole === "user") {
    return `
      <div class="message user">
        <div class="message-bubble">${escapeHtml(content ?? "")}</div>
      </div>
    `;
  }

  return `
    <div class="message assistant">
      <div class="message-bubble">${renderMarkdown(content)}</div>
    </div>
  `;
}

export function showToast(message, type = "info") {
  const toast = document.createElement("div");
  toast.className = `toast ${type}`;
  toast.textContent = message;

  elements.toastContainer.appendChild(toast);

  setTimeout(() => {
    toast.style.opacity = "0";
    toast.style.transform = "translateY(10px)";
    setTimeout(() => toast.remove(), 250);
  }, 3200);
}

export function renderConversations(conversations, selectedConversationId, callbacks = {}) {
  const { onSelect, onRename, onDelete } = callbacks;

  if (!elements.conversationList) return;

  if (!conversations || conversations.length === 0) {
    elements.conversationList.innerHTML = `
      <div class="panel-card">
        <p class="muted">No conversations yet.</p>
      </div>
    `;
    return;
  }

  elements.conversationList.innerHTML = conversations
    .map((conversation) => {
      const conversationId =
        conversation.conversation_id || conversation.session_id || "";
      const title = escapeHtml(conversation.title || "Untitled Conversation");
      const provider = escapeHtml(conversation.provider || "—");
      const model = escapeHtml(conversation.model || "—");
      const status = normalizeConversationStatus(conversation);
      const activeClass =
        conversationId === selectedConversationId ? "active" : "";
      const isCancelled = status === "cancelled";

      return `
        <div class="conversation-item ${activeClass}" data-conversation-id="${escapeHtml(conversationId)}">
          <div class="conversation-top">
            <div class="conversation-title" data-role="select">${title}</div>
          </div>

          <div class="conversation-meta" data-role="select">
            ${truncate(model, 60)}
          </div>

          <div class="conversation-badges" data-role="select">
            <span class="badge badge-provider">${provider}</span>
            <span class="badge ${
              isCancelled ? "badge-status-cancelled" : "badge-status-active"
            }">${status}</span>
          </div>

          <div class="conversation-item-actions">
            <button type="button" class="icon-btn" data-action="rename">Rename</button>
            <button type="button" class="icon-btn danger" data-action="delete">Delete</button>
          </div>
        </div>
      `;
    })
    .join("");

  elements.conversationList.querySelectorAll(".conversation-item").forEach((item) => {
    const conversationId = item.dataset.conversationId;

    item.querySelectorAll('[data-role="select"]').forEach((node) => {
      node.addEventListener("click", () => {
        if (conversationId && onSelect) onSelect(conversationId);
      });
    });

    const renameBtn = item.querySelector('[data-action="rename"]');
    if (renameBtn) {
      renameBtn.addEventListener("click", (event) => {
        event.stopPropagation();
        if (conversationId && onRename) onRename(conversationId);
      });
    }

    const deleteBtn = item.querySelector('[data-action="delete"]');
    if (deleteBtn) {
      deleteBtn.addEventListener("click", (event) => {
        event.stopPropagation();
        if (conversationId && onDelete) onDelete(conversationId);
      });
    }
  });
}

export function renderModeManagementList(modes, callbacks = {}) {
  const { onDelete } = callbacks;

  if (!elements.modeManagementList) return;

  if (!modes || modes.length === 0) {
    elements.modeManagementList.innerHTML = `<p class="muted">No modes yet.</p>`;
    return;
  }

  elements.modeManagementList.innerHTML = modes
    .map((mode) => {
      const modeId = mode.mode_id || mode.id || "";
      const title = escapeHtml(mode.title || "Untitled mode");
      const description = escapeHtml(mode.description || "");

      return `
        <div class="conversation-item" data-mode-id="${escapeHtml(modeId)}">
          <div class="conversation-top">
            <div class="conversation-title">${title}</div>
          </div>
          <div class="conversation-meta">${truncate(description, 70)}</div>
          <div class="conversation-item-actions">
            <button type="button" class="icon-btn danger" data-action="delete">Delete</button>
          </div>
        </div>
      `;
    })
    .join("");

  elements.modeManagementList.querySelectorAll(".conversation-item").forEach((item) => {
    const modeId = item.dataset.modeId;

    const deleteBtn = item.querySelector('[data-action="delete"]');
    if (deleteBtn) {
      deleteBtn.addEventListener("click", () => {
        if (modeId && onDelete) onDelete(modeId);
      });
    }
  });
}

export function renderMessages(messages = []) {
  if (!elements.messagesContainer) return;

  if (!messages.length) {
    elements.messagesContainer.innerHTML = `
      <div class="empty-chat-state" id="emptyChatState">
        <div class="empty-chat-icon">✨</div>
        <h3>How can I help you today?</h3>
        <p>Type your message below to start the conversation.</p>
      </div>
    `;
    return;
  }

  elements.messagesContainer.innerHTML = messages
    .map((message) =>
      renderMessageHtml(
        message.role,
        message.message ?? message.content ?? ""
      )
    )
    .join("");

  scrollMessagesToBottom();
}

export function renderSelectedConversation(conversation) {
  if (!conversation) {
    elements.chatTitle.textContent = "Select or create a conversation";
    elements.chatMeta.textContent = "No conversation selected";
    elements.selectedConversationDetails.innerHTML =
      `<p class="muted">No conversation selected.</p>`;
    return;
  }

  const status = normalizeConversationStatus(conversation);

  elements.chatTitle.textContent = conversation.title || "Untitled Conversation";
  elements.chatMeta.textContent = `${conversation.provider || "—"} • ${conversation.model || "—"} • ${status}`;

  elements.selectedConversationDetails.innerHTML = `
    <div class="detail-row">
      <div class="detail-label">Conversation ID</div>
      <div class="detail-value">${escapeHtml(conversation.conversation_id || conversation.session_id || "—")}</div>
    </div>
    <div class="detail-row">
      <div class="detail-label">Title</div>
      <div class="detail-value">${escapeHtml(conversation.title || "Untitled Conversation")}</div>
    </div>
    <div class="detail-row">
      <div class="detail-label">Provider</div>
      <div class="detail-value">${escapeHtml(conversation.provider || "—")}</div>
    </div>
    <div class="detail-row">
      <div class="detail-label">Model</div>
      <div class="detail-value">${escapeHtml(conversation.model || "—")}</div>
    </div>
    <div class="detail-row">
      <div class="detail-label">Mode</div>
      <div class="detail-value">${escapeHtml(conversation.mode_id || "No mode")}</div>
    </div>
    <div class="detail-row">
      <div class="detail-label">Status</div>
      <div class="detail-value">${escapeHtml(status)}</div>
    </div>
    <div class="detail-row">
      <div class="detail-label">Created</div>
      <div class="detail-value">${escapeHtml(formatDate(conversation.created_at || conversation.createdAt))}</div>
    </div>
  `;
}

export function appendMessage(role, content) {
  if (!elements.messagesContainer) return;

  const existingEmpty = document.getElementById("emptyChatState");
  if (existingEmpty) existingEmpty.remove();

  const wrapper = document.createElement("div");
  wrapper.className = `message ${role}`;
  wrapper.innerHTML = `
    <div class="message-bubble">${escapeHtml(content)}</div>
  `;

  elements.messagesContainer.appendChild(wrapper);
  scrollMessagesToBottom();
}

export function createStreamingAssistantMessage() {
  const existingEmpty = document.getElementById("emptyChatState");
  if (existingEmpty) existingEmpty.remove();

  const wrapper = document.createElement("div");
  wrapper.className = "message assistant";
  wrapper.innerHTML = `
    <div class="message-bubble typing-cursor" data-streaming-bubble></div>
  `;

  elements.messagesContainer.appendChild(wrapper);
  scrollMessagesToBottom();

  return wrapper.querySelector("[data-streaming-bubble]");
}

/**
 * Re-renders the streaming bubble's markdown on every chunk so the
 * assistant output appears live-formatted rather than raw markdown text.
 */
export function updateStreamingAssistantMessage(bubbleEl, content) {
  if (!bubbleEl) return;
  bubbleEl.innerHTML = renderMarkdown(content);
  scrollMessagesToBottom();
}

export function finalizeStreamingAssistantMessage(bubbleEl, content) {
  if (!bubbleEl) return;
  bubbleEl.innerHTML = renderMarkdown(content);
  bubbleEl.classList.remove("typing-cursor");
  scrollMessagesToBottom();
}

export function scrollMessagesToBottom() {
  if (!elements.messagesContainer) return;
  elements.messagesContainer.scrollTop = elements.messagesContainer.scrollHeight;
}

export function setBackendStatus(isOnline) {
  const el = elements.backendStatus;
  if (!el) return;

  el.textContent = isOnline ? "Online" : "Offline";
  el.className = `status-badge ${isOnline ? "status-online" : "status-error"}`;
}

export function setStreamingStatus(isStreaming) {
  const el = elements.streamingStatus;
  if (!el) return;

  el.textContent = isStreaming ? "Streaming" : "Idle";
  el.className = `status-badge ${isStreaming ? "status-streaming" : "status-idle"}`;
}

export function getSelectedConversationStatus(conversation) {
  return normalizeConversationStatus(conversation);
}