# ORBIT — Development Rules & Constraints

## Project Identity

**ORBIT is my ORIGINAL APOGEE application under a new name.**

It must **never** be merged with:
- The older ORBIT prototype (separate repository)
- The experimental APOGEE + ORBIT merged project (separate repository)

This codebase (`/Users/aaminahasan/Desktop/apogeenew/skillpath`) is the **single source of truth** for the hackathon submission.

---

## Git & Version Control

| Rule | Enforcement |
|------|-------------|
| Never force-push to `main` | `git push --force` blocked |
| Never rebase shared history | Use merge commits |
| Preserve all databases | `backend/apogee.db` untracked, never reset |
| `.env` never committed | In `.gitignore` |
| Commit messages: `feat:`, `fix:`, `docs:`, `refactor:` | Conventional commits |

### Current Branch State
- Branch: `main`
- Status: Diverged from `origin/main` (3 local, 1 remote commits)
- Remotes: `origin` → `github.com/aamina15/apogee`, `frontendapogee` → separate repo

---

## Code Quality Standards

### Backend (Python)
- **Python 3.9+** (3.9.6 in venv)
- **Pydantic v2** — use `model_config = {...}` not `class Config`
- **SQLAlchemy 2.0** — `declarative_base()` from `sqlalchemy.orm`
- **Type hints** on all public functions
- **Pytest** — 43 tests must pass
- **No raw exceptions in API responses** — global handler returns `{"detail": "We could not complete that request. Please try again."}`

### Frontend (React + TypeScript-ready)
- **ESLint (oxlint)** — 77 warnings allowed, 0 errors
- **No `any` types** — use proper interfaces
- **React hooks exhaustive-deps** — warn but don't block
- **Dark theme only** — CSS custom properties in `index.css`
- **Tailwind** — utility classes, custom design tokens in `tailwind.config.js`

### Design System (Preserved)
| Token | Value |
|-------|-------|
| Primary | Indigo (`#4F46E5`) |
| Secondary | Cyan (`#4CD7F6`) |
| Tertiary | Emerald (`#4EDEA3`) |
| Surface | `#0F131D` (dark) |
| Font: Headline | Plus Jakarta Sans |
| Font: Body | Inter |
| Radius | `rounded-xl` (12px) default |

---

## API Contracts (Immutable)

### Response Envelope
All endpoints return data directly (no envelope). Errors:
```json
{ "detail": "Human-readable message" }  // 4xx/5xx
```

### Critical Invariants
1. **`graph_source`** ∈ `{"gemini", "fallback"}` — never null after graph generation
2. **`verified`** only set via `POST /verify` — public mastery endpoints reject it (422)
3. **Route versions** monotonically increase; `route_json` stores full snapshot
4. **Diagnostic questions** never expose `correct_index` or `explanation`
5. **Verification questions** never expose `correct_index` or `explanation`

---

## Database Rules

| Table | Constraint |
|-------|------------|
| `goals` | `status` ∈ `{"active", "completed", "archived"}` |
| `skills` | `slug` unique per goal (for resource lookup) |
| `mastery` | `verified` = `verification_score ≥ 0.70` (enforced by state engine) |
| `routes` | `version` auto-increment per goal |
| `diagnostic_questions` | `skill_slug` = `"verif_{skill_id}"` for verification questions |

---

## Testing Rules

### Backend Tests (43 total)
```bash
cd backend && source .venv/bin/activate && python -m pytest tests/ -v
```
**Must pass:**
- 19 acceptance journey checks
- 6 DAG validator tests
- 2 diagnostic tests
- 2 generate-graph tests
- 3 resource tests
- 3 security acceptance tests
- 7 state engine tests

### Frontend Tests
- No unit test framework configured (manual browser testing)
- Production build must succeed: `npm run build`
- Lint must pass: `npm run lint` (0 errors)

---

## Gemini Integration Rules

| Rule | Implementation |
|------|----------------|
| Never log API key | `test_gemini_failures_do_not_log_credentials` asserts |
| Timeout | 60s (increased from 15s for 3.5 Flash) |
| Model | `gemini-3.5-flash` (stable as of 2026) |
| Fallback | Deterministic, curated, honest (`source: "fallback"`) |
| Retry | None (fail fast → fallback); exponential backoff = future work |

---

## Deployment Constraints

### Hackathon (Oct 3, 2026)
- Single-user demo on localhost
- SQLite database
- No authentication required
- Backend + frontend on same machine

### Production (Post-Hackathon)
- **Add authentication first** (Cognito + JWT authorizer)
- Migrate to PostgreSQL
- Add user_id to Goal, scope all queries
- HTTPS + CORS tightening
- Rate limiting on `/generate-graph`, `/verify`

---

## Forbidden Patterns

```python
# ❌ Never do this in backend
mastery.verified = True  # outside verification endpoint
mastery.verification_score = 1.0  # outside verification endpoint

# ❌ Never do this in frontend
localStorage.setItem('verified', 'true')  # no client-side verification

# ❌ Never commit
.env
*.db
__pycache__/
node_modules/
dist/
```

---

## Change Control

### Safe Changes (No Approval Needed)
- Bug fixes with test coverage
- Documentation updates
- Lint cleanup
- CSS/theme tweaks within design system

### Requires Explicit Approval
- Schema migrations (Alembic)
- New API endpoints
- Authentication integration
- Database engine changes
- External service dependencies

---

## Emergency Procedures

### Backend Won't Start
1. Check port 8000: `lsof -ti:8000 | xargs kill -9`
2. Verify `.venv` active: `source .venv/bin/activate`
3. Check `.env` exists with `GEMINI_API_KEY`

### Database Corrupted
1. `cp backend/apogee.db backend/apogee.db.backup`
2. Restore from backup or re-run `Base.metadata.create_all()`

### Gemini 503 Spam
1. Stop retrying — fallback is working
2. Check quota in Google Cloud Console
3. Document as "temporarily unavailable" in demo