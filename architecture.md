# ORBIT — Technical Architecture

## System Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                        ORBIT Application                            │
├─────────────────────────────────────────────────────────────────────┤
│  Frontend (React + Vite)         │  Backend (FastAPI + SQLite)      │
│  ──────────────────────────      │  ────────────────────────────    │
│  • Header (nav, API status)      │  • REST API (/api/*)             │
│  • IntakeScreen (goal form)      │  • AI Service (Gemini + Fallback)│
│  • DiagnosticQuizModal           │  • DAG Validator (Kahn's algo)   │
│  • RouteScreen (phased timeline) │  • State Engine (4-state rules)  │
│  • CompletionGraph (SVG DAG)     │  • Resource Catalogue            │
│  • ProofOfSkillModal (verification)│  • Route Planner (topological) │
│  • CalendarRePlanModal           │  • Persistence (SQLAlchemy)      │
│  • CareerPackModal (export)      │  • Health Check                  │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Frontend Architecture

### Tech Stack
- **React 18** + **Vite 5** — fast dev server, optimized production build
- **Tailwind CSS** — utility-first styling with custom design tokens
- **Lucide React** — consistent icon system
- **Canvas Confetti** — verification celebration

### State Management
- **React useState/useEffect** — all local component state
- **App.jsx** — single source of truth for:
  - `goal` (active goal from backend)
  - `graph` (skill DAG + validation metadata)
  - `step` (1: Intake → 2: Diagnostic → 3: Route → 4: Career Pack)
  - `userState` (readiness band, profile, UI preferences)
  - `apiStatus` (online/offline/connecting)

### Data Flow
```
User Action → API Call → Backend → SQLite → Response → Frontend State → UI Update
```

### Key Components

| Component | Responsibility |
|-----------|----------------|
| `Header` | Navigation (4 steps), API status, brand, user profile |
| `IntakeScreen` | Goal form validation, quick-start profiles |
| `DiagnosticQuizModal` | Fetch questions, collect answers, submit for grading |
| `CompletionGraph` | SVG DAG rendering, node inspection, prerequisite visualization |
| `RouteScreen` | Phased timeline, resource cards, verify buttons, feasibility |
| `ProofOfSkillModal` | Verification quiz, grading receipt, confetti on pass |
| `CalendarRePlanModal` | Hours input, replan preview, version diff, apply |
| `CareerPackModal` | PDF-ready credential export with readiness band |

### API Client (`src/services/api.js`)
- Single `apiFetch` wrapper with 30s timeout
- Friendly error messages (no stack traces)
- All endpoints typed with JSDoc

---

## Backend Architecture

### Tech Stack
- **FastAPI** — async, auto OpenAPI docs, Pydantic validation
- **SQLAlchemy 2.0** — ORM with declarative models
- **SQLite** (dev) / **PostgreSQL** (prod-ready)
- **httpx** — async HTTP client for Gemini API
- **Pydantic v2** — settings, request/response models

### Project Structure
```
backend/
├── config.py           # Settings (Pydantic BaseSettings)
├── main.py             # FastAPI app, CORS, routers, error handler
├── db/
│   └── database.py     # Engine, SessionLocal, lock_goal_write
├── models/
│   ├── goal.py         # Goal + graph_source/warning/validation
│   ├── skill.py        # Skill (slug for resource lookup)
│   ├── mastery.py      # Mastery (diagnostic/verification scores)
│   ├── route.py        # Route versions (JSON blob + metadata)
│   ├── diagnostic.py   # Questions (separate namespaces for diag/verify)
│   └── resource.py     # Resource catalogue entries
├── routes/
│   ├── goals.py        # CRUD + /active (single-user global)
│   ├── graph.py        # generate-graph, get-graph (state engine)
│   ├── diagnostic.py   # get/submit diagnostic, mastery persistence
│   ├── verification.py # fetch questions, submit verification
│   ├── routes.py       # build route, replan, version history
│   └── mastery.py      # CRUD (diagnostic_score only)
├── services/
│   ├── ai_service.py   # Gemini + deterministic fallback
│   ├── crud.py         # Database operations
│   ├── dag_validator.py# Kahn's algorithm (cycle detection/repair)
│   ├── diagnostic_service.py # Question generation/grading
│   ├── resource_service.py   # Catalogue lookup + creation
│   └── state_engine.py # 4-state deterministic rules
└── tests/
    ├── test_acceptance.py      # 19 journey checks + failure paths
    ├── test_security_acceptance.py # Verification bypass, isolation
    ├── test_dag_validator.py
    ├── test_diagnostic.py
    ├── test_generate_graph.py
    ├── test_resources.py
    └── test_state_engine.py
```

### Database Schema (ER Diagram)

```
Goal (1) ──< Skill (N)
Skill (1) ──< SkillDependency (N) ──> Skill (M)  [prerequisite → dependent]
Goal (1) ──< Mastery (N) >── Skill (1)
Goal (1) ──< Route (N)        [versioned JSON snapshots]
Goal (1) ──< DiagnosticQuestion (N)  [diag + verify namespaces]
Skill (1) ──< Resource (N)
```

---

## Core Algorithms

### 1. DAG Validation & Repair (`dag_validator.py`)
```
Input: skills[], dependencies[]
Process:
  1. Build adjacency list + indegree map
  2. Kahn's algorithm: queue zero-indegree nodes
  3. If processed < total → cycle exists
  4. Repair: drop edges creating cycles (greedy, preserve max edges)
Output: { skills, dependencies, validation: { acyclic, repaired, ... } }
```

### 2. State Engine (`state_engine.py`) — **Deterministic Rules**
```
For each skill (iterative until stable):
  1. If mastery.verified == True → VERIFIED
  2. Else if mastery.in_progress AND all prereqs VERIFIED → IN_PROGRESS
  3. Else if NO prerequisites → AVAILABLE
  4. Else if ALL prerequisites VERIFIED → AVAILABLE
  5. Else → LOCKED

CRITICAL: Multiple prerequisites → skill stays LOCKED until ALL are VERIFIED
```

### 3. Route Planner (`routes.py`)
```
Input: skills (topo order), masteries, resources, hours_per_week
Process:
  1. Topological sort (Kahn) → ordered skill IDs
  2. For each skill: hours = 0 if VERIFIED else resource.duration_hours
  3. Accumulate elapsed hours → start_hour, end_hour
  4. total_weeks = ceil(elapsed / hours_per_week)
  5. feasible = elapsed ≤ (hours_per_week × duration_weeks) AND no missing resources
Output: { phases, total_hours, total_weeks, feasible, feasibility_message }
```

### 4. Replanning (`routes.py`)
```
POST /api/goals/{id}/replan { hours_per_week }
  1. Lock goal write (SQLite: BEGIN IMMEDIATE)
  2. Build new route with new hours_per_week
  3. Save as new version (v+1)
  4. Update goal.hours_per_week
  5. Return receipt: preserved_verified, rescheduled, diff
Rollback on any failure (atomic)
```

---

## Gemini Integration (`ai_service.py`)

### Request Flow
```
generate_skill_dag_with_gemini(goal_title, hpw, weeks, budget)
  1. Read GEMINI_API_KEY from settings
  2. If empty → return fallback immediately (no HTTP call)
  3. Build prompt with goal context + strict JSON schema
  4. POST https://generativelanguage.googleapis.com/v1beta/models/gemini-3.5-flash:generateContent
  5. Parse JSON → validate with Pydantic (GeminiDAGResponse)
  6. Return { source: "gemini", warning: null, skills, dependencies }
  7. On ANY error (503, timeout, malformed) → fallback + warning
```

### Fallback Generator
- **Frontend goals** → 6 skills (HTML/CSS → JS → React → State/TS/Testing)
- **ML goals** → 6 skills (Python → Math → Data → Sklearn → DL → MLOps)
- **Generic** → 5 skills (Foundations → Core → Projects → Advanced → Capstone)
- Always returns `{ source: "fallback", warning: "AI generation unavailable..." }`

---

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Health check |
| POST | `/api/goals` | Create goal |
| GET | `/api/goals` | List all goals |
| GET | `/api/goals/active` | Get latest active goal (global) |
| GET | `/api/goals/{id}` | Get goal by ID |
| PATCH | `/api/goals/{id}` | Update goal |
| POST | `/api/goals/{id}/generate-graph` | Generate + persist skill DAG |
| GET | `/api/goals/{id}/graph` | Get graph with computed states |
| POST | `/api/goals/{id}/diagnostic` | Generate diagnostic questions |
| POST | `/api/goals/{id}/diagnostic/submit` | Grade + persist mastery |
| GET | `/api/goals/{id}/diagnostic/mastery` | Get saved diagnostic scores |
| POST | `/api/goals/{id}/skills/{skill_id}/verification` | Get verification questions |
| POST | `/api/goals/{id}/skills/{skill_id}/verify` | Grade verification quiz |
| GET | `/api/goals/{id}/route` | Get/build current route |
| POST | `/api/goals/{id}/replan` | Change hours/week → new version |
| GET | `/api/goals/{id}/routes` | List all route versions |
| GET | `/api/goals/{id}/routes/latest` | Get latest stored route |

---

## Security Model

### Verification Bypass Prevention
- `MasteryCreate` schema: ONLY `goal_id`, `skill_id`, `diagnostic_score` (`extra="forbid"`)
- `MasteryUpdate` schema: ONLY `diagnostic_score`
- `verified` and `verification_score` **rejected with 422** on public endpoints
- Verification ONLY via `POST /verify` with server-side grading

### Known Limitation: Single-User Active Goal
- `GET /api/goals/active` returns globally most recent active goal
- **No session/user isolation** — unsafe for multi-user deployment
- Requires authentication (Cognito/JWT) + `user_id` on Goal before production

---

## Deployment

### Development
```bash
# Backend
cd backend && source .venv/bin/activate && python main.py  # :8000

# Frontend
npm run dev  # :5173 (proxies to :8000 via Vite config)
```

### Production Build
```bash
npm run build  # → dist/ (static assets)
# Serve dist/ via nginx + FastAPI on :8000 (or same origin)
```

### Environment Variables
```bash
# backend/.env
DATABASE_URL=sqlite:///./apogee.db  # or postgresql+psycopg2://...
GEMINI_API_KEY=your_key_here
```

---

## Monitoring & Observability
- Health endpoint: `GET /health`
- Structured logging (Python `logging` module)
- No APM/telemetry integrated (future work)