# NUMÉ AI Marketing Assistant — Fullstack

A fully integrated **React 19 + Vite + TypeScript** frontend talking to a
**FastAPI + SQLAlchemy 2.0 + PostgreSQL** backend, with Redis cache, JWT
authentication, role-based access control, real file uploads and a clean
architecture ready for Phase 2 (RAG + AI agents).

> ✅ **Phase 1.1 — Integration complete.**
> ⏭️ Phase 2 placeholders (RAG, vector DB, LLM providers, agents, memory,
>   prompts, embeddings) are scaffolded under `backend/app/ai/`,
>   `backend/app/rag/` and `backend/app/vector/` but **not implemented**.

---

## ✨ What's integrated

| Concern                   | Status | Notes |
| ------------------------- | ------ | ----- |
| JWT authentication        | ✅     | login / register / refresh / logout / logout-all |
| Refresh-token rotation    | ✅     | axios interceptor auto-refreshes on 401 |
| Protected routes          | ✅     | `AppLayout` redirects unauthenticated users |
| Role-based access         | ✅     | backend enforces `require_roles("admin", …)` |
| Products CRUD             | ✅     | search, filter, pagination, create/update/delete |
| Knowledge CRUD            | ✅     | search, filter, preview, delete |
| Campaigns CRUD            | ✅     | list with metrics + budget utilisation |
| Users CRUD                | ✅     | admin-only create/delete, with strong password rule |
| Uploads (file upload)     | ✅     | drag&drop, multi-file, progress, preview, replace, download |
| Settings CRUD             | ✅     | key/value store with sensitive-value masking |
| Global loading state      | ✅     | React Query `isLoading` / skeletons everywhere |
| API error handling        | ✅     | normalised `ApiError`, toast on failure |
| Phase 2 scaffolding       | ✅     | `app/ai/`, `app/rag/`, `app/vector/` placeholders |

## 🧱 Architecture

```
┌───────────────────────────┐        ┌──────────────────────────────┐
│  Frontend (React + Vite)  │        │  Backend (FastAPI)           │
│                           │  HTTPS │                              │
│  Axios client             │ ──────▶│  /api/v1/* routes            │
│   ├─ request interceptor  │        │   ├─ Auth (JWT)              │
│   │  (Bearer token)       │        │   ├─ Users CRUD              │
│   └─ response interceptor │        │   ├─ Products CRUD           │
│      (auto-refresh 401)   │        │   ├─ Knowledge CRUD          │
│                           │        │   ├─ Campaigns CRUD          │
│  React Query hooks        │        │   ├─ Uploads (multipart)     │
│   └─ useApi.ts            │        │   └─ Settings CRUD           │
│                           │        │                              │
│  Pages                    │        │  Service layer               │
│   ├─ Login                │        │   └─ business logic          │
│   ├─ Dashboard            │        │                              │
│   ├─ Products             │        │  Repository layer            │
│   ├─ Knowledge            │        │   └─ generic BaseRepository  │
│   ├─ Campaigns            │        │                              │
│   ├─ Uploads              │        │  SQLAlchemy 2.0 models       │
│   ├─ Users                │        │   └─ 13 tables               │
│   ├─ Settings             │        │                              │
│   └─ Profile / 404        │        │  Middleware                  │
└───────────────────────────┘        │   ├─ CORS                    │
                                     │   ├─ Request logging         │
                                     │   └─ Exception handlers      │
                                     │                              │
                                     │  Phase 2 placeholders        │
                                     │   ├─ app/ai/providers        │
                                     │   ├─ app/ai/agents           │
                                     │   ├─ app/ai/memory           │
                                     │   ├─ app/ai/prompts          │
                                     │   ├─ app/ai/embeddings       │
                                     │   ├─ app/rag                 │
                                     │   └─ app/vector              │
                                     └──────────────┬───────────────┘
                                                    │
                                       ┌────────────┴────────────┐
                                       │  PostgreSQL 16          │
                                       │  Redis 7                │
                                       └─────────────────────────┘
```

## 📂 Project layout

```
nume-fullstack/
├── frontend/                  # React 19 + Vite + TS + Tailwind + shadcn/ui
│   ├── src/
│   │   ├── api/
│   │   │   ├── client.ts      # axios + JWT interceptor + refresh
│   │   │   ├── index.ts
│   │   │   └── mock/services.ts  # real backend API calls
│   │   ├── components/        # ui, layout, common, dashboard
│   │   ├── context/           # AuthContext, ThemeProvider, SidebarContext
│   │   ├── hooks/useApi.ts    # React Query hooks
│   │   ├── pages/             # 12 pages
│   │   ├── types/             # shared TS types
│   │   └── lib/               # utils, queryClient, nav
│   ├── Dockerfile
│   ├── .env                   # VITE_API_BASE_URL=http://localhost:8000/api/v1
│   └── package.json
│
├── backend/                   # FastAPI + SQLAlchemy 2.0 + PostgreSQL
│   ├── app/
│   │   ├── api/v1/            # auth, users, products, knowledge, campaigns, uploads, settings
│   │   ├── core/              # security (JWT, bcrypt), exceptions, logging
│   │   ├── config/            # pydantic-settings
│   │   ├── database/          # base, session, init_db
│   │   ├── models/            # 13 SQLAlchemy models
│   │   ├── schemas/           # Pydantic v2 schemas
│   │   ├── repositories/      # generic BaseRepository + per-entity
│   │   ├── services/          # business logic
│   │   ├── middleware/        # CORS, logging, exception handlers
│   │   ├── dependencies/      # auth, db, pagination, RBAC
│   │   ├── utils/
│   │   ├── ai/                # ⏭ Phase 2: providers, agents, memory, prompts, embeddings
│   │   ├── rag/               # ⏭ Phase 2: RAG pipeline
│   │   ├── vector/            # ⏭ Phase 2: vector store interface
│   │   └── main.py            # FastAPI app factory
│   ├── migrations/            # Alembic
│   ├── tests/                 # pytest (17 tests)
│   ├── uploads/               # local file storage
│   ├── logs/
│   ├── Dockerfile
│   ├── docker-compose.yml     # backend-only compose (also exists)
│   ├── alembic.ini
│   ├── requirements.txt
│   └── .env
│
├── docker-compose.yml         # ⭐ fullstack compose (DB + Redis + backend + frontend)
├── .env.example
└── README.md                  # ← you are here
```

## 🚀 Quickstart

### Option A — Docker Compose (recommended, one command)

```bash
# 1. Copy env files
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env

# 2. Boot everything
docker compose up --build

# 3. Open the app
open http://localhost:5173         # frontend
open http://localhost:8000/docs    # backend Swagger UI
```

The backend container automatically:
1. Runs `alembic upgrade head` (creates the 13-table schema)
2. Runs `python -m app.database.init_db` (seeds 4 roles + admin user)
3. Starts uvicorn on port 8000

### Option B — Local dev (fastest iteration)

```bash
# ─── Terminal 1: backend ─────────────────────────────
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env          # edit DATABASE_URL if needed
alembic upgrade head
python -m app.database.init_db
uvicorn app.main:app --reload --port 8000

# ─── Terminal 2: frontend ────────────────────────────
cd frontend
npm install
cp .env.example .env
npm run dev                   # → http://localhost:5173
```

> 💡 If you don't have a local PostgreSQL, spin one up with:
> `docker compose up db redis -d`

## 🔐 Default credentials

After `init_db` runs:

| Email             | Password      | Role  |
| ----------------- | ------------- | ----- |
| `admin@nume.ai`   | `Admin@12345` | admin (superuser) |

The login form is pre-filled with these credentials.

## 🔄 JWT auth flow

```
1. POST /api/v1/auth/login
      { email, password }
   ←  { access_token, refresh_token, user }

2. Frontend stores both tokens in localStorage
   (nume.access, nume.refresh)

3. Every request includes:
      Authorization: Bearer <access_token>

4. When access_token expires (401):
   ├─ Axios interceptor catches 401
   ├─ POST /api/v1/auth/refresh { refresh_token }
   ├─ Stores new access_token + refresh_token
   └─ Replays the original request

5. POST /api/v1/auth/logout { refresh_token }
   ← Revokes the session in DB
```

The interceptor also handles concurrent requests during refresh: only one
refresh call is fired; other requests queue and replay once the new token
arrives.

## 📤 File uploads

Drag & drop multiple files into the Uploads page. The frontend:

1. Validates file type (PDF, DOCX, TXT, CSV, PNG, JPG, WEBP, MP4, MOV)
2. Auto-detects category (Knowledge / Report / Asset / Other)
3. Shows a per-file progress bar
4. POSTs to `/api/v1/uploads` as `multipart/form-data`
5. On success, invalidates the React Query cache so the list refreshes

Backend stores files under `uploads/<year>/<month>/<uuid>_<filename>`,
computes a SHA-256 checksum, persists an `Upload` row in PostgreSQL, and
serves downloads via `/api/v1/uploads/{id}/download`.

**Replace** is implemented client-side as delete-then-upload (backend
expose a PUT endpoint in a future phase).

## 🛡️ Role-Based Access Control

| Role    | Permissions |
| ------- | ----------- |
| admin   | Everything. Can manage users, settings, all CRUD. |
| manager | Read most resources; can manage users (list/get). |
| editor  | Read + create/update on content resources. |
| viewer  | Read-only. |

The backend enforces this via `Depends(require_roles("admin", "manager"))`
on protected endpoints. Superusers (the seeded admin) bypass role checks.

## 🧪 Testing

### Backend (pytest, 17 tests)

```bash
cd backend
source .venv/bin/activate
pytest -v
```

Covers: health endpoints, register/login/refresh/logout, RBAC, product
CRUD with conflict detection.

### Frontend (build verification)

```bash
cd frontend
npm run build        # tsc -b && vite build — type-checks + bundles
```

### End-to-end manual smoke test

1. Start backend + frontend (Option A or B above).
2. Open http://localhost:5173 → login with `admin@nume.ai / Admin@12345`.
3. Visit Products → create a product → edit it → delete it.
4. Visit Uploads → drag a PDF/PNG → wait for "Completed" badge → preview → download → delete.
5. Visit Settings → change brand name → save → reload → confirm persisted.
6. Visit Users → invite a new user (with strong password) → see them in the list.
7. Open browser DevTools → Network → confirm `Authorization: Bearer …` header on API calls.
8. Wait 30 min (or shorten `ACCESS_TOKEN_EXPIRE_MINUTES`) → confirm the
   interceptor auto-refreshes without losing the user's session.

## ⏭️ Phase 2 — what's scaffolded

These folders exist with placeholder base classes and detailed docstrings
explaining what each will contain. **No AI functionality is implemented in
Phase 1.1.**

| Folder                          | Purpose |
| ------------------------------- | ------- |
| `backend/app/ai/providers/`     | LLM provider clients (OpenAI, Anthropic, Gemini, Cohere, Mistral) |
| `backend/app/ai/agents/`        | Agent orchestration (content gen, optimiser, review responder, monitor) |
| `backend/app/ai/memory/`        | Short-term + long-term agent memory |
| `backend/app/ai/prompts/`       | Versioned, parameterised prompt templates |
| `backend/app/ai/embeddings/`    | Embedding-model wrappers |
| `backend/app/rag/`              | End-to-end RAG pipeline (ingest + query) |
| `backend/app/vector/`           | Backend-agnostic vector DB interface |

When Phase 2 lands, you'll add:
- A `pgvector` migration (single Alembic revision)
- Concrete provider implementations in `app/ai/providers/`
- A `/api/v1/ai/generate` endpoint that uses `app.rag.RAGPipeline`
- New React pages for chat / content generation

The architecture is designed so that wiring AI in does **not** require
restructuring any existing code.

## 🔧 Configuration

### Backend (`backend/.env`)

| Variable                     | Default                  | Description |
| ---------------------------- | ------------------------ | ----------- |
| `DATABASE_URL`               | `postgresql+psycopg2://…`| SQLAlchemy URL |
| `REDIS_URL`                  | `redis://localhost:6379/0` | Redis connection |
| `JWT_SECRET`                 | _change me_              | JWT signing secret |
| `ACCESS_TOKEN_EXPIRE_MINUTES`| `30`                     | Access token TTL |
| `REFRESH_TOKEN_EXPIRE_DAYS`  | `7`                      | Refresh token TTL |
| `UPLOAD_PATH`                | `./uploads`              | Local upload dir |
| `MAX_UPLOAD_SIZE_MB`         | `50`                     | Max file size |
| `FRONTEND_URL`               | `http://localhost:5173`  | CORS origin |
| `OPENAI_API_KEY`             | _(empty)_                | Phase 2 — stored only |
| `CLAUDE_API_KEY`             | _(empty)_                | Phase 2 — stored only |
| `GEMINI_API_KEY`             | _(empty)_                | Phase 2 — stored only |

### Frontend (`frontend/.env`)

| Variable            | Default                              | Description |
| ------------------- | ------------------------------------ | ----------- |
| `VITE_API_BASE_URL` | `http://localhost:8000/api/v1`       | Backend API base URL |

## 📜 License

Proprietary — © NUMÉ Beauty Labs. All rights reserved.
