import { useEffect, useState } from 'react';
import {
  AlertOctagon,
  AlertTriangle,
  ShieldCheck,
  BarChart3,
  RefreshCw,
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
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Dashboard</h1>
        <button
          onClick={load}
          disabled={loading}
          className="flex items-center gap-2 px-4 py-2 bg-[var(--color-accent)] text-white rounded-lg text-sm font-medium hover:opacity-90 transition-opacity disabled:opacity-50"
        >
          <RefreshCw size={16} className={loading ? 'animate-spin' : ''} />
          Refresh
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
      <div className="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-xl p-5">
        <h2 className="text-lg font-semibold mb-4">Hourly Violations (Today)</h2>
        <div className="h-64">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={hourly}>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" />
              <XAxis
                dataKey="hour"
                tick={{ fill: 'var(--color-text-muted)', fontSize: 11 }}
                interval={1}
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
      <div className="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-xl p-5">
        <h2 className="text-lg font-semibold mb-4">Recent Violations</h2>
        <ViolationTable violations={recent} showImage={false} />
      </div>
    </div>
  );
}
