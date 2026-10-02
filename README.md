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

# Optional: seed demo users and issues
python seed.py

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
| `alice@example.com`| `password123` | member|
| `bob@example.com`  | `password123` | member|

Or register a new account from the Register page.

## API Endpoints

| Method | Path                            | Auth required | Description                       |
| ------ | ------------------------------- | ------------- | --------------------------------- |
| GET    | `/api/health`                   | No            | Liveness probe                    |
| POST   | `/api/auth/register`            | No            | Create an account (requires `confirm_password`) |
| POST   | `/api/auth/login`               | No            | Get a JWT access token            |
| GET    | `/api/auth/me`                  | Yes           | Current user profile              |
| GET    | `/api/users`                    | Yes           | List users                        |
| GET    | `/api/issues`                   | Yes           | List issues (`?status=open`)      |
| POST   | `/api/issues`                   | Yes           | Create an issue                   |
| GET    | `/api/issues/{id}`              | Yes           | Issue details                     |
| PATCH  | `/api/issues/{id}`              | Yes           | Update status/priority/assignee   |
| DELETE | `/api/issues/{id}`              | Yes           | Delete an issue (cascades comments)|
| GET    | `/api/issues/{id}/comments`     | Yes           | List comments on an issue         |
| POST   | `/api/issues/{id}/comments`     | Yes           | Add a comment                     |

Registration payload: `{ "name", "email", "password", "confirm_password" }`. Duplicate emails return `409`, invalid credentials `401`, expired tokens `401` with a session-expired message, and schema violations `422`.

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

### Frontend (`frontend/.env`)

| Variable        | Default | Purpose                                                |
| --------------- | ------- | ------------------------------------------------------ |
| `VITE_API_URL`  | `/api`  | Backend base URL; Vite proxies `/api` → `:8000` in dev |

## Development Commands

| Command                                          | Location     | Purpose                     |
| ------------------------------------------------ | ------------ | --------------------------- |
| `uvicorn app.main:app --reload`                  | `backend/`   | Run API with hot reload     |
| `python seed.py`                                 | `backend/`   | Seed demo data              |
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

The suite runs against an isolated SQLite database (`test_issue_tracker.db`, removed afterwards) and covers registration (success, duplicate email, password mismatch, weak/invalid input), login (valid and invalid credentials), protected endpoints without a token, garbage and expired tokens, and the comment flow including cascading deletes.

## Security Notes

- Passwords are hashed with bcrypt and hashes are never serialized in API responses (`UserRead` omits them).
- No secrets are hardcoded: `SECRET_KEY` comes from the environment / `backend/.env`. If it is missing, a random key is generated at startup (with a warning) and tokens are invalidated on restart.
- JWTs carry a configurable expiry (`ACCESS_TOKEN_EXPIRE_MINUTES`); expired or invalid tokens are rejected with `401`.
- All protected routes require a valid bearer token; the frontend clears the stored session on `401` and redirects to the login page with an expiry notice.
- CORS is restricted to the configured `CORS_ORIGINS` (the frontend dev server by default).

## Deploying with PostgreSQL

1. Install the PostgreSQL driver: `pip install "psycopg[binary]"` (uncommented in `requirements.txt`).
2. Point `DATABASE_URL` at your database, e.g.
   `DATABASE_URL=postgresql+psycopg://user:password@localhost:5432/issue_tracker`
3. Set a strong `SECRET_KEY` (e.g. `python -c "import secrets; print(secrets.token_hex(32))"`).
4. Set `CORS_ORIGINS` to your frontend origin.
5. Build the frontend (`npm run build`) and serve `dist/`, setting `VITE_API_URL` to the backend URL at build time.

The application uses `Base.metadata.create_all` on startup for simplicity. For a production PostgreSQL setup, introduce Alembic migrations before evolving the schema.
