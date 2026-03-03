/**
 * API helper.
 * - Local dev : Vite proxy rewrites /api → http://localhost:5000
 * - Vercel    : set VITE_API_BASE_URL=https://your-render-url.onrender.com in
 *               Vercel project settings (Environment Variables)
 */

export const BASE = import.meta.env.VITE_API_BASE_URL
  ? import.meta.env.VITE_API_BASE_URL.replace(/\/$/, '')  // strip trailing slash
  : '/api';                              // local dev: Vite proxy

/** True when running on Vercel/production without an API URL configured */
export const API_MISCONFIGURED =
  !import.meta.env.VITE_API_BASE_URL &&
  import.meta.env.PROD;  // import.meta.env.PROD is true after `vite build`

async function fetchJSON(path, options = {}) {
  if (API_MISCONFIGURED) {
    throw new Error(
      'API not configured. Set VITE_API_BASE_URL in Vercel → Project Settings → Environment Variables.'
    );
  }

  let res;
  try {
    res = await fetch(`${BASE}${path}`, options);
  } catch (networkErr) {
    throw new Error(`Network error – is the backend running? (${networkErr.message})`);
  }

  const contentType = res.headers.get('content-type') || '';
  if (!contentType.includes('application/json')) {
    // Got HTML (e.g. Vercel 404 page or nginx error) – surface a clear message
    const text = await res.text();
    throw new Error(
      `Expected JSON but got HTML (${res.status}). ` +
      `Check VITE_API_BASE_URL points to your Render backend.\n\nResponse: ${text.slice(0, 120)}`
    );
  }

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

// ─── Demo videos ─────────────────────────────────────────

export async function getDemoList() {
  return fetchJSON('/demo/list');
}

export async function getDemoOriginals() {
  return fetchJSON('/demo/originals');
}

export function demoVideoUrl(filename) {
  return `${BASE}/demo/video/${encodeURIComponent(filename)}`;
}

export function originalVideoUrl(filename) {
  return `${BASE}/demo/original/${encodeURIComponent(filename)}`;
}

// ─── Health ──────────────────────────────────────────────

export async function healthCheck() {
  return fetchJSON('/health');
}
