from tests.conftest import auth_header


def test_login_success(client):
    h = auth_header(client, "+998901112233", "Admin12345")
    me = client.get("/api/v1/auth/me", headers=h).json()
    assert me["role"] == "admin"


def test_login_bad_credentials(client):
    r = client.post("/api/v1/auth/login", json={"phone": "x", "password": "y"})
    assert r.status_code == 401


def test_i18n_error_messages(client):
    uz = client.post("/api/v1/auth/login", json={"phone": "x", "password": "y"},
                     headers={"Accept-Language": "uz"})
    en = client.post("/api/v1/auth/login", json={"phone": "x", "password": "y"},
                     headers={"Accept-Language": "en"})
    assert uz.json()["detail"] != en.json()["detail"]


def test_refresh_rotation_and_revocation(client):
    login = client.post("/api/v1/auth/login",
                        json={"phone": "+998901112233", "password": "Admin12345"}).json()
    rt = login["refresh_token"]
    ok = client.post("/api/v1/auth/refresh", json={"refresh_token": rt})
    assert ok.status_code == 200
    reused = client.post("/api/v1/auth/refresh", json={"refresh_token": rt})
    assert reused.status_code == 401  # old token revoked
