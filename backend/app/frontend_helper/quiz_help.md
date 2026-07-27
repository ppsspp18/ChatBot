```markdown
# Quiz API - Frontend Integration Guide

## Base URL
http://localhost:8000


## Endpoints

### 1. Create Quiz
**`POST /quiz/`**

Generate a new quiz using AI.

#### Request Body
```json
{
  "topic": "string (required)",
  "concept": "string (required)",
  "difficulty": "Easy | Medium | Hard (required)",
  "number_of_questions": "integer (1-100, required)",
  "additional_description": "string (optional)"
}
```

#### Example Request
```javascript
const response = await fetch('http://localhost:8000/quiz/', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    topic: "Python",
    concept: "Decorators",
    difficulty: "Medium",
    number_of_questions: 5,
    additional_description: "Focus on practical use cases"
  })
});
const quiz = await response.json();
```

#### Example Response (`201`)
```json
{
  "_id": "507f1f77bcf86cd799439011",
  "session_id": "quiz_20260127143022_a1b2c3d4e5f6",
  "sequence": 1,
  "topic": "Python",
  "concept": "Decorators",
  "difficulty": "Medium",
  "title": "Python Decorators Quiz",
  "questions": [
    {
      "questionNo": 1,
      "question": "What does @staticmethod do?",
      "options": [
        "Binds method to class",
        "Makes method static",
        "Removes self parameter binding",
        "Creates class variable"
      ],
      "correctOption": 3
    }
  ],
  "created_at": "2026-01-27T14:30:22.123Z",
  "inference_log_id": "abc123def456"
}
```

#### Error Response (`500`)
```json
{
  "detail": "Error message"
}
```

---

### 2. Get All Quizzes
**`GET /quiz/`**

Fetch all previously generated quizzes (newest first).

#### Example Request
```javascript
const response = await fetch('http://localhost:8000/quiz/');
const quizzes = await response.json();
```

#### Example Response (`200`)
```json
[
  {
    "_id": "507f1f77bcf86cd799439011",
    "session_id": "quiz_20260127143022_a1b2c3d4e5f6",
    "sequence": 1,
    "topic": "Python",
    "concept": "Decorators",
    "difficulty": "Medium",
    "title": "Python Decorators Quiz",
    "questions": [...],
    "created_at": "2026-01-27T14:30:22.123Z",
    "inference_log_id": "abc123def456"
  }
]
```

