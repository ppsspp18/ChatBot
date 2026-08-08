
```md
# Chat API Cheat Sheet

## Base Details

- backend URL : local host 8000 
- Auth header for all protected endpoints:

```http
Authorization: Bearer <access_token>
Content-Type: application/json
```

- Common errors:

```json
{
  "detail": "Error message here"
}
```

## Conversations

### Create Conversation

```http
POST /conversations/
```

Request:

```json
{
  "title": "New Conversation",
  "provider": "openai",
  "model": "gpt-4o",
  "mode_id": "mode_123"
}
```
Whenever creating new conversation name it New Conversation, whenever he send message it will automatically renamed. 

Response:

```json
{
  "_id": "665f1c2a9b1e8f3a2c4d5e6f",
  "conversation_id": "a1b2c3d4-5678-90ef-gh12-345678901234",
  "user_id": "user_123",
  "title": "My First Chat",
  "provider": "openai",
  "model": "gpt-4o",
  "mode_id": "mode_123",
  "total_tokens": 0,
  "created_at": "2026-06-16T10:00:00Z",
  "updated_at": "2026-06-16T10:00:00Z"
}
```

### List Conversations

```http
GET /conversations/
```

Response:

```json
[
  {
    "_id": "665f1c2a9b1e8f3a2c4d5e6f",
    "conversation_id": "a1b2c3d4-5678-90ef-gh12-345678901234",
    "user_id": "user_123",
    "title": "My First Chat",
    "provider": "openai",
    "model": "gpt-4o",
    "mode_id": "mode_123",
    "total_tokens": 0,
    "created_at": "2026-06-16T10:00:00Z",
    "updated_at": "2026-06-16T10:00:00Z"
  }
]
```

### Get Conversation

```http
GET /conversations/{conversation_id}
```

Response: same as single conversation object above.

### Update Conversation Title

```http
PATCH /conversations/
```

Request:

```json
{
  "conversation_id": "a1b2c3d4-5678-90ef-gh12-345678901234",
  "title": "Renamed Chat"
}
```

Response: updated conversation object.

### Delete Conversation

```http
DELETE /conversations/{conversation_id}
```

Response:

```json
{
  "message": "Conversation deleted successfully"
}
```

## Messages

### Send Message

```http
POST /messages/
```

Request:

```json
{
  "conversation_id": "a1b2c3d4-5678-90ef-gh12-345678901234",
  "message": "Hello, how are you?"
}
```

Non-streaming response example:

```json
{
  "conversation_id": "a1b2c3d4-5678-90ef-gh12-345678901234",
  "role": "assistant",
  "message": "Hello! How can I help you today?",
  "sequence": 2,
  "timestamp": "2026-06-16T10:05:00Z"
}
```

stream message response : 

message stream logic : 
            async for content in generate_stream(
                provider=provider,
                model=model,
                messages=context_messages
            ):
                if first_chunk:
                    ttft_ms = (time.time() - start) * 1000
                    first_chunk = False

                full_response += content
                yield f"data: {json.dumps({'content': content})}\n\n"

          # finally yield : f"data: {json.dumps({'done': True, 'latency_ms': round(latency_ms, 2), 'ttft_ms': round(ttft_ms, 2)})}\n\n"

every response will be in streaming. 

### Get Message History

```http
GET /messages/{conversation_id}
```

Response:

```json
[
  {
    "conversation_id": "a1b2c3d4-5678-90ef-gh12-345678901234",
    "role": "user",
    "message": "Hello, how are you?",
    "sequence": 1,
    "timestamp": "2026-06-16T10:04:55Z"
  },
  {
    "conversation_id": "a1b2c3d4-5678-90ef-gh12-345678901234",
    "role": "assistant",
    "message": "Hello! How can I help you today?",
    "sequence": 2,
    "timestamp": "2026-06-16T10:05:00Z"
  }
]
```


## Modes

### Create Mode

```http
POST /modes/
```

Request:

```json
{
  "title": "Code Helper",
  "description": "Assistant optimized for coding",
  "system_prompt": "You are a helpful coding assistant."
}
```

Response:

```json
{
  "mode_id": "mode_123",
  "user_id": "user_123",
  "title": "Code Helper",
  "description": "Assistant optimized for coding",
  "system_prompt": "You are a helpful coding assistant.",
  "updated_at": "2026-06-16T10:10:00Z"
}
```

### List Modes

```http
GET /modes/
```

Response:

```json
[
  {
    "mode_id": "mode_123",
    "user_id": "user_123",
    "title": "Code Helper",
    "description": "Assistant optimized for coding",
    "system_prompt": "You are a helpful coding assistant.",
    "updated_at": "2026-06-16T10:10:00Z"
  }
]
```

### Get Mode

```http
GET /modes/{mode_id}
```

### Delete Mode

```http
DELETE /modes/{mode_id}
```

