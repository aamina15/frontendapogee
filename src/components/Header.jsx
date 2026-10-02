import { Calendar, Award, Compass, Zap, Layers, Lock } from 'lucide-react';

const steps = [
  { id: 1, label: 'Goal', icon: Compass },
  { id: 2, label: 'Diagnose', icon: Zap },
  { id: 3, label: 'Build Route', icon: Layers },
  { id: 4, label: 'Learn & Verify', icon: Award },
];

export default function Header({ activeStep, setActiveStep, onOpenCalendarRePlan, onOpenHome, hasGraph, routeReady, busy, readinessBand, apiStatus = 'checking' }) {
  return (
    <header className="app-header sticky top-0 z-40 border-b border-white/10 bg-surface/95 backdrop-blur-xl">
      <div className="max-w-7xl mx-auto px-4 lg:px-8 py-4 flex flex-wrap items-center justify-between gap-3">
        <button onClick={onOpenHome} disabled={busy} aria-label="ORBIT Home" className="flex items-center gap-2.5 rounded-xl disabled:opacity-50">
          <img src="/orbit-logo.svg" alt="" className="w-8 h-8" />
          <span className="text-sm font-headline-sm font-bold tracking-[0.15em]">ORBIT</span>
        </button>
        <nav aria-label="Learning journey" className="journey-nav order-3 lg:order-none w-full lg:w-auto grid grid-cols-4 gap-1 rounded-2xl border border-white/10 bg-surface-container-lowest p-1.5">
          {steps.map(({ id, label, icon: Icon }) => {
            const unavailable = id > 1 && !hasGraph || id > 2 && !routeReady;
            const reason = id > 1 && !hasGraph ? 'Create your goal first' : id > 2 && !routeReady ? 'Complete or skip your diagnostic first' : '';
            return <button key={id} disabled={busy || unavailable} title={busy ? 'Please wait while your progress is saved or loaded' : reason || label}
              aria-current={activeStep === id ? 'step' : undefined}
              onClick={() => setActiveStep(id)}
              className={`journey-step flex items-center justify-center gap-2 rounded-xl px-3 py-3 text-xs font-semibold transition-colors ${activeStep === id ? 'bg-primary-container text-white shadow-lg shadow-indigo-950/40' : 'text-on-surface-variant hover:bg-white/5 hover:text-white'} disabled:opacity-40 disabled:cursor-not-allowed`}>
              {unavailable ? <Lock className="w-3.5 h-3.5 shrink-0" /> : <Icon className="w-3.5 h-3.5 shrink-0" />}
              <span>{id}. {label}</span>
            </button>;
          })}
        </nav>
        <div className="flex items-center gap-2">
          <div className="text-right"><span role="status" className={`text-[10px] tracking-wider font-semibold ${apiStatus === 'online' ? 'text-tertiary' : 'text-amber-300'}`}>● {apiStatus === 'online' ? 'CONNECTED' : apiStatus === 'offline' ? 'OFFLINE' : 'CONNECTING'}</span><span className="block text-[10px] text-outline">{readinessBand ? `Diagnostic estimate ${readinessBand.min === readinessBand.max ? `${readinessBand.min}%` : `${readinessBand.min}%–${readinessBand.max}%`}` : 'Diagnostic pending'}</span></div>
          {routeReady && <button disabled={busy} onClick={onOpenCalendarRePlan} className="btn-secondary text-xs !px-2 !py-2" title="Adjust your weekly availability"><Calendar className="w-4 h-4" />Smart Re-plan</button>}
        </div>
      </div>
      {!hasGraph && !busy && <p className="lg:hidden px-4 pb-3 text-xs text-outline">Create your goal to unlock the next steps.</p>}
    </header>
  );
}
