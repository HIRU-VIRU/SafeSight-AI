import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  AlertOctagon,
  AlertTriangle,
  ShieldCheck,
  BarChart3,
  RefreshCw,
  Film,
  Radio,
} from 'lucide-react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid,
} from 'recharts';

import StatCard from '../components/StatCard';
import ViolationTable from '../components/ViolationTable';
import {
  getSeverityCounts,
  getHourlyStats,
  getRecentViolations,
} from '../api';

export default function Dashboard() {
  const navigate = useNavigate();
  const [counts, setCounts] = useState(null);
  const [hourly, setHourly] = useState([]);
  const [recent, setRecent] = useState([]);
  const [loading, setLoading] = useState(true);

  const load = async () => {
    setLoading(true);
    try {
      const [c, h, r] = await Promise.all([
        getSeverityCounts(),
        getHourlyStats(),
        getRecentViolations(15),
      ]);
      setCounts(c);
      // Pad hourly data to 24 hours
      const hourMap = Object.fromEntries((h.hourly_stats || []).map((x) => [x.hour, x.count]));
      const padded = Array.from({ length: 24 }, (_, i) => ({
        hour: `${String(i).padStart(2, '0')}:00`,
        count: hourMap[i] || 0,
      }));
      setHourly(padded);
      setRecent(r.violations || []);
    } catch (err) {
      console.error('Dashboard load error:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
    const interval = setInterval(load, 30000); // auto-refresh 30s
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-xl sm:text-2xl font-bold">Dashboard</h1>
          <p className="text-sm text-[var(--color-text-muted)] mt-0.5">Real-time PPE compliance overview</p>
        </div>
        <button
          onClick={load}
          disabled={loading}
          className="flex items-center gap-2 px-4 py-2 bg-[var(--color-surface)] border border-[var(--color-border)] text-[var(--color-text-muted)] rounded-xl text-sm font-medium hover:bg-[var(--color-surface-alt)] transition-all disabled:opacity-50"
        >
          <RefreshCw size={15} className={loading ? 'animate-spin' : ''} />
          Refresh
        </button>
      </div>

      {/* Quick Actions */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        {/* Live Inference */}
        <button
          onClick={() => navigate('/inference')}
          className="btn-live group relative overflow-hidden rounded-2xl px-6 py-5 text-white text-left shadow-lg"
        >
          <div className="absolute inset-0 opacity-0 group-hover:opacity-100 transition-opacity duration-300" style={{ background: 'linear-gradient(135deg,rgba(255,255,255,.08) 0%,transparent 60%)' }} />
          <div className="flex items-center gap-4">
            <div className="w-12 h-12 rounded-xl bg-white/20 flex items-center justify-center flex-shrink-0 backdrop-blur-sm">
              <Radio size={22} className="text-white" />
            </div>
            <div>
              <p className="text-base font-bold tracking-tight">Live Inference</p>
              <p className="text-xs text-white/75 mt-0.5">Start real-time PPE detection on a video stream</p>
            </div>
          </div>
          <div className="absolute right-5 top-1/2 -translate-y-1/2 opacity-30 group-hover:opacity-60 transition-opacity">
            <Radio size={48} />
          </div>
        </button>

        {/* Demo */}
        <button
          onClick={() => navigate('/demo')}
          className="btn-demo group relative overflow-hidden rounded-2xl px-6 py-5 text-white text-left shadow-lg"
        >
          <div className="absolute inset-0 opacity-0 group-hover:opacity-100 transition-opacity duration-300" style={{ background: 'linear-gradient(135deg,rgba(255,255,255,.08) 0%,transparent 60%)' }} />
          <div className="flex items-center gap-4">
            <div className="w-12 h-12 rounded-xl bg-white/20 flex items-center justify-center flex-shrink-0 backdrop-blur-sm">
              <Film size={22} className="text-white" />
            </div>
            <div>
              <p className="text-base font-bold tracking-tight">Demo Videos</p>
              <p className="text-xs text-white/75 mt-0.5">Watch 4 pre-processed AI safety detection clips</p>
            </div>
          </div>
          <div className="absolute right-5 top-1/2 -translate-y-1/2 opacity-30 group-hover:opacity-60 transition-opacity">
            <Film size={48} />
          </div>
        </button>
      </div>

      {/* Stat cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          icon={AlertOctagon}
          label="Critical Alerts"
          value={counts?.critical ?? '—'}
          color="var(--color-critical)"
        />
        <StatCard
          icon={AlertTriangle}
          label="Warning Alerts"
          value={counts?.warning ?? '—'}
          color="var(--color-warning)"
        />
        <StatCard
          icon={ShieldCheck}
          label="Total Violations"
          value={counts?.total ?? '—'}
          color="var(--color-accent)"
        />
        <StatCard
          icon={BarChart3}
          label="Today (Hourly Peak)"
          value={hourly.length ? Math.max(...hourly.map((h) => h.count)) : '—'}
          color="var(--color-success)"
        />
      </div>

      {/* Hourly chart */}
      <div className="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-xl p-4 sm:p-5">
        <h2 className="text-base sm:text-lg font-semibold mb-4">Hourly Violations — Today</h2>
        <div className="h-52 sm:h-64">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={hourly}>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" />
              <XAxis
                dataKey="hour"
                tick={{ fill: 'var(--color-text-muted)', fontSize: 10 }}
                interval={3}
                tickFormatter={(v) => v.replace(':00', 'h')}
              />
              <YAxis tick={{ fill: 'var(--color-text-muted)', fontSize: 11 }} allowDecimals={false} />
              <Tooltip
                contentStyle={{
                  background: 'var(--color-surface-alt)',
                  border: '1px solid var(--color-border)',
                  borderRadius: '8px',
                  color: 'var(--color-text)',
                }}
              />
              <Bar dataKey="count" fill="var(--color-accent)" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Recent violations */}
      <div className="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-xl p-4 sm:p-5">
        <h2 className="text-base sm:text-lg font-semibold mb-4">Recent Violations</h2>
        <ViolationTable violations={recent} showImage={false} />
      </div>
    </div>
  );
}
