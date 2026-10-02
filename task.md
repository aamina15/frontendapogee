# ORBIT — Task Tracker & Hackathon Priorities

## Hackathon Deadline: **October 3, 2026**

---

## ✅ COMPLETED (P0 Roadmap)

| Task | Status | Notes |
|------|--------|-------|
| P0-0: Project setup (FastAPI + React + Vite) | ✅ | |
| P0-1: Goal CRUD + SQLite persistence | ✅ | |
| P0-2: Graph generation endpoint | ✅ | |
| P0-3: Gemini AI integration | ✅ | Key configured; 503 intermittent |
| P0-4: DAG validation (Kahn's algorithm) | ✅ | Cycle detection + repair |
| P0-5: Diagnostic generation & grading | ✅ | 10 questions, server-graded |
| P0-6: Skill gap analysis (mastery states) | ✅ | 4-state engine |
| P0-7: Graph display + prerequisite states | ✅ | SVG DAG with status colors |
| P0-8: Topological route ordering | ✅ | Prerequisite-safe |
| P0-9: Hour budget + infeasibility | ✅ | Clear messaging |
| P0-10: Real resource URLs | ✅ | MDN, React.dev, etc. |
| P0-11: Skill-specific verification | ✅ | 5 MCQs, ≥70% pass |
| P0-12: All-prereqs unlocking | ✅ | Strict AND logic |
| P0-13: Replanning + versioning | ✅ | Atomic, preserves verified |

---

## 🔄 IN PROGRESS (This Session)

| Task | Priority | Status |
|------|----------|--------|
| Final Gemini integration check | P0 | ✅ New goal "Learn Rust" → `graph_source: gemini` |
| Rebrand APOGEE → ORBIT | P0 | ✅ All user-facing strings updated |
| Create project documentation | P0 | ✅ prd.md, architecture.md, rules.md, design.md |
| Run final tests + build | P0 | 🔄 Next step |

---

## 📋 HACKATHON PRIORITIES (Oct 3 Demo)

### Must Work for Live Demo
| # | Scenario | Test Command |
|---|----------|--------------|
| 1 | Create goal → graph → diagnostic → verify → route → replan | Manual browser flow |
| 2 | Graph shows `source: "gemini"` (or honest fallback) | `curl /api/goals/{id}/graph` |
| 3 | Infeasible budget clearly reported | Set 1h/week on 60h route |
| 4 | Verification unlocks downstream skills | Verify HTML/CSS → JS unlocks |
| 5 | Replan preserves verified progress | Change hours → v2 route |
| 6 | Browser refresh preserves all state | F5 at any step |
| 7 | Backend restart preserves data | `pkill python main.py` → restart |
| 8 | No raw errors in UI | Check all error states |

### Demo Script (3 min)
```
1. "I want to become a Frontend Developer Intern" (7h/wk, 8wks, free)
2. → ORBIT generates AI skill graph (shows gemini/fallback badge)
3. → Take diagnostic (10 questions, real grading)
4. → See skill states update (LOCKED → IN_PROGRESS)
5. → Open route: real resources, 61h, feasible/infeasible
6. → Verify HTML/CSS (quiz, confetti on pass)
7. → Watch JavaScript unlock (prerequisite satisfied)
8. → Replan to 4h/wk → new version, 16 weeks, infeasible reported
9. → Refresh browser → everything restored
```

---

## 🎯 POST-HACKATHON ROADMAP

### Phase 1: Production Hardening (Week 1-2)
| Task | Effort | Dependencies |
|------|--------|--------------|
| Add authentication (Cognito + JWT) | M | None |
| User-scoped goals (add `user_id` to Goal) | M | Auth |
| Migrate to PostgreSQL | S | Docker/Cloud SQL |
| Rate limiting on `/generate-graph` | S | Auth |
| HTTPS + proper CORS | S | Domain/SSL |

### Phase 2: Multi-User & Collaboration (Month 1)
| Task | Effort | Dependencies |
|------|--------|--------------|
| Team/organization workspaces | L | Auth |
| Shared learning paths | M | Teams |
| Mentor/coach dashboard | M | Teams |
| Invite links + roles | S | Teams |

### Phase 3: Intelligence & Content (Month 2-3)
| Task | Effort | Dependencies |
|------|--------|--------------|
| Grounded chat tutor (RAG over resources) | L | Vector DB |
| Market pulse integration (live job data) | M | External APIs |
| Advanced analytics (cohort, dropout) | M | Events |
| Custom resource catalogue editor | M | Admin UI |

### Phase 4: Platform (Quarter 2+)
| Task | Effort | Dependencies |
|------|--------|--------------|
| Mobile app (React Native) | XL | API stable |
| Plugin/extension system | L | Core stable |
| Enterprise SSO (SAML/OIDC) | M | Auth v2 |
| White-label theming | M | Design system v2 |

---

## 🐛 KNOWN BUGS / TECH DEBT

| ID | Issue | Severity | Workaround |
|----|-------|----------|------------|
| BUG-001 | Gemini 503 intermittent | Medium | Fallback works; retry later |
| BUG-002 | 77 lint warnings (unused imports) | Low | Cleanup sprint |
| BUG-003 | `/api/goals/active` returns global latest | Critical (multi-user) | Single-user demo only |
| BUG-004 | Diagnostic covers 5/6 skills | Medium | Acceptable for MVP |
| BUG-005 | Resource hours are estimates | Low | Documented |
| BUG-006 | Python deprecation warnings (3) | Low | Upgrade deps post-hackathon |
| BUG-007 | No unit tests for frontend | Medium | Add Vitest/RTL post-hackathon |

---

## 🚀 DEPLOYMENT CHECKLIST (Hackathon Day)

- [ ] Backend running on `:8000` (`python main.py`)
- [ ] Frontend dev server on `:5173` (`npm run dev`) OR production build served
- [ ] `backend/.env` has valid `GEMINI_API_KEY`
- [ ] `backend/apogee.db` exists with test data
- [ ] Browser opens `http://localhost:5173`
- [ ] Health check: `curl http://localhost:8000/health`
- [ ] Demo goal created and tested end-to-end
- [ ] Screenshots/recording ready for submission

---

## 📝 DAILY STANDUP (Hackathon Week)

| Date | Focus | Blocker |
|------|-------|---------|
| Sep 30 | Final audit + Gemini key | None |
| Oct 1 | Rebrand + docs | None |
| Oct 2 | Demo rehearsal + edge cases | None |
| **Oct 3** | **HACKATHON SUBMISSION** | — |

---

## 🏷️ TAGS FOR ISSUE TRACKING

| Tag | Meaning |
|-----|---------|
| `p0-blocker` | Must fix before demo |
| `p1-high` | Fix this week |
| `p2-medium` | Next sprint |
| `p3-low` | Backlog |
| `tech-debt` | Refactor/cleanup |
| `docs` | Documentation only |
| `design` | UI/UX only |
| `security` | Auth/isolation |
| `gemini` | AI integration |