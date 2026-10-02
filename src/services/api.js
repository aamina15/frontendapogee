// ORBIT Backend API Client Utility
// All calls go through this module — never put the base URL anywhere else.

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

async function apiFetch(path, options = {}) {
  const url = `${API_BASE_URL}${path}`;
  const defaults = {
    headers: { 'Content-Type': 'application/json' },
  };
  let res;
  try {
    res = await fetch(url, { ...defaults, ...options, signal: AbortSignal.timeout(30000) });
  } catch {
    throw new Error('Cannot reach the backend. Please check the connection and try again.');
  }
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    const message = res.status >= 500
      ? 'We could not complete that request. Please try again.'
      : Array.isArray(body.detail)
        ? body.detail.map(item => `${item.loc?.at(-1) || 'Input'}: ${item.msg}`).join('; ')
        : typeof body.detail === 'string' ? body.detail : 'Request failed. Please try again.';
    const error = new Error(message);
    error.status = res.status;
    throw error;
  }
  return res.json();
}

// ── Health ────────────────────────────────────────────────────────────────────

export async function checkBackendHealth() {
  try {
    const data = await apiFetch('/health');
    return { ok: true, data };
  } catch (error) {
    console.warn('[ORBIT API] Health check failed:', error.message);
    return { ok: false, error: error.message };
  }
}

// ── Goals ─────────────────────────────────────────────────────────────────────

/**
 * Create a new goal.
 * @param {{ title: string, hours_per_week: number, duration_weeks: number, budget?: number }} payload
 */
export function createGoal(payload) {
  return apiFetch('/api/goals', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

export function listGoals() {
  return apiFetch('/api/goals');
}

export function getActiveGoal() {
  return apiFetch('/api/goals/active');
}

export function getGoal(goalId) {
  return apiFetch(`/api/goals/${goalId}`);
}

export function updateGoal(goalId, payload) {
  return apiFetch(`/api/goals/${goalId}`, {
    method: 'PATCH',
    body: JSON.stringify(payload),
  });
}

// ── Skills ────────────────────────────────────────────────────────────────────

export function createSkill(goalId, payload) {
  return apiFetch(`/api/goals/${goalId}/skills`, {
    method: 'POST',
    body: JSON.stringify({ ...payload, goal_id: goalId }),
  });
}

export function listSkills(goalId) {
  return apiFetch(`/api/goals/${goalId}/skills`);
}

export function createSkillDependency(goalId, payload) {
  return apiFetch(`/api/goals/${goalId}/skill-dependencies`, {
    method: 'POST',
    body: JSON.stringify({ ...payload, goal_id: goalId }),
  });
}

export function listSkillDependencies(goalId) {
  return apiFetch(`/api/goals/${goalId}/skill-dependencies`);
}

// ── Mastery ───────────────────────────────────────────────────────────────────

/**
 * Upsert a mastery record (creates or updates diagnostic score).
 * @param {number} goalId
 * @param {{ skill_id: number, diagnostic_score: number }} payload
 */
export function upsertMastery(goalId, payload) {
  return apiFetch(`/api/goals/${goalId}/mastery`, {
    method: 'POST',
    body: JSON.stringify({ ...payload, goal_id: goalId }),
  });
}

export function listMastery(goalId) {
  return apiFetch(`/api/goals/${goalId}/mastery`);
}

/**
 * Update an existing mastery record (e.g., after skill verification).
 * @param {number} goalId
 * @param {number} masteryId
 * @param {{ verification_score?: number, verified?: boolean }} payload
 */
export function updateMastery(goalId, masteryId, payload) {
  return apiFetch(`/api/goals/${goalId}/mastery/${masteryId}`, {
    method: 'PATCH',
    body: JSON.stringify(payload),
  });
}

// ── Resources ─────────────────────────────────────────────────────────────────

export function createResource(skillId, payload) {
  return apiFetch(`/api/skills/${skillId}/resources`, {
    method: 'POST',
    body: JSON.stringify({ ...payload, skill_id: skillId }),
  });
}

export function listResources(skillId) {
  return apiFetch(`/api/skills/${skillId}/resources`);
}

// ── Routes ────────────────────────────────────────────────────────────────────

/**
 * Save a new route version for a goal (increments version automatically if backend handles it).
 * @param {number} goalId
 * @param {{ version: number, total_hours: number, total_weeks: number, route_json: string, change_reason?: string }} payload
 */
export function createRoute(goalId, payload) {
  return apiFetch(`/api/goals/${goalId}/routes`, {
    method: 'POST',
    body: JSON.stringify({ ...payload, goal_id: goalId }),
  });
}

export function fetchGoalRoute(goalId) {
  return apiFetch(`/api/goals/${goalId}/route`);
}

/**
 * Deterministic replan: change hours_per_week and get a new versioned route.
 * @param {number} goalId
 * @param {{ hours_per_week: number }} payload
 * @returns {Promise<ReplanReceipt>}
 */
export function replanGoal(goalId, payload) {
  return apiFetch(`/api/goals/${goalId}/replan`, {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

export function getLatestRoute(goalId) {
  return apiFetch(`/api/goals/${goalId}/routes/latest`);
}


export function listRoutes(goalId) {
  return apiFetch(`/api/goals/${goalId}/routes`);
}

// ── AI Skill Graph Generation ──────────────────────────────────────────────────

/**
 * Generate a structured, validated skill graph DAG for a goal.
 * @param {number} goalId
 */
export function generateGraphForGoal(goalId) {
  return apiFetch(`/api/goals/${goalId}/generate-graph`, {
    method: 'POST',
  });
}

// ── Real Diagnostic API ────────────────────────────────────────────────────────

/**
 * Fetch / generate diagnostic questions for a goal.
 * Server masks correct_index and explanation.
 * @param {number} goalId
 */
export function fetchDiagnostic(goalId) {
  return apiFetch(`/api/goals/${goalId}/diagnostic`, {
    method: 'POST',
  });
}

/**
 * Submit diagnostic answers for grading and mastery persistence.
 * @param {number} goalId
 * @param {Array<{ question_id: number, selected_option: number }>} answers
 */
export function submitDiagnostic(goalId, answers) {
  return apiFetch(`/api/goals/${goalId}/diagnostic/submit`, {
    method: 'POST',
    body: JSON.stringify({ answers }),
  });
}

/**
 * Retrieve saved diagnostic mastery scores for a goal (persistence test).
 * @param {number} goalId
 */
export function fetchGoalDiagnosticMastery(goalId) {
  return apiFetch(`/api/goals/${goalId}/diagnostic/mastery`);
}

/**
 * Fetch ~5 MCQ verification questions for a skill (no correct answers returned).
 * @param {number} goalId
 * @param {number} skillDbId - integer DB id of the skill
 */
export function fetchVerificationQuestions(goalId, skillDbId) {
  return apiFetch(`/api/goals/${goalId}/skills/${skillDbId}/verification`, {
    method: 'POST',
  });
}

/**
 * Submit quiz answers; backend grades and returns a receipt.
 * @param {number} goalId
 * @param {number} skillDbId
 * @param {Array<{ question_id: number, selected_option: number }>} answers
 */
export function submitVerification(goalId, skillDbId, answers) {
  return apiFetch(`/api/goals/${goalId}/skills/${skillDbId}/verify`, {
    method: 'POST',
    body: JSON.stringify({ answers }),
  });
}

export function fetchGraph(goalId) {
  return apiFetch(`/api/goals/${goalId}/graph`);
}
