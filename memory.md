# ORBIT — Project Memory & Context

## Project Identity

**ORBIT is my ORIGINAL APOGEE application under a new name.**

This codebase (`/Users/aaminahasan/Desktop/apogeenew/skillpath`) is the **single source of truth** for the hackathon submission.

It must **never** be merged with:
- The older ORBIT prototype (separate repository, different codebase)
- The experimental APOGEE + ORBIT merged project (separate repository, different codebase)

---

## Key Decisions & Rationale

| Decision | Date | Rationale |
|----------|------|-----------|
| Rename APOGEE → ORBIT | Oct 2, 2026 | Hackathon branding; tagline "Your Goal. Your Path. Your ORBIT." |
| Keep internal `apogee` identifiers | Oct 2, 2026 | Avoid breaking changes; database tables, package names unchanged |
| SQLite for dev, PostgreSQL-ready | Sep 2026 | Zero-config local dev; prod migration path exists |
| Single-user `/api/goals/active` | Sep 2026 | MVP scope; auth = post-hackathon blocker |
| Gemini 3.5 Flash model | Oct 1, 2026 | Stable, supports JSON mode, 1M token context |
| Deterministic fallback graphs | Sep 2026 | Honest UX when API unavailable; curated per domain |
| 4-state skill engine (LOCKED→AVAILABLE→IN_PROGRESS→VERIFIED) | Sep 2026 | Clear mental model; all-prereqs rule prevents gaps |
| Route versioning (immutable snapshots) | Sep 2026 | Replan audit trail; verified progress preservation |
| 70% verification threshold | Sep 2026 | Standard mastery bar; configurable later |

---

## Architecture Memory

### Database Evolution
```
Initial: goals, skills, skill_dependencies, mastery
+ graph_source, graph_warning, graph_validation (migration in main.py)
+ route versions table (route_json blob)
+ diagnostic_questions (dual namespace: diag + verif_)
```

### Critical Invariants (Must Never Break)
1. **Verification bypass impossible** — `verified` only set by `POST /verify` with server grading
2. **Graph source honesty** — Always `"gemini"` or `"fallback"`, never null after generation
3. **Prerequisite AND logic** — Skill unlocks ONLY when ALL prereqs are VERIFIED
4. **Replan atomicity** — SQLite `BEGIN IMMEDIATE` + rollback on failure
5. **No client-side secrets** — API key only in backend `.env`, never in frontend

---

## Gemini Integration History

| Date | Event |
|------|-------|
| Sep 2026 | Initial integration with `gemini-2.5-flash` |
| Oct 1, 2026 | Migrated to `gemini-3.5-flash` (2.5 deprecated for new users) |
| Oct 1, 2026 | Increased timeout 15s → 60s for 3.5 Flash |
| Oct 1, 2026 | Added response logging for debugging 503s |
| Oct 2, 2026 | API key configured in `backend/.env` |
| Oct 2, 2026 | **Live generation confirmed** — Goal 132 "Learn Rust" → `source: "gemini"` |
| Oct 2, 2026 | Intermittent 503 Service Unavailable (Google capacity) |

### Working Prompt Template
```
You are ORBIT's Skill Graph AI Architect.
Generate a concise, structured prerequisite Skill Graph (DAG) for a learner's goal:
- Goal Title: "{goal_title}"
- Weekly Time Commitment: {hours_per_week} hours/week
- Target Horizon: {duration_weeks} weeks
- Budget: ${budget}

REQUIREMENTS:
1. Provide between 5 and 10 essential skills necessary to master this goal.
2. Provide directed prerequisite dependencies between skills (from -> to).
3. "from" is the prerequisite skill ID, and "to" is the dependent skill ID.
4. Keep skill IDs short, clean, and lowercase snake_case (e.g. "python", "html_css", "pytorch").
5. The graph must be an ACYCLIC directed graph (no cycles!).

Respond ONLY with JSON matching this exact structure:
{
  "skills": [
    {
      "id": "python",
      "name": "Python Fundamentals",
      "target_level": "Proficient",
      "importance": 0.9
    }
  ],
  "dependencies": [
    {
      "from": "python",
      "to": "pytorch"
    }
  ]
}
```

---

## Test Results Memory

### Backend (43 tests, all passing)
```
test_acceptance.py              19 tests  ✅ Journey + failure paths
test_security_acceptance.py      3 tests  ✅ Verification bypass, isolation
test_dag_validator.py            6 tests  ✅ Kahn's algorithm + repair
test_diagnostic.py               2 tests  ✅ Generation + grading
test_generate_graph.py           2 tests  ✅ Endpoint + fallback
test_resources.py                3 tests  ✅ Catalogue + missing
test_state_engine.py             7 tests  ✅ 4-state rules
```

### Frontend
- Production build: ✅ 318 kB gzipped JS
- Lint: 77 warnings (unused imports), 0 errors
- Dev server: ✅ Hot reload working

### Manual Browser Journey (Verified Oct 2)
1. Create goal "Learn Rust" (10h/wk, 8wks) → ID 132
2. Generate graph → `source: "gemini"`, 8 skills, 9 deps, acyclic
3. Diagnostic → 10 questions, submit → 5 mastery records
4. Graph states → HTML/CSS `IN_PROGRESS`, others `LOCKED`
5. Route → 61h total, feasible at 10h/wk (7 weeks)
6. Verify HTML/CSS → 5/5 correct → `VERIFIED`, confetti
7. Graph refresh → JavaScript `IN_PROGRESS` (unlocked)
8. Replan 4h/wk → v2 route, 16 weeks, infeasible reported
9. Browser refresh → All state preserved
10. Backend restart → All state preserved

---

## Known Limitations (Documented for Demo)

| Limitation | Impact | Mitigation |
|------------|--------|------------|
| No authentication | Multi-user unsafe | Demo is single-user only |
| Gemini 503 intermittent | May show fallback | Honest badge: "AI generation unavailable" |
| Diagnostic covers 5/6 skills | One skill untested | Acceptable for MVP |
| Resource hours estimated | Not measured completion | Documented in UI |
| 77 lint warnings | Code hygiene only | Non-blocking |
| Python deprecation warnings | SQLAlchemy/Pydantic v2 | Upgrade post-hackathon |

---

## File Ownership Map

| Area | Files | Owner |
|------|-------|-------|
| Frontend components | `src/components/*.jsx` | React |
| Frontend services | `src/services/api.js` | API client |
| Frontend data | `src/data/mockData.js` | Static profiles |
| Backend config | `backend/config.py`, `backend/.env` | Settings |
| Backend models | `backend/models/*.py` | SQLAlchemy |
| Backend routes | `backend/routes/*.py` | FastAPI endpoints |
| Backend services | `backend/services/*.py` | Business logic |
| Backend tests | `backend/tests/*.py` | Pytest suites |
| Database | `backend/apogee.db` | SQLite (dev) |
| Documentation | `*.md` | This session |

---

## Hackathon Demo Context

**Date:** October 3, 2026
**Format:** Live demo + submission
**Duration:** ~3 minutes
**Environment:** Localhost (backend :8000, frontend :5173)

### Demo Account State (As of Oct 2)
- Active goal: ID 132 "Learn Rust Programming" (gemini graph)
- Previous goals: 131 "Learn Go Programming" (fallback), 95 "Frontend Developer Internship" (fallback, verified skills)
- Database: `backend/apogee.db` (95+ goals, 500+ skills, 1000+ masteries)

### Demo Flow (Memorized)
```
1. Intake: "Frontend Developer Internship" → 7h/wk, 8wks, free
2. Graph: Shows fallback badge, 6 skills, 5 deps
3. Diagnostic: 10 questions → submit → mastery persisted
4. Route: Real URLs (MDN, javascript.info, React.dev), 61h
5. Verify: HTML/CSS quiz → 100% → confetti → VERIFIED
6. Unlock: JavaScript becomes IN_PROGRESS (prereq satisfied)
7. Replan: 4h/wk → v2, 16 weeks, infeasible message
8. Refresh: Everything restored
```

---

## Post-Hackathon Immediate Actions

1. **Add authentication** (Cognito + JWT) — unblocks multi-user
2. **Add user_id to Goal** — scope all queries
3. **Migrate to PostgreSQL** — production readiness
4. **Exponential backoff for Gemini 503** — reliability
5. **Frontend unit tests (Vitest + RTL)** — confidence
6. **Landing page** — marketing

---

## Credentials & Secrets (Never Commit)

| Secret | Location | Rotation |
|--------|----------|----------|
| `GEMINI_API_KEY` | `backend/.env` | Google Cloud Console |
| Database password | `DATABASE_URL` (prod) | Cloud SQL / Supabase |

**Current API Key:** Configured in `backend/.env` (not printed here)

---

## Contact & References

- **Repository:** `github.com/aamina15/apogee` (origin remote)
- **Frontend reference:** `github.com/aamina15/frontendapogee` (separate)
- **Hackathon:** October 3, 2026
- **Primary maintainer:** Aamina Hasan

---

*This memory file captures the essential context for any future session. Read this first before making changes.*