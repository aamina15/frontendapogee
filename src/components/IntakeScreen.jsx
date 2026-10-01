import React, { useState } from 'react';
import { MISSION_PROFILES } from '../data/mockData';

export default function IntakeScreen({ currentProfile, onSelectProfile, onStartDiagnostic, busy, error }) {
  const [title, setTitle] = useState(currentProfile?.title || 'Frontend Developer Internship');
  const [hours, setHours] = useState(currentProfile?.commitment || 7);
  const [weeks, setWeeks] = useState(currentProfile?.duration_weeks || 8);
  const [budget, setBudget] = useState(0);
  const [validation, setValidation] = useState(null);
  const fieldClass = 'w-full mt-2 p-3 rounded-xl bg-surface-container-high border border-outline-variant/60 text-on-surface';

  const submit = (event) => {
    event.preventDefault();
    if (title.trim().length < 3 || title.trim().length > 300) {
      setValidation('Enter a goal between 3 and 300 characters.');
      return;
    }
    setValidation(null);
    onStartDiagnostic({ title: title.trim(), hours_per_week: Number(hours), duration_weeks: Number(weeks), budget: Number(budget) });
  };

  return (
    <form onSubmit={submit} className="w-full max-w-4xl mx-auto px-4 py-10 flex flex-col gap-6">
      <h1 className="text-3xl font-bold">Build your learning route</h1>
      <p className="text-on-surface-variant">Set your goal and time budget, diagnose your starting skills, then learn and verify your progress.</p>
      <div className="flex flex-wrap gap-2">
        {MISSION_PROFILES.map(profile => <button key={profile.id} type="button" disabled={busy}
          className="px-3 py-2 rounded-xl border border-outline-variant/60 text-sm"
          onClick={() => { onSelectProfile(profile.id); setTitle(profile.title); setHours(profile.commitment); }}>
          {profile.title}
        </button>)}
      </div>
      <label className="font-semibold">Goal
        <input aria-label="Goal" value={title} onChange={e => setTitle(e.target.value)} maxLength={300} disabled={busy} className={fieldClass} />
      </label>
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <label>Hours per week<input aria-label="Hours per week" type="number" min="1" max="168" step="0.5" required disabled={busy} value={hours} onChange={e => setHours(e.target.value)} className={fieldClass} /></label>
        <label>Duration (weeks)<input aria-label="Duration (weeks)" type="number" min="1" max="104" required disabled={busy} value={weeks} onChange={e => setWeeks(e.target.value)} className={fieldClass} /></label>
        <label>Budget<select aria-label="Budget" value={budget} disabled={busy} onChange={e => setBudget(e.target.value)} className={fieldClass}><option value="0">Free</option></select></label>
      </div>
      {(validation || error) && <p role="alert" className="text-rose-300">{validation || error}</p>}
      <button type="submit" disabled={busy} className="py-4 rounded-xl bg-primary text-on-primary font-bold disabled:opacity-50">
        {busy ? 'Saving goal and generating skill graph…' : 'Build My Capability Map'}
      </button>
    </form>
  );
}
