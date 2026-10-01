import React, { useState, useEffect } from 'react';
import { 
  Sparkles, 
  ExternalLink, 
  CheckCircle2, 
  Clock, 
  ShieldCheck, 
  HelpCircle, 
  Layers, 
  Info, 
  Lock, 
  Play, 
  Award, 
  Sliders, 
  AlertCircle, 
  ChevronDown, 
  ChevronUp, 
  Zap, 
  Search,
  Filter,
  Check,
  RotateCcw,
  Loader2
} from 'lucide-react';
import { fetchGoalRoute } from '../services/api';

export default function RouteScreen({ 
  profile,
  goalId,
  routeOptimizationMode, 
  setRouteOptimizationMode, 
  onSwitchToGraphView, 
  onOpenProofModal,
  userState,
  onUpdateResourceState,
  replanKey,
  onGoalCreated,
}) {
  const [routeData, setRouteData] = useState(null); // { goal_id, total_hours, total_weeks, hours_per_week, phases }
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [expandedReasonId, setExpandedReasonId] = useState(null);

  const goalTitle = profile?.title || "Frontend Developer Internship";
  const hoursPerWeek = profile?.commitment || 10;
  const durationWeeks = profile?.sprints ? profile.sprints * 4 : 12;

  // Load real backend route & real learning resources
  const loadRoute = async () => {
    setLoading(true);
    setError(null);
    try {
      const rData = await fetchGoalRoute(goalId);
      setRouteData(rData);
    } catch (err) {
      console.error('[APOGEE Route API Error]', err);
      setError(err.message || 'Failed to load backend route');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadRoute();
  }, [goalId, replanKey]);

  const toggleReasonExpand = (rid) => {
    setExpandedReasonId(expandedReasonId === rid ? null : rid);
  };

  const handleOpenCourseLink = (resource) => {
    if (!resource.url) {
      alert(`No verified resource is currently catalogued for ${resource.target_skill_name || 'this skill'}.`);
      return;
    }
    window.location.assign(resource.url);
  };

  return (
    <div className="w-full max-w-6xl mx-auto px-4 py-6 flex flex-col gap-6">
      {/* Top Telemetry Header & Navigation Controls */}
      <div className="w-full rounded-2xl bg-surface-container border border-outline-variant/60 p-5 shadow-xl flex flex-col gap-4">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-4 border-b border-outline-variant/40">
          <div>
            <div className="flex items-center gap-2">
              <h2 className="text-xl font-bold text-on-surface font-headline-md">{goalTitle} Route · v{routeData?.version || 1}</h2>
              <span className="text-xs px-2.5 py-0.5 rounded-full bg-tertiary-container/30 text-tertiary border border-tertiary/30 font-bold">
                REAL BACKEND RESOURCES
              </span>
            </div>
            <p className="text-xs text-on-surface-variant mt-1">
              Deterministic route generated from verified real learning materials & total duration calculations.
            </p>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={onSwitchToGraphView}
              className="px-4 py-2.5 rounded-xl bg-primary text-on-primary font-bold text-xs flex items-center gap-2 hover:bg-primary/90 transition-all shadow-md shadow-indigo-900/30 cursor-pointer"
            >
              <Layers className="w-4 h-4" />
              <span>Open Skill Completion Graph</span>
            </button>
          </div>
        </div>

        {/* Telemetry Strip */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
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

          <div className="p-3 rounded-xl bg-surface-container-high border border-outline-variant/40 flex flex-col gap-0.5">
            <span className="text-[11px] text-outline font-semibold uppercase">Readiness Band</span>
            <div className="text-lg font-bold text-secondary font-mono">
              {userState.readinessBand ? `${userState.readinessBand.min}% – ${userState.readinessBand.max}%` : 'Pending'}
            </div>
            <span className="text-[10px] text-outline">
              {userState.readinessBand ? 'Average diagnostic score' : 'Complete diagnostic to set baseline'}
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
      </div>

      {routeData && !loading && !error && <p role="status" className={`p-4 rounded-xl border ${routeData.feasible ? 'text-tertiary' : 'text-amber-300'}`}>
        {routeData.feasibility_message}
      </p>}
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

      {/* Phased Route Timeline */}
      {!loading && !error && routeData?.phases && (
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

              {/* Resources List in Phase */}
              <div className="flex flex-col gap-4">
                {phase.resources.map((res, rIdx) => {
                  const isExpanded = expandedReasonId === (res.id || rIdx);

                  return (
                    <div 
                      key={res.id || rIdx}
                      className="rounded-2xl border bg-surface-container border-outline-variant/60 shadow-md transition-all"
                    >
                      <div className="p-5 flex flex-col md:flex-row md:items-center justify-between gap-4">
                        {/* Left info */}
                        <div className="flex flex-col gap-2 max-w-2xl">
                          <div className="flex flex-wrap items-center gap-2">
                            <span className="text-xs font-bold text-secondary bg-secondary-container/20 px-2.5 py-0.5 rounded border border-secondary/30">
                              {res.source}
                            </span>
                            <span className="text-xs text-outline flex items-center gap-1 font-mono">
                              <Clock className="w-3.5 h-3.5 text-outline" /> {res.duration_hours} hrs
                            </span>

                            {res.has_resource ? (
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
                            className={`text-base font-bold text-on-surface transition-colors ${res.url ? 'hover:text-primary cursor-pointer' : ''}`}
                            onClick={() => res.url && handleOpenCourseLink(res)}
                          >
                            {res.title}
                          </h4>

                          <div className="text-xs text-on-surface-variant flex items-center gap-2">
                            <span>Target Skill: <strong className="text-primary font-semibold">{res.target_skill_name}</strong></span>
                          </div>
                        </div>

                        {/* Right Actions */}
                        <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-2">
                          {/* Course Launch Button */}
                          <button
                            onClick={() => handleOpenCourseLink(res)}
                            disabled={!res.url}
                            className={`px-4 py-2 rounded-xl text-xs font-semibold flex items-center justify-center gap-1.5 transition-colors border ${
                              res.url
                                ? 'bg-surface-container-high hover:bg-surface-container-highest border-outline-variant/60 text-on-surface'
                                : 'bg-surface-container-low text-outline border-outline-variant/30 cursor-not-allowed'
                            }`}
                          >
                            <ExternalLink className="w-3.5 h-3.5 text-secondary" />
                            <span>{res.url ? 'Open Course' : 'No URL Available'}</span>
                          </button>

                          {/* Verify Skill Button */}
                          <button
                            disabled={res.status === 'LOCKED' || res.status === 'VERIFIED'}
                            onClick={() => onOpenProofModal({ id: res.skill_id, label: res.target_skill_name })}
                            className="px-4 py-2 rounded-xl bg-primary-container text-white font-bold text-xs flex items-center justify-center gap-1.5 hover:bg-indigo-600 transition-colors shadow"
                          >
                            <Award className="w-3.5 h-3.5" />
                            <span>{res.status === 'VERIFIED' ? 'VERIFIED' : res.status === 'LOCKED' ? 'LOCKED — Verify prerequisites' : 'Verify Skill'}</span>
                          </button>
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
