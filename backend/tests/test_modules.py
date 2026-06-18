from tests.conftest import auth_header


def test_dashboard_stats(client):
    h = auth_header(client, "+998901112233", "Admin12345")
    s = client.get("/api/v1/dashboard/stats", headers=h).json()
    assert s["total_students"] >= 3 and "attendance_rate" in s


def test_student_crud(client):
    h = auth_header(client, "+998901112233", "Admin12345")
    created = client.post("/api/v1/students", headers=h, json={
        "full_name": "Test Student", "phone": "+998900000999",
        "parent_phone": "+998900000000", "status": "active", "password": "secret123",
    })
    assert created.status_code == 201, created.text
    sid = created.json()["id"]
    client.patch(f"/api/v1/students/{sid}", headers=h, json={"status": "frozen"})
    got = client.get(f"/api/v1/students/{sid}", headers=h).json()
    assert got["status"] == "frozen"
    assert client.delete(f"/api/v1/students/{sid}", headers=h).status_code == 204


def test_duplicate_student_phone_returns_conflict(client):
    h = auth_header(client, "+998901112233", "Admin12345")
    h["Accept-Language"] = "uz"
    r = client.post("/api/v1/students", headers=h, json={
        "full_name": "Duplicate Student", "phone": "+998901000101",
        "parent_phone": "+998900000000", "status": "active", "password": "secret123",
    })
    detail = r.json()["detail"]
    assert r.status_code == 409
    assert "telefon raqami" in detail
    assert "duplicate key" not in detail.lower()


def test_logs_endpoints(client):
    stats = client.get("/api/v1/logs/stats")
    assert stats.status_code == 200
    assert stats.json()["status"] == "ok"

    compat = client.get("/api/logs/stats")
    assert compat.status_code == 200

    stream = client.get("/api/v1/logs/stream", params={"once": "true"})
    assert stream.status_code == 200
    assert "text/event-stream" in stream.headers["content-type"]
    assert "event: heartbeat" in stream.text


def test_bot_flow(client):
    bh = {"X-Bot-Token": "bot-internal-secret-token"}
    link = client.post("/api/v1/bot/link", headers=bh,
                       json={"phone": "+998901000103", "telegram_id": 999001})
    assert link.status_code == 200 and link.json()["role"] == "student"
    g = client.get("/api/v1/bot/student/groups", headers=bh, params={"telegram_id": 999001})
    assert g.status_code == 200
    # bad token rejected
    assert client.get("/api/v1/bot/me", params={"telegram_id": 999001}).status_code == 401
