# XClipboard Backend Implementation Guide

## Quick Reference

### File Structure

```
XClipboard/
├── db/
│   └── CreateTables.py
├── back/
│   ├── ClipModels.py       (Pydantic models for API)
│   ├── ClipBackend.py      (FastAPI application & endpoints)
│   ├── logger.py           (Logging setup)
│   └── bruno/              (API test requests)
│       ├── bruno.json
│       ├── environments/
│       │   └── local.bru
│       ├── Auth/
│       │   ├── POST login.bru
│       │   ├── POST logout.bru
│       │   └── POST add user.bru
│       └── Clips/
│           ├── GET clips.bru
│           └── POST clip.bru
├── PLAN.md
├── BACKEND_IMPL.md (this file)
└── xclipboard.db   (SQLite database)
```

---

## Authentication & Sessions

### Password Hashing

- **Library**: `bcrypt`
- **Approach**: Automatic salt generation (no configuration needed)
- **Usage**:
  ```python
  import bcrypt
  hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt())  # Store this
  valid = bcrypt.checkpw(password.encode(), stored_hash)        # Verify on login
  ```

### Session Management

- **Storage**: In-memory dictionary (session_id → username)
  - Lost on server restart (acceptable for MVP)
  - Format: `sessions = {uuid_string: "username"}`
- **Session Cookie Configuration**:
  ```python
  response.set_cookie(
      key="session_id",
      value=session_id_uuid,
      httponly=True,      # No JavaScript access
      secure=True,        # HTTPS only
      samesite="lax",     # CSRF protection
      max_age=604800      # 7 days (in seconds)
  )
  ```

### Admin Token

- Environment variable: `ADMIN_TOKEN`
- **Validation**: Check `X-Admin-Token` header matches the env var
- Return `403 Forbidden` if invalid or missing on admin endpoints

---

## API Endpoints

### 1. POST /auth/login

**Purpose**: Authenticate user and create session

**Request**:

```json
{
  "username": "string",
  "password": "string"
}
```

**Response (201 Created)**:

```json
{
  "message": "Login successful",
  "username": "string"
}
```

Sets `session_id` cookie automatically.

**Errors**:

- `400`: Invalid username/password
- `422`: Validation error (missing fields)

---

### 2. POST /auth/logout

**Purpose**: Invalidate session

**Headers**:

- Cookie: `session_id` (required)

**Response (200 OK)**:

```json
{
  "message": "Logged out successfully"
}
```

**Errors**:

- `401`: Invalid/missing session

---

### 3. POST /auth/register (Admin Only)

**Purpose**: Add a new user to the system

**Headers**:

- `X-Admin-Token`: Must match `ADMIN_TOKEN` env var

**Request**:

```json
{
  "username": "string",
  "password": "string"
}
```

**Response (201 Created)**:

```json
{
  "message": "User created",
  "username": "string"
}
```

**Errors**:

- `403`: Invalid/missing admin token
- `400`: Username already exists
- `422`: Validation error (missing fields)

---

### 4. GET /clips

**Purpose**: Fetch user's 25 most recent clips (newest first)

**Headers**:

- Cookie: `session_id` (required)

**Response (200 OK)**:

```json
{
  "clips": [
    {
      "clip_id": 1,
      "clip_text": "string",
      "created_at": "2026-04-25T14:30:45-04:00"
    }
  ]
}
```

- Maximum 25 clips returned
- Sorted by `created_at` descending (newest first)

**Errors**:

- `401`: Invalid/missing session

---

### 5. POST /clip

**Purpose**: Save a single clip for the authenticated user

**Headers**:

- Cookie: `session_id` (required)

**Request**:

```json
{
  "clip_text": "string"
}
```

**Response (201 Created)**:

```json
{
  "message": "Clip saved",
  "clip_id": 1,
  "created_at": "2026-04-25T14:30:45-04:00"
}
```

**Errors**:

- `401`: Invalid/missing session
- `400`: Empty clip_text
- `422`: Validation error

---

## Timestamps

- **Format**: ISO 8601 with timezone
- **Timezone**: US Eastern (UTC-4 or UTC-5 depending on DST)
- **Example**: `2026-04-25T14:30:45-04:00`
- **Implementation**: Use Python's `datetime` with `timezone.utc` or system timezone awareness

**Database Storage**: Store as ISO 8601 string for consistency

---

## Logging

### Requirements

- Log all API requests: method, path, status code, response time
- Log errors with appropriate context
- Format: console (human-readable) + file (JSON, optional for MVP)
- Can be simpler than the PredictionGame logger (no need to be as verbose)

### Key Implementation Detail

- Disable Uvicorn's default access logging:
  ```python
  import logging
  logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
  ```

---

## Error Handling

**Standard Error Response**:

```json
{
  "error": "error message"
}
```

**HTTP Status Codes**:

- `200 OK`: Successful GET or POST
- `201 Created`: Resource created (login, register, clip saved)
- `400 Bad Request`: Invalid input
- `401 Unauthorized`: Missing/invalid session
- `403 Forbidden`: Invalid admin token
- `422 Unprocessable Entity`: Validation error
- `500 Internal Server Error`: Server error

---

## Environment Variables

```
ADMIN_TOKEN=your_secret_admin_token_here
```

---

## CORS

**Not needed** — frontend and backend run on same server/origin

---

## Dependencies to Install

```
fastapi
uvicorn
bcrypt
pydantic
python-multipart
```

---

## Notes for Implementation

1. **Session Middleware**: Create a dependency or middleware to extract and validate `session_id` cookie on protected endpoints
2. **Admin Middleware/Dependency**: Similar to session validation but checks `X-Admin-Token` header
3. **Database Connection**: Centralize SQLite connection logic (consider a simple connection helper)
4. **Request/Response Models**: Use Pydantic for type validation and auto-documentation
5. **Sorting**: Use SQL `ORDER BY created_at DESC LIMIT 25` in GET /clips query
