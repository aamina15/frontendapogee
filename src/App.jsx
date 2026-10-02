import React, { useState, useEffect, useRef } from 'react';
import { Layers } from 'lucide-react';
import Header from './components/Header';
import IntakeScreen from './components/IntakeScreen';
import DiagnosticQuizModal from './components/DiagnosticQuizModal';
import SkillGapAnalysis from './components/SkillGapAnalysis';
import RouteScreen from './components/RouteScreen';
import CompletionGraph from './components/CompletionGraph';
import ProofOfSkillModal from './components/ProofOfSkillModal';
import CalendarRePlanModal from './components/CalendarRePlanModal';
import LandingPage from './components/LandingPage';
import { MISSION_PROFILES, INITIAL_USER_STATE } from './data/mockData';
import { checkBackendHealth, createGoal, getActiveGoal, generateGraphForGoal, fetchGraph, fetchGoalDiagnosticMastery, listRoutes } from './services/api';

const stagePaths = ['goal', 'diagnose', 'route', 'learn'];
const requestedStage = () => ['#app/map', '#app/results'].includes(window.location.hash) ? 2 : stagePaths.indexOf(window.location.hash.replace('#app/', '')) + 1;

export default function App() {
  const [showLanding, setShowLanding] = useState(() => !requestedStage());
  const [routeReady, setRouteReady] = useState(false);
  const [profileId, setProfileId] = useState(MISSION_PROFILES.find(p => p.title.includes('Frontend'))?.id || MISSION_PROFILES[0].id);
  const [goal, setGoal] = useState(null);
  const [graph, setGraph] = useState(null);
  const [step, setStep] = useState(1);
  const [restoring, setRestoring] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(null);
  const [apiStatus, setApiStatus] = useState('checking');
  const [refreshKey, setRefreshKey] = useState(0);
  const [proof, setProof] = useState(null);
  const [replanOpen, setReplanOpen] = useState(false);
  const [hasSavedProgress, setHasSavedProgress] = useState(false);
  const [mapOpen, setMapOpen] = useState(window.location.hash === '#app/map');
  const [intakeKey, setIntakeKey] = useState(0);
  const [newGoalIntent, setNewGoalIntent] = useState(false);
  const [diagnosticDone, setDiagnosticDone] = useState(false);
  const [diagDepth, setDiagDepth] = useState('quick');
  const [info, setInfo] = useState(null);
  const [userState, setUserState] = useState({ ...INITIAL_USER_STATE, readinessBand: null });
  const preset = MISSION_PROFILES.find(p => p.id === profileId) || MISSION_PROFILES[0];
  const profile = goal ? { ...preset, title: goal.title, commitment: goal.hours_per_week, duration_weeks: goal.duration_weeks, budget: goal.budget } : preset;

  const setMastery = (scores) => {
    if (!scores.length) return;
    const average = Math.round(scores.reduce((a, b) => a + b, 0) / scores.length);
    setUserState(prev => ({ ...prev, readinessBand: { min: average, max: average } }));
  };

  const restore = async () => {
    setRestoring(true);
    setError(null);
    const health = await checkBackendHealth();
    setApiStatus(health.ok ? 'online' : 'offline');
    try {
      const saved = await getActiveGoal();
      setGoal(saved);
      setHasSavedProgress(true);
      const savedGraph = await fetchGraph(saved.id).catch(err => {
        if (err.status === 404) return null;
        throw err;
      });
      setGraph(savedGraph);
      const mastery = await fetchGoalDiagnosticMastery(saved.id);
      const routes = await listRoutes(saved.id);
      const canRoute = !!savedGraph && (mastery.mastery.some(m => m.assessed) || routes.length > 0 || localStorage.getItem(`orbit_diagnostic_decision_${saved.id}`) === 'skipped');
      setRouteReady(canRoute);
      // A previously assessed goal reopens at its gap analysis, not the quiz.
      setDiagnosticDone(canRoute);
      setMastery(mastery.mastery.filter(m => m.assessed).map(m => m.score));
      const requested = requestedStage();
      const available = requested === 1 || (requested === 2 && savedGraph) || (requested >= 3 && canRoute);
      const restored = available ? requested : savedGraph ? (canRoute ? 3 : 2) : 1;
      setStep(restored);
      if (requested && !['#app/map', '#app/results'].includes(window.location.hash)) window.history.replaceState(null, '', `#app/${stagePaths[restored - 1]}`);
    } catch (err) {
      if (err.status !== 404) setError(err.message);
      if (requestedStage()) window.history.replaceState(null, '', '#app/goal');
    } finally {
      setRestoring(false);
    }
  };
  useEffect(() => { restore(); }, []);

  const start = async payload => {
    setBusy(true);
    setError(null);
    try {
      const same = !newGoalIntent && goal && goal.title === payload.title && goal.hours_per_week === payload.hours_per_week && goal.duration_weeks === payload.duration_weeks && goal.budget === payload.budget;
      const saved = same ? goal : await createGoal(payload);
      setGoal(saved);
      setHasSavedProgress(true);
      setNewGoalIntent(false);
      setMapOpen(true);
      // Visible outcome: reusing an identical goal restores it instead of silently duplicating.
      setInfo(same ? 'Continuing with your saved goal — its skill map and progress were restored.' : null);
      if (!same) {
        setGraph(null);
        setRouteReady(false);
        setDiagnosticDone(false);
        setDiagDepth('quick');
        setUserState(prev => ({ ...prev, readinessBand: null }));
      }
      setGraph(await generateGraphForGoal(saved.id));
      setApiStatus('online');
      setStep(2);
      setShowLanding(false);
      window.history.pushState(null, '', '#app/map');
      window.scrollTo({ top: 0, behavior: 'instant' });
    } catch (err) {
      setError(err.message);
    } finally { setBusy(false); }
  };

  // Resume returns the learner to the furthest stage their saved progress allows.
  const handleStartLearning = () => {
    setNewGoalIntent(false);
    navigate(goal && graph ? (routeReady ? 3 : 2) : 1);
    setMapOpen(!!graph && !routeReady);
    if (graph && !routeReady) window.history.replaceState(null, '', '#app/map');
  };
  // Start New Goal always opens the intake form; nothing is deleted.
  const handleStartNewGoal = () => {
    setNewGoalIntent(true);
    setIntakeKey(k => k + 1);
    navigate(1);
  };
  const finishDiagnostic = mastery => {
    if (mastery) setMastery(Object.values(mastery));
    localStorage.setItem(`orbit_diagnostic_decision_${goal.id}`, mastery ? 'assessed' : 'skipped');
    setMapOpen(false);
    setRouteReady(true);
    setDiagnosticDone(true);
    refresh();
    setStep(2);
    window.history.replaceState(null, '', '#app/results');
    window.scrollTo({ top: 0, behavior: 'instant' });
  };
  const reopenDiagnostic = (depth) => {
    setMapOpen(false);
    window.history.replaceState(null, '', '#app/diagnose');
    setDiagDepth(depth || 'quick');
    setDiagnosticDone(false);
    window.scrollTo({ top: 0, behavior: 'instant' });
  };

  const navigate = next => {
    if (busy || restoring || (next > 1 && !graph) || (next > 2 && !routeReady)) return;
    setProof(null);
    setReplanOpen(false);
    setShowLanding(false);
    setStep(next);
    if (next === 2) setMapOpen(false);
    window.history.pushState(null, '', `#app/${stagePaths[next - 1]}`);
    window.scrollTo({ top: 0, behavior: 'instant' });
  };
  useEffect(() => {
    const onHashChange = () => {
      const next = requestedStage();
      if (!next) {
        setShowLanding(true);
        window.scrollTo({ top: 0, behavior: 'instant' });
        return;
      }
      if (restoring) return;
      const allowed = next === 1 || (next === 2 && graph) || (next >= 3 && routeReady);
      setShowLanding(false);
      setStep(allowed ? next : 1);
      setMapOpen(window.location.hash === '#app/map');
      setProof(null);
      setReplanOpen(false);
      if (!allowed) window.history.replaceState(null, '', '#app/goal');
      window.scrollTo({ top: 0, behavior: 'instant' });
    };
    window.addEventListener('hashchange', onHashChange);
    window.addEventListener('popstate', onHashChange);
    return () => {
      window.removeEventListener('hashchange', onHashChange);
      window.removeEventListener('popstate', onHashChange);
    };
  }, [graph, routeReady, restoring]);
  const refresh = () => setRefreshKey(k => k + 1);
  const graphDetailsRef = useRef(null);
  const openGraphDetails = () => {
    if (graphDetailsRef.current) graphDetailsRef.current.open = true;
    requestAnimationFrame(() => document.getElementById('skill-graph')?.scrollIntoView({ behavior: 'smooth' }));
  };

  if (showLanding) {
    return (
      <div className="min-h-screen bg-surface font-body-md text-on-surface">
        <LandingPage
          onStartLearning={handleStartLearning}
          onStartNew={handleStartNewGoal}
          canResume={hasSavedProgress && !!goal}
          starting={restoring}
        />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-surface font-body-md text-on-surface flex flex-col">
      <Header activeStep={step} setActiveStep={navigate} hasGraph={!!graph} routeReady={routeReady} busy={busy || restoring} onOpenHome={() => { window.location.hash = ''; setShowLanding(true); }} onOpenCalendarRePlan={() => setReplanOpen(true)} userName={userState.userName} readinessBand={userState.readinessBand} apiStatus={apiStatus} />
      <main className="flex-1 pb-16">
        {restoring ? <p className="p-10 text-center">Loading saved progress…</p> : <>
          {error && step !== 1 && <p role="alert" className="p-4 text-rose-300">{error}</p>}
          {apiStatus === 'offline' && <div role="alert" className="p-4 text-amber-300">Backend unavailable. Your saved progress will load when the connection returns. <button onClick={restore} className="underline">Retry connection</button></div>}
          {step === 1 && <IntakeScreen key={intakeKey} currentProfile={newGoalIntent ? null : profile} onSelectProfile={setProfileId} onStartDiagnostic={start} busy={busy} error={error} savedGoal={hasSavedProgress ? goal : null} onResume={handleStartLearning} restoring={restoring} />}
          {step > 1 && info && <p role="status" className="max-w-6xl mx-auto px-4 pt-4 text-sm text-secondary">{info}</p>}
          {step > 1 && graph?.warning && <p role="status" className="max-w-6xl mx-auto p-4 text-amber-300">{graph.warning}</p>}
          {step > 1 && graph?.validation?.repaired && <p role="status" className="max-w-6xl mx-auto p-4 text-amber-300">A cycle in the generated graph was repaired before saving.</p>}
          {step === 2 && <>
            {mapOpen ? <section className="max-w-6xl mx-auto px-4 py-8"><h1 className="text-3xl font-bold mb-3">Your capability map</h1><p className="text-on-surface-variant mb-5">Inspect a skill and its prerequisites. Next, assess what you already know.</p><button className="btn-primary" onClick={() => { setMapOpen(false); reopenDiagnostic('quick'); }}>Start Diagnostic</button></section> : diagnosticDone ? (
              <SkillGapAnalysis
                goalId={goal.id}
                profile={profile}
                skipped={userState.readinessBand === null}
                onContinue={() => navigate(3)}
                onDeepenAssessment={() => reopenDiagnostic('deep')}
                onTakeDiagnostic={() => reopenDiagnostic('quick')}
              />
            ) : (
              <DiagnosticQuizModal goalId={goal.id} profile={profile} depth={diagDepth} onSkipDiagnostic={() => finishDiagnostic()} onCompleteDiagnostic={finishDiagnostic} />
            )}
            {mapOpen && <CompletionGraph goalId={goal.id} profile={profile} onSelectNodeForProof={setProof} userState={userState} refreshKey={refreshKey} onNavigateToRoute={routeReady ? () => navigate(3) : null} />}
          </>}
          {(step === 3 || step === 4) && <>
            <RouteScreen mode={step === 4 ? 'learn' : 'route'} graphData={graph} onStartLearning={() => navigate(4)} goalId={goal.id} profile={profile} userState={userState} replanKey={refreshKey} onOpenProofModal={setProof} onSwitchToGraphView={step === 3 ? openGraphDetails : () => document.getElementById('skill-graph')?.scrollIntoView({ behavior: 'smooth' })} />
            {step === 3 ? (
              <details ref={graphDetailsRef} className="max-w-7xl mx-auto px-4 w-full group">
                <summary className="cursor-pointer select-none list-none flex items-center justify-between rounded-2xl bg-surface-container border border-outline-variant/60 p-4 text-sm font-semibold text-on-surface hover:border-primary/40 transition-colors">
                  <span className="flex items-center gap-2">
                    <Layers className="w-4 h-4 text-secondary" />
                    <span>Skill map (optional) — inspect prerequisites and skill details</span>
                  </span>
                  <span className="text-xs text-outline group-open:hidden">Show</span>
                  <span className="text-xs text-outline hidden group-open:inline">Hide</span>
                </summary>
                <section id="skill-graph" className="mt-4"><CompletionGraph goalId={goal.id} profile={profile} onSelectNodeForProof={setProof} userState={userState} refreshKey={refreshKey} onNavigateToRoute={() => navigate(3)} /></section>
              </details>
            ) : (
              <section id="skill-graph"><CompletionGraph goalId={goal.id} profile={profile} onSelectNodeForProof={setProof} userState={userState} refreshKey={refreshKey} onNavigateToRoute={() => navigate(3)} /></section>
            )}
          </>}
        </>}
      </main>
      {proof && <ProofOfSkillModal resourceOrNode={proof} goalId={goal?.id} onClose={() => setProof(null)} onVerifySuccess={refresh} />}
      {replanOpen && <CalendarRePlanModal goalId={goal?.id} currentHoursPerWeek={goal?.hours_per_week || 7} userState={userState} onClose={() => setReplanOpen(false)} onApplyRePlan={receipt => { setGoal(prev => ({ ...prev, hours_per_week: receipt.new_hours_per_week })); refresh(); }} />}
    </div>
  );
}
