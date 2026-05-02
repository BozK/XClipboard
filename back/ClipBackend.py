import os
import sqlite3
import uuid
from datetime import datetime, timezone, timedelta
from typing import Optional, List
import bcrypt
from fastapi import FastAPI, APIRouter, Request, Response, HTTPException, Depends, status, Cookie
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
import time
from pathlib import Path

from ClipModels import (
    LoginRequest, RegisterRequest, ClipCreate,
    MessageResponse, UserMessageResponse, ClipMessageResponse,
    ClipsResponse, ClipResponse, ErrorResponse
)
from logger import logger, log_request, log_database_query

ADMIN_TOKEN = os.getenv("ADMIN_TOKEN")

# ============================================================================
# Session Management (In-Memory)
# ============================================================================
sessions = {}  # Format: {session_id_uuid: "username"}

DB_PATH = Path(__file__).parent.parent / "db" / "xclipboard.db"

# ============================================================================
# Database Helpers
# ============================================================================

def get_db_connection():
    """Create and return a database connection"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


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


# ============================================================================
# API Endpoints
# ============================================================================

# -------- Authentication --------

@app.post("/auth/login", response_model=UserMessageResponse, status_code=status.HTTP_201_CREATED)
async def login(request: LoginRequest, response: Response):
    """
    POST /auth/login
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


@app.post("/auth/logout", response_model=MessageResponse, status_code=status.HTTP_200_OK)
async def logout(response: Response, current_user: str = Depends(get_current_user)):
    """
    POST /auth/logout
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


@app.post("/auth/register", response_model=UserMessageResponse, status_code=status.HTTP_201_CREATED)
async def register(request: RegisterRequest, _: bool = Depends(validate_admin_token)):
    """
    POST /auth/register
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

@app.get("/clips", response_model=ClipsResponse, status_code=status.HTTP_200_OK)
async def get_clips(current_user: str = Depends(get_current_user)):
    """
    GET /clips
    Fetch user's 25 most recent clips (newest first)
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    query = """
        SELECT clip_id, clip_text, created_at
        FROM CLIPS
        WHERE username = ?
        ORDER BY created_at DESC
        LIMIT 25
        """
    cursor.execute(query, (current_user,))
    log_database_query(logger, query, (current_user,))
    
    rows = cursor.fetchall()
    conn.close()
    
    clips = [
        ClipResponse(clip_id=row[0], clip_text=row[1], created_at=row[2])
        for row in rows
    ]
    
    return ClipsResponse(clips=clips)


@app.post("/clip", response_model=ClipMessageResponse, status_code=status.HTTP_201_CREATED)
async def create_clip(request: ClipCreate, current_user: str = Depends(get_current_user)):
    """
    POST /clip
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


@app.delete("/clip/{clip_id}", response_model=MessageResponse, status_code=status.HTTP_200_OK)
async def delete_clip(clip_id: int, current_user: str = Depends(get_current_user)):
    """
    DELETE /clip/{clip_id}
    Delete a specific clip belonging to the authenticated user
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Verify the clip belongs to the current user
        select_query = "SELECT username FROM CLIPS WHERE clip_id = ?"
        cursor.execute(select_query, (clip_id,))
        log_database_query(logger, select_query, (clip_id,))
        clip = cursor.fetchone()
        
        if not clip:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Clip not found"
            )
        
        if clip["username"] != current_user:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot delete clip belonging to another user"
            )
        
        # Delete the clip
        delete_query = "DELETE FROM CLIPS WHERE clip_id = ?"
        cursor.execute(delete_query, (clip_id,))
        log_database_query(logger, delete_query, (clip_id,))
        conn.commit()
    finally:
        conn.close()
    
    return MessageResponse(message="Clip deleted successfully")


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
    # # Register API router with /api prefix
    # app.include_router(api_router)

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
        host="127.0.0.1",
        port=8001,
        log_config=None  # Use our custom logging
    )
