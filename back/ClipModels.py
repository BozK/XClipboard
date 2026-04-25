from pydantic import BaseModel, Field
from typing import List
from datetime import datetime


# ============================================================================
# Authentication Models
# ============================================================================

class LoginRequest(BaseModel):
    """Request body for POST /auth/login"""
    username: str = Field(..., min_length=1)
    password: str = Field(..., min_length=1)


class RegisterRequest(BaseModel):
    """Request body for POST /auth/register"""
    username: str = Field(..., min_length=1)
    password: str = Field(..., min_length=1)


# ============================================================================
# Clip Models
# ============================================================================

class ClipCreate(BaseModel):
    """Request body for POST /clip"""
    clip_text: str = Field(..., min_length=1)


class ClipResponse(BaseModel):
    """Single clip object returned in responses"""
    clip_id: int
    clip_text: str
    created_at: str  # ISO 8601 format


class ClipsResponse(BaseModel):
    """Response body for GET /clips"""
    clips: List[ClipResponse]


# ============================================================================
# Generic Response Models
# ============================================================================

class MessageResponse(BaseModel):
    """Generic response with just a message"""
    message: str


class ErrorResponse(BaseModel):
    """Generic error response"""
    error: str


class UserMessageResponse(BaseModel):
    """Response for operations that create/auth a user"""
    message: str
    username: str


class ClipMessageResponse(BaseModel):
    """Response for clip creation"""
    message: str
    clip_id: int
    created_at: str
