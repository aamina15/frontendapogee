# ORBIT — Product Requirements Document

## Product Vision

**ORBIT** is a learning navigation platform that turns any free-text career goal into a verified, prerequisite-locked, hour-budgeted learning route backed by real web resources and AI-generated skill graphs.

**Tagline:** Your Goal. Your Path. Your ORBIT.

---

## Core Problem

Learners face three systemic barriers when upskilling:
1. **No prerequisite awareness** — They start advanced topics without foundations, causing frustration and dropout.
2. **No time budgeting** — They overcommit to unrealistic timelines without knowing actual resource hours.
3. **No verification** — They confuse "watched a video" with "mastered the skill," leaving gaps that block downstream progress.

---

## Solution

ORBIT provides a **four-step workflow**:
1. **Goal Intake** — Free-text goal + weekly hours + duration + budget.
2. **AI Skill Graph** — Gemini generates a prerequisite DAG (5–10 skills, directed edges). Backend validates acyclicity (Kahn's algorithm) and repairs cycles.
3. **Diagnostic Assessment** — ~10 MCQs across skills, graded server-side. Scores set initial mastery states (`IN_PROGRESS` for roots with score > 0).
4. **Route & Verification** — Topological route with real resource URLs (MDN, React.dev, etc.). Skills unlock **only** when ALL prerequisites are `VERIFIED` via quiz (≥70%). Replan preserves verified progress.

---

## Target User

- Self-directed developers upskilling for role transitions (frontend → full-stack, backend → ML, etc.)
- Bootcamp graduates needing structured gap-filling
- Career switchers with limited weekly hours (4–10h/week)

---

## Key Features

| Feature | Description |
|---------|-------------|
| **Goal → Graph** | LLM (Gemini 3.5 Flash) generates skill DAG; fallback to curated graphs if API unavailable |
| **DAG Validation** | Deterministic Kahn's algorithm; cycles repaired before persistence |
| **Diagnostic** | 2 questions/skill, server-graded, `correct_index` never exposed to client |
| **State Engine** | Four states: `LOCKED` → `AVAILABLE` → `IN_PROGRESS` → `VERIFIED` |
| **All-Prereqs Rule** | A skill unlocks **only when ALL prerequisites are VERIFIED** |
| **Real Resources** | Curated catalogue with live URLs (MDN, javascript.info, React.dev, TypeScript.org, etc.) |
| **Hour Budget** | Route sums resource hours; compares to `hours_per_week × duration_weeks` |
| **Replanning** | Change weekly hours → new route version; verified skills preserved at 0h |
| **Persistence** | SQLite (dev) / PostgreSQL (prod); survives browser refresh & backend restart |

---

## Non-Functional Requirements

| Requirement | Target |
|-------------|--------|
| API latency (P95) | < 500ms |
| Frontend build size | < 400 kB gzipped |
| Test coverage | 43 backend tests passing |
| Accessibility | WCAG AA (color contrast, keyboard nav, ARIA labels) |
| Security | No client-side verification bypass; `verified` only via server quiz |

---

## Success Metrics (Hackathon Demo)

- ✅ Create goal → generate graph → take diagnostic → verify skill → see unlock → replan
- ✅ Graph source shows `gemini` (when API available) or `fallback` (honest)
- ✅ Infeasible budget clearly reported (e.g., "61h required, 48h available")
- ✅ No raw stack traces in UI; friendly error messages
- ✅ All 43 backend tests pass; production build succeeds

---

## Out of Scope (Post-Hackathon)

- User authentication / multi-user isolation
- Landing page & marketing site
- Mobile app
- Team/organization features
- Advanced analytics dashboard
- LLM chat tutor (GroundedChatDrawer — stubbed only)