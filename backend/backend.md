# Backend Architecture

The backend is a FastAPI + Python service that powers the AI Chatbot. It exposes a REST API plus Server-Sent Events (SSE) streaming for chat responses, and integrates multiple LLM providers through LangChain.

---

## Tech Stack

| Layer        | Technology |
|--------------|------------|
| Language     | Python 3.11 |
| Web framework| FastAPI + Uvicorn |
| Database     | MongoDB (Atlas, cloud) via Motor (async) + PyMongo |
| Validation   | Pydantic v2 + Pydantic Settings |
| Auth         | JWT (PyJWT) + PBKDF2-SHA256 password hashing |
| Rate limiting| SlowAPI + Redis (Upstash / cloud) |
| LLM layer    | LangChain (`langchain-core`, `langchain-groq`, `langchain-openai`, `langchain-google-genai`, `langchain-ollama`) |
| Streaming    | SSE via `sse-starlette` / FastAPI `StreamingResponse` |
| Config       | `python-dotenv` (environment variables) |
| Deployment   | Render (free plan) / Docker + Docker Compose |

---

## Project Structure

```
backend/
├── Dockerfile
├── requirements.txt
└── app/
    ├── main.py                        # FastAPI app, lifespan, CORS, routers, health check
    ├── config/
    │   └── settings.py                # Env vars: API keys, DB, Redis, JWT, CORS
    ├── core/
    │   ├── limiter.py                 # SlowAPI limiter bound to Redis (Upstash)
    │   └── security.py                # JWT encode/decode, PBKDF2 hashing, auth dependency
    ├── database/
    │   ├── mongodb.py                 # Motor client + collection references
    │   └── indexes.py                 # MongoDB index creation on startup
    ├── routes/
    │   ├── auth_routes.py             # /auth (register, login, me)
    │   ├── conversation_routes.py     # /conversations (CRUD)
    │   ├── message_routes.py          # /messages (send SSE stream, get history)
    │   ├── mode_routes.py             # /modes (CRUD system-prompt modes)
    │   └── quiz_route.py              # /quiz (generate, list, delete)
    ├── schemas/                       # Pydantic request/response models
    │   ├── user_schema.py
    │   ├── conversation_schema.py
    │   ├── message_schema.py
    │   ├── mode_schema.py
    │   └── quiz_schema.py
    └── services/                      # Business logic
        ├── auth_service.py
        ├── conversation_service.py
        ├── message_service.py
        ├── mode_service.py
        ├── quiz_service.py
        ├── langchain_provider.py      # Multi-provider LLM factory + chat/stream
        └── langchain_provider_quiz.py # Quiz generator with retry/fallback logic
```

---

## How Each Feature Is Implemented

### 1. Configuration (`app/config/settings.py`)
All configuration is read from the environment via `python-dotenv`:
- Provider API keys: `GROQ_API_KEY`, `GOOGLE_API_KEY`, `DEEPSEEK_API_KEY`, `OPENROUTER_API_KEY`
- `MONGO_URI`, `DATABASE_NAME`
- `REDIS_URL` (Upstash)
- JWT settings: `SECRET_KEY`, `ALGORITHM` (HS256), `ACCESS_TOKEN_EXPIRE_MINUTES`
- `CORS_ORIGINS` (comma-separated list, parsed into a list)

### 2. Database — MongoDB Atlas (`app/database/mongodb.py`)
- A single async `AsyncIOMotorClient` connects to the Atlas cluster (`MONGO_URI`).
- Connection pool settings: `maxPoolSize=50`, `minPoolSize=10`, `serverSelectionTimeoutMS=5000`.
- Five collections are exposed: `users`, `conversations`, `messages`, `modes`, `quizes`.

### 3. Indexes for Performance (`app/database/indexes.py`)
Indexes are created automatically on every app startup (in the FastAPI `lifespan`). Index creation failures are logged as non-fatal warnings so the app still boots:
- **users**: unique on `user_id`, unique on `username`
- **conversations**: unique on `conversation_id`, compound `(user_id, updated_at DESC)` for fast sidebar listing
- **messages**: unique compound `(conversation_id, sequence)` — enforces ordering/duplicates
- **modes**: unique on `mode_id`, unique compound `(user_id, mode_id)`
- **quizes**: unique on `quiz_id`, compound `(user_id, created_at DESC)`

### 4. JWT Authentication (`app/core/security.py`)
- Passwords are hashed with **PBKDF2-SHA256** (200,000 iterations) with a per-user random salt, stored as `pbkdf2_sha256$...`.
- Passwords are verified with a constant-time `hmac.compare_digest`.
- On login a JWT (`HS256`) is issued containing `sub` (user_id), `username`, and `exp`.
- Protected routes use the `get_current_user` dependency (`HTTPBearer`), which decodes the token and loads the user from Mongo; invalid/missing users get `401`.

### 5. Redis Rate Limiting — Upstash (`app/core/limiter.py`)
- SlowAPI `Limiter` is connected to the Upstash Redis instance via `REDIS_URL`.
- `ssl_cert_reqs=None` disables strict cert verification for cloud-managed Redis.
- Applied via decorators:
  - `/auth/login` → **5/minute**
  - POST `/conversations` (create conversation) → **5/minute**
  - POST `/messages` (get AI reply) → **5/minute**
  - POST `/quiz` (generate quiz) → **2/minute**
- A `RateLimitExceeded` handler returns a clean HTTP 429.

### 6. Multi-Provider LLM Integration (`app/services/langchain_provider.py`)
A `LLMFactory` builds the right LangChain chat model from `provider` + `model`:
- **groq** → `ChatGroq`
- **google** → `ChatGoogleGenerativeAI`
- **deepseek** → `ChatOpenAI` with `base_url="https://api.deepseek.com"`
- **openrouter** → `ChatOpenAI` with `base_url="https://openrouter.ai/api/v1"`
- `langchain-ollama` is also in requirements for local Ollama support.

History messages are converted to LangChain `SystemMessage` / `HumanMessage` / `AIMessage`.

### 7. Streaming Responses (SSE)
- `generate_stream()` calls `llm.astream()` and yields each text chunk.
- `message_service.send_message()` wraps the generator in a FastAPI `StreamingResponse` with `media_type="text/event-stream"`.
- Chunks are emitted in SSE `data: {...}` events, followed by a final `done` event carrying `latency_ms` (total) and `ttft_ms` (time-to-first-token).
- On failure an SSE `error` event is sent instead.

### 8. Context Window Management (`app/services/message_service.py`)
- Before each AI call, the last **10 messages** of the conversation are fetched (sorted by `sequence` desc, then reversed to chronological order).
- The new user message is appended, and optionally a `system` message from the conversation's mode is prepended — keeping the prompt within a bounded context window.

### 9. Automatic Conversation Renaming (`app/services/message_service.py`)
- New conversations start titled `"NEW CONVERSATION"`.
- After the first AI reply, `generate_title()` asks an LLM to produce a short 2–4 word title from the user's first message, strips quotes, falls back to `"NEW CONVERSATION"`, and updates the conversation title via `_update_conversation_title()`.

### 10. Modes (Custom System Prompts) (`app/services/mode_service.py`)
- Users can create modes: `title`, `description`, and a `system_prompt`.
- A mode is attached to a conversation via `mode_id`; at generate time the system prompt is injected into the context.
- Modes are validated to belong to the current user; deleting a mode sets `mode_id` to `None` on all affected conversations.

### 11. Quiz Generation with Retries (`app/services/langchain_provider_quiz.py`)
- `generate_quiz()` tries up to **5 attempts** (`MAX_RETRIES = 5`).
- Each attempt randomly picks a provider/model from a curated list (Google + Groq), calls the LLM once, strips markdown code fences if present, and parses the JSON.
- If parsing/validation fails on an attempt, it falls through to the next provider/model, giving resilience against per-provider failures.
- The response is validated with Pydantic (`QuizLLMResponse`: exactly 4 options, `correctOption` 1–4, question count bounds), then stored in the `quizes` collection with measured `latency_ms`.

### 12. CORS & Deployment (`app/main.py`)
- CORS is configured from `CORS_ORIGINS` env (comma-separated). This makes the API work both **locally** (e.g. `http://localhost:8501`) and **in production** (e.g. the Vercel/Netlify frontend URL).
- **Render**: `render.yaml` defines the backend service (uvicorn on `$PORT`, free plan).
- **Docker**: `Dockerfile` runs uvicorn on port 8000; `docker-compose.yml` runs backend + frontend together with `.env` loaded.

---

## API Surface

| Method | Endpoint         | Auth   | Rate limited | Description |
|--------|------------------|--------|--------------|-------------|
| POST   | `/auth/register` | No     | —            | Create account |
| POST   | `/auth/login`    | No     | 5/min        | Login, returns JWT |
| GET    | `/auth/me`       | Yes    | —            | Current user |
| POST   | `/conversations` | Yes    | 5/min        | Create conversation |
| GET    | `/conversations` | Yes    | —            | List conversations |
| GET    | `/conversations/{id}` | Yes | —          | Conversation detail |
| PATCH  | `/conversations` | Yes    | —            | Rename conversation |
| DELETE | `/conversations/{id}` | Yes | —         | Delete conversation |
| POST   | `/messages`      | Yes    | 5/min        | Send message, SSE stream reply |
| GET    | `/messages/{conversation_id}` | Yes | —  | Message history |
| POST   | `/modes`         | Yes    | —            | Create mode (system prompt) |
| GET    | `/modes`         | Yes    | —            | List modes |
| GET    | `/modes/{id}`    | Yes    | —            | Mode detail |
| DELETE | `/modes/{id}`    | Yes    | —            | Delete mode |
| POST   | `/quiz`          | Yes    | 2/min        | Generate quiz |
| GET    | `/quiz`          | Yes    | —            | List quizzes |
| DELETE | `/quiz/{id}`     | Yes    | —            | Delete quiz |
| GET    | `/` and `/health` | No    | —            | Health check |

---

## Environment Variables

```
APP_ENV
GROQ_API_KEY
GOOGLE_API_KEY
DEEPSEEK_API_KEY
OPENROUTER_API_KEY
MONGO_URI
DATABASE_NAME
REDIS_URL
SECRET_KEY
ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES
CORS_ORIGINS
```