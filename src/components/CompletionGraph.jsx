import React, { useState, useEffect, useMemo } from 'react';
import { 
  Layers, 
  Lock, 
  CheckCircle2, 
  Zap, 
  Clock, 
  AlertCircle, 
  ShieldCheck, 
  ArrowRight, 
  Info, 
  Award, 
  RotateCcw,
  Check,
  Search,
  Sliders,
  ExternalLink,
  Loader2,
  RefreshCw
} from 'lucide-react';
import { fetchGraph, fetchGoalDiagnosticMastery } from '../services/api';

/**
 * Computes topological depth and SVG canvas coordinates for any DAG.
 */
function computeDynamicNodeCoords(nodes, dependencies) {
  if (!nodes || nodes.length === 0) return {};

  const depsMap = new Map();
  nodes.forEach(n => depsMap.set(n.id, new Set()));

  dependencies.forEach(dep => {
    if (depsMap.has(dep.to)) {
      depsMap.get(dep.to).add(dep.from);
    }
  });

  const depths = new Map();
  function getDepth(id, visited = new Set()) {
    if (depths.has(id)) return depths.get(id);
    if (visited.has(id)) return 0; // Cycle safety guard
    visited.add(id);

    const prereqs = Array.from(depsMap.get(id) || []);
    if (prereqs.length === 0) {
      depths.set(id, 0);
      return 0;
    }

    let maxPrereqDepth = 0;
    for (const p of prereqs) {
      maxPrereqDepth = Math.max(maxPrereqDepth, getDepth(p, new Set(visited)));
    }
    const d = maxPrereqDepth + 1;
    depths.set(id, d);
    return d;
  }

  nodes.forEach(n => getDepth(n.id));

  const levelGroups = new Map();
  nodes.forEach(n => {
    const d = depths.get(n.id) || 0;
    if (!levelGroups.has(d)) levelGroups.set(d, []);
    levelGroups.get(d).push(n.id);
  });

  const maxLevel = Math.max(0, ...Array.from(levelGroups.keys()));

  const coords = {};
  const canvasWidth = 1180;
  const canvasHeight = 360;
  
  const startX = 140;
  const endX = 1040;
  const xStep = maxLevel > 0 ? (endX - startX) / maxLevel : 0;

  levelGroups.forEach((nodeIdsAtLevel, level) => {
    const x = maxLevel === 0 ? canvasWidth / 2 : startX + level * xStep;
    const count = nodeIdsAtLevel.length;

    nodeIdsAtLevel.forEach((id, index) => {
      let y;
      if (count === 1) {
        y = canvasHeight / 2;
      } else {
        const startY = 80;
        const endY = 280;
        y = startY + index * ((endY - startY) / (count - 1));
      }
      coords[id] = { x: Math.round(x), y: Math.round(y) };
    });
  });

  return coords;
}

export default function CompletionGraph({ 
  profile, 
  graphViewMode, 
  setGraphViewMode, 
  onSelectNodeForProof,
  userState,
  goalId,
  refreshKey,
}) {
  const [graphData, setGraphData] = useState(null); // { goal_id, skills, dependencies, masteries, validation }
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedNodeId, setSelectedNodeId] = useState(null);

  const goalTitle = profile?.title || "Frontend Developer Internship";
  const hoursPerWeek = profile?.commitment || 10;
  const durationWeeks = profile?.sprints ? profile.sprints * 4 : 12;

  // Fetch real DAG and persisted diagnostic mastery from backend
  const fetchBackendGraph = async () => {
    setLoading(true);
    setError(null);
    try {
      const dagRes = await fetchGraph(goalId);

      // 3. Fetch persisted diagnostic mastery for page refresh retention
      const masteryRes = await fetchGoalDiagnosticMastery(goalId).catch(() => ({ mastery: [] }));
      
      setGraphData({
        ...dagRes,
        masteries: masteryRes?.mastery || []
      });
      
      if (dagRes?.skills && dagRes.skills.length > 0) {
        setSelectedNodeId(dagRes.skills[0].id);
      }
    } catch (err) {
      console.error('[APOGEE Graph API Error]', err);
      setError(err.message || 'Failed to load backend DAG');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchBackendGraph();
  }, [goalId, refreshKey]);

  // Map backend skills -> graph nodes
  // Map backend dependencies -> graph edges
  const { nodes, dependencies } = useMemo(() => {
    if (!graphData || !graphData.skills) return { nodes: [], dependencies: [] };

    const rawSkills = graphData.skills || [];
    const rawDeps = graphData.dependencies || [];
    const masteriesList = graphData.masteries || [];

    // Map DB skill_id, skill_db_id, or name -> score
    const masteryMap = {};
    masteriesList.forEach(m => {
      if (m.skill_id) masteryMap[m.skill_id] = m.score;
      if (m.skill_db_id) masteryMap[`skill_${m.skill_db_id}`] = m.score;
      if (m.skill_name) masteryMap[m.skill_name.toLowerCase()] = m.score;
    });

    const mappedNodes = rawSkills.map((s) => {
      // Find prerequisite skill IDs (where to == s.id)
      const prereqIds = rawDeps
        .filter((d) => d.to === s.id)
        .map((d) => d.from);

      // Score from diagnostic/masteries
      const score = masteryMap[s.id] ?? masteryMap[`skill_${s.db_id}`] ?? masteryMap[(s.name || '').toLowerCase()] ?? 0;

      // Backend status is source of truth (AVAILABLE, LOCKED, IN_PROGRESS, VERIFIED)
      let rawStatus = (s.status || (prereqIds.length === 0 ? 'AVAILABLE' : 'LOCKED')).toUpperCase();

      // Format for UI helper
      let displayStatus = 'Locked';
      if (rawStatus === 'VERIFIED') displayStatus = 'Verified';
      else if (rawStatus === 'IN_PROGRESS') displayStatus = 'In Progress';
      else if (rawStatus === 'AVAILABLE') displayStatus = 'Available';

      return {
        id: s.id || `skill_${s.db_id || s.name}`,
        db_id: s.db_id,
        label: s.name || s.id || 'Unnamed Skill',
        category: s.target_level || 'Core Skill',
        level: s.target_level || 'Proficient',
        importance: s.importance ?? 1.0,
        mastery: score,
        status: displayStatus,
        deps: prereqIds
      };
    });


    return { nodes: mappedNodes, dependencies: rawDeps };
  }, [graphData]);


  // Compute SVG layout coordinates dynamically
  const nodeCoords = useMemo(() => {
    return computeDynamicNodeCoords(nodes, dependencies);
  }, [nodes, dependencies]);

  // Safely find selected node
  const selectedNode = nodes.find((n) => n.id === selectedNodeId) || nodes[0] || {
    id: 'none',
    label: 'No Skill Selected',
    category: 'N/A',
    level: 'N/A',
    mastery: 0,
    status: 'Locked',
    deps: []
  };

  // Derive node status color helpers
  const getStatusColor = (status) => {
    switch (status) {
      case 'Verified':
        return { bg: 'bg-tertiary-container/30', border: 'border-tertiary', text: 'text-tertiary', stroke: '#4edea3', fill: 'rgba(78, 222, 163, 0.15)' };
      case 'Completed':
        return { bg: 'bg-secondary-container/30', border: 'border-secondary', text: 'text-secondary', stroke: '#4cd7f6', fill: 'rgba(76, 215, 246, 0.15)' };
      case 'In Progress':
        return { bg: 'bg-amber-950/40', border: 'border-amber-400', text: 'text-amber-400', stroke: '#f59e0b', fill: 'rgba(245, 158, 11, 0.15)' };
      case 'Available':
        return { bg: 'bg-surface-container-high', border: 'border-secondary/60', text: 'text-secondary', stroke: '#4cd7f6', fill: 'rgba(38, 42, 53, 0.8)' };
      case 'Needs Review':
        return { bg: 'bg-rose-950/40', border: 'border-rose-400', text: 'text-rose-400', stroke: '#f43f5e', fill: 'rgba(244, 63, 94, 0.15)' };
      case 'Locked':
      default:
        return { bg: 'bg-surface-container-low', border: 'border-outline-variant/40', text: 'text-outline', stroke: '#464555', fill: 'rgba(23, 27, 38, 0.8)' };
    }
  };

  return (
    <div className="w-full max-w-7xl mx-auto px-4 py-6 flex flex-col gap-6">
      {/* Header Controls & Toggle */}
      <div className="w-full rounded-2xl bg-surface-container border border-outline-variant/60 p-5 shadow-xl flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <h2 className="text-xl font-bold text-on-surface font-headline-md">Skill & Capability Graph</h2>
            <span className="text-[10px] font-bold text-tertiary bg-tertiary-container/30 border border-tertiary/40 px-2.5 py-0.5 rounded-full uppercase">
              {graphData?.validation?.acyclic ? 'BACKEND DAG ACYCLIC' : 'BACKEND LIVE DATA'}
            </span>
          </div>
          <p className="text-xs text-on-surface-variant mt-1">
            Saved prerequisite graph for: <strong className="text-primary">{goalTitle}</strong>
          </p>
        </div>

        {/* View Switcher & Refresh Button */}
        <div className="flex items-center gap-2">
          <button
            onClick={fetchBackendGraph}
            disabled={loading}
            className="px-3 py-1.5 rounded-lg text-xs font-semibold bg-surface-container-high hover:bg-surface-container-highest text-on-surface border border-outline-variant/50 flex items-center gap-1.5 transition-colors disabled:opacity-50"
            title="Refresh backend DAG"
          >
            <RefreshCw className={`w-3.5 h-3.5 text-secondary ${loading ? 'animate-spin' : ''}`} />
            <span>Refresh Graph</span>
          </button>

          <div className="flex items-center gap-1 bg-surface-container-lowest p-1 rounded-xl border border-outline-variant/50">
            <button
              onClick={() => setGraphViewMode('skills')}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                graphViewMode === 'skills'
                  ? 'bg-primary text-on-primary font-bold shadow'
                  : 'text-on-surface-variant hover:text-on-surface'
              }`}
            >
              Skills DAG
            </button>
            <button
              onClick={() => setGraphViewMode('courses')}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                graphViewMode === 'courses'
                  ? 'bg-primary text-on-primary font-bold shadow'
                  : 'text-on-surface-variant hover:text-on-surface'
              }`}
            >
              Course Prerequisites
            </button>
          </div>
        </div>
      </div>

      {/* Legend Bar */}
      <div className="flex flex-wrap items-center justify-between gap-3 p-3 rounded-xl bg-surface-container-high border border-outline-variant/40 text-xs">
        <span className="font-bold text-outline uppercase tracking-wider text-[11px]">Node Status Legend:</span>
        <div className="flex flex-wrap items-center gap-3">
          <div className="flex items-center gap-1.5">
            <span className="w-3 h-3 rounded-full bg-tertiary border border-tertiary" />
            <span className="text-on-surface font-medium">Verified (Passed)</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="w-3 h-3 rounded-full bg-secondary border border-secondary" />
            <span className="text-on-surface font-medium">Completed (Self)</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="w-3 h-3 rounded-full bg-amber-400 border border-amber-400" />
            <span className="text-on-surface font-medium">In Progress</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="w-3 h-3 rounded-full bg-surface-container-highest border border-secondary" />
            <span className="text-on-surface font-medium">Available (Root)</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="w-3 h-3 rounded-full bg-surface-container-low border border-outline" />
            <span className="text-on-surface-variant font-medium">Locked (Prereq Required)</span>
          </div>
        </div>
      </div>

      {/* Loading State */}
      {loading && (
        <div className="w-full min-h-[400px] rounded-2xl bg-surface-container-lowest border border-outline-variant/60 flex flex-col items-center justify-center gap-3 shadow-xl">
          <Loader2 className="w-10 h-10 text-primary animate-spin" />
          <p className="text-sm font-bold text-on-surface font-headline-md">Synthesizing Prerequisite DAG from APOGEE Backend...</p>
          <p className="text-xs text-on-surface-variant">Running backend validation and Kahn's algorithm cycle detection</p>
        </div>
      )}

      {/* API Failure State */}
      {!loading && error && (
        <div className="w-full p-8 rounded-2xl bg-rose-950/30 border border-rose-500/50 flex flex-col items-center justify-center text-center gap-3 shadow-xl">
          <AlertCircle className="w-10 h-10 text-rose-400" />
          <h4 className="text-base font-bold text-rose-300">Backend Graph Request Failed</h4>
          <p className="text-xs text-on-surface-variant max-w-md">{error}</p>
          <button
            onClick={fetchBackendGraph}
            className="px-4 py-2 rounded-xl bg-rose-500 hover:bg-rose-600 text-white text-xs font-bold transition-colors shadow"
          >
            Retry Backend Request
          </button>
        </div>
      )}

      {/* Empty Graph State */}
      {!loading && !error && nodes.length === 0 && (
        <div className="w-full min-h-[360px] rounded-2xl bg-surface-container-lowest border border-outline-variant/60 flex flex-col items-center justify-center text-center gap-2 shadow-xl">
          <Layers className="w-10 h-10 text-outline" />
          <h4 className="text-base font-bold text-on-surface">No Skills Found in Graph</h4>
          <p className="text-xs text-on-surface-variant max-w-md">The backend did not return any skill nodes for this goal trajectory.</p>
        </div>
      )}

      {/* Main 2-Pane Desktop Layout */}
      {!loading && !error && nodes.length > 0 && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Left 2-Cols: Interactive SVG DAG Canvas */}
          <div className="lg:col-span-2 rounded-2xl bg-surface-container-lowest border border-outline-variant/60 p-4 shadow-xl overflow-x-auto relative min-h-[480px]">
            <div className="absolute top-3 left-4 text-[11px] text-outline font-mono">
              Live Backend DAG Canvas — Click any node to inspect details
            </div>

            <svg className="w-full min-w-[720px] h-[440px]" viewBox="0 0 1180 360">
              <defs>
                <marker id="arrowhead" markerWidth="8" markerHeight="6" refX="7" refY="3" orient="auto">
                  <polygon points="0 0, 8 3, 0 6" fill="#464555" />
                </marker>
                <marker id="arrowhead-active" markerWidth="8" markerHeight="6" refX="7" refY="3" orient="auto">
                  <polygon points="0 0, 8 3, 0 6" fill="#4cd7f6" />
                </marker>
              </defs>

              {/* Draw Prerequisite Edge Lines */}
              {nodes.map((node) => {
                const targetCoords = nodeCoords[node.id];
                if (!targetCoords) return null;

                return node.deps.map((prereqId) => {
                  const sourceCoords = nodeCoords[prereqId];
                  if (!sourceCoords) return null;

                  const isPrereqVerified = nodes.find(n => n.id === prereqId)?.status === 'Verified';

                  return (
                    <g key={`${prereqId}-${node.id}`}>
                      <line
                        x1={sourceCoords.x + 80}
                        y1={sourceCoords.y}
                        x2={targetCoords.x - 80}
                        y2={targetCoords.y}
                        stroke={isPrereqVerified ? '#4edea3' : '#464555'}
                        strokeWidth={isPrereqVerified ? 2.5 : 1.5}
                        strokeDasharray={isPrereqVerified ? 'none' : '4 4'}
                        markerEnd={isPrereqVerified ? 'url(#arrowhead-active)' : 'url(#arrowhead)'}
                      />
                    </g>
                  );
                });
              })}

              {/* Draw Skill Nodes */}
              {nodes.map((node) => {
                const coords = nodeCoords[node.id];
                if (!coords) return null;

                const style = getStatusColor(node.status);
                const isSelected = selectedNode?.id === node.id;
                const labelText = node.label || node.id || 'Skill';

                return (
                  <g 
                    key={node.id} 
                    transform={`translate(${coords.x}, ${coords.y})`}
                    onClick={() => setSelectedNodeId(node.id)}
                    className="cursor-pointer group"
                  >
                    {/* Selection Ring */}
                    {isSelected && (
                      <rect
                        x="-88"
                        y="-38"
                        width="176"
                        height="76"
                        rx="14"
                        fill="none"
                        stroke="#4f46e5"
                        strokeWidth="3"
                        className="animate-pulse"
                      />
                    )}

                    {/* Node Rect */}
                    <rect
                      x="-82"
                      y="-32"
                      width="164"
                      height="64"
                      rx="12"
                      fill={style.fill}
                      stroke={style.stroke}
                      strokeWidth={isSelected ? "2.5" : "1.5"}
                      className="transition-all group-hover:stroke-primary"
                    />

                    {/* Icon & Label */}
                    <text
                      x="0"
                      y="-8"
                      textAnchor="middle"
                      fill="#dfe2f1"
                      fontSize="11"
                      fontWeight="bold"
                      fontFamily="Inter, sans-serif"
                    >
                      {labelText.length > 20 ? labelText.substring(0, 18) + '...' : labelText}
                    </text>

                    {/* Status pill inside node */}
                    <rect
                      x="-45"
                      y="8"
                      width="90"
                      height="18"
                      rx="9"
                      fill={style.stroke}
                      opacity="0.9"
                    />
                    <text
                      x="0"
                      y="21"
                      textAnchor="middle"
                      fill="#0f131d"
                      fontSize="9"
                      fontWeight="bold"
                      fontFamily="Inter, sans-serif"
                    >
                      {(node.status || 'LOCKED').toUpperCase()}
                    </text>
                  </g>
                );
              })}
            </svg>
          </div>

          {/* Right Col: Interactive Node Inspection Detail Panel */}
          <div className="flex flex-col gap-4">
            <div className="p-5 rounded-2xl bg-surface-container border border-outline-variant/60 shadow-xl flex flex-col gap-4">
              <div className="flex items-center justify-between pb-3 border-b border-outline-variant/40">
                <span className="text-xs font-bold text-outline uppercase tracking-wider">Node Details</span>
                <span className={`text-xs px-2.5 py-0.5 rounded-full font-bold ${getStatusColor(selectedNode.status).bg} ${getStatusColor(selectedNode.status).text} border ${getStatusColor(selectedNode.status).border}`}>
                  {selectedNode.status}
                </span>
              </div>

              <div>
                <h3 className="text-lg font-bold text-on-surface font-headline-md">{selectedNode.label}</h3>
                <div className="flex items-center gap-2 text-xs text-on-surface-variant mt-1">
                  <span>Category: {selectedNode.category}</span>
                  <span>•</span>
                  <span>Target: {selectedNode.level}</span>
                </div>
              </div>

              {/* Current Verified Mastery Gauge */}
              <div className="p-3.5 rounded-xl bg-surface-container-high border border-outline-variant/40 flex flex-col gap-2">
                <div className="flex justify-between text-xs font-semibold">
                  <span className="text-on-surface-variant">Diagnostic score</span>
                  <span className="font-mono text-tertiary font-bold">{selectedNode.mastery}%</span>
                </div>
                <div className="h-2 w-full rounded-full bg-surface-container-lowest overflow-hidden">
                  <div 
                    className="h-full bg-gradient-to-r from-secondary to-tertiary transition-all duration-500 rounded-full"
                    style={{ width: `${selectedNode.mastery}%` }}
                  />
                </div>
              </div>

              {/* Prerequisite Dependencies */}
              <div className="flex flex-col gap-2">
                <span className="text-xs font-bold text-outline uppercase tracking-wider">Prerequisite Requirements:</span>
                {!selectedNode.deps || selectedNode.deps.length === 0 ? (
                  <span className="text-xs text-tertiary font-medium">Zero prerequisites (Root Foundational Skill)</span>
                ) : (
                  <div className="flex flex-col gap-1.5">
                    {selectedNode.deps.map((depId) => {
                      const depNode = nodes.find(n => n.id === depId);
                      const isVerified = depNode?.status === 'Verified';

                      return (
                        <div key={depId} className="p-2.5 rounded-lg bg-surface-container-high border border-outline-variant/40 flex items-center justify-between text-xs">
                          <span className="text-on-surface font-medium">{depNode?.label || depId}</span>
                          {isVerified ? (
                            <span className="text-tertiary font-bold flex items-center gap-1">
                              <Check className="w-3.5 h-3.5" /> Verified
                            </span>
                          ) : (
                            <span className="text-amber-400 font-medium flex items-center gap-1">
                              <Lock className="w-3.5 h-3.5" /> Unverified (Blocks Unlock)
                            </span>
                          )}
                        </div>
                      );
                    })}
                  </div>
                )}
              </div>

              {/* Unlock Rule Warning */}
              <div className="p-3 rounded-xl bg-surface-container-lowest border border-outline-variant/40 text-xs flex flex-col gap-1">
                <div className="flex items-center gap-1.5 font-bold text-secondary">
                  <Info className="w-4 h-4" /> Prerequisite Unlock Rule:
                </div>
                <p className="text-[11px] text-on-surface-variant">
                  Only a <strong>Verified</strong> completion unlocks downstream prerequisite nodes in Apogee.
                </p>
              </div>

              {/* Action CTAs */}
              <div className="flex flex-col gap-2 pt-2">
                <button
                  disabled={selectedNode.status === 'Locked' || selectedNode.status === 'Verified'}
                  onClick={() => onSelectNodeForProof(selectedNode)}
                  className="w-full py-3 px-4 rounded-xl bg-primary-container text-white font-bold text-xs flex items-center justify-center gap-2 shadow hover:bg-indigo-600 transition-colors"
                >
                  <Award className="w-4 h-4" />
                  <span>Verify Mastery via Proof / Quiz</span>
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
