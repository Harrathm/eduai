# EDUAI Learning Platform

A full-stack e-learning platform with multi-tenant architecture, AI-powered tutoring, dual-currency economy (TOKEN + DT), course authoring, and governance features (ABAC, impersonation, CMS lifecycle, bulk seats, revenue share).

## Architecture

```
RAG_APP_new/
├── backend/          # FastAPI + SQLAlchemy + PostgreSQL
│   ├── app/
│   │   ├── routers/   # API endpoints
│   │   ├── models/    # SQLAlchemy models
│   │   ├── schemas/   # Pydantic schemas
│   │   ├── services/  # Business logic
│   │   ├── ai/        # OpenAI embeddings & RAG
│   │   └── core/      # Config, auth, middleware
│   ├── tests/         # pytest (30 tests)
│   └── .venv/         # Python virtual environment
└── frontend/          # React 18 + TypeScript + Vite
    ├── src/
    │   ├── features/  # Admin, Auth, Learner, Teacher, Student
    │   ├── api/       # API clients
    │   ├── store/     # Zustand stores
    │   └── test/      # vitest tests (29 tests)
    └── dist/          # Production build
```

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.11+, FastAPI 0.109+, SQLAlchemy 2.0, Pydantic v2 |
| Database | PostgreSQL 15+ |
| Frontend | React 18, TypeScript 6, Vite 5, TailwindCSS 3 |
| State | Zustand 4 |
| Testing | pytest (backend), vitest + Testing Library (frontend) |
| AI | OpenAI API (embeddings + chat completions) |
| Auth | JWT (HS256), bcrypt password hashing |

## Quick Start (Development)

### Prerequisites
- Python 3.11+
- Node.js 18+
- PostgreSQL 15+
- pnpm (recommended) or npm

### Backend

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate  # Windows
pip install -r requirements.txt

# Copy and configure environment
cp .env.example .env
# Edit .env with your PostgreSQL URL and secrets

# Run database migrations
python -m alembic upgrade head

# Start development server
python -m uvicorn app.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install

# Create .env.local
echo "VITE_API_URL=http://localhost:8000" > .env.local

npm run dev
```

### Run Tests

```bash
# Backend
cd backend
.venv\Scripts\activate
python -m pytest tests/ -v

# Frontend
cd frontend
npm run test:run
```

## Environment Variables

### Backend (.env)
| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | Required |
| `JWT_SECRET` | JWT signing key (min 32 chars in prod) | Auto-generated (dev) |
| `ENVIRONMENT` | `development`, `staging`, `production` | `development` |
| `CORS_ORIGINS` | Allowed CORS origins (comma-separated) | `http://localhost:5173` |
| `OPENAI_API_KEY` | OpenAI API key for AI features | Required for AI |
| `STRIPE_SECRET_KEY` | Stripe key for payments | Optional |

### Frontend (.env.local)
| Variable | Description | Default |
|----------|-------------|---------|
| `VITE_API_URL` | Backend API URL | `http://localhost:8000` |

## Deployment (Docker)

### Docker Compose

```bash
# Build and start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop
docker-compose down
```

Services:
- `postgres`: PostgreSQL 15 (port 5432)
- `backend`: FastAPI app (port 8000)
- `frontend`: Nginx serving React app (port 80)

### Manual Production Deploy

```bash
# Backend
cd backend
pip install -r requirements.txt
python -m alembic upgrade head
gunicorn -w 4 -k uvicorn.workers.UvicornWorker app.main:app --bind 0.0.0.0:8000

# Frontend
cd frontend
npm install
npm run build
# Serve dist/ with Nginx/Caddy
```

## API Routes

### Public
- `GET /` — Health check
- `POST /api/auth/login` — JWT login
- `POST /api/auth/register` — User registration
- `GET /api/catalog/courses` — Browse courses (paginated)

### Authenticated (Learner)
- `GET /api/learner/courses` — My enrolled courses
- `GET /api/learner/courses/:id` — Course detail
- `POST /api/learner/courses/:id/enroll` — Enroll in course
- `GET /api/learner/courses/:id/certificate` — Get/download certificate
- `POST /api/learner/lessons/:id/progress` — Update progress
- `POST /api/learner/quizzes/:id/start` — Start quiz
- `POST /api/learner/quizzes/:id/submit` — Submit quiz answers

### Admin (super_admin)
- `GET/POST/PATCH/DELETE /api/admin/courses` — Course CRUD
- `GET/POST/PATCH/DELETE /api/admin/courses/:id/chapters` — Chapter CRUD
- `GET/POST/PATCH/DELETE /api/admin/lessons` — Lesson CRUD
- `GET/POST/PATCH/DELETE /api/admin/quizzes` — Quiz CRUD
- `GET /api/admin/users` — User management (paginated)
- `GET /api/admin/schools` — School management
- `GET /api/admin/analytics` — Platform analytics
- `GET /api/admin/audit-logs` — Audit trail

### LMS
- `GET/POST/DELETE /api/lms/classes` — Classroom management
- `GET /api/lms/enrollments` — Enrollment tracking
- `GET /api/lms/assignments` — Assignments

## Role System

| Role | Access |
|------|--------|
| `student` | Enrolled courses, quizzes, certificates |
| `teacher` | Classroom management, enrolled students |
| `admin_school` | School-scoped admin (courses, users, analytics) |
| `pedagogical_lead` | School-scoped pedagogical approval, learning goals |
| `pedagogical_admin` | Global pedagogical review, B2B approval, AI Factory |
| `super_admin` | Global admin (all schools, settings, audit logs) |
| `parent` | Read-only: children's progress tracking |

### Governance Features (Planned)
- **Context Switcher**: Multi-role users switch roles without re-login
- **Impersonation**: Support agents enter user sessions (max 30min, full audit)
- **ABAC Engine**: Attribute-based policies (role + school + tier + time)
- **CMS Lifecycle**: Brouillon → Soumission → Validation IA → Validation Humaine → Publication → Archivage
- **AI Factory Atomization**: Generate single lessons/quizzes/chapters independently
- **Versioning / Fork**: Course versioning with rollback capability
- **Bulk Seats**: Schools purchase multiple seats in bulk
- **Revenue Share Ledger**: Automatic teacher revenue calculation per sale

## Multi-Tenancy

- Each `School` has isolated data (users, courses, transactions)
- All queries scoped by `school_id` automatically
- `super_admin` can access any school via `x-school-id` header

## Dual-Economy

- **TOKEN**: In-platform currency for course purchases
- **DT**: Real monetary balance for withdrawals/revenue share

Teachers earn DT from course sales (configurable revenue share %).

## Database Indexes

Key composite indexes for performance:
- `(school_id, role)` on users
- `(student_id, course_id)` on enrollments (unique)
- `(course_id, status)` on courses
- `(chapter_id, order_index)` on lessons

## Test Coverage

- **Backend**: 30 pytest tests (admin CRUD, auth, CORS, health)
- **Frontend**: 29 vitest tests (LoginPage, CourseCatalog, MyLearning)

Run with: `npm run test:run` (frontend) or `pytest` (backend)

## Known Deprecations

- Python 3.12+ emits warnings for `datetime.utcnow()` — resolved via custom `utcnow()` helper using `datetime.now(timezone.utc)`
- SQLAlchemy 2.x emits warnings for naive datetime defaults — use timezone-aware `utcnow()` helper

## License

Proprietary — EDUAI Learning Platform# eduai
