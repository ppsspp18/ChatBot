# Frontend Authentication Guide

This document outlines how to implement authentication in your frontend application to interact with the FastAPI backend. The backend uses **JSON Web Tokens (JWT)** for stateless authentication.

## 1. Authentication Flow
1. **Register / Login:** The user submits their credentials to the backend.
2. **Token Issuance:** On success, the backend returns a JWT `access_token`.
3. **Token Storage:** The frontend stores this token securely (e.g., `localStorage`, `sessionStorage`, or memory).
4. **Authenticated Requests:** For every subsequent request to protected all endpoints, the frontend attaches the token in the `Authorization` header.

---

## 2. API Endpoints

### Register
- **Endpoint:** `POST /auth/register`
- **Payload:**
  ```json
  {
    "username": "string",
    "password": "string"
  }
  ```
- **Success Response (200):**
  ```json
  {
    "user_id": "uuid",
    "username": "string",
    "created_at": "2024-01-01T00:00:00Z"
  }
  ```
- **Errors:** `409 Conflict` (Username already exists).

### Login
- **Endpoint:** `POST /auth/login`
- **Payload:**
  ```json
  {
    "username": "string",
    "password": "string"
  }
  ```
- **Success Response (200):**
  ```json
  {
    "access_token": "eyJhbGciOiJIUzI1...",
    "token_type": "bearer"
  }
  ```
- **Errors:** `401 Unauthorized` (Incorrect username/password).

### Get Current User
- **Endpoint:** `GET /auth/me`
- **Headers:** `Authorization: Bearer <access_token>`
- **Success Response (200):** Returns `UserResponse` object (`user_id`, `username`, `created_at`).
- **Errors:** `401 Unauthorized` (Invalid, expired, or missing token).

---