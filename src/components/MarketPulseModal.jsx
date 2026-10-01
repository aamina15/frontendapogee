import React from 'react';
import { 
  BarChart3, 
  X, 
  TrendingUp, 
  DollarSign, 
  Calendar, 
  ShieldCheck, 
  Sparkles,
  Info
} from 'lucide-react';

export default function MarketPulseModal({ profile, onClose }) {
  const mp = profile.marketPulse;

  if (!mp) return null;

  return (
    <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
      <div className="w-full max-w-3xl bg-surface-container border border-outline-variant/60 rounded-2xl shadow-2xl overflow-hidden flex flex-col max-h-[90vh]">
        {/* Header */}
        <div className="p-5 bg-surface-container-high border-b border-outline-variant/50 flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="w-9 h-9 rounded-xl bg-secondary-container/40 text-secondary flex items-center justify-center border border-secondary/40">
              <BarChart3 className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-base font-bold text-on-surface font-headline-sm">Market Pulse Intelligence (N1)</h3>
              <p className="text-xs text-on-surface-variant">Live job postings demand grounded in real market data (FR7)</p>
            </div>
          </div>

          <button onClick={onClose} className="p-1.5 rounded-lg text-outline hover:text-on-surface hover:bg-surface-container-highest">
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content */}
        <div className="p-6 overflow-y-auto flex flex-col gap-5">
          {/* Top Telemetry Grid */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            <div className="p-3.5 rounded-xl bg-surface-container-high border border-outline-variant/40 flex flex-col gap-0.5">
              <span className="text-[11px] text-outline font-semibold uppercase">Job Postings Sample</span>
              <span className="text-lg font-bold text-on-surface font-mono">{mp.sampleSize}</span>
              <span className="text-[10px] text-tertiary font-medium">{mp.updatedDate}</span>
            </div>

            <div className="p-3.5 rounded-xl bg-surface-container-high border border-outline-variant/40 flex flex-col gap-0.5">
              <span className="text-[11px] text-outline font-semibold uppercase">Demand Growth</span>
              <span className="text-lg font-bold text-tertiary font-mono">{mp.demandTrend}</span>
              <span className="text-[10px] text-outline">Q/Q Velocity</span>
            </div>

            <div className="p-3.5 rounded-xl bg-surface-container-high border border-outline-variant/40 flex flex-col gap-0.5 sm:col-span-2">
              <span className="text-[11px] text-outline font-semibold uppercase">Target Compensation Range</span>
              <span className="text-lg font-bold text-secondary font-mono">{mp.avgSalary}</span>
              <span className="text-[10px] text-outline">US Tech Market Base</span>
            </div>
          </div>

          {/* Skill Frequency & Weight Blend Table */}
          <div className="flex flex-col gap-3">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-on-surface uppercase tracking-wider flex items-center gap-1.5">
                <Sparkles className="w-4 h-4 text-secondary" />
                Live Skill Demand Frequency & Weight Blending
              </span>
              <span className="text-[10px] text-outline font-mono">FR7 Sample Grounding</span>
            </div>

            <div className="flex flex-col gap-2">
              {mp.topSkills.map((skill, idx) => (
                <div key={idx} className="p-3.5 rounded-xl bg-surface-container-lowest border border-outline-variant/40 flex flex-col gap-2">
                  <div className="flex justify-between items-center text-xs font-semibold">
                    <span className="text-on-surface">{skill.name}</span>
                    <span className="font-mono text-secondary font-bold">{skill.frequency}% of Job Postings</span>
                  </div>

                  <div className="h-2 w-full rounded-full bg-surface-container-high overflow-hidden">
                    <div 
                      className="h-full bg-gradient-to-r from-secondary to-tertiary rounded-full"
                      style={{ width: `${skill.frequency}%` }}
                    />
                  </div>

                  <div className="flex justify-between text-[10px] text-outline pt-0.5">
                    <span>Model Importance Weight: <strong className="text-on-surface-variant font-mono">{skill.modelWeight}</strong></span>
                    <span>Market Pulse Weight: <strong className="text-tertiary font-mono">{skill.marketWeight}</strong></span>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Explanation Footer */}
          <div className="p-4 rounded-xl bg-surface-container-high border border-outline-variant/40 text-xs flex items-start gap-2.5">
            <Info className="w-5 h-5 text-secondary shrink-0 mt-0.5" />
            <div className="text-on-surface-variant leading-relaxed text-[11px]">
              <strong>How Market Pulse Works:</strong> Apogee scans live job postings for <strong>{profile.role}</strong> and blends real hiring demand into the skill DAG weights. Skills required in &gt;80% of postings are prioritized in Phase 1 & 2 set-cover routes.
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
