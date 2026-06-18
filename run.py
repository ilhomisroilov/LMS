#!/usr/bin/env python3
"""
EduCore — single-command local launcher.

Usage:
    python run.py            # start everything (backend + frontend + bot if configured)
    python run.py --all      # same as above
    python run.py --backend  # only the FastAPI backend
    python run.py --frontend # only the React admin panel
    python run.py --bot      # only the Telegram bot

What it does automatically:
  • loads .env (creating it from .env.example on first run)
  • verifies PostgreSQL is reachable before starting the backend
  • creates the backend virtualenv and installs dependencies if missing
  • runs database migrations and seeds demo data
  • detects Node.js / npm and installs frontend dependencies if needed
  • starts each requested service and prints clear status + URLs
  • starts the Telegram bot only if TELEGRAM_BOT_TOKEN is configured

No Docker required — this is the primary V1 deployment model.
"""
from __future__ import annotations

import argparse
import os
import platform
import shutil
import signal
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

# ──────────────────────────── paths ────────────────────────────
ROOT = Path(__file__).resolve().parent
BACKEND_DIR = ROOT / "backend"
FRONTEND_DIR = ROOT / "frontend"
BOT_DIR = ROOT / "bot"
VENV_DIR = BACKEND_DIR / ".venv"
ENV_FILE = ROOT / ".env"
ENV_EXAMPLE = ROOT / ".env.example"
IS_WINDOWS = platform.system() == "Windows"

# ──────────────────────────── pretty output ────────────────────────────
_USE_COLOR = sys.stdout.isatty() and not os.environ.get("NO_COLOR")
if IS_WINDOWS:
    os.system("")  # enable ANSI escape processing on Windows terminals


def _c(code: str, text: str) -> str:
    return f"\033[{code}m{text}\033[0m" if _USE_COLOR else text


def info(msg: str) -> None:    print(f"{_c('36', 'ℹ')}  {msg}")
def ok(msg: str) -> None:      print(f"{_c('32', '✔')}  {msg}")
def warn(msg: str) -> None:    print(f"{_c('33', '!')}  {msg}")
def err(msg: str) -> None:     print(f"{_c('31', '✗')}  {msg}", file=sys.stderr)
def step(msg: str) -> None:    print(f"\n{_c('1;35', '▶')} {_c('1', msg)}")


def banner(lines: list[str]) -> None:
    width = max(len(l) for l in lines) + 2
    bar = "═" * width
    print(_c("36", f"\n╔{bar}╗"))
    for l in lines:
        print(_c("36", f"║ {l.ljust(width - 1)}║"))
    print(_c("36", f"╚{bar}╝\n"))


# ──────────────────────────── env handling ────────────────────────────
def ensure_env_file() -> None:
    if ENV_FILE.exists():
        return
    if ENV_EXAMPLE.exists():
        ENV_FILE.write_text(ENV_EXAMPLE.read_text(encoding="utf-8"), encoding="utf-8")
        ok(".env created from .env.example (review it before going to production)")
    else:
        warn("No .env or .env.example found — using built-in defaults")


def load_env() -> dict[str, str]:
    env: dict[str, str] = {}
    if ENV_FILE.exists():
        for raw in ENV_FILE.read_text(encoding="utf-8").splitlines():
            line = raw.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, val = line.partition("=")
            env[key.strip()] = val.strip().strip('"').strip("'")
    # Make values visible to child processes too
    for k, v in env.items():
        os.environ.setdefault(k, v)
    return env


# ──────────────────────────── venv helpers ────────────────────────────
def venv_python() -> Path:
    return VENV_DIR / ("Scripts/python.exe" if IS_WINDOWS else "bin/python")


def ensure_backend_venv() -> Path:
    py = venv_python()
    if not py.exists():
        step("Creating backend virtual environment")
        try:
            subprocess.run([sys.executable, "-m", "venv", str(VENV_DIR)], check=True)
        except subprocess.CalledProcessError:
            err("Failed to create virtualenv. Is the 'venv' module available?")
            sys.exit(1)
        ok(f"Virtualenv created at {VENV_DIR.relative_to(ROOT)}")
    # Ensure dependencies are present and bcrypt is compatible with passlib.
    probe_code = (
        "import uvicorn, fastapi, sqlalchemy, bcrypt\n"
        "raise SystemExit(0 if getattr(bcrypt, '__version__', '') == '4.0.1' else 1)\n"
    )
    probe = subprocess.run([str(py), "-c", probe_code], capture_output=True)
    if probe.returncode != 0:
        step("Installing/updating backend dependencies (first run may take a minute)")
        subprocess.run([str(py), "-m", "pip", "install", "--upgrade", "pip"],
                       check=True, cwd=BACKEND_DIR)
        subprocess.run([str(py), "-m", "pip", "install", "-r", "requirements.txt"],
                       check=True, cwd=BACKEND_DIR)
        ok("Backend dependencies installed")
    return py


def ensure_bot_deps(py: Path) -> bool:
    probe = subprocess.run([str(py), "-c", "import aiogram"], capture_output=True)
    if probe.returncode != 0:
        step("Installing Telegram bot dependencies")
        try:
            subprocess.run([str(py), "-m", "pip", "install", "-r", "requirements.txt"],
                           check=True, cwd=BOT_DIR)
            ok("Bot dependencies installed")
        except subprocess.CalledProcessError:
            err("Failed to install bot dependencies")
            return False
    return True


# ──────────────────────────── PostgreSQL check ────────────────────────────
def _parse_pg(env: dict[str, str]) -> tuple[str, int]:
    host = env.get("POSTGRES_HOST") or os.environ.get("POSTGRES_HOST", "localhost")
    port = env.get("POSTGRES_PORT") or os.environ.get("POSTGRES_PORT", "5432")
    url = env.get("DATABASE_URL", "")
    # Prefer host/port parsed from DATABASE_URL when present
    if "@" in url and "/" in url:
        try:
            after_at = url.split("@", 1)[1]
            hostport = after_at.split("/", 1)[0]
            if ":" in hostport:
                host, port = hostport.split(":", 1)
            else:
                host = hostport
        except Exception:
            pass
    try:
        return host, int(port)
    except ValueError:
        return host, 5432


def check_postgres(env: dict[str, str]) -> bool:
    host, port = _parse_pg(env)
    step(f"Checking PostgreSQL at {host}:{port}")
    try:
        with socket.create_connection((host, port), timeout=4):
            ok("PostgreSQL is reachable")
            return True
    except OSError:
        err(f"Cannot reach PostgreSQL at {host}:{port}")
        print(_c("33", "   To fix this:"))
        print("   1. Install PostgreSQL and make sure the service is running.")
        print("   2. Create the database and user (one time):")
        print(_c("90", "        psql -U postgres -c \"CREATE USER educore WITH PASSWORD 'educore_pass';\""))
        print(_c("90", "        psql -U postgres -c \"CREATE DATABASE educore OWNER educore;\""))
        print("   3. Check DATABASE_URL / POSTGRES_* values in your .env file.")
        return False


# ──────────────────────────── Node / npm check ────────────────────────────
def npm_cmd() -> str | None:
    for name in (["npm.cmd", "npm"] if IS_WINDOWS else ["npm"]):
        if shutil.which(name):
            return name
    return None


def check_node() -> str | None:
    node = shutil.which("node")
    npm = npm_cmd()
    if not node or not npm:
        err("Node.js / npm not found.")
        print(_c("33", "   Install Node.js 18+ from https://nodejs.org/ and re-run."))
        return None
    try:
        ver = subprocess.run([node, "--version"], capture_output=True, text=True).stdout.strip()
        ok(f"Node.js detected ({ver})")
    except Exception:
        ok("Node.js detected")
    return npm


# ──────────────────────────── service starters ────────────────────────────
def prepare_backend(py: Path) -> None:
    step("Applying database migrations")
    subprocess.run([str(py), "-m", "alembic", "upgrade", "head"], check=True, cwd=BACKEND_DIR)
    step("Seeding demo data")
    subprocess.run([str(py), "-m", "app.seed"], check=True, cwd=BACKEND_DIR)


def start_backend(py: Path) -> subprocess.Popen:
    info("Starting FastAPI backend → http://127.0.0.1:8000")
    return subprocess.Popen(
        [str(py), "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0",
         "--port", "8000", "--reload"],
        cwd=BACKEND_DIR,
    )


def wait_for_backend(proc: subprocess.Popen, timeout: int = 60) -> bool:
    """Wait until the backend accepts TCP connections on 127.0.0.1:8000.

    Uses a raw socket rather than an HTTP request so the check is immune to
    corporate HTTP proxies (HTTP_PROXY/HTTPS_PROXY) that would otherwise try to
    route even 127.0.0.1 through a proxy and fail.
    """
    step("Waiting for backend to become ready on 127.0.0.1:8000")
    deadline = time.time() + timeout
    while time.time() < deadline:
        code = proc.poll()
        if code is not None:
            err(f"Backend exited before becoming ready (code {code}).")
            return False
        try:
            with socket.create_connection(("127.0.0.1", 8000), timeout=2):
                ok("Backend is ready")
                return True
        except OSError:
            time.sleep(0.5)
    warn(f"Backend not confirmed ready within {timeout}s — continuing anyway "
         "(the frontend will connect once it finishes starting).")
    return False


def _vite_bin() -> Path:
    bin_name = "vite.cmd" if IS_WINDOWS else "vite"
    return FRONTEND_DIR / "node_modules" / ".bin" / bin_name


def _frontend_deps_ok() -> bool:
    """The runnable Vite binary is installed, not just node_modules."""
    return _vite_bin().exists()


def prepare_frontend(npm: str) -> bool:
    nm = FRONTEND_DIR / "node_modules"
    if _frontend_deps_ok():
        ok("Frontend dependencies already installed")
        return True

    if nm.exists():
        warn("node_modules looks incomplete (vite missing) — reinstalling cleanly")
        shutil.rmtree(nm, ignore_errors=True)
    else:
        step("Installing frontend dependencies (first run may take a few minutes)")

    try:
        subprocess.run([npm, "install"], check=True, cwd=FRONTEND_DIR)
    except subprocess.CalledProcessError:
        err("npm install failed. Try running it manually:  cd frontend && npm install")
        return False

    if not _frontend_deps_ok():
        err("Frontend dependencies still incomplete after install. "
            "Delete frontend/node_modules and run 'npm install' manually.")
        return False
    ok("Frontend dependencies installed")
    return True


def start_frontend(npm: str) -> subprocess.Popen:
    info("Starting React admin panel → http://localhost:5173")
    return subprocess.Popen([npm, "run", "dev", "--", "--host"], cwd=FRONTEND_DIR)


def bot_token_configured(env: dict[str, str]) -> bool:
    token = env.get("TELEGRAM_BOT_TOKEN") or os.environ.get("TELEGRAM_BOT_TOKEN", "")
    placeholders = {"", "put-your-bot-token-here", "put-token-here", "changeme"}
    return token.strip() not in placeholders


def start_bot(py: Path) -> subprocess.Popen:
    info("Starting Telegram bot")
    return subprocess.Popen([str(py), "-m", "main"], cwd=BOT_DIR)


# ──────────────────────────── orchestration ────────────────────────────
def parse_args() -> set[str]:
    p = argparse.ArgumentParser(
        description="EduCore local launcher (no Docker).",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument("--backend", action="store_true", help="Start only the backend API")
    p.add_argument("--frontend", action="store_true", help="Start only the React admin panel")
    p.add_argument("--bot", action="store_true", help="Start only the Telegram bot")
    p.add_argument("--all", action="store_true", help="Start everything (default)")
    a = p.parse_args()
    chosen = {n for n in ("backend", "frontend", "bot") if getattr(a, n)}
    if a.all or not chosen:
        return {"backend", "frontend", "bot"}
    return chosen


def main() -> None:
    banner([
        "EduCore CRM + LMS — local launcher",
        "Single-command startup · no Docker required",
    ])
    services = parse_args()
    ensure_env_file()
    env = load_env()

    procs: list[tuple[str, subprocess.Popen]] = []
    started_urls: list[str] = []
    backend_proc: subprocess.Popen | None = None

    # ---------- Backend ----------
    if "backend" in services:
        if not check_postgres(env):
            err("Backend cannot start without PostgreSQL. Aborting.")
            sys.exit(1)
        py = ensure_backend_venv()
        try:
            prepare_backend(py)
        except subprocess.CalledProcessError:
            err("Database migration or seeding failed. Check your DATABASE_URL and PostgreSQL.")
            sys.exit(1)
        backend_proc = start_backend(py)
        procs.append(("backend", backend_proc))
        started_urls += ["API / Swagger:  http://127.0.0.1:8000/docs",
                         "Health check:   http://127.0.0.1:8000/health"]
    else:
        py = venv_python()

    # ---------- Frontend ----------
    if "frontend" in services:
        if backend_proc is not None:
            ready = wait_for_backend(backend_proc)
            if not ready and backend_proc.poll() is not None:
                # Backend actually crashed — nothing to attach the frontend to.
                err("Backend process exited during startup. Aborting.")
                sys.exit(1)
            # If not ready but still alive, proceed — vite proxies to it once up.
        npm = check_node()
        if npm and prepare_frontend(npm):
            procs.append(("frontend", start_frontend(npm)))
            started_urls.insert(0, "Admin panel:    http://localhost:5173")
        elif "frontend" in services and len(services) == 1:
            sys.exit(1)  # explicit frontend-only request failed
        else:
            warn("Skipping frontend (Node.js/npm unavailable).")

    # ---------- Bot ----------
    if "bot" in services:
        if bot_token_configured(env):
            bot_py = py if py.exists() else ensure_backend_venv()
            if ensure_bot_deps(bot_py):
                procs.append(("bot", start_bot(bot_py)))
        else:
            warn("Skipping Telegram bot — set TELEGRAM_BOT_TOKEN in .env to enable it.")

    if not procs:
        err("No services were started.")
        sys.exit(1)

    # ---------- Status ----------
    time.sleep(1)
    banner(["EduCore is starting up!", *started_urls,
            "",
            "Demo admin login:  +998901112233 / Admin12345",
            "Press Ctrl+C to stop all services."])

    # ---------- Wait / shutdown ----------
    def shutdown(*_):
        print()
        info("Shutting down services...")
        for name, proc in procs:
            if proc.poll() is None:
                proc.terminate()
        for name, proc in procs:
            try:
                proc.wait(timeout=8)
            except subprocess.TimeoutExpired:
                proc.kill()
        ok("All services stopped. Goodbye!")
        sys.exit(0)

    signal.signal(signal.SIGINT, shutdown)
    if hasattr(signal, "SIGTERM"):
        signal.signal(signal.SIGTERM, shutdown)

    # If any process exits on its own, report and tear down the rest
    while True:
        for name, proc in procs:
            code = proc.poll()
            if code is not None:
                warn(f"Service '{name}' exited (code {code}).")
                shutdown()
        time.sleep(1)


if __name__ == "__main__":
    main()
