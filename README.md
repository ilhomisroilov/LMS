# EduCore — CRM + LMS (V1 MVP)

Bilingual (🇺🇿 Uzbek / 🇬🇧 English) management system for small/medium learning centers:
student & teacher CRM, groups/courses, attendance, payments, a basic LMS, a **fully
functional Telegram bot**, and a React admin panel.

> **V1 runs entirely on your local machine — no Docker, no containers.**
> Containerized deployment is a planned future enhancement (see the bottom of this file).

## Architecture

```
React Admin (Vite + Tailwind + i18next)
        │  REST /api/v1
        ▼
FastAPI Backend ──► PostgreSQL (main DB, local install)
   │  service/      ──► Redis (optional: cache, rate-limit)
   │  repository    ──► Local file storage (./storage/uploads)
   │  layers
   └────────────────► Telegram Bot (aiogram) — talks to /api/v1/bot/*
```

Clean layered backend: **models → repositories → services → API**. Stateless,
versioned (`/api/v1`), JWT-authenticated — ready for a mobile client in V2.

## Tech stack

| Layer    | Tech |
|----------|------|
| Frontend | React 18 (Vite), TailwindCSS, React Router, Axios, react-i18next |
| Backend  | FastAPI (Python 3.11), SQLAlchemy 2, Pydantic v2, Alembic, JWT, bcrypt |
| Database | PostgreSQL (local) |
| Cache    | Redis (local, optional) |
| Bot      | aiogram 3 |

## Prerequisites

Install these natively on your machine:

- **Python 3.11+**
- **Node.js 18+** and npm
- **PostgreSQL 14+** running locally
- **Redis** *(optional)* — if not installed, the app still runs; rate limiting just
  becomes a no-op.

### Create the database (one time)

```bash
# Using psql (adjust to your local Postgres auth):
psql -U postgres -c "CREATE USER educore WITH PASSWORD 'educore_pass';"
psql -U postgres -c "CREATE DATABASE educore OWNER educore;"
```

Then copy the env file and edit if your DB credentials differ:

```bash
cp .env.example .env
```

## Quick start — one command 🚀

After installing the prerequisites and creating the database, just run:

```bash
python run.py
```

That single command starts the **entire local environment**. `run.py` automatically:

- loads `.env` (creating it from `.env.example` on first run),
- verifies PostgreSQL is reachable (with a clear fix-it message if not),
- creates the backend virtualenv and installs dependencies if missing,
- applies database migrations and seeds demo data,
- detects Node.js / npm and runs `npm install` if `node_modules` is missing,
- starts the FastAPI backend and the React admin panel,
- starts the Telegram bot **only if** `TELEGRAM_BOT_TOKEN` is set in `.env`,
- prints service URLs and stops everything cleanly on `Ctrl+C`.

### Run individual services

```bash
python run.py            # everything (default)
python run.py --all      # everything (explicit)
python run.py --backend  # FastAPI backend only
python run.py --frontend # React admin panel only
python run.py --bot      # Telegram bot only
```

> Works on Windows, macOS, and Linux with `python run.py` (use `python3` on macOS/Linux
> if `python` is not aliased).

## Manual setup (optional)

Prefer to run services yourself? Helper scripts live in `scripts/` (`.sh` for
macOS/Linux, `.bat` for Windows), or run the steps directly:

**Backend**
```bash
cd backend
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
alembic upgrade head             # create tables
python -m app.seed               # demo data
uvicorn app.main:app --reload
pytest                           # run the test suite
```

**Frontend**
```bash
cd frontend
npm install
npm run dev                      # http://localhost:5173 (proxies /api -> :8000)
```

**Telegram bot** (set `TELEGRAM_BOT_TOKEN` in `.env` first)
```bash
cd bot
source ../backend/.venv/bin/activate
pip install -r requirements.txt
python -m main
```

### URLs

| Service        | URL |
|----------------|-----|
| Admin panel    | http://localhost:5173 |
| API + Swagger  | http://localhost:8000/docs |
| Health check   | http://localhost:8000/health |

### Seeded demo logins

| Role    | Phone           | Password    |
|---------|-----------------|-------------|
| Admin   | +998901112233   | Admin12345  |
| Teacher | +998901000001   | teacher123  |
| Student | +998901000101   | student123  |
| Parent  | +998901000010   | parent123   |

## Roles (RBAC)

- **Admin** — full access to every module.
- **Teacher** — own groups, take attendance, manage lessons, view students.
- **Student** — own schedule, payments, lessons, attendance (`/api/v1/me/*`).
- **Parent** — children's attendance & payments.

## Telegram bot

Users authenticate by **sharing their phone number** (Telegram contact); the backend
matches it to a registered user and binds the `telegram_id`. Menus and replies are
fully bilingual and adapt to the user's role:

- **Students** — my groups · attendance · payments · lessons
- **Teachers** — groups · take attendance (inline marking) · students
- **Parents** — children → attendance / payments
- 🌐 in-chat language switch (UZ/EN), persisted on the account.

## Internationalization

- **Frontend:** react-i18next, `src/i18n/locales/{uz,en}.json`, language switcher (persisted to `localStorage`).
- **Backend:** translatable message keys resolved via `Accept-Language` (`app/core/i18n.py`).
- **Bot:** `bot/locales/{uz,en}.py`.

Uzbek is the default everywhere.

## Project layout

```
LMS/
├── run.py                 single-command local launcher
├── .env.example
├── scripts/                local setup & run scripts (.sh + .bat)
├── backend/                FastAPI app
│   ├── app/
│   │   ├── core/           config, db, security, redis, i18n, deps, rate-limit, storage
│   │   ├── models/         SQLAlchemy ORM (3NF, FKs, indexes)
│   │   ├── schemas/        Pydantic v2
│   │   ├── repositories/   data-access layer
│   │   ├── services/       business logic
│   │   ├── api/v1/         versioned routers
│   │   ├── seed.py         idempotent demo data
│   │   └── main.py
│   ├── alembic/            migrations
│   └── tests/              pytest (auth, RBAC, modules, bot)
├── bot/                    aiogram 3 bot
├── frontend/               React admin
└── docs/API.md             full endpoint reference
```

## Security

JWT access + rotating refresh tokens (revocable, persisted), bcrypt password hashing,
role-based access control, Pydantic input validation, ORM-only queries (no raw SQL),
optional Redis-backed rate limiting, CORS allow-list.

## Future enhancements

- **Docker / Docker Compose support** — containerized deployment was intentionally
  removed for the V1 MVP to keep local development simple. It can be reintroduced
  later (a compose file orchestrating Postgres, Redis, backend, bot, and frontend).
- **Mobile app (V2)** — the stateless, versioned API is ready for it.
- **S3/MinIO storage** — storage layer is already abstracted (`app/core/storage.py`).
- **Multi-branch / SaaS** — add a `branch_id` tenant column + scoping.
