import React, { useState, useEffect } from 'react';
import {
  BarChart2,
  AlertCircle,
  ArrowRight,
  Lock,
  Loader2,
  RefreshCw,
  Target,
  Info,
  Search,
  ShieldCheck,
  PlayCircle,
} from 'lucide-react';
import { fetchGraph, fetchGoalDiagnosticMastery } from '../services/api';

const STRONG_THRESHOLD = 70;

/**
 * Skill Gap Analysis — the visible outcome of the diagnostic (or of skipping it).
 * Answers: what do I already know, what needs work, what was not assessed, and
 * where should I begin? Diagnostic scores are estimates; they never verify or
 * unlock anything — server-graded skill checks do.
 */
export default function SkillGapAnalysis({
  goalId,
  profile,
  skipped,
  onContinue,
  onDeepenAssessment,
  onTakeDiagnostic,
}) {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [data, setData] = useState(null);

  const load = async () => {
    setLoading(true);
    setError(null);
    try {
      const [graph, mastery] = await Promise.all([
        fetchGraph(goalId),
        fetchGoalDiagnosticMastery(goalId),
      ]);
      setData({ graph, mastery: mastery.mastery || [] });
    } catch (err) {
      console.warn('[ORBIT SkillGap Error]', err.message);
      setError(err.message || 'Failed to load your results');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, [goalId]);

  if (loading) {
    return (
      <div className="w-full max-w-5xl mx-auto px-4 py-10 flex flex-col gap-4" aria-busy="true">
        <div className="h-8 w-72 rounded-lg bg-surface-container-high animate-pulse" />
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          {[0, 1, 2, 3].map(i => <div key={i} className="h-24 rounded-xl bg-surface-container-high animate-pulse" />)}
        </div>
        <div className="h-64 rounded-2xl bg-surface-container-high animate-pulse" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="w-full max-w-3xl mx-auto px-4 py-12 flex flex-col items-center text-center gap-3">
        <AlertCircle className="w-10 h-10 text-rose-400" />
        <h2 className="text-lg font-bold text-rose-300">Could Not Load Your Results</h2>
        <p className="text-xs text-on-surface-variant max-w-md">{error}</p>
        <button onClick={load} className="px-4 py-2 rounded-xl bg-secondary text-on-secondary text-xs font-bold flex items-center gap-1.5">
          <RefreshCw className="w-3.5 h-3.5" /> Retry
        </button>
      </div>
    );
  }

  const skills = data?.graph?.skills || [];
  const deps = data?.graph?.dependencies || [];
  const coverage = data?.graph?.coverage;
  const masteryRows = data?.mastery || [];
  const masteryByDbId = {};
  masteryRows.forEach(m => { masteryByDbId[m.skill_db_id] = m; });

  const nameById = {};
  skills.forEach(s => { nameById[s.id] = s.name; });

  const rows = skills.map(s => {
    const m = masteryByDbId[s.db_id];
    const assessed = !!m?.assessed;
    const score = assessed ? m.score : null;
    const prereqNames = deps.filter(d => d.to === s.id).map(d => nameById[d.from] || d.from);
    const state = (s.status || 'LOCKED').toUpperCase();
    return {
      dbId: s.db_id,
      name: s.name,
      state,
      assessed,
      score,
      strong: assessed && score >= STRONG_THRESHOLD,
      weak: assessed && score < STRONG_THRESHOLD,
      prereqNames,
    };
  });

  const assessedRows = rows.filter(r => r.assessed);
  const unassessedRows = rows.filter(r => !r.assessed);
  const strongRows = rows.filter(r => r.strong);
  const weakRows = rows.filter(r => r.weak);

  // "Where should I begin?" — the first unlockable skill that isn't already strong.
  const beginRow = rows.find(r =>
    (r.state === 'AVAILABLE' || r.state === 'IN_PROGRESS') && !r.strong)
    || rows.find(r => r.state === 'AVAILABLE' || r.state === 'IN_PROGRESS');

  // Prerequisite implications: which unverified skills are gating locked skills
  const stateBySlug = {};
  skills.forEach(s => { stateBySlug[s.id] = (s.status || 'LOCKED').toUpperCase(); });
  const gating = [];
  deps.forEach(d => {
    if (stateBySlug[d.to] !== 'LOCKED') return;
    const fromRow = rows.find(r => {
      const skill = skills.find(s => s.id === d.from);
      return skill && skill.db_id === r.dbId;
    });
    if (stateBySlug[d.from] !== 'VERIFIED') {
      gating.push({
        from: nameById[d.from] || d.from,
        to: nameById[d.to] || d.to,
        assessed: !!fromRow?.assessed,
        score: fromRow?.score ?? null,
      });
    }
  });

  const stateBadge = {
    VERIFIED: 'bg-tertiary-container/30 text-tertiary border-tertiary/30',
    IN_PROGRESS: 'bg-amber-950/40 text-amber-400 border-amber-500/30',
    AVAILABLE: 'bg-secondary-container/20 text-secondary border-secondary/30',
    LOCKED: 'bg-surface-container-low text-outline border-outline-variant/40',
  };

  const SkillRow = ({ row }) => (
    <div className="p-3 rounded-xl bg-surface-container-high border border-outline-variant/40 flex flex-wrap items-center justify-between gap-2">
      <div className="flex flex-col gap-0.5 min-w-0">
        <span className="text-sm font-semibold text-on-surface truncate">{row.name}</span>
        {row.prereqNames.length > 0 && (
          <span className="text-[10px] text-outline">After: {row.prereqNames.join(', ')}</span>
        )}
      </div>
      <div className="flex items-center gap-2 flex-shrink-0">
        <span className={`text-[10px] px-2 py-0.5 rounded-full border font-bold ${stateBadge[row.state]}`}>{row.state}</span>
        {row.assessed ? (
          <span className={`text-xs font-mono font-bold px-2 py-0.5 rounded ${row.strong ? 'text-tertiary' : 'text-amber-400'}`}>
            {row.score}%
          </span>
        ) : (
          <span className="text-[10px] font-bold px-2 py-0.5 rounded border border-outline-variant/40 text-outline tracking-wider">
            UNASSESSED
          </span>
        )}
      </div>
    </div>
  );

  /* ===== SKIPPED DIAGNOSTIC: purposeful empty state — no zero-stat wall ===== */
  if (skipped) {
    return (
      <div className="w-full max-w-3xl mx-auto px-4 py-8 flex flex-col gap-6">
        <div className="pt-4 pb-2">
          <p className="eyebrow mb-3">02 / YOUR STARTING POINT</p>
          <h1 className="text-3xl sm:text-4xl font-bold font-headline-lg tracking-tight">Your Skill Gap Analysis</h1>
          <p className="mt-3 text-sm text-on-surface-variant">
            For <strong className="text-on-surface">{profile?.title}</strong>
          </p>
        </div>

        <div className="rounded-2xl bg-surface-container border border-outline-variant/60 p-8 shadow-xl flex flex-col items-center text-center gap-4">
          <span className="w-14 h-14 rounded-2xl bg-secondary/10 border border-secondary/30 flex items-center justify-center">
            <Target className="w-7 h-7 text-secondary" />
          </span>
          <h2 className="text-xl font-bold text-on-surface font-headline-md">You haven't taken a diagnostic yet.</h2>
          <p className="text-sm text-on-surface-variant max-w-lg leading-relaxed">
            ORBIT can still build a learning route, but your prior knowledge hasn't been assessed.
            Every skill will start unassessed — nothing has been scored, verified, or unlocked, and
            nothing has failed.
          </p>
          <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-3 mt-2">
            <button onClick={onTakeDiagnostic} className="btn-primary text-sm">
              <PlayCircle className="w-4 h-4" />
              <span>Take Diagnostic</span>
            </button>
            <button onClick={onContinue} className="btn-secondary text-sm">
              <span>Continue Without Assessment</span>
              <ArrowRight className="w-4 h-4" />
            </button>
          </div>
        </div>

        <div className="p-4 rounded-xl bg-surface-container border border-outline-variant/60 flex items-start gap-2.5 text-xs text-on-surface-variant">
          <Info className="w-4 h-4 text-secondary mt-0.5 flex-shrink-0" />
          <span>
            Whenever you continue, skill checks (≥70%) remain the only way to verify skills and
            unlock prerequisites. Taking the diagnostic first simply gives you a starting estimate —
            it never unlocks anything on its own.
          </span>
        </div>
      </div>
    );
  }

  /* ===== ASSESSED: full gap analysis ===== */
  return (
    <div className="w-full max-w-6xl mx-auto px-4 py-6 flex flex-col gap-6">
      <div className="pt-4 pb-2">
        <p className="eyebrow mb-3">02 / YOUR STARTING POINT</p>
        <h1 className="text-3xl sm:text-4xl font-bold font-headline-lg tracking-tight">Your Skill Gap Analysis</h1>
        <p className="mt-3 text-sm text-on-surface-variant max-w-2xl">
          What you already know, what needs work, and where to begin — server-graded for{' '}
          <strong className="text-on-surface">{profile?.title}</strong>.
        </p>
      </div>

      {/* Assessment summary */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <div className="p-3.5 rounded-xl bg-surface-container-high border border-outline-variant/40">
          <span className="text-[11px] text-outline font-semibold uppercase">Assessed</span>
          <div className="text-lg font-bold text-on-surface font-mono">{assessedRows.length}/{rows.length}</div>
          <span className="text-[10px] text-on-surface-variant">skills with graded questions</span>
        </div>
        <div className="p-3.5 rounded-xl bg-tertiary-container/20 border border-tertiary/30">
          <span className="text-[11px] text-tertiary font-semibold uppercase">Strong areas</span>
          <div className="text-lg font-bold text-tertiary font-mono">{strongRows.length}</div>
          <span className="text-[10px] text-on-surface-variant">scored ≥ {STRONG_THRESHOLD}%</span>
        </div>
        <div className="p-3.5 rounded-xl bg-amber-950/30 border border-amber-500/30">
          <span className="text-[11px] text-amber-400 font-semibold uppercase">Needs work</span>
          <div className="text-lg font-bold text-amber-400 font-mono">{weakRows.length}</div>
          <span className="text-[10px] text-on-surface-variant">scored below {STRONG_THRESHOLD}%</span>
        </div>
        <div className="p-3.5 rounded-xl bg-surface-container-high border border-outline-variant/40">
          <span className="text-[11px] text-outline font-semibold uppercase">Not assessed</span>
          <div className="text-lg font-bold text-on-surface font-mono">{unassessedRows.length}</div>
          <span className="text-[10px] text-on-surface-variant">no score — never counted as 0%</span>
        </div>
      </div>

      {/* Where to begin */}
      {beginRow && (
        <div role="status" className="flex items-start gap-2.5 px-4 py-3.5 rounded-xl border border-secondary/30 bg-gradient-to-br from-secondary/10 to-primary/5 text-sm">
          <ShieldCheck className="w-4 h-4 text-secondary mt-0.5 flex-shrink-0" />
          <span className="text-on-surface">
            Where to begin: <strong>{beginRow.name}</strong>
            {beginRow.assessed && !beginRow.strong
              ? ` — your diagnostic estimate was ${beginRow.score}%, so this is the first unlockable skill worth strengthening.`
              : ' — it is the first skill in your route that is ready to work on.'}
          </span>
        </div>
      )}

      {/* Verified Goal Coverage — clearly separated from diagnostic estimates */}
      {coverage && (
        <div className="flex flex-wrap items-center gap-x-3 gap-y-1 px-4 py-3 rounded-xl bg-surface-container border border-primary/30 text-xs">
          <span className="flex items-center gap-1.5 font-bold text-primary">
            <ShieldCheck className="w-4 h-4" /> Verified Goal Coverage: {coverage.verified_coverage_pct}%
          </span>
          <span className="text-outline">
            ({coverage.verified_skills}/{coverage.total_skills} skills verified · {coverage.remaining_skills} remaining) —
            from server-graded skill checks only. Diagnostic estimates below never count toward it.
          </span>
        </div>
      )}

      {/* Strong areas */}
      {strongRows.length > 0 && (
        <section className="rounded-2xl bg-surface-container border border-tertiary/30 p-5 shadow-xl flex flex-col gap-3">
          <h2 className="text-base font-bold text-tertiary font-headline-md flex items-center gap-2">
            <BarChart2 className="w-4 h-4" /> Strong areas — scored ≥ {STRONG_THRESHOLD}%
          </h2>
          <div className="flex flex-col gap-2">
            {strongRows.map(row => <SkillRow key={row.dbId} row={row} />)}
          </div>
          <p className="text-[11px] text-outline">Strong estimates still need a verified skill check to count toward coverage.</p>
        </section>
      )}

      {/* Needs work */}
      {weakRows.length > 0 && (
        <section className="rounded-2xl bg-surface-container border border-amber-500/30 p-5 shadow-xl flex flex-col gap-3">
          <h2 className="text-base font-bold text-amber-400 font-headline-md flex items-center gap-2">
            <BarChart2 className="w-4 h-4" /> Needs work — scored below {STRONG_THRESHOLD}%
          </h2>
          <div className="flex flex-col gap-2">
            {weakRows.map(row => <SkillRow key={row.dbId} row={row} />)}
          </div>
        </section>
      )}

      {/* Not assessed — explicit, never a zero score */}
      {unassessedRows.length > 0 && (
        <section className="rounded-2xl bg-surface-container border border-outline-variant/60 p-5 shadow-xl flex flex-col gap-3">
          <h2 className="text-base font-bold text-on-surface font-headline-md flex items-center gap-2">
            <Info className="w-4 h-4 text-secondary" /> Not assessed
          </h2>
          <p className="text-xs text-on-surface-variant">
            These skills had no diagnostic questions, so they carry <strong className="text-on-surface">no score at all</strong> —
            they are not failures and are never counted as 0%. You can deepen the assessment or simply verify them later.
          </p>
          <div className="flex flex-wrap gap-2">
            {unassessedRows.map(row => (
              <span key={row.dbId} className="text-[11px] font-semibold px-2.5 py-1 rounded-lg border border-outline-variant/40 bg-surface-container-high text-on-surface-variant">
                {row.name}
              </span>
            ))}
          </div>
        </section>
      )}

      {/* Prerequisite gaps + route influence */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="p-5 rounded-2xl bg-surface-container border border-outline-variant/60 shadow-xl flex flex-col gap-3">
          <h3 className="text-sm font-bold text-on-surface flex items-center gap-2">
            <Lock className="w-4 h-4 text-secondary" /> Prerequisite gaps affecting your route
          </h3>
          {gating.length === 0 ? (
            <p className="text-xs text-on-surface-variant">
              Nothing extra is blocked right now. Skills unlock when <strong>all</strong> their
              prerequisites are verified — the diagnostic does not unlock anything.
            </p>
          ) : (
            <ul className="flex flex-col gap-2">
              {gating.slice(0, 6).map((g, i) => (
                <li key={i} className="text-xs text-on-surface-variant flex items-start gap-2">
                  <Lock className="w-3.5 h-3.5 text-outline mt-0.5 flex-shrink-0" />
                  <span>
                    <strong className="text-on-surface">{g.to}</strong> stays locked until{' '}
                    <strong className="text-on-surface">{g.from}</strong> is verified
                    {g.assessed ? ` (diagnostic estimate: ${g.score}% — still needs verification)` : ' (not yet assessed)'}.
                  </span>
                </li>
              ))}
            </ul>
          )}
        </div>
        <div className="p-5 rounded-2xl bg-surface-container border border-outline-variant/60 shadow-xl flex flex-col gap-3">
          <h3 className="text-sm font-bold text-on-surface flex items-center gap-2">
            <Info className="w-4 h-4 text-secondary" /> How this shapes your route
          </h3>
          <ul className="text-xs text-on-surface-variant flex flex-col gap-2 list-disc pl-4">
            <li>Skills with unmet prerequisites stay <strong className="text-on-surface">Locked</strong>; verified prerequisites unlock them.</li>
            <li>Diagnostic estimates never count toward Verified Coverage — only server-graded skill checks do.</li>
            <li>Your route's remaining hours shrink only when a skill is <strong className="text-on-surface">Verified</strong>.</li>
          </ul>
        </div>
      </div>

      {/* Actions — primary CTA first */}
      <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-3 pb-4">
        <button onClick={onContinue} className="btn-primary text-sm">
          <span>Continue to Build Route</span>
          <ArrowRight className="w-4 h-4" />
        </button>
        <button onClick={onDeepenAssessment} className="btn-secondary text-sm">
          <Search className="w-4 h-4" />
          <span>Deeper assessment (2 questions per skill)</span>
        </button>
      </div>
    </div>
  );
}
