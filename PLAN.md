# XClipboard - Project Plan

## Overview

XClipboard is a self-hosted web application for sharing text snippets across devices. Users can save text to a server, view their 25 most recent clips, and copy them to their clipboard with one click. Multi-user support is built in from day one, with session-based authentication.

## Tech Stack

- **Frontend**: React + Tailwind CSS (mobile-first responsive design)
- **Backend**: FastAPI (Python)
- **Database**: SQLite
- **Authentication**: Session cookies (HttpOnly, Secure, SameSite flags)
- **Hosting**: Self-hosted with existing domain/hardware and HTTPS (Cloudflare proxy)

## Database Schema

### USERS Table

- `id` (INTEGER PRIMARY KEY)
- `username` (TEXT UNIQUE)
- `password_hash` (TEXT) — bcrypt hashed

### CLIPS Table

- `id` (INTEGER PRIMARY KEY)
- `user_id` (INTEGER FOREIGN KEY → USERS.id)
- `text` (TEXT)
- `created_at` (TIMESTAMP)

## Authentication Flow

1. Unauthenticated users → Login page
2. Valid credentials → Session cookie set (server-side session storage)
3. Cookie persists across browser refreshes (user stays logged in)
4. Logout button clears session

**Session Cookie Configuration**:

- HttpOnly flag (prevents JavaScript access)
- Secure flag (HTTPS only)
- SameSite=Lax (CSRF protection)
- Reasonable expiration (e.g., 7 days)

## UI/UX - Phase 1 MVP

### Layout (Mobile-First)

- **Title bar**: "XClipboard" header with logout button (top-right)
- **Textarea**: Large text input occupying most of the screen
- **Action buttons** (below textarea):
  - "Copy to Clipboard" (Browser Clipboard API; button color changes on success)
  - "Save Clip to Server" (POST to backend)
- **Clips drawer** (optional, collapsible): Displays the 25 most recent clips in chronological order (newest first). Each clip entry shows timestamp and truncated text with a one-click copy button.

**Responsive Design**:

- Mobile (default): Full-width textarea, buttons stacked vertically
- Desktop (min-width breakpoint): Textarea + buttons positioned side-by-side as needed
- Touch-friendly button sizing (min 44px height)

## Core Features - Phase 1

### Backend

- **POST /auth/login**: Accept username + password, return session cookie
- **POST /auth/logout**: Clear session
- **GET /clips**: Fetch user's 25 most recent clips (requires auth)
- **POST /clips**: Create new clip (requires auth)
- Session middleware to protect authenticated endpoints

### Frontend

- **Login page**: Username/password form, error handling
- **Main app page**: Textarea, action buttons, clips drawer
- Copy-to-clipboard button with visual feedback (text/color change)
- Fetch clips on mount and after saving
- Responsive Tailwind styling

### Database

- User account creation (initial setup, phase 1 may not have a signup UI, just manual DB insertion or simple setup script)
- Clip CRUD operations

## Implementation Breakdown

### Database Setup

- SQLite schema creation
- Bcrypt integration for password hashing

### Backend (FastAPI)

- Session management middleware
- Authentication endpoints
- Clips endpoints (GET, POST)
- Error handling and validation

### Frontend (React)

- Login page component
- Main app component (textarea, buttons, drawer)
- Clips list component
- API client functions
- Tailwind CSS responsive styling

## Phase 2 Considerations

- Clipboard history UI improvements (search, filters, delete individual clips)
- Device naming/identification (track which device saved each clip)
- Read-only mode for shared/guest access
- File/image support (not just text)
- Refresh token implementation for extended sessions
- User signup/registration page (invite-based or open)
- Analytics (most-copied clips, usage patterns)
- Keyboard shortcuts (e.g., Escape to clear textarea, Ctrl+S to save)
