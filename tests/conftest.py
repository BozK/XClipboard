import os
import runpy
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

REPO_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(REPO_ROOT / "back"))

# ClipBackend reads these at import, so set them first. Each test then points it at its own temp dir
ADMIN_TOKEN = "test-admin-token"
os.environ["ADMIN_TOKEN"] = ADMIN_TOKEN

import ClipBackend  # noqa: E402

ClipBackend.app.include_router(ClipBackend.api_router)  # Done in __main__ when run for real

USERNAME = "alice"
PASSWORD = "correct horse battery staple"


@pytest.fixture
def backend(tmp_path, monkeypatch):
    """ClipBackend with a fresh DB (tables + public user), empty file storage, and no sessions or login counts"""
    db_path = tmp_path / "xclipboard.db"
    files_path = tmp_path / "files"
    (files_path / "thumbs").mkdir(parents=True)

    monkeypatch.setenv("DB_PATH", str(db_path))
    runpy.run_path(str(REPO_ROOT / "db" / "CreateTables.py"))

    monkeypatch.setattr(ClipBackend, "DB_PATH", db_path)
    monkeypatch.setattr(ClipBackend, "FILES_PATH", files_path)
    monkeypatch.setattr(ClipBackend, "THUMBS_PATH", files_path / "thumbs")
    monkeypatch.setattr(ClipBackend, "sessions", {})
    monkeypatch.setattr(ClipBackend, "login_limiter", ClipBackend.LoginLimiter())
    return ClipBackend


@pytest.fixture
def anon(backend):
    # https, or the client won't send back the Secure session cookie
    return TestClient(backend.app, base_url="https://testserver")


@pytest.fixture
def client(anon):
    """Logged in as a registered user"""
    anon.post(
        "/api/admin/register",
        json={"username": USERNAME, "password": PASSWORD},
        headers={"X-Admin-Token": ADMIN_TOKEN},
    )
    anon.post("/api/auth/login", json={"username": USERNAME, "password": PASSWORD})
    return anon
