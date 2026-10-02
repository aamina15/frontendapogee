import React, { useState, useEffect } from 'react';
import Header from './components/Header';
import IntakeScreen from './components/IntakeScreen';
import DiagnosticQuizModal from './components/DiagnosticQuizModal';
import RouteScreen from './components/RouteScreen';
import CompletionGraph from './components/CompletionGraph';
import ProofOfSkillModal from './components/ProofOfSkillModal';
import CalendarRePlanModal from './components/CalendarRePlanModal';
import LandingPage from './components/LandingPage';
import { MISSION_PROFILES, INITIAL_USER_STATE } from './data/mockData';
import { checkBackendHealth, createGoal, getActiveGoal, generateGraphForGoal, fetchGraph, fetchGoalDiagnosticMastery, listRoutes } from './services/api';

const stagePaths = ['goal', 'diagnose', 'route', 'learn'];
const requestedStage = () => stagePaths.indexOf(window.location.hash.replace('#app/', '')) + 1;

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
  const [graphViewMode, setGraphViewMode] = useState('skills');
  const [proof, setProof] = useState(null);
  const [replanOpen, setReplanOpen] = useState(false);
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
      const savedGraph = await fetchGraph(saved.id).catch(err => {
        if (err.status === 404) return null;
        throw err;
      });
      setGraph(savedGraph);
      const mastery = await fetchGoalDiagnosticMastery(saved.id);
      const routes = await listRoutes(saved.id);
      const canRoute = !!savedGraph && (mastery.mastery.length > 0 || routes.length > 0);
      setRouteReady(canRoute);
      setMastery(mastery.mastery.map(m => m.score));
      const requested = requestedStage();
      const available = requested === 1 || (requested === 2 && savedGraph) || (requested >= 3 && canRoute);
      const restored = available ? requested : savedGraph ? (canRoute ? 3 : 2) : 1;
      setStep(restored);
      if (requested) window.history.replaceState(null, '', `#app/${stagePaths[restored - 1]}`);
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
      const same = goal && goal.title === payload.title && goal.hours_per_week === payload.hours_per_week && goal.duration_weeks === payload.duration_weeks && goal.budget === payload.budget;
      const saved = same ? goal : await createGoal(payload);
      setGoal(saved);
      if (!same) {
        setGraph(null);
        setRouteReady(false);
        setUserState(prev => ({ ...prev, readinessBand: null }));
      }
      setGraph(await generateGraphForGoal(saved.id));
      setApiStatus('online');
      setStep(2);
      setShowLanding(false);
      window.history.pushState(null, '', '#app/diagnose');
      window.scrollTo({ top: 0, behavior: 'instant' });
    } catch (err) {
      setError(err.message);
    } finally { setBusy(false); }
  };

  const navigate = next => {
    if (busy || restoring || (next > 1 && !graph) || (next > 2 && !routeReady)) return;
    setProof(null);
    setReplanOpen(false);
    setShowLanding(false);
    setStep(next);
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

  const handleStartLearning = () => {
    navigate(goal && graph ? (routeReady ? 3 : 2) : 1);
  };
  const finishDiagnostic = mastery => {
    if (mastery) setMastery(Object.values(mastery));
    setRouteReady(true);
    refresh();
    setStep(3);
    window.history.pushState(null, '', '#app/route');
    window.scrollTo({ top: 0, behavior: 'instant' });
  };

  if (showLanding) {
    return (
      <div className="min-h-screen bg-surface font-body-md text-on-surface">
        <LandingPage onStartLearning={handleStartLearning} starting={restoring} />
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
          {step === 1 && <IntakeScreen currentProfile={profile} onSelectProfile={setProfileId} onStartDiagnostic={start} busy={busy} error={error} />}
          {step > 1 && graph?.warning && <p role="status" className="max-w-6xl mx-auto p-4 text-amber-300">{graph.warning}</p>}
          {step > 1 && graph?.validation?.repaired && <p role="status" className="max-w-6xl mx-auto p-4 text-amber-300">A cycle in the generated graph was repaired before saving.</p>}
          {step === 2 && <>
            <DiagnosticQuizModal goalId={goal.id} profile={profile} onSkipDiagnostic={() => finishDiagnostic()} onCompleteDiagnostic={finishDiagnostic} />
            <CompletionGraph goalId={goal.id} profile={profile} graphViewMode={graphViewMode} setGraphViewMode={setGraphViewMode} onSelectNodeForProof={setProof} userState={userState} refreshKey={refreshKey} />
          </>}
          {(step === 3 || step === 4) && <>
            <RouteScreen mode={step === 4 ? 'learn' : 'route'} onStartLearning={() => navigate(4)} goalId={goal.id} profile={profile} userState={userState} replanKey={refreshKey} onOpenProofModal={setProof} onSwitchToGraphView={() => document.getElementById('skill-graph')?.scrollIntoView({ behavior: 'smooth' })} />
            <section id="skill-graph"><CompletionGraph goalId={goal.id} profile={profile} graphViewMode={graphViewMode} setGraphViewMode={setGraphViewMode} onSelectNodeForProof={setProof} userState={userState} refreshKey={refreshKey} /></section>
          </>}
        </>}
      </main>
      {proof && <ProofOfSkillModal resourceOrNode={proof} goalId={goal?.id} onClose={() => setProof(null)} onVerifySuccess={refresh} />}
      {replanOpen && <CalendarRePlanModal goalId={goal?.id} currentHoursPerWeek={goal?.hours_per_week || 7} userState={userState} onClose={() => setReplanOpen(false)} onApplyRePlan={receipt => { setGoal(prev => ({ ...prev, hours_per_week: receipt.new_hours_per_week })); refresh(); }} />}
    </div>
  );
}
