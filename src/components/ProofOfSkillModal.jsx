import React, { useState, useEffect } from 'react';
import {
  Award,
  X,
  CheckCircle2,
  XCircle,
  Sparkles,
  ShieldCheck,
  Cpu,
  ChevronRight,
  AlertCircle,
  Loader2,
  RotateCcw,
  Lock,
  Unlock,
} from 'lucide-react';
import confetti from 'canvas-confetti';
import { fetchVerificationQuestions, submitVerification } from '../services/api';

/**
 * ProofOfSkillModal — Quiz-based skill verification (MVP)
 *
 * Props:
 *   resourceOrNode   - { id (slug), db_id (int), label, targetSkillName }
 *   goalId           - integer goal id (required for API calls)
 *   onClose          - () => void
 *   onVerifySuccess  - (receipt) => void  — called on PASS with the full receipt
 */
export default function ProofOfSkillModal({
  resourceOrNode,
  goalId,
  onClose,
  onVerifySuccess,
}) {
  // skill metadata
  const skillName =
    resourceOrNode?.targetSkillName ||
    resourceOrNode?.label ||
    resourceOrNode?.name ||
    'Unknown Skill';

  // DB integer id — required for the backend endpoints
  const skillDbId =
    resourceOrNode?.db_id ||
    (typeof resourceOrNode?.id === 'number' ? resourceOrNode.id : null);

  // Quiz state
  const [phase, setPhase] = useState('loading'); // loading | quiz | submitting | result | error
  const [questions, setQuestions] = useState([]);
  const [threshold, setThreshold] = useState(70);
  const [answers, setAnswers] = useState({}); // { [questionId]: selectedOptionIndex }
  const [receipt, setReceipt] = useState(null);
  const [errorMsg, setErrorMsg] = useState(null);

  // Load questions on mount
  useEffect(() => {
    if (!goalId || !skillDbId) {
      setErrorMsg(
        skillDbId
          ? 'No active goal — complete the intake form first.'
          : 'Skill ID unavailable. Try opening verification from the graph view.'
      );
      setPhase('error');
      return;
    }

    fetchVerificationQuestions(goalId, skillDbId)
      .then(data => {
        setQuestions(data.questions || []);
        setThreshold(data.threshold ?? 70);
        setPhase('quiz');
      })
      .catch(err => {
        setErrorMsg(err.message || 'Failed to load verification questions.');
        setPhase('error');
      });
  }, [goalId, skillDbId]);

  const allAnswered = questions.length > 0 && questions.every(q => answers[q.id] !== undefined);

  const handleSubmit = async () => {
    if (!allAnswered) return;
    setPhase('submitting');
    try {
      const answerList = Object.entries(answers).map(([qid, sel]) => ({
        question_id: Number(qid),
        selected_option: sel,
      }));
      const data = await submitVerification(goalId, skillDbId, answerList);
      setReceipt(data);
      setPhase('result');

      if (data.passed) {
        onVerifySuccess(data);
        try {
          confetti({ particleCount: 90, spread: 70, origin: { y: 0.6 } });
        } catch (_) {}
      }
    } catch (err) {
      setErrorMsg(err.message || 'Submission failed. Try again.');
      setPhase('error');
    }
  };

  const handleApply = () => {
    onClose();
  };

  const handleRetry = () => {
    setAnswers({});
    setReceipt(null);
    setErrorMsg(null);
    setPhase('quiz');
  };

  return (
    <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
      <div className="w-full max-w-2xl bg-surface-container border border-outline-variant/60 rounded-2xl shadow-2xl overflow-hidden flex flex-col max-h-[92vh]">

        {/* Header */}
        <div className="p-5 bg-surface-container-high border-b border-outline-variant/50 flex items-center justify-between shrink-0">
          <div className="flex items-center gap-2.5">
            <div className="w-9 h-9 rounded-xl bg-tertiary-container/40 text-tertiary flex items-center justify-center border border-tertiary/40">
              <Award className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-base font-bold text-on-surface font-headline-sm">
                Skill Verification Quiz
              </h3>
              <p className="text-xs text-on-surface-variant">
                Score ≥ {threshold}% to verify mastery &amp; unlock downstream skills
              </p>
            </div>
          </div>
          <button
            aria-label="Close verification"
            onClick={onClose}
            className="p-1.5 rounded-lg text-outline hover:text-on-surface hover:bg-surface-container-highest transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Body */}
        <div className="p-6 overflow-y-auto flex flex-col gap-5">

          {/* Skill badge */}
          <div className="p-3.5 rounded-xl bg-surface-container-high border border-outline-variant/40 flex items-center justify-between">
            <div className="flex flex-col gap-0.5">
              <span className="text-[11px] font-bold text-tertiary uppercase tracking-wider">
                Verification Checkpoint
              </span>
              <span className="text-sm font-bold text-on-surface">{skillName}</span>
            </div>
            <div className="flex items-center gap-1 text-[11px] text-outline font-semibold">
              <ShieldCheck className="w-4 h-4 text-secondary" />
              Pass threshold: {threshold}%
            </div>
          </div>

          {/* ── LOADING ── */}
          {phase === 'loading' && (
            <div className="flex flex-col items-center justify-center py-10 gap-3 text-outline">
              <Loader2 className="w-8 h-8 animate-spin text-secondary" />
              <span className="text-sm">Loading verification quiz…</span>
            </div>
          )}

          {/* ── ERROR ── */}
          {phase === 'error' && (
            <div className="p-4 rounded-xl bg-rose-950/40 border border-rose-500/50 flex items-start gap-3">
              <AlertCircle className="w-5 h-5 text-rose-400 mt-0.5 shrink-0" />
              <div className="flex flex-col gap-1">
                <span className="text-sm font-bold text-rose-300">Verification Unavailable</span>
                <span className="text-xs text-rose-400">{errorMsg}</span>
              </div>
            </div>
          )}

          {/* ── QUIZ ── */}
          {phase === 'quiz' && (
            <div className="flex flex-col gap-4">
              <span className="text-xs font-bold text-outline uppercase tracking-wider">
                {questions.length} Questions — Select one answer per question
              </span>

              {questions.map((q, qi) => (
                <div
                  key={q.id}
                  className="p-4 rounded-xl bg-surface-container-lowest border border-outline-variant/40 flex flex-col gap-3"
                >
                  <p className="text-sm font-semibold text-on-surface">
                    <span className="text-secondary font-bold mr-1.5">Q{qi + 1}.</span>
                    {q.question}
                  </p>
                  <div className="grid grid-cols-1 gap-2">
                    {q.options.map((opt, oi) => {
                      const selected = answers[q.id] === oi;
                      return (
                        <button
                          key={oi}
                          onClick={() => setAnswers(prev => ({ ...prev, [q.id]: oi }))}
                          className={`text-left px-3.5 py-2.5 rounded-lg border text-xs font-medium transition-all ${
                            selected
                              ? 'bg-primary-container/60 text-white border-indigo-400 shadow-md shadow-indigo-900/30'
                              : 'bg-surface-container-high text-on-surface-variant border-outline-variant/50 hover:border-primary/40 hover:text-on-surface'
                          }`}
                        >
                          <span className={`font-bold mr-2 ${selected ? 'text-indigo-300' : 'text-outline'}`}>
                            {String.fromCharCode(65 + oi)}.
                          </span>
                          {opt}
                        </button>
                      );
                    })}
                  </div>
                </div>
              ))}

              <button
                onClick={handleSubmit}
                disabled={!allAnswered}
                className={`w-full py-3.5 px-4 rounded-xl font-bold text-sm flex items-center justify-center gap-2 transition-all ${
                  allAnswered
                    ? 'bg-tertiary text-on-tertiary hover:bg-tertiary/90 shadow-lg cursor-pointer'
                    : 'bg-surface-container text-outline border border-outline-variant/40 cursor-not-allowed'
                }`}
              >
                <Sparkles className="w-5 h-5" />
                {allAnswered ? 'Submit & Verify Competency' : `Answer all ${questions.length} questions to submit`}
              </button>
            </div>
          )}

          {/* ── SUBMITTING ── */}
          {phase === 'submitting' && (
            <div className="flex flex-col items-center justify-center py-10 gap-3 text-outline">
              <Cpu className="w-8 h-8 animate-spin text-tertiary" />
              <span className="text-sm">Grading your answers…</span>
            </div>
          )}

          {/* ── RESULT ── */}
          {phase === 'result' && receipt && (
            <div className="flex flex-col gap-5 animate-fadeIn">

              {/* Pass / Fail banner */}
              <div className={`p-4 rounded-xl flex items-center justify-between border ${
                receipt.passed
                  ? 'bg-tertiary-container/30 border-tertiary/40'
                  : 'bg-rose-950/40 border-rose-500/50'
              }`}>
                <div className="flex items-center gap-3">
                  {receipt.passed
                    ? <CheckCircle2 className="w-8 h-8 text-tertiary" />
                    : <XCircle className="w-8 h-8 text-rose-400" />
                  }
                  <div>
                    <h4 className="text-base font-bold text-on-surface">
                      {receipt.passed ? 'Competency Verified!' : 'Not Quite There Yet'}
                    </h4>
                    <p className="text-xs text-on-surface-variant">
                      {receipt.passed
                        ? 'Passed rubric — Verified badge issued.'
                        : `Score ${receipt.score}% — need ${receipt.threshold}% to pass. Try again!`}
                    </p>
                  </div>
                </div>
                <div className={`text-2xl font-bold font-mono ${receipt.passed ? 'text-tertiary' : 'text-rose-400'}`}>
                  {receipt.score}<span className="text-xs text-outline font-normal">/100</span>
                </div>
              </div>

              {/* Newly unlocked */}
              {receipt.passed && receipt.newly_unlocked?.length > 0 && (
                <div className="p-3.5 rounded-xl bg-surface-container-high border border-outline-variant/50 flex flex-col gap-2">
                  <div className="flex items-center gap-1.5 text-xs font-bold text-secondary uppercase tracking-wide">
                    <Unlock className="w-3.5 h-3.5" />
                    Newly Unlocked ({receipt.newly_unlocked.length} skill{receipt.newly_unlocked.length > 1 ? 's' : ''})
                  </div>
                  <div className="flex flex-wrap gap-1.5">
                    {receipt.newly_unlocked.map((sk, i) => (
                      <span
                        key={i}
                        className="text-[11px] flex items-center gap-1 px-2.5 py-1 rounded-lg bg-secondary-container/30 text-secondary border border-secondary/30 font-semibold"
                      >
                        <Unlock className="w-3 h-3" /> {sk.name}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {/* Per-question feedback */}
              <div className="flex flex-col gap-2">
                <span className="text-xs font-bold text-outline uppercase tracking-wider">
                  Answer Feedback:
                </span>
                {receipt.feedback?.map((f, i) => (
                  <div
                    key={i}
                    className={`p-3 rounded-xl border text-xs flex flex-col gap-1 ${
                      f.is_correct
                        ? 'bg-tertiary-container/20 border-tertiary/30'
                        : 'bg-rose-950/30 border-rose-500/30'
                    }`}
                  >
                    <div className="flex items-start justify-between gap-2">
                      <span className="font-semibold text-on-surface">{f.question}</span>
                      {f.is_correct
                        ? <CheckCircle2 className="w-4 h-4 text-tertiary shrink-0" />
                        : <XCircle className="w-4 h-4 text-rose-400 shrink-0" />
                      }
                    </div>
                    {!f.is_correct && f.explanation && (
                      <p className="text-[11px] text-on-surface-variant mt-0.5">
                        <span className="font-bold text-secondary">Why: </span>
                        {f.explanation}
                      </p>
                    )}
                  </div>
                ))}
              </div>

              {/* CTA */}
              {receipt.passed ? (
                <button
                  onClick={handleApply}
                  className="w-full py-3.5 px-4 rounded-xl bg-primary text-on-primary font-bold text-sm flex items-center justify-center gap-2 hover:bg-primary/90 transition-all cursor-pointer shadow-lg shadow-indigo-900/30"
                >
                  <span>View Updated Graph</span>
                  <ChevronRight className="w-5 h-5" />
                </button>
              ) : (
                <button
                  onClick={handleRetry}
                  className="w-full py-3.5 px-4 rounded-xl bg-surface-container-high border border-outline-variant/60 text-on-surface font-bold text-sm flex items-center justify-center gap-2 hover:bg-surface-container-highest transition-all cursor-pointer"
                >
                  <RotateCcw className="w-4 h-4" />
                  <span>Retry Quiz</span>
                </button>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
