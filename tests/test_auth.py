from ClipBackend import LOGIN_MAX_ATTEMPTS

from conftest import ADMIN_TOKEN, PASSWORD, USERNAME


def test_health(anon):
    assert anon.get("/health").json() == {"status": "ok"}


def test_register_then_login(anon):
    res = anon.post(
        "/api/admin/register",
        json={"username": USERNAME, "password": PASSWORD},
        headers={"X-Admin-Token": ADMIN_TOKEN},
    )
    assert res.status_code == 201

    res = anon.post("/api/auth/login", json={"username": USERNAME, "password": PASSWORD})
    assert res.status_code == 201
    assert "session_id" in res.cookies
    assert anon.get("/api/me").json() == {"username": USERNAME}


def test_public_login(anon):
    res = anon.post("/api/auth/login", json={"username": "public", "password": " "})
    assert res.status_code == 201
    assert anon.get("/api/me").json() == {"username": "public"}


def test_logout(client):
    assert client.post("/api/auth/logout").status_code == 200
    assert client.get("/api/me").status_code == 401


def test_login_is_rate_limited_per_ip(anon):
    def login(ip):
        return anon.post(
            "/api/auth/login",
            json={"username": USERNAME, "password": "wrong"},
            headers={"CF-Connecting-IP": ip},
        )

    for _ in range(LOGIN_MAX_ATTEMPTS):
        login("203.0.113.7")
    res = login("203.0.113.7")
    assert res.status_code == 429
    assert int(res.headers["Retry-After"]) > 0

    # Another IP is unaffected
    assert login("198.51.100.2").status_code == 400


def test_admin_endpoints_are_off_without_a_configured_token(anon, backend, monkeypatch):
    monkeypatch.setattr(backend, "ADMIN_TOKEN", "")
    res = anon.post(
        "/api/admin/register",
        json={"username": USERNAME, "password": PASSWORD},
        headers={"X-Admin-Token": ""},
    )
    assert res.status_code == 403
