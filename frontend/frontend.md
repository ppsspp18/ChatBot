# Frontend

This document explains how the chatbot's frontend was built, what features it has, and how to use the web app.

---

## 1. How the Frontend Was Created

The frontend is a **static, single-page web application** built with plain HTML, CSS, and vanilla JavaScript. It has **no build step, no framework, and no package manager** — it is served as-is, which keeps it lightweight, fast to load, and easy to deploy on any static host.

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

### Project Structure

```
frontend/
├── Dockerfile          # Builds an nginx image that serves the static files
├── nginx.conf          # Serves static files and reverse-proxies API routes to the backend
├── vercel.json         # Rewrites all routes to index.html (for Vercel deploys)
├── index.html          # Main SPA: boot, auth, home, and chat screens
└── assets/
    ├── css/styles.css  # Main app styles (auth, home, chat, modals, sidebar)
    ├── js/
    │   ├── config.js   # Backend URL resolution + provider/model lists
    │   ├── auth.js     # Token & user persistence helpers (localStorage)
    │   ├── api.js      # All fetch calls to the backend (auth, chat, quiz)
    │   ├── state.js    # In-memory app state (conversations, modes, messages)
    │   ├── ui.js       # DOM rendering helpers (messages, lists, toasts, markdown)
    │   └── app.js      # Main controller: screens, events, streaming, modals
    └── quiz/
        ├── quiz.html   # Separate quiz page (list + take-a-quiz views)
        ├── quiz.js     # Quiz logic: create, list, delete, and submit quizzes
        └── styles.css  # Quiz page styles
```

### How It Is Put Together

- **`config.js`** decides which backend to talk to: `http://localhost:8000` when running on `localhost`/`127.0.0.1`, otherwise the production URL (`https://chatbot-j3lf.onrender.com`). It also holds the list of supported LLM providers and their models (e.g. Google `gemma-4-26b-a4b-it`, Groq `openai/gpt-oss-120b`).
- **`auth.js`** stores the JWT access token and the logged-in user object in `localStorage`, and exposes helpers to read, write, and clear them.
- **`api.js`** wraps every backend call (`/auth/*`, `/conversations/*`, `/messages/*`, `/modes/*`, `/quiz/*`, `/health`). Every request automatically attaches `Authorization: Bearer <token>`. Streaming responses are read with `fetch` + a `ReadableStream` reader and parsed line-by-line as SSE-ish `data:` events.
- **`state.js`** keeps a single in-memory store of conversations, modes, the selected conversation, its messages, and whether a response is currently streaming.
- **`ui.js`** owns all DOM rendering: conversation lists, mode lists, message bubbles, toasts, and an empty-state helper. Assistant messages are rendered as **markdown** via `marked`, and the output is sanitized with `DOMPurify` to prevent XSS.
- **`app.js`** is the controller. It handles screen switching (auth → home → chat), event binding, modals, the mobile sidebar, form submissions, and the streaming send/receive loop. It also shows a "waking up" splash screen while the backend starts (needed because free-tier hosts put the server to sleep).

### How It Is Served

The frontend is a collection of static files, so it can run anywhere:

- **Docker / nginx** — `Dockerfile` copies the HTML, CSS, and JS into an nginx container. `nginx.conf` serves the static files and **reverse-proxies** the `/auth/`, `/conversations/`, `/messages/`, `/modes/`, `/quiz/`, `/metrics/`, and `/ingest/` routes to the backend. `/messages/` is configured for streaming (buffering off, long read timeout).
- **Docker Compose** — the `frontend` service maps port `8501 → 80` and depends on the `backend` service.
- **Vercel** — `vercel.json` enables clean URLs and rewrites every route to `index.html`.

---

## 2. Features

### Authentication

- **Register** — create an account with a username and password (password must be at least 6 characters, and the confirmation must match). Registration auto-logs you in.
- **Login / Logout** — log in with your credentials; logout clears the token and returns you to the login screen.
- **Session persistence** — your session survives page refreshes because the token lives in `localStorage`.

### Backend Wake-up Screen

- On load, the app pings the backend health endpoint. If the server is asleep (common on free hosting tiers), a "Please wait, we are getting ready..." screen is shown and the app polls until the backend responds, then proceeds.

### Home Screen

- Greets you by username and offers two options: **Chat** and **Quiz**.

### Chat

- **Conversations** — create new conversations from a modal where you pick a **provider**, a **model**, and optionally a **mode**. Conversation titles are editable (rename) and conversations can be deleted.
- **Quick start** — if you type a message without opening a conversation first, the app automatically creates one for you with a random provider/model.
- **Streaming responses** — assistant replies stream in live (token by token) and render as markdown in real time.
- **Mode support** — pick a custom mode when creating a conversation, or go without one.
- **Message composer** — multi-line textarea with auto-resize; **Enter** sends, **Shift+Enter** makes a new line.

### Modes

- Modes are reusable "personas" defined by a **title**, a short **description**, and a **system prompt**.
- Create, list, and delete modes from the sidebar.

### Sidebar

- On desktop it is a permanent left panel; on mobile it becomes a **slide-out drawer** opened via the hamburger button.
- Shows your conversation history, lets you start a new conversation, and manage modes.

### Quiz

- **Create quizzes** — a "New Quiz" modal asks for a topic, concept, difficulty (Easy/Medium/Hard), and number of questions (1–10), plus an optional extra description. The quiz is generated by the backend LLM and shown immediately.
- **Take quizzes** — click a quiz card to open it; answer multiple-choice questions and press "Submit Quiz" to get an instant score with correct/wrong highlighting per question.
- **Manage quizzes** — your quiz list shows topic, concept, difficulty, question count, and creation date; quizzes can be deleted.

### General UX

- Responsive design that works well on phones and desktops.
- Toast notifications for feedback (success, error, info).
- Markdown rendering of assistant replies with XSS sanitization.

---

## 3. How to Use the Web App

1. **Open the app** in a browser. You'll see the boot screen while the backend wakes up (can take up to a minute on free-tier hosts).

2. **Log in or register**:
   - Use the **Login** tab if you already have an account.
   - Use the **Register** tab to create one (username + password + confirm password). Registration signs you in automatically.

3. **Home screen** — you'll be greeted by username with two cards:
   - **💬 Chat** — go to the chat workspace.
   - **📝 Quiz** — go to the quiz page.

### Using Chat

- **Start a conversation**:
  - Click **+ New Conversation** in the sidebar, choose a provider, model, and optional mode, then click **Create Conversation**. It will appear in the sidebar under *Conversations*.
  - Or just type a message in the composer and press **Send** — a conversation is created for you automatically.
- **Chat** — type your message and press **Enter** (or click **Send**). The assistant's reply streams in and renders as formatted markdown. Wait for the current reply to finish before sending the next message.
- **Switch conversations** — click any conversation in the sidebar to open it.
- **Rename** — click the **Rename** button on a conversation and enter a new name.
- **Delete** — click the **Delete** button and confirm. The chat panel resets if you deleted the active conversation.
- **Refresh** — use the **Refresh** button in the top bar to re-sync conversations and modes.
- **Home / Logout** — use the buttons in the top bar to return home or log out.
- **On mobile** — tap the hamburger (☰) to open the sidebar drawer, and ✕ to close it.

### Creating / Managing Modes

- Click **+ New Mode** in the sidebar.
- Fill in **Title**, **Description**, and **System Prompt**, then click **Create Mode**.
- Modes appear under *Modes* in the sidebar, where you can delete them.
- When creating a conversation you can attach one of your modes to steer the assistant's behavior.

### Using Quiz

- Click **📝 Quiz** from the home screen.
- Click **+ New Quiz**, fill in the **Topic**, **Concept**, **Difficulty**, and **Number of Questions** (1–10, optional extra description), then click **Generate Quiz**. Wait a few seconds while it generates.
- Click a quiz card to open it and answer the questions. When done, press **Submit Quiz** to see your score and which answers were right/wrong.
- Delete a quiz with the ✕ button on its card.
- Use **← Home** to return to the home screen and **Logout** to sign out.
