import os
import shutil
import sqlite3
import mimetypes
import uuid
from datetime import datetime, timezone, timedelta
from typing import Optional, List
import bcrypt
from fastapi import FastAPI, APIRouter, Request, Response, HTTPException, Depends, status, Cookie
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, FileResponse
from fastapi.concurrency import run_in_threadpool
from starlette.datastructures import UploadFile
from PIL import Image, ImageOps
from pillow_heif import register_heif_opener
import time
from pathlib import Path

from ClipModels import (
    LoginRequest, RegisterRequest, ClipCreate,
    MessageResponse, UserMessageResponse, ClipMessageResponse,
    ClipsResponse, ClipResponse, ClipFileInfo, ErrorResponse
)
from logger import logger, log_request, log_database_query

ADMIN_TOKEN = os.getenv("ADMIN_TOKEN")

# ============================================================================
# Session Management (In-Memory)
# ============================================================================
sessions = {}  # Format: {session_id_uuid: "username"}

DB_PATH = Path(os.getenv("DB_PATH", Path(__file__).parent.parent / "db" / "xclipboard.db"))

# ============================================================================
# File Storage
# ============================================================================
FILES_PATH = Path(os.getenv("FILES_PATH", Path(__file__).parent.parent / "db" / "files"))
THUMBS_PATH = FILES_PATH / "thumbs"
THUMBS_PATH.mkdir(parents=True, exist_ok=True)

PUBLIC_USERNAME = "public"  # Shared account with a known password, so it stays text-only
MAX_FILE_BYTES = 25 * 1024 * 1024
MULTIPART_OVERHEAD_BYTES = 64 * 1024  # Slack for boundaries/part headers when pre-checking Content-Length
THUMB_SIZE = 640  # Longest side of the preview, in pixels
# Only real raster images may render inline on our origin; everything else is forced to download
INLINE_MIME_TYPES = {"image/jpeg", "image/png", "image/gif", "image/webp", "image/heic", "image/heif"}

register_heif_opener()  # Lets Pillow read iPhone HEIC photos

# ============================================================================
# Database Helpers
# ============================================================================

def get_db_connection():
    """Create and return a database connection"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def get_owned_clip(cursor: sqlite3.Cursor, clip_id: int, username: str) -> sqlite3.Row:
    """Fetch a clip and its file metadata (if any). 404 if missing, 403 if it belongs to another user"""
    query = """
        SELECT c.clip_id, c.username, f.stored_name, f.original_name, f.mime_type, f.has_thumb
        FROM CLIPS c
        LEFT JOIN ClipFiles f ON f.clip_id = c.clip_id
        WHERE c.clip_id = ?
        """
    cursor.execute(query, (clip_id,))
    log_database_query(logger, query, (clip_id,))
    clip = cursor.fetchone()

    if not clip:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Clip not found"
        )

    if clip["username"] != username:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Clip belongs to another user"
        )

    return clip


def get_user_by_username(username: str) -> Optional[sqlite3.Row]:
    """Fetch user from database by username"""
    conn = get_db_connection()
    cursor = conn.cursor()
    query = "SELECT * FROM Users WHERE username = ?"
    cursor.execute(query, (username,))
    log_database_query(logger, query, (username,))
    user = cursor.fetchone()
    conn.close()
    return user


# ============================================================================
# FastAPI Application Setup
# ============================================================================

app = FastAPI(title="XClipboard API", version="1.0.0")

@app.middleware("http")
async def log_requests(request: Request, call_next):
    """inline logging middleware"""
    start_time = time.time()
    response = await call_next(request)
    process_time_ms = (time.time() - start_time) * 1000
    log_request(
        logger,
        method=request.method,
        path=request.url.path,
        client_ip=request.client.host if request.client else "unknown",
        status_code=response.status_code,
        response_time_ms=process_time_ms
    )
    return response


# ============================================================================
# Dependencies (Session & Admin Validation)
# ============================================================================

async def get_current_user(session_id: Optional[str] = Cookie(None)) -> str:
    """Dependency to validate session and return authenticated username"""
    if not session_id or session_id not in sessions:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing session"
        )
    return sessions[session_id]


async def validate_admin_token(request: Request) -> bool:
    """Dependency to validate admin token from X-Admin-Token header"""
    token = request.headers.get("X-Admin-Token")
    if token != ADMIN_TOKEN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid or missing admin token"
        )
    return True


# ============================================================================
# Helper Functions
# ============================================================================

def get_current_timestamp_iso8601() -> str:
    """Return current timestamp in ISO 8601 format with timezone"""
    return datetime.now(timezone.utc).isoformat()


def hash_password(password: str) -> bytes:
    """Hash a password using bcrypt"""
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt())


def verify_password(password: str, hashed: bytes) -> bool:
    """Verify a password against its bcrypt hash"""
    return bcrypt.checkpw(password.encode(), hashed)


def make_thumbnail(source: Path, stored_name: str) -> Optional[str]:
    """
    Write a small JPEG preview to THUMBS_PATH if Pillow can decode the file as an image.
    Returns the MIME type Pillow detected, or None if the file isn't an image.
    """
    try:
        with Image.open(source) as img:
            mime_type = Image.MIME.get(img.format, "application/octet-stream")
            img.draft("RGB", (THUMB_SIZE * 2, THUMB_SIZE * 2))  # Fast JPEG downscale while decoding
            # iPhone photos are stored sideways with an EXIF rotation flag
            img = ImageOps.exif_transpose(img)
            img.thumbnail((THUMB_SIZE, THUMB_SIZE))

            if img.mode in ("RGBA", "LA", "P"):
                # JPEG has no transparency: flatten onto white instead of black
                img = img.convert("RGBA")
                flattened = Image.new("RGB", img.size, "white")
                flattened.paste(img, mask=img.getchannel("A"))
                img = flattened
            else:
                img = img.convert("RGB")

            img.save(THUMBS_PATH / f"{stored_name}.jpg", "JPEG", quality=80)
        return mime_type
    except Exception as e:
        logger.info(f"No thumbnail for {stored_name}: {e}")
        return None


def delete_stored_file(stored_name: str):
    """Remove an uploaded file and its thumbnail from disk"""
    (FILES_PATH / stored_name).unlink(missing_ok=True)
    (THUMBS_PATH / f"{stored_name}.jpg").unlink(missing_ok=True)


def save_file_clip(upload: UploadFile, username: str) -> tuple[int, str]:
    """Copy an upload to disk, build its preview and insert the clip. Returns (clip_id, created_at)"""
    stored_name = uuid.uuid4().hex
    # Never trust the client's filename for paths: it's only kept for display and downloads
    original_name = Path(upload.filename).name.strip()[:255] or "file"

    upload.file.seek(0)
    with open(FILES_PATH / stored_name, "wb") as out:
        shutil.copyfileobj(upload.file, out, 1024 * 1024)

    try:
        size_bytes = (FILES_PATH / stored_name).stat().st_size
        detected_mime = make_thumbnail(FILES_PATH / stored_name, stored_name)
        has_thumb = detected_mime is not None
        mime_type = (
            detected_mime
            or mimetypes.guess_type(original_name)[0]
            or upload.content_type
            or "application/octet-stream"
        )
        created_at = get_current_timestamp_iso8601()

        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            clip_query = "INSERT INTO CLIPS (username, clip_text, created_at) VALUES (?, '', ?)"
            cursor.execute(clip_query, (username, created_at))
            log_database_query(logger, clip_query, (username, created_at))
            clip_id = cursor.lastrowid

            file_query = """
                INSERT INTO ClipFiles (clip_id, stored_name, original_name, mime_type, size_bytes, has_thumb)
                VALUES (?, ?, ?, ?, ?, ?)
                """
            file_params = (clip_id, stored_name, original_name, mime_type, size_bytes, int(has_thumb))
            cursor.execute(file_query, file_params)
            log_database_query(logger, file_query, file_params)
            conn.commit()
        finally:
            conn.close()
    except Exception:
        delete_stored_file(stored_name)
        raise

    logger.info(f"File clip saved for {username}: {original_name} ({size_bytes} bytes, {mime_type})")
    return clip_id, created_at


# ============================================================================
# API Router
# ============================================================================

api_router = APIRouter(prefix="/api")

# ============================================================================
# API Endpoints
# ============================================================================

# -------- Authentication --------

@api_router.post("/auth/login", response_model=UserMessageResponse, status_code=status.HTTP_201_CREATED)
def login(request: LoginRequest, response: Response):
    """
    POST /api/auth/login
    Authenticate user and create session
    """
    user = get_user_by_username(request.username)
    
    if not user:
        logger.warning(f"Login attempt with non-existent username: {request.username}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid username or password"
        )
    
    # Verify password
    try:
        password_hash = user["password_hash"].encode() if isinstance(user["password_hash"], str) else user["password_hash"]
        if not verify_password(request.password, password_hash):
            logger.warning(f"Failed login attempt for user: {request.username}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid username or password"
            )
    except Exception as e:
        logger.error(f"Password verification error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid username or password"
        )
    
    # Create session
    session_id = str(uuid.uuid4())
    sessions[session_id] = request.username
    
    # Set session cookie
    response.set_cookie(
        key="session_id",
        value=session_id,
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=604800  # 7 days
    )
    
    logger.info(f"User logged in: {request.username}")
    return UserMessageResponse(message="Login successful", username=request.username)


@api_router.post("/auth/logout", response_model=MessageResponse, status_code=status.HTTP_200_OK)
def logout(response: Response, current_user: str = Depends(get_current_user)):
    """
    POST /api/auth/logout
    Invalidate session
    """
    # Find and remove session
    session_to_remove = None
    for session_id, username in sessions.items():
        if username == current_user:
            session_to_remove = session_id
            break
    
    if session_to_remove:
        del sessions[session_to_remove]
    
    # Clear cookie
    response.delete_cookie(key="session_id")
    
    logger.info(f"User logged out: {current_user}")
    return MessageResponse(message="Logged out successfully")


@api_router.post("/admin/register", response_model=UserMessageResponse, status_code=status.HTTP_201_CREATED)
def register(request: RegisterRequest, _: bool = Depends(validate_admin_token)):
    """
    POST /api/admin/register
    Add a new user to the system (Admin only)
    """
    # Check if user already exists
    existing_user = get_user_by_username(request.username)
    if existing_user:
        logger.warning(f"Registration attempt with existing username: {request.username}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already exists"
        )
    
    # Hash password and insert into database
    password_hash = hash_password(request.password)
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        query = "INSERT INTO Users (username, password_hash) VALUES (?, ?)"
        cursor.execute(query, (request.username, password_hash))
        log_database_query(logger, query, (request.username, "<hash>"))
        conn.commit()
    except sqlite3.IntegrityError:
        logger.warning(f"Registration failed (user exists): {request.username}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already exists"
        )
    finally:
        conn.close()
    
    return UserMessageResponse(message="User created", username=request.username)


# -------- Clips --------

@api_router.get("/me", status_code=status.HTTP_200_OK)
def get_current_user_info(current_user: str = Depends(get_current_user)):
    """
    GET /api/me
    Return the username of the currently authenticated user
    """
    return {"username": current_user}


@api_router.get("/clips", response_model=ClipsResponse, status_code=status.HTTP_200_OK)
def get_clips(current_user: str = Depends(get_current_user)):
    """
    GET /api/clips
    Fetch user's 25 most recent clips (newest first)
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    query = """
        SELECT c.clip_id, c.clip_text, c.created_at,
               f.original_name, f.mime_type, f.size_bytes, f.has_thumb
        FROM CLIPS c
        LEFT JOIN ClipFiles f ON f.clip_id = c.clip_id
        WHERE c.username = ?
        ORDER BY c.created_at DESC
        LIMIT 25
        """
    cursor.execute(query, (current_user,))
    log_database_query(logger, query, (current_user,))

    rows = cursor.fetchall()
    conn.close()

    clips = [
        ClipResponse(
            clip_id=row["clip_id"],
            clip_text=row["clip_text"],
            created_at=row["created_at"],
            file=ClipFileInfo(
                name=row["original_name"],
                mime_type=row["mime_type"],
                size_bytes=row["size_bytes"],
                has_thumb=bool(row["has_thumb"]),
            ) if row["original_name"] is not None else None,
        )
        for row in rows
    ]
    
    return ClipsResponse(clips=clips)


@api_router.post("/clip", response_model=ClipMessageResponse, status_code=status.HTTP_201_CREATED)
def create_clip(request: ClipCreate, current_user: str = Depends(get_current_user)):
    """
    POST /api/clip
    Save a single clip for the authenticated user
    """
    if not request.clip_text or request.clip_text.strip() == "":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Empty clip_text"
        )
    
    created_at = get_current_timestamp_iso8601()
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        query = "INSERT INTO CLIPS (username, clip_text, created_at) VALUES (?, ?, ?)"
        cursor.execute(query, (current_user, request.clip_text, created_at))
        log_database_query(logger, query, (current_user, "<clip_text>", created_at))
        conn.commit()
        clip_id = cursor.lastrowid
    finally:
        conn.close()
    
    return ClipMessageResponse(
        message="Clip saved",
        clip_id=clip_id,
        created_at=created_at
    )


@api_router.delete("/clip/{clip_id}", response_model=MessageResponse, status_code=status.HTTP_200_OK)
def delete_clip(clip_id: int, current_user: str = Depends(get_current_user)):
    """
    DELETE /api/clip/{clip_id}
    Delete a specific clip belonging to the authenticated user
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        clip = get_owned_clip(cursor, clip_id, current_user)

        # Delete the attachment row (if any), then the clip
        file_delete_query = "DELETE FROM ClipFiles WHERE clip_id = ?"
        cursor.execute(file_delete_query, (clip_id,))
        log_database_query(logger, file_delete_query, (clip_id,))

        delete_query = "DELETE FROM CLIPS WHERE clip_id = ?"
        cursor.execute(delete_query, (clip_id,))
        log_database_query(logger, delete_query, (clip_id,))
        conn.commit()
    finally:
        conn.close()

    if clip["stored_name"]:
        delete_stored_file(clip["stored_name"])

    return MessageResponse(message="Clip deleted successfully")


# -------- File Clips --------

@api_router.post("/clip/file", response_model=ClipMessageResponse, status_code=status.HTTP_201_CREATED)
async def create_file_clip(request: Request, current_user: str = Depends(get_current_user)):
    """
    POST /api/clip/file
    Save an uploaded file (multipart field "file") as a clip for the authenticated user.
    Takes the raw Request so auth and size checks run before the body is read and spooled to disk.
    """
    if current_user == PUBLIC_USERNAME:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="File uploads are disabled for the public account"
        )

    too_large = HTTPException(
        status_code=status.HTTP_413_CONTENT_TOO_LARGE,
        detail=f"File too large (max {MAX_FILE_BYTES // (1024 * 1024)} MB)"
    )
    content_length = request.headers.get("content-length", "")
    if not content_length.isdigit():
        raise HTTPException(
            status_code=status.HTTP_411_LENGTH_REQUIRED,
            detail="Content-Length required"
        )
    if int(content_length) > MAX_FILE_BYTES + MULTIPART_OVERHEAD_BYTES:
        raise too_large

    form = await request.form(max_files=1, max_fields=1)
    try:
        upload = form.get("file")
        if not isinstance(upload, UploadFile) or not upload.filename:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Missing file"
            )
        if upload.size > MAX_FILE_BYTES:
            raise too_large

        clip_id, created_at = await run_in_threadpool(save_file_clip, upload, current_user)
    finally:
        await form.close()

    return ClipMessageResponse(
        message="File saved",
        clip_id=clip_id,
        created_at=created_at
    )


@api_router.get("/clip/{clip_id}/file", status_code=status.HTTP_200_OK)
def download_clip_file(clip_id: int, inline: bool = False, current_user: str = Depends(get_current_user)):
    """
    GET /api/clip/{clip_id}/file
    Download a file clip at full size. ?inline=true shows images in the browser instead
    """
    conn = get_db_connection()
    try:
        clip = get_owned_clip(conn.cursor(), clip_id, current_user)
    finally:
        conn.close()

    path = FILES_PATH / clip["stored_name"] if clip["stored_name"] else None
    if not path or not path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found"
        )

    # has_thumb means Pillow really decoded it as an image, so a renamed .html can't sneak through on its extension
    can_inline = clip["has_thumb"] and clip["mime_type"] in INLINE_MIME_TYPES
    disposition = "inline" if inline and can_inline else "attachment"
    return FileResponse(
        path,
        media_type=clip["mime_type"],
        filename=clip["original_name"],
        content_disposition_type=disposition,
        headers={"X-Content-Type-Options": "nosniff"},
    )


@api_router.get("/clip/{clip_id}/thumb", status_code=status.HTTP_200_OK)
def get_clip_thumbnail(clip_id: int, current_user: str = Depends(get_current_user)):
    """
    GET /api/clip/{clip_id}/thumb
    Small JPEG preview of an image clip
    """
    conn = get_db_connection()
    try:
        clip = get_owned_clip(conn.cursor(), clip_id, current_user)
    finally:
        conn.close()

    path = THUMBS_PATH / f"{clip['stored_name']}.jpg" if clip["has_thumb"] else None
    if not path or not path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Thumbnail not found"
        )

    # Clip ids are never reused (AUTOINCREMENT), so a thumbnail never changes
    return FileResponse(
        path,
        media_type="image/jpeg",
        headers={
            "Cache-Control": "private, max-age=31536000, immutable",
            "X-Content-Type-Options": "nosniff",
        },
    )


# ============================================================================
# Error Handlers
# ============================================================================

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Custom HTTP exception handler"""
    logger.warning(f"HTTP {exc.status_code}: {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail}
    )


# ============================================================================
# Health Check
# ============================================================================

@app.get("/health", status_code=status.HTTP_200_OK)
async def health_check():
    """Simple health check endpoint"""
    return {"status": "ok"}

# ============================================================================
# Run Server
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    
    # Register API router with /api prefix
    app.include_router(api_router)

    # Serve React frontend static files at /
    # Resolve frontend/dist path (works from back/ or root directory)
    frontend_dist = Path(__file__).parent.parent / "frontend" / "dist"
    
    if frontend_dist.exists():
        app.mount("/", StaticFiles(directory=frontend_dist, html=True), name="static")
    else:
        logger.warning(f"Frontend dist not found at: {frontend_dist}")
    
    logger.info("Starting XClipboard API server...")
    uvicorn.run(
        app,
        host=os.getenv("HOST", "127.0.0.1"),
        port=int(os.getenv("PORT", "8001")),
        log_config=None  # Use our custom logging
    )
