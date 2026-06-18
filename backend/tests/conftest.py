"""Pytest fixtures: a REAL PostgreSQL instance (embedded via pgserver) + seed.

The v1.2 backend targets PostgreSQL only. ``pgserver`` ships PostgreSQL 16
binaries in a wheel and runs a throwaway cluster in a temp dir, so the suite
exercises the same database engine as production with zero external setup.
"""
import atexit
import os
import pathlib
import tempfile

import pytest

# --- Boot an embedded PostgreSQL BEFORE the app (and its engine) import ------
import pgserver  # noqa: E402

_PG_DIR = pathlib.Path(tempfile.mkdtemp(prefix="educore_pg_"))
_server = pgserver.get_server(_PG_DIR)
try:
    _server.psql("CREATE DATABASE educore_test;")
except Exception:  # already exists on a warm dir
    pass

os.environ["DATABASE_URL"] = _server.get_uri(database="educore_test")
os.environ.setdefault("STORAGE_LOCAL_DIR", tempfile.mkdtemp())
os.environ.setdefault("SECRET_KEY", "test-secret-key")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/15")


@atexit.register
def _cleanup_pg() -> None:
    try:
        _server.cleanup()
    except Exception:
        pass


@pytest.fixture(scope="session")
def client():
    from fastapi.testclient import TestClient

    from app import models  # noqa: F401  register models on Base.metadata
    from app import seed
    from app.core.database import Base, engine
    from app.main import app

    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    seed.run()
    with TestClient(app) as c:
        yield c


def login(client, phone, password):
    r = client.post("/api/v1/auth/login", json={"phone": phone, "password": password})
    assert r.status_code == 200, r.text
    return r.json()


def auth_header(client, phone, password):
    return {"Authorization": f"Bearer {login(client, phone, password)['access_token']}"}
