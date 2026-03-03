import { useEffect, useRef, useState } from 'react';
import { Film, Cpu, Play, Pause, RotateCcw } from 'lucide-react';
import { getDemoList, getDemoOriginals, demoVideoUrl, originalVideoUrl } from '../api';

/* ─── human-readable title from demo filename ─────────────────────────────── */
function makeTitle(stem) {
  // stem looks like  "demo_1_a-team-bw"  or  "demo_3_energetic-construction-..."
  const withoutPrefix = stem.replace(/^demo_\d+_/, '');
  const words = withoutPrefix.replace(/[-_]/g, ' ').replace(/\s+/g, ' ').trim();
  return words.charAt(0).toUpperCase() + words.slice(1);
}

const TITLES = [
  'Construction Team – B&W Footage',
  'Workers Walking Toward Camera (Slow-Mo)',
  'Energetic Brick-Laying in Progress',
  'Pouring Concrete – Civil Works',
];

/* ─── single video card ───────────────────────────────────────────────────── */
function VideoCard({ title, originalUrl, processedUrl, badge }) {
  const origRef = useRef(null);
  const procRef = useRef(null);
  const [playing, setPlaying] = useState(false);
  const [progress, setProgress] = useState(0);
  const [duration, setDuration] = useState(0);
  const [active, setActive] = useState('processed'); // 'original' | 'processed'

  const currentRef = active === 'original' ? origRef : procRef;

  const toggle = () => {
    const vid = currentRef.current;
    if (!vid) return;
    if (vid.paused) {
      vid.play();
      setPlaying(true);
    } else {
      vid.pause();
      setPlaying(false);
    }
  };

  const restart = () => {
    const vid = currentRef.current;
    if (!vid) return;
    vid.currentTime = 0;
    vid.play();
    setPlaying(true);
  };

  const onTimeUpdate = (ref) => () => {
    const vid = ref.current;
    if (!vid) return;
    setProgress(vid.duration ? (vid.currentTime / vid.duration) * 100 : 0);
  };

  const onLoaded = (ref) => () => {
    const vid = ref.current;
    if (vid) setDuration(vid.duration);
  };

  const onEnded = () => setPlaying(false);

  const seek = (e) => {
    const vid = currentRef.current;
    if (!vid) return;
    const rect = e.currentTarget.getBoundingClientRect();
    const ratio = (e.clientX - rect.left) / rect.width;
    vid.currentTime = ratio * vid.duration;
  };

  // Pause the hidden video when switching tabs
  const switchTab = (tab) => {
    [origRef, procRef].forEach((r) => {
      if (r.current && !r.current.paused) r.current.pause();
    });
    setPlaying(false);
    setActive(tab);
  };

  const fmt = (s) => {
    if (!s || isNaN(s)) return '0:00';
    const m = Math.floor(s / 60);
    const sec = Math.floor(s % 60);
    return `${m}:${sec.toString().padStart(2, '0')}`;
  };

  return (
    <div className="rounded-2xl overflow-hidden border border-[var(--color-border)] bg-[var(--color-surface)] shadow-sm flex flex-col">
      {/* Badge + Title */}
      <div className="px-4 pt-4 pb-2 flex items-start gap-3">
        <span className="inline-flex items-center justify-center w-7 h-7 rounded-full bg-[var(--color-accent)] text-white text-xs font-bold flex-shrink-0 mt-0.5">
          {badge}
        </span>
        <span className="text-sm font-semibold text-[var(--color-text)] leading-tight">{title}</span>
      </div>

      {/* Tab switcher */}
      <div className="flex mx-4 mb-2 rounded-lg overflow-hidden border border-[var(--color-border)] text-xs font-medium">
        <button
          onClick={() => switchTab('original')}
          className={`flex-1 flex items-center justify-center gap-1.5 py-1.5 transition-colors ${
            active === 'original'
              ? 'bg-[var(--color-accent)] text-white'
              : 'text-[var(--color-text-muted)] hover:bg-[var(--color-surface-alt)]'
          }`}
        >
          <Film size={12} />
          Original
        </button>
        <button
          onClick={() => switchTab('processed')}
          className={`flex-1 flex items-center justify-center gap-1.5 py-1.5 transition-colors ${
            active === 'processed'
              ? 'bg-[var(--color-accent)] text-white'
              : 'text-[var(--color-text-muted)] hover:bg-[var(--color-surface-alt)]'
          }`}
        >
          <Cpu size={12} />
          AI Processed
        </button>
      </div>

      {/* Video area */}
      <div className="relative bg-black aspect-video mx-4 rounded-xl overflow-hidden">
        {/* Original – hidden when not active */}
        <video
          ref={origRef}
          src={originalUrl}
          preload="metadata"
          className={`absolute inset-0 w-full h-full object-contain transition-opacity duration-200 ${
            active === 'original' ? 'opacity-100' : 'opacity-0 pointer-events-none'
          }`}
          onTimeUpdate={onTimeUpdate(origRef)}
          onLoadedMetadata={onLoaded(origRef)}
          onEnded={onEnded}
        />
        {/* Processed */}
        <video
          ref={procRef}
          src={processedUrl}
          preload="metadata"
          className={`absolute inset-0 w-full h-full object-contain transition-opacity duration-200 ${
            active === 'processed' ? 'opacity-100' : 'opacity-0 pointer-events-none'
          }`}
          onTimeUpdate={onTimeUpdate(procRef)}
          onLoadedMetadata={onLoaded(procRef)}
          onEnded={onEnded}
        />

        {/* Overlay badge for processed */}
        {active === 'processed' && (
          <span className="absolute top-2 right-2 bg-[var(--color-accent)]/80 text-white text-[10px] font-semibold px-2 py-0.5 rounded-full backdrop-blur-sm">
            AI Annotated
          </span>
        )}
      </div>

      {/* Seek bar */}
      <div
        className="mx-4 mt-2 h-1.5 bg-[var(--color-border)] rounded-full cursor-pointer overflow-hidden"
        onClick={seek}
      >
        <div
          className="h-full bg-[var(--color-accent)] rounded-full transition-all"
          style={{ width: `${progress}%` }}
        />
      </div>

      {/* Controls */}
      <div className="flex items-center gap-3 px-4 py-3">
        <button
          onClick={toggle}
          className="flex items-center justify-center w-8 h-8 rounded-full bg-[var(--color-accent)] text-white hover:opacity-90 transition-opacity"
        >
          {playing ? <Pause size={14} /> : <Play size={14} />}
        </button>
        <button
          onClick={restart}
          className="flex items-center justify-center w-7 h-7 rounded-full border border-[var(--color-border)] text-[var(--color-text-muted)] hover:bg-[var(--color-surface-alt)] transition-colors"
        >
          <RotateCcw size={12} />
        </button>
        <span className="text-[11px] text-[var(--color-text-muted)] ml-auto">
          {fmt(duration)}
        </span>
      </div>
    </div>
  );
}

/* ─── main Demo page ──────────────────────────────────────────────────────── */
export default function Demo() {
  const [demos, setDemos] = useState([]);
  const [originals, setOriginals] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    (async () => {
      try {
        const [dRes, oRes] = await Promise.all([getDemoList(), getDemoOriginals()]);
        setDemos(dRes.demos || []);
        setOriginals(oRes.originals || []);
      } catch (e) {
        setError(e.message);
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  /* pair demos with originals by index */
  const pairs = demos.slice(0, 4).map((d, i) => ({
    demo: d,
    original: originals[i] || null,
    title: TITLES[i] || makeTitle(d.id),
  }));

  return (
    <div className="space-y-6">
      {/* ── Header ── */}
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-xl sm:text-2xl font-bold">Demo – AI Safety Detection</h1>
          <p className="text-sm text-[var(--color-text-muted)] mt-0.5">
            Watch 4 real construction-site clips before and after SafeSight AI processing.
          </p>
        </div>

        <div className="flex items-center gap-2 text-xs text-[var(--color-text-muted)] bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg px-3 py-2">
          <Cpu size={14} className="text-[var(--color-accent)]" />
          YOLO26m · 6-class PPE detection
        </div>
      </div>

      {/* ── Legend ── */}
      <div className="flex flex-wrap gap-4 text-xs">
        {[
          { color: 'bg-green-500', label: 'Compliant person' },
          { color: 'bg-red-500', label: 'CRITICAL violation (helmet + vest missing)' },
          { color: 'bg-orange-400', label: 'WARNING violation' },
          { color: 'bg-yellow-300', label: 'PPE item detected' },
        ].map(({ color, label }) => (
          <span key={label} className="flex items-center gap-1.5 text-[var(--color-text-muted)]">
            <span className={`inline-block w-3 h-3 rounded-sm ${color}`} />
            {label}
          </span>
        ))}
      </div>

      {/* ── Content ── */}
      {loading && (
        <div className="flex items-center justify-center py-24 text-[var(--color-text-muted)] text-sm gap-3">
          <svg className="animate-spin h-5 w-5 text-[var(--color-accent)]" viewBox="0 0 24 24" fill="none">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
          </svg>
          Loading demo videos…
        </div>
      )}

      {error && (
        <div className="rounded-xl border border-red-200 bg-red-50 text-red-700 px-4 py-3 text-sm">
          {error}
        </div>
      )}

      {!loading && !error && pairs.length === 0 && (
        <div className="rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] px-6 py-10 text-center text-sm text-[var(--color-text-muted)]">
          No demo videos found.
          <br />
          Run <code className="bg-[var(--color-surface-alt)] px-1 rounded">python scripts/generate_demo_videos.py</code> to generate them.
        </div>
      )}

      {!loading && pairs.length > 0 && (
        <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-2 gap-5">
          {pairs.map((p, i) => (
            <VideoCard
              key={p.demo.id}
              badge={i + 1}
              title={p.title}
              originalUrl={p.original ? originalVideoUrl(p.original.filename) : ''}
              processedUrl={demoVideoUrl(p.demo.filename)}
            />
          ))}
        </div>
      )}

      {/* ── Info footer ── */}
      <div className="rounded-xl bg-[var(--color-accent-soft)] border border-[var(--color-border)] px-5 py-4 text-sm text-[var(--color-text-muted)] space-y-1">
        <p className="font-semibold text-[var(--color-accent)]">How it works</p>
        <p>Each clip is processed offline through the full SafeSight AI pipeline: YOLO26m detection → centroid tracker → IoU-based PPE violation engine → annotation renderer.</p>
        <p>Green boxes = compliant. Orange = warning (optional PPE missing). Red = critical (helmet or vest missing).</p>
      </div>
    </div>
  );
}
