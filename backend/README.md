# `backend/README.md`

# ChatBot Backend API Guide for Frontend Engineers

This document explains **how to call every backend endpoint**, **what request body to send**, and **what the response looks like** so a frontend can be built **without reading backend code**.

---

# Table of Contents

1. [Base Overview](#base-overview)
2. [Conversations API](#conversations-api)
3. [Messages API](#messages-api)
4. [Modes API](#modes-api)
5. [Ingestion API](#ingestion-api)
6. [Metrics API](#metrics-api)
7. [Recommended Frontend Flow](#recommended-frontend-flow)
8. [Frontend Data Notes](#frontend-data-notes)
9. [Common Error Responses](#common-error-responses)

---

# Base Overview

## Backend responsibility

This backend has **two major responsibilities**:

1. **Chat System APIs**

   * conversations
   * messages
   * modes

2. **Observability / Analytics APIs**

   * ingestion of inference logs
   * metrics for dashboards

---

## Main resource identifiers

The frontend will mainly work with these IDs:

* **`session_id`** → unique ID of a conversation
* **`mode_id`** → unique ID of a mode
* **`log_id`** → unique ID of an inference log

---

## Main collections of endpoints

### Chat / User-facing endpoints

* `/conversations`
* `/messages`
* `/modes`

### Developer / Analytics endpoints

* `/ingest`
* `/metrics`

---

# Conversations API

A **conversation** represents one chat session.

A conversation stores:

* `session_id`
* title
* selected provider
* selected model
* selected mode
* status
* total token usage
* timestamps

---

## Conversation Object Shape

A conversation returned by the API looks like this:

```json
{
  "_id": "686d8d6d8dceba2c9fd7a111",
  "session_id": "f530a9c2-f1ea-4a13-8ecf-9b3f0e6b81f1",
  "title": "Python Help",
  "provider": "groq",
  "model": "llama3-70b",
  "mode_id": "b5f1a6e2-11c9-4b0b-9c0e-fcb3dbfbb9d8",
  "status": "active",
  "total_tokens": 482,
  "created_at": "2026-07-09T09:12:01.121000",
  "updated_at": "2026-07-09T09:18:42.341000"
}
```

### Field meanings

| Field          |                                  Type | Meaning                                                   |
| -------------- | ------------------------------------: | --------------------------------------------------------- |
| `_id`          |                                string | MongoDB document id                                       |
| `session_id`   |                                string | Primary frontend identifier for the conversation          |
| `title`        |                                string | Conversation title                                        |
| `provider`     |                                string | LLM provider used for this conversation                   |
| `model`        |                                string | LLM model used for this conversation                      |
| `mode_id`      |                         string | null | Optional mode attached to the conversation                |
| `status`       | `"active"` / `"cancelled"` / `"done"` | Conversation status                                       |
| `total_tokens` |                                number | Running total token count accumulated in the conversation |
| `created_at`   |                   ISO datetime string | Creation timestamp                                        |
| `updated_at`   |                   ISO datetime string | Last update timestamp                                     |

---

## 1) Create Conversation

Creates a new conversation.

### Endpoint

```http
POST /conversations/
```

### Request Body

```json
{
  "title": "New Conversation",
  "provider": "groq",
  "model": "llama3-70b",
  "mode_id": "optional-mode-id"
}
```

### Request Fields

| Field      | Required |          Type | Description                        |
| ---------- | -------- | ------------: | ---------------------------------- |
| `title`    | yes      |        string | Initial title for the conversation |
| `provider` | yes      |        string | LLM provider name                  |
| `model`    | yes      |        string | LLM model name                     |
| `mode_id`  | no       | string | null | Optional mode to attach            |

### Example cURL

```bash
curl -X POST "http://localhost:8000/conversations/" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "New Conversation",
    "provider": "groq",
    "model": "llama3-70b",
    "mode_id": null
  }'
```

### Success Response

```json
{
  "_id": "686d8d6d8dceba2c9fd7a111",
  "session_id": "f530a9c2-f1ea-4a13-8ecf-9b3f0e6b81f1",
  "title": "New Conversation",
  "provider": "groq",
  "model": "llama3-70b",
  "mode_id": null,
  "status": "active",
  "total_tokens": 0,
  "created_at": "2026-07-09T09:12:01.121000",
  "updated_at": "2026-07-09T09:12:01.121000"
}
```

### Frontend Notes

* Save `session_id` immediately. This is the main key for message APIs.
* If the user selected a mode in the UI, pass `mode_id`.
* If you want a generic blank chat, you can use a placeholder title like `"NEW CONVERSATION"` or `"New Chat"`.

---

## 2) Get All Conversations

Returns all conversations sorted by latest `updated_at` first.

### Endpoint

```http
GET /conversations/
```

### Example cURL

```bash
curl "http://localhost:8000/conversations/"
```

### Success Response

```json
[
  {
    "_id": "686d8d6d8dceba2c9fd7a111",
    "session_id": "f530a9c2-f1ea-4a13-8ecf-9b3f0e6b81f1",
    "title": "Python Help",
    "provider": "groq",
    "model": "llama3-70b",
    "mode_id": "b5f1a6e2-11c9-4b0b-9c0e-fcb3dbfbb9d8",
    "status": "active",
    "total_tokens": 482,
    "created_at": "2026-07-09T09:12:01.121000",
    "updated_at": "2026-07-09T09:18:42.341000"
  },
  {
    "_id": "686d8e338dceba2c9fd7a112",
    "session_id": "0ebadf2f-5f42-4f5f-b909-12e919d20f9f",
    "title": "FastAPI Questions",
    "provider": "openai",
    "model": "gpt-4o-mini",
    "mode_id": null,
    "status": "cancelled",
    "total_tokens": 127,
    "created_at": "2026-07-09T09:16:03.101000",
    "updated_at": "2026-07-09T09:17:20.551000"
  }
]
```

### Frontend Notes

Use this endpoint to populate:

* sidebar conversation list
* conversation history page
* “recent chats” UI

---

## 3) Get Single Conversation

Returns one conversation by `session_id`.

### Endpoint

```http
GET /conversations/{session_id}
```

### Example

```http
GET /conversations/f530a9c2-f1ea-4a13-8ecf-9b3f0e6b81f1
```

### Example cURL

```bash
curl "http://localhost:8000/conversations/f530a9c2-f1ea-4a13-8ecf-9b3f0e6b81f1"
```

### Success Response

```json
{
  "_id": "686d8d6d8dceba2c9fd7a111",
  "session_id": "f530a9c2-f1ea-4a13-8ecf-9b3f0e6b81f1",
  "title": "Python Help",
  "provider": "groq",
  "model": "llama3-70b",
  "mode_id": "b5f1a6e2-11c9-4b0b-9c0e-fcb3dbfbb9d8",
  "status": "active",
  "total_tokens": 482,
  "created_at": "2026-07-09T09:12:01.121000",
  "updated_at": "2026-07-09T09:18:42.341000"
}
```

### Possible Error

```json
{
  "detail": "Conversation not found"
}
```

---

## 4) Update Conversation

Updates selected fields of a conversation.

### Endpoint

```http
PATCH /conversations/
```

### Request Body

All fields except `session_id` are optional.

```json
{
  "session_id": "f530a9c2-f1ea-4a13-8ecf-9b3f0e6b81f1",
  "title": "Updated Chat Title",
  "provider": "groq",
  "model": "llama3-70b",
  "mode_id": "optional-mode-id"
}
```

### Request Fields

| Field        | Required |          Type | Description            |
| ------------ | -------- | ------------: | ---------------------- |
| `session_id` | yes      |        string | Conversation to update |
| `title`      | no       | string | null | New title              |
| `provider`   | no       | string | null | New provider           |
| `model`      | no       | string | null | New model              |
| `mode_id`    | no       | string | null | New mode id            |

### Example cURL

```bash
curl -X PATCH "http://localhost:8000/conversations/" \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "f530a9c2-f1ea-4a13-8ecf-9b3f0e6b81f1",
    "title": "Updated Chat Title",
    "mode_id": "b5f1a6e2-11c9-4b0b-9c0e-fcb3dbfbb9d8"
  }'
```

### Success Response

```json
{
  "message": "Conversation updated successfully"
}
```

### Frontend Notes

Use this endpoint for:

* renaming a conversation
* switching provider/model for a conversation
* assigning or changing mode

---

## 5) Cancel Conversation

Marks a conversation as cancelled.

### Endpoint

```http
PATCH /conversations/cancel/{session_id}
```

### Example cURL

```bash
curl -X PATCH "http://localhost:8000/conversations/cancel/f530a9c2-f1ea-4a13-8ecf-9b3f0e6b81f1"
```

### Success Response

```json
{
  "message": "Conversation cancelled successfully",
  "session_id": "f530a9c2-f1ea-4a13-8ecf-9b3f0e6b81f1"
}
```

### Frontend Notes

A cancelled conversation cannot be used normally by chat flow unless re-activated.

---

## 6) Activate Conversation

Re-activates a cancelled conversation.

### Endpoint

```http
PATCH /conversations/activate/{session_id}
```

### Example cURL

```bash
curl -X PATCH "http://localhost:8000/conversations/activate/f530a9c2-f1ea-4a13-8ecf-9b3f0e6b81f1"
```

### Success Response

```json
{
  "message": "Conversation activated successfully",
  "session_id": "f530a9c2-f1ea-4a13-8ecf-9b3f0e6b81f1"
}
```

---

## 7) Delete Conversation

Deletes the conversation and also deletes all messages belonging to that conversation.

### Endpoint

```http
DELETE /conversations/{session_id}
```

### Example cURL

```bash
curl -X DELETE "http://localhost:8000/conversations/f530a9c2-f1ea-4a13-8ecf-9b3f0e6b81f1"
```

### Success Response

```json
{
  "message": "Conversation deleted successfully"
}
```

### Frontend Notes

After deleting:

* remove the conversation from sidebar state
* clear message view if the deleted conversation was open

---

# Messages API

This API handles:

* sending a user message
* streaming assistant response
* retrieving chat history for a conversation

---

# Message Object Shape

A message returned by `GET /messages/{session_id}` looks like this:

```json
{
  "_id": "686d91088dceba2c9fd7a113",
  "session_id": "f530a9c2-f1ea-4a13-8ecf-9b3f0e6b81f1",
  "role": "user",
  "message": "Explain Python decorators",
  "provider": "groq",
  "model": "llama3-70b",
  "sequence": 1,
  "timestamp": "2026-07-09T09:19:04.100000",
  "inference_log_id": null
}
```

Assistant messages look similar, but may include `inference_log_id`:

```json
{
  "_id": "686d910f8dceba2c9fd7a114",
  "session_id": "f530a9c2-f1ea-4a13-8ecf-9b3f0e6b81f1",
  "role": "assistant",
  "message": "A decorator in Python is a function that wraps another function...",
  "provider": "groq",
  "model": "llama3-70b",
  "sequence": 2,
  "timestamp": "2026-07-09T09:19:05.500000",
  "inference_log_id": "686d910f8dceba2c9fd7a200"
}
```

---

## 1) Send Message

Sends a user message to an existing conversation and returns the assistant response as a **stream**.

### Endpoint

```http
POST /messages/
```

### Request Body

```json
{
  "session_id": "f530a9c2-f1ea-4a13-8ecf-9b3f0e6b81f1",
  "message": "Explain Python decorators"
}
```

### Request Fields

| Field        | Required |   Type | Description              |
| ------------ | -------- | -----: | ------------------------ |
| `session_id` | yes      | string | Existing conversation id |
| `message`    | yes      | string | User message text        |

---

## Important: Response type is SSE stream

This endpoint returns:

```http
Content-Type: text/event-stream
```

So the frontend should consume it as a **streaming response**, not a normal JSON response.

---

## Streaming Response Format

The backend emits chunks like this:

### Token chunk event

```text
data: {"content":"A decorator "}
```

```text
data: {"content":"in Python "}
```

```text
data: {"content":"is a function "}
```

### Error event

If generation fails:

```text
data: {"error":"Provider request failed"}
```

### Final done event

At the end:

```text
data: {"done":true,"latency_ms":842.37,"ttft_ms":152.91}
```

---

## Example frontend parsing expectation

The stream will usually contain multiple SSE events in this order:

1. many `content` chunks
2. one final `done` event

Possible sequence:

```text
data: {"content":"Hello"}
data: {"content":" there"}
data: {"content":"!"}
data: {"done":true,"latency_ms":512.4,"ttft_ms":120.3}
```

---

## What backend does internally on send

When `POST /messages/` is called, backend does the following:

1. validates the conversation
2. loads recent conversation context
3. injects mode system prompt if a mode is attached
4. streams LLM response
5. stores the user message
6. stores the assistant message
7. logs inference metrics
8. updates conversation token count
9. auto-generates title if the conversation title is `"NEW CONVERSATION"`

---

## Example fetch usage from frontend

### Browser fetch with stream reader

```javascript
const response = await fetch("http://localhost:8000/messages/", {
  method: "POST",
  headers: {
    "Content-Type": "application/json"
  },
  body: JSON.stringify({
    session_id: "f530a9c2-f1ea-4a13-8ecf-9b3f0e6b81f1",
    message: "Explain Python decorators"
  })
});

const reader = response.body.getReader();
const decoder = new TextDecoder();

let assistantText = "";

while (true) {
  const { value, done } = await reader.read();
  if (done) break;

  const chunk = decoder.decode(value, { stream: true });
  const lines = chunk.split("\n");

  for (const line of lines) {
    if (!line.startsWith("data: ")) continue;

    const payload = line.replace("data: ", "").trim();
    if (!payload) continue;

    try {
      const parsed = JSON.parse(payload);

      if (parsed.content) {
        assistantText += parsed.content;
      }

      if (parsed.error) {
        console.error("Stream error:", parsed.error);
      }

      if (parsed.done) {
        console.log("Generation finished", parsed);
      }
    } catch (err) {
      console.error("Failed to parse SSE chunk", err);
    }
  }
}
```

---

## Example cURL

`curl` can show the stream, but frontend should use fetch/stream reader or SSE parsing logic.

```bash
curl -N -X POST "http://localhost:8000/messages/" \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "f530a9c2-f1ea-4a13-8ecf-9b3f0e6b81f1",
    "message": "Explain Python decorators"
  }'
```

---

## Frontend Notes for Send Message

### You should:

* create a temporary assistant message in UI
* append `content` chunks into that message as they arrive
* stop loader when `done: true` arrives
* show error if an `error` chunk arrives

### Suggested UI flow:

1. user submits prompt
2. immediately render user bubble
3. create empty assistant bubble
4. stream chunks into assistant bubble
5. on final `done`, stop spinner
6. optionally refresh messages from `GET /messages/{session_id}` if you want server-confirmed state

---

## 2) Get Messages of a Conversation

Returns all messages for a conversation sorted by `sequence` ascending.

### Endpoint

```http
GET /messages/{session_id}
```

### Example cURL

```bash
curl "http://localhost:8000/messages/f530a9c2-f1ea-4a13-8ecf-9b3f0e6b81f1"
```

### Success Response

```json
[
  {
    "_id": "686d91088dceba2c9fd7a113",
    "session_id": "f530a9c2-f1ea-4a13-8ecf-9b3f0e6b81f1",
    "role": "user",
    "message": "Explain Python decorators",
    "provider": "groq",
    "model": "llama3-70b",
    "sequence": 1,
    "timestamp": "2026-07-09T09:19:04.100000",
    "inference_log_id": null
  },
  {
    "_id": "686d910f8dceba2c9fd7a114",
    "session_id": "f530a9c2-f1ea-4a13-8ecf-9b3f0e6b81f1",
    "role": "assistant",
    "message": "A decorator in Python is a function that wraps another function...",
    "provider": "groq",
    "model": "llama3-70b",
    "sequence": 2,
    "timestamp": "2026-07-09T09:19:05.500000",
    "inference_log_id": "686d910f8dceba2c9fd7a200"
  }
]
```

### Frontend Notes

Use this endpoint when:

* opening a conversation
* refreshing history
* reloading after page refresh
* syncing messages after a stream finishes

---

# Modes API

A **mode** stores custom AI behavior using a system prompt.

Examples:

* Tutor
* Code Reviewer
* Interviewer
* Resume Helper

A mode can be attached to a conversation using `mode_id`.

---

# Mode Object Shape

```json
{
  "_id": "686d93d18dceba2c9fd7a121",
  "mode_id": "b5f1a6e2-11c9-4b0b-9c0e-fcb3dbfbb9d8",
  "title": "Tutor",
  "description": "Explains concepts simply",
  "system_prompt": "You are a helpful tutor...",
  "updated_at": "2026-07-09T09:28:00.000000"
}
```

---

## 1) Create Mode

### Endpoint

```http
POST /modes/
```

### Request Body

```json
{
  "title": "Tutor",
  "description": "Explains concepts simply",
  "system_prompt": "You are a helpful tutor who explains step by step."
}
```

### Request Fields

| Field           | Required |   Type | Description                       |
| --------------- | -------- | -----: | --------------------------------- |
| `title`         | yes      | string | Mode title                        |
| `description`   | yes      | string | Short description                 |
| `system_prompt` | yes      | string | Prompt inserted as system message |

### Example cURL

```bash
curl -X POST "http://localhost:8000/modes/" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Tutor",
    "description": "Explains concepts simply",
    "system_prompt": "You are a helpful tutor who explains step by step."
  }'
```

### Success Response

```json
{
  "_id": "686d93d18dceba2c9fd7a121",
  "mode_id": "b5f1a6e2-11c9-4b0b-9c0e-fcb3dbfbb9d8",
  "title": "Tutor",
  "description": "Explains concepts simply",
  "system_prompt": "You are a helpful tutor who explains step by step.",
  "updated_at": "2026-07-09T09:28:00.000000"
}
```

### Possible Error

If another mode already has the same title:

```json
{
  "detail": "Mode title already exists"
}
```

---

## 2) Get All Modes

### Endpoint

```http
GET /modes/
```

### Example cURL

```bash
curl "http://localhost:8000/modes/"
```

### Success Response

```json
[
  {
    "_id": "686d93d18dceba2c9fd7a121",
    "mode_id": "b5f1a6e2-11c9-4b0b-9c0e-fcb3dbfbb9d8",
    "title": "Tutor",
    "description": "Explains concepts simply",
    "system_prompt": "You are a helpful tutor who explains step by step.",
    "updated_at": "2026-07-09T09:28:00.000000"
  },
  {
    "_id": "686d94088dceba2c9fd7a122",
    "mode_id": "2b8a4f9f-4d8d-421f-8f40-c1cb2e6bbd91",
    "title": "Coder",
    "description": "Writes and explains code",
    "system_prompt": "You are an expert software engineer.",
    "updated_at": "2026-07-09T09:29:12.000000"
  }
]
```

### Frontend Notes

Use this endpoint to populate:

* mode dropdown
* mode management page
* create/edit mode admin UI

---

## 3) Get Single Mode

### Endpoint

```http
GET /modes/{mode_id}
```

### Example cURL

```bash
curl "http://localhost:8000/modes/b5f1a6e2-11c9-4b0b-9c0e-fcb3dbfbb9d8"
```

### Success Response

```json
{
  "_id": "686d93d18dceba2c9fd7a121",
  "mode_id": "b5f1a6e2-11c9-4b0b-9c0e-fcb3dbfbb9d8",
  "title": "Tutor",
  "description": "Explains concepts simply",
  "system_prompt": "You are a helpful tutor who explains step by step.",
  "updated_at": "2026-07-09T09:28:00.000000"
}
```

### Possible Error

```json
{
  "detail": "Mode not found"
}
```

---

## 4) Update Mode

### Endpoint

```http
PATCH /modes/{mode_id}
```

### Request Body

```json
{
  "title": "Tutor",
  "description": "Explains concepts step by step",
  "system_prompt": "You are a patient tutor who explains with examples."
}
```

### Example cURL

```bash
curl -X PATCH "http://localhost:8000/modes/b5f1a6e2-11c9-4b0b-9c0e-fcb3dbfbb9d8" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Tutor",
    "description": "Explains concepts step by step",
    "system_prompt": "You are a patient tutor who explains with examples."
  }'
```

### Success Response

```json
{
  "_id": "686d93d18dceba2c9fd7a121",
  "mode_id": "b5f1a6e2-11c9-4b0b-9c0e-fcb3dbfbb9d8",
  "title": "Tutor",
  "description": "Explains concepts step by step",
  "system_prompt": "You are a patient tutor who explains with examples.",
  "updated_at": "2026-07-09T09:35:00.000000"
}
```

---

## 5) Delete Mode

### Endpoint

```http
DELETE /modes/{mode_id}
```

### Example cURL

```bash
curl -X DELETE "http://localhost:8000/modes/b5f1a6e2-11c9-4b0b-9c0e-fcb3dbfbb9d8"
```

### Success Response

```json
{
  "message": "Mode deleted successfully"
}
```

### Important Frontend/Backend Note

Deleting a mode only deletes the mode document.
If your product logic requires conversations using that mode to be detached or updated, handle that flow explicitly in backend or frontend product logic.

---

# Ingestion API

This API is for **asynchronous logging of inference events**.
It is **not** part of normal end-user chat UI. It is mainly for:

* SDKs
* telemetry
* analytics
* internal observability

The ingestion route validates the payload and puts it on an internal event queue.
The caller receives a fast **202 Accepted** response.

---

# Inference Log Payload Shape

```json
{
  "session_id": "f530a9c2-f1ea-4a13-8ecf-9b3f0e6b81f1",
  "log_id": "log-123",
  "provider": "groq",
  "model": "llama3-70b",
  "latency_ms": 120.4,
  "ttft_ms": 45.7,
  "prompt_tokens": 100,
  "completion_tokens": 250,
  "total_tokens": 350,
  "status": "success",
  "pii_detected": false,
  "entities": [],
  "input_preview": "Hello",
  "output_preview": "Hi there"
}
```

---

## 1) Send Inference Log

### Endpoint

```http
POST /ingest
```

### Request Body

```json
{
  "session_id": "f530a9c2-f1ea-4a13-8ecf-9b3f0e6b81f1",
  "log_id": "log-123",
  "provider": "groq",
  "model": "llama3-70b",
  "latency_ms": 120.4,
  "ttft_ms": 45.7,
  "prompt_tokens": 100,
  "completion_tokens": 250,
  "total_tokens": 350,
  "status": "success",
  "pii_detected": false,
  "entities": [],
  "input_preview": "Hello",
  "output_preview": "Hi there"
}
```

### Request Fields

| Field               | Required |                                    Type | Description                    |
| ------------------- | -------- | --------------------------------------: | ------------------------------ |
| `session_id`        | yes      |                                  string | Conversation session id        |
| `log_id`            | yes      |                                  string | Unique log id from caller side |
| `provider`          | yes      |                                  string | LLM provider                   |
| `model`             | yes      |                                  string | Model name                     |
| `latency_ms`        | yes      |                                  number | Total latency in milliseconds  |
| `ttft_ms`           | yes      |                                  number | Time to first token            |
| `prompt_tokens`     | yes      |                                  number | Prompt token count             |
| `completion_tokens` | yes      |                                  number | Completion token count         |
| `total_tokens`      | yes      |                                  number | Total tokens                   |
| `status`            | yes      | `"success"` / `"error"` / `"cancelled"` | Result status                  |
| `pii_detected`      | yes      |                                 boolean | Whether PII was detected       |
| `entities`          | yes      |                                string[] | Extracted entities             |
| `input_preview`     | yes      |                                  string | Small input preview            |
| `output_preview`    | yes      |                                  string | Small output preview           |

### Example cURL

```bash
curl -X POST "http://localhost:8000/ingest" \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "f530a9c2-f1ea-4a13-8ecf-9b3f0e6b81f1",
    "log_id": "log-123",
    "provider": "groq",
    "model": "llama3-70b",
    "latency_ms": 120.4,
    "ttft_ms": 45.7,
    "prompt_tokens": 100,
    "completion_tokens": 250,
    "total_tokens": 350,
    "status": "success",
    "pii_detected": false,
    "entities": [],
    "input_preview": "Hello",
    "output_preview": "Hi there"
  }'
```

### Success Response

Status code is **202 Accepted**

```json
{
  "status": "accepted",
  "log_id": "log-123",
  "queue_size": 1
}
```

### Meaning of response

| Field        | Meaning                      |
| ------------ | ---------------------------- |
| `status`     | queue accepted the log       |
| `log_id`     | same log id sent by caller   |
| `queue_size` | current in-memory queue size |

---

## 2) Ingestion Health

Returns the current queue size.

### Endpoint

```http
GET /ingest/health
```

### Example cURL

```bash
curl "http://localhost:8000/ingest/health"
```

### Success Response

```json
{
  "status": "ok",
  "queue_size": 0
}
```

---

# Metrics API

These endpoints are meant for **dashboard / analytics UI**.

They read from inference logs and provide:

* summary numbers
* latency stats
* errors
* token usage
* throughput

---

## Shared Query Parameter

Most metrics endpoints support:

```http
?hours=24
```

### Meaning

Return metrics for the last `N` hours.

### Validation

* minimum = `1`
* maximum = `168` (7 days)

---

# 1) Metrics Overview

Returns summary cards for dashboard header.

### Endpoint

```http
GET /metrics/overview?hours=24
```

### Example cURL

```bash
curl "http://localhost:8000/metrics/overview?hours=24"
```

### Success Response

```json
{
  "total_calls": 128,
  "total_prompt_tokens": 12040,
  "total_completion_tokens": 28190,
  "total_tokens": 40230,
  "avg_latency_ms": 842.12,
  "error_count": 5,
  "success_count": 123,
  "error_rate": 3.91,
  "window_hours": 24
}
```

### Field meanings

| Field                     | Meaning                             |
| ------------------------- | ----------------------------------- |
| `total_calls`             | total inference calls in the window |
| `total_prompt_tokens`     | sum of prompt tokens                |
| `total_completion_tokens` | sum of completion tokens            |
| `total_tokens`            | total token usage                   |
| `avg_latency_ms`          | average latency                     |
| `error_count`             | total failed calls                  |
| `success_count`           | total successful calls              |
| `error_rate`              | error percentage                    |
| `window_hours`            | hours used for this query           |

---

# 2) Metrics Latency

Returns latency percentiles and hourly time-series.

### Endpoint

```http
GET /metrics/latency?hours=24
```

### Example cURL

```bash
curl "http://localhost:8000/metrics/latency?hours=24"
```

### Success Response

```json
{
  "p50_ms": 620.12,
  "p95_ms": 1510.48,
  "p99_ms": 2104.77,
  "avg_ms": 804.52,
  "min_ms": 210.15,
  "max_ms": 2920.41,
  "sample_count": 128,
  "time_series": [
    {
      "timestamp": "2026-07-09 09:00",
      "avg_latency_ms": 740.25,
      "count": 12
    },
    {
      "timestamp": "2026-07-09 10:00",
      "avg_latency_ms": 802.55,
      "count": 18
    }
  ],
  "window_hours": 24
}
```

### Frontend Use Cases

Use this endpoint for:

* latency line chart
* p50/p95/p99 cards
* performance dashboard

---

# 3) Metrics Errors

Returns error breakdowns and error-rate time-series.

### Endpoint

```http
GET /metrics/errors?hours=24
```

### Example cURL

```bash
curl "http://localhost:8000/metrics/errors?hours=24"
```

### Success Response

```json
{
  "by_provider": [
    {
      "provider": "groq",
      "count": 3
    },
    {
      "provider": "openai",
      "count": 2
    }
  ],
  "by_type": [
    {
      "error_type": "Rate limit exceeded",
      "count": 2
    },
    {
      "error_type": "Provider timeout",
      "count": 1
    }
  ],
  "time_series": [
    {
      "timestamp": "2026-07-09 09:00",
      "total": 12,
      "errors": 1,
      "error_rate": 8.33
    },
    {
      "timestamp": "2026-07-09 10:00",
      "total": 18,
      "errors": 0,
      "error_rate": 0
    }
  ],
  "window_hours": 24
}
```

### Frontend Use Cases

Use this for:

* provider error bar chart
* error category table
* hourly error rate chart

---

# 4) Metrics Tokens

Returns token usage grouped by provider and model.

### Endpoint

```http
GET /metrics/tokens?hours=24
```

### Example cURL

```bash
curl "http://localhost:8000/metrics/tokens?hours=24"
```

### Success Response

```json
{
  "by_provider": [
    {
      "provider": "groq",
      "prompt_tokens": 5000,
      "completion_tokens": 12000,
      "total_tokens": 17000,
      "call_count": 40
    },
    {
      "provider": "openai",
      "prompt_tokens": 7040,
      "completion_tokens": 16190,
      "total_tokens": 23230,
      "call_count": 88
    }
  ],
  "by_model": [
    {
      "provider": "openai",
      "model": "gpt-4o-mini",
      "total_tokens": 15000,
      "call_count": 55
    },
    {
      "provider": "groq",
      "model": "llama3-70b",
      "total_tokens": 12000,
      "call_count": 28
    }
  ],
  "window_hours": 24
}
```

### Frontend Use Cases

Use this for:

* provider token usage cards
* model usage table
* cost estimation dashboards

---

# 5) Metrics Throughput

Returns request throughput over time.

### Endpoint

```http
GET /metrics/throughput?hours=24
```

### Example cURL

```bash
curl "http://localhost:8000/metrics/throughput?hours=24"
```

### Success Response

```json
{
  "per_minute": [
    {
      "timestamp": "2026-07-09 09:10",
      "requests": 2
    },
    {
      "timestamp": "2026-07-09 09:11",
      "requests": 1
    }
  ],
  "per_hour": [
    {
      "timestamp": "2026-07-09 09:00",
      "requests": 24
    },
    {
      "timestamp": "2026-07-09 10:00",
      "requests": 37
    }
  ],
  "avg_rpm": 1.42,
  "total_requests": 128,
  "window_hours": 24
}
```

### Frontend Use Cases

Use this for:

* traffic chart
* requests-per-minute graph
* requests-per-hour graph
* load dashboard

---

# Recommended Frontend Flow

This is the simplest correct way to build the frontend on top of this backend.

---

# A) Chat App Flow

## Step 1: Load sidebar conversations

Call:

```http
GET /conversations/
```

Render:

* title
* updated time
* maybe status
* maybe token count

---

## Step 2: User opens a conversation

Call:

```http
GET /messages/{session_id}
```

Render the full message history.

---

## Step 3: User creates a new chat

Call:

```http
POST /conversations/
```

with:

* title
* provider
* model
* optional mode

Save returned `session_id`.

---

## Step 4: User sends a message

Call:

```http
POST /messages/
```

with:

* `session_id`
* `message`

Then stream the assistant response from SSE.

---

## Step 5: Update UI while streaming

* append user bubble immediately
* create empty assistant bubble
* append chunks from `content`
* finalize on `done: true`

---

## Step 6: Optional refresh after stream

If needed, refresh history using:

```http
GET /messages/{session_id}
```

---

# B) Mode Management Flow

## To show available modes

Call:

```http
GET /modes/
```

## To create mode

Call:

```http
POST /modes/
```

## To update mode

Call:

```http
PATCH /modes/{mode_id}
```

## To attach mode to conversation

Call:

```http
PATCH /conversations/
```

with a `mode_id`.

---

# C) Analytics Dashboard Flow

For an admin dashboard, you can call these on page load:

* `GET /metrics/overview?hours=24`
* `GET /metrics/latency?hours=24`
* `GET /metrics/errors?hours=24`
* `GET /metrics/tokens?hours=24`
* `GET /metrics/throughput?hours=24`

---

# Frontend Data Notes

## 1) Use `session_id` as the main conversation key

Do **not** use Mongo `_id` as your frontend routing key.
Use `session_id`.

Good examples:

* `/chat/:session_id`
* selectedConversationSessionId
* messagesBySessionId

---

## 2) Messages are ordered by `sequence`

When messages are fetched from:

```http
GET /messages/{session_id}
```

they are already sorted in ascending `sequence`.

---

## 3) A conversation stores provider + model

The conversation itself already stores:

* `provider`
* `model`
* `mode_id`

So when a message is sent, the backend reads those values from the conversation.

That means the frontend does **not** need to send provider/model on every message request.

---

## 4) Modes are optional

A conversation can have:

* a valid `mode_id`
* or `mode_id = null`

If mode exists, backend injects that mode’s `system_prompt` into chat context.

---

## 5) Cancelled conversations

If a conversation is cancelled:

* backend may reject normal chat usage depending on validation path
* frontend should usually disable the input box or show “reactivate conversation”

---

## 6) Message streaming is not a normal JSON response

`POST /messages/` is **streaming**.

Do not write frontend code like:

```javascript
const data = await response.json();
```

That will not work correctly for streamed assistant generation.

Use a stream reader and parse `data:` events.

---

## 7) Title generation behavior

If a conversation title is `"NEW CONVERSATION"`, backend may auto-generate a better title after the first user message.

So the frontend should be prepared for conversation title changes after first message.

A good pattern:

* after first message completes, optionally refetch conversation list

---

# Common Error Responses

Most backend validation errors return JSON like this:

```json
{
  "detail": "Some error message"
}
```

Examples:

## Conversation not found

```json
{
  "detail": "Conversation not found"
}
```

## Conversation cancelled

```json
{
  "detail": "Conversation is cancelled"
}
```

## Mode not found

```json
{
  "detail": "Mode not found"
}
```

## Mode title already exists

```json
{
  "detail": "Mode title already exists"
}
```

## Validation error example

FastAPI may return a validation error in this shape:

```json
{
  "detail": [
    {
      "type": "missing",
      "loc": ["body", "session_id"],
      "msg": "Field required",
      "input": {
        "message": "Hello"
      }
    }
  ]
}
```

---

# Quick Endpoint Summary

## Conversations

| Method   | Endpoint                               | Purpose                          |
| -------- | -------------------------------------- | -------------------------------- |
| `POST`   | `/conversations/`                      | Create conversation              |
| `GET`    | `/conversations/`                      | List conversations               |
| `GET`    | `/conversations/{session_id}`          | Get one conversation             |
| `PATCH`  | `/conversations/`                      | Update title/provider/model/mode |
| `PATCH`  | `/conversations/cancel/{session_id}`   | Cancel conversation              |
| `PATCH`  | `/conversations/activate/{session_id}` | Activate conversation            |
| `DELETE` | `/conversations/{session_id}`          | Delete conversation              |

## Messages

| Method | Endpoint                 | Purpose                                 |
| ------ | ------------------------ | --------------------------------------- |
| `POST` | `/messages/`             | Send message and stream assistant reply |
| `GET`  | `/messages/{session_id}` | Get message history                     |

## Modes

| Method   | Endpoint           | Purpose      |
| -------- | ------------------ | ------------ |
| `POST`   | `/modes/`          | Create mode  |
| `GET`    | `/modes/`          | List modes   |
| `GET`    | `/modes/{mode_id}` | Get one mode |
| `PATCH`  | `/modes/{mode_id}` | Update mode  |
| `DELETE` | `/modes/{mode_id}` | Delete mode  |

## Ingestion

| Method | Endpoint         | Purpose                       |
| ------ | ---------------- | ----------------------------- |
| `POST` | `/ingest`        | Push inference log into queue |
| `GET`  | `/ingest/health` | Queue health                  |

## Metrics

| Method | Endpoint                       | Purpose          |
| ------ | ------------------------------ | ---------------- |
| `GET`  | `/metrics/overview?hours=24`   | Summary metrics  |
| `GET`  | `/metrics/latency?hours=24`    | Latency stats    |
| `GET`  | `/metrics/errors?hours=24`     | Error stats      |
| `GET`  | `/metrics/tokens?hours=24`     | Token stats      |
| `GET`  | `/metrics/throughput?hours=24` | Throughput stats |

---

# Final Integration Advice

If you are building the frontend, the safest implementation order is:

1. **Modes list** → `GET /modes/`
2. **Conversation sidebar** → `GET /conversations/`
3. **Create conversation** → `POST /conversations/`
4. **Load message history** → `GET /messages/{session_id}`
5. **Send message with streaming UI** → `POST /messages/`
6. **Conversation edit / rename / mode change** → `PATCH /conversations/`
7. **Admin analytics dashboard** → `/metrics/*`

If you implement the **message streaming parser** and use **`session_id` as the primary key**, the rest of the frontend becomes straightforward.
