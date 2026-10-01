import React from 'react';
import { 
  BarChart3, 
  Calendar, 
  Award, 
  Sparkles, 
  Compass, 
  CheckCircle2, 
  User, 
  Zap, 
  Layers,
  FileText
} from 'lucide-react';

export default function Header({ 
  activeStep, 
  setActiveStep, 
  onOpenMarketPulse, 
  onOpenCalendarRePlan, 
  onOpenCareerPack,
  userName,
  readinessBand,
  apiStatus = 'online'
}) {
  const steps = [
    { id: 1, label: "1. Goal", icon: Compass },
    { id: 2, label: "2. Diagnose", icon: Zap },
    { id: 3, label: "3. Build Route", icon: Layers },
    { id: 4, label: "4. Learn & Verify", icon: Award }
  ];

  return (
    <header className="w-full bg-surface-container-low/90 backdrop-blur-md border-b border-outline-variant/40 sticky top-0 z-40 px-4 lg:px-8 py-3">
      <div className="max-w-7xl mx-auto flex flex-col md:flex-row items-center justify-between gap-3">
        {/* Brand & Online Telemetry */}
        <div className="flex items-center justify-between w-full md:w-auto gap-4">
          <div className="flex items-center gap-3 cursor-pointer" onClick={() => setActiveStep(1)}>
            <div className="w-9 h-9 rounded-xl bg-primary-container/20 p-1.5 flex items-center justify-center border border-primary/30 shadow-sm relative overflow-hidden group">
              <img src="/apogee-logo.svg" alt="APOGEE" className="w-full h-full object-contain group-hover:rotate-12 transition-transform duration-300" />
            </div>
            <div className="flex flex-col">
              <div className="flex items-center gap-2">
                <span className="font-headline-sm font-bold text-on-surface tracking-wider text-base">APOGEE</span>
                <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-bold border ${
                  apiStatus === 'online'
                    ? 'bg-tertiary-container/30 text-tertiary border-tertiary/30'
                    : 'bg-amber-950/40 text-amber-400 border-amber-500/40'
                }`}>
                  <span className={`w-1.5 h-1.5 rounded-full ${apiStatus === 'online' ? 'bg-tertiary animate-ping' : 'bg-amber-400'}`}></span>
                  {apiStatus === 'online' ? 'API: ONLINE' : apiStatus === 'offline' ? 'API: OFFLINE' : 'API: CONNECTING'}
                </span>
              </div>
              <span className="text-[11px] text-on-surface-variant/80 font-medium">Skill Intelligence & Learning Navigator</span>
            </div>
          </div>

          {/* User profile / Readiness Pill on mobile */}
          <div className="flex md:hidden items-center gap-2">
            <span className="text-xs font-bold text-secondary bg-secondary-container/20 px-2.5 py-1 rounded-lg border border-secondary/30">
              {readinessBand ? `Readiness ${readinessBand.min}%–${readinessBand.max}%` : 'Readiness: Pending'}
            </span>
          </div>
        </div>

        {/* 4-Step Navigation Bar */}
        <nav className="flex items-center gap-1 bg-surface-container-lowest/80 p-1.5 rounded-xl border border-outline-variant/40 w-full md:w-auto justify-center overflow-x-auto">
          {steps.map((step) => {
            const Icon = step.icon;
            const isActive = activeStep === step.id;
            const isDone = activeStep > step.id;

            return (
              <button
                key={step.id}
                onClick={() => setActiveStep(step.id)}
                className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all whitespace-nowrap ${
                  isActive
                    ? 'bg-primary text-on-primary font-bold shadow-md shadow-indigo-900/40'
                    : isDone
                    ? 'text-tertiary hover:bg-surface-container-high'
                    : 'text-on-surface-variant hover:text-on-surface hover:bg-surface-container-high/50'
                }`}
              >
                {isDone ? (
                  <CheckCircle2 className="w-3.5 h-3.5 text-tertiary" />
                ) : (
                  <Icon className={`w-3.5 h-3.5 ${isActive ? 'text-on-primary' : ''}`} />
                )}
                <span>{step.label}</span>
              </button>
            );
          })}
        </nav>

        {/* Action Controls */}
        <div className="flex items-center gap-2.5">
          {/* Smart Re-plan trigger - Core MVP action available after a route exists */}
          {activeStep >= 3 && (
            <button
              onClick={onOpenCalendarRePlan}
              className="flex items-center gap-1.5 px-3.5 py-1.5 rounded-xl bg-tertiary-container/30 hover:bg-tertiary-container/50 border border-tertiary/40 text-tertiary text-xs font-bold transition-colors shadow-sm"
              title="Replan route when weekly availability changes"
            >
              <Calendar className="w-3.5 h-3.5 text-tertiary" />
              <span>Smart Re-plan</span>
            </button>
          )}

          {/* Profile User avatar */}
          <div className="flex items-center gap-2 pl-2 border-l border-outline-variant/40">
            <div className="w-7 h-7 rounded-full bg-primary-container text-white text-xs font-bold flex items-center justify-center border border-indigo-400/40">
              AH
            </div>
          </div>
        </div>
      </div>
    </header>
  );
}
