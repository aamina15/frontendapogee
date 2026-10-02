import { useState } from 'react';
import { ArrowRight, Compass, Clock3, CalendarDays, Wallet, Sparkles, Loader2 } from 'lucide-react';
import { MISSION_PROFILES } from '../data/mockData';

const budgetOptions = [
  { value: '0', label: 'Free', description: 'Use free learning resources.' },
  { value: '50', label: 'Low Cost · up to $50', description: 'A total learning budget of up to $50.' },
  { value: '150', label: 'Moderate · up to $150', description: 'A total learning budget of up to $150.' },
  { value: '500', label: 'Premium · up to $500', description: 'A total learning budget of up to $500.' },
  { value: 'any', label: 'No Preference', description: 'No budget preference. Free resources are still included.' },
];

export default function IntakeScreen({ currentProfile, onSelectProfile, onStartDiagnostic, busy, error }) {
  const [title, setTitle] = useState(currentProfile?.title || 'Frontend Developer Internship');
  const [hours, setHours] = useState(currentProfile?.commitment || 7);
  const [weeks, setWeeks] = useState(currentProfile?.duration_weeks || 8);
  const [budget, setBudget] = useState(currentProfile?.budget === null ? 'any' : String(currentProfile?.budget ?? 0));
  const [validation, setValidation] = useState(null);
  const selectedBudget = budgetOptions.find(option => option.value === budget);

  const submit = event => {
    event.preventDefault();
    if (title.trim().length < 3 || title.trim().length > 300) {
      setValidation('Enter a goal between 3 and 300 characters.');
      return;
    }
    setValidation(null);
    onStartDiagnostic({ title: title.trim(), hours_per_week: Number(hours), duration_weeks: Number(weeks), budget: budget === 'any' ? null : Number(budget) });
  };

  return (
    <section className="intake-shell max-w-5xl mx-auto px-4 py-10 sm:py-16">
      <div className="mb-9 max-w-2xl">
        <p className="eyebrow mb-4"><Compass className="w-4 h-4" />01 / SET YOUR DIRECTION</p>
        <h1 className="text-3xl sm:text-4xl font-headline-lg font-bold tracking-tight mb-4">A clear goal.<br /><span className="text-gradient">A path built around you.</span></h1>
        <p className="text-on-surface-variant leading-relaxed">Tell us where you want to go and the time you have. Your skill map, starting assessment, and learning route begin here.</p>
      </div>
      <form onSubmit={submit} className="intake-card rounded-3xl border border-white/10 p-5 sm:p-8 shadow-2xl shadow-black/20 flex flex-col gap-7">
        <div>
          <label htmlFor="learning-goal" className="label-text">What would you like to achieve?</label>
          <input id="learning-goal" aria-label="Goal" aria-describedby="goal-help" value={title} onChange={e => setTitle(e.target.value)} maxLength={300} required disabled={busy} className="input-field text-base sm:text-lg" placeholder="e.g. Frontend Developer Internship" />
          <p id="goal-help" className="mt-2 text-xs text-outline">A role, a project, or a skill you want to develop.</p>
        </div>
        <div>
          <p className="text-xs text-outline mb-3">Need a starting point?</p>
          <div className="flex flex-wrap gap-2">
            {MISSION_PROFILES.map(profile => <button key={profile.id} type="button" disabled={busy} aria-pressed={title === profile.title}
              className="preset-chip px-3 py-2 rounded-full border border-white/10 text-xs text-on-surface-variant hover:border-secondary/40 hover:text-secondary transition-colors aria-pressed:border-secondary/40 aria-pressed:bg-secondary/10"
              onClick={() => { onSelectProfile(profile.id); setTitle(profile.title); setHours(profile.commitment); }}>
              {profile.title}
            </button>)}
          </div>
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-5 pt-6 border-t border-white/10">
          <div><label htmlFor="weekly-hours" className="label-text flex items-center gap-2"><Clock3 className="w-4 h-4 text-secondary" />Hours per week</label><input id="weekly-hours" type="number" min="1" max="168" step="0.5" required disabled={busy} value={hours} onChange={e => setHours(e.target.value)} className="input-field" /></div>
          <div><label htmlFor="duration-weeks" className="label-text flex items-center gap-2"><CalendarDays className="w-4 h-4 text-primary" />Duration (weeks)</label><input id="duration-weeks" type="number" min="1" max="104" required disabled={busy} value={weeks} onChange={e => setWeeks(e.target.value)} className="input-field" /></div>
          <div><label htmlFor="learning-budget" className="label-text flex items-center gap-2"><Wallet className="w-4 h-4 text-secondary" />Budget</label><select id="learning-budget" value={budget} disabled={busy} onChange={e => setBudget(e.target.value)} aria-describedby="budget-help" className="input-field">{!selectedBudget && <option value={budget}>Custom · ${budget}</option>}{budgetOptions.map(option => <option key={option.value} value={option.value}>{option.label}</option>)}</select></div>
        </div>
        <p id="budget-help" className="text-xs text-outline leading-relaxed -mt-3">{selectedBudget?.description || `Your saved total budget is $${budget}.`} The current resource catalogue is free; paid course recommendations are not available yet.</p>
        {(validation || error) && <p role="alert" className="rounded-xl border border-rose-400/30 bg-rose-400/10 p-4 text-sm text-rose-200">{validation || error}</p>}
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-5 pt-2">
          <p className="text-sm text-on-surface-variant flex items-center gap-2"><Sparkles className="w-4 h-4 text-secondary shrink-0" />{Number(hours) * Number(weeks) || 0} hours to invest in your next step</p>
          <button type="submit" disabled={busy} className="btn-primary w-full sm:w-auto">
            {busy ? <><Loader2 className="w-4 h-4 animate-spin" />Building your skill map…</> : <>Build My Capability Map<ArrowRight className="w-4 h-4" /></>}
          </button>
        </div>
      </form>
    </section>
  );
}
