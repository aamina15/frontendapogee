import React, { useState, useEffect } from 'react';
import { 
  Zap, 
  HelpCircle, 
  CheckCircle2, 
  ArrowRight, 
  Sparkles, 
  BarChart2, 
  ShieldAlert,
  ChevronRight,
  TrendingUp,
  Loader2,
  AlertCircle
} from 'lucide-react';
import { fetchDiagnostic, submitDiagnostic } from '../services/api';

export default function DiagnosticQuizModal({
  profile,
  goalId,
  depth = 'quick',
  onCompleteDiagnostic,
  onSkipDiagnostic
}) {
  const [uncovered, setUncovered] = useState([]);
  const [questions, setQuestions] = useState([]);
  const [currentIdx, setCurrentIdx] = useState(0);
  const [selectedOption, setSelectedOption] = useState(null);
  const [userAnswers, setUserAnswers] = useState({}); // q_id -> selected_option
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState(null);
  const [masteryVector, setMasteryVector] = useState({});

  const goalTitle = profile?.title || "Frontend Developer Internship";
  const hoursPerWeek = profile?.commitment || 10;
  const durationWeeks = profile?.sprints ? profile.sprints * 4 : 12;

  // Fetch real diagnostic questions from backend (goal-aware distribution)
  const loadDiagnostic = async () => {
    setLoading(true);
    setError(null);
    try {
      const diagRes = await fetchDiagnostic(goalId, depth);
      const fetchedQuestions = diagRes?.questions || [];
      setQuestions(fetchedQuestions);
      setUncovered(diagRes.unassessed_skills || []);

      // Initialize mastery vector preview
      const initialVector = {};
      fetchedQuestions.forEach(q => {
        if (q.skill_name) initialVector[q.skill_name] = 0;
      });
      setMasteryVector(initialVector);

    } catch (err) {
      console.warn('[ORBIT Diagnostic Fetch Error]', err.message);
      setError(err.message || 'Failed to load backend diagnostic questions');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadDiagnostic();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [goalId, depth]);

  const currentQ = questions[currentIdx];

  const handleOptionSelect = (optionIdx) => {
    if (!currentQ) return;
    setSelectedOption(optionIdx);

    setUserAnswers((prev) => ({
      ...prev,
      [currentQ.id]: optionIdx
    }));

  };

  const handleNext = async () => {
    if (currentIdx < questions.length - 1) {
      setCurrentIdx(currentIdx + 1);
      setSelectedOption(userAnswers[questions[currentIdx + 1]?.id] ?? null);
    } else {
      // Submit all answers to backend for grading & mastery persistence
      setSubmitting(true);
      setError(null);
      try {
        const formattedAnswers = Object.entries(userAnswers).map(([qid, opt]) => ({
          question_id: Number(qid),
          selected_option: Number(opt)
        }));

        const submitRes = await submitDiagnostic(goalId, formattedAnswers);
        
        // Convert array response to mastery object map for parent state
        const finalMasteryMap = {};
        if (submitRes?.mastery) {
          submitRes.mastery.forEach(m => {
            finalMasteryMap[m.skill_name || m.skill_id] = m.score;
          });
        }

        onCompleteDiagnostic(finalMasteryMap);
      } catch (err) {
        console.warn('[ORBIT Diagnostic Submit Error]', err.message);
        setError(err.message || 'Failed to submit diagnostic answers');
      } finally {
        setSubmitting(false);
      }
    }
  };

  // Loading State
  if (loading) {
    return (
      <div className="w-full max-w-3xl mx-auto px-4 py-16 flex flex-col items-center justify-center text-center gap-4">
        <Loader2 className="w-10 h-10 text-secondary animate-spin" />
        <h2 className="text-xl font-bold text-on-surface font-headline-md">Generating ORBIT Diagnostic Assessment...</h2>
        <p className="text-xs text-on-surface-variant">Generating targeted questions for {goalTitle} on backend</p>
      </div>
    );
  }

  // Error State
  if (error && questions.length === 0) {
    return (
      <div className="w-full max-w-3xl mx-auto px-4 py-12 flex flex-col items-center justify-center text-center gap-4">
        <AlertCircle className="w-10 h-10 text-rose-400" />
        <h2 className="text-lg font-bold text-rose-300">Backend Diagnostic Request Failed</h2>
        <p className="text-xs text-on-surface-variant max-w-md">{error}</p>
        <button
          onClick={loadDiagnostic}
          className="px-4 py-2 rounded-xl bg-secondary text-on-secondary text-xs font-bold shadow"
        >
          Retry Backend Diagnostic
        </button>
      </div>
    );
  }

  // Empty state fallback
  if (!currentQ) {
    return (
      <div className="w-full max-w-3xl mx-auto px-4 py-8 flex flex-col items-center justify-center text-center">
        <Sparkles className="w-12 h-12 text-tertiary mb-3" />
        <h2 className="text-2xl font-bold text-on-surface">No Diagnostic Questions for This Goal</h2>
        <p className="text-sm text-on-surface-variant mt-2 max-w-md">
          No assessment questions are available for this goal's skill graph yet. You can continue
          now — skill checks (≥70%) remain the only way to verify skills and unlock prerequisites.
        </p>
        <button
          onClick={onSkipDiagnostic}
          className="mt-6 px-6 py-3 rounded-xl bg-primary text-on-primary font-bold shadow"
        >
          See My Skill Gap Analysis
        </button>
      </div>
    );
  }

  const isLast = currentIdx === questions.length - 1;

  return (
    <div className="w-full max-w-4xl mx-auto px-4 py-6 flex flex-col gap-6">
      <p role="status" className="text-sm text-on-surface-variant">{questions.some(q => q.source === 'openai' || q.source === 'gemini') ? `Includes validated AI question proposals from ${questions.some(q => q.source === 'openai') ? 'OpenAI' : 'Gemini'}.` : questions.some(q => q.source === 'legacy_bank') ? 'Previously saved assessment; question relevance has not been revalidated.' : 'Saved skill-specific question bank; no live AI generation is claimed.'} Questions are graded on the server. {uncovered.length > 0 && `No reliable questions available for: ${uncovered.join(', ')}. These skills remain UNASSESSED.`}</p>
      {/* Step 2 Progress Header */}
      <section className="w-full">
        <div className="grid grid-cols-4 gap-3">
          <div className="flex flex-col gap-1.5 opacity-60">
            <div className="h-2 w-full rounded-full bg-primary" />
            <span className="text-xs text-on-surface-variant font-medium">1. Goal</span>
          </div>
          <div className="flex flex-col gap-1.5">
            <div className="h-2 w-full rounded-full bg-secondary shadow-[0_0_12px_rgba(76,215,246,0.7)]" />
            <div className="flex items-center gap-1.5">
              <span className="w-4 h-4 rounded-full bg-secondary text-on-secondary font-mono text-[10px] flex items-center justify-center font-bold">2</span>
              <span className="text-xs text-on-surface font-bold">Diagnose</span>
            </div>
          </div>
          <div className="flex flex-col gap-1.5 opacity-60">
            <div className="h-2 w-full rounded-full bg-surface-container-highest" />
            <span className="text-xs text-on-surface-variant font-medium">3. Build Route</span>
          </div>
          <div className="flex flex-col gap-1.5 opacity-60">
            <div className="h-2 w-full rounded-full bg-surface-container-highest" />
            <span className="text-xs text-on-surface-variant font-medium">4. Learn & Verify</span>
          </div>
        </div>
      </section>

      {error && <p role="alert" className="text-rose-300">{error} Your answers are still here; submit again to retry.</p>}
      {/* Main Diagnostic Container */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left 2 Cols: Question Card */}
        <div className="lg:col-span-2 flex flex-col gap-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className="text-xs font-bold text-secondary bg-secondary-container/30 border border-secondary/40 px-2.5 py-1 rounded-lg flex items-center gap-1">
                <Zap className="w-3.5 h-3.5 text-secondary" />
                Question {currentIdx + 1} of {questions.length}
              </span>
              <span className="text-xs text-on-surface-variant font-medium">
                Goal: <strong className="text-primary">{goalTitle}</strong>
              </span>
            </div>

            <button
              onClick={onSkipDiagnostic}
              className="text-xs text-outline hover:text-on-surface underline transition-colors"
              type="button"
            >
              Skip diagnostic — nothing is verified or unlocked
            </button>
          </div>

          <div className="p-6 rounded-2xl bg-surface-container border border-outline-variant/60 shadow-xl flex flex-col gap-5">
            <div className="flex flex-col gap-1">
              <span className="text-[11px] font-bold text-tertiary uppercase tracking-wider">
                Testing Skill: {currentQ.skill_name}
              </span>
              <h3 className="text-lg font-bold text-on-surface font-headline-sm leading-snug">
                {currentQ.question}
              </h3>
            </div>

            {/* Answer Options */}
            <div className="flex flex-col gap-2.5">
              {currentQ.options.map((optionText, optIdx) => {
                const isSelected = selectedOption === optIdx;
                let btnStyle = isSelected
                  ? "bg-primary-container text-white border-indigo-400 font-semibold"
                  : "bg-surface-container-high hover:bg-surface-container-highest text-on-surface border-outline-variant/60";

                return (
                  <button
                    key={optIdx}
                    onClick={() => handleOptionSelect(optIdx)}
                    disabled={submitting}
                    className={`w-full p-4 rounded-xl text-xs md:text-sm text-left transition-all border flex items-center justify-between gap-3 ${btnStyle}`}
                  >
                    <div className="flex items-center gap-3">
                      <span className="w-6 h-6 rounded-full bg-surface-container-lowest text-on-surface-variant text-xs font-mono font-bold flex items-center justify-center border border-outline-variant/40 shrink-0">
                        {String.fromCharCode(65 + optIdx)}
                      </span>
                      <span>{optionText}</span>
                    </div>
                  </button>
                );
              })}
            </div>

            {/* Bottom action button */}
            <div className="flex justify-end pt-2">
              <button
                onClick={handleNext}
                disabled={selectedOption === null || submitting}
                className={`px-6 py-3 rounded-xl font-bold text-xs md:text-sm flex items-center gap-2 transition-all ${
                  selectedOption !== null && !submitting
                    ? 'bg-primary text-on-primary hover:bg-primary/90 cursor-pointer shadow-lg shadow-indigo-900/30'
                    : 'bg-surface-container-highest text-outline cursor-not-allowed'
                }`}
              >
                {submitting ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" />
                    <span>Grading on the server…</span>
                  </>
                ) : (
                  <>
                    <span>{isLast ? "Submit Diagnostic & See My Skill Gaps" : "Next Question"}</span>
                    <ChevronRight className="w-4 h-4" />
                  </>
                )}
              </button>
            </div>
          </div>
        </div>

        <aside className="p-5 rounded-2xl bg-surface-container border border-outline-variant/60">
          <h3 className="font-bold">Diagnostic progress</h3>
          <p className="text-sm mt-3">{Object.keys(userAnswers).length} of {questions.length} answered.</p>
          <p className="text-xs mt-3 text-on-surface-variant">Your answers are graded and saved when you submit. Diagnostic results guide your starting state; verification unlocks prerequisite skills.</p>
        </aside>
      </div>
    </div>
  );
}
