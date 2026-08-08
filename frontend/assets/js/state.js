export const state = {
  conversations: [],
  modes: [],
  selectedConversationId: null,
  selectedConversation: null,
  messages: [],
  isStreaming: false
};

export function setConversations(conversations) {
  state.conversations = Array.isArray(conversations) ? conversations : [];
}

export function setModes(modes) {
  state.modes = Array.isArray(modes) ? modes : [];
}

export function setSelectedConversation(conversation) {
  state.selectedConversation = conversation || null;
  state.selectedConversationId =
    conversation?.conversation_id || conversation?.session_id || null;
}

export function setMessages(messages) {
  state.messages = Array.isArray(messages) ? messages : [];
}

export function setStreaming(isStreaming) {
  state.isStreaming = Boolean(isStreaming);
}