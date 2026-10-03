# ORBIT

ORBIT is an AI-assisted skill intelligence and learning navigator. A learner defines a goal, receives a validated prerequisite skill graph, completes a goal-aware diagnostic, and follows a personalized learning route with persisted progress and skill verification.

This repository contains:

- A React 19 and Vite frontend intended for Vercel.
- A FastAPI and SQLAlchemy backend intended for Render.
- PostgreSQL support for production and SQLite for local development.
- OpenAI as the primary AI provider, with Gemini failover and deterministic fallbacks.

## Core workflow

1. Create or resume a learning goal.
2. Generate a prerequisite skill graph.
3. Validate and repair the graph before it is persisted.
4. Run a goal-aware diagnostic without exposing answer keys to the browser.
5. Build a learning route from skill state, mastery, time, and budget.
6. Verify skills through server-graded assessments and unlock dependents.
7. Replan the route while retaining learner progress.

## AI provider strategy

OpenAI is the default provider for skill-graph generation and assessment-question proposals. Provider output is validated before it can enter the application.

```text
OpenAI -> Gemini -> deterministic fallback
```

Set `AI_PROVIDER=gemini` to prefer Gemini while retaining OpenAI as the secondary provider. Set `AI_PROVIDER=fallback` to disable external model calls and use deterministic content only.

Provider failures do not prevent the learner from continuing:

- Invalid OpenAI output falls through to Gemini.
- Invalid Gemini output falls through to the deterministic graph or curated question bank.
- Graphs pass through deterministic DAG validation and cycle repair.
- Question proposals pass through schema, relevance, duplicate, and answer-key validation.

The historical backend function name `generate_skill_dag_with_gemini` is intentionally retained for route and test compatibility, even though it now runs the provider chain.

## Technology

### Frontend

- React 19
- Vite 8
- Tailwind CSS 4
- Lucide React
- Oxlint

### Backend

- FastAPI
- Pydantic 2
- SQLAlchemy 2
- HTTPX
- PostgreSQL through psycopg/psycopg2
- SQLite for local development
- Pytest

The OpenAI and Gemini integrations use the existing HTTPX client. No OpenAI SDK is required.

## Repository layout

```text
.
├── src/                       React application
│   ├── components/            Learner workflow and visualization components
│   ├── services/api.js        Centralized backend API client
│   └── App.jsx                Application workflow and navigation
├── backend/
│   ├── main.py                FastAPI application and CORS setup
│   ├── config.py              Runtime and AI-provider settings
│   ├── db/                    SQLAlchemy engine and sessions
│   ├── models/                Persistence models
│   ├── routes/                HTTP endpoints
│   ├── services/              AI, validation, assessment, and state logic
│   └── tests/                 Backend regression and provider tests
├── package.json
└── vite.config.js
```

## Local development

### Prerequisites

- Node.js and npm compatible with Vite 8
- Python 3.9 or newer

### Install the frontend

From the repository root:

```bash
npm ci
```

### Install the backend

```bash
python3 -m venv backend/.venv
source backend/.venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r backend/requirements.txt
```

### Configure the backend

Create `backend/.env` for local-only values. Environment files are ignored by Git and must never be committed.

```dotenv
AI_PROVIDER=openai
OPENAI_API_KEY=
OPENAI_MODEL=gpt-4o-mini

GEMINI_API_KEY=
GEMINI_MODEL=gemini-3.5-flash

# Optional. SQLite is used when DATABASE_URL is omitted.
DATABASE_URL=sqlite:///./apogee.db

CORS_ORIGINS=["http://localhost:5173","http://127.0.0.1:5173"]
```

The application works without either provider key by using deterministic and curated fallbacks.

### Run the backend

Run FastAPI from the backend directory so local imports and `backend/.env` resolve consistently:

```bash
cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

- Health check: `http://localhost:8000/health`
- Interactive API documentation: `http://localhost:8000/docs`

### Run the frontend

In another terminal, from the repository root:

```bash
npm run dev
```

The frontend uses `http://localhost:8000` by default. To use another backend, create a local frontend environment file:

```dotenv
VITE_API_BASE_URL=http://localhost:8000
```

## Environment variables

### Backend

| Variable | Required | Default | Purpose |
| --- | --- | --- | --- |
| `AI_PROVIDER` | No | `openai` | Preferred provider: `openai`, `gemini`, or `fallback` |
| `OPENAI_API_KEY` | For OpenAI calls | Empty | Server-side OpenAI credential |
| `OPENAI_MODEL` | No | `gpt-4o-mini` | OpenAI model used for graph and question generation |
| `GEMINI_API_KEY` | For Gemini calls | Empty | Server-side Gemini credential |
| `GEMINI_MODEL` | No | `gemini-3.5-flash` | Gemini model used for graph and question generation |
| `DATABASE_URL` | Production | SQLite URL | PostgreSQL or SQLite database connection |
| `CORS_ORIGINS` | Production | Local Vite origins | JSON array of allowed frontend origins |
| `HOST` | No | `0.0.0.0` | Backend bind address |
| `PORT` | No | `8000` | Backend port; Render normally supplies this |

### Frontend

| Variable | Required | Default | Purpose |
| --- | --- | --- | --- |
| `VITE_API_BASE_URL` | Production | `http://localhost:8000` | Public Render backend URL used by the browser |

Never expose `OPENAI_API_KEY`, `GEMINI_API_KEY`, or `DATABASE_URL` through a `VITE_` variable. Vite variables are included in the browser bundle.

## Deployment

### Render backend

Create a Python web service with `backend` as its root directory.

- Build command: `pip install -r requirements.txt`
- Start command: `uvicorn main:app --host 0.0.0.0 --port $PORT`
- Health-check path: `/health`

Configure these Render environment variables:

```text
AI_PROVIDER=openai
OPENAI_API_KEY=<server-side secret>
OPENAI_MODEL=gpt-4o-mini
GEMINI_API_KEY=<optional server-side fallback secret>
GEMINI_MODEL=gemini-3.5-flash
DATABASE_URL=<Render PostgreSQL internal URL>
CORS_ORIGINS=["https://your-vercel-project.vercel.app"]
```

For preview or custom Vercel domains, add every trusted origin to the JSON array. Do not use a wildcard when credentials are enabled.

### Vercel frontend

Deploy the repository root as a Vite project.

- Install command: `npm ci`
- Build command: `npm run build`
- Output directory: `dist`

Set the frontend environment variable:

```text
VITE_API_BASE_URL=https://your-render-service.onrender.com
```

Do not include a trailing slash because API paths already begin with `/`.

## Testing and quality checks

Provider tests mock HTTP responses and do not make paid OpenAI or Gemini requests.

Run the backend suite with provider credentials explicitly blanked:

```bash
cd backend
AI_PROVIDER=openai OPENAI_API_KEY='' GEMINI_API_KEY='' python -m pytest -q
```

Run frontend checks from the repository root:

```bash
npm run build
npm run lint
```

The provider regression coverage includes:

- OpenAI success and provider attribution.
- OpenAI failure or malformed output falling through to Gemini.
- Provider failure falling through to deterministic content.
- Credential non-leakage in logs.
- AI question validation and curated-bank fallback.

## Security and data integrity

- API keys remain in the backend environment and are never sent to the frontend.
- Diagnostic and verification answer keys remain server-side.
- Assessment submission is graded by the backend.
- AI output is untrusted until it passes application validation.
- Graph output passes deterministic DAG validation before persistence.
- Learner progress and graph metadata are persisted in the database.
- Existing routes and database schemas are shared across AI and fallback flows.
- `.env` files, build output, and dependency directories are ignored by Git. Local SQLite databases must also remain uncommitted.

## Useful commands

```bash
# Frontend development
npm run dev

# Frontend production build
npm run build

# Frontend lint
npm run lint

# Backend development
cd backend && uvicorn main:app --reload

# Backend tests without external provider calls
cd backend && AI_PROVIDER=openai OPENAI_API_KEY='' GEMINI_API_KEY='' python -m pytest -q
```
