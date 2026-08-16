# AI Chatbot

A full-stack AI chatbot with streaming chat responses, custom system-prompt "modes," and an AI-generated quiz feature. The frontend is a lightweight vanilla JS single-page app, and the backend is a FastAPI + Python service that integrates multiple LLM providers through LangChain.

---

## Overview

| Piece    | Description |
|----------|-------------|
| Frontend | Static single-page app (HTML, CSS, vanilla JS) — no build step |
| Backend  | FastAPI + Python 3.11 REST API with SSE streaming |
| Database | MongoDB Atlas (async Motor) |
| LLM      | Groq, Google, DeepSeek, OpenRouter via LangChain |
| Auth     | JWT (PyJWT) + PBKDF2-SHA256 password hashing |
| Rate limit | SlowAPI + Redis (Upstash) |
| Deploy   | Docker / Docker Compose, Render (backend), Vercel (frontend) |

---

## Features

- **Authentication** — register, login, logout, session persistence via JWT in `localStorage`.
- **Chat with streaming** — assistant replies stream in token-by-token (SSE) and render as markdown.
- **Multi-provider LLM** — pick a provider and model per conversation (Groq, Google, DeepSeek, OpenRouter).
- **Modes** — reusable "personas" defined by a title, description, and system prompt.
- **Conversations** — create, rename, delete, and auto-title after the first reply.
- **Quiz** — generate quizzes on any topic/concept with adjustable difficulty and question count, then take and score them.
- **Responsive UI** — mobile sidebar drawer, toast notifications, markdown rendering with XSS sanitization.
- **Backend wake-up screen** — polls the health endpoint until a sleeping free-tier host responds.

---

## Getting Started

### Prerequisites

- Python 3.11+
- Node / any static file server (or Docker)
- MongoDB Atlas cluster, Redis (Upstash), and API keys for the LLM providers you want to use

### Backend

1. Copy `.env` from `backend/` and fill in the required variables (see below).
2. Install dependencies and run:

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### Frontend

The frontend has no build step. Serve it with any static server, or run both services together with Docker Compose:

```bash
docker compose up
```

The frontend automatically points at `http://localhost:8000` when served locally and at the production backend URL otherwise.

---

## Project Structure

```
ChatBot/
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── render.yaml
│   └── app/
│       ├── main.py                        # FastAPI app, lifespan, CORS, routers, health check
│       ├── config/settings.py             # Env vars: API keys, DB, Redis, JWT, CORS
│       ├── core/
│       │   ├── limiter.py                 # SlowAPI limiter bound to Redis (Upstash)
│       │   └── security.py                # JWT encode/decode, PBKDF2 hashing, auth dependency
│       ├── database/
│       │   ├── mongodb.py                 # Motor client + collection references
│       │   └── indexes.py                 # MongoDB index creation on startup
│       ├── routes/                        # auth, conversation, message, mode, quiz routers
│       ├── schemas/                       # Pydantic request/response models
│       └── services/
│           ├── langchain_provider.py      # Multi-provider LLM factory + chat/stream
│           └── langchain_provider_quiz.py # Quiz generator with retry/fallback logic
└── frontend/
    ├── Dockerfile                         # nginx serving static files
    ├── nginx.conf                         # Static files + API reverse proxy
    ├── vercel.json                        # Rewrites all routes to index.html
    ├── index.html                         # Main SPA
    └── assets/
        ├── css/styles.css
        ├── js/                            # config, auth, api, state, ui, app
        └── quiz/                          # quiz.html, quiz.js, styles.css
```

---

## Backend

The backend exposes a REST API plus SSE streaming for chat responses and integrates multiple LLM providers through LangChain.

### Tech Stack

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

### Implementation Notes

- **JWT auth** — PBKDF2-SHA256 (200,000 iterations) with per-user salt; protected routes use the `get_current_user` dependency.
- **Rate limiting** — SlowAPI bound to Upstash Redis: `/auth/login` 5/min, create conversation 5/min, POST `/messages` 5/min, POST `/quiz` 2/min.
- **Multi-provider LLM** — a `LLMFactory` builds the right LangChain chat model from provider + model (Groq, Google, DeepSeek, OpenRouter; Ollama supported locally).
- **Streaming** — chunks are emitted as SSE `data:` events followed by a `done` event carrying `latency_ms` and `ttft_ms`.
- **Context window** — the last 10 messages (plus an optional mode system prompt) are sent per request.
- **Auto-renaming** — new conversations start as `"NEW CONVERSATION"`; after the first reply the LLM generates a 2–4 word title.
- **Quiz generation** — up to 5 attempts across a curated provider/model list with JSON retry/fallback, validated by Pydantic.

### API Surface

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

### Environment Variables

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

---

## Frontend

A static, single-page web application built with plain HTML, CSS, and vanilla JavaScript — no build step, no framework, no package manager.

### Tech Stack

| Piece          | Technology                                                  |
| -------------- | ----------------------------------------------------------- |
| Markup         | Semantic HTML5 (`index.html`, `assets/quiz/quiz.html`)      |
| Styling        | Custom CSS (`assets/css/styles.css`, `assets/quiz/styles.css`) |
| JavaScript     | Vanilla ES modules (`assets/js/*.js`, `assets/quiz/quiz.js`) |
| Markdown       | `marked` (CDN) for rendering assistant replies              |
| Sanitization   | `DOMPurify` (CDN) to clean rendered markdown                |
| Backend API    | REST + SSE-style streaming, accessed via `fetch`            |
| Auth           | JWT tokens stored in `localStorage`                         |

### How It Works

- **`config.js`** decides which backend to talk to (`http://localhost:8000` locally, otherwise the production URL) and holds the provider/model lists.
- **`api.js`** wraps every backend call and auto-attaches the `Authorization: Bearer <token>` header; streaming is read with `fetch` + `ReadableStream` and parsed line-by-line.
- **`ui.js`** renders conversation/mode lists and message bubbles; assistant replies are rendered as markdown via `marked` and sanitized with `DOMPurify`.
- **`app.js`** is the controller — screens, events, modals, the mobile sidebar, and the streaming send/receive loop, plus the "waking up" splash screen.

### Serving

- **Docker / nginx** — the Dockerfile copies static files into nginx, which reverse-proxies API routes to the backend (streaming enabled on `/messages/`).
- **Docker Compose** — the `frontend` service maps port `8501 → 80` and depends on the backend.
- **Vercel** — `vercel.json` rewrites every route to `index.html`.

---

## Usage

1. Open the app in a browser — a boot screen shows while the backend wakes up.
2. Log in or register (auto-login on registration).
3. From the home screen, choose **💬 Chat** or **📝 Quiz**.

- **Chat**: create a conversation (pick provider, model, optional mode) or just type to auto-create one. Stream replies, rename, delete, and switch conversations from the sidebar. **Enter** sends, **Shift+Enter** adds a new line.
- **Modes**: create a mode with a title, description, and system prompt, then attach it to conversations to steer the assistant.
- **Quiz**: generate quizzes by topic, concept, difficulty, and question count (1–10), then take and score them instantly.

---

## Deployment

- **Backend**: Render (`render.yaml`) runs uvicorn on `$PORT`; Docker runs it on port 8000.
- **Frontend**: any static host (Vercel via `vercel.json`, nginx via Docker, etc.).
- **Together**: `docker compose up` runs both services with `.env` loaded.
