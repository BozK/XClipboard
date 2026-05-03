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
- Refresh token implementation for extended sessions
- User signup/registration page (invite-based or open)
- Analytics (most-copied clips, usage patterns)
- Keyboard shortcuts (e.g., Escape to clear textarea, Ctrl+S to save)
- Link detection in text clips (auto-linkify URLs starting with `http`, clickable in clips drawer)

### File/image storage

**Backend Changes:**

- **Database schema**: Add `CLIPS_FILES` table or extend `CLIPS` to support `content_type` (text/image/pdf/etc) and `file_path`/blob storage
- **File storage strategy**:
  - SQLite BLOB: Simple, all data in one file, but bloats database (suitable for MVP)
  - Filesystem storage: Store files on disk with references in DB (more scalable, requires disk management)
  - S3/external storage: Best for production, requires external service setup
- **Upload endpoint**: `POST /clips/file` handling multipart form data with MIME type validation and file size limits (e.g., 10MB)
- **Download endpoint**: `GET /clips/{id}/file` serving files with proper MIME types and authentication
- **Security considerations**: MIME type validation, file size limits, access control per clip, virus scanning (optional)

**Frontend Changes:**

- **File input UI**: File chooser or drag-drop zone in main upload section
- **Upload handling**: Multipart form submissions with progress tracking
- **Display logic**: Differentiate rendering based on clip type
  - Text: current behavior
  - Images: thumbnail/preview in drawer, expandable modal view
  - PDFs/documents: icon, filename, download button
  - Other files: icon, name, download button
- **Type handling**: Different rendering strategies for each file type

**Data Model Implications:**

- **Backward compatibility**: Existing text clips continue to work, clips become polymorphic (text OR file)
- **Query changes**: `POST /clips` becomes flexible for text or file upload
- **Response model**: `ClipResponse` needs `type` field and optional `file_url`/`file_name`

**Complexity estimate**: 8-16 hours depending on storage backend choice and supported file types

### Public clips page

**Use case**: Share specific text clips with friends or across devices without requiring them to log in.

**Approach: Per-clip share tokens** (recommended)

**Backend Changes:**

- **Database schema**: Add `is_public (bool)` and `share_token (uuid, nullable, unique)` columns to CLIPS table
- **New endpoint**: `GET /public/clip/{share_token}` (no authentication required) returns read-only `ClipResponse`
- **Update clip endpoints**: Allow authenticated users to toggle `is_public` flag and generate/revoke share tokens
  - `POST /clip/{clip_id}/share` - generate token and make public
  - `DELETE /clip/{clip_id}/share` - revoke token and make private
- **Security**: Share tokens should be high-entropy UUIDs, different from clip IDs

**Frontend Changes:**

- **Share button per clip**: Toggle button to generate/copy/revoke share link
- **Share link format**: `xclipboard.yourdomain.com/public/{share_token}` (short, memorable)
- **Public view route**: Detect `/public/:token` and render read-only clip display
  - Show clip text with ClipContent rendering (links clickable)
  - "Copy to Clipboard" button functional
  - No delete or edit controls
  - Can show timestamp

**Data Model Implications:**

- Clips table fields: `is_public`, `share_token` (nullable)
- New response model: `PublicClipResponse` (read-only variant)
- Backward compatibility: Existing clips default to `is_public=false`

**Complexity estimate**: 4-6 hours (moderate - mostly CRUD operations and routing)
