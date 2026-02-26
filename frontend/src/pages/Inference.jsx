import { useEffect, useState } from 'react';
import { Play, Square, RefreshCw, Wifi, WifiOff, Video, VideoOff } from 'lucide-react';
import {
  startInference,
  getInferenceStatus,
  stopInference,
  healthCheck,
  inferenceStreamUrl,
} from '../api';

export default function Inference() {
  const [source, setSource] = useState('');
  const [streamId, setStreamId] = useState('');
  const [streams, setStreams] = useState([]);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [loading, setLoading] = useState(false);
  const [apiOnline, setApiOnline] = useState(null);
  const [expandedStream, setExpandedStream] = useState(null); // stream_id to show full-size

  const refresh = async () => {
    try {
      await healthCheck();
      setApiOnline(true);
      const res = await getInferenceStatus();
      setStreams(res.streams || []);
    } catch {
      setApiOnline(false);
      setStreams([]);
    }
  };

  useEffect(() => {
    refresh();
    const interval = setInterval(refresh, 5000);
    return () => clearInterval(interval);
  }, []);

  const handleStart = async (e) => {
    e.preventDefault();
    setError('');
    setSuccess('');
    if (!source.trim()) {
      setError('Please enter a video source URL or path');
      return;
    }
    setLoading(true);
    try {
      const res = await startInference(source.trim(), streamId.trim() || undefined);
      setSuccess(`Started stream "${res.stream_id}" on source: ${res.source}`);
      setSource('');
      setStreamId('');
      setTimeout(refresh, 1000);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleStop = async (sid) => {
    try {
      await stopInference(sid);
      setSuccess(`Stopped stream "${sid}"`);
      if (expandedStream === sid) setExpandedStream(null);
      setTimeout(refresh, 500);
    } catch (err) {
      setError(err.message);
    }
  };

  const inputClass =
    'w-full bg-[var(--color-surface-alt)] border border-[var(--color-border)] text-[var(--color-text)] rounded-lg px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-[var(--color-accent)] placeholder:text-[var(--color-text-muted)]';

  const aliveStreams = streams.filter((s) => s.alive);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h1 className="text-xl sm:text-2xl font-bold">Inference Control</h1>
        <span className="flex items-center gap-2 text-sm">
          {apiOnline === true ? (
            <>
              <Wifi size={16} className="text-[var(--color-success)]" />
              <span className="text-[var(--color-success)]">API Online</span>
            </>
          ) : apiOnline === false ? (
            <>
              <WifiOff size={16} className="text-[var(--color-critical)]" />
              <span className="text-[var(--color-critical)]">API Offline</span>
            </>
          ) : (
            <span className="text-[var(--color-text-muted)]">Checking…</span>
          )}
        </span>
      </div>

      {/* Start form */}
      <form
        onSubmit={handleStart}
        className="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-xl p-4 sm:p-6 space-y-4"
      >
        <h2 className="text-base sm:text-lg font-semibold">Start New Inference</h2>

        <div>
          <label className="block text-sm text-[var(--color-text-muted)] mb-1">
            Video Source <span className="text-[var(--color-critical)]">*</span>
          </label>
          <input
            className={inputClass}
            placeholder="rtsp://camera_ip:port/stream  or  /path/to/video.mp4  or  http://..."
            value={source}
            onChange={(e) => setSource(e.target.value)}
          />
        </div>

        <div>
          <label className="block text-sm text-[var(--color-text-muted)] mb-1">
            Stream Label <span className="text-[var(--color-text-muted)]">(optional)</span>
          </label>
          <input
            className={inputClass}
            placeholder="e.g. gate_camera_01"
            value={streamId}
            onChange={(e) => setStreamId(e.target.value)}
          />
        </div>

        {error && (
          <p className="text-sm text-[var(--color-critical)] bg-[var(--color-critical)]/10 px-4 py-2 rounded-lg">
            {error}
          </p>
        )}
        {success && (
          <p className="text-sm text-[var(--color-success)] bg-[var(--color-success)]/10 px-4 py-2 rounded-lg">
            {success}
          </p>
        )}

        <button
          type="submit"
          disabled={loading || apiOnline === false}
          className="flex items-center gap-2 px-6 py-2.5 bg-[var(--color-accent)] text-white rounded-lg text-sm font-medium hover:opacity-90 transition-opacity disabled:opacity-50"
        >
          <Play size={16} />
          {loading ? 'Starting…' : 'Start Inference'}
        </button>
      </form>

      {/* Running streams */}
      <div className="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-xl p-4 sm:p-6 space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-base sm:text-lg font-semibold">Running Streams</h2>
          <button
            onClick={refresh}
            className="p-2 rounded-lg hover:bg-[var(--color-surface-alt)] transition-colors"
          >
            <RefreshCw size={16} />
          </button>
        </div>

        {streams.length === 0 ? (
          <p className="text-sm text-[var(--color-text-muted)]">No active streams</p>
        ) : (
          <div className="space-y-3">
            {streams.map((s) => (
              <div
                key={s.stream_id}
                className="bg-[var(--color-surface-alt)] rounded-lg overflow-hidden"
              >
                <div className="flex items-center justify-between px-4 py-3">
                  <div>
                    <p className="text-sm font-medium">{s.stream_id}</p>
                    <p className="text-xs text-[var(--color-text-muted)]">
                      {s.source} &middot; started{' '}
                      {new Date(s.started_at).toLocaleTimeString()}
                    </p>
                  </div>
                  <div className="flex items-center gap-3">
                    <span
                      className={`text-xs font-semibold ${
                        s.alive
                          ? 'text-[var(--color-success)]'
                          : 'text-[var(--color-text-muted)]'
                      }`}
                    >
                      {s.alive ? 'Running' : 'Stopped'}
                    </span>
                    {s.alive && (
                      <>
                        <button
                          onClick={() =>
                            setExpandedStream(
                              expandedStream === s.stream_id ? null : s.stream_id,
                            )
                          }
                          className="p-1.5 rounded-lg bg-[var(--color-accent)]/20 text-[var(--color-accent)] hover:bg-[var(--color-accent)]/30 transition-colors"
                          title={
                            expandedStream === s.stream_id
                              ? 'Hide live view'
                              : 'Show live view'
                          }
                        >
                          {expandedStream === s.stream_id ? (
                            <VideoOff size={14} />
                          ) : (
                            <Video size={14} />
                          )}
                        </button>
                        <button
                          onClick={() => handleStop(s.stream_id)}
                          className="p-1.5 rounded-lg bg-[var(--color-critical)]/20 text-[var(--color-critical)] hover:bg-[var(--color-critical)]/30 transition-colors"
                          title="Stop stream"
                        >
                          <Square size={14} />
                        </button>
                      </>
                    )}
                  </div>
                </div>

                {/* Inline MJPEG live view */}
                {expandedStream === s.stream_id && s.alive && (
                  <div className="px-4 pb-4">
                    <img
                      src={inferenceStreamUrl(s.stream_id)}
                      alt={`Live: ${s.stream_id}`}
                      className="w-full rounded-lg border border-[var(--color-border)]"
                    />
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Live Feed Grid — show all live streams at once */}
      {aliveStreams.length > 0 && (
        <div className="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-xl p-4 sm:p-6 space-y-4">
          <h2 className="text-base sm:text-lg font-semibold">Live Feed</h2>
          <div
            className={`grid gap-4 ${
              aliveStreams.length === 1
                ? 'grid-cols-1'
                : 'grid-cols-1 lg:grid-cols-2'
            }`}
          >
            {aliveStreams.map((s) => (
              <div key={s.stream_id} className="space-y-2">
                <div className="flex items-center gap-2">
                  <span className="inline-block w-2 h-2 rounded-full bg-[var(--color-critical)] animate-pulse" />
                  <span className="text-sm font-medium">{s.stream_id}</span>
                </div>
                <img
                  src={inferenceStreamUrl(s.stream_id)}
                  alt={`Live: ${s.stream_id}`}
                  className="w-full rounded-lg border border-[var(--color-border)]"
                />
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
