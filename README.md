# Issue Tracker

A full-stack Issue Tracker built for a 5-hour development test. Single repository containing a React (TypeScript + Tailwind CSS) frontend and a Python FastAPI backend with SQLite for local development and PostgreSQL-ready configuration for deployment.

## Tech Stack

| Layer      | Technology                                              |
| ---------- | ------------------------------------------------------- |
| Frontend   | React 18, TypeScript, Vite, Tailwind CSS, React Router, Axios |
| Backend    | Python, FastAPI, SQLAlchemy 2 (ORM), Pydantic v2        |
| Database   | SQLite (local dev) → PostgreSQL (deployment)            |
| Auth       | JWT access tokens (PyJWT) + bcrypt password hashing     |
| API docs   | FastAPI Swagger UI (`/docs`) and ReDoc (`/redoc`)       |

## Project Structure

```
.
├── backend/                  # FastAPI application
│   ├── app/
│   │   ├── api/              # Dependencies (deps.py) and routers (routes/)
│   │   ├── core/             # Settings (config.py), security (JWT, bcrypt)
│   │   ├── db/               # Declarative base, engine/session management
│   │   ├── models/           # SQLAlchemy models (User, Issue, Comment)
│   │   ├── schemas/          # Pydantic request/response schemas
│   │   └── main.py           # App entrypoint (routers, CORS, docs)
│   ├── tests/                # Pytest suite (auth, protected endpoints, comments)
│   ├── seed.py               # Demo data seeder
│   ├── requirements.txt
│   ├── requirements-dev.txt  # pytest + httpx
│   └── .env / .env.example
├── frontend/                 # React + Vite application
│   ├── src/
│   │   ├── api/              # Axios client + typed API modules
│   │   ├── components/       # Layout (sidebar/topbar), ui/, issues/, guards
│   │   ├── context/          # AuthContext (JWT session state)
│   │   ├── lib/              # Formatting helpers
│   │   ├── pages/            # Login, Register, Dashboard, Issues, Issue Details, Users, 404
│   │   └── types/            # Shared domain types
│   ├── package.json
│   └── .env / .env.example
├── .gitignore
└── README.md
```

## Prerequisites

- Python 3.12+ (`python --version`)
- Node.js 18+ and npm (`node --version`)

## Getting Started

### 1. Backend (FastAPI)

From the `backend/` directory:

```bash
# Create and activate a virtual environment
python -m venv .venv
# Windows (bash / Git Bash):
source .venv/Scripts/activate
# macOS / Linux:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Environment variables (a dev-ready .env is included; see .env.example)
cp .env.example .env   # adjust if needed

# Seed the admin account (idempotent; reads ADMIN_* from .env)
python seed.py

# Optional: also seed local demo users and issues
python seed.py --demo

# Start the API (from the backend/ directory)
uvicorn app.main:app --reload
```

The API is now available at:

- Swagger UI: <http://localhost:8000/docs>
- ReDoc: <http://localhost:8000/redoc>
- Health check: <http://localhost:8000/api/health>

### 2. Frontend (React)

From the `frontend/` directory (new terminal):

```bash
npm install

# Environment variables (optional in dev; see .env.example)
cp .env.example .env

npm run dev
```

The app is available at <http://localhost:5173>. The Vite dev server proxies all `/api/*` requests to `http://localhost:8000`, so no CORS configuration is needed in development.

### 3. Sign in

With the seeded database, use:

| Email              | Password      | Role  |
| ------------------ | ------------- | ----- |
| `admin@example.com`| `password123` | admin |
| `alice@example.com`| `password123` | user  |
| `bob@example.com`  | `password123` | user  |

Or register a new account from the Register page.

## API Endpoints

| Method | Path                            | Auth required | Description                                        |
| ------ | ------------------------------- | ------------- | -------------------------------------------------- |
| GET    | `/api/health`                   | No            | Liveness probe                                     |
| POST   | `/api/auth/register`            | No            | Create an account (requires `confirm_password`)    |
| POST   | `/api/auth/login`               | No            | Get a JWT access token                             |
| GET    | `/api/auth/me`                  | Yes           | Current user profile                               |
| GET    | `/api/users`                    | Admin only    | List users (for assignment pickers)                |
| GET    | `/api/issues`                   | Yes           | Paginated list: `?page=&page_size=&status=&assignee_id=&unassigned=&search=` (members: assigned only) |
| POST   | `/api/issues`                   | Admin only    | Create an issue (reporter set server-side)         |
| GET    | `/api/issues/{id}`              | Yes           | Issue details                                      |
| PUT    | `/api/issues/{id}`              | Admin only    | Edit an issue (full replacement)                   |
| PATCH  | `/api/issues/{id}`              | Admin only    | Partial update                                     |
| PATCH  | `/api/issues/{id}/status`       | Admin/assignee| Update only the status                             |
| PATCH  | `/api/issues/{id}/assign`       | Admin only    | Assign to a user (`null` unassigns)                |
| DELETE | `/api/issues/{id}`              | Admin only    | Delete an issue (cascades comments)                |
| GET    | `/api/issues/{id}/comments`     | Yes           | List comments on an issue (chronological)          |
| POST   | `/api/issues/{id}/comments`     | Yes           | Add a comment (members: assigned issues only)      |
| GET    | `/api/dashboard/summary`        | Yes           | Live counters, recent issues, my assigned issues   |

Registration payload: `{ "name", "email", "password", "confirm_password" }`. Duplicate emails return `409`, invalid credentials `401`, expired tokens `401` with a session-expired message, schema violations `422`, nonexistent assignees `400`, missing issues `404`.

## Authorization (RBAC)

Roles are stored on the user (`admin` / `user`) and enforced on the **backend APIs** for every request:

| Capability                                            | Admin | User  |
| ----------------------------------------------------- | ----- | ----- |
| View all issues                                       | ✅    | ❌ (only issues assigned to them) |
| Create / edit (PUT, PATCH) / delete issues            | ✅    | ❌ (`403`) |
| Assign issues (any target, incl. unassign)            | ✅    | ❌ (`403`) — regular users can never assign |
| Update status (open / in_progress / closed)           | ✅ (any issue) | ✅ (only issues assigned to them) |
| Comment                                               | ✅    | ✅ (only on issues assigned to them) |
| List users (`/api/users`)                             | ✅    | ❌ (`403`) |
| Dashboard counters                                    | whole project | scoped to their assigned tasks |

Violations return `403` with a readable message; the frontend mirrors these rules (create/edit/delete/assign controls and the Users page are hidden for members) but hiding UI is never the only barrier.

To try protected endpoints in Swagger UI, click **Authorize**, paste a token from `POST /api/auth/login`, and execute requests with the stored token.

## Environment Variables

### Backend (`backend/.env`)

| Variable                       | Default                          | Purpose                        |
| ------------------------------ | -------------------------------- | ------------------------------ |
| `PROJECT_NAME`                 | `Issue Tracker API`              | Shown in Swagger UI            |
| `SECRET_KEY`                   | dev value                        | JWT signing key (change in prod) |
| `ALGORITHM`                    | `HS256`                          | JWT algorithm                  |
| `ACCESS_TOKEN_EXPIRE_MINUTES`  | `1440`                           | Token lifetime                 |
| `DATABASE_URL`                 | `sqlite:///./issue_tracker.db`   | SQLAlchemy connection string   |
| `CORS_ORIGINS`                 | `http://localhost:5173,...`      | Comma-separated allowed origins|
| `ADMIN_NAME`                   | *(empty)*                        | Display name for the seeded admin |
| `ADMIN_EMAIL`                  | *(empty)*                        | Email for the seeded admin (skips seeding when empty) |
| `ADMIN_PASSWORD`               | *(empty)*                        | Password for the seeded admin (8+ chars; hashed, never printed) |

### Frontend (`frontend/.env`)

| Variable        | Default | Purpose                                                |
| --------------- | ------- | ------------------------------------------------------ |
| `VITE_API_URL`  | `/api`  | Backend base URL; Vite proxies `/api` → `:8000` in dev |

## Admin Seeding

The admin account is bootstrapped from environment variables - no credentials are hardcoded:

```bash
# backend/.env (local, gitignored) or real environment variables (production)
ADMIN_NAME=Admin
ADMIN_EMAIL=admin@example.com
ADMIN_PASSWORD=change-me-strong-password

# Run from backend/ - idempotent, safe to run repeatedly
python seed.py
```

Behaviour:

- Creates the user with role `admin` **only if no user with that email exists**; the password is hashed with bcrypt and never printed.
- If the email already exists, the script only ensures the role is `admin` (logged) - no duplicate accounts.
- If `ADMIN_EMAIL` / `ADMIN_PASSWORD` are unset, seeding is skipped with a warning (exit `0`), so the command is safe in every environment.
- Rejects passwords shorter than 8 characters (exit `1`).
- Regular users registered through the API always receive the `user` role.
- `.env` files are gitignored; only `.env.example` (placeholders) is committed.
- Add `--demo` to also create local demo users and issues - never in production.

## Development Commands

| Command                                          | Location     | Purpose                     |
| ------------------------------------------------ | ------------ | --------------------------- |
| `uvicorn app.main:app --reload`                  | `backend/`   | Run API with hot reload     |
| `python seed.py`                                 | `backend/`   | Seed admin (idempotent)     |
| `python seed.py --demo`                          | `backend/`   | Seed admin + demo data      |
| `python -m pytest tests -v`                      | `backend/`   | Run the backend test suite  |
| `npm run dev`                                    | `frontend/`  | Run frontend dev server     |
| `npm run build`                                  | `frontend/`  | Typecheck + production build|
| `npm run typecheck`                              | `frontend/`  | TypeScript check only       |
| `npm run preview`                                | `frontend/`  | Preview the production build|

## Testing

```bash
cd backend
pip install -r requirements-dev.txt
python -m pytest tests -v
```

The suite runs against an isolated SQLite database (`test_issue_tracker.db`, removed afterwards) and covers:

- **Auth**: registration (success, duplicate email, password mismatch, weak/invalid input), login (valid and invalid credentials), protected endpoints, garbage and expired tokens.
- **Issue management**: CRUD, filters, search and pagination.
- **RBAC**: members blocked from create/edit/delete/assign/users (`403`), member lists and detail views scoped to assigned tasks only, member status updates limited to assigned tasks, admin retains full access, member dashboard scoped.
- **Comments**: persistence verified directly against the database (author, timestamps), chronological ordering, blank/missing-issue rejection, cascading deletes.
- **Dashboard**: counters change exactly with create/edit/assign/close/delete operations, verified against the database; recent-issues and my-assigned-issues lists.
- **Admin seeding**: script run twice stays idempotent (single account), password is bcrypt-hashed and never printed, existing regular users are promoted, unconfigured/weak-password runs behave correctly, legacy `MEMBER` roles are normalized to `USER`.

## Security Notes

- Passwords are hashed with bcrypt and hashes are never serialized in API responses (`UserRead` omits them).
- No secrets are hardcoded: `SECRET_KEY` comes from the environment / `backend/.env`. If it is missing, a random key is generated at startup (with a warning) and tokens are invalidated on restart.
- JWTs carry a configurable expiry (`ACCESS_TOKEN_EXPIRE_MINUTES`); expired or invalid tokens are rejected with `401`.
- All protected routes require a valid bearer token; the frontend clears the stored session on `401` and redirects to the login page with an expiry notice.
- CORS is restricted to the configured `CORS_ORIGINS` (the frontend dev server by default).

## Deploying with PostgreSQL

1. Install the PostgreSQL driver: `pip install "psycopg[binary]"` (declared in `requirements.txt`).
2. Point `DATABASE_URL` at your database, e.g.
   `DATABASE_URL=postgresql+psycopg://user:password@localhost:5432/issue_tracker`
3. Set a strong `SECRET_KEY` (e.g. `python -c "import secrets; print(secrets.token_hex(32))"`).
4. Set `CORS_ORIGINS` to your frontend origin.
5. Set `ADMIN_NAME`, `ADMIN_EMAIL` and `ADMIN_PASSWORD` (strong, 8+ characters) and run
   `python seed.py` once to create the admin account (idempotent; safe to re-run).
6. Build the frontend (`npm run build`) and serve `dist/`, setting `VITE_API_URL` to the backend URL at build time.

The application uses `Base.metadata.create_all` on startup for simplicity. For a production PostgreSQL setup, introduce Alembic migrations before evolving the schema.
