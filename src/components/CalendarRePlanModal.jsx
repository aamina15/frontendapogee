import React, { useState } from 'react';
import {
  RotateCcw,
  X,
  CheckCircle2,
  Clock,
  ChevronRight,
  AlertCircle,
  Shield,
  ArrowRight,
  Loader2,
  ExternalLink,
  Zap,
} from 'lucide-react';
import { replanGoal } from '../services/api';

export default function CalendarRePlanModal({
  userState,
  goalId,
  currentHoursPerWeek,
  onClose,
  onApplyRePlan,
}) {
  const [newHours, setNewHours] = useState(currentHoursPerWeek || 10);
  const [isReplanning, setIsReplanning] = useState(false);
  const [receipt, setReceipt] = useState(null);
  const [error, setError] = useState(null);

  const handleReplan = async () => {
    if (!goalId) {
      setError('No active goal found. Complete the intake form first.');
      return;
    }
    if (newHours === currentHoursPerWeek) {
      setError('New hours per week is the same as the current value — no replan needed.');
      return;
    }

    setIsReplanning(true);
    setError(null);
    setReceipt(null);

    try {
      const data = await replanGoal(goalId, { hours_per_week: Number(newHours) });
      setReceipt(data);
      onApplyRePlan(data);
    } catch (err) {
      setError(err.message || 'Replan request failed. Check the backend is running.');
    } finally {
      setIsReplanning(false);
    }
  };

  const handleApply = () => {
    onClose();
  };

  const rescheduledChanges = receipt?.changes?.filter(c => c.change_type === 'rescheduled') || [];
  const preservedChanges = receipt?.changes?.filter(c => c.change_type === 'preserved_verified') || [];

  return (
    <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
      <div className="w-full max-w-2xl bg-surface-container border border-outline-variant/60 rounded-2xl shadow-2xl overflow-hidden flex flex-col max-h-[92vh]">

        {/* Header */}
        <div className="p-5 bg-surface-container-high border-b border-outline-variant/50 flex items-center justify-between shrink-0">
          <div className="flex items-center gap-2.5">
            <div className="w-9 h-9 rounded-xl bg-secondary-container/40 text-secondary flex items-center justify-center border border-secondary/40">
              <RotateCcw className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-base font-bold text-on-surface font-headline-sm">
                Smart Re-Plan — Change Weekly Hours
              </h3>
              <p className="text-xs text-on-surface-variant">
                Deterministic replanner — preserves VERIFIED skills, recalculates the full schedule
              </p>
            </div>
          </div>
          <button aria-label="Close replan" onClick={onClose} className="p-1.5 rounded-lg text-outline hover:text-on-surface hover:bg-surface-container-highest transition-colors">
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Body */}
        <div className="p-6 overflow-y-auto flex flex-col gap-5">

          {/* Input panel — always visible */}
          <div className="p-4 rounded-xl bg-surface-container-lowest border border-outline-variant/40 flex flex-col gap-4">
            <div className="flex items-center gap-2 text-xs font-semibold text-on-surface">
              <Clock className="w-4 h-4 text-secondary" />
              <span>Update Weekly Learning Hours</span>
            </div>

            <div className="flex flex-col sm:flex-row sm:items-center gap-4">
              <div className="flex-1">
                <label className="text-[11px] text-outline uppercase tracking-wider font-semibold mb-1.5 block">
                  Current: {currentHoursPerWeek}h/week
                </label>
                <div className="flex items-center gap-3">
                  <input
                    aria-label="Weekly learning hours"
                    type="number"
                    min={1}
                    max={40}
                    step={1}
                    value={newHours}
                    onChange={e => setNewHours(Number(e.target.value))}
                    className="flex-1 accent-indigo-500 cursor-pointer"
                    disabled={isReplanning}
                  />
                  <span className="text-lg font-bold text-on-surface font-mono w-16 text-right">
                    {newHours}h<span className="text-xs text-outline font-normal">/wk</span>
                  </span>
                </div>
              </div>

              {/* Quick presets */}
              <div className="flex gap-1.5 flex-wrap">
                {[3, 5, 7, 10, 15, 20].map(h => (
                  <button
                    key={h}
                    onClick={() => setNewHours(h)}
                    disabled={isReplanning}
                    className={`px-2.5 py-1 rounded-lg text-[11px] font-bold border transition-colors ${
                      newHours === h
                        ? 'bg-primary text-on-primary border-primary'
                        : 'bg-surface-container text-on-surface-variant border-outline-variant/60 hover:border-primary/50 hover:text-primary'
                    }`}
                  >
                    {h}h
                  </button>
                ))}
              </div>
            </div>

            {receipt && (
            <div role="status" className={`flex items-center gap-2 px-3 py-2 rounded-lg border text-sm ${
              receipt.route.feasible && !receipt.route.missing_resources?.length
                ? 'bg-tertiary/10 border-tertiary/30 text-tertiary'
                : 'bg-amber-900/30 border-amber-500/30 text-amber-300'
            }`}>
              {receipt.route.missing_resources?.length > 0 ? (
                <>
                  <AlertCircle className="w-4 h-4 flex-shrink-0" />
                  <span>Missing resources for: <strong>{receipt.route.missing_resources.join(', ')}</strong>. Estimates used for scheduling.</span>
                </>
              ) : receipt.route.feasible ? (
                <>
                  <CheckCircle2 className="w-4 h-4 flex-shrink-0" />
                  <span>{receipt.route.feasibility_message}</span>
                </>
              ) : (
                <>
                  <AlertCircle className="w-4 h-4 flex-shrink-0" />
                  <span>{receipt.route.feasibility_message}</span>
                </>
              )}
            </div>
          )}
            {/* Arrow preview */}
            {newHours !== currentHoursPerWeek && (
              <div className="flex items-center gap-2 text-xs font-semibold">
                <span className="px-2 py-0.5 rounded bg-surface-container-high text-outline font-mono">
                  {currentHoursPerWeek}h/week
                </span>
                <ArrowRight className="w-4 h-4 text-secondary" />
                <span className="px-2 py-0.5 rounded bg-secondary-container/30 text-secondary font-mono border border-secondary/30">
                  {newHours}h/week
                </span>
              </div>
            )}
          </div>

          {/* Error */}
          {error && (
            <div role="alert" className="p-3 rounded-xl bg-rose-950/40 border border-rose-500/50 flex items-start gap-2 text-xs text-rose-300">
              <AlertCircle className="w-4 h-4 mt-0.5 shrink-0" />
              <span>{error}</span>
            </div>
          )}

          {/* Receipt */}
          {receipt && !isReplanning && (
            <div className="flex flex-col gap-4 animate-fadeIn">

              {/* ROUTE UPDATED banner */}
              <div className="p-4 rounded-xl bg-tertiary-container/30 border border-tertiary/40 flex flex-col gap-3">
                <div className="flex items-center gap-2 font-bold text-sm text-tertiary">
                  <CheckCircle2 className="w-5 h-5" />
                  ROUTE UPDATED — Version {receipt.new_version}
                </div>

                {/* Change summary grid */}
                <div className="grid grid-cols-2 gap-3">
                  <div className="p-2.5 rounded-lg bg-surface-container-high border border-outline-variant/40 text-xs">
                    <div className="text-outline uppercase tracking-wide font-semibold text-[10px] mb-1">Weekly Availability</div>
                    <div className="flex items-center gap-1.5 font-bold text-on-surface font-mono">
                      <span className="text-outline">{receipt.previous_hours_per_week}h</span>
                      <ArrowRight className="w-3 h-3 text-secondary" />
                      <span className="text-secondary">{receipt.new_hours_per_week}h</span>
                    </div>
                  </div>
                  <div className="p-2.5 rounded-lg bg-surface-container-high border border-outline-variant/40 text-xs">
                    <div className="text-outline uppercase tracking-wide font-semibold text-[10px] mb-1">Route Version</div>
                    <div className="flex items-center gap-1.5 font-bold font-mono">
                      <span className="text-outline">v{receipt.previous_version}</span>
                      <ArrowRight className="w-3 h-3 text-secondary" />
                      <span className="text-tertiary">v{receipt.new_version}</span>
                    </div>
                  </div>
                  <div className="p-2.5 rounded-lg bg-surface-container-high border border-outline-variant/40 text-xs">
                    <div className="text-outline uppercase tracking-wide font-semibold text-[10px] mb-1">Total Hours</div>
                    <div className="font-bold font-mono text-on-surface">{receipt.route.total_hours}h</div>
                  </div>
                  <div className="p-2.5 rounded-lg bg-surface-container-high border border-outline-variant/40 text-xs">
                    <div className="text-outline uppercase tracking-wide font-semibold text-[10px] mb-1">New Horizon</div>
                    <div className="font-bold font-mono text-on-surface">{receipt.route.total_weeks} weeks</div>
                  </div>
                </div>
              </div>

              {/* Preserved verified skills */}
              {receipt.preserved_verified_skills.length > 0 && (
                <div className="p-3.5 rounded-xl bg-surface-container-high border border-outline-variant/50 flex flex-col gap-2">
                  <div className="flex items-center gap-1.5 text-xs font-bold text-tertiary uppercase tracking-wide">
                    <Shield className="w-3.5 h-3.5" />
                    Preserved (Already Verified)
                  </div>
                  <div className="flex flex-wrap gap-1.5">
                    {receipt.preserved_verified_skills.map((sk, i) => (
                      <span key={i} className="text-[11px] flex items-center gap-1 px-2.5 py-1 rounded-lg bg-tertiary-container/30 text-tertiary border border-tertiary/30 font-semibold">
                        <CheckCircle2 className="w-3 h-3" /> {sk}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {/* Rescheduled changes */}
              {rescheduledChanges.length > 0 && (
                <div className="p-3.5 rounded-xl bg-surface-container-high border border-outline-variant/50 flex flex-col gap-2">
                  <div className="flex items-center gap-1.5 text-xs font-bold text-secondary uppercase tracking-wide">
                    <Zap className="w-3.5 h-3.5" />
                    Rescheduled ({rescheduledChanges.length} skills)
                  </div>
                  <div className="flex flex-col gap-1">
                    {rescheduledChanges.map((c, i) => (
                      <div key={i} className="flex items-center justify-between text-xs text-on-surface-variant px-1">
                        <span className="font-medium text-on-surface truncate max-w-[200px]">{c.skill_name}</span>
                        <span className="flex items-center gap-1 font-mono shrink-0">
                          <span className="text-outline">{c.previous_duration_weeks}w</span>
                          <ArrowRight className="w-3 h-3 text-secondary" />
                          <span className="text-secondary font-bold">{c.new_duration_weeks}w</span>
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* New phased route preview */}
              <div className="flex flex-col gap-3">
                <span className="text-xs font-bold text-outline uppercase tracking-wider">
                  Recalculated Route
                </span>
                {receipt.route.phases.map(phase => (
                  <div key={phase.phase_num} className="p-3 rounded-xl bg-surface-container-lowest border border-outline-variant/40">
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center gap-2">
                        <span className="w-6 h-6 rounded-lg bg-primary-container text-white text-[10px] font-bold flex items-center justify-center">
                          P{phase.phase_num}
                        </span>
                        <span className="text-xs font-bold text-on-surface">{phase.title}</span>
                      </div>
                      <span className="text-[11px] font-mono text-outline">
                        {phase.hours_total}h · {phase.duration_weeks}wk
                      </span>
                    </div>
                    <div className="flex flex-col gap-1">
                      {phase.resources.map((res, ri) => (
                        <div key={ri} className="flex items-center justify-between text-[11px] px-1">
                          <span className={`flex items-center gap-1 ${res.has_resource ? 'text-on-surface-variant' : 'text-amber-400'}`}>
                            {res.has_resource
                              ? <CheckCircle2 className="w-3 h-3 text-tertiary shrink-0" />
                              : <AlertCircle className="w-3 h-3 shrink-0" />
                            }
                            <span className="truncate max-w-[240px]">{res.title}</span>
                          </span>
                          <span className="font-mono text-outline shrink-0">{res.duration_hours}h</span>
                        </div>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* CTA buttons */}
          <div className="flex flex-col gap-2 mt-1">
            {!receipt ? (
              <button
                onClick={handleReplan}
                disabled={isReplanning || newHours === currentHoursPerWeek}
                className={`w-full py-3.5 px-4 rounded-xl font-bold text-xs md:text-sm flex items-center justify-center gap-2 transition-all ${
                  isReplanning || newHours === currentHoursPerWeek
                    ? 'bg-surface-container text-outline border border-outline-variant/40 cursor-not-allowed'
                    : 'bg-secondary-container/50 text-secondary border border-secondary/50 hover:bg-secondary-container/70 cursor-pointer'
                }`}
              >
                {isReplanning ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" />
                    <span>Running Deterministic Replan...</span>
                  </>
                ) : (
                  <>
                    <RotateCcw className="w-4 h-4" />
                    <span>
                      {newHours === currentHoursPerWeek
                        ? 'Adjust hours above to replan'
                        : `Replan at ${newHours}h/week`}
                    </span>
                  </>
                )}
              </button>
            ) : (
              <button
                onClick={handleApply}
                className="w-full py-3.5 px-4 rounded-xl bg-primary text-on-primary font-bold text-xs md:text-sm flex items-center justify-center gap-2 hover:bg-primary/90 transition-all cursor-pointer shadow-lg shadow-indigo-900/30"
              >
                <span>View Updated Route</span>
                <ChevronRight className="w-4 h-4" />
              </button>
            )}

            {receipt && (
              <button
                onClick={() => { setReceipt(null); setError(null); }}
                className="text-xs text-outline hover:text-on-surface text-center py-1 transition-colors"
              >
                ← Adjust hours again
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
