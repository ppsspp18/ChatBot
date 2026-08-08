import { BACKEND_URL } from "./config.js";
import { getToken } from "./auth.js";

function buildHeaders() {
  const headers = {
    "Content-Type": "application/json"
  };

  const token = getToken();
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  return headers;
}

async function handleJsonResponse(response) {
  const contentType = response.headers.get("content-type") || "";

  if (!response.ok) {
    let errorText = `Request failed with status ${response.status}`;
    try {
      if (contentType.includes("application/json")) {
        const data = await response.json();
        errorText = data.detail || JSON.stringify(data);
      } else {
        errorText = await response.text();
      }
    } catch (_) {
      // ignore parse failure
    }

    if (response.status === 401) {
      errorText = `${errorText} (Unauthorized — please log in again.)`;
    }

    throw new Error(errorText);
  }

  if (contentType.includes("application/json")) {
    return response.json();
  }

  return response.text();
}

// ── Auth ───────────────────────────────────────────────────────────

export async function registerUser(payload) {
  const res = await fetch(`${BACKEND_URL}/auth/register`, {
    method: "POST",
    headers: buildHeaders(),
    body: JSON.stringify(payload)
  });
  return handleJsonResponse(res);
}

export async function loginUser(payload) {
  const res = await fetch(`${BACKEND_URL}/auth/login`, {
    method: "POST",
    headers: buildHeaders(),
    body: JSON.stringify(payload)
  });
  return handleJsonResponse(res);
}

export async function fetchCurrentUser() {
  const res = await fetch(`${BACKEND_URL}/auth/me`, {
    method: "GET",
    headers: buildHeaders()
  });
  return handleJsonResponse(res);
}

// ── Conversations ──────────────────────────────────────────────────

export async function fetchConversations() {
  const res = await fetch(`${BACKEND_URL}/conversations/`, {
    method: "GET",
    headers: buildHeaders()
  });
  return handleJsonResponse(res);
}

export async function fetchConversation(conversationId) {
  const res = await fetch(`${BACKEND_URL}/conversations/${conversationId}`, {
    method: "GET",
    headers: buildHeaders()
  });
  return handleJsonResponse(res);
}

export async function createConversation(payload) {
  const res = await fetch(`${BACKEND_URL}/conversations/`, {
    method: "POST",
    headers: buildHeaders(),
    body: JSON.stringify(payload)
  });
  return handleJsonResponse(res);
}

export async function updateConversation(payload) {
  const res = await fetch(`${BACKEND_URL}/conversations/`, {
    method: "PATCH",
    headers: buildHeaders(),
    body: JSON.stringify(payload)
  });
  return handleJsonResponse(res);
}

export async function deleteConversation(conversationId) {
  const res = await fetch(`${BACKEND_URL}/conversations/${conversationId}`, {
    method: "DELETE",
    headers: buildHeaders()
  });
  return handleJsonResponse(res);
}

// ── Messages ───────────────────────────────────────────────────────

export async function fetchMessages(conversationId) {
  const res = await fetch(`${BACKEND_URL}/messages/${conversationId}`, {
    method: "GET",
    headers: buildHeaders()
  });
  return handleJsonResponse(res);
}

/**
 * Stream assistant response from POST /messages/
 * Expected SSE-ish response chunks:
 * data: {"content":"..."}
 * data: {"done":true,...}
 */
export async function streamMessage(payload, handlers = {}) {
  const { onChunk, onDone, onError } = handlers;

  const response = await fetch(`${BACKEND_URL}/messages/`, {
    method: "POST",
    headers: buildHeaders(),
    body: JSON.stringify(payload)
  });

  if (!response.ok) {
    let errorText = `Streaming request failed with status ${response.status}`;
    try {
      errorText = await response.text();
    } catch (_) {}
    throw new Error(errorText);
  }

  if (!response.body) {
    throw new Error("Streaming response body is not available.");
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder("utf-8");
  let buffer = "";

  while (true) {
    const { value, done } = await reader.read();

    if (done) {
      break;
    }

    buffer += decoder.decode(value, { stream: true });

    const events = buffer.split("\n\n");
    buffer = events.pop() || "";

    for (const eventBlock of events) {
      const lines = eventBlock
        .split("\n")
        .map((line) => line.trim())
        .filter(Boolean);

      for (const line of lines) {
        if (!line.startsWith("data:")) continue;

        const raw = line.slice(5).trim();
        if (!raw) continue;

        try {
          const parsed = JSON.parse(raw);

          if (parsed.error) {
            if (onError) onError(parsed.error);
            continue;
          }

          if (parsed.content) {
            if (onChunk) onChunk(parsed.content);
          }

          if (parsed.done) {
            if (onDone) onDone(parsed);
          }
        } catch (err) {
          console.error("Failed to parse SSE line:", raw, err);
        }
      }
    }
  }
}

// ── Modes ──────────────────────────────────────────────────────────

export async function fetchModes() {
  const res = await fetch(`${BACKEND_URL}/modes/`, {
    method: "GET",
    headers: buildHeaders()
  });
  return handleJsonResponse(res);
}

export async function createMode(payload) {
  const res = await fetch(`${BACKEND_URL}/modes/`, {
    method: "POST",
    headers: buildHeaders(),
    body: JSON.stringify(payload)
  });
  return handleJsonResponse(res);
}

export async function deleteMode(modeId) {
  const res = await fetch(`${BACKEND_URL}/modes/${modeId}`, {
    method: "DELETE",
    headers: buildHeaders()
  });
  return handleJsonResponse(res);
}

// ── Quiz ───────────────────────────────────────────────────────────

export async function createQuiz(payload) {
  const res = await fetch(`${BACKEND_URL}/quiz/`, {
    method: "POST",
    headers: buildHeaders(),
    body: JSON.stringify(payload)
  });
  return handleJsonResponse(res);
}

export async function fetchQuizzes() {
  const res = await fetch(`${BACKEND_URL}/quiz/`, {
    method: "GET",
    headers: buildHeaders()
  });
  return handleJsonResponse(res);
}

// ── Health ─────────────────────────────────────────────────────────

export async function checkBackendHealth() {
  try {
    const res = await fetch(`${BACKEND_URL}/conversations/`, {
      method: "GET",
      headers: buildHeaders()
    });

    return res.ok;
  } catch (_) {
    return false;
  }
}