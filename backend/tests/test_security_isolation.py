"""Gating security & isolation suite (v1.2 spec §17.2).

These tests are the hard acceptance gate: role-matrix, cross-tenant isolation,
ownership scope, refresh-token lifecycle, no-default-password, and audit.
They run against a real PostgreSQL instance (see conftest).
"""
from tests.conftest import auth_header, login

ORG_A_ADMIN = ("+998901112233", "Admin12345")
ORG_A_MANAGER = ("+998901112200", "Manager12345")
ORG_A_TEACHER1 = ("+998901000001", "teacher123")   # teaches ENG-101
ORG_A_STUDENT = ("+998901000101", "student123")     # Jasur, ENG-101
ORG_A_PARENT = ("+998901000010", "parent123")       # linked to Jasur
ORG_B_ADMIN = ("+998909990001", "Admin12345")


def _ids_by_phone(client):
    h = auth_header(client, *ORG_A_ADMIN)
    rows = client.get("/api/v1/students?size=100", headers=h).json()["items"]
    return {r["phone"]: r["id"] for r in rows}


# --------------------------------------------------------------- role matrix
def test_role_matrix_students_list(client):
    """STUDENT_READ holders (admin/manager/teacher) may list; student/parent 403."""
    expected = {
        ORG_A_ADMIN: 200, ORG_A_MANAGER: 200, ORG_A_TEACHER1: 200,
        ORG_A_STUDENT: 403, ORG_A_PARENT: 403,
    }
    for creds, code in expected.items():
        h = auth_header(client, *creds)
        r = client.get("/api/v1/students", headers=h)
        assert r.status_code == code, f"{creds} -> {r.status_code}, expected {code}"


def test_role_matrix_me_available_to_all(client):
    for creds in (ORG_A_ADMIN, ORG_A_TEACHER1, ORG_A_STUDENT, ORG_A_PARENT):
        h = auth_header(client, *creds)
        assert client.get("/api/v1/auth/me", headers=h).status_code == 200


def test_me_exposes_permissions_and_org(client):
    h = auth_header(client, *ORG_A_ADMIN)
    me = client.get("/api/v1/auth/me", headers=h).json()
    assert me["role"] == "admin"
    assert "organization_id" in me
    assert "student:write" in me["permissions"]
    # A student's permission set must NOT include admin/finance powers.
    sh = auth_header(client, *ORG_A_STUDENT)
    sme = client.get("/api/v1/auth/me", headers=sh).json()
    assert "payment:read" not in sme["permissions"]
    assert "student:read" not in sme["permissions"]


# ------------------------------------------------------------- cross tenant
def test_cross_tenant_student_list_isolation(client):
    a = auth_header(client, *ORG_A_ADMIN)
    b = auth_header(client, *ORG_B_ADMIN)
    a_total = client.get("/api/v1/students", headers=a).json()["total"]
    b_total = client.get("/api/v1/students", headers=b).json()["total"]
    assert a_total >= 3            # org A demo students
    assert b_total == 1            # org B has exactly one student
    assert a_total != b_total


def test_cross_tenant_get_by_id_blocked(client):
    ids = _ids_by_phone(client)                 # org A student ids
    jasur = ids["+998901000101"]
    b = auth_header(client, *ORG_B_ADMIN)
    # Org B admin must not be able to read an Org A student (tenant filter -> 404).
    assert client.get(f"/api/v1/students/{jasur}", headers=b).status_code == 404


# --------------------------------------------------------------- ownership
def test_teacher_sees_only_assigned_students(client):
    ids = _ids_by_phone(client)
    jasur = ids["+998901000101"]    # ENG-101 (teacher1's group)
    sardor = ids["+998901000103"]   # MATH-201 (NOT teacher1's group)
    h = auth_header(client, *ORG_A_TEACHER1)
    assert client.get(f"/api/v1/students/{jasur}", headers=h).status_code == 200
    assert client.get(f"/api/v1/students/{sardor}", headers=h).status_code == 403


def test_parent_blocked_from_admin_endpoints(client):
    h = auth_header(client, *ORG_A_PARENT)
    ids = _ids_by_phone(client)
    assert client.get("/api/v1/students", headers=h).status_code == 403
    assert client.get(f"/api/v1/students/{ids['+998901000101']}", headers=h).status_code == 403


# ----------------------------------------------------------- token lifecycle
def test_refresh_reuse_revokes_whole_family(client):
    tok = login(client, *ORG_A_ADMIN)
    rt = tok["refresh_token"]
    first = client.post("/api/v1/auth/refresh", json={"refresh_token": rt})
    assert first.status_code == 200
    new_rt = first.json()["refresh_token"]
    # Reusing the rotated-away token is theft/replay -> 401 AND kills the family.
    assert client.post("/api/v1/auth/refresh", json={"refresh_token": rt}).status_code == 401
    assert client.post("/api/v1/auth/refresh", json={"refresh_token": new_rt}).status_code == 401


def test_logout_all_invalidates_access_tokens(client):
    tok = login(client, *ORG_A_MANAGER)
    h = {"Authorization": f"Bearer {tok['access_token']}"}
    assert client.get("/api/v1/auth/me", headers=h).status_code == 200
    assert client.post("/api/v1/auth/logout-all", headers=h).status_code == 204
    # token_version bumped -> the previously valid access token is now dead.
    assert client.get("/api/v1/auth/me", headers=h).status_code == 401


def test_invited_user_has_no_usable_password(client):
    r = client.post("/api/v1/auth/login",
                    json={"phone": "+998901119999", "password": "anything"})
    assert r.status_code == 401


def test_invite_accept_and_change_password_flow(client):
    from app.core.database import SessionLocal
    from app.repositories.user_repository import UserRepository
    from app.services.auth_service import AuthService

    db = SessionLocal()
    try:
        invited = UserRepository(db).get_by_phone("+998901119999")
        raw = AuthService(db).create_invite(invited.id)
    finally:
        db.close()

    # Accept invite -> sets password, activates account, returns tokens.
    acc = client.post("/api/v1/auth/accept-invite",
                      json={"token": raw, "new_password": "NewPass123"})
    assert acc.status_code == 200, acc.text
    assert login(client, "+998901119999", "NewPass123")["access_token"]

    # Change password -> bumps token_version, invalidating the old access token.
    tok = login(client, "+998901119999", "NewPass123")
    h = {"Authorization": f"Bearer {tok['access_token']}"}
    chg = client.post("/api/v1/auth/change-password", headers=h,
                      json={"old_password": "NewPass123", "new_password": "NewPass456"})
    assert chg.status_code == 204
    assert client.get("/api/v1/auth/me", headers=h).status_code == 401
    assert login(client, "+998901119999", "NewPass456")["access_token"]


# ------------------------------------------------------------------- audit
def test_sensitive_actions_are_audited(client):
    login(client, *ORG_A_ADMIN)  # generates an auth.login audit row
    from app.core.database import SessionLocal
    from app.models.audit_log import AuditLog
    db = SessionLocal()
    try:
        count = db.query(AuditLog).filter(AuditLog.action == "auth.login").count()
    finally:
        db.close()
    assert count >= 1
