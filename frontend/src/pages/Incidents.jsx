import { useEffect, useState, useCallback } from 'react';
import { X } from 'lucide-react';

import FilterBar from '../components/FilterBar';
import {
  getFilteredViolations,
  getCameras,
  getDates,
  violationImageUrl,
} from '../api';

export default function Incidents() {
  const [violations, setViolations] = useState([]);
  const [cameras, setCameras] = useState([]);
  const [dates, setDates] = useState([]);
  const [camera, setCamera] = useState('');
  const [date, setDate] = useState('');
  const [loading, setLoading] = useState(false);
  const [lightbox, setLightbox] = useState(null); // image URL for lightbox

  useEffect(() => {
    getCameras().then((d) => setCameras(d.cameras || [])).catch(() => {});
    getDates().then((d) => setDates(d.dates || [])).catch(() => {});
  }, []);

  const fetchData = useCallback(async () => {
    setLoading(true);
    try {
      // Only show critical violations that have images
      const res = await getFilteredViolations({
        cameraId: camera || undefined,
        date: date || undefined,
        severity: 'critical',
        limit: 500,
      });
      // Filter to entries with images
      setViolations((res.violations || []).filter((v) => v.image_path));
    } catch (err) {
      console.error('Incidents fetch error:', err);
    } finally {
      setLoading(false);
    }
  }, [camera, date]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  return (
    <div className="space-y-6">
      <h1 className="text-xl sm:text-2xl font-bold">Incident Images</h1>

      <FilterBar
        cameras={cameras}
        dates={dates}
        selectedCamera={camera}
        selectedDate={date}
        onCameraChange={setCamera}
        onDateChange={setDate}
        showSeverity={false}
      />

      {loading ? (
        <div className="text-center py-12 text-[var(--color-text-muted)]">Loading…</div>
      ) : violations.length === 0 ? (
        <div className="text-center py-12 text-[var(--color-text-muted)]">
          No incident images found
        </div>
      ) : (
        <>
          <p className="text-sm text-[var(--color-text-muted)]">
            Showing <strong>{violations.length}</strong> critical incident(s) with images
          </p>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
            {violations.map((v) => {
              const imgUrl = violationImageUrl(v.image_path);
              const missing = [];
              if (v.helmet_violation) missing.push('Helmet');
              if (v.vest_violation) missing.push('Vest');
              if (v.boots_violation) missing.push('Boots');
              if (v.gloves_violation) missing.push('Gloves');
              if (v.goggles_violation) missing.push('Goggles');

              return (
                <div
                  key={v.id}
                  className="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-xl overflow-hidden hover:border-[var(--color-critical)] transition-colors"
                >
                  <img
                    src={imgUrl}
                    alt={`Incident ${v.id}`}
                    className="w-full h-44 object-cover cursor-pointer hover:opacity-90 transition-opacity"
                    loading="lazy"
                    onClick={() => setLightbox(imgUrl)}
                  />
                  <div className="p-3 space-y-1">
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-semibold text-[var(--color-critical)] uppercase">
                        Critical
                      </span>
                      <span className="text-xs text-[var(--color-text-muted)]">
                        Person #{v.person_id}
                      </span>
                    </div>
                    <p className="text-xs text-[var(--color-text-muted)]">
                      {v.camera_id} &middot;{' '}
                      {v.timestamp ? new Date(v.timestamp).toLocaleString() : '—'}
                    </p>
                    <div className="flex flex-wrap gap-1 pt-1">
                      {missing.map((m) => (
                        <span
                          key={m}
                          className="px-2 py-0.5 rounded text-[10px] font-medium bg-[var(--color-surface-alt)] text-[var(--color-text)]"
                        >
                          {m}
                        </span>
                      ))}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </>
      )}

      {/* Lightbox */}
      {lightbox && (
        <div
          className="fixed inset-0 z-50 bg-black/80 flex items-center justify-center p-4"
          onClick={() => setLightbox(null)}
        >
          <button
            className="absolute top-4 right-4 text-white hover:opacity-80"
            onClick={() => setLightbox(null)}
          >
            <X size={28} />
          </button>
          <img
            src={lightbox}
            alt="Incident"
            className="max-h-[90vh] max-w-[90vw] rounded-lg shadow-xl"
            onClick={(e) => e.stopPropagation()}
          />
        </div>
      )}
    </div>
  );
}
