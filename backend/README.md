# NUMÉ AI Marketing Assistant — Backend (Phase 1.1)

A production-ready **FastAPI + SQLAlchemy 2.0 + PostgreSQL** backend for the
NUMÉ AI Marketing Assistant. Phase 1.1 ships authentication, RBAC, full CRUD
for the core domain entities, Alembic migrations, Docker support and a clean
architecture (repositories → services → API).

> ⚠️ **Phase 1.1 scope.** This release intentionally **does not** include AI,
> LangChain, RAG, vector databases or chatbot functionality. The schema has
> been designed so AI features can be added in a later phase without further
> migrations.

---

## ✨ Features

- **Authentication** — JWT login, register, logout, refresh-token rotation,
  password hashing (bcrypt) and session revocation.
- **Role-Based Access Control** — four default roles (admin, manager, editor,
  viewer) with class-based guards.
- **13 SQLAlchemy 2.0 models** — Users, Roles, Sessions, Products,
  KnowledgeDocuments, Campaigns, GeneratedContent, BrandGuidelines,
  Competitors, CustomerReviews, Uploads, Settings, AuditLogs.
- **Full CRUD REST APIs** — Auth, Users, Products, Knowledge, Campaigns,
  Uploads (with file upload + download), Settings.
- **Clean architecture** — Repository pattern, service layer, dependency
  injection, separation of concerns.
- **Middleware** — CORS, request/response logging with `X-Request-ID`, global
  exception handler with consistent JSON envelopes.
- **Alembic migrations** — single initial migration creates the full schema.
- **Docker Compose** — PostgreSQL 16 + Redis 7 + backend container with
  health-checks, auto-migration and DB seeding.
- **Settings via `.env`** — pydantic-settings v2 with validation.
- **Audit logging** — extensible audit-trail table + service.
- **Test suite** — pytest fixtures, in-memory SQLite, tests for health, auth
  and products.

---

## 🧱 Tech Stack

| Concern            | Library                  |
| ------------------ | ------------------------ |
| Framework          | FastAPI 0.115            |
| Language           | Python 3.12              |
| ORM                | SQLAlchemy 2.0           |
| Migrations         | Alembic 1.14             |
| Database           | PostgreSQL 16            |
| Cache              | Redis 7                  |
| Auth               | python-jose + passlib    |
| Validation         | Pydantic v2 + pydantic-settings |
| HTTP server        | Uvicorn                  |
| Logging            | stdlib logging + loguru + JSON formatter |
| Testing            | pytest + httpx           |

---

## 📂 Project Structure

```
backend/
├── app/
│   ├── api/
│   │   └── v1/
│   │       ├── router.py         # aggregates all routers
│   │       ├── auth.py           # /auth (login, register, refresh, logout, me)
│   │       ├── users.py          # /users CRUD
│   │       ├── products.py       # /products CRUD
│   │       ├── knowledge.py      # /knowledge CRUD
│   │       ├── campaigns.py      # /campaigns CRUD
│   │       ├── uploads.py        # /uploads (file upload, list, download, delete)
│   │       └── settings.py       # /settings CRUD + upsert by key
│   ├── core/
│   │   ├── security.py           # JWT + password hashing
│   │   ├── exceptions.py         # AppException hierarchy
│   │   └── logging.py            # logging setup
│   ├── config/
│   │   └── settings.py           # pydantic-settings
│   ├── database/
│   │   ├── base.py               # declarative base + mixins
│   │   ├── session.py            # engine, SessionLocal, get_db
│   │   └── init_db.py            # seed roles + admin
│   ├── models/                   # 13 SQLAlchemy models
│   ├── schemas/                  # Pydantic v2 schemas
│   ├── repositories/             # generic BaseRepository + specific repos
│   ├── services/                 # business logic
│   ├── middleware/               # CORS, logging, exception handlers
│   ├── dependencies/             # auth, db, pagination
│   ├── utils/                    # helpers
│   └── main.py                   # FastAPI app factory + lifespan
├── migrations/                   # Alembic
│   ├── env.py
│   ├── script.py.mako
│   └── versions/0001_initial.py
├── tests/                        # pytest suite
├── uploads/                      # local file storage
├── logs/                         # rotating logs
├── alembic.ini
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── .env.example
├── pytest.ini
└── README.md
```

---

## 🚀 Quickstart (Docker Compose)

The fastest way to run everything is via Docker Compose:

```bash
# 1. Copy .env.example → .env and edit values
cp .env.example .env

# 2. Build and start PostgreSQL, Redis and the backend
docker compose up --build

# 3. Open the interactive API docs
open http://localhost:8000/docs
```

The backend container automatically runs:

1. `alembic upgrade head` — applies all migrations.
2. `python -m app.database.init_db` — seeds the four default roles and a
   superuser (`admin@nume.ai` / `Admin@12345`).
3. `uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 2` — starts the
   API server.

---

## 🛠 Local development (without Docker)

### Prerequisites

- Python 3.12
- PostgreSQL 16 (or use Docker just for the DB: `docker compose up db redis`)
- Redis 7 (optional — the backend gracefully degrades if Redis is unreachable)

### Setup

```bash
# 1. Create + activate a virtualenv
python3.12 -m venv venv
source venv/bin/activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure environment
cp .env.example .env
# edit .env to point DATABASE_URL at your local PostgreSQL

# 4. Run migrations
alembic upgrade head

# 5. Seed default roles + admin user
python -m app.database.init_db

# 6. Start the dev server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

---

## 🔐 Default credentials

After running `init_db`, a superuser is created:

| Email             | Password      |
| ----------------- | ------------- |
| `admin@nume.ai`   | `Admin@12345` |

**Change this password immediately in any non-demo environment.**

---

## 📡 API overview

All API routes are prefixed with `/api/v1`.

### Auth (`/auth`)

| Method | Endpoint       | Description                          |
| ------ | -------------- | ------------------------------------ |
| POST   | `/auth/register` | Register a new user                |
| POST   | `/auth/login`    | Login → access + refresh tokens    |
| POST   | `/auth/refresh`  | Exchange refresh token → new access|
| POST   | `/auth/logout`   | Revoke a session                   |
| POST   | `/auth/logout-all` | Revoke all sessions              |
| GET    | `/auth/me`       | Get the current user               |

### Users (`/users`)

| Method | Endpoint         | Auth            | Description            |
| ------ | ---------------- | --------------- | ---------------------- |
| GET    | `/users`         | admin, manager  | List users (paginated) |
| GET    | `/users/{id}`    | admin, manager  | Get a user             |
| POST   | `/users`         | admin           | Create a user          |
| PATCH  | `/users/{id}`    | admin, manager  | Update a user          |
| DELETE | `/users/{id}`    | admin           | Delete a user          |

### Products / Knowledge / Campaigns (`/products`, `/knowledge`, `/campaigns`)

Each resource follows the same shape:

| Method | Endpoint             | Auth            | Description         |
| ------ | -------------------- | --------------- | ------------------- |
| GET    | `/{resource}`        | any user        | List (paginated)    |
| GET    | `/{resource}/{id}`   | any user        | Get one             |
| POST   | `/{resource}`        | any user        | Create              |
| PATCH  | `/{resource}/{id}`   | any user        | Update              |
| DELETE | `/{resource}/{id}`   | any user        | Delete              |

### Uploads (`/uploads`)

| Method | Endpoint                  | Auth      | Description               |
| ------ | ------------------------- | --------- | ------------------------- |
| GET    | `/uploads`                | any user  | List uploads              |
| GET    | `/uploads/{id}`           | any user  | Get an upload             |
| POST   | `/uploads`                | any user  | Upload a file (multipart) |
| DELETE | `/uploads/{id}`           | any user  | Delete + remove file      |
| GET    | `/uploads/{id}/download`  | any user  | Download the file         |

### Settings (`/settings`)

| Method | Endpoint              | Auth               | Description                |
| ------ | --------------------- | ------------------ | -------------------------- |
| GET    | `/settings`           | any user           | List (sensitive masked)    |
| GET    | `/settings/{id}`      | any user           | Get by ID                  |
| GET    | `/settings/by-key/{k}`| any user           | Get by key                 |
| POST   | `/settings`           | admin, manager     | Create                     |
| PUT    | `/settings/by-key/{k}`| admin, manager     | Upsert by key              |
| PATCH  | `/settings/{id}`      | admin, manager     | Update                     |
| DELETE | `/settings/{id}`      | admin              | Delete                     |

### System

| Method | Endpoint   | Description        |
| ------ | ---------- | ------------------ |
| GET    | `/`        | Service metadata   |
| GET    | `/health`  | Liveness probe     |
| GET    | `/healthz` | K8s liveness probe |
| GET    | `/docs`    | Swagger UI (dev)   |
| GET    | `/redoc`   | ReDoc (dev)        |

---

## 🧪 Tests

Tests use pytest with an in-memory SQLite database (no PostgreSQL required):

```bash
pytest
```

Coverage:

- `tests/test_health.py` — health endpoints
- `tests/test_auth.py` — register, login, refresh, logout, /me, RBAC
- `tests/test_products.py` — full CRUD + duplicate SKU conflict

---

## 🔧 Configuration

All configuration is read from environment variables (or `.env`). Key variables:

| Variable                     | Default                  | Description                          |
| ---------------------------- | ------------------------ | ------------------------------------ |
| `APP_ENV`                    | `development`            | development / staging / production   |
| `APP_DEBUG`                  | `true`                   | Debug mode (echo SQL, expose errors) |
| `FRONTEND_URL`               | `http://localhost:5173`  | CORS origin                          |
| `DATABASE_URL`               | `postgresql+psycopg2://…`| SQLAlchemy URL                       |
| `REDIS_URL`                  | `redis://localhost:6379/0` | Redis connection string            |
| `JWT_SECRET`                 | _change me_              | JWT signing secret                   |
| `ACCESS_TOKEN_EXPIRE_MINUTES`| `30`                     | Access token TTL                     |
| `REFRESH_TOKEN_EXPIRE_DAYS`  | `7`                      | Refresh token TTL                    |
| `UPLOAD_PATH`                | `./uploads`              | Local upload directory               |
| `MAX_UPLOAD_SIZE_MB`         | `50`                     | Max file size for uploads            |
| `OPENAI_API_KEY`             | _(empty)_                | Stored only, **not used** in Phase 1.1 |
| `CLAUDE_API_KEY`             | _(empty)_                | Stored only, **not used** in Phase 1.1 |
| `GEMINI_API_KEY`             | _(empty)_                | Stored only, **not used** in Phase 1.1 |
| `LOG_LEVEL`                  | `INFO`                   | Logging level                        |

---

## 🏗 Architecture

```
HTTP Request
    ↓
[Middleware: CORS → RequestLogging → ExceptionHandlers]
    ↓
[API Router → Endpoint]
    ↓
[Dependencies: get_db, get_current_user, require_role]
    ↓
[Service Layer — business logic, raises AppException subclasses]
    ↓
[Repository Layer — generic CRUD + custom queries]
    ↓
[SQLAlchemy 2.0 Models → PostgreSQL]
```

- **Repository pattern** — `BaseRepository` provides `get`, `list`, `create`,
  `update`, `delete`; specific repos add custom queries.
- **Service layer** — encapsulates business rules; raises
  `AppException`-derived errors.
- **Dependency injection** — FastAPI `Depends` wires DB sessions, the current
  user and pagination params.
- **Migrations** — Alembic with a single initial migration covering all 13
  tables.

---

## 🔒 Security notes

- Passwords hashed with bcrypt (Passlib).
- JWTs signed with HS256; refresh tokens carry a `jti` stored in the
  `sessions` table for revocation.
- Logout revokes the session; logout-all revokes every active session.
- Superusers bypass role checks.
- Settings marked `is_sensitive` are masked in API responses.

---

## 🗺 Roadmap (future phases)

- AI content generation (OpenAI / Claude / Gemini)
- RAG over knowledge base + vector store
- Audit-log middleware auto-recording all mutations
- Async background tasks (Celery + Redis)
- S3 / object-storage backend for uploads
- Comprehensive integration tests against PostgreSQL

---

## 📜 License

Proprietary — © NUMÉ Beauty Labs. All rights reserved.
