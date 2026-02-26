/**
 * API helper – all calls go through Vite's proxy (/api -> Flask :5000).
 */

const BASE = '/api';

async function fetchJSON(path, options = {}) {
  const res = await fetch(`${BASE}${path}`, options);
  const data = await res.json();
  if (!res.ok || data.success === false) {
    throw new Error(data.error || `Request failed (${res.status})`);
  }
  return data;
}

// ─── Violations ──────────────────────────────────────────

export async function getViolationsToday(cameraId) {
  const params = new URLSearchParams();
  if (cameraId) params.set('camera_id', cameraId);
  return fetchJSON(`/violations/today?${params}`);
}

export async function getFilteredViolations({ cameraId, date, severity, limit, offset } = {}) {
  const params = new URLSearchParams();
  if (cameraId) params.set('camera_id', cameraId);
  if (date) params.set('date', date);
  if (severity) params.set('severity', severity);
  if (limit) params.set('limit', limit);
  if (offset) params.set('offset', offset);
  return fetchJSON(`/violations/filter?${params}`);
}

export async function getViolationCount({ startDate, endDate, cameraId } = {}) {
  const params = new URLSearchParams();
  if (startDate) params.set('start_date', startDate);
  if (endDate) params.set('end_date', endDate);
  if (cameraId) params.set('camera_id', cameraId);
  return fetchJSON(`/violations/count?${params}`);
}

export async function getHourlyStats(date) {
  const params = new URLSearchParams();
  if (date) params.set('date', date);
  return fetchJSON(`/violations/hourly?${params}`);
}

export async function getSeverityCounts({ cameraId, date } = {}) {
  const params = new URLSearchParams();
  if (cameraId) params.set('camera_id', cameraId);
  if (date) params.set('date', date);
  return fetchJSON(`/violations/severity-counts?${params}`);
}

export async function getRecentViolations(limit = 10) {
  return fetchJSON(`/violations/recent?limit=${limit}`);
}

export async function getStats() {
  return fetchJSON('/violations/stats');
}

export async function getCameras() {
  return fetchJSON('/violations/cameras');
}

export async function getDates() {
  return fetchJSON('/violations/dates');
}

export function violationImageUrl(imagePath) {
  if (!imagePath) return null;
  // The DB stores paths relative to storage/, e.g. "violations/2026-02-25/file.jpg"
  // Pass as-is to the backend which resolves from <project>/storage/
  return `${BASE}/violations/image/${imagePath}`;
}

export async function exportCSV({ startDate, endDate } = {}) {
  const params = new URLSearchParams();
  if (startDate) params.set('start_date', startDate);
  if (endDate) params.set('end_date', endDate);
  const res = await fetch(`${BASE}/violations/export?${params}`);
  if (!res.ok) throw new Error('Export failed');
  const blob = await res.blob();
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `violations_${new Date().toISOString().slice(0, 10)}.csv`;
  a.click();
  URL.revokeObjectURL(url);
}

// ─── Inference control ───────────────────────────────────

export async function startInference(source, streamId) {
  return fetchJSON('/inference/start', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ source, stream_id: streamId || undefined }),
  });
}

export async function getInferenceStatus() {
  return fetchJSON('/inference/status');
}

export async function stopInference(streamId) {
  return fetchJSON('/inference/stop', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ stream_id: streamId }),
  });
}

export function inferenceStreamUrl(streamId) {
  return `${BASE}/inference/stream/${encodeURIComponent(streamId)}`;
}

// ─── Health ──────────────────────────────────────────────

export async function healthCheck() {
  return fetchJSON('/health');
}
