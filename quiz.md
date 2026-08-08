# Quiz API Guide

## How Quiz Routes Work

The Quiz module allows users to generate dynamic multiple-choice quizzes using various LLM providers (Google, Groq, OpenRouter) and save them to the database. 

1. **Quiz Generation**: The backend constructs a prompt based on the user's request and sends it to a randomly selected LLM provider.
2. **Validation**: The LLM's JSON response is validated against a strict Pydantic schema (`QuizLLMResponse`) to ensure all questions have exactly 4 options and a valid correct option index.
3. **Storage**: Validated quizzes are saved to MongoDB and associated with the authenticated user's ID.
4. **Authentication**: All quiz endpoints require a valid JWT token in the `Authorization: Bearer <token>` header (using the `authFetch` helper from the Authentication Guide).

---

## API Endpoints

| Method | Endpoint | Description | Auth Required | Request Body | Response |
|--------|----------|-------------|---------------|----------------|----------|
| `POST` | `/quiz/` | Generate and save a new quiz | ✅ Yes | `QuizRequest` JSON | Created Quiz Object |
| `GET` | `/quiz/` | Retrieve all quizzes for the current user | ✅ Yes | - | List of Quiz Objects |

---

## Request & Response Examples

### 1. Create a Quiz (`POST /quiz/`)

Generates a new quiz based on the provided topic, concept, and difficulty.

**Request:**

```http
POST /quiz/
Authorization: Bearer <your_jwt_token>
Content-Type: application/json

{
  "topic": "Python Programming",
  "concept": "Asynchronous Programming",
  "difficulty": "Medium",
  "number_of_questions": 2,
  "additional_description": "Focus on asyncio and event loops."
}


{
  "quiz_id": "123e4567-e89b-12d3-a456-426614174000",
  "user_id": "user_abc123",
  "topic": "Python Programming",
  "concept": "Asynchronous Programming",
  "difficulty": "Medium",
  "questions": [
    {
      "questionNo": 1,
      "question": "What is the primary purpose of the `asyncio` module in Python?",
      "options": [
        "To handle multi-threading",
        "To write concurrent code using the async/await syntax",
        "To manage database connections",
        "To execute CPU-bound tasks faster"
      ],
      "correctOption": 2
    },
    {
      "questionNo": 2,
      "question": "Which of the following is required to run an async function in Python?",
      "options": [
        "A thread pool",
        "An event loop",
        "A separate process",
        "A context manager"
      ],
      "correctOption": 2
    }
  ],
  "created_at": "2026-08-08T10:30:00.000Z",
  "latency_ms": 1450.25,
  "_id": "64f1b2c3d4e5f6a7b8c9d0e1"
}