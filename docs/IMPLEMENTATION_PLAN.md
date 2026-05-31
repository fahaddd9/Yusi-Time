# Yusi Time — Implementation Plan
**Version:** 1.0 (Final)
**Date:** 2026-05-26
**Status:** Finalized ✅
**Aligned With:** PRD v1.3 · TRD v1.2 · DB Schema v2.1 · API Spec v1.1 · UI/UX Blueprint v2.0 · FRONTEND_SKILL.md · AGENT.md v1.1

---

## HOW TO USE THIS DOCUMENT

This plan divides the entire Yusi Time MVP into **8 phases**. Each phase
builds frontend and backend **side by side**. No phase begins until the
previous phase passes all tests.

**Reading this document:**
- Each phase has a clear scope, step-by-step implementation sequence,
  and a testing checklist.
- Each step tells you exactly what file to create, what it must contain,
  and what to verify before moving on.
- Backend steps are marked **[BE]**. Frontend steps are marked **[FE]**.
  Steps marked **[BOTH]** require coordination.

**Phase completion rule:**
A phase is ONLY complete when:
1. All backend unit + integration tests pass
2. All frontend components implement all states (loading/empty/error/data)
3. Phase testing checklist passes 100%
4. `PROJECT_STATE.md` updated with phase marked COMPLETED

**Never start Phase N+1 until Phase N is fully complete and approved.**

---

## Phase Overview

| Phase | Name | Key Deliverables | Complexity |
|-------|------|-----------------|------------|
| 0 | Setup & Infrastructure | Monorepo, DB, Docker, CI, design system | Medium |
| 1 | Authentication | Auth endpoints, JWT, Google OAuth, landing page, auth screens | High |
| 1.5 | Super Admin Backend | `is_superadmin` flag, dependency bypasses, migration | Low |
| 2 | Workspace & Members | Workspace CRUD, invite system, settings pages | High |
| 3 | Projects, Tasks, Clients & Tags | Full entity CRUD, project screens, settings | High |
| 4 | Time Tracking Core | Timer, manual entry, rounding, dashboard, timesheet grid | Very High |
| 5 | Continue, Duplicate & Draft | 2 new endpoints, Continue/Duplicate UI, draft hook | Medium |
| 6 | Approvals & Notifications | Approval workflow, notification system | High |
| 7 | Reports & Analytics | Summary, Detailed, Weekly reports, charts, export | High |
| 7.5 | Super Admin UI Dashboard | `/superadmin` Next.js dashboard, platform API endpoints | High |
| 8 | Webhooks, Polish & Deployment | Webhooks, UI polish, accessibility, AWS deploy | Medium |

---

## PHASE 0 — Project Setup & Infrastructure

**Goal:** Fully working local development environment. Backend connects to DB.
Frontend renders a blank page. CI pipelines exist. Zero functionality but the
entire technical foundation is rock-solid before any feature work begins.

---

### Step 0.1 [BOTH] — Initialize the Monorepo

Create Git repository `yusi-time` with this exact top-level structure:
```
yusi-time/
├── backend/
├── web/
├── app/              ← empty placeholder, NEVER touch during MVP
├── .github/
│   └── workflows/
│       ├── backend.yml
│       └── web.yml
├── docker-compose.yml
├── .gitignore
└── README.md
```

**`.gitignore`** must include:
```
__pycache__/
*.py[cod]
.env
*.egg-info/
.venv/
.pytest_cache/
node_modules/
.next/
.env.local
.env.*.local
.DS_Store
*.log
coverage/
```

**Verify:** `git init`, initial commit with empty structure passes.

---

### Step 0.2 [BE] — Initialize FastAPI Backend

```bash
cd backend
poetry init
poetry add fastapi==0.115.0 uvicorn==0.30.0 sqlalchemy==2.0.30 \
  asyncpg==0.29.0 alembic==1.13.0 pydantic==2.8.0 \
  pydantic-settings==2.3.0 python-jose==3.3.0 argon2-cffi==23.1.0 \
  httpx==0.27.0 slowapi==0.1.9 bleach==6.1.0 structlog==24.4.0 \
  boto3==1.34.0
poetry add --group dev pytest==8.2.0 pytest-asyncio==0.23.0 \
  pytest-mock==3.14.0 ruff==0.4.0 pytest-cov
```

Create `backend/app/main.py`:
```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Yusi Time API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health():
    return {"status": "ok", "version": "1.0.0"}
```

Create `backend/app/core/config.py` with full `Settings` class (BaseSettings)
loading all env vars from TRD v1.2 §6.2 Appendix A.

Create `backend/.env.example` with placeholder values. Copy to `.env` locally.

**Verify:**
```bash
poetry run uvicorn app.main:app --reload --port 8000
# GET http://localhost:8000/health → {"status":"ok"}
# GET http://localhost:8000/docs  → Swagger UI loads
```

---

### Step 0.3 [BE] — PostgreSQL via Docker Compose

**`docker-compose.yml`:**
```yaml
version: '3.9'
services:
  db:
    image: postgres:15-alpine
    environment:
      POSTGRES_USER: yusitime
      POSTGRES_PASSWORD: yusitime_dev
      POSTGRES_DB: yusitime
    ports: ["5432:5432"]
    volumes: [postgres_data:/var/lib/postgresql/data]
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U yusitime"]
      interval: 5s
      timeout: 5s
      retries: 5

  db_test:
    image: postgres:15-alpine
    environment:
      POSTGRES_USER: yusitime_test
      POSTGRES_PASSWORD: yusitime_test
      POSTGRES_DB: yusitime_test
    ports: ["5433:5432"]
    volumes: [postgres_test_data:/var/lib/postgresql/data]

volumes:
  postgres_data:
  postgres_test_data:
```

**`backend/.env`** (local only, never commit):
```
APP_ENV=development
DATABASE_URL=postgresql+asyncpg://yusitime:yusitime_dev@localhost:5432/yusitime
TEST_DATABASE_URL=postgresql+asyncpg://yusitime_test:yusitime_test@localhost:5433/yusitime_test
JWT_SECRET=dev-jwt-secret-change-in-production-minimum-32-chars
JWT_REFRESH_SECRET=dev-refresh-secret-different-from-above-32-chars
FRONTEND_URL=http://localhost:3000
GOOGLE_CLIENT_ID=placeholder
GOOGLE_CLIENT_SECRET=placeholder
AWS_ACCESS_KEY_ID=placeholder
AWS_SECRET_ACCESS_KEY=placeholder
AWS_SES_REGION=us-east-1
```

**Verify:** `docker-compose up -d db db_test` → both containers healthy.

---

### Step 0.4 [BE] — SQLAlchemy Async + Alembic

**`backend/app/core/database.py`:**
```python
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from app.core.config import get_settings

settings = get_settings()
engine = create_async_engine(settings.database_url, echo=False)
AsyncSessionLocal = async_sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

class Base(DeclarativeBase):
    pass

async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
```

Initialize Alembic:
```bash
cd backend
alembic init alembic
```

Edit `alembic/env.py` to use async engine and import `Base` from `app.core.database`.
Set `target_metadata = Base.metadata`.

**Verify:** `alembic revision --autogenerate -m "test"` creates file without errors.

---

### Step 0.5 [BE] — Full Initial Database Migration

Create `backend/alembic/versions/20260526_0900_initial_schema.py`.

This migration implements the **complete DDL** from DB Schema v2.0 Appendix A.
Write in this exact dependency order:

**`upgrade()` function must:**
1. Create pgcrypto extension: `CREATE EXTENSION IF NOT EXISTS "pgcrypto"`
2. Create all enums: workspace_role, project_visibility, project_status,
   entry_status, submission_status, rounding_mode, webhook_event_type,
   notification_event_type, audit_action, webhook_delivery_status
3. Create `set_updated_at` trigger function
4. Create tables in this order (respecting FK dependencies):
   `users` → `password_reset_tokens` → `workspaces` → `workspace_members`
   → `invites` → `clients` → `projects` → `project_members` → `tasks`
   → `tags` → `time_entries` → `time_entry_tags` → `timesheet_submissions`
   → `submission_entries` → `saved_report_views` → `webhooks`
   → `webhook_delivery_logs` → `notifications` → `audit_logs`
5. Create all indexes from DB Schema §6
6. Apply all triggers from DB Schema §7

**`downgrade()` function must:** Drop all tables, indexes, triggers, and enums
in reverse dependency order.

**Next, create the v2.1 update migration:**
Create `backend/alembic/versions/20260526_1000_add_weekly_report_type.py`.
This migration must update the `saved_report_views.report_type` CHECK constraint to include `'weekly'` per DB Schema Changelog v2.1 §11.

**Verify:**
```bash
alembic upgrade head    # All 19 tables created, no errors
alembic downgrade base  # All tables dropped cleanly
alembic upgrade head    # Re-applies cleanly — proves downgrade/upgrade are symmetric
```

---

### Step 0.6 [BE] — Structured Logging + Global Error Handling

**`backend/app/core/logging.py`:**
Configure structlog with JSON output. Create `RequestLoggingMiddleware`
that injects `request_id` UUID into every request. Add `X-Request-ID`
response header.

**`backend/app/core/exceptions.py`:**
Create global exception handler that:
- Catches all `HTTPException` → returns `{"detail": "...", "code": "..."}`
- Catches unhandled exceptions → logs full traceback at ERROR, returns
  `{"detail": "Internal server error", "code": "INTERNAL_ERROR"}` with 500

Register both in `main.py`.

**Verify:** Hit an invalid endpoint → response is `{"detail":"Not Found","code":"NOT_FOUND"}`.

---

### Step 0.7 [FE] — Initialize Next.js Frontend

```bash
cd web
pnpm create next-app@14.2.0 . --typescript --tailwind --eslint --app \
  --src-dir --import-alias "@/*"

pnpm add @tanstack/react-query@5.40.0 zustand@4.5.0 \
  react-hook-form@7.51.0 zod@3.23.0 @hookform/resolvers@3.4.0 \
  axios@1.7.0 framer-motion@11.0.0 next-themes@0.3.0 \
  sonner@1.5.0 lucide-react@0.383.0 \
  class-variance-authority@0.7.0 clsx@2.1.0 tailwind-merge@2.3.0 \
  tailwindcss-animate@1.0.7

# shadcn/ui init
pnpm dlx shadcn-ui@latest init
# Settings: TypeScript, Default style, CSS variables: yes

# Add all required shadcn components
pnpm dlx shadcn-ui@latest add button input label textarea select \
  dialog alert-dialog sheet tabs switch table badge avatar progress \
  popover dropdown-menu tooltip command separator skeleton card \
  scroll-area
```

Ensure `web/tsconfig.json` has `"strict": true`.

**Verify:** `pnpm dev` → blank Next.js page loads at `http://localhost:3000`. Zero TypeScript errors.

---

### Step 0.8 [FE] — Design System Foundation

**`web/src/styles/globals.css`:**
Apply the complete CSS variable system from Blueprint v2.0 Part 0 — both
`:root` light theme and `.dark` dark theme with ALL tokens including:
brand-navy (#1E2D4B), brand-orange (#F06900), all semantic colors,
sidebar tokens, status tokens, text hierarchy, and border tokens.

**`web/tailwind.config.ts`:**
Apply complete config from FRONTEND_SKILL.md §1.4 with these brand additions:
```typescript
darkMode: ['class'],
theme: {
  extend: {
    fontFamily: {
      sans: ['DM Sans', 'system-ui', 'sans-serif'],
      mono: ['DM Mono', 'ui-monospace', 'monospace'],
    },
    colors: {
      brand: {
        navy: '#1E2D4B',
        'navy-light': '#EEF1F7',
        orange: '#F06900',
        'orange-hover': '#D95E00',
        'orange-light': '#FFF0E6',
      },
      // ... all CSS variable token mappings
    },
  },
},
plugins: [require('tailwindcss-animate')],
```

**`web/src/lib/utils.ts`:**
```typescript
import { type ClassValue, clsx } from 'clsx'
import { twMerge } from 'tailwind-merge'

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export function formatDuration(seconds: number): string {
  const h = Math.floor(seconds / 3600)
  const m = Math.floor((seconds % 3600) / 60)
  if (h === 0) return `${m}m`
  return `${h}h ${m}m`
}

export function formatMoney(cents: number | null | undefined): string {
  if (cents == null) return '—'
  return `$${(cents / 100).toFixed(2)}`
}

export function descriptionDraftKey(userId: string, workspaceId: string): string {
  return `yt_desc_draft_${userId}_${workspaceId}`
}
```

**`web/src/app/layout.tsx`:**
```tsx
import type { Metadata } from 'next'
import { DM_Sans, DM_Mono } from 'next/font/google'
import { ThemeProvider } from '@/components/ThemeProvider'
import { QueryClientWrapper } from '@/components/QueryClientWrapper'
import { Toaster } from 'sonner'
import { MotionConfig } from 'framer-motion'
import './globals.css'

const dmSans = DM_Sans({ subsets: ['latin'], variable: '--font-sans' })
const dmMono = DM_Mono({
  subsets: ['latin'],
  weight: ['400', '500', '700'],
  variable: '--font-mono',
})

export const metadata: Metadata = {
  title: 'Yusi Time — Smart Time Tracking',
  description: 'Track time, manage approvals, and get paid faster.',
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className={`${dmSans.variable} ${dmMono.variable} font-sans antialiased`}>
        <ThemeProvider
          attribute="class"
          defaultTheme="system"
          enableSystem
          disableTransitionOnChange
        >
          <QueryClientWrapper>
            <MotionConfig reducedMotion="user">
              {children}
              <Toaster position="bottom-right" richColors />
            </MotionConfig>
          </QueryClientWrapper>
        </ThemeProvider>
      </body>
    </html>
  )
}
```

Note: `QueryClientWrapper` is a `'use client'` component wrapping
`<QueryClientProvider client={queryClient}>`. This keeps the root layout
as a Server Component.

**Verify:** Light/dark toggle works. DM Sans and DM Mono fonts load.
No TypeScript errors on `pnpm tsc --noEmit`.

---

### Step 0.9 [FE] — API Client + Token Store

**`web/src/lib/token-store.ts`:**
```typescript
// Module-level variable — NEVER localStorage, NEVER sessionStorage
let accessToken: string | null = null

export const tokenStore = {
  getAccessToken: () => accessToken,
  setAccessToken: (token: string) => { accessToken = token },
  clearAccessToken: () => { accessToken = null },
}
```

**`web/src/lib/api-client.ts`:**
```typescript
import axios from 'axios'
import { tokenStore } from './token-store'

export const apiClient = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL,
  withCredentials: true, // required for HttpOnly refresh cookie
})

// Attach access token from memory to every request
apiClient.interceptors.request.use((config) => {
  const token = tokenStore.getAccessToken()
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

// Silent refresh on 401 → redirect to /login on failure
apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response?.status === 401 && !error.config._retry) {
      error.config._retry = true
      try {
        const { data } = await apiClient.post('/auth/refresh')
        tokenStore.setAccessToken(data.access_token)
        error.config.headers.Authorization = `Bearer ${data.access_token}`
        return apiClient(error.config)
      } catch {
        tokenStore.clearAccessToken()
        if (typeof window !== 'undefined') {
          window.location.href = '/login'
        }
      }
    }
    return Promise.reject(error)
  }
)
```

**Verify:** Import without errors. Token store is module-scoped (not persisted).

---

### Step 0.10 [BOTH] — GitHub Actions CI Pipelines

**`.github/workflows/backend.yml`:**
On push: install deps → ruff lint → alembic upgrade head → pytest with coverage ≥ 80%.

**`.github/workflows/web.yml`:**
On push: pnpm install → eslint → `tsc --noEmit` → `pnpm build`.

**Verify:** Push to a test branch → both pipelines run green.

---

### Step 0.11 [BE] — Test Infrastructure

**`backend/tests/conftest.py`:**
```python
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from app.main import app
from app.core.database import Base, get_db
from app.core.config import get_settings

settings = get_settings()

@pytest_asyncio.fixture
async def async_client():
    engine = create_async_engine(settings.test_database_url)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    async def override_get_db():
        async with session_factory() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()
```

Create empty scaffold files for all services, routers, and models per TRD v1.2 §6.1
with correct imports and `# TODO: implement` comments. This prevents import errors
in later phases when other modules reference them.

**Verify:** `pytest tests/ --collect-only` → zero import errors.

---

### Phase 0 — Testing Checklist

```
[ ] docker-compose up starts both db and db_test without errors
[ ] alembic upgrade head creates all 19 tables with correct structure
[ ] alembic downgrade base drops all tables cleanly
[ ] alembic upgrade head re-applies cleanly (symmetric test)
[ ] GET /health returns {"status":"ok","version":"1.0.0"}
[ ] GET /docs loads Swagger UI without errors
[ ] pnpm dev loads Next.js page at localhost:3000
[ ] Light/dark theme toggle works on blank page
[ ] DM Sans loads as UI font (verify in browser DevTools → Network → Fonts)
[ ] DM Mono loads as mono font (same check)
[ ] pnpm tsc --noEmit passes with zero errors
[ ] pnpm lint passes with zero warnings
[ ] pnpm build completes without errors
[ ] backend.yml CI pipeline green on test push
[ ] web.yml CI pipeline green on test push
[ ] pytest --collect-only shows no import errors
[ ] brand-orange color (#F06900) visible in browser color picker (test element)
[ ] brand-navy (#1E2D4B) applied correctly on test element
```

---

## PHASE 1 — Authentication

**Goal:** Users can sign up (email/password + Google OAuth), log in, reset
passwords, and accept invite links. JWT tokens work. The landing page is live.
All auth screens are implemented and visually complete.

---

### Step 1.1 [BE] — User + Workspace + WorkspaceMember Models

**`backend/app/models/user.py`:** `User` model per DB Schema §4.1.
All columns, UNIQUE constraints (email functional lowercase index, google_id).

**`backend/app/models/workspace.py`:** `Workspace` model per DB Schema §4.3.
All columns including all CHECK constraints (rounding, idle timeout).

**`backend/app/models/workspace_member.py`:** `WorkspaceMember` model per DB Schema §4.4.
Composite PK (workspace_id, user_id).

**`backend/app/models/password_reset_token.py`:** `PasswordResetToken` model per DB Schema §4.2.

**Verify:** All models import cleanly. `alembic check` shows no pending migrations.

---

### Step 1.2 [BE] — Security Utilities

**`backend/app/core/security.py`:**

```python
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError, VerificationError
from jose import jwt, JWTError
from datetime import datetime, timedelta, timezone
import secrets
from fastapi import HTTPException

ph = PasswordHasher()

def hash_password(plain: str) -> str:
    return ph.hash(plain)

def verify_password(plain: str, hashed: str) -> bool:
    try:
        return ph.verify(hashed, plain)
    except (VerifyMismatchError, VerificationError):
        return False

def create_access_token(user_id: str, settings) -> str:
    payload = {
        "sub": user_id,
        "type": "access",
        "iat": datetime.now(timezone.utc),
        "exp": datetime.now(timezone.utc) + timedelta(minutes=settings.access_token_expire_minutes),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm="HS256")

def create_refresh_token(user_id: str, settings) -> str:
    payload = {
        "sub": user_id,
        "type": "refresh",
        "iat": datetime.now(timezone.utc),
        "exp": datetime.now(timezone.utc) + timedelta(days=settings.refresh_token_expire_days),
    }
    return jwt.encode(payload, settings.jwt_refresh_secret, algorithm="HS256")

def verify_access_token(token: str, jwt_secret: str) -> dict:
    try:
        payload = jwt.decode(token, jwt_secret, algorithms=["HS256"])
        if payload.get("type") != "access":
            raise HTTPException(401, detail="Invalid token type", headers={"code": "UNAUTHENTICATED"})
        return payload
    except JWTError as e:
        if "expired" in str(e).lower():
            raise HTTPException(401, detail="Token expired", headers={"code": "TOKEN_EXPIRED"})
        raise HTTPException(401, detail="Invalid token", headers={"code": "UNAUTHENTICATED"})

def generate_secure_token() -> str:
    return secrets.token_urlsafe(32)
```

**Unit tests (`tests/unit/test_security.py`):**
- `hash_password` + `verify_password` round-trip works
- Wrong password returns False (no exception)
- `create_access_token` + `verify_access_token` round-trip
- Expired token raises 401 TOKEN_EXPIRED
- Wrong secret raises 401 UNAUTHENTICATED

---

### Step 1.3 [BE] — FastAPI Dependencies

**`backend/app/core/dependencies.py`:**

```python
from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.core.security import verify_access_token
from app.core.config import get_settings
from app.models.user import User
from app.models.workspace_member import WorkspaceMember
from uuid import UUID

settings = get_settings()
bearer_scheme = HTTPBearer(auto_error=False)

async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    if not credentials:
        raise HTTPException(401, detail="Not authenticated", headers={"code": "UNAUTHENTICATED"})
    payload = verify_access_token(credentials.credentials, settings.jwt_secret)
    user = await db.get(User, UUID(payload["sub"]))
    if not user or not user.is_active:
        raise HTTPException(401, detail="User not found", headers={"code": "UNAUTHENTICATED"})
    return user

async def get_workspace_member(
    workspace_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> WorkspaceMember:
    result = await db.execute(
        select(WorkspaceMember).where(
            WorkspaceMember.workspace_id == workspace_id,
            WorkspaceMember.user_id == current_user.id,
        )
    )
    member = result.scalar_one_or_none()
    if not member:
        raise HTTPException(404, detail="Workspace not found", headers={"code": "NOT_FOUND"})
    return member

def require_role(*roles: str):
    async def _require_role(
        member: WorkspaceMember = Depends(get_workspace_member),
    ) -> WorkspaceMember:
        if member.role not in roles:
            raise HTTPException(403, detail="Insufficient permissions", headers={"code": "FORBIDDEN"})
        return member
    return _require_role
```

---

### Step 1.4 [BE] — Auth Pydantic Schemas

**`backend/app/schemas/auth.py`** — full request/response models:
SignupRequest (with validators for password length and name), LoginRequest,
SignupResponse, LoginResponse, ForgotPasswordRequest, ResetPasswordRequest,
RefreshResponse.

**`backend/app/schemas/user.py`** — UserPublic model with `from_attributes=True`.

**`backend/app/schemas/workspace.py`** — WorkspaceSummary model (id, name, logo_url, created_at).

---

### Step 1.5 [BE] — Email Utility

**`backend/app/utils/email.py`:**
```python
import structlog
from app.core.config import get_settings

logger = structlog.get_logger()
settings = get_settings()

async def send_reset_email(to_email: str, token: str) -> None:
    reset_url = f"{settings.frontend_url}/reset-password?token={token}"
    if settings.app_env == "development":
        logger.info("PASSWORD_RESET_LINK", email=to_email, url=reset_url)
        print(f"\n🔗 PASSWORD RESET LINK: {reset_url}\n")
        return
    # Production: AWS SES
    import boto3
    ses = boto3.client("ses", region_name=settings.aws_ses_region)
    ses.send_email(
        Source="noreply@yusitime.com",
        Destination={"ToAddresses": [to_email]},
        Message={
            "Subject": {"Data": "Reset your Yusi Time password"},
            "Body": {"Text": {"Data": f"Click to reset your password:\n{reset_url}\n\nExpires in 1 hour."}},
        },
    )
```

---

### Step 1.6 [BE] — Auth Service

**`backend/app/services/auth_service.py`:**

Implement all 5 functions with full business logic per TRD v1.2 §6.6:

`register(db, email, password, full_name)`:
1. `SELECT` user by `LOWER(email)`. Raise `409 EMAIL_ALREADY_EXISTS` if exists.
2. `hash_password(password)`.
3. Create `User` record (email stored as-is, looked up case-insensitively).
4. Create `Workspace(name=f"{full_name}'s Workspace")`.
5. Create `WorkspaceMember(role='admin')` linking user and workspace.
6. `await db.flush()` (get IDs before commit).
7. Create and return `access_token` + `refresh_token`.

`login(db, email, password)`:
1. Fetch user by `LOWER(email)`. Raise `401 INVALID_CREDENTIALS` if not found.
2. `verify_password(password, user.password_hash)`. Raise `401` if False.
3. Check `user.is_active`. Raise `401` if False.
4. Return tokens.

`refresh_tokens(db, refresh_token_str)`:
1. Decode refresh token using `jwt_refresh_secret`. Raise `401` on failure.
2. Verify `payload["type"] == "refresh"`.
3. Fetch user. Return new access token.

`initiate_password_reset(db, email)`:
1. Fetch user by email. If not found: **return silently** (no error — prevents enumeration).
2. Delete all prior `PasswordResetToken` rows for this user.
3. Generate token via `generate_secure_token()`.
4. Create `PasswordResetToken(expires_at=now()+1h)`.
5. `await email.send_reset_email(email, token)`.

`reset_password(db, token, new_password)`:
1. Fetch `PasswordResetToken` by token value.
2. If not found, already `used=True`, or `expires_at <= now()`: raise `400 BAD_REQUEST`.
3. Update `user.password_hash = hash_password(new_password)`.
4. Set `token.used = True`.
5. Return success message.

---

### Step 1.7 [BE] — Auth Router

**`backend/app/routers/auth.py`:**
Implement all 8 endpoints from API Spec v1.1 §3.

Cookie settings for refresh token (apply in login + signup + refresh):
```python
response.set_cookie(
    key="refresh_token",
    value=refresh_token,
    httponly=True,
    secure=settings.app_env != "development",
    samesite="strict",
    max_age=60 * 60 * 24 * 7,  # 7 days in seconds
    path="/api/v1/auth/refresh",
)
```

Cookie clearing for logout:
```python
response.delete_cookie(key="refresh_token", path="/api/v1/auth/refresh")
```

Apply `slowapi` Limiter to: `/auth/login`, `/auth/signup`, `/auth/forgot-password`
at 10 requests/minute per IP.

Register in `main.py`: `app.include_router(auth_router, prefix="/api/v1")`

**Google OAuth implementation:**
- `GET /auth/google` → build Google OAuth URL and return `RedirectResponse`
- `GET /auth/google/callback` → exchange code for profile, create/login user,
  redirect to frontend with access token in URL param, set refresh cookie

---

### Step 1.8 [BE] — Auth Tests

**`backend/tests/unit/test_auth_service.py`:**
```python
# Every function with mocked DB session:
async def test_register_creates_user_workspace_member(mock_db): ...
async def test_register_duplicate_email_raises_409(mock_db): ...
async def test_login_wrong_password_raises_401(mock_db): ...
async def test_login_inactive_user_raises_401(mock_db): ...
async def test_reset_used_token_raises_400(mock_db): ...
async def test_reset_expired_token_raises_400(mock_db): ...
async def test_initiate_reset_nonexistent_email_returns_silently(mock_db): ...
```

**`backend/tests/integration/test_auth.py`:**
```python
# Full HTTP flows using async_client fixture:
async def test_signup_returns_201_with_access_token(async_client): ...
async def test_signup_duplicate_email_returns_409(async_client): ...
async def test_signup_short_password_returns_422(async_client): ...
async def test_login_success_sets_cookie(async_client): ...
async def test_login_wrong_password_returns_401(async_client): ...
async def test_refresh_with_cookie_returns_new_token(async_client): ...
async def test_refresh_without_cookie_returns_401(async_client): ...
async def test_logout_clears_cookie(async_client): ...
async def test_forgot_password_nonexistent_returns_200(async_client): ...
async def test_reset_password_expired_token_returns_400(async_client): ...
```

**Verify:** `pytest tests/ -v --cov=app --cov-fail-under=80` passes.

---

### Step 1.9 [FE] — Auth Layout + ThemeProvider + ThemeToggle

**`web/src/components/ThemeProvider.tsx`** — next-themes wrapper (Phase 0 already done).

**`web/src/components/ThemeToggle.tsx`:**
```tsx
'use client'
import { useTheme } from 'next-themes'
import { Sun, Moon, Monitor } from 'lucide-react'
import { Button } from '@/components/ui/button'
import {
  DropdownMenu, DropdownMenuContent,
  DropdownMenuItem, DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'

export function ThemeToggle({ className }: { className?: string }) {
  const { setTheme } = useTheme()
  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button variant="ghost" size="icon" className={cn("h-8 w-8", className)} aria-label="Toggle theme">
          <Sun className="w-4 h-4 rotate-0 scale-100 transition-all dark:-rotate-90 dark:scale-0" />
          <Moon className="absolute w-4 h-4 rotate-90 scale-0 transition-all dark:rotate-0 dark:scale-100" />
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end">
        <DropdownMenuItem onClick={() => setTheme('light')}>
          <Sun className="w-4 h-4 mr-2" />Light
        </DropdownMenuItem>
        <DropdownMenuItem onClick={() => setTheme('dark')}>
          <Moon className="w-4 h-4 mr-2" />Dark
        </DropdownMenuItem>
        <DropdownMenuItem onClick={() => setTheme('system')}>
          <Monitor className="w-4 h-4 mr-2" />System
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  )
}
```

**`web/src/app/(auth)/layout.tsx`:**
```tsx
export default function AuthLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-screen bg-background flex items-center justify-center p-4 relative overflow-hidden">
      {/* Dot grid background */}
      <div
        className="absolute inset-0 opacity-[0.025]"
        style={{
          backgroundImage: 'radial-gradient(circle, hsl(var(--foreground)) 1px, transparent 1px)',
          backgroundSize: '24px 24px',
        }}
      />
      {/* Orange glow blob */}
      <div className="absolute top-0 right-0 w-[400px] h-[400px] rounded-full
                      bg-brand-orange/5 blur-[80px] pointer-events-none" />
      <div className="absolute top-4 right-4">
        <ThemeToggle />
      </div>
      <div className="relative z-10 w-full max-w-[420px]">{children}</div>
    </div>
  )
}
```

---

### Step 1.10 [FE] — Landing Page

**`web/src/app/page.tsx`** — redirects authenticated users to /dashboard,
shows LandingPage for unauthenticated users.

**`web/src/features/landing/`** — create all 9 components from Blueprint v2.0 Part 1:

`LandingNav.tsx` — sticky nav. On scroll >80px: `bg-background/95 backdrop-blur-md border-b`.
Logo: YT mark (orange rounded-xl) + "Yusi" (navy/foreground) + "Time" (brand-orange).
CTAs: "Sign in" ghost + "Start Free" bg-brand-orange button + ThemeToggle.

`HeroSection.tsx` — navy background (`bg-brand-navy`), dot grid overlay,
orange glow blob, split layout. Left: eyebrow badge (orange), 3-line headline
(white, white, brand-orange), subheadline, CTAs with orange glow shadow.
Right: app preview card with browser chrome and mini dashboard render.
Framer Motion float animation.

`SocialProofStrip.tsx` — stats with animated counter (Framer Motion useMotionValue
+ useTransform, triggered by `useInView`).

`FeaturesSection.tsx` — 6 feature cards. Orange icon containers.
Stagger animation on scroll into view.

`TimerDemoSection.tsx` — interactive client-side demo with no API calls.
Start button → timer counts up → Stop → shows entry row.

`ComparisonSection.tsx` — table comparing Yusi Time vs Clockify vs Generic.
Orange checkmarks for Yusi Time wins.

`FinalCTA.tsx` — navy section, orange glow, large orange CTA button.

`LandingFooter.tsx` — navy bg, links, ThemeToggle.

**Verify:** Landing page renders fully in light + dark mode. All animations play.
CTAs navigate correctly.

---

### Step 1.11 [FE] — Auth API Layer

**`web/src/features/auth/api.ts`:**
```typescript
import { apiClient } from '@/lib/api-client'

export const authApi = {
  signup: (data: { email: string; password: string; full_name: string }) =>
    apiClient.post('/auth/signup', data),
  login: (data: { email: string; password: string }) =>
    apiClient.post('/auth/login', data),
  refresh: () => apiClient.post('/auth/refresh'),
  logout: () => apiClient.post('/auth/logout'),
  forgotPassword: (email: string) =>
    apiClient.post('/auth/forgot-password', { email }),
  resetPassword: (token: string, new_password: string) =>
    apiClient.post('/auth/reset-password', { token, new_password }),
}
```

**`web/src/features/auth/schemas.ts`:**
```typescript
import { z } from 'zod'

export const loginSchema = z.object({
  email: z.string().email('Enter a valid email address'),
  password: z.string().min(1, 'Password is required'),
})

export const signupSchema = z.object({
  full_name: z.string().min(1, 'Name is required').max(100).trim(),
  email: z.string().email('Enter a valid email address').max(254),
  password: z.string().min(8, 'Minimum 8 characters'),
})

export const forgotPasswordSchema = z.object({
  email: z.string().email('Enter a valid email address'),
})

export const resetPasswordSchema = z.object({
  new_password: z.string().min(8, 'Minimum 8 characters'),
  confirm_password: z.string(),
}).refine(d => d.new_password === d.confirm_password, {
  message: "Passwords don't match",
  path: ['confirm_password'],
})

export type LoginInput = z.infer<typeof loginSchema>
export type SignupInput = z.infer<typeof signupSchema>
export type ForgotPasswordInput = z.infer<typeof forgotPasswordSchema>
export type ResetPasswordInput = z.infer<typeof resetPasswordSchema>
```

**`web/src/features/auth/hooks/`** — create all mutation hooks:
`useLogin`, `useSignup`, `useForgotPassword`, `useResetPassword`, `useLogout`.

Each hook calls the corresponding API function, handles success (token store +
redirect) and error (form.setError for 422, toast for 500).

---

### Step 1.12 [FE] — All Auth Screens

Implement all 5 screens exactly per Blueprint v2.0 Part 2.

Every screen must have:
- React Hook Form + Zod resolver (schemas from Step 1.11)
- Loading state: button shows `<Loader2 className="w-4 h-4 animate-spin mr-2" />` + disabled
- Error state: server errors mapped to form fields or displayed in amber alert banner
- Success state: redirect or success message with animation
- Both light and dark theme tested

**`web/src/app/(auth)/login/page.tsx`** — per Blueprint A1 Steps 1–7.
Card with logo, headings, Google OAuth button, divider, email+password form,
forgot password link, sign up link.

**`web/src/app/(auth)/signup/page.tsx`** — per Blueprint A2.
Same card with name+email+password, password strength bar, terms note.

**`web/src/app/(auth)/forgot-password/page.tsx`** — per Blueprint A3.
Email form → success state with CheckCircle2 animation.

**`web/src/app/(auth)/reset-password/page.tsx`** — per Blueprint A4.
Reads `?token=` param. Valid: two password inputs. Invalid/expired: error card.

**`web/src/app/join/[token]/page.tsx`** — per Blueprint A5.
Calls `GET /invites/{token}`. Shows workspace + role + join CTA.
Three error states: expired, used, revoked.

---

### Step 1.13 [FE] — Next.js Middleware + Token Refresh

**`web/src/middleware.ts`:**
```typescript
import { NextResponse } from 'next/server'
import type { NextRequest } from 'next/server'

const protectedPrefixes = ['/dashboard', '/timesheet', '/projects',
                            '/reports', '/approvals', '/settings']

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl
  const isProtected = protectedPrefixes.some(p => pathname.startsWith(p))
  const hasRefreshCookie = request.cookies.has('refresh_token')

  if (isProtected && !hasRefreshCookie) {
    const loginUrl = new URL('/login', request.url)
    loginUrl.searchParams.set('redirect', pathname)
    return NextResponse.redirect(loginUrl)
  }

  return NextResponse.next()
}

export const config = {
  matcher: ['/((?!api|_next/static|_next/image|favicon.ico|join).*)'],
}
```

**`web/src/app/(app)/layout.tsx`** (minimal — completed fully in Phase 4):
```tsx
'use client'
import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { tokenStore } from '@/lib/token-store'
import { authApi } from '@/features/auth/api'

export default function AppLayout({ children }: { children: React.ReactNode }) {
  const router = useRouter()
  const [isReady, setIsReady] = useState(false)

  useEffect(() => {
    const init = async () => {
      if (!tokenStore.getAccessToken()) {
        try {
          const res = await authApi.refresh()
          tokenStore.setAccessToken(res.data.access_token)
        } catch {
          router.push('/login')
          return
        }
      }
      setIsReady(true)
    }
    init()
  }, [router])

  if (!isReady) {
    return <div className="min-h-screen bg-background animate-pulse" />
  }

  return <main className="min-h-screen bg-background p-6">{children}</main>
}
```

---

### Phase 1 — Testing Checklist

```
BACKEND:
[ ] POST /auth/signup valid → 201 + user + workspace + access_token + cookie
[ ] POST /auth/signup duplicate email → 409 EMAIL_ALREADY_EXISTS
[ ] POST /auth/signup password < 8 chars → 422 VALIDATION_ERROR
[ ] POST /auth/signup creates user AND default workspace AND admin membership
[ ] POST /auth/login correct → 200 + access_token + HttpOnly refresh cookie
[ ] POST /auth/login wrong password → 401 INVALID_CREDENTIALS
[ ] POST /auth/login inactive user → 401 INVALID_CREDENTIALS
[ ] POST /auth/refresh valid cookie → 200 + new access_token
[ ] POST /auth/refresh no cookie → 401 UNAUTHENTICATED
[ ] POST /auth/logout → 200 + cookie cleared (Max-Age=0)
[ ] POST /auth/forgot-password any email → always 200
[ ] POST /auth/forgot-password dev mode → reset link printed to stdout
[ ] POST /auth/reset-password valid token → 200 password updated
[ ] POST /auth/reset-password expired token → 400 BAD_REQUEST
[ ] POST /auth/reset-password used token → 400 BAD_REQUEST
[ ] All error responses use format {"detail":"...","code":"..."}
[ ] Rate limit: 11th login in 1 minute → 429 Too Many Requests
[ ] pytest coverage ≥ 80% on auth service

FRONTEND:
[ ] Landing page hero section renders fully
[ ] Landing page all sections visible and correct
[ ] Orange CTAs use brand-orange (#F06900)
[ ] Navy sections use brand-navy (#1E2D4B)
[ ] Landing page light mode looks correct
[ ] Landing page dark mode looks correct
[ ] Scroll animations play correctly
[ ] "Start Tracking Free" → /signup
[ ] "Sign in" → /login
[ ] Login: email format validation shows inline error
[ ] Login: spinner shows during submit
[ ] Login: wrong credentials shows error message
[ ] Login: success sets token + redirects to /dashboard
[ ] Signup: all fields validate correctly
[ ] Signup: password strength bar shows 3 levels
[ ] Signup: success redirects to /dashboard
[ ] Forgot password: success shows CheckCircle2 state with animation
[ ] Reset password: expired token shows error card with "Request new link" CTA
[ ] Invite page: valid token shows workspace name + role
[ ] Invite page: expired token shows expiry error
[ ] Invite page: used token shows used error
[ ] ThemeToggle switches light/dark on all auth pages
[ ] Tab/keyboard navigation works on all forms
[ ] All focus rings visible in orange color
[ ] Middleware: visiting /dashboard without cookie redirects to /login
```

---

---

## PHASE 1.5 — Super Admin Backend (API-Only)

**Goal:** Add the `is_superadmin` boolean to the `users` table and implement
the three dependency changes in `dependencies.py` that give Super Admin users
unconditional platform-level access. No frontend work. No new routers. The
`get_superadmin_user` dependency is added now to establish the pattern cleanly
for the post-Phase 2 UI phase.

**Dependencies:** Phase 1 complete.
**Prerequisite reading:** DB Schema v2.2 Changelog §12, TRD v1.3 §6.5.

---

### Step 1.5.1 [BE] — Add `is_superadmin` to User Model

**File:** `backend/app/models/user.py`

Find the `is_active` column definition:
```python
is_active = Column(Boolean, nullable=False, default=True)
```

Add directly after:
```python
is_superadmin = Column(Boolean, nullable=False, default=False)
```

**Verify:** Python import of `User` model succeeds with no errors.

---

### Step 1.5.2 [BE] — Add `is_superadmin` to UserPublic Schema

**File:** `backend/app/schemas/user.py`

Find the `UserPublic` class and add `is_superadmin: bool` after
`weekly_hours_goal`:

```python
weekly_hours_goal: int | None
is_superadmin: bool
created_at: datetime
```

**Verify:** `UserPublic.model_fields` contains `is_superadmin`.

---

### Step 1.5.3 [BE] — Update Dependencies

**File:** `backend/app/core/dependencies.py`

Three changes in this file:

**A) Modify `get_workspace_member()`** — add synthetic member bypass for
Super Admin before the DB query. Full implementation in DB Schema v2.2
Changelog §12 Application Layer section.

**B) Modify `require_role()`** — inject `current_user` as second dependency
parameter and add unconditional Super Admin bypass before the role check.
Full implementation in DB Schema v2.2 Changelog §12 Application Layer section.

**C) Add `get_superadmin_user()`** — new dependency function that wraps
`get_current_user` and raises `403 FORBIDDEN` if `is_superadmin is False`.
Full implementation in DB Schema v2.2 Changelog §12 Application Layer section.

**Verify:** All three functions import cleanly. Existing tests still pass.

---

### Step 1.5.4 [BE] — Generate and Apply Migration

```bash
cd backend
alembic revision --autogenerate -m "add_is_superadmin_to_users"
```

Review the generated file. Confirm:
- `upgrade()` adds: `is_superadmin BOOLEAN NOT NULL DEFAULT FALSE`
- `downgrade()` drops the column cleanly

```bash
alembic upgrade head
```

---

### Step 1.5.5 [BE] — Seed Super Admin Account

```sql
UPDATE users SET is_superadmin = TRUE WHERE email = 'your-founder-email@example.com';
```

Run directly against your database. Confirm with:
```sql
SELECT email, is_superadmin FROM users WHERE is_superadmin = TRUE;
```

---

### Step 1.5.6 [BE] — Write Tests

**File:** `backend/tests/unit/test_superadmin.py`

```python
# Required test cases — all must pass:

async def test_get_workspace_member_superadmin_returns_synthetic_admin_role(): ...
async def test_get_workspace_member_superadmin_does_not_query_workspace_members(): ...
async def test_require_role_superadmin_bypasses_admin_check(): ...
async def test_require_role_superadmin_bypasses_member_check(): ...
async def test_require_role_superadmin_bypasses_viewer_check(): ...
async def test_require_role_normal_user_still_enforced(): ...
async def test_get_superadmin_user_returns_user_when_flag_true(): ...
async def test_get_superadmin_user_raises_403_when_flag_false(): ...
async def test_register_new_user_always_has_superadmin_false(): ...
async def test_google_oauth_new_user_always_has_superadmin_false(): ...
```

**File:** `backend/tests/integration/test_superadmin.py`

```python
async def test_superadmin_accesses_workspace_without_membership_200(async_client): ...
async def test_superadmin_accesses_admin_only_endpoint_without_admin_role_200(async_client): ...
async def test_normal_user_calls_admin_endpoint_gets_403(async_client): ...
async def test_superadmin_response_includes_is_superadmin_true(async_client): ...
async def test_normal_user_response_includes_is_superadmin_false(async_client): ...
```

---

### Phase 1.5 — Testing Checklist
[ ] alembic upgrade head applies cleanly — is_superadmin column exists in users table
[ ] alembic downgrade reverses cleanly
[ ] GET /users/me response includes is_superadmin: true for seeded founder account
[ ] GET /users/me response includes is_superadmin: false for normal user
[ ] Super Admin user calls GET /workspaces/{id} with no membership → 200
[ ] Super Admin user calls endpoint requiring admin role with member role → 200
[ ] Normal user calls GET /admin/* → 403 FORBIDDEN (when admin router exists)
[ ] Newly registered user via POST /auth/signup → is_superadmin: false
[ ] is_superadmin field absent from SignupRequest schema (cannot be set via API)
[ ] pytest tests/unit/test_superadmin.py — all 10 cases pass
[ ] pytest tests/integration/test_superadmin.py — all 5 cases pass
[ ] pytest tests/ -v --cov=app --cov-fail-under=80 — overall coverage maintained
[ ] ruff check app/ — zero warnings

---

## PHASE 2 — Workspace & Member Management

**Goal:** Admins manage workspace settings and invite members. Invite link flow
works end-to-end. Members/Invite settings pages are fully functional.

---

### Step 2.1 [BE] — Remaining Phase 2 Models

**`backend/app/models/invite.py`:** `Invite` model per DB Schema §4.5.
All CHECK constraints: expires_at > created_at, used/used_at consistency,
revoked/revoked_at consistency, not both used and revoked, role != admin.

**`backend/app/models/audit_log.py`:** `AuditLog` model per DB Schema §4.19.
Append-only — service layer writes to it; no UPDATE/DELETE ever issued.

**`backend/app/models/notification.py`:** `Notification` model per DB Schema §4.18.

---

### Step 2.2 [BE] — Workspace Schemas (Full)

Extend `backend/app/schemas/workspace.py` with:
- `WorkspaceDetail` — full settings including financial fields
- `WorkspaceDetailViewer` — same but without `default_hourly_rate` and `currency`
- `WorkspaceUpdate` — all optional fields with `@model_validator` validating
  rounding_mode/interval and idle_detection/timeout consistency
- `WorkspaceListItem` — for the list endpoint (id, name, logo_url, role, member_count)

---

### Step 2.3 [BE] — Workspace Service + Router

**`backend/app/services/workspace_service.py`:**

`get_workspace(db, workspace_id, current_user)`:
- Fetch workspace; verify not soft-deleted (`deleted_at IS NULL`)
- Return `WorkspaceDetail` or `WorkspaceDetailViewer` based on caller role

`update_workspace(db, workspace_id, data, admin_user)`:
- Require Admin role
- If `approval_workflow_enabled` changed from True → False:
  call `approval_service.handle_workflow_disabled(db, workspace_id)`
- Update fields, return updated workspace

`soft_delete_workspace(db, workspace_id, admin_user)`:
- Require Admin role
- Set `workspace.deleted_at = now()`
- Call `notification_service.create_for_role(workspace_id, all_roles, 'workspace_deleted', ...)`
- Log to audit_logs (action=workspace_soft_deleted)

`get_user_workspaces(db, user_id)`:
- Join workspaces + workspace_members filtered by user_id
- Excludes soft-deleted workspaces

**`backend/app/routers/workspaces.py`:** 5 workspace endpoints per API Spec v1.1 §5.

---

### Step 2.4 [BE] — Member Service + Router

**`backend/app/services/member_service.py`:**

`list_members(db, workspace_id, page, per_page)`:
- Join workspace_members + users for workspace_id
- Paginated

`change_role(db, workspace_id, target_user_id, new_role, admin_user)`:
1. Verify admin_user is Admin in workspace
2. Reject if `new_role == 'admin'` → raise `400 BAD_REQUEST`
3. Check if target is sole Admin and being demoted → raise `403 SOLE_ADMIN`
4. Update `workspace_member.role`
5. Log audit: `action=role_change`, `old_values={'role': old}`, `new_values={'role': new}`

`remove_member(db, workspace_id, target_user_id, admin_user)`:
1. Verify admin_user is Admin
2. Check if removing sole Admin → raise `403 SOLE_ADMIN`
3. Delete `WorkspaceMember` row

**`backend/app/routers/members.py`:** 3 endpoints per API Spec v1.1 §6.

---

### Step 2.5 [BE] — Invite Service + Router

**`backend/app/services/invite_service.py`:**
Full implementation per TRD v1.2 §6.6 — all 5 functions.

Key implementation details:
- `create_invite`: generates `token_urlsafe(32)`, role cannot be 'admin' (enforce
  with CHECK constraint already in DB and also at service layer)
- `validate_invite`: checks expired, used, revoked in that order with specific
  error codes: `INVITE_EXPIRED`, `INVITE_USED`, `INVITE_REVOKED`
- `accept_invite`: atomic — create membership AND mark used in same transaction

All create + revoke actions logged to `audit_logs`.

**`backend/app/routers/invites.py`:** 5 invite endpoints per API Spec v1.1 §7.

---

### Step 2.6 [BE] — User CRUD Endpoints

**`backend/app/services/user_service.py`:**

`get_me(user)` → return user

`update_me(db, user, data)`:
- Update only provided fields (PATCH semantics)
- Validate timezone string if provided

`delete_me(db, user)`:
1. Check if sole Admin in any non-deleted workspace → raise `403 SOLE_ADMIN`
2. Delete all `WorkspaceMember` rows for this user
3. Anonymize: `email = f"deleted-{short_uuid}@anonymous.local"`,
   `full_name = f"Deleted User {short_uuid}"`, `google_id = None`,
   `is_active = False`

**`backend/app/routers/users.py`:** 3 endpoints per API Spec v1.1 §4.

---

### Step 2.7 [BE] — Phase 2 Tests

**`backend/tests/unit/test_invite_service.py`:**
```python
async def test_create_invite_expires_in_7_days(mock_db): ...
async def test_create_invite_role_admin_raises_400(mock_db): ...
async def test_validate_invite_expired_raises_400(mock_db): ...
async def test_validate_invite_used_raises_400(mock_db): ...
async def test_validate_invite_revoked_raises_400(mock_db): ...
async def test_accept_invite_creates_membership(mock_db): ...
async def test_accept_invite_already_member_raises_409(mock_db): ...
async def test_accept_invite_marks_used_true(mock_db): ...
```

**`backend/tests/unit/test_member_service.py`:**
```python
async def test_change_role_to_admin_raises_400(mock_db): ...
async def test_remove_sole_admin_raises_403(mock_db): ...
async def test_demote_sole_admin_raises_403(mock_db): ...
```

**`backend/tests/integration/test_workspace_invite.py`:**
Full flow: Admin creates workspace → invites member → member accepts →
member appears in list with correct role → Admin changes role → Admin removes member.

---

### Step 2.8 [FE] — App Shell Scaffold + Zustand Stores

**`web/src/stores/workspace-store.ts`:**
```typescript
import { create } from 'zustand'
import { queryClient } from '@/lib/query-client'

interface WorkspaceStore {
  activeWorkspaceId: string | null
  setWorkspaceId: (id: string) => void
}

export const useWorkspaceStore = create<WorkspaceStore>((set) => ({
  activeWorkspaceId: null,
  setWorkspaceId: (id) => {
    set({ activeWorkspaceId: id })
    queryClient.clear() // invalidate all cached data on workspace switch
  },
}))
```

**`web/src/stores/ui-store.ts`:**
```typescript
import { create } from 'zustand'

interface UIStore {
  sidebarOpen: boolean
  activeModal: string | null
  toggleSidebar: () => void
  openModal: (id: string) => void
  closeModal: () => void
}

export const useUIStore = create<UIStore>((set) => ({
  sidebarOpen: true,
  activeModal: null,
  toggleSidebar: () => set(s => ({ sidebarOpen: !s.sidebarOpen })),
  openModal: (id) => set({ activeModal: id }),
  closeModal: () => set({ activeModal: null }),
}))
```

---

### Step 2.9 [FE] — Sidebar Component

**`web/src/features/layout/components/Sidebar.tsx`:**
Full implementation per Blueprint v2.0 G2 — all 5 steps:

Step 1: Logo area (h-16, border-b) with YT mark + "Yusi"+"Time" color split.
Workspace name below in muted text.

Step 2: Navigation section with role-filtered items. Each NavItem uses
`usePathname()` to detect active route. Active state: `bg-brand-orange/12
text-white border-l-2 border-brand-orange font-medium` with `pl-[6px]`.

Step 3: Reports sub-navigation (expandable). ChevronRight rotates to ChevronDown.
Sub-items: Summary, Detailed, Weekly — each with same active state logic.

Step 4: Role filtering:
```typescript
const navItems = [
  { href: '/dashboard', label: 'Dashboard', icon: LayoutDashboard, roles: ['admin','manager','member','viewer'] },
  { href: '/timesheet', label: 'Timesheet', icon: CalendarClock, roles: ['admin','manager','member','viewer'] },
  { href: '/projects', label: 'Projects', icon: FolderOpen, roles: ['admin','manager','member','viewer'] },
  // Reports with sub-items
  { href: '/approvals', label: 'Approvals', icon: CheckSquare, roles: ['admin','manager'] },
  { href: '/settings', label: 'Settings', icon: Settings, roles: ['admin','manager','member','viewer'] },
]
const visible = navItems.filter(item => item.roles.includes(userRole))
```

Step 5: Footer (border-t) with Avatar + name + ThemeToggle.

---

### Step 2.10 [FE] — Workspace Settings Pages

**`web/src/features/settings/api.ts`:**
Typed API functions for workspace GET/PATCH/DELETE and member/invite operations.

**`web/src/features/settings/hooks/`:**
- `useWorkspace(id)` — React Query with 300s staleTime
- `useUpdateWorkspace()` — mutation with cache invalidation
- `useWorkspaceMembers(id)` — paginated list
- `useInvites(id)` — Admin only

**`web/src/app/(app)/settings/workspace/page.tsx`:**
Full implementation per Blueprint v2.0 H1–H4:
- General card: all fields, disabled for non-Admin
- Time Tracking card: rounding + idle (shadcn Switch with brand-orange thumb)
- Compliance card: lock period + approval workflow toggle
  (approval toggle OFF → AlertDialog with amber warning)
- Danger Zone: delete workspace → AlertDialog requiring workspace name confirmation

**`web/src/app/(app)/settings/members/page.tsx`:**
Full implementation per Blueprint v2.0 H4:
- Members table with role DropdownMenu (Admin only)
- Invite form (two-state: form → success with copyable link)
- Pending invites table with revoke
- Admin-only sections use `{role === 'admin' && ...}` pattern (absent not hidden)

---

### Phase 2 — Testing Checklist

```
BACKEND:
[ ] GET /workspaces → lists user's workspaces with roles
[ ] GET /workspaces/{id} → returns full settings
[ ] GET /workspaces/{id} (Viewer) → default_hourly_rate absent from response
[ ] PATCH /workspaces/{id} (Admin) → updates and returns new values
[ ] PATCH /workspaces/{id} (Manager) → 403 FORBIDDEN
[ ] PATCH /workspaces/{id} rounding_mode!=none, no interval → 400 BAD_REQUEST
[ ] DELETE /workspaces/{id} (Admin) → deleted_at set, members notified
[ ] GET /workspaces/{id}/members → paginated list with roles
[ ] PATCH /workspaces/{id}/members/{uid} role=admin → 400 BAD_REQUEST
[ ] PATCH /workspaces/{id}/members/{uid} (sole admin demotion) → 403 SOLE_ADMIN
[ ] DELETE /workspaces/{id}/members/{sole_admin_uid} → 403 SOLE_ADMIN
[ ] POST /workspaces/{id}/invites (Admin) → invite created, expires in 7 days
[ ] POST /workspaces/{id}/invites (Manager) → 403 FORBIDDEN
[ ] POST /workspaces/{id}/invites role=admin → 400 BAD_REQUEST
[ ] GET /workspaces/{id}/invites → only pending (not expired/used/revoked)
[ ] DELETE /workspaces/{id}/invites/{token} → revoked=True set
[ ] GET /invites/{token} valid → 200 with workspace+role
[ ] GET /invites/{token} expired → 400 INVITE_EXPIRED
[ ] GET /invites/{token} used → 400 INVITE_USED
[ ] GET /invites/{token} revoked → 400 INVITE_REVOKED
[ ] POST /invites/{token}/accept → membership created, invite marked used
[ ] POST /invites/{token}/accept (already member) → 409 ALREADY_MEMBER
[ ] audit_logs: invite_generated entry created on invite creation
[ ] audit_logs: invite_revoked entry created on revoke
[ ] audit_logs: role_change entry with old + new values

FRONTEND:
[ ] Sidebar renders with brand-navy background
[ ] Sidebar active item shows orange left border + orange tint
[ ] Sidebar Approvals item absent for Member role
[ ] WorkspaceSwitcher shows all user workspaces
[ ] Workspace settings form loads with current values pre-filled
[ ] Rounding mode change shows/hides interval selector correctly
[ ] Idle toggle shows/hides timeout selector correctly
[ ] Approval workflow toggle OFF shows AlertDialog warning
[ ] Danger Zone delete requires workspace name confirmation
[ ] Members table shows correct roles
[ ] Role change dropdown only shows manager/member/viewer (not admin)
[ ] Remove member shows AlertDialog confirmation
[ ] Invite form generates link and shows State B (success) with copy button
[ ] Copy button changes to "Copied!" for 2 seconds
[ ] Expiry notice shows in amber
[ ] Pending invites table shows with revoke button
[ ] All admin-only sections absent for Manager/Member/Viewer
[ ] Settings pages work in light + dark mode
```


---

## PHASE 3 — Projects, Tasks, Clients & Tags

**Goal:** Full CRUD for all organizational entities. Projects list and project
detail screens live. Clients and Tags settings pages complete.

**Dependencies:** Phase 2 complete.

---

### Step 3.1 [BE] — Project, Task, Client, Tag Models

**`backend/app/models/project.py`:** `Project` model per DB Schema §4.7.
All fields: `client_id` (nullable FK), `budget_hours` (NUMERIC 10,2),
`budget_amount_cents` (BIGINT), `visibility` (project_visibility enum),
`status` (project_status enum), `hourly_rate_cents`, `color` (CHAR 7),
`archived_at`. CHECK: archived status ↔ archived_at consistency.

**`backend/app/models/project_member.py`:** `ProjectMember` junction per DB Schema §4.8.
PK (project_id, user_id).

**`backend/app/models/task.py`:** `Task` per DB Schema §4.9. Include denormalized
`workspace_id`. UNIQUE(project_id, name).

**`backend/app/models/client.py`:** `Client` per DB Schema §4.6. UNIQUE(workspace_id, name).

**`backend/app/models/tag.py`:** `Tag` per DB Schema §4.10. UNIQUE(workspace_id, name).

**Verify:** All models import cleanly. Relationships defined with `back_populates`.

---

### Step 3.2 [BE] — Entity Schemas (Viewer Variants)

For each entity create TWO Pydantic response schemas:
- Full schema (Admin/Manager/Member) — includes `hourly_rate`, `budget_amount`
- Viewer schema — those financial fields completely absent (not None, absent)

Pattern for all:
```python
class ProjectResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    name: str
    # ... all fields including:
    hourly_rate: str | None      # present for admin/manager/member
    budget_amount: str | None    # present for admin/manager/member

class ProjectResponseViewer(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    name: str
    # ... all fields EXCEPT hourly_rate and budget_amount
```

Router selects schema based on `caller_role == 'viewer'`.

---

### Step 3.3 [BE] — Client Service + Router

**`backend/app/services/client_service.py`:**
- `list_clients` — paginated, include `project_count` subquery
- `create_client` — UNIQUE(workspace_id, name) check → `409 DUPLICATE_NAME`
- `update_client` — same unique check on name change
- `delete_client` — Admin only. DB cascade sets `client_id=NULL` on projects.

**`backend/app/routers/clients.py`:** 5 endpoints per API Spec v1.1 §8.
Viewer response omits `hourly_rate`.

---

### Step 3.4 [BE] — Project Service + Router

**`backend/app/services/project_service.py`:**

`list_projects(db, workspace_id, caller, status_filter, client_id)`:
- Admin/Manager: all projects
- Member/Viewer: public + projects where caller is in `project_members`
- Include `hours_logged` via `SUM(duration_seconds)/3600` subquery

`create_project` — UNIQUE check, validate `client_id` in same workspace.

`archive_project` — sets `status='archived'`, `archived_at=now()`.

`delete_project` — Admin only. Raise `400 BAD_REQUEST` if any `time_entries`
reference this project ("Archive instead — time entries exist.").

`add_project_member` / `remove_project_member` — Manager/Admin only.

**`backend/app/routers/projects.py`:** 9 endpoints per API Spec v1.1 §9.

---

### Step 3.5 [BE] — Task Service + Router

**`backend/app/services/task_service.py`:**
- `list_tasks` — verify caller has project visibility access
- `create_task` — UNIQUE(project_id, name), validate assignee is workspace member
- `delete_task` — DB cascade sets `task_id=NULL` on time_entries

**`backend/app/routers/tasks.py`:** 5 endpoints per API Spec v1.1 §10.

---

### Step 3.6 [BE] — Tag Service + Router

**`backend/app/services/tag_service.py`:**
- `list_tags` / `create_tag` (UNIQUE check) / `update_tag` / `delete_tag`
- Delete cascades via `time_entry_tags` ON DELETE CASCADE

**`backend/app/routers/tags.py`:** 4 endpoints per API Spec v1.1 §11.

---

### Step 3.7 [BE] — Phase 3 Tests

**Unit tests** — `tests/unit/test_project_service.py`:
```python
async def test_list_projects_member_sees_public_and_assigned_private_only(): ...
async def test_list_projects_admin_sees_all(): ...
async def test_create_project_duplicate_name_raises_409(): ...
async def test_archive_project_sets_status_and_archived_at(): ...
async def test_delete_project_with_entries_raises_400(): ...
async def test_add_project_member_already_assigned_raises_409(): ...
```

**Integration tests** — `tests/integration/test_projects.py`:
Full CRUD flow + visibility enforcement + budget display.

---

### Step 3.8 [FE] — Shared Components Library

Build ALL shared components before any feature pages. Every subsequent
phase depends on these.

**`web/src/components/shared/EmptyState.tsx`:**
```tsx
interface EmptyStateProps {
  icon: LucideIcon
  heading: string
  description: string
  action?: React.ReactNode
  className?: string
}

export function EmptyState({ icon: Icon, heading, description, action, className }: EmptyStateProps) {
  return (
    <div className={cn("flex flex-col items-center justify-center py-16 px-4 text-center", className)}>
      <div className="w-11 h-11 rounded-xl bg-brand-orange/8 flex items-center justify-center mb-4">
        <Icon className="w-5 h-5 text-brand-orange" />
      </div>
      <h3 className="text-sm font-semibold text-foreground mb-1">{heading}</h3>
      <p className="text-xs text-muted-foreground max-w-xs leading-relaxed mb-5">{description}</p>
      {action}
    </div>
  )
}
```

**`web/src/components/shared/PageHeader.tsx`** — title + description + actions.

**`web/src/components/shared/StatusBadge.tsx`** — all status/role variants
using CSS variable tokens, `rounded-md` (not rounded-full).

**`web/src/components/shared/ConfirmDialog.tsx`** — reusable AlertDialog with
loading spinner on confirm button.

**`web/src/components/shared/RoleBadge.tsx`** — role-specific badge colors.

**`web/src/components/shared/TableRowSkeleton.tsx`** — skeleton matching table structure.

---

### Step 3.9 [FE] — Projects API + Hooks

**`web/src/features/projects/api.ts`:** Typed functions for all project endpoints.

**`web/src/features/projects/hooks/useProjects.ts`:**
```typescript
export const projectKeys = {
  all: (wsId: string, status = 'active') => ['projects', wsId, status] as const,
  detail: (id: string) => ['projects', 'detail', id] as const,
}

export function useProjects(workspaceId: string, status = 'active') {
  return useQuery({
    queryKey: projectKeys.all(workspaceId, status),
    queryFn: () => projectsApi.list(workspaceId, status),
    staleTime: 60_000,
    enabled: !!workspaceId,
  })
}
```

Also create: `useProject(id)`, `useCreateProject()`, `useUpdateProject()`,
`useArchiveProject()`, `useDeleteProject()`.

---

### Step 3.10 [FE] — Projects List Page

**`web/src/app/(app)/projects/page.tsx`:** Full implementation per Blueprint v2.0 E1.

Grid of project cards (`grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-3`).
Each card: `hover:border-brand-orange/30 transition-all duration-200 cursor-pointer`.
Budget progress: `<Progress className="[&>div]:bg-brand-orange" value={pct} />`.
80% threshold → `[&>div]:bg-warning`. 100% → `[&>div]:bg-destructive`.
Private badge: `Lock` icon + "Private" (text-[10px]).
Three-dot menu (Admin/Manager only): Edit, Archive, Delete.
Loading: 6 skeleton cards matching exact card shape.
Empty: `<EmptyState icon={FolderOpen} heading="No projects yet" ... />`.
New Project Dialog: 8 color swatches in `grid grid-cols-4 gap-1.5`.
Selected swatch: `ring-2 ring-brand-orange ring-offset-2`.

---

### Step 3.11 [FE] — Project Detail Page

**`web/src/app/(app)/projects/[id]/page.tsx`:** Full implementation per Blueprint v2.0 E2.

Back link → `/projects`. Project header with archive/edit buttons (Manager/Admin).
Budget card: `{role !== 'viewer' && <BudgetCard />}`.
shadcn Tabs active state: `data-[state=active]:text-brand-orange
data-[state=active]:border-b-2 data-[state=active]:border-brand-orange`.
Overview tab: Recharts BarChart with `fill="#F06900"` bars.
Tasks tab: list with add/edit/delete (Manager/Admin). Assignee avatars.
Settings tab: edit form + Danger Zone (Archive / Delete).

---

### Step 3.12 [FE] — Clients + Tags Settings Pages

**`web/src/app/(app)/settings/clients/page.tsx`:** Table with add/edit Sheet,
delete AlertDialog. `hourly_rate` column: `{role !== 'viewer' && <TableHead>Rate</TableHead>}`.

**`web/src/app/(app)/settings/tags/page.tsx`:** Tag pills with dynamic bg color.
`style={{ backgroundColor: \`${tag.color}22\`, color: tag.color }}` (hex with 22=13% opacity).
Color picker: 8 swatches + custom hex input.

---

### Phase 3 — Testing Checklist

```
BACKEND:
[ ] GET /projects (Member) → only public + assigned private projects
[ ] GET /projects (Admin) → all projects including private
[ ] GET /projects (Viewer) → hourly_rate and budget_amount absent from response
[ ] POST /projects duplicate name → 409 DUPLICATE_NAME
[ ] POST /projects/{id}/archive → status=archived, archived_at timestamp set
[ ] DELETE /projects/{id} with time entries → 400 BAD_REQUEST
[ ] DELETE /projects/{id} without entries → 200 success
[ ] GET /tasks?project_id → only tasks for that project
[ ] POST /tasks duplicate name in same project → 409 DUPLICATE_NAME
[ ] DELETE /tasks/{id} → time entries get task_id=NULL (not deleted)
[ ] GET /clients → hourly_rate absent for Viewer role
[ ] DELETE /clients/{id} → linked projects get client_id=NULL
[ ] GET /tags → all workspace tags
[ ] DELETE /tags/{id} → removed from all time_entry_tags rows

FRONTEND:
[ ] Projects list loads with loading skeleton cards
[ ] Project cards show color dots correctly
[ ] Budget progress bar shows orange fill
[ ] Budget at ≥80%: warning color automatically applied
[ ] Budget at ≥100%: destructive color applied
[ ] Private badge visible on private projects
[ ] New Project dialog (Admin/Manager only — absent for others)
[ ] Color picker: 8 swatches + custom hex, selected swatch shows orange ring
[ ] Project archive works, card updates immediately
[ ] Project detail tabs: Overview, Tasks, Members, Settings navigate correctly
[ ] Recharts bar chart renders with brand-orange fill on Overview tab
[ ] Task list loads, add task button works (Manager/Admin only)
[ ] Client table shows rate column — absent for Viewer
[ ] Client add/edit sheet saves correctly
[ ] Client delete shows AlertDialog
[ ] Tag pills render with correct background color derived from tag.color
[ ] Tag add with color picker saves correctly
[ ] All pages correct in light + dark mode
```

---

## PHASE 4 — Time Tracking Core

**Goal:** Complete time tracking experience — timer, manual entries, rounding,
dashboard, timesheet grid. This is the most complex phase.

**Dependencies:** Phase 3 complete.

---

### Step 4.1 [BE] — Time Entry Model + Tag Junction

**`backend/app/models/time_entry.py`:** `TimeEntry` per DB Schema §4.11.
All fields. All three CHECK constraints:
1. `end_time > start_time` (when both present)
2. Running: `end_time IS NULL AND duration_seconds IS NULL`
3. Non-running non-draft: `end_time IS NOT NULL AND duration_seconds IS NOT NULL`

**`backend/app/models/time_entry_tag.py`:** Junction. PK (time_entry_id, tag_id).
Both ON DELETE CASCADE.

---

### Step 4.2 [BE] — Rounding Service (Critical — Test Thoroughly)

**`backend/app/services/rounding_service.py`:**
```python
import math
from dataclasses import dataclass
from enum import Enum

class RoundingMode(str, Enum):
    NONE = "none"
    NEAREST = "nearest"
    UP = "up"
    DOWN = "down"

@dataclass
class RoundingRule:
    mode: RoundingMode
    interval_minutes: int | None

@dataclass
class RoundingResult:
    raw_seconds: int
    rounded_seconds: int
    rounding_mode: RoundingMode
    rounding_interval_minutes: int | None

def round_duration(raw_seconds: int, rule: RoundingRule) -> RoundingResult:
    if rule.mode == RoundingMode.NONE or not rule.interval_minutes:
        return RoundingResult(raw_seconds, raw_seconds, rule.mode, None)
    interval_s = rule.interval_minutes * 60
    if rule.mode == RoundingMode.NEAREST:
        rounded = round(raw_seconds / interval_s) * interval_s
    elif rule.mode == RoundingMode.UP:
        rounded = math.ceil(raw_seconds / interval_s) * interval_s
    else:  # DOWN
        rounded = (raw_seconds // interval_s) * interval_s
    return RoundingResult(raw_seconds, int(rounded), rule.mode, rule.interval_minutes)
```

**Unit tests — every boundary condition:**
```python
def test_none_mode_returns_unchanged(): assert round_duration(3780, RoundingRule(RoundingMode.NONE, None)).rounded_seconds == 3780
def test_nearest_15min_below_half_rounds_down(): assert round_duration(3780, RoundingRule(RoundingMode.NEAREST, 15)).rounded_seconds == 3600  # 1h3m → 1h
def test_nearest_15min_above_half_rounds_up(): assert round_duration(4080, RoundingRule(RoundingMode.NEAREST, 15)).rounded_seconds == 4500  # 1h8m → 1h15m
def test_up_exactly_on_interval_stays(): assert round_duration(3600, RoundingRule(RoundingMode.UP, 15)).rounded_seconds == 3600
def test_up_one_second_over_rounds_up(): assert round_duration(3601, RoundingRule(RoundingMode.UP, 15)).rounded_seconds == 4500
def test_down_just_below_rounds_to_previous(): assert round_duration(4499, RoundingRule(RoundingMode.DOWN, 15)).rounded_seconds == 3600
def test_zero_seconds_all_modes_return_zero(): ...
def test_all_valid_intervals_work(): ...  # 1,5,6,10,15,30 minutes
```

---

### Step 4.3 [BE] — Rate Service

**`backend/app/services/rate_service.py`:**
```python
async def resolve_rate(db, workspace_id, project_id, task_id) -> int | None:
    # 1. Task-level
    if task_id:
        task = await db.get(Task, task_id)
        if task and task.hourly_rate_cents is not None:
            return task.hourly_rate_cents
    # 2. Project-level
    project = await db.get(Project, project_id)
    if project:
        if project.hourly_rate_cents is not None:
            return project.hourly_rate_cents
        # 3. Client-level
        if project.client_id:
            client = await db.get(Client, project.client_id)
            if client and client.hourly_rate_cents is not None:
                return client.hourly_rate_cents
    # 4. Workspace default
    workspace = await db.get(Workspace, workspace_id)
    if workspace and workspace.default_hourly_rate_cents is not None:
        return workspace.default_hourly_rate_cents
    return None
```

**Unit tests:** All 4 levels. Fallthrough when higher level is None.

---

### Step 4.4 [BE] — Time Entry Schemas

**`backend/app/schemas/time_entry.py`:**
- `TimeEntryObject` — includes `hourly_rate` and `billable_amount`
- `TimeEntryObjectViewer` — those fields absent (separate Pydantic model)
- `RoundingResult` — always included in stop/create/update responses
- All request models: `StartTimerRequest`, `StopTimerRequest`,
  `CreateManualEntryRequest`, `UpdateEntryRequest`
- Response models include `rounding: RoundingResult` always

---

### Step 4.5 [BE] — Time Entry Service

**`backend/app/services/time_entry_service.py`:**
All 7 functions. Two critical helpers:

```python
def _check_lock(entry, caller_role: str, workspace) -> None:
    if caller_role == 'admin':
        return
    if entry.status in ('pending', 'approved'):
        raise HTTPException(403, detail="Entry is locked", headers={"code": "ENTRY_LOCKED"})
    cutoff = datetime.now(timezone.utc) - timedelta(days=workspace.lock_period_days)
    if entry.start_time.replace(tzinfo=timezone.utc) < cutoff:
        raise HTTPException(403, detail="Entry past lock date", headers={"code": "ENTRY_LOCKED"})

def _compute_billable(duration_seconds: int, rate_cents: int | None) -> int | None:
    if rate_cents is None:
        return None
    return round((duration_seconds / 3600.0) * rate_cents)
```

`start_timer` enforces `mandatory_description` check before any DB operation.
`stop_timer` stores ONLY rounded duration — raw seconds never persisted.
`list_entries` uses cursor pagination on `(start_time DESC, id DESC)`.
All save operations call `rate_service.resolve_rate()` for fresh snapshot.
All save operations return `RoundingResult` so frontend can show toast.

---

### Step 4.6 [BE] — Time Entry Router

**`backend/app/routers/time_entries.py`:**
CRITICAL route registration order — specific paths before parameterized:
```
/current     (GET)   ← before /{entry_id}
/start       (POST)  ← before /{entry_id}
/{id}/stop   (POST)
/{id}/continue (POST)  ← scaffold now, implement Phase 5
/{id}/duplicate (POST) ← scaffold now, implement Phase 5
/{id}        (GET, PATCH, DELETE)
/            (GET, POST)
```

All responses: select `TimeEntryObject` or `TimeEntryObjectViewer` per role.

---

### Step 4.7 [BE] — Time Entry Tests

**`backend/tests/unit/test_time_entry_service.py`:**
```python
async def test_start_snapshots_rate_from_hierarchy(): ...
async def test_start_force_true_stops_running_first(): ...
async def test_start_force_false_running_raises_409(): ...
async def test_start_mandatory_description_missing_raises_400(): ...
async def test_stop_stores_rounded_not_raw_seconds(): ...
async def test_stop_with_idle_end_time_correct_duration(): ...
async def test_stop_always_returns_rounding_object(): ...
async def test_create_manual_past_limit_raises_400(): ...
async def test_create_manual_overlap_returns_has_overlap_true(): ...
async def test_update_pending_raises_403(): ...
async def test_update_approved_admin_succeeds(): ...
async def test_update_rerounds_from_new_raw_not_old(): ...
async def test_update_resnaps_rate_from_current_hierarchy(): ...
async def test_delete_pending_raises_403(): ...
```

**`backend/tests/integration/test_time_entries.py`:**
```python
async def test_full_timer_flow_rounded_duration_stored(async_client): ...
async def test_viewer_response_no_financial_fields(async_client): ...
async def test_force_true_stops_old_starts_new(async_client): ...
async def test_past_entry_limit_enforced(async_client): ...
```

---

### Step 4.8 [FE] — Stores

**`web/src/stores/timer-store.ts`** — `isIdle`, `idleStartTime`, `setIdle`, `clearIdle`.
**`web/src/stores/ui-store.ts`** — `sidebarOpen`, `activeModal`, `toggleSidebar`,
`openModal`, `closeModal`. Already created in Phase 2 — verify complete.

---

### Step 4.9 [FE] — Idle Detector Hook

**`web/src/features/timer/hooks/useIdleDetector.ts`:**
Events: `mousemove`, `mousedown`, `keydown`, `touchstart`, `scroll`.
On timeout: `setIdle(true, new Date())`.
On first activity after idle: `openModal('idle')` (does NOT reset timer — modal handles it).
Cleanup: `clearTimeout` + `removeEventListener` on unmount.

---

### Step 4.10 [FE] — Description Draft Hook

**`web/src/features/timer/hooks/useDescriptionDraft.ts`:**
Key: `yt_desc_draft_{userId}_{workspaceId}` in localStorage.
`getDraft()` — returns saved text or empty string.
`saveDraft(value)` — debounced 500ms, clears key if value is empty.
`clearDraft()` — removes key from localStorage.
SSR guard: `if (typeof window === 'undefined') return ''`.

---

### Step 4.11 [FE] — Rounding Toast

**`web/src/lib/rounding-toast.ts`:**
```typescript
import { toast } from 'sonner'
import { formatDuration } from './utils'

export function showRoundingToast(rounding: {
  raw_seconds: number
  rounded_seconds: number
  rounding_mode: string
  rounding_interval_minutes: number | null
}): void {
  const wasRounded = rounding.raw_seconds !== rounding.rounded_seconds
  const rounded = formatDuration(rounding.rounded_seconds)
  const raw = formatDuration(rounding.raw_seconds)

  if (wasRounded) {
    toast.success(`Saved as ${rounded}`, {
      description: `${raw} → rounded ${rounding.rounding_mode} to nearest ${rounding.rounding_interval_minutes}m`,
      duration: 5000,
    })
  } else {
    toast.success(`Saved: ${rounded}`, { duration: 3000 })
  }
}
```

Called in EVERY mutation `onSuccess` that saves a time entry.
This is non-negotiable — verified in the testing checklist.

---

### Step 4.12 [FE] — Time Entry API + Hooks

**`web/src/features/time-entries/api.ts`:** All 9 functions typed.

**Query key factory:**
```typescript
export const entryKeys = {
  all: (wsId: string) => ['time-entries', wsId] as const,
  current: (wsId: string) => ['timer', 'current', wsId] as const,
}
```

**`useCurrentTimer`** — staleTime: 0, refetchInterval: 5000.
**`useStopTimer`** — onSuccess: `showRoundingToast()` MANDATORY + invalidate.
**`useCreateEntry`** — onSuccess: `showRoundingToast()` MANDATORY + invalidate.
**`useUpdateEntry`** — onSuccess: `showRoundingToast()` MANDATORY + invalidate.
**`useStartTimer`**, **`useTimeEntries`**, **`useDeleteEntry`** — standard patterns.

---

### Step 4.13 [FE] — Full App Shell Layout

Update `web/src/app/(app)/layout.tsx` to include:
- Token refresh on mount with full-screen skeleton during in-flight
- `<Sidebar />`, `<TimerBar />`, `<IdleModal />` all mounted
- `<main>` content area with overflow-y-auto

Create `AppShellSkeleton` — gray bars matching sidebar + timer bar + content area shape.

---

### Step 4.14 [FE] — TimerBar Component

**`web/src/features/timer/components/TimerBar.tsx`:** Per Blueprint v2.0 G3.

Elapsed counter: `setInterval(1000)` computing `now() - entry.start_time`.
Use `font-variant-numeric: tabular-nums` (included in `font-mono` Tailwind class)
to prevent layout reflow as digits increment.

ProjectSelector: shadcn `Command` in `Popover`. Groups: "Recent" + "All Active".
Each item: color dot (6px) + project name + client name (muted).

Description draft: `useDescriptionDraft` hook. On mount: restore draft if no
active timer. On change: `debouncedSaveDraft(value)`. On start/stop: `clearDraft()`.

Timer state colors:
- Not running: elapsed `text-muted-foreground`, Start = `bg-brand-orange`
- Running: elapsed `text-brand-orange font-mono`, Stop = `bg-destructive`
- Idle: elapsed `text-warning`, amber pill "Idle Xm" visible

BillableToggle Switch: `className="data-[state=checked]:bg-brand-orange"`.

---

### Step 4.15 [FE] — Idle Modal

**`web/src/features/timer/components/IdleModal.tsx`:** Per Blueprint v2.0 G4.

MANDATORY implementation:
```tsx
<Dialog open={isIdle} onOpenChange={() => {}}>
  <DialogContent
    className="sm:max-w-sm [&>button]:hidden"
    onPointerDownOutside={(e) => e.preventDefault()}
    onEscapeKeyDown={(e) => e.preventDefault()}
  >
    {/* Three options — no X button, no dismiss */}
  </DialogContent>
</Dialog>
```

Three buttons handle different stop/continue combinations.
Loading state on click: spinner + all three buttons disabled.
Error state: re-enable all three + `toast.error(...)`.

---

### Step 4.16 [FE] — Dashboard Page

**`web/src/app/(app)/dashboard/page.tsx`:** Per Blueprint v2.0 C1 all 8 steps.

4 stat cards with correct skeletons matching shape.
Billable amount card: `{role !== 'viewer' && <BillableStatCard />}`.
Top projects chart: Recharts, orange bars, stagger animation on scroll.
Quick actions + last 5 entries with Continue ▶ buttons (absent on pending).
Recent entries table: group-hover pattern for action icons.
Locked rows: edit/delete `opacity-30 cursor-not-allowed title="Entry is locked"`.

---

### Step 4.17 [FE] — Timesheet Grid Page

**`web/src/app/(app)/timesheet/page.tsx`:** Per Blueprint v2.0 D1 all 8 steps.

Build in sub-steps:
A. Week state: `weekStart` useState, `weekEnd = addDays(weekStart, 6)`, day array.
B. Query: `useTimeEntries({ workspaceId, dateFrom, dateTo })`.
C. Transform: group by project → task → day.
D. Grid: header row (today = orange circle) + project groups + task rows + total row.
E. Cell states: empty (+hover), draft (pencil-hover), pending (violet), approved (green).
F. AddEntry/EditEntry Sheet with live rounding preview (pure client-side function).
G. Submit Week button: disabled + Tooltip when no draft entries. Modal with entry list.

Rounding preview (no API call):
```typescript
function previewRounding(rawSeconds: number, workspace: WorkspaceSettings) {
  if (workspace.rounding_mode === 'none') return { rounded: rawSeconds, changed: false }
  const i = (workspace.rounding_interval_minutes ?? 15) * 60
  const mode = workspace.rounding_mode
  const r = mode === 'nearest' ? Math.round(rawSeconds/i)*i
           : mode === 'up'     ? Math.ceil(rawSeconds/i)*i
           :                     Math.floor(rawSeconds/i)*i
  return { rounded: r, changed: r !== rawSeconds }
}
```

---

### Phase 4 — Testing Checklist

```
BACKEND:
[ ] GET /time-entries/current → running entry or {"data":null}
[ ] POST /time-entries/start → rate snapshot stored on new entry
[ ] POST /time-entries/start (force=false, timer running) → 409
[ ] POST /time-entries/start (force=true, timer running) → old stopped, new started
[ ] POST /time-entries/start mandatory description missing → 400
[ ] POST /time-entries/{id}/stop → duration_seconds = ROUNDED (never raw)
[ ] POST /time-entries/{id}/stop → rounding object in response body always
[ ] POST /time-entries/{id}/stop idle_end_time → duration=idle_end-start
[ ] POST /time-entries (manual) past limit → 400 PAST_ENTRY_LIMIT_EXCEEDED
[ ] POST /time-entries (manual) overlap → has_overlap=true, entry created
[ ] PATCH /time-entries/{id} pending → 403 ENTRY_LOCKED
[ ] PATCH /time-entries/{id} approved admin → 200
[ ] PATCH /time-entries/{id} → rounding re-applied from new raw value
[ ] PATCH /time-entries/{id} → rate re-snapshotted from current hierarchy
[ ] DELETE /time-entries/{id} pending → 403 ENTRY_LOCKED
[ ] GET /time-entries Viewer → hourly_rate and billable_amount absent
[ ] Rounding up 15min: 1h3m (3780s) → duration_seconds=4500 (1h15m)
[ ] Rounding down 15min: 1h3m (3780s) → duration_seconds=3600 (1h0m)
[ ] Rounding nearest 15min: 1h3m (3780s) → 3600; 1h8m (4080s) → 4500
[ ] Rate hierarchy: task→project→client→workspace priority verified

FRONTEND:
[ ] TimerBar renders in light and dark mode correctly
[ ] Start button is bg-brand-orange with Play icon
[ ] ProjectSelector Command popover opens and filters
[ ] TaskSelector populates after project selected, disabled before
[ ] Timer starts: elapsed counts up every second
[ ] Elapsed display uses DM Mono font (tabular nums — no layout shift)
[ ] Elapsed color: brand-orange when running
[ ] Stop button is destructive red
[ ] Stop: ROUNDING TOAST appears — mandatory verification
[ ] Rounding toast shows correct before/after format
[ ] Idle: amber "Idle Xm" pill appears after configured timeout
[ ] Idle modal opens on first interaction after idle state
[ ] Idle modal: NO X close button present in DOM
[ ] Idle modal: clicking outside does NOT close
[ ] Idle modal: Escape key does NOT close
[ ] "Keep Time": modal closes, timer continues unchanged
[ ] "Discard & Stop": entry saved at idle start, rounding toast
[ ] "Discard & Continue": old saved, new timer starts, rounding toast
[ ] Description draft: type → close browser → reopen → text restored
[ ] Description draft: cleared on start timer
[ ] Description draft: cleared on stop timer
[ ] Dashboard stat cards load with real data
[ ] Billable Amount card absent for Viewer
[ ] Top projects Recharts chart renders with orange bars
[ ] Continue ▶ on recent entries works
[ ] Continue ▶ absent on pending entries (not rendered, not disabled)
[ ] Recent entries table locked rows: icons opacity-30 cursor-not-allowed
[ ] Timesheet grid renders for current week
[ ] Empty cells: + icon on hover, orange tint bg
[ ] Draft cells: pencil on hover
[ ] Pending cells: violet-muted bg + violet dot top-right
[ ] Approved cells: green-muted bg + green dot top-right
[ ] Submit Week disabled + tooltip when no draft entries
[ ] Submit Week modal lists correct entries with count in button
[ ] After submit: cells transition to violet (pending) state
[ ] AddEntry Sheet opens, rounding preview updates live
[ ] All pages correct in light + dark mode
```

---

## PHASE 5 — Continue, Duplicate & Draft

**Goal:** Continue and Duplicate endpoints live. UI components wired.
Description draft already works from Phase 4 — just verify.

**Dependencies:** Phase 4 complete.

---

### Step 5.1 [BE] — Continue Entry

Add to `time_entry_service.py`:

```python
async def continue_entry(db, user, workspace_id, entry_id, force=False):
    source = await db.get(TimeEntry, entry_id)
    if not source or source.workspace_id != workspace_id:
        raise HTTPException(404, detail="Entry not found", headers={"code": "NOT_FOUND"})
    # Authorization
    if user.role == 'member' and source.user_id != user.id:
        raise HTTPException(403, detail="Cannot continue another user's entry",
                          headers={"code": "FORBIDDEN"})
    # Status check
    if source.status == 'pending':
        raise HTTPException(400, detail="Cannot continue a pending entry",
                          headers={"code": "CANNOT_CONTINUE_PENDING"})
    # Timer conflict
    running = await _get_running_timer(db, user.id, workspace_id)
    if running and not force:
        raise HTTPException(409, detail="Timer already running",
                          headers={"code": "TIMER_ALREADY_RUNNING"})
    if running and force:
        await stop_timer(db, user, workspace_id, str(running.id))
    # Copy tags from source
    tag_ids = [row.tag_id for row in source.tags]
    # Fresh rate snapshot
    rate_cents = await rate_service.resolve_rate(db, workspace_id,
                                                  source.project_id, source.task_id)
    # Create new entry
    new_entry = TimeEntry(
        workspace_id=workspace_id,
        user_id=user.id,
        project_id=source.project_id,
        task_id=source.task_id,
        description=source.description,
        billable=source.billable,
        status='running',
        start_time=datetime.now(timezone.utc),
        hourly_rate_cents=rate_cents,
    )
    db.add(new_entry)
    await db.flush()
    for tid in tag_ids:
        db.add(TimeEntryTag(time_entry_id=new_entry.id, tag_id=tid))
    return new_entry, str(source.id)
```

Add `POST /{entry_id}/continue` endpoint to router (already scaffolded).

---

### Step 5.2 [BE] — Duplicate Entry

Add to `time_entry_service.py`:

```python
async def duplicate_entry(db, user, workspace_id, entry_id):
    source = await db.get(TimeEntry, entry_id)
    if not source or source.workspace_id != workspace_id:
        raise HTTPException(404, headers={"code": "NOT_FOUND"})
    if user.role == 'member' and source.user_id != user.id:
        raise HTTPException(403, headers={"code": "FORBIDDEN"})
    if source.status == 'pending':
        raise HTTPException(400, headers={"code": "CANNOT_DUPLICATE_PENDING"})

    # Today midnight in workspace timezone
    from zoneinfo import ZoneInfo
    workspace = await db.get(Workspace, workspace_id)
    tz = ZoneInfo(workspace.default_timezone or 'UTC')
    today_midnight = datetime.now(tz).replace(hour=0, minute=0, second=0, microsecond=0)
    start_utc = today_midnight.astimezone(timezone.utc)
    raw_seconds = source.duration_seconds or 0
    end_utc = start_utc + timedelta(seconds=raw_seconds)

    # Rounding
    rule = RoundingRule(RoundingMode(workspace.rounding_mode), workspace.rounding_interval_minutes)
    rounding_result = round_duration(raw_seconds, rule)

    # Rate snapshot
    rate_cents = await rate_service.resolve_rate(db, workspace_id,
                                                  source.project_id, source.task_id)
    billable_cents = _compute_billable(rounding_result.rounded_seconds, rate_cents)

    new_entry = TimeEntry(
        workspace_id=workspace_id, user_id=user.id,
        project_id=source.project_id, task_id=source.task_id,
        description=source.description, billable=source.billable,
        status='draft', start_time=start_utc, end_time=end_utc,
        duration_seconds=rounding_result.rounded_seconds,
        hourly_rate_cents=rate_cents,
        billable_amount_cents=billable_cents,
    )
    db.add(new_entry)
    await db.flush()
    for row in source.tags:
        db.add(TimeEntryTag(time_entry_id=new_entry.id, tag_id=row.tag_id))
    return new_entry, rounding_result, str(source.id)
```

Add `POST /{entry_id}/duplicate` endpoint to router.

---

### Step 5.3 [BE] — Phase 5 Tests

```python
# tests/unit/test_continue_duplicate.py
async def test_continue_draft_entry_creates_running(): ...
async def test_continue_approved_entry_creates_running(): ...
async def test_continue_pending_raises_400(): ...
async def test_continue_other_user_member_raises_403(): ...
async def test_continue_force_true_stops_running_first(): ...
async def test_continue_fresh_rate_not_source_rate(): ...
async def test_continue_copies_all_tags(): ...
async def test_duplicate_pending_raises_400(): ...
async def test_duplicate_start_time_today_midnight_workspace_tz(): ...
async def test_duplicate_applies_rounding(): ...
async def test_duplicate_returns_rounding_result(): ...
async def test_duplicate_computes_billable_amount(): ...
async def test_duplicate_source_entry_unchanged(): ...
```

---

### Step 5.4 [FE] — Continue + Duplicate Hooks

**`web/src/features/time-entries/hooks/useContinueEntry.ts`:**
```typescript
export function useContinueEntry() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ entryId, workspaceId, force = false }:
      { entryId: string; workspaceId: string; force?: boolean }) =>
      timeEntriesApi.continue(entryId, { workspaceId, force }),
    onSuccess: (_, { workspaceId }) => {
      qc.invalidateQueries({ queryKey: entryKeys.current(workspaceId) })
      qc.invalidateQueries({ queryKey: entryKeys.all(workspaceId) })
    },
  })
}
```

**`web/src/features/time-entries/hooks/useDuplicateEntry.ts`:**
```typescript
export function useDuplicateEntry() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ entryId, workspaceId }:
      { entryId: string; workspaceId: string }) =>
      timeEntriesApi.duplicate(entryId, { workspaceId }),
    onSuccess: (response, { workspaceId }) => {
      showRoundingToast(response.data.rounding)  // MANDATORY
      qc.invalidateQueries({ queryKey: entryKeys.all(workspaceId) })
      qc.invalidateQueries({ queryKey: ['dashboard', workspaceId] })
    },
  })
}
```

---

### Step 5.5 [FE] — ContinueButton + DuplicateMenuItem

**`web/src/components/shared/ContinueButton.tsx`:**
```tsx
interface ContinueButtonProps {
  entryId: string
  entryStatus: string
  workspaceId: string
  hasRunningTimer: boolean
}

export function ContinueButton({
  entryId, entryStatus, workspaceId, hasRunningTimer
}: ContinueButtonProps) {
  // ABSENT for pending — returns null, not disabled
  if (entryStatus === 'pending') return null

  const { mutate, isPending } = useContinueEntry()
  const [showConfirm, setShowConfirm] = useState(false)

  const handleClick = () => {
    if (hasRunningTimer) {
      setShowConfirm(true)
    } else {
      mutate({ entryId, workspaceId })
    }
  }

  return (
    <>
      <Tooltip>
        <TooltipTrigger asChild>
          <button
            onClick={handleClick}
            disabled={isPending}
            aria-label="Continue this entry"
            className="p-1.5 rounded-md text-muted-foreground
                       hover:text-brand-orange hover:bg-brand-orange/8
                       transition-colors duration-120"
          >
            <Play className="w-3.5 h-3.5" />
          </button>
        </TooltipTrigger>
        <TooltipContent>Continue this entry</TooltipContent>
      </Tooltip>

      <AlertDialog open={showConfirm} onOpenChange={setShowConfirm}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Switch active timer?</AlertDialogTitle>
            <AlertDialogDescription>
              Your current timer will be stopped and saved before starting this one.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction
              className="bg-brand-orange hover:bg-brand-orange-hover text-white"
              onClick={() => {
                setShowConfirm(false)
                mutate({ entryId, workspaceId, force: true })
              }}
            >
              Stop & Continue
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </>
  )
}
```

**`web/src/components/shared/DuplicateMenuItem.tsx`:**
```tsx
export function DuplicateMenuItem({ entryId, entryStatus, workspaceId }: Props) {
  if (entryStatus === 'pending') return null  // ABSENT not disabled
  const { mutate } = useDuplicateEntry()
  return (
    <DropdownMenuItem onClick={() => mutate({ entryId, workspaceId })}>
      <Copy className="w-4 h-4 mr-2" />Duplicate
    </DropdownMenuItem>
  )
}
```

Wire both into Dashboard recent entries, Timesheet row menus, Detailed Report rows.

---

### Phase 5 — Testing Checklist

```
BACKEND:
[ ] POST /{id}/continue (draft) → 201 new running entry
[ ] POST /{id}/continue (approved) → 201 new running entry
[ ] POST /{id}/continue (pending) → 400 CANNOT_CONTINUE_PENDING
[ ] POST /{id}/continue (Member, other user) → 403 FORBIDDEN
[ ] POST /{id}/continue (force=true, timer running) → old stopped, new starts
[ ] POST /{id}/continue → same project/task/description/billable/tags
[ ] POST /{id}/continue → FRESH rate (not inherited from source)
[ ] POST /{id}/continue → source entry UNCHANGED
[ ] POST /{id}/duplicate (draft) → 201 new draft
[ ] POST /{id}/duplicate (pending) → 400 CANNOT_DUPLICATE_PENDING
[ ] POST /{id}/duplicate → start_time = today midnight workspace timezone
[ ] POST /{id}/duplicate → rounding applied, rounding object in response
[ ] POST /{id}/duplicate → billable_amount_cents computed
[ ] POST /{id}/duplicate → source entry UNCHANGED

FRONTEND:
[ ] Continue ▶ button on draft entries (Dashboard, Timesheet, Detailed Report)
[ ] Continue ▶ button on approved entries
[ ] Continue ▶ NULL/absent on pending entries — not in DOM
[ ] Continue no running timer → starts immediately
[ ] Continue with running timer → AlertDialog appears
[ ] AlertDialog "Stop & Continue" → rounding toast → new timer
[ ] Duplicate in three-dot menu on draft/approved entries
[ ] Duplicate ABSENT from menu on pending entries
[ ] Duplicate success → rounding toast with new entry duration
[ ] Duplicate success → entry appears in list with today's date
[ ] Description draft works (verified from Phase 4)
```

---

## PHASE 6 — Approvals & Notifications

**Goal:** Full approval workflow. Members submit, managers approve/reject.
In-app notifications. Notification panel live.

---

### Step 6.1 [BE] — Submission Models

**`backend/app/models/timesheet_submission.py`:** `TimesheetSubmission` per DB Schema §4.13.
All CHECK constraints including week_start Monday check.

**`backend/app/models/submission_entry.py`:** `SubmissionEntry` per DB Schema §4.14.
Unique index on `time_entry_id` alone (entry can be in at most one submission).

---

### Step 6.2 [BE] — Notification Service + Router

**`backend/app/services/notification_service.py`:**
`create`, `create_for_role`, `mark_read`, `mark_all_read` — per TRD v1.2 §6.6.

`create_for_role` fetches all `WorkspaceMember` rows matching `role IN [roles]`
and calls `create` for each. Done inside the same transaction as the trigger event.

**`backend/app/routers/notifications.py`:** 3 endpoints per API Spec v1.1 §16.

---

### Step 6.3 [BE] — Approval Service + Router

**`backend/app/services/approval_service.py`:** All 4 functions per TRD v1.2 §6.6.

Key `submit_week` atomicity: all entry status updates + submission creation
+ submission_entry rows must happen in one transaction. Use `db.flush()` to
get submission ID before creating submission_entry rows.

`reject_submission` validates `note.strip()` is non-empty before any DB change.
Return `422 VALIDATION_ERROR` if blank or whitespace-only.

`handle_workflow_disabled` is intentionally a no-op for entry statuses —
lock enforcement logic handles the behavior implicitly.

**`backend/app/routers/approvals.py`:** 4 endpoints per API Spec v1.1 §13.
All check `workspace.approval_workflow_enabled == True` first.

---

### Step 6.4 [BE] — Approval Tests

```python
# tests/unit/test_approval_service.py
async def test_submit_only_draft_entries_included(): ...
async def test_submit_approved_entries_excluded(): ...
async def test_submit_no_entries_raises_400(): ...
async def test_submit_double_submit_raises_409(): ...
async def test_submit_not_monday_raises_400(): ...
async def test_approve_sets_all_entries_approved(): ...
async def test_reject_blank_note_raises_422(): ...
async def test_reject_whitespace_note_raises_422(): ...
async def test_reject_sets_entries_to_draft(): ...
async def test_workflow_disabled_pending_stays_pending(): ...

# tests/integration/test_approvals.py
async def test_full_approve_flow(async_client): ...
async def test_full_reject_resubmit_flow(async_client): ...
async def test_member_cannot_edit_pending(async_client): ...
async def test_admin_can_edit_pending(async_client): ...
```

---

### Step 6.5 [FE] — Notifications API + Hook

**`web/src/features/notifications/api.ts`** and
**`web/src/features/notifications/hooks/useNotifications.ts`:**
staleTime: 30_000, refetchInterval: 30_000.

---

### Step 6.6 [FE] — NotificationBell + Panel

**`web/src/features/notifications/components/NotificationBell.tsx`:** Per Blueprint v2.0 G5.
Unread badge: `bg-destructive` circle. Framer Motion spring bounce on count increase.
Sheet side="right" w-[360px]. Mark all read on panel open (2s delay).
Event icons: CheckCircle2=approved, XCircle=rejected, Send=submitted,
AlarmClock=timer_stopped, Trash2=deleted.

---

### Step 6.7 [FE] — Approvals Page

**`web/src/app/(app)/approvals/page.tsx`:** Per Blueprint v2.0 G1 all 7 steps.

Access guard: `if (role !== 'admin' && role !== 'manager') redirect('/dashboard')`.
Status tabs: active = `bg-brand-orange/10 text-brand-orange border border-brand-orange/20`.
Submission card: `hover:border-brand-orange/20`. Expand chevron Framer Motion rotate.
Approve: AlertDialog, green button. On success: card exits with AnimatePresence.
Reject: Dialog, Textarea with counter. Validates non-empty on submit.
Empty: `<EmptyState icon={CheckCircle2} heading="All caught up!" />`.

---

### Phase 6 — Testing Checklist

```
BACKEND:
[ ] POST /approvals/submit → entries become pending, submission created
[ ] POST /approvals/submit (no drafts) → 400 NO_ENTRIES_TO_SUBMIT
[ ] POST /approvals/submit (not Monday) → 400 INVALID_WEEK_START
[ ] POST /approvals/submit (double submit) → 409 ALREADY_SUBMITTED
[ ] POST /approvals/submit → approved entries in same week excluded
[ ] POST /approvals/submit (workflow disabled) → 400 BAD_REQUEST
[ ] GET /approvals/pending (Manager) → 200 with list
[ ] GET /approvals/pending (Member) → 403 FORBIDDEN
[ ] POST /approvals/{id}/approve → entries=approved, member notified
[ ] POST /approvals/{id}/approve (not pending) → 400
[ ] POST /approvals/{id}/reject blank note → 422
[ ] POST /approvals/{id}/reject whitespace note → 422
[ ] POST /approvals/{id}/reject → entries=draft, note stored, member notified
[ ] Notifications created for correct recipients on each event
[ ] GET /notifications → user's notifications
[ ] POST /notifications/read → marks specified IDs read
[ ] POST /notifications/read-all → marks all read

FRONTEND:
[ ] Approvals: Member → redirected to /dashboard
[ ] Submission cards load correctly
[ ] Expand chevron rotates, entry table appears
[ ] Approve AlertDialog correct message, green button
[ ] Approve success: card animates out
[ ] Reject Dialog: blank submit shows error "Rejection note is required"
[ ] Reject character counter: warning color at 900+
[ ] Notification bell shows unread count
[ ] Opening panel shows notifications with correct icons
[ ] Mark all read clears badge
[ ] Approvals empty state: "All caught up!" with CheckCircle2 icon
[ ] All in light + dark mode
```

---

## PHASE 7 — Reports & Analytics

**Goal:** Summary, Detailed, Weekly report pages fully functional with
filtering, charts, exports, and saved views.

---

### Step 7.1 [BE] — SavedReportView Model + Report Service

**`backend/app/models/saved_report_view.py`:** Per DB Schema §4.15.
`report_type` CHECK includes `'weekly'` (DB Schema v2.1 fix already in migration).

**`backend/app/services/report_service.py`:** All report functions per TRD v1.2 §6.6.

`get_summary` — GROUP BY aggregation query. Viewer isolation: omit
`total_billable_amount` from response schema.

`get_weekly_report` — validate span ≤ 31 days. Lock user_id for Member/Viewer.
GROUP BY `(user_id, DATE(start_time AT TIME ZONE workspace_tz))`. Build
per-user, per-day dict. Include zero-hour days in response.

`export_*` — `StreamingResponse` with `text/csv` content type.

Saved views: `list`, `create` (UNIQUE check), `delete` (verify ownership).

**`backend/app/routers/reports.py`:** All 9 endpoints per API Spec v1.1 §14.

---

### Step 7.2 [BE] — Report Tests

```python
async def test_summary_member_locked_to_own_data(): ...
async def test_summary_viewer_billable_amount_absent(): ...
async def test_weekly_member_locked_to_own_row(): ...
async def test_weekly_span_31_days_passes(): ...
async def test_weekly_span_32_days_raises_400(): ...
async def test_weekly_zero_hour_days_included(): ...
async def test_detailed_cursor_pagination_page2(): ...
async def test_csv_exports_valid_format(): ...
```

---

### Step 7.3 [FE] — Report API + Hooks + FilterBar

**`web/src/features/reports/api.ts`** and all hooks.
**`web/src/features/reports/components/FilterBar.tsx`:** Reusable across all 3 pages.
Date range Popover with presets. User filter hidden for Member.
Export: blob download pattern. Save View: inline input on click.

---

### Step 7.4 [FE] — All Report Pages

**Summary** — FilterBar + 4 metric cards + Recharts HorizontalBarChart
(billable: `fill="#F06900"`, non-billable: `fill="hsl(var(--muted))"`) +
sortable table + saved views sidebar.

**Detailed** — Same FilterBar + infinite scroll table + Continue/Duplicate per row.

**Weekly** — Grid table. Today column orange tint. Zero = "—" muted.
Has-hours: `font-mono` bold, click → Popover with entries + "View in Detailed" link.

All: Billable columns absent for Viewer. CSV export triggers file download.

---

### Phase 7 — Testing Checklist

```
BACKEND + FRONTEND combined:
[ ] Summary: Member only sees own data
[ ] Summary: Viewer response has no billable_amount fields
[ ] Summary: Group by project/user/client/tag all work
[ ] Detailed: cursor pagination returns correct pages
[ ] Weekly: Member sees only own row
[ ] Weekly: date span >31 days → 400
[ ] Weekly: zero-hour days included with "—" in cell
[ ] All CSV exports download valid files
[ ] Saved views: create, apply, delete
[ ] Report pages: billable columns absent for Viewer
[ ] Recharts chart renders with orange bars
[ ] Cell click in Weekly opens Popover with entries
[ ] All pages correct in light + dark mode
```
---

## PHASE 7.5 — Super Admin UI Dashboard

**Goal:** Build the complete Super Admin Next.js dashboard at `/superadmin`.
This phase adds the platform-level backend API endpoints (`/admin/*`) and the
full frontend dashboard. By this point Phase 2 (Workspace & Members) is fully
implemented, meaning real workspace and user data exists to populate and test
the dashboard immediately.

**Dependencies:** Phase 7 complete. Phase 2 must be complete (real workspace
and member data required for meaningful Super Admin UI).
**Prerequisite reading:** UI/UX Blueprint v2.0 Part 14 (Super Admin Dashboard),
DB Schema v2.2 Changelog §12, TRD v1.3 §6.5.

---

### Step 7.5.1 [BE] — Create Admin Router

**File:** `backend/app/routers/admin.py` *(new file)*

All endpoints in this router use `Depends(get_superadmin_user)` as their
auth dependency. No workspace membership is required.

Implement these endpoints:

```python
GET  /admin/workspaces          # List ALL workspaces, paginated, with member_count
GET  /admin/workspaces/{id}     # Get single workspace full detail
GET  /admin/users               # List ALL users, paginated, with workspace_count
GET  /admin/users/{id}          # Get single user full detail + workspace memberships
GET  /admin/stats               # Platform aggregate statistics
```

Register in `main.py`:
```python
app.include_router(admin_router, prefix="/api/v1")
```

---

### Step 7.5.2 [BE] — Admin Service

**File:** `backend/app/services/admin_service.py` *(new file)*

```python
async def list_all_workspaces(db, page, per_page) -> list[WorkspaceAdminView]:
    """List all workspaces across platform. No workspace_id filter."""

async def get_workspace_detail(db, workspace_id) -> WorkspaceAdminView:
    """Get full workspace detail. No membership check."""

async def list_all_users(db, page, per_page) -> list[UserAdminView]:
    """List all users across platform with workspace membership counts."""

async def get_user_detail(db, user_id) -> UserAdminDetail:
    """Get single user with all workspace memberships and roles."""

async def get_platform_stats(db) -> PlatformStats:
    """
    Returns:
      total_workspaces: int
      total_users: int
      total_time_entries: int
      active_timers_now: int
      new_workspaces_last_30_days: int
      new_users_last_30_days: int
    """
```

---

### Step 7.5.3 [BE] — Admin Schemas

**File:** `backend/app/schemas/admin.py` *(new file)*

```python
class WorkspaceAdminView(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    name: str
    logo_url: str | None
    default_timezone: str
    currency: str
    member_count: int
    approval_workflow_enabled: bool
    deleted_at: datetime | None
    created_at: datetime

class UserAdminView(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    full_name: str
    email: str
    is_superadmin: bool
    is_active: bool
    workspace_count: int
    created_at: datetime

class UserAdminDetail(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    full_name: str
    email: str
    avatar_url: str | None
    timezone: str | None
    is_superadmin: bool
    is_active: bool
    created_at: datetime
    workspaces: list[WorkspaceMembershipView]

class WorkspaceMembershipView(BaseModel):
    workspace_id: UUID
    workspace_name: str
    role: str
    joined_at: datetime

class PlatformStats(BaseModel):
    total_workspaces: int
    total_users: int
    total_time_entries: int
    active_timers_now: int
    new_workspaces_last_30_days: int
    new_users_last_30_days: int
```

---

### Step 7.5.4 [BE] — Admin Tests

**File:** `backend/tests/unit/test_admin_service.py`

```python
async def test_list_all_workspaces_returns_all_no_filter(): ...
async def test_list_all_workspaces_pagination_correct(): ...
async def test_get_workspace_detail_no_membership_required(): ...
async def test_list_all_users_returns_all_users(): ...
async def test_get_user_detail_includes_workspace_memberships(): ...
async def test_platform_stats_returns_correct_counts(): ...
async def test_platform_stats_active_timers_count_correct(): ...
```

**File:** `backend/tests/integration/test_admin_router.py`

```python
async def test_get_admin_workspaces_superadmin_200(async_client): ...
async def test_get_admin_workspaces_normal_user_403(async_client): ...
async def test_get_admin_users_superadmin_200(async_client): ...
async def test_get_admin_stats_superadmin_200(async_client): ...
async def test_admin_workspace_list_includes_all_workspaces(async_client): ...
```

---

### Step 7.5.5 [FE] — Super Admin Route Guard in Middleware

**File:** `web/src/middleware.ts`

Add `/superadmin` to the protected prefixes list:
```typescript
const protectedPrefixes = ['/dashboard', '/timesheet', '/projects',
                            '/reports', '/approvals', '/settings',
                            '/superadmin']
```

Add Super Admin redirect guard after the existing auth check:
```typescript
// Super Admin route protection
if (pathname.startsWith('/superadmin')) {
  // Middleware cannot read is_superadmin from JWT (not in token payload)
  // The AppShell will handle the redirect on client-side mount
  // Middleware only ensures the user is authenticated
}
```

**Note:** The `is_superadmin` check is enforced client-side in the Super Admin
layout component (Step 7.5.6), not in middleware, because the flag is not
stored in the JWT. The middleware guarantees authentication; the layout
guarantees Super Admin authorization.

---

### Step 7.5.6 [FE] — Super Admin App Shell Layout

**File:** `web/src/app/superadmin/layout.tsx` *(new file)*

```tsx
'use client'
export default function SuperAdminLayout({ children }) {
  // On mount: call GET /users/me
  // If is_superadmin === false: redirect to /dashboard
  // If is_superadmin === true: render Super Admin shell

  // Shell structure:
  // <div className="flex h-screen bg-background">
  //   <SuperAdminSidebar />
  //   <main className="flex-1 overflow-y-auto">{children}</main>
  // </div>
}
```

Full component specification in UI/UX Blueprint v2.0 Part 14.

---

### Step 7.5.7 [FE] — Super Admin Pages

Create all pages per UI/UX Blueprint v2.0 Part 14:

| File | Route | Description |
|------|-------|-------------|
| `app/superadmin/page.tsx` | `/superadmin` | Stats dashboard home |
| `app/superadmin/workspaces/page.tsx` | `/superadmin/workspaces` | All workspaces list |
| `app/superadmin/workspaces/[id]/page.tsx` | `/superadmin/workspaces/[id]` | Single workspace detail |
| `app/superadmin/users/page.tsx` | `/superadmin/users` | All users list |
| `app/superadmin/users/[id]/page.tsx` | `/superadmin/users/[id]` | Single user detail |

---

### Step 7.5.8 [FE] — Super Admin API Layer

**File:** `web/src/features/superadmin/api.ts` *(new file)*

```typescript
export const superAdminApi = {
  getStats: () =>
    apiClient.get('/admin/stats'),
  listWorkspaces: (page = 1, perPage = 20) =>
    apiClient.get('/admin/workspaces', { params: { page, per_page: perPage } }),
  getWorkspace: (id: string) =>
    apiClient.get(`/admin/workspaces/${id}`),
  listUsers: (page = 1, perPage = 20) =>
    apiClient.get('/admin/users', { params: { page, per_page: perPage } }),
  getUser: (id: string) =>
    apiClient.get(`/admin/users/${id}`),
}
```

---

### Phase 7.5 — Testing Checklist

```
BACKEND:
[ ] GET /admin/workspaces (Super Admin) → 200 with all workspaces
[ ] GET /admin/workspaces (normal user) → 403 FORBIDDEN
[ ] GET /admin/workspaces/{id} (Super Admin, not a member) → 200
[ ] GET /admin/users (Super Admin) → 200 with all users
[ ] GET /admin/users/{id} (Super Admin) → 200 with memberships
[ ] GET /admin/stats (Super Admin) → 200 with correct counts
[ ] active_timers_now reflects real running timers
[ ] pytest tests/unit/test_admin_service.py — all pass
[ ] pytest tests/integration/test_admin_router.py — all pass

FRONTEND:
[ ] /superadmin inaccessible to non-super-admin → redirected to /dashboard
[ ] Super Admin sidebar visible only when is_superadmin=true
[ ] Stats cards show correct platform numbers
[ ] Workspace list loads all workspaces with member counts
[ ] Workspace detail page loads without membership
[ ] User list loads all users
[ ] User detail shows workspace memberships
[ ] All pages correct in light + dark mode
[ ] pnpm tsc --noEmit → zero errors
[ ] pnpm build → success
```

---

## PHASE 8 — Webhooks, Polish & Deployment

**Goal:** Webhooks live. All settings pages complete. Full UI polish.
CI/CD deploys to staging. End-to-end QA.

---

### Step 8.1 [BE] — Webhook Service + Router + Audit Logs

**`backend/app/models/webhook.py`** and `webhook_delivery_log.py` per DB Schema.

**`backend/app/services/webhook_service.py`:** Non-blocking dispatch via
`BackgroundTasks`. HMAC-SHA256 signing. Retry: delays [5, 25, 125]s.
Log each attempt to `webhook_delivery_logs`.

Integrate `dispatch` into: `submit_week`, `approve_submission`,
`reject_submission`, `create_manual_entry`, `update_entry`.

Audit log writes for: `lock_override`, `approve`, `reject` (already done in
approval_service). Verify all 7 events from §8.6 are covered.

**`backend/app/routers/webhooks.py`:** 5 endpoints. Admin only.

---

### Step 8.2 [FE] — Webhooks + Profile Settings Pages

**`web/src/app/(app)/settings/webhooks/page.tsx`:** Per Blueprint v2.0 H7.
Webhook cards, delivery logs accordion, Add Webhook Sheet with events checklist.
Active Switch: `data-[state=checked]:bg-brand-orange`.

**`web/src/app/(app)/settings/profile/page.tsx`:** Per Blueprint v2.0 H8.
Profile form + change password (email accounts only) + delete account danger zone.

---

### Step 8.3 [FE] — UI Polish Pass

**Animation audit:** All durations ≤ 0.3s. `reducedMotion="user"` respected.
**Interaction audit:** All buttons `active:scale-[0.97]`. All inputs orange focus ring.
All disabled: `opacity-50 cursor-not-allowed`. All icon-only buttons: `aria-label`.
**Typography audit:** Every time/money value uses `font-mono`. Zero raw hex in components.
**Brand audit:** All primary CTAs `bg-brand-orange`. Sidebar `bg-brand-navy`.
**Viewer isolation final audit:** Verify every financial field is absent (not hidden)
across all 21 screens for Viewer role.

---

### Step 8.4 [FE] — Accessibility + Responsive Final Pass

Accessibility: Tab navigation, aria-labels, focus trapping in modals,
skip link at `<a href="#main" className="sr-only focus:not-sr-only">`.

Responsive test at: 375px, 768px, 1024px, 1440px.
Fix any overflow, horizontal scroll, or broken layouts.

---

### Step 8.5 [BOTH] — AWS Deployment

**Backend:** Dockerfile, ECR push, ECS Fargate (2 tasks), ALB, RDS PostgreSQL 15,
SSM for secrets, `alembic upgrade head` as pre-deploy task.

**Frontend:** Amplify connected to GitHub main branch, NEXT_PUBLIC_API_URL env var,
custom domain (app.yusitime.com).

**CI/CD updated:** backend.yml adds Docker build + ECR push + ECS deploy.
Frontend auto-deploys via Amplify on push to main.

---

### Step 8.6 [BOTH] — Final End-to-End QA

Run all 12 user stories from PRD v1.3 §6 on staging:
1. Signup → default workspace created
2. Invite flow end-to-end
3. Timer → stop → rounding toast
4. Submit → approve → entries locked green
5. Submit → reject with note → unlock → resubmit
6. Viewer: zero financial fields anywhere
7. Idle detection all three options
8. Continue entry one-click
9. Duplicate entry + rounding toast
10. Description draft across refresh
11. Weekly report grid + cell popover + export
12. Expired invite link error page

---

### Phase 8 — Final Testing Checklist

```
BACKEND:
[ ] Webhooks dispatch on all 5 event types
[ ] Webhook retry: 3 attempts in delivery_logs
[ ] HMAC signature header correct when secret set
[ ] Audit logs: all 7 event types verified
[ ] GET /health → 200 on staging
[ ] alembic upgrade head from zero on staging DB
[ ] All 76 endpoints correct {detail, code} error format
[ ] No 500 errors during QA session

FRONTEND:
[ ] Webhooks settings CRUD works
[ ] Profile settings save correctly
[ ] All animations ≤ 0.3s
[ ] reducedMotion: animations skipped
[ ] Tab navigation on all forms
[ ] All icon-only buttons have aria-label
[ ] Skip link on focus
[ ] 21 screens: light mode visual QA ✓
[ ] 21 screens: dark mode visual QA ✓
[ ] 375px: no horizontal scroll on any screen
[ ] pnpm build: zero errors, zero TypeScript errors

END-TO-END:
[ ] All 12 PRD user stories pass on staging
[ ] CloudWatch logs structured JSON
[ ] Amplify + ECS pipelines green
[ ] Custom domain with TLS resolves
```

---

## PROJECT_STATE.md Template

Create at `yusi-time/PROJECT_STATE.md` before Phase 0 begins.

```markdown
# Yusi Time — Project State
**Last Updated:** YYYY-MM-DD HH:MM
**Current Phase:** Phase N — [Name] — [Status]

## Phase Summary

| Phase | Name | Status | Completed |
|-------|------|--------|-----------|
| 0 | Setup & Infrastructure | ⬜ Not Started | — |
| 1 | Authentication | ⬜ Not Started | — |
| 2 | Workspace & Members | ⬜ Not Started | — |
| 3 | Projects, Tasks, Clients, Tags | ⬜ Not Started | — |
| 4 | Time Tracking Core | ⬜ Not Started | — |
| 5 | Continue, Duplicate & Draft | ⬜ Not Started | — |
| 6 | Approvals & Notifications | ⬜ Not Started | — |
| 7 | Reports & Analytics | ⬜ Not Started | — |
| 8 | Webhooks, Polish & Deploy | ⬜ Not Started | — |

Status: ⬜ Not Started | 🔄 In Progress | ✅ Completed | ❌ Blocked

## Current Phase Detail

### Steps Completed
### Steps In Progress
### Steps Remaining
### Decisions Made
### Issues / Blockers
### Test Results
- pytest: X passed, 0 failed. Coverage: X%
- pnpm tsc --noEmit: 0 errors
- pnpm lint: 0 warnings
```

---

## Phase Dependency Chain

```
Phase 0 (Setup)
    ↓
Phase 1 (Auth + Landing)
    ↓
Phase 1.5 (Super Admin Backend)
    ↓
Phase 2 (Workspace & Members)
    ↓
Phase 3 (Projects, Tasks, Clients, Tags)
    ↓
Phase 4 (Time Tracking Core) ← most complex
    ↓
Phase 5 (Continue, Duplicate & Draft)
    ↓
Phase 6 (Approvals & Notifications)
    ↓
Phase 7 (Reports & Analytics)
    ↓
Phase 7.5 (Super Admin UI Dashboard)
    ↓
Phase 8 (Webhooks, Polish & Deploy)
    ↓
MVP Complete
    ↓
Flutter app (separate plan, post-MVP)
```

Each phase is strictly sequential. Never start Phase N+1 until Phase N
passes 100% of its testing checklist and is explicitly approved.
