import { useEffect, useState, useCallback } from 'react';
import { Download } from 'lucide-react';

import FilterBar from '../components/FilterBar';
import ViolationTable from '../components/ViolationTable';
import {
  getFilteredViolations,
  getCameras,
  getDates,
  exportCSV,
} from '../api';

export default function Alerts() {
  const [violations, setViolations] = useState([]);
  const [cameras, setCameras] = useState([]);
  const [dates, setDates] = useState([]);
  const [camera, setCamera] = useState('');
  const [date, setDate] = useState('');
  const [severity, setSeverity] = useState('');
  const [loading, setLoading] = useState(false);

  // Load filter options once
  useEffect(() => {
    getCameras().then((d) => setCameras(d.cameras || [])).catch(() => {});
    getDates().then((d) => setDates(d.dates || [])).catch(() => {});
  }, []);

  // Fetch violations whenever filters change
  const fetchData = useCallback(async () => {
    setLoading(true);
    try {
      const res = await getFilteredViolations({
        cameraId: camera || undefined,
        date: date || undefined,
        severity: severity || undefined,
        limit: 500,
      });
      setViolations(res.violations || []);
    } catch (err) {
      console.error('Alerts fetch error:', err);
    } finally {
      setLoading(false);
    }
  }, [camera, date, severity]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const handleExport = async () => {
    try {
      await exportCSV({ startDate: date || undefined, endDate: date || undefined });
    } catch (err) {
      alert('Export failed: ' + err.message);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Alerts</h1>
        <button
          onClick={handleExport}
          className="flex items-center gap-2 px-4 py-2 bg-[var(--color-surface-alt)] border border-[var(--color-border)] rounded-lg text-sm font-medium hover:bg-[var(--color-border)] transition-colors"
        >
          <Download size={16} />
          Export CSV
        </button>
      </div>

      {/* Filters */}
      <FilterBar
        cameras={cameras}
        dates={dates}
        selectedCamera={camera}
        selectedDate={date}
        selectedSeverity={severity}
        onCameraChange={setCamera}
        onDateChange={setDate}
        onSeverityChange={setSeverity}
      />

      {/* Results */}
      <div className="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-xl p-5">
        {loading ? (
          <div className="text-center py-12 text-[var(--color-text-muted)]">Loading…</div>
        ) : (
          <>
            <p className="text-sm text-[var(--color-text-muted)] mb-4">
              Showing <strong>{violations.length}</strong> violation(s)
            </p>
            <ViolationTable violations={violations} showImage={false} />
          </>
        )}
      </div>
    </div>
  );
}
