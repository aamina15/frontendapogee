import React, { useState, useEffect, useMemo, useRef } from 'react';
import {
  Layers,
  Lock,
  AlertCircle,
  Info,
  Award,
  Check,
  ExternalLink,
  Loader2,
  RefreshCw,
  ChevronRight,
} from 'lucide-react';
import { fetchGraph, fetchGoalDiagnosticMastery, listResources } from '../services/api';

/**
 * Content-aware Capability Map layout.
 *
 * Skills are placed by topological depth into horizontal bands of at most
 * COLS_PER_BAND columns, so small graphs render compact and balanced while
 * deep graphs wrap instead of overlapping. The SVG viewBox is sized from the
 * actual content (columns used x bands), never from a fixed canvas, so there
 * is no oversized empty area — and the map renders ~1:1 for readable labels,
 * scrolling horizontally only when a graph genuinely needs more room.
 */
const NODE_W = 176;
const NODE_H = 64;
const COL_PITCH = 200;      // horizontal distance between level columns
const COLS_PER_BAND = 4;    // levels per horizontal band
const MARGIN_X = 24;
const MARGIN_Y = 30;
const BAND_GAP = 44;        // vertical breathing room between bands
const ROW_H = NODE_H + 14;  // vertical space when several skills share a level

function computeDynamicNodeCoords(nodes, dependencies) {
  if (!nodes || nodes.length === 0) return { coords: {}, width: 640, height: 320 };

  const depsMap = new Map();
  nodes.forEach(n => depsMap.set(n.id, new Set()));
  dependencies.forEach(dep => {
    if (depsMap.has(dep.to)) depsMap.get(dep.to).add(dep.from);
  });

  const depths = new Map();
  function getDepth(id, visited = new Set()) {
    if (depths.has(id)) return depths.get(id);
    if (visited.has(id)) return 0; // cycle safety guard
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
  const levelCount = maxLevel + 1;
  const bands = Math.ceil(levelCount / COLS_PER_BAND);
  const maxStack = Math.max(1, ...Array.from(levelGroups.values()).map(ids => ids.length));
  const bandH = NODE_H + (maxStack - 1) * ROW_H + BAND_GAP;
  const height = MARGIN_Y * 2 + bands * bandH - BAND_GAP;

  const coords = {};
  levelGroups.forEach((ids, level) => {
    const band = Math.floor(level / COLS_PER_BAND);
    const col = level % COLS_PER_BAND;
    const x = MARGIN_X + NODE_W / 2 + col * COL_PITCH;
    const count = ids.length;
    const cy = MARGIN_Y + band * bandH + NODE_H / 2 + ((maxStack - 1) * ROW_H) / 2;
    ids.forEach((id, i) => {
      const y = count === 1 ? cy : cy - ((count - 1) * ROW_H) / 2 + i * ROW_H;
      coords[id] = { x: Math.round(x), y: Math.round(y) };
    });
  });

  // Width follows the widest band actually used (never a fixed canvas).
  const colsUsed = Math.min(levelCount, COLS_PER_BAND);
  const width = MARGIN_X * 2 + NODE_W + (colsUsed - 1) * COL_PITCH;
  return { coords, width, height };
}

// Visual states map 1:1 to the ACTUAL backend states — nothing invented.
function getStatusColor(status) {
  switch (status) {
    case 'Verified':
      return { bg: 'bg-tertiary-container/30', border: 'border-tertiary', text: 'text-tertiary', stroke: '#4edea3', fill: 'rgba(78, 222, 163, 0.14)', pillText: '#003824' };
    case 'In Progress':
      return { bg: 'bg-amber-950/40', border: 'border-amber-400', text: 'text-amber-400', stroke: '#f59e0b', fill: 'rgba(245, 158, 11, 0.13)', pillText: '#3a2a00' };
    case 'Available':
      return { bg: 'bg-secondary-container/20', border: 'border-secondary', text: 'text-secondary', stroke: '#4cd7f6', fill: 'rgba(76, 215, 246, 0.10)', pillText: '#003640' };
    case 'Locked':
    default:
      return { bg: 'bg-surface-container-low', border: 'border-outline-variant', text: 'text-on-surface-variant', stroke: '#5a5f6e', fill: 'rgba(23, 27, 38, 0.85)', pillText: '#c7c4d8' };
  }
}

export default function CompletionGraph({
  profile,
  onSelectNodeForProof,
  onNavigateToRoute,
  userState,
  goalId,
  refreshKey,
}) {
  const [graphData, setGraphData] = useState(null); // { goal_id, skills, dependencies, masteries, validation }
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedNodeId, setSelectedNodeId] = useState(null);
  const detailRef = useRef(null);
  const selectNode = id => {
    setSelectedNodeId(id);
    requestAnimationFrame(() => { detailRef.current?.focus({ preventScroll: true }); detailRef.current?.scrollIntoView({ behavior: 'smooth', block: 'nearest' }); });
  };
  const [routeResources, setRouteResources] = useState({}); // skill_id -> real resource entries

  const goalTitle = profile?.title || "Frontend Developer Internship";

  // Fetch real DAG and persisted diagnostic mastery from backend
  const fetchBackendGraph = async () => {
    setLoading(true);
    setError(null);
    try {
      const dagRes = await fetchGraph(goalId);

      // Fetch persisted diagnostic mastery for page refresh retention
      const masteryRes = await fetchGoalDiagnosticMastery(goalId);

      const resourceRows = await Promise.all(dagRes.skills.map(async skill => [skill.db_id, await listResources(skill.db_id)]));
      setRouteResources(Object.fromEntries(resourceRows));
      setGraphData({
        ...dagRes,
        masteries: masteryRes?.mastery || []
      });

      if (dagRes?.skills && dagRes.skills.length > 0) {
        setSelectedNodeId(current => dagRes.skills.some(s => s.id === current) ? current : dagRes.skills[0].id);
      }
    } catch (err) {
      console.warn('[ORBIT Graph API Error]', err.message);
      setError(err.message || 'Failed to load your skill map');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchBackendGraph();
  }, [goalId, refreshKey]);

  // Map backend skills -> graph nodes
  const { nodes, dependencies } = useMemo(() => {
    if (!graphData || !graphData.skills) return { nodes: [], dependencies: [] };

    const rawSkills = graphData.skills || [];
    const rawDeps = graphData.dependencies || [];
    const masteriesList = graphData.masteries || [];

    // Map DB skill_id, skill_db_id, or name -> { score, assessed }
    const masteryMap = {};
    masteriesList.forEach(m => {
      const entry = { score: m.score, assessed: m.assessed !== false };
      if (m.skill_id) masteryMap[m.skill_id] = entry;
      if (m.skill_db_id) masteryMap[`skill_${m.skill_db_id}`] = entry;
      if (m.skill_name) masteryMap[m.skill_name.toLowerCase()] = entry;
    });

    const mappedNodes = rawSkills.map((s) => {
      const prereqIds = rawDeps
        .filter((d) => d.to === s.id)
        .map((d) => d.from);

      // Diagnostic estimate: only present when the skill was actually assessed
      const m = masteryMap[s.id] ?? masteryMap[`skill_${s.db_id}`] ?? masteryMap[(s.name || '').toLowerCase()];
      const score = m?.assessed ? m.score : null;

      // Backend status is source of truth (AVAILABLE, LOCKED, IN_PROGRESS, VERIFIED)
      let rawStatus = (s.status || (prereqIds.length === 0 ? 'AVAILABLE' : 'LOCKED')).toUpperCase();

      let displayStatus = 'Locked';
      if (rawStatus === 'VERIFIED') displayStatus = 'Verified';
      else if (rawStatus === 'IN_PROGRESS') displayStatus = 'In Progress';
      else if (rawStatus === 'AVAILABLE') displayStatus = 'Available';

      return {
        id: s.id || `skill_${s.db_id || s.name}`,
        db_id: s.db_id,
        label: s.name || s.id || 'Unnamed Skill',
        level: s.target_level || 'Proficient',
        importance: s.importance ?? 1.0,
        mastery: score, // null = not assessed (never fabricate 0%)
        status: displayStatus,
        state: rawStatus,
        deps: prereqIds
      };
    });

    return { nodes: mappedNodes, dependencies: rawDeps };
  }, [graphData]);

  // Content-aware layout coordinates
  const { coords: nodeCoords, width: mapWidth, height: mapHeight } = useMemo(() => {
    return computeDynamicNodeCoords(nodes, dependencies);
  }, [nodes, dependencies]);

  const selectedNode = nodes.find((n) => n.id === selectedNodeId) || nodes[0] || {
    id: 'none',
    label: 'No Skill Selected',
    level: 'N/A',
    mastery: null,
    status: 'Locked',
    state: 'LOCKED',
    deps: []
  };

  const resourcesFor = (node) => routeResources[node?.db_id] || [];

  // Data-driven, honest one-line description (no invented copy)
  const describeSkill = (node) => {
    if (node.state === 'VERIFIED') return 'Mastery demonstrated — counts toward Verified Coverage.';
    if (node.state === 'IN_PROGRESS') return 'Started and in your plan — verify when you are ready.';
    if (node.state === 'AVAILABLE') return 'All prerequisites met — ready to learn and verify.';
    if (node.deps?.length) {
      const blocking = node.deps.filter(depId => nodes.find(n => n.id === depId)?.state !== 'VERIFIED');
      return blocking.length
        ? `Waiting on ${blocking.length} prerequisite${blocking.length > 1 ? 's' : ''} before it can be verified.`
        : 'Prerequisites verified — unlocking.';
    }
    return 'Foundational skill — no prerequisites.';
  };

  return (
    <div className="w-full max-w-7xl mx-auto px-4 py-6 flex flex-col gap-5">
      {/* Header */}
      <div className="w-full rounded-2xl bg-surface-container border border-outline-variant/60 p-5 shadow-xl flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <h2 className="text-xl font-bold text-on-surface font-headline-md">Your Capability Map</h2>
            <span className="text-[10px] font-bold text-tertiary bg-tertiary-container/30 border border-tertiary/40 px-2.5 py-0.5 rounded-full uppercase">
              {graphData?.validation?.acyclic ? 'Prerequisites validated' : 'Prerequisites validated — cycle repaired'}
            </span>
          </div>
          <p className="text-xs text-on-surface-variant mt-1">
            Skill map for: <strong className="text-primary">{goalTitle}</strong>
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={fetchBackendGraph}
            disabled={loading}
            className="px-3 py-1.5 rounded-lg text-xs font-semibold bg-surface-container-high hover:bg-surface-container-highest text-on-surface border border-outline-variant/50 flex items-center gap-1.5 transition-colors disabled:opacity-50"
            title="Reload your saved skill map"
          >
            <RefreshCw className={`w-3.5 h-3.5 text-secondary ${loading ? 'animate-spin' : ''}`} />
            <span>Refresh map</span>
          </button>

        </div>
      </div>

      {/* Status key */}
      <div className="flex flex-wrap items-center justify-between gap-3 p-3 rounded-xl bg-surface-container-high border border-outline-variant/40 text-xs">
        <span className="font-bold text-outline uppercase tracking-wider text-[11px]">Status key</span>
        <div className="flex flex-wrap items-center gap-x-4 gap-y-2">
          <span className="flex items-center gap-1.5">
            <span className="w-3 h-3 rounded-full bg-tertiary border border-tertiary" />
            <span className="text-on-surface font-medium">Verified — passed skill check</span>
          </span>
          <span className="flex items-center gap-1.5">
            <span className="w-3 h-3 rounded-full bg-amber-400 border border-amber-400" />
            <span className="text-on-surface font-medium">In progress</span>
          </span>
          <span className="flex items-center gap-1.5">
            <span className="w-3 h-3 rounded-full bg-secondary border border-secondary" />
            <span className="text-on-surface font-medium">Available — prerequisites met</span>
          </span>
          <span className="flex items-center gap-1.5">
            <span className="w-3 h-3 rounded-full bg-surface-container-highest border border-outline" />
            <span className="text-on-surface-variant font-medium">Locked — prerequisites pending</span>
          </span>
        </div>
      </div>

      {/* Loading State */}
      {loading && (
        <div className="w-full min-h-[320px] rounded-2xl bg-surface-container-lowest border border-outline-variant/60 flex flex-col items-center justify-center gap-3 shadow-xl" aria-busy="true">
          <Loader2 className="w-9 h-9 text-primary animate-spin" />
          <p className="text-sm font-bold text-on-surface font-headline-md">Building your skill map…</p>
          <p className="text-xs text-on-surface-variant">Validating prerequisite order</p>
        </div>
      )}

      {/* Error State */}
      {!loading && error && (
        <div className="w-full p-8 rounded-2xl bg-rose-950/30 border border-rose-500/50 flex flex-col items-center justify-center text-center gap-3 shadow-xl">
          <AlertCircle className="w-10 h-10 text-rose-400" />
          <h4 className="text-base font-bold text-rose-300">Couldn't load your skill map</h4>
          <p className="text-xs text-on-surface-variant max-w-md">{error}</p>
          <button
            onClick={fetchBackendGraph}
            className="px-4 py-2 rounded-xl bg-rose-500 hover:bg-rose-600 text-white text-xs font-bold transition-colors shadow"
          >
            Retry
          </button>
        </div>
      )}

      {/* Empty Graph State */}
      {!loading && !error && nodes.length === 0 && (
        <div className="w-full min-h-[280px] rounded-2xl bg-surface-container-lowest border border-outline-variant/60 flex flex-col items-center justify-center text-center gap-2 shadow-xl">
          <Layers className="w-10 h-10 text-outline" />
          <h4 className="text-base font-bold text-on-surface">Your skill map is empty</h4>
          <p className="text-xs text-on-surface-variant max-w-md">This goal doesn't have any skills in its graph yet.</p>
        </div>
      )}

      {/* Main 2-Pane Layout: map + selected skill panel */}
      {!loading && !error && nodes.length > 0 && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-5 items-start">
          {/* Skill map canvas — content-sized, horizontally scrollable when needed */}
          <div className="lg:col-span-2 rounded-2xl bg-surface-container-lowest border border-outline-variant/60 p-4 shadow-xl">
            <p className="text-[11px] text-outline mb-2 flex items-center gap-1.5">
              <Info className="w-3.5 h-3.5 flex-shrink-0" />
              <span>Your Skill Map — click any skill to inspect details. Prerequisites flow left to right.</span>
            </p>
            <div className="overflow-x-auto rounded-lg">
              <svg
                viewBox={`0 0 ${mapWidth} ${mapHeight}`}
                style={{ width: '100%', minWidth: Math.min(mapWidth, 620), height: 'auto', display: 'block' }}
                role="img"
                aria-label={`Skill map for ${goalTitle}: ${nodes.length} skills. Use the buttons inside the map to inspect each skill.`}
              >
                <defs>
                  <marker id="arrowhead" markerWidth="8" markerHeight="6" refX="7" refY="3" orient="auto">
                    <polygon points="0 0, 8 3, 0 6" fill="#5a5f6e" />
                  </marker>
                  <marker id="arrowhead-active" markerWidth="8" markerHeight="6" refX="7" refY="3" orient="auto">
                    <polygon points="0 0, 8 3, 0 6" fill="#4edea3" />
                  </marker>
                </defs>

                {/* Prerequisite connectors (never interactive) */}
                {nodes.map((node) => {
                  const targetCoords = nodeCoords[node.id];
                  if (!targetCoords) return null;

                  return node.deps.map((prereqId) => {
                    const sourceCoords = nodeCoords[prereqId];
                    if (!sourceCoords) return null;

                    const isPrereqVerified = nodes.find(n => n.id === prereqId)?.state === 'VERIFIED';

                    return (
                      <g key={`${prereqId}-${node.id}`}>
                        <line
                          x1={sourceCoords.x + NODE_W / 2 + 2}
                          y1={sourceCoords.y}
                          x2={targetCoords.x - NODE_W / 2 - 2}
                          y2={targetCoords.y}
                          stroke={isPrereqVerified ? '#4edea3' : '#5a5f6e'}
                          strokeWidth={isPrereqVerified ? 2.5 : 1.5}
                          strokeDasharray={isPrereqVerified ? 'none' : '4 4'}
                          markerEnd={isPrereqVerified ? 'url(#arrowhead-active)' : 'url(#arrowhead)'}
                        />
                      </g>
                    );
                  });
                })}

                {/* Skill nodes — states map 1:1 to backend states */}
                {nodes.map((node) => {
                  const coords = nodeCoords[node.id];
                  if (!coords) return null;

                  const style = getStatusColor(node.status);
                  const isSelected = selectedNode?.id === node.id;
                  const labelText = node.label || node.id || 'Skill';
                  const shortLabel = labelText.length > 19 ? labelText.substring(0, 17) + '…' : labelText;

                  return (
                    <g
                      key={node.id}
                      transform={`translate(${coords.x}, ${coords.y})`}
                      onClick={() => selectNode(node.id)}
                      onKeyDown={(e) => {
                        if (e.key === 'Enter' || e.key === ' ') {
                          e.preventDefault();
                          selectNode(node.id);
                        }
                      }}
                      tabIndex={0}
                      role="button"
                      aria-label={`${node.label} — ${node.status}${node.mastery !== null ? `, diagnostic estimate ${node.mastery}%` : ', not assessed'}. Press Enter to inspect details.`}
                      className="cursor-pointer group focus:outline-none"
                    >
                      <title>{labelText}</title>
                      {/* Selection highlight */}
                      {isSelected && (
                        <rect
                          x="-92"
                          y="-36"
                          width={NODE_W + 16}
                          height={NODE_H + 16}
                          rx="14"
                          fill="none"
                          stroke="#4f46e5"
                          strokeWidth="2.5"
                          className="animate-pulse"
                        />
                      )}
                      {/* Keyboard focus indicator */}
                      <rect
                        x="-92"
                        y="-36"
                        width={NODE_W + 16}
                        height={NODE_H + 16}
                        rx="14"
                        fill="none"
                        stroke="transparent"
                        strokeWidth="2.5"
                        className="group-focus:stroke-secondary"
                      />
                      {/* Node body */}
                      <rect
                        x={-NODE_W / 2}
                        y={-NODE_H / 2}
                        width={NODE_W}
                        height={NODE_H}
                        rx="12"
                        fill={style.fill}
                        stroke={style.stroke}
                        strokeWidth={isSelected ? 2.5 : 1.5}
                        className="transition-all duration-150 group-hover:stroke-secondary"
                      />
                      {/* Label (full name available via tooltip + aria-label) */}
                      <text
                        x="0"
                        y="-8"
                        textAnchor="middle"
                        fill="#dfe2f1"
                        fontSize="12"
                        fontWeight="600"
                        fontFamily="Inter, sans-serif"
                      >
                        {shortLabel}
                      </text>
                      {/* Status pill */}
                      <rect
                        x="-48"
                        y="8"
                        width="96"
                        height="18"
                        rx="9"
                        fill={style.stroke}
                      />
                      <text
                        x="0"
                        y="20.5"
                        textAnchor="middle"
                        fill={style.pillText}
                        fontSize="9.5"
                        fontWeight="700"
                        fontFamily="Inter, sans-serif"
                      >
                        {(node.status || 'LOCKED').toUpperCase()}
                      </text>
                    </g>
                  );
                })}
              </svg>
            </div>
          </div>

          {/* Selected skill panel */}
          <div className="flex flex-col gap-4 min-w-0">
            <div ref={detailRef} tabIndex={-1} role="region" aria-label="Selected skill details" className="p-5 rounded-2xl bg-surface-container border border-outline-variant/60 shadow-xl flex flex-col gap-4">
              <div className="flex items-center justify-between pb-3 border-b border-outline-variant/40">
                <span className="text-xs font-bold text-outline uppercase tracking-wider">Skill details</span>
                <span className={`text-xs px-2.5 py-0.5 rounded-full font-bold ${getStatusColor(selectedNode.status).bg} ${getStatusColor(selectedNode.status).text} border ${getStatusColor(selectedNode.status).border}`}>
                  {selectedNode.status}
                </span>
              </div>

              <div>
                <h3 className="text-lg font-bold text-on-surface font-headline-md">{selectedNode.label}</h3>
                <p className="text-xs text-on-surface-variant mt-1.5 leading-relaxed">{describeSkill(selectedNode)}</p>
                <div className="flex items-center gap-2 text-[11px] text-outline mt-1.5">
                  <span>Target level: {selectedNode.level}</span>
                  <span>•</span>
                  <span>Importance: {selectedNode.importance}</span>
                </div>
              </div>

              {/* Diagnostic estimate — honest about unassessed skills */}
              {selectedNode.mastery !== null ? (
                <div className="p-3.5 rounded-xl bg-surface-container-high border border-outline-variant/40 flex flex-col gap-2">
                  <div className="flex justify-between text-xs font-semibold">
                    <span className="text-on-surface-variant">Diagnostic estimate</span>
                    <span className="font-mono text-tertiary font-bold">{selectedNode.mastery}%</span>
                  </div>
                  <div className="h-2 w-full rounded-full bg-surface-container-lowest overflow-hidden">
                    <div
                      className="h-full bg-gradient-to-r from-secondary to-tertiary transition-all duration-500 rounded-full"
                      style={{ width: `${selectedNode.mastery}%` }}
                    />
                  </div>
                  <span className="text-[10px] text-outline">Placement estimate only — never counts as verification.</span>
                </div>
              ) : (
                <div className="p-3.5 rounded-xl bg-surface-container-high border border-outline-variant/40 flex flex-col gap-1">
                  <div className="flex justify-between text-xs font-semibold">
                    <span className="text-on-surface-variant">Diagnostic estimate</span>
                    <span className="text-[10px] font-bold text-outline tracking-wider border border-outline-variant/40 px-2 py-0.5 rounded">UNASSESSED</span>
                  </div>
                  <span className="text-[10px] text-outline">No diagnostic score for this skill yet — no score is guessed.</span>
                </div>
              )}

              {/* Prerequisites — labels are visibly interactive */}
              <div className="flex flex-col gap-2">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold text-outline uppercase tracking-wider">Prerequisites</span>
                  {selectedNode.deps?.length > 0 && (
                    <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full border ${
                      selectedNode.deps.every(depId => nodes.find(n => n.id === depId)?.state === 'VERIFIED')
                        ? 'text-tertiary border-tertiary/40 bg-tertiary-container/20'
                        : 'text-amber-400 border-amber-500/40 bg-amber-950/30'
                    }`}>
                      {selectedNode.deps.filter(depId => nodes.find(n => n.id === depId)?.state === 'VERIFIED').length} of {selectedNode.deps.length} verified
                    </span>
                  )}
                </div>
                {!selectedNode.deps || selectedNode.deps.length === 0 ? (
                  <span className="text-xs text-tertiary font-medium">No prerequisites — foundational skill.</span>
                ) : (
                  <div className="flex flex-col gap-1.5">
                    {selectedNode.deps.map((depId) => {
                      const depNode = nodes.find(n => n.id === depId);
                      const isVerified = depNode?.state === 'VERIFIED';

                      return (
                        <button
                          type="button"
                          key={depId}
                          onClick={() => selectNode(depId)}
                          aria-label={`Inspect prerequisite ${depNode?.label || depId}`}
                          className="text-left group/prereq hover:border-secondary/60 hover:bg-surface-container-highest p-2.5 rounded-lg bg-surface-container-high border border-outline-variant/40 flex items-center justify-between text-xs transition-colors"
                        >
                          <span className="text-on-surface font-medium flex items-center gap-1.5 min-w-0">
                            {isVerified
                              ? <Check className="w-3.5 h-3.5 text-tertiary flex-shrink-0" />
                              : <Lock className="w-3.5 h-3.5 text-amber-400 flex-shrink-0" />}
                            <span className="truncate">{depNode?.label || depId}</span>
                          </span>
                          {isVerified ? (
                            <span className="text-tertiary font-bold flex items-center gap-1 flex-shrink-0">
                              Verified
                            </span>
                          ) : (
                            <span className="text-amber-400 font-medium flex items-center gap-1 flex-shrink-0">
                              <span className="hidden sm:inline">Blocks unlock</span>
                              <ChevronRight className="w-3.5 h-3.5 opacity-70 group-hover/prereq:translate-x-0.5 transition-transform" />
                            </span>
                          )}
                        </button>
                      );
                    })}
                    <span className="text-[10px] text-outline">Select a prerequisite to inspect it on the map.</span>
                  </div>
                )}
              </div>

              {/* Unlock rule */}
              <div className="p-3 rounded-xl bg-surface-container-lowest border border-outline-variant/40 text-xs flex flex-col gap-1">
                <div className="flex items-center gap-1.5 font-bold text-secondary">
                  <Info className="w-4 h-4" /> How unlocking works
                </div>
                <p className="text-[11px] text-on-surface-variant">
                  Only a <strong>Verified</strong> skill check unlocks downstream skills — estimates never do.
                </p>
              </div>

              {/* Learning resources (real, from the verified catalogue) */}
              <div className="flex flex-col gap-2">
                <span className="text-xs font-bold text-outline uppercase tracking-wider">Learning resources</span>
                {resourcesFor(selectedNode).length > 0 ? (
                  <div className="flex flex-col gap-1.5">
                    {resourcesFor(selectedNode).map((res) => (
                      <div key={`${selectedNode.db_id}-${res.id ?? res.format}`} className="p-2.5 rounded-lg bg-surface-container-high border border-outline-variant/40 flex items-center justify-between gap-2 text-xs">
                        <div className="flex flex-col min-w-0">
                          <span className="text-on-surface font-medium truncate">{res.title}</span>
                          <span className="text-[10px] text-outline">{res.source} · {res.duration_hours} hrs · {res.format}</span>
                        </div>
                        {res.url && (
                          <a
                            href={res.url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="flex items-center gap-1 text-secondary hover:text-on-surface font-semibold flex-shrink-0"
                          >
                            <ExternalLink className="w-3.5 h-3.5" /> Open
                          </a>
                        )}
                      </div>
                    ))}
                  </div>
                ) : (
                  <span className="text-xs text-on-surface-variant">No verified resource catalogued for this skill yet.</span>
                )}
              </div>

              {/* Actions — status-aware; locked skills explain themselves and cannot bypass */}
              <div className="flex flex-col gap-2 pt-1">
                {selectedNode.state === 'LOCKED' && (
                  <p className="text-[11px] text-amber-400 flex items-start gap-1.5">
                    <Lock className="w-3.5 h-3.5 mt-0.5 flex-shrink-0" />
                    <span>
                      This skill cannot be verified yet —{' '}
                      {selectedNode.deps.filter(depId => nodes.find(n => n.id === depId)?.state !== 'VERIFIED').map(depId => nodes.find(n => n.id === depId)?.label || depId).join(', ')}{' '}
                      must be verified first.
                    </span>
                  </p>
                )}
                <button
                  disabled={selectedNode.state === 'LOCKED' || selectedNode.state === 'VERIFIED'}
                  onClick={() => onSelectNodeForProof(selectedNode)}
                  className="w-full py-3 px-4 rounded-xl bg-primary-container text-white font-bold text-xs flex items-center justify-center gap-2 shadow hover:bg-indigo-600 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  <Award className="w-4 h-4" />
                  <span>
                    {selectedNode.state === 'VERIFIED'
                      ? 'Verified — mastery demonstrated'
                      : selectedNode.state === 'LOCKED'
                      ? 'Locked — verify prerequisites first'
                      : 'Verify Mastery via Skill Check'}
                  </span>
                </button>
                {onNavigateToRoute && selectedNode.state !== 'VERIFIED' && (
                  <button
                    onClick={onNavigateToRoute}
                    className="w-full py-2.5 px-4 rounded-xl border border-outline-variant/60 bg-surface-container-high hover:bg-surface-container-highest text-on-surface font-bold text-xs flex items-center justify-center gap-2 transition-colors"
                  >
                    <ExternalLink className="w-4 h-4 text-secondary" />
                    <span>View Learning Resources in Route</span>
                  </button>
                )}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
