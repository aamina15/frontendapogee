import React from 'react';
import { 
  Award, 
  X, 
  Printer, 
  Download, 
  CheckCircle2, 
  GitBranch, 
  Briefcase, 
  Sparkles,
  ShieldCheck,
  FileText
} from 'lucide-react';

export default function CareerPackModal({ profile, userState, onClose }) {
  const handlePrint = () => {
    window.print();
  };

  return (
    <div className="fixed inset-0 z-50 bg-black/75 backdrop-blur-sm flex items-center justify-center p-4">
      <div className="w-full max-w-4xl bg-surface-container border border-outline-variant/60 rounded-2xl shadow-2xl overflow-hidden flex flex-col max-h-[90vh]">
        {/* Header */}
        <div className="p-5 bg-surface-container-high border-b border-outline-variant/50 flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="w-9 h-9 rounded-xl bg-tertiary-container/40 text-tertiary flex items-center justify-center border border-tertiary/40">
              <Award className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-base font-bold text-on-surface font-headline-sm">Career Output Pack (N7)</h3>
              <p className="text-xs text-on-surface-variant">Verified skill credentials, resume bullets, and readiness telemetry report</p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={handlePrint}
              className="px-3.5 py-1.5 rounded-xl bg-primary text-on-primary font-bold text-xs flex items-center gap-1.5 shadow hover:bg-primary/90 transition-colors"
            >
              <Printer className="w-4 h-4" />
              <span>Export PDF / Print</span>
            </button>
            <button onClick={onClose} className="p-1.5 rounded-lg text-outline hover:text-on-surface hover:bg-surface-container-highest">
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Exportable PDF Document Preview Body */}
        <div className="p-8 overflow-y-auto flex flex-col gap-6 bg-surface-container-lowest text-on-surface border border-outline-variant/30 m-4 rounded-xl shadow-inner">
          {/* Document Header */}
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-6 border-b border-outline-variant/50">
            <div>
              <div className="flex items-center gap-2">
                <span className="text-xl font-bold tracking-wider font-headline-md text-primary">APOGEE</span>
                <span className="text-xs font-bold text-tertiary bg-tertiary-container/30 px-2.5 py-0.5 rounded-full border border-tertiary/40">
                  VERIFIED CREDENTIAL
                </span>
              </div>
              <h1 className="text-2xl font-bold text-on-surface mt-1">{userState.userName}</h1>
              <p className="text-xs text-on-surface-variant">{profile.role} — {profile.spec}</p>
            </div>

            <div className="p-3 rounded-xl bg-surface-container border border-outline-variant/40 flex flex-col items-end text-xs font-mono">
              <span className="text-outline">Readiness Score:</span>
              <span className="text-lg font-bold text-secondary">{userState.readinessBand.min}% – {userState.readinessBand.max}%</span>
              <span className="text-[10px] text-tertiary">Verified Proof Signal</span>
            </div>
          </div>

          {/* Section 1: Verified Skills Matrix */}
          <div className="flex flex-col gap-3">
            <h3 className="text-sm font-bold text-on-surface uppercase tracking-wider flex items-center gap-2 border-b border-outline-variant/30 pb-1">
              <ShieldCheck className="w-4 h-4 text-tertiary" />
              1. Verified Skills Matrix
            </h3>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {profile.skillNodes.map((node) => (
                <div key={node.id} className="p-3 rounded-xl bg-surface-container border border-outline-variant/40 flex items-center justify-between text-xs">
                  <div>
                    <strong className="text-on-surface">{node.label}</strong>
                    <div className="text-[10px] text-outline">{node.category} • {node.level}</div>
                  </div>
                  <span className={`px-2 py-0.5 rounded font-bold font-mono text-[10px] ${node.status === 'Verified' ? 'bg-tertiary-container/40 text-tertiary border border-tertiary/40' : 'bg-surface-container-high text-outline'}`}>
                    {node.status.toUpperCase()} ({node.mastery}%)
                  </span>
                </div>
              ))}
            </div>
          </div>

          {/* Section 2: Verified Project Portfolio */}
          <div className="flex flex-col gap-3">
            <h3 className="text-sm font-bold text-on-surface uppercase tracking-wider flex items-center gap-2 border-b border-outline-variant/30 pb-1">
              <GitBranch className="w-4 h-4 text-secondary" />
              2. Verified Artifact Portfolio
            </h3>

            <div className="p-4 rounded-xl bg-surface-container border border-outline-variant/40 flex flex-col gap-2 text-xs">
              <div className="flex items-center justify-between">
                <span className="font-bold text-on-surface">PyTorch Vectorized Autograd & ResNet Vision Engine</span>
                <span className="text-tertiary font-mono font-bold">Grade: 94/100 (Verified)</span>
              </div>
              <p className="text-on-surface-variant text-[11px]">
                Built a custom tensor autograd engine in Python/PyTorch with gradient backpropagation and ResNet skip-connection architecture.
              </p>
              <div className="text-[10px] font-mono text-secondary">
                Repository: https://github.com/aamina-hasan/pytorch-autograd-engine
              </div>
            </div>
          </div>

          {/* Section 3: Tailored Resume Bullets */}
          <div className="flex flex-col gap-3">
            <h3 className="text-sm font-bold text-on-surface uppercase tracking-wider flex items-center gap-2 border-b border-outline-variant/30 pb-1">
              <Briefcase className="w-4 h-4 text-primary" />
              3. Verified Resume Experience Bullets
            </h3>

            <div className="flex flex-col gap-2 text-xs text-on-surface-variant">
              <div className="p-3 rounded-xl bg-surface-container border border-outline-variant/40 leading-relaxed">
                • Engineered modular PyTorch deep learning pipelines for computer vision tasks, implementing vector tensor operations and optimizing GPU memory bandwidth.
              </div>
              <div className="p-3 rounded-xl bg-surface-container border border-outline-variant/40 leading-relaxed">
                • Verified foundational linear algebra and calculus principles, designing loss functions and backpropagation engines with 0 prerequisite violations across 180 hours of coursework.
              </div>
            </div>
          </div>

          {/* Document Footer */}
          <div className="pt-4 border-t border-outline-variant/40 flex items-center justify-between text-[11px] text-outline">
            <span>Generated by APOGEE Skill Intelligence Platform</span>
            <span>Document ID: APG-2026-AH-9942</span>
          </div>
        </div>
      </div>
    </div>
  );
}
