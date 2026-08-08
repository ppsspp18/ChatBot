# AI Chatbot

## Features

- **Authentication**: Uses JWT authentication. All API endpoints require a valid authentication token.
- **Mobile friendly UI**: The interface is responsive and works well on phones. On small screens the chat sidebar becomes a slide-out drawer toggled from the top bar.
- **Navigation**: After login, the main home page provides a simple, mobile-friendly choice between the Quiz page and the Chat page.
- **Conversations**:
  - Create new conversations from a modal popup (provider, model, and optional mode).
  - Conversation names update automatically based on context.
  - Users can manually edit conversation names.
  - Users can delete conversations.
  - Supports streaming responses for messages.
- **Chat Sidebar**:
  - Slide-out sidebar (mobile drawer) containing new-conversation, mode management, and conversation history.
  - Modes are managed inline in the sidebar; the create-mode popup is kept simple (title, description, system prompt).
- **Chat Modes**:
  - Users have the option to select a specific mode or continue without one.
  - Users can create new custom modes.
  - Users can delete modes.
- **Quizzes**:
  - Lists all user quizzes with topic, concept, difficulty, and number of questions.
  - Click any quiz in the list to open and take it.
  - "New Quiz" opens a simple popup to enter details (topic, concept, difficulty, up to 10 questions); the generated quiz is shown immediately.