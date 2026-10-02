# Issue Tracker

A full-stack Issue Tracker built as a 5-hour development test. Users can register and log in, admins can create / edit / delete / assign issues, issues move through an **Open → In Progress → Closed** workflow with comments, and a dashboard shows live counters. The repository contains a **React (TypeScript) frontend** and a **FastAPI backend** with JWT authentication, backend-enforced role-based access control, and a full pytest suite (73 tests).

**Live deployment:**

| | URL |
| --- | --- |
| Frontend (Vercel) | <https://issue-tracker-ets.vercel.app> |
| Backend API (Render) | <https://issue-tracker-ets.onrender.com> |
| Swagger UI | <https://issue-tracker-ets.onrender.com/docs> |
| Health check | <https://issue-tracker-ets.onrender.com/api/health> |

---

## Table of Contents

- [Implemented Features](#implemented-features)
- [Architecture](#architecture)
- [Technology Stack](#technology-stack)
- [Project Structure](#project-structure)
- [Prerequisites](#prerequisites)
- [Local Installation and Setup](#local-installation-and-setup)
- [Environment Variables](#environment-variables)
- [Database Configuration and Migrations](#database-configuration-and-migrations)
- [Authentication](#authentication)
- [Authorization (RBAC)](#authorization-rbac)
- [API Endpoints](#api-endpoints)
- [Swagger UI / API Testing](#swagger-ui--api-testing)
- [Testing](#testing)
- [Deployment](#deployment)
- [Known Limitations and Future Improvements](#known-limitations-and-future-improvements)

## Implemented Features

- **User registration and login** — JWT-based sessions; registration requires `name`, `email`, `password` and `confirm_password` (min. 8 characters, must match).
- **Issue management (admin)** — create, edit (full `PUT` and partial `PATCH`), and delete issues; the reporter is set server-side from the authenticated admin.
- **Issue assignment (admin)** — assign an issue to any registered user, or unassign with `null`; validated against existing users.
- **Status tracking** — `open`, `in_progress`, `closed` via a dedicated status endpoint; admins can update any issue, regular users only issues assigned to them.
- **Priority** — `low`, `medium` (default), `high` on every issue.
- **Comments** — chronological comment threads on issues; admins comment on any issue, regular users on their assigned issues.
- **Dashboard** — live counters (total / open / in progress / closed) computed from the database, plus *recent issues* and *my assigned issues* lists; scoped by role.
- **Issue list with pagination, filters and search** — `page`, `page_size` (max 100), `status`, `assignee_id`, `unassigned`, and case-insensitive `search` over title/description.
- **Role-based access control** — `admin` and `user` roles, enforced on every backend endpoint (403 on violation), mirrored by role-aware UI.
- **Admin seeding** — idempotent `seed.py` bootstraps the admin account from environment variables; no credentials are hardcoded.
- **UX polish** — toast notifications, confirmation dialogs for destructive actions, protected/public route guards, session-expiry handling (redirect with `?expired=1`), 404 page.

## Architecture

```mermaid
flowchart LR
    subgraph Client["Browser"]
        UI["React SPA<br/>(Vercel static hosting)"]
    end

    subgraph Backend["Render - FastAPI web service"]
        API["FastAPI app<br/>/api routers + JWT + RBAC<br/>Swagger at /docs"]
    end

    DB[("PostgreSQL<br/>(deployment)<br/>SQLite for local dev)")]

    UI -- "HTTPS - axios - VITE_API_URL" --> API
    API -- "SQLAlchemy 2 (sync sessions)" --> DB
```

- **Development:** the Vite dev server proxies `/api/*` to `http://localhost:8000`, so no CORS setup is needed locally.
- **Production:** the SPA is served from Vercel and calls the Render API directly; CORS is restricted to the exact frontend origin via `CORS_ORIGINS`.

## Technology Stack

| Layer | Technology |
| --- | --- |
| Frontend | React 18, TypeScript 5.6, Vite 5, Tailwind CSS 3, React Router 6, Axios |
| Backend | Python 3.12+, FastAPI, SQLAlchemy 2 (ORM), Pydantic v2, pydantic-settings |
| Database | SQLite (zero-config local dev) → PostgreSQL (deployment, `psycopg` 3 driver) |
| Auth | JWT access tokens (PyJWT, HS256) + bcrypt password hashing |
| API docs | Swagger UI (`/docs`) and ReDoc (`/redoc`) |
| Testing | pytest + FastAPI `TestClient` (httpx) |
| Deployment | Vercel (frontend), Render (backend), GitHub (source) |

## Project Structure

```
.
├── backend/                      # FastAPI application
│   ├── app/
│   │   ├── api/
│   │   │   ├── deps.py           # Auth dependency + require_admin RBAC guard
│   │   │   └── routes/           # auth, users, issues, dashboard routers
│   │   ├── core/
│   │   │   ├── config.py         # Settings (env/.env), CORS parsing, SECRET_KEY fallback
│   │   │   └── security.py       # bcrypt hashing, JWT create/decode
│   │   ├── db/
│   │   │   ├── base.py           # Declarative Base
│   │   │   ├── session.py        # Engine + per-request session
│   │   │   └── init_db.py        # create_all on startup + legacy role normalization
│   │   ├── models/               # User, Issue, Comment ORM models
│   │   ├── schemas/              # Pydantic request/response schemas
│   │   └── main.py               # App entrypoint: routers, CORS, docs, health
│   ├── tests/                    # 73 pytest tests (auth, issues, RBAC, dashboard, seed)
│   ├── seed.py                   # Idempotent admin seeder (+ --demo for local data)
│   ├── requirements.txt          # Runtime dependencies
│   ├── requirements-dev.txt      # pytest + httpx
│   └── .env.example              # Config template (copy to .env)
├── frontend/                     # React + Vite application
│   ├── src/
│   │   ├── api/                  # Axios client (client.ts) + typed API modules
│   │   ├── components/
│   │   │   ├── layout/           # AppLayout, Sidebar, Topbar
│   │   │   ├── issues/           # IssueForm, IssueComments
│   │   │   ├── ui/               # Button, Input, Card, Badge, ConfirmDialog, ...
│   │   │   ├── ProtectedRoute.tsx / PublicOnlyRoute.tsx
│   │   ├── context/              # AuthContext (session), ToastContext (notifications)
│   │   ├── pages/                # Login, Register, Dashboard, Issues, Issue Details, Users, 404
│   │   ├── types/                # Shared domain types
│   │   └── lib/                  # Formatting helpers
│   ├── vercel.json               # SPA rewrite for Vercel
│   ├── vite.config.ts            # Dev server + /api proxy
│   ├── package.json
│   └── .env.example
├── BRD.md                        # Business Requirements Document
├── .gitignore                    # Ignores .env, *.db, node_modules, dist, ...
└── README.md
```

## Prerequisites

- **Python 3.12+** — `python --version`
- **Node.js 18+** and npm — `node --version`
- (Deployment only) A PostgreSQL database

## Local Installation and Setup

### 1. Backend (FastAPI)

```bash
cd backend

# Create and activate a virtual environment
python -m venv .venv
source .venv/Scripts/activate      # Windows (Git Bash)
# source .venv/bin/activate        # macOS / Linux

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env               # then adjust values (see Environment Variables)

# Create tables and seed the admin account (idempotent, reads ADMIN_* from .env)
python seed.py

# Optional: also seed local demo users and issues (never in production)
python seed.py --demo

# Start the API
uvicorn app.main:app --reload
```

The API is available at:

- Swagger UI: <http://localhost:8000/docs>
- ReDoc: <http://localhost:8000/redoc>
- Health check: <http://localhost:8000/api/health>

### 2. Frontend (React)

```bash
cd frontend
npm install
cp .env.example .env               # optional in dev; VITE_API_URL=/api
npm run dev
```

The app runs at <http://localhost:5173>. The Vite dev server proxies all `/api/*` requests to `http://localhost:8000`, so no CORS configuration is needed in development.

### 3. Sign in

- **Admin:** the account created by `python seed.py` — the email is the `ADMIN_EMAIL` value in `backend/.env`, and the password is the `ADMIN_PASSWORD` value you configured (never committed to the repository).
- **Demo users (local only):** `python seed.py --demo` creates demo accounts whose passwords are defined by the `DEMO_PASSWORD` constant in `backend/seed.py`.
- Or register a new account from the **Register** page — self-registered accounts always receive the `user` role.

## Environment Variables

> Only example/placeholder values are shown. Real values live in gitignored `.env` files (local) or the hosting provider's environment settings (production). Never commit secrets.

### Backend (`backend/.env` or process environment)

| Variable | Example value | Purpose |
| --- | --- | --- |
| `PROJECT_NAME` | `Issue Tracker API` | Shown in Swagger UI |
| `SECRET_KEY` | *(generate: `python -c "import secrets; print(secrets.token_hex(32))"`)* | JWT signing key. If unset, a random key is generated at startup with a warning (tokens then invalidate on restart) |
| `ALGORITHM` | `HS256` | JWT algorithm |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `1440` | Token lifetime (default 24 h) |
| `DATABASE_URL` | `sqlite:///./issue_tracker.db` or `postgresql+psycopg://user:password@localhost:5432/issue_tracker` | SQLAlchemy connection string |
| `CORS_ORIGINS` | `http://localhost:5173,http://127.0.0.1:5173` | Comma-separated allowed origins — exact match, no trailing slash |
| `ADMIN_NAME` | `Admin` | Display name for the seeded admin |
| `ADMIN_EMAIL` | `admin@example.com` | Email for the seeded admin (seeding skipped when empty) |
| `ADMIN_PASSWORD` | `change-me-strong-password` | Password for the seeded admin (min. 8 chars; bcrypt-hashed, never printed) |

### Frontend (`frontend/.env` or hosting environment)

| Variable | Example value | Purpose |
| --- | --- | --- |
| `VITE_API_URL` | `/api` (dev) · `https://issue-tracker-ets.onrender.com/api` (prod) | Backend base URL. **Must include the `/api` prefix.** Read at build time — rebuild/redeploy after changing it |

## Database Configuration and Migrations

- **Local development:** SQLite by default (`sqlite:///./issue_tracker.db`), zero configuration. The file is gitignored.
- **Deployment:** PostgreSQL via `DATABASE_URL=postgresql+psycopg://...` (the `psycopg` 3 driver is declared in `requirements.txt`).
- **Schema management:** on startup the backend runs `Base.metadata.create_all()` to create missing tables, plus one idempotent data fix (legacy `MEMBER` role → `USER`). **There is no Alembic migration tool yet** — introducing Alembic is listed as a future improvement before evolving the schema in production.
- **Seeding:** `python seed.py` is idempotent and safe to run repeatedly (it creates the admin only if the email does not exist, and only ensures the `admin` role otherwise).

## Authentication

- **Passwords** are hashed with **bcrypt** (first 72 bytes, per bcrypt's limit) and hashes are never included in API responses.
- **Login** (`POST /api/auth/login`) returns a signed **JWT access token** (PyJWT, HS256) whose subject is the user id; the default lifetime is 24 hours (`ACCESS_TOKEN_EXPIRE_MINUTES`).
- **Protected endpoints** require `Authorization: Bearer <token>`. Missing/invalid/expired tokens return `401` (expired tokens get a distinct "session has expired" message).
- The frontend stores the token in `localStorage` (`issue_tracker.token`), attaches it to every request via an Axios interceptor, and on a `401` clears the session and redirects to `/login?expired=1`.
- **Registration** enforces: valid email, name 2–120 chars, password 8–128 chars, `password == confirm_password`. Duplicate emails return `409`.

## Authorization (RBAC)

Roles are stored on the user (`admin` / `user`) and enforced on the **backend API** for every request; the frontend merely hides controls the user cannot use.

| Capability | Admin | User |
| --- | --- | --- |
| View issues | all issues | only issues assigned to them |
| Create / edit (`PUT`, `PATCH`) / delete issues | ✅ | ❌ `403` |
| Assign issues (assign, reassign, unassign) | ✅ | ❌ `403` |
| Update status (`open` / `in_progress` / `closed`) | ✅ any issue | ✅ only issues assigned to them |
| Comment | ✅ any issue | ✅ only on issues assigned to them |
| List users (`GET /api/users`) | ✅ | ❌ `403` |
| Dashboard counters/lists | whole project | scoped to their assigned tasks |

## API Endpoints

Base URL (production): `https://issue-tracker-ets.onrender.com/api` · (local): `http://localhost:8000/api`

| Method | Path | Auth | Description |
| --- | --- | --- | --- |
| GET | `/api/health` | — | Liveness probe → `{"status":"ok"}` |
| POST | `/api/auth/register` | — | Create account → `201` (duplicate email → `409`) |
| POST | `/api/auth/login` | — | Email + password → JWT (`200`); bad credentials → `401` |
| GET | `/api/auth/me` | Bearer | Current user's profile |
| GET | `/api/users` | Admin | All users (for assignment pickers), ordered by name |
| GET | `/api/issues` | Bearer | Paginated list, newest first. Query: `page`, `page_size` (1–100), `status`, `assignee_id`, `unassigned=true`, `search` (members receive only their assigned issues) |
| POST | `/api/issues` | Admin | Create issue → `201` (reporter set server-side) |
| GET | `/api/issues/{id}` | Bearer | Issue details (members: assigned issues only) |
| PUT | `/api/issues/{id}` | Admin | Full replacement of editable fields |
| PATCH | `/api/issues/{id}` | Admin | Partial update |
| PATCH | `/api/issues/{id}/status` | Admin or assignee | Update only `{"status": "open" \| "in_progress" \| "closed"}` |
| PATCH | `/api/issues/{id}/assign` | Admin | `{"assignee_id": <id> \| null}` — `null` unassigns |
| DELETE | `/api/issues/{id}` | Admin | Delete issue → `204` (comments cascade) |
| GET | `/api/issues/{id}/comments` | Bearer | Comments, oldest first |
| POST | `/api/issues/{id}/comments` | Bearer | Add comment → `201` (members: assigned issues only) |
| GET | `/api/dashboard/summary` | Bearer | Live counters + `recent_issues` + `my_assigned_issues` |

**Status codes:** `400` nonexistent assignee · `401` bad credentials / invalid or expired token · `403` RBAC violation · `404` missing issue · `409` duplicate email · `422` schema validation · `201` created · `204` deleted.

### Examples

```bash
# Register
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"name":"Jane Doe","email":"jane@example.com","password":"strong-pass-1","confirm_password":"strong-pass-1"}'

# Login (returns access_token)
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"jane@example.com","password":"strong-pass-1"}'

# Create an issue (admin token)
curl -X POST http://localhost:8000/api/issues \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"title":"Login page shows stale error","description":"Steps to reproduce...","priority":"medium","assignee_id":2}'

# List issues with filters
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/api/issues?page=1&page_size=10&status=open&search=login"
```

## Swagger UI / API Testing

1. Open <http://localhost:8000/docs> (or <https://issue-tracker-ets.onrender.com/docs> for the live API).
2. Click **Authorize**, paste a token obtained from `POST /api/auth/login` (value only — the `Bearer ` prefix is added by Swagger), and execute requests with the stored token.
3. The `HTTPBearer` scheme has `auto_error=False`, so unprotected endpoints (`/api/health`, register, login) work without a token. ReDoc is available at `/redoc`.

## Testing

```bash
cd backend
pip install -r requirements.txt -r requirements-dev.txt
python -m pytest tests -q        # or: python -m pytest tests -v
```

Current status: **73 passed** (verified locally).

The suite runs against an isolated SQLite database (`test_issue_tracker.db`, created fresh and deleted afterwards — the development database is never touched) and covers:

| File | Tests | Coverage |
| --- | --- | --- |
| `tests/test_auth.py` | 19 | Registration (success, duplicate email, password mismatch, weak/invalid input), login (valid/invalid), protected endpoints, garbage and expired tokens |
| `tests/test_issues.py` | 30 | CRUD, filters, search, pagination, assignment validation, comments (persistence, ordering, blank rejection, cascade deletes) |
| `tests/test_rbac.py` | 13 | Members blocked from create/edit/delete/assign/users (`403`), scoped lists/details/status updates, admin retains full access, member dashboard scoping |
| `tests/test_dashboard.py` | 5 | Counters react exactly to create/edit/assign/close/delete; recent and my-assigned lists |
| `tests/test_seed.py` | 6 | Idempotent admin seeding, bcrypt hashing (password never printed), role promotion, weak-password rejection, legacy `MEMBER` → `USER` normalization |

Frontend checks:

```bash
cd frontend
npm run build        # tsc --noEmit + vite build (typecheck + production bundle)
npm run typecheck    # TypeScript check only
npm run preview      # Preview the production build locally
```

## Deployment

### Deployment architecture

```mermaid
flowchart TB
    subgraph GH["GitHub"]
        REPO["joswintauro28/Issue-Tracker-ETS- (branch: dev)"]
    end

    subgraph Vercel["Vercel - frontend"]
        SPA["Static SPA build<br/>root: frontend/ - rewrite via vercel.json<br/>VITE_API_URL baked at build time"]
    end

    subgraph Render["Render - backend"]
        API2["FastAPI web service<br/>start: python seed.py && uvicorn app.main:app --host 0.0.0.0 --port $PORT<br/>env: SECRET_KEY, DATABASE_URL, CORS_ORIGINS, ADMIN_*"]
    end

    PG[("PostgreSQL<br/>via DATABASE_URL")]

    REPO -- "push" --> SPA
    REPO -- "push / manual deploy" --> API2
    SPA -- "HTTPS + CORS (exact origin)" --> API2
    API2 --> PG
```

| Piece | Hosting | Configuration in repo |
| --- | --- | --- |
| Frontend SPA | **Vercel** (static site) | `frontend/vercel.json` — SPA rewrite `/(.*) → /`; build `npm run build`, output `dist` |
| Backend API | **Render** (web service) | `backend/requirements.txt` (build), start command below, environment variables in dashboard |
| Source | **GitHub** | repo `joswintauro28/Issue-Tracker-ETS-`, working branch `dev` |
| Database | PostgreSQL, connection string supplied via `DATABASE_URL` | driver declared in `requirements.txt` |

### Backend (Render)

1. Create a **Web Service** from the GitHub repo with root directory `backend`.
2. **Build command:** `pip install -r requirements.txt`
3. **Start command:** `python seed.py && uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   (seeds the admin idempotently, then starts the API on Render's `$PORT`).
4. Set environment variables:

   | Variable | Value |
   | --- | --- |
   | `DATABASE_URL` | Postgres connection string. Render/Heroku-style `postgres://` URLs must be converted to SQLAlchemy form: `postgresql+psycopg://user:password@host:5432/dbname?sslmode=require` |
   | `SECRET_KEY` | A generated value: `python -c "import secrets; print(secrets.token_hex(32))"` |
   | `CORS_ORIGINS` | `https://issue-tracker-ets.vercel.app` — the exact origin, **no trailing slash** |
   | `ADMIN_NAME` / `ADMIN_EMAIL` / `ADMIN_PASSWORD` | Bootstrap admin (password min. 8 chars) |
   | `ACCESS_TOKEN_EXPIRE_MINUTES` | Optional; defaults to `1440` |

5. Deploy. The free instance tier sleeps when idle, so the first request after idle can take ~30 s.

### Frontend (Vercel)

1. Import the repo as a **static** project with root directory `frontend` (Framework: Vite).
2. Build command `npm run build`, output directory `dist` (Vite defaults).
3. Set the environment variable `VITE_API_URL=https://issue-tracker-ets.onrender.com/api` — **it must end with `/api`**, and it is read **at build time**.
4. The SPA rewrite in `frontend/vercel.json` is committed, so deep links (`/login`, `/issues/42`) work without extra config.

### Deploying an update

1. Push commits to the `dev` branch on GitHub.
2. **Backend:** redeploy the Render service (dashboard → *Manual Deploy* → *Deploy latest commit*, or enable auto-deploy). Environment changes require a service restart.
3. **Frontend:** create a new Vercel deployment (*Redeploy*). Any change to `VITE_API_URL` requires a **rebuild**, because Vite inlines it into the bundle.
4. Verify: `GET /api/health` on the backend returns `{"status":"ok"}`, and the app loads at the frontend URL. If a stale frontend bundle is served after redeploy, hard-refresh (`Ctrl+Shift+R`) — Vercel's CDN caches HTML briefly.

### Database migration and backup

- **Migrations:** none yet — schema is created with `create_all()` on startup. Before any schema change in production, introduce **Alembic** and run `alembic upgrade head` as part of the deploy step.
- **Backups:** no automated backup pipeline exists in this repository. Use the database provider's automated backups, or dump manually: `pg_dump $DATABASE_URL > backup.sql`.

## Known Limitations and Future Improvements

**Limitations**

- No Alembic migrations — schema changes rely on `create_all()` (fine for greenfield tables, not for altering existing ones).
- No password reset / email verification, no refresh tokens, no rate limiting.
- Comments cannot be edited or deleted and are not paginated.
- The Users page is a read-only directory (no role management UI); roles change only via seeding/database.
- Tokens are stored in `localStorage` (vulnerable to XSS rather than CSRF); no HTTP-only cookie option yet.
- The free Render instance sleeps when idle (slow first request); SQLite is local-file only (PostgreSQL is used in deployment).
- No CI/CD pipeline; tests run locally.

**Future improvements**

- Alembic migration workflow + automated backups.
- Refresh tokens or HTTP-only cookie sessions; rate limiting on auth endpoints.
- Comment edit/delete, notifications/mentions, file attachments.
- Optimistic locking (`updated_at`) for concurrent edits; DB-level indexes beyond the current ones.
- E2E tests (Playwright) and a CI workflow running the pytest suite on push.

---

Generated documentation for the Issue Tracker test project. See [BRD.md](BRD.md) for the Business Requirements Document.
