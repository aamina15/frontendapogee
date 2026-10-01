import React, { useState, useEffect } from 'react';
import Header from './components/Header';
import IntakeScreen from './components/IntakeScreen';
import DiagnosticQuizModal from './components/DiagnosticQuizModal';
import RouteScreen from './components/RouteScreen';
import CompletionGraph from './components/CompletionGraph';
import ProofOfSkillModal from './components/ProofOfSkillModal';
import CalendarRePlanModal from './components/CalendarRePlanModal';
import { MISSION_PROFILES, INITIAL_USER_STATE } from './data/mockData';
import { checkBackendHealth, createGoal, getActiveGoal, generateGraphForGoal, fetchGraph, fetchGoalDiagnosticMastery } from './services/api';

export default function App() {
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
  const profile = goal ? { ...preset, title: goal.title, commitment: goal.hours_per_week, duration_weeks: goal.duration_weeks } : preset;

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
      setMastery(mastery.mastery.map(m => m.score));
      setStep(savedGraph ? (mastery.mastery.length ? 3 : 2) : 1);
    } catch (err) {
      if (err.status !== 404) setError(err.message);
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
      setGraph(await generateGraphForGoal(saved.id));
      setApiStatus('online');
      setStep(2);
    } catch (err) {
      setError(err.message);
    } finally { setBusy(false); }
  };

  const navigate = next => {
    setStep(next > 1 && !graph ? 1 : next);
  };
  const refresh = () => setRefreshKey(k => k + 1);
  return (
    <div className="min-h-screen bg-surface font-body-md text-on-surface flex flex-col">
      <Header activeStep={step} setActiveStep={navigate} onOpenCalendarRePlan={() => setReplanOpen(true)} userName={userState.userName} readinessBand={userState.readinessBand} apiStatus={apiStatus} />
      <main className="flex-1 pb-16">
        {restoring ? <p className="p-10 text-center">Loading saved progress…</p> : <>
          {error && step !== 1 && <p role="alert" className="p-4 text-rose-300">{error}</p>}
          {apiStatus === 'offline' && <div role="alert" className="p-4 text-amber-300">Backend unavailable. Your saved progress will load when the connection returns. <button onClick={restore} className="underline">Retry connection</button></div>}
          {step === 1 && <IntakeScreen currentProfile={profile} onSelectProfile={setProfileId} onStartDiagnostic={start} busy={busy} error={error} />}
          {step > 1 && graph?.warning && <p role="status" className="max-w-6xl mx-auto p-4 text-amber-300">{graph.warning}</p>}
          {step > 1 && graph?.validation?.repaired && <p role="status" className="max-w-6xl mx-auto p-4 text-amber-300">A cycle in the generated graph was repaired before saving.</p>}
          {step === 2 && <>
            <CompletionGraph goalId={goal.id} profile={profile} graphViewMode={graphViewMode} setGraphViewMode={setGraphViewMode} onSelectNodeForProof={setProof} userState={userState} refreshKey={refreshKey} />
            <DiagnosticQuizModal goalId={goal.id} profile={profile} onSkipDiagnostic={() => setStep(3)} onCompleteDiagnostic={mastery => { setMastery(Object.values(mastery)); refresh(); setStep(3); }} />
          </>}
          {(step === 3 || step === 4) && <>
            <RouteScreen goalId={goal.id} profile={profile} userState={userState} replanKey={refreshKey} onOpenProofModal={setProof} onSwitchToGraphView={() => document.getElementById('skill-graph')?.scrollIntoView({ behavior: 'smooth' })} />
            <section id="skill-graph"><CompletionGraph goalId={goal.id} profile={profile} graphViewMode={graphViewMode} setGraphViewMode={setGraphViewMode} onSelectNodeForProof={setProof} userState={userState} refreshKey={refreshKey} /></section>
          </>}
        </>}
      </main>
      {proof && <ProofOfSkillModal resourceOrNode={proof} goalId={goal?.id} onClose={() => setProof(null)} onVerifySuccess={refresh} />}
      {replanOpen && <CalendarRePlanModal goalId={goal?.id} currentHoursPerWeek={goal?.hours_per_week || 7} userState={userState} onClose={() => setReplanOpen(false)} onApplyRePlan={receipt => { setGoal(prev => ({ ...prev, hours_per_week: receipt.new_hours_per_week })); refresh(); }} />}
    </div>
  );
}
