import React, { useState, useEffect, useMemo, useCallback } from 'react';
import { ExternalLink, Clock, Layers, Play, Award, AlertCircle, CheckCircle2, Loader2, Monitor, BookOpen, Layers as LayersIcon, ChevronDown, Unlock } from 'lucide-react';
import { fetchGoalRoute } from '../services/api';

// Format preference options
const FORMAT_OPTIONS = [
  { value: 'both', label: 'Video & Reading', icon: LayersIcon, description: 'Show all available formats' },
  { value: 'video', label: 'Video Only', icon: Monitor, description: 'Prioritize video courses & tutorials' },
  { value: 'reading', label: 'Reading Only', icon: BookOpen, description: 'Prioritize documentation & text guides' },
];

export default function RouteScreen({ 
  mode = 'route',
  graphData,
  onStartLearning,
  profile,
  goalId,
  onSwitchToGraphView, 
  onOpenProofModal,
  userState,
  replanKey,
}) {
  const [routeData, setRouteData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [formatPreference, setFormatPreference] = useState(() => {
    if (goalId) {
      const stored = localStorage.getItem(`orbit_format_pref_${goalId}`);
      if (stored && ['video', 'reading', 'both'].includes(stored)) {
        return stored;
      }
    }
    return 'both';
  });
  const [formatOpen, setFormatOpen] = useState(false);

  const goalTitle = profile?.title || "Frontend Developer Internship";
  const allResources = useMemo(
    () => routeData?.phases?.flatMap(phase => phase.resources) || [],
    [routeData]
  );

  // Resolve the real resource entries to display per skill under the selected
  // format preference. Each route item carries `all_formats` — the actual
  // verified reading and/or video resources from the backend catalogue.
  const entriesForItem = useCallback((item) => {
    const list = item.all_formats?.length ? item.all_formats : [item];
    if (formatPreference === 'both') return list;
    return list.filter(e => e.format === formatPreference || e.format === 'both');
  }, [formatPreference]);

  // Study order across the whole route (1-based), by skill id
  const orderById = useMemo(
    () => new Map(allResources.map((r, i) => [r.skill_id, i + 1])),
    [allResources]
  );

  // One display record per schedule item: the item (status, schedule, skill)
  // plus the resource entries that match the current format preference.
  const displayItems = useMemo(
    () => allResources.map(item => ({ item, entries: entriesForItem(item) })),
    [allResources, entriesForItem]
  );

  // The next actionable skill: the FIRST skill in deterministic route order
  // whose prerequisites are met (AVAILABLE) or which is underway (IN_PROGRESS).
  // Format preference changes which RESOURCES are shown, never which skill is
  // verifiable — a reading-only skill stays next-up under "Video Only".
  const nextDisplay = displayItems.find(({ item }) =>
    item.status === 'AVAILABLE' || item.status === 'IN_PROGRESS');
  const nextSkill = nextDisplay
    ? {
        ...(nextDisplay.entries[0] || {}),
        target_skill_name: nextDisplay.item.target_skill_name,
        status: nextDisplay.item.status,
        entries: nextDisplay.entries,
        hasFormatMatch: nextDisplay.entries.length > 0,
      }
    : null;

  // What verifying the next skill unlocks (from the saved prerequisite graph)
  const unlockPreview = useMemo(() => {
    if (!graphData?.skills || !nextSkill) return null;
    const slug = graphData.skills.find(s => s.db_id === nextSkill.skill_id)?.id;
    if (!slug) return null;
    const names = (graphData.dependencies || [])
      .filter(d => d.from === slug)
      .map(d => graphData.skills.find(s => s.id === d.to)?.name || d.to);
    return names.length ? names.join(', ') : null;
  }, [graphData, nextSkill]);

  // Pre-compute header strings to avoid JSX parsing issues with nested ternaries
  const stepLabel = mode === 'learn' ? '04 / PUT YOUR SKILLS INTO PRACTICE' : '03 / YOUR LEARNING PLAN';
  const headerTitle = mode === 'learn' ? 'Learn & Verify' : 'Your route forward';
  const headerDesc = mode === 'learn'
    ? 'Open a resource, practice, then take a skill check to unlock what comes next.'
    : 'Review the study schedule, prerequisite order, resource coverage and feasibility — then move into learning when you\'re ready.';
  const visibleItems = displayItems.filter(({ entries }) => entries.length > 0);
  const nextSkillLabel = nextSkill ? 'READY FOR YOU' : 'YOUR PROGRESS';
  const nextSkillTitle = nextSkill?.target_skill_name ||
    (visibleItems.length && visibleItems.every(({ item }) => item.status === 'VERIFIED')
      ? 'Every skill in this route is verified'
      : 'Check your prerequisite graph');
  const nextSkillDesc = nextSkill
    ? "This skill's prerequisites are met. Learn at your pace and verify when ready."
    : 'Your saved skill states are shown below.';

  // Load real backend route & real learning resources
  const loadRoute = async () => {
    setLoading(true);
    setError(null);
    try {
      const rData = await fetchGoalRoute(goalId);
      setRouteData(rData);
    } catch (err) {
      console.warn('[ORBIT Route API Error]', err.message);
      setError(err.message || 'Failed to load backend route');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadRoute();
  }, [goalId, replanKey]);

  // Persist format preference
  useEffect(() => {
    if (goalId) {
      localStorage.setItem(`orbit_format_pref_${goalId}`, formatPreference);
    }
  }, [formatPreference, goalId]);

  // Close the format dropdown on outside click or Escape
  useEffect(() => {
    if (!formatOpen) return;
    const onPointerDown = (e) => {
      if (!e.target.closest?.('[aria-label="Learning format preference"]')) {
        setFormatOpen(false);
      }
    };
    const onKeyDown = (e) => {
      if (e.key === 'Escape') setFormatOpen(false);
    };
    document.addEventListener('mousedown', onPointerDown);
    document.addEventListener('keydown', onKeyDown);
    return () => {
      document.removeEventListener('mousedown', onPointerDown);
      document.removeEventListener('keydown', onKeyDown);
    };
  }, [formatOpen]);

  const handleOpenCourseLink = (resource) => {
    if (!resource.url) {
      alert(`No verified resource is currently catalogued for ${resource.target_skill_name || 'this skill'}.`);
      return;
    }
    // Keep the demo/app on screen: real resources open in a new tab.
    window.open(resource.url, '_blank', 'noopener');
  };

  const handleFormatChange = (value) => {
    setFormatPreference(value);
    setFormatOpen(false);
  };

  // Get selected format option for rendering
  const selectedFormatOption = FORMAT_OPTIONS.find(o => o.value === formatPreference) || FORMAT_OPTIONS[0];

  return (
    <div className="w-full max-w-6xl mx-auto px-4 py-6 flex flex-col gap-6">
      <div className="pt-4 pb-2">
        <p className="eyebrow mb-3">{stepLabel}</p>
        <h1 className="text-3xl sm:text-4xl font-bold font-headline-lg tracking-tight">{headerTitle}</h1>
        <p className="mt-3 text-sm text-on-surface-variant">{headerDesc}</p>
      </div>
      {!loading && !error && mode === 'learn' && <section aria-label="Next skill" className="rounded-2xl border border-secondary/30 bg-gradient-to-br from-secondary/10 to-primary/5 p-6 flex flex-col sm:flex-row sm:items-center justify-between gap-5">
        <div className="min-w-0">
          <p className="eyebrow mb-2">{nextSkillLabel}</p>
          <h2 className="text-xl font-semibold">{nextSkillTitle}</h2>
          <p className="text-sm text-on-surface-variant mt-2">{nextSkillDesc}</p>
          {nextSkill && (nextSkill.entries?.length > 0 ? (
            <div className="flex flex-wrap items-center gap-2 mt-3">
              {nextSkill.entries.map(e => (
                <button
                  key={`${e.id ?? e.format}`}
                  onClick={() => e.url && handleOpenCourseLink({ ...e, target_skill_name: nextSkill.target_skill_name })}
                  disabled={!e.url}
                  className="px-3 py-1.5 rounded-lg border border-outline-variant/60 bg-surface-container-high hover:bg-surface-container-highest text-xs font-semibold text-on-surface flex items-center gap-1.5 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {e.format === 'video' ? <Monitor className="w-3.5 h-3.5 text-secondary" /> : e.format === 'reading' ? <BookOpen className="w-3.5 h-3.5 text-secondary" /> : <LayersIcon className="w-3.5 h-3.5 text-secondary" />}
                  <span>Open {e.format === 'video' ? 'video' : 'reading'}: {e.title.length > 34 ? e.title.slice(0, 32) + '…' : e.title}</span>
                </button>
              ))}
            </div>
          ) : (
            <p className="text-xs text-amber-400 mt-3 flex items-center gap-1.5">
              <AlertCircle className="w-3.5 h-3.5" />
              <span>No {formatPreference === 'video' ? 'video' : 'reading'} resource for this skill — switch format to see its materials. It is still verifiable.</span>
            </p>
          ))}
          {nextSkill && unlockPreview && (
            <p className="text-xs text-on-surface-variant mt-2 flex items-center gap-1.5">
              <Unlock className="w-3.5 h-3.5 text-secondary flex-shrink-0" />
              <span>Verifying this skill unlocks: <strong className="text-on-surface">{unlockPreview}</strong></span>
            </p>
          )}
        </div>
        {nextSkill && <div className="flex flex-wrap gap-3 shrink-0">
          <button onClick={() => onOpenProofModal({ id: nextSkill.skill_id, label: nextSkill.target_skill_name })} className="btn-primary text-sm">Verify Next Skill<Award className="w-4 h-4" /></button>
        </div>}
      </section>}
      {!loading && !error && mode === 'route' && <div><button onClick={onStartLearning} className="btn-primary text-sm">Continue to Learn & Verify<Play className="w-4 h-4" /></button></div>}
      {/* Top Telemetry Header & Navigation Controls */}
      <div className="w-full rounded-2xl bg-surface-container border border-outline-variant/60 p-5 shadow-xl flex flex-col gap-4">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-4 border-b border-outline-variant/40">
          <div>
            <div className="flex flex-wrap items-center gap-2">
              <h2 className="text-xl font-bold text-on-surface font-headline-md">{goalTitle} Route · v{routeData?.version || 1}</h2>
              <span className="text-xs px-2.5 py-0.5 rounded-full bg-tertiary-container/30 text-tertiary border border-tertiary/30 font-bold">
                Learning resources
              </span>
            </div>
            <p className="text-xs text-on-surface-variant mt-1">
              Deterministic route generated from verified real learning materials & total duration calculations.
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-2">
            {/* Format Preference Selector */}
            <div className="relative" role="group" aria-label="Learning format preference">
              <button
                type="button"
                className="btn-secondary text-xs !px-3 !py-2 flex items-center gap-1.5"
                aria-haspopup="listbox"
                aria-expanded={formatOpen}
                onClick={() => setFormatOpen(open => !open)}
              >
                <span className="flex items-center gap-1">
                  {selectedFormatOption.icon && (
                    <selectedFormatOption.icon className="w-3.5 h-3.5" />
                  )}
                  <span>{selectedFormatOption.label}</span>
                </span>
                <ChevronDown className="w-3.5 h-3.5" />
              </button>
              {formatOpen && (
              <div className="absolute right-0 mt-1 w-56 rounded-xl bg-surface-container border border-outline-variant/60 shadow-xl py-1 z-10 animate-in fade-in-0 zoom-in-95">
                {FORMAT_OPTIONS.map(opt => (
                  <button
                    key={opt.value}
                    type="button"
                    role="option"
                    aria-selected={formatPreference === opt.value}
                    onClick={() => handleFormatChange(opt.value)}
                    className={`w-full px-3 py-2 text-left text-sm flex items-center gap-2 transition-colors ${
                      formatPreference === opt.value
                        ? 'bg-primary/10 text-primary font-medium'
                        : 'text-on-surface hover:bg-surface-container-high'
                    }`}
                  >
                    <opt.icon className="w-4 h-4 flex-shrink-0" />
                    <div className="flex flex-col">
                      <span>{opt.label}</span>
                      <span className="text-[10px] text-on-surface-variant">{opt.description}</span>
                    </div>
                  </button>
                ))}
              </div>
              )}
            </div>

            <button
              onClick={onSwitchToGraphView}
              className="btn-secondary text-xs !px-4 !py-2.5"
            >
              <Layers className="w-4 h-4" />
              <span>Open Skill Completion Graph</span>
            </button>
          </div>
        </div>

        {/* Telemetry Strip — Verified Goal Coverage is the primary progress indicator */}
        <div className="grid grid-cols-2 sm:grid-cols-6 gap-3">
          {/* Verified Goal Coverage (primary) */}
          <div className="p-3 rounded-xl bg-surface-container-high border border-primary/50 ring-1 ring-primary/20 flex flex-col gap-0.5">
            <span className="text-[11px] text-primary font-semibold uppercase">Verified Coverage</span>
            <div className="text-lg font-bold text-primary font-mono">
              {routeData?.coverage?.verified_coverage_pct !== undefined ? `${routeData.coverage.verified_coverage_pct}%` : '0.0%'}
            </div>
            <span className="text-[10px] text-on-surface-variant">
              {routeData?.coverage
                ? `${routeData.coverage.verified_skills}/${routeData.coverage.total_skills} skills verified · ${routeData.coverage.remaining_skills} remaining`
                : 'Generate graph to begin'}
            </span>
          </div>

          {/* Diagnostic knowledge estimate (kept separate from verified coverage) */}
          <div className="p-3 rounded-xl bg-surface-container-high border border-outline-variant/40 flex flex-col gap-0.5">
            <span className="text-[11px] text-outline font-semibold uppercase">Diagnostic Coverage</span>
            <div className="text-lg font-bold text-secondary font-mono">
              {routeData?.coverage?.diagnostic_coverage_pct !== undefined ? `${routeData.coverage.diagnostic_coverage_pct}%` : '0.0%'}
            </div>
            <span className="text-[10px] text-secondary font-medium">
              Estimate only — not verified
            </span>
          </div>

          <div className="p-3 rounded-xl bg-surface-container-high border border-outline-variant/40 flex flex-col gap-0.5">
            <span className="text-[11px] text-outline font-semibold uppercase">Route Total Hours</span>
            <div className="text-lg font-bold text-on-surface font-mono">
              {routeData?.total_hours || 0} <span className="text-xs text-outline font-normal">hrs</span>
            </div>
            <span className="text-[10px] text-tertiary font-medium">Calculated from resource durations</span>
          </div>

          <div className="p-3 rounded-xl bg-surface-container-high border border-outline-variant/40 flex flex-col gap-0.5">
            <span className="text-[11px] text-outline font-semibold uppercase">Estimated Horizon</span>
            <div className="text-lg font-bold text-on-surface font-mono">
              {routeData?.total_weeks || 0} <span className="text-xs text-outline font-normal">weeks</span>
            </div>
            <span className="text-[10px] text-secondary font-medium">At {routeData?.hours_per_week || 10} hrs/week</span>
          </div>

          {/* Diagnostic average (simplified: single honest value, no readiness claim) */}
          <div className="p-3 rounded-xl bg-surface-container-high border border-outline-variant/40 flex flex-col gap-0.5">
            <span className="text-[11px] text-outline font-semibold uppercase">Diagnostic Average</span>
            <div className="text-lg font-bold text-secondary font-mono">
              {userState.readinessBand
                ? (userState.readinessBand.min === userState.readinessBand.max
                    ? `${userState.readinessBand.min}%`
                    : `${userState.readinessBand.min}%–${userState.readinessBand.max}%`)
                : '—'}
            </div>
            <span className="text-[10px] text-outline">
              {userState.readinessBand ? 'Placement quiz estimate' : 'Complete diagnostic to set baseline'}
            </span>
          </div>

          <div className="p-3 rounded-xl bg-surface-container-high border border-outline-variant/40 flex flex-col gap-0.5">
            <span className="text-[11px] text-outline font-semibold uppercase">Prerequisite Status</span>
            <div className="text-lg font-bold text-tertiary font-mono">
              {routeData?.prerequisite_safe ? 0 : '—'} <span className="text-xs text-tertiary font-normal">Violations</span>
            </div>
            <span className="text-[10px] text-tertiary font-medium">Strict ALL-Verified Rule</span>
          </div>
        </div>

        {/* Coverage disclaimer: progress metric only — never a promise of outcome */}
        {routeData?.coverage && (
          <p className="text-[10px] leading-relaxed text-outline">
            Verified Coverage counts skills passed on server-graded checks, weighted by importance.
            It is a learning-progress metric only — it does not guarantee employment or professional readiness.
            Diagnostic Coverage and Diagnostic Average are estimates from the placement quiz and never count toward verified progress.
          </p>
        )}
      </div>

      {routeData && !loading && !error && (routeData.missing_resources?.length > 0 || routeData.total_hours > routeData.available_hours) && (
          <div className="flex flex-col gap-2">
            {routeData.missing_resources?.length > 0 && (
              <div role="status" className="flex items-center gap-2 px-3 py-2.5 rounded-lg border text-sm bg-amber-900/30 border-amber-500/30 text-amber-300">
                <AlertCircle className="w-4 h-4 flex-shrink-0" />
                <span>Missing resources for: <strong>{routeData.missing_resources.join(', ')}</strong>. Estimates used for scheduling.</span>
              </div>
            )}
            {routeData.total_hours > routeData.available_hours && (
              <div role="status" className="flex items-center gap-2 px-3 py-2.5 rounded-lg border text-sm bg-amber-900/30 border-amber-500/30 text-amber-300">
                <AlertCircle className="w-4 h-4 flex-shrink-0" />
                <span>
                  Infeasible within {routeData.duration_weeks} weeks: {routeData.total_hours} hours required,
                  {' '}{routeData.available_hours} available. Allow {routeData.total_weeks} weeks or increase weekly hours.
                </span>
              </div>
            )}
          </div>
        )}
      {routeData && !loading && !error && routeData.feasible && !(routeData.missing_resources?.length > 0) && routeData.total_hours <= routeData.available_hours && (
          <div role="status" className="flex items-center gap-2 px-3 py-2.5 rounded-lg border text-sm bg-tertiary/10 border-tertiary/30 text-tertiary">
            <CheckCircle2 className="w-4 h-4 flex-shrink-0" />
            <span>{routeData.feasibility_message}</span>
          </div>
        )}
      {/* Loading State */}
      {loading && (
        <div className="w-full min-h-[320px] rounded-2xl bg-surface-container-lowest border border-outline-variant/60 flex flex-col items-center justify-center gap-3 shadow-xl">
          <Loader2 className="w-10 h-10 text-primary animate-spin" />
          <p className="text-sm font-bold text-on-surface font-headline-md">Loading Real Learning Resources for Route...</p>
        </div>
      )}

      {/* Error State */}
      {!loading && error && (
        <div className="w-full p-6 rounded-2xl bg-rose-950/30 border border-rose-500/50 flex flex-col items-center justify-center text-center gap-3 shadow-xl">
          <AlertCircle className="w-8 h-8 text-rose-400" />
          <h4 className="text-base font-bold text-rose-300">Route API Request Failed</h4>
          <p className="text-xs text-on-surface-variant max-w-md">{error}</p>
          <button onClick={loadRoute} className="px-4 py-2 rounded-xl bg-rose-500 hover:bg-rose-600 text-white text-xs font-bold transition-colors">
            Retry Loading Route
          </button>
        </div>
      )}

      {/* Learn & Verify: verification checklist (no duplicate route timeline) */}
      {!loading && !error && mode === 'learn' && routeData && (
        <div className="rounded-2xl bg-surface-container border border-outline-variant/60 p-5 shadow-xl flex flex-col gap-3">
          <div>
            <h3 className="text-base font-bold text-on-surface font-headline-md flex items-center gap-2">
              <Award className="w-4 h-4 text-secondary" /> Verification checklist
            </h3>
            <p className="text-xs text-on-surface-variant mt-1">
              Work down the prerequisite order. A skill check (≥70%) is the only way to verify a skill,
              shrink your remaining hours, and unlock what depends on it.
            </p>
          </div>
          <div className="flex flex-col gap-2">
            {displayItems.map(({ item, entries }) => {
              const badge = {
                VERIFIED: 'bg-tertiary-container/30 text-tertiary border-tertiary/30',
                IN_PROGRESS: 'bg-amber-950/40 text-amber-400 border-amber-500/30',
                AVAILABLE: 'bg-secondary-container/20 text-secondary border-secondary/30',
                LOCKED: 'bg-surface-container-low text-outline border-outline-variant/40',
              }[item.status] || 'bg-surface-container-low text-outline border-outline-variant/40';
              return (
                <div key={item.skill_id} className="p-3 rounded-xl bg-surface-container-high border border-outline-variant/40 flex flex-wrap items-center justify-between gap-2">
                  <div className="flex items-center gap-2.5 min-w-0">
                    <span className={`text-[10px] px-2 py-0.5 rounded-full border font-bold ${badge}`}>{item.status}</span>
                    <span className="text-sm font-semibold text-on-surface truncate">{item.target_skill_name}</span>
                  </div>
                  <div className="flex items-center gap-2 flex-shrink-0">
                    {entries.length > 0 ? (
                      <button
                        onClick={() => handleOpenCourseLink({ ...entries[0], target_skill_name: item.target_skill_name })}
                        disabled={!entries[0].url}
                        className="px-3 py-1.5 rounded-lg border border-outline-variant/60 bg-surface-container hover:bg-surface-container-highest text-xs font-semibold text-on-surface flex items-center gap-1.5 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                      >
                        <ExternalLink className="w-3.5 h-3.5 text-secondary" />
                        <span>Open {entries[0].format === 'video' ? 'video' : 'reading'}</span>
                      </button>
                    ) : (
                      <span className="text-[10px] text-amber-400 font-medium">No resource in this format</span>
                    )}
                    <button
                      disabled={item.status === 'LOCKED' || item.status === 'VERIFIED'}
                      onClick={() => onOpenProofModal({ id: item.skill_id, label: item.target_skill_name })}
                      className="btn-primary text-xs !px-3.5 !py-1.5 disabled:shadow-none"
                    >
                      <Award className="w-3.5 h-3.5" />
                      <span>{item.status === 'VERIFIED' ? 'Verified ✓' : item.status === 'LOCKED' ? 'Locked' : 'Verify Skill'}</span>
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
          <p className="text-[10px] text-outline">
            Need the full schedule and resource catalogue? Open Build Route from the header.
          </p>
        </div>
      )}

      {/* Build Route: prerequisite-ordered schedule timeline */}
      {!loading && !error && mode === 'route' && routeData?.phases && (
        <div className="flex flex-col gap-6">
          {routeData.phases.map((phase) => (
            <div key={phase.phase_num} className="flex flex-col gap-4">
              {/* Phase Header */}
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-2 border-b border-outline-variant/50">
                <div className="flex items-center gap-3">
                  <span className="w-8 h-8 rounded-xl bg-primary-container text-white font-bold text-sm flex items-center justify-center border border-indigo-400/40">
                    P{phase.phase_num}
                  </span>
                  <div>
                    <h3 className="text-lg font-bold text-on-surface font-headline-sm">{phase.title}</h3>
                    <div className="flex items-center gap-2 text-xs text-on-surface-variant mt-0.5">
                      <span>{phase.duration_weeks} Weeks</span>
                      <span>•</span>
                      <span>{phase.hours_total} Hours Total</span>
                      <span>•</span>
                      <span>Study in this order — skills unlock as prerequisites are verified</span>
                    </div>
                  </div>
                </div>

                <div className="flex flex-wrap gap-1.5">
                  {phase.skill_coverage.map((sc, i) => (
                    <span key={i} className="text-[11px] px-2.5 py-0.5 rounded-md bg-surface-container-highest text-on-surface-variant font-medium">
                      {sc}
                    </span>
                  ))}
                </div>
              </div>

              {/* Resources List in Phase — renders the actual resource for the selected format */}
              <div className="flex flex-col gap-4">
                {phase.resources.map((item) => {
                  const entries = entriesForItem(item);

                  // Honest fallback: this skill has NO verified resource in the selected format
                  if (entries.length === 0) {
                    const list = item.all_formats?.length ? item.all_formats : [item];
                    const hasVideo = list.some(e => e.format === 'video' || e.format === 'both');
                    const hasReading = list.some(e => e.format === 'reading' || e.format === 'both');

                    let message = '';
                    if (formatPreference === 'video' && !hasVideo && hasReading) {
                      message = `No verified video resource available for "${item.target_skill_name}" yet. Reading resources are available — switch to "Reading" or "Video & Reading" to see them.`;
                    } else if (formatPreference === 'reading' && !hasReading && hasVideo) {
                      message = `No verified reading resource available for "${item.target_skill_name}" yet. Video resources are available — switch to "Video" or "Video & Reading" to see them.`;
                    } else if (formatPreference === 'both') {
                      message = `No verified resource catalogued for "${item.target_skill_name}".`;
                    } else {
                      message = `No verified ${formatPreference} resource available for "${item.target_skill_name}" yet.`;
                    }

                    return (
                      <div
                        key={`missing-${item.skill_id}`}
                        className="rounded-2xl border bg-amber-500/10 border-amber-500/30 p-5 flex flex-col md:flex-row md:items-center justify-between gap-4"
                        role="status"
                        aria-live="polite"
                      >
                        <div className="flex flex-col gap-2 max-w-2xl">
                          <div className="flex flex-wrap items-center gap-2">
                            <span className="text-xs font-bold text-amber-400 bg-amber-950/40 px-2.5 py-0.5 rounded border border-amber-500/40 flex items-center gap-1">
                              <AlertCircle className="w-3.5 h-3.5" />
                              Format Not Available
                            </span>
                          </div>
                          <p className="text-sm text-amber-300">{message}</p>
                        </div>
                        <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-2 shrink-0">
                          <button
                            onClick={() => handleFormatChange('both')}
                            className="btn-secondary text-xs !px-4 !py-2"
                          >
                            <LayersIcon className="w-3.5 h-3.5" />
                            <span>Show All Formats</span>
                          </button>
                        </div>
                      </div>
                    );
                  }

                  // Render each matching verified resource entry with its own real
                  // title, source, URL and duration. Status/scheduling come from the item.
                  return entries.map((entry) => (
                    <div
                      key={`${item.skill_id}-${entry.id ?? entry.format}`}
                      className="rounded-2xl border bg-surface-container border-outline-variant/60 shadow-md transition-all"
                    >
                      <div className="p-5 flex flex-col md:flex-row md:items-center justify-between gap-4">
                        {/* Left info */}
                        <div className="flex flex-col gap-2 max-w-2xl">
                          <div className="flex flex-wrap items-center gap-2">
                            <span className="text-xs font-bold text-secondary bg-secondary-container/20 px-2.5 py-0.5 rounded border border-secondary/30">
                              {entry.source}
                            </span>
                            <span className="text-xs text-outline flex items-center gap-1 font-mono">
                              <Clock className="w-3.5 h-3.5 text-outline" /> {entry.duration_hours} hrs
                            </span>

                            {/* Format badge — colored by this entry's actual format */}
                            {entry.format && (
                              <span className={`text-xs font-mono px-2 py-0.5 rounded border flex items-center gap-1 ${
                                entry.format === 'video'
                                  ? 'bg-blue-500/20 text-blue-400 border-blue-500/30'
                                  : entry.format === 'reading'
                                  ? 'bg-green-500/20 text-green-400 border-green-500/30'
                                  : 'bg-purple-500/20 text-purple-400 border-purple-500/30'
                              }`}>
                                {entry.format === 'video' && <Monitor className="w-3 h-3" />}
                                {entry.format === 'reading' && <BookOpen className="w-3 h-3" />}
                                {entry.format === 'both' && <LayersIcon className="w-3 h-3" />}
                                <span className="capitalize">{entry.format}</span>
                              </span>
                            )}

                            {entry.has_resource ? (
                              <span className="text-xs font-mono font-bold text-tertiary bg-tertiary-container/30 px-2 py-0.5 rounded border border-tertiary/30 flex items-center gap-1">
                                Free Learning Resource
                              </span>
                            ) : (
                              <span className="text-xs font-mono font-bold text-amber-400 bg-amber-950/40 px-2 py-0.5 rounded border border-amber-500/40 flex items-center gap-1">
                                Catalog Gap — No Verified Resource Available
                              </span>
                            )}
                          </div>

                          <h4
                            className={`text-base font-bold text-on-surface transition-colors ${entry.url ? 'hover:text-primary cursor-pointer' : ''}`}
                            onClick={() => entry.url && handleOpenCourseLink({ ...entry, target_skill_name: item.target_skill_name })}
                          >
                            {entry.title}
                          </h4>

                          <div className="text-xs text-on-surface-variant flex items-center gap-2">
                            <span className="text-[10px] font-mono font-bold text-outline border border-outline-variant/40 rounded px-1.5 py-0.5" title="Study order">
                              #{orderById.get(item.skill_id) ?? '—'}
                            </span>
                            <span>Target Skill: <strong className="text-primary font-semibold">{item.target_skill_name}</strong></span>
                          </div>
                        </div>

                        {/* Right Actions */}
                        <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-2">
                          {/* Course Launch Button */}
                          <button
                            onClick={() => handleOpenCourseLink({ ...entry, target_skill_name: item.target_skill_name })}
                            disabled={!entry.url}
                            className={`px-4 py-2 rounded-xl text-xs font-semibold flex items-center justify-center gap-1.5 transition-colors border ${
                              entry.url
                                ? 'bg-surface-container-high hover:bg-surface-container-highest border-outline-variant/60 text-on-surface'
                                : 'bg-surface-container-low text-outline border-outline-variant/30 cursor-not-allowed'
                            }`}
                          >
                            <ExternalLink className="w-3.5 h-3.5 text-secondary" />
                            <span>{entry.url ? 'Open Course' : 'No URL Available'}</span>
                          </button>

                          {/* Verify Skill Button */}
                          <button
                            disabled={item.status === 'LOCKED' || item.status === 'VERIFIED'}
                            onClick={() => onOpenProofModal({ id: item.skill_id, label: item.target_skill_name })}
                            className="btn-primary text-xs !px-4 !py-2 disabled:shadow-none"
                          >
                            <Award className="w-3.5 h-3.5" />
                            <span>{item.status === 'VERIFIED' ? 'VERIFIED' : item.status === 'LOCKED' ? 'LOCKED — Verify prerequisites' : 'Verify Skill'}</span>
                          </button>
                        </div>
                      </div>
                    </div>
                  ));
                })}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
