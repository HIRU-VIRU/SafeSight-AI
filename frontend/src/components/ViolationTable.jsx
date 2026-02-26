import { violationImageUrl } from '../api';
import { AlertTriangle, AlertOctagon, Clock, Camera, User } from 'lucide-react';

function severity(v) {
  if (v.helmet_violation && v.vest_violation) return 'critical';
  if (v.helmet_violation || v.vest_violation || v.boots_violation || v.gloves_violation || v.goggles_violation)
    return 'warning';
  return 'normal';
}

function missingList(v) {
  const missing = [];
  if (v.helmet_violation) missing.push('Helmet');
  if (v.vest_violation) missing.push('Vest');
  if (v.boots_violation) missing.push('Boots');
  if (v.gloves_violation) missing.push('Gloves');
  if (v.goggles_violation) missing.push('Goggles');
  return missing;
}

/**
 * Table to display violations.
 */
export default function ViolationTable({ violations = [], showImage = false }) {
  if (violations.length === 0) {
    return (
      <div className="text-center py-12 text-[var(--color-text-muted)]">
        No violations found
      </div>
    );
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-[var(--color-border)] text-left text-[var(--color-text-muted)]">
            <th className="py-3 px-4">Severity</th>
            <th className="py-3 px-4">Time</th>
            <th className="py-3 px-4">Camera</th>
            <th className="py-3 px-4">Person</th>
            <th className="py-3 px-4">Missing PPE</th>
            {showImage && <th className="py-3 px-4">Image</th>}
          </tr>
        </thead>
        <tbody>
          {violations.map((v) => {
            const sev = severity(v);
            const missing = missingList(v);
            const sevColor =
              sev === 'critical'
                ? 'var(--color-critical)'
                : sev === 'warning'
                ? 'var(--color-warning)'
                : 'var(--color-success)';
            const SevIcon = sev === 'critical' ? AlertOctagon : AlertTriangle;

            return (
              <tr
                key={v.id}
                className="border-b border-[var(--color-border)] hover:bg-[var(--color-surface-alt)] transition-colors"
              >
                <td className="py-3 px-4">
                  <span
                    className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold uppercase"
                    style={{ backgroundColor: `${sevColor}20`, color: sevColor }}
                  >
                    <SevIcon size={12} />
                    {sev}
                  </span>
                </td>
                <td className="py-3 px-4 text-[var(--color-text-muted)] whitespace-nowrap">
                  <span className="inline-flex items-center gap-1">
                    <Clock size={13} />
                    {v.timestamp ? new Date(v.timestamp).toLocaleString() : '—'}
                  </span>
                </td>
                <td className="py-3 px-4">
                  <span className="inline-flex items-center gap-1">
                    <Camera size={13} />
                    {v.camera_id}
                  </span>
                </td>
                <td className="py-3 px-4">
                  <span className="inline-flex items-center gap-1">
                    <User size={13} />
                    #{v.person_id}
                  </span>
                </td>
                <td className="py-3 px-4">
                  <div className="flex flex-wrap gap-1.5">
                    {missing.map((m) => (
                      <span
                        key={m}
                        className="px-2 py-0.5 rounded text-xs font-medium bg-[var(--color-surface-alt)] text-[var(--color-text)]"
                      >
                        {m}
                      </span>
                    ))}
                  </div>
                </td>
                {showImage && (
                  <td className="py-3 px-4">
                    {v.image_path ? (
                      <img
                        src={violationImageUrl(v.image_path)}
                        alt={`Violation ${v.id}`}
                        className="h-16 w-24 object-cover rounded border border-[var(--color-border)] cursor-pointer hover:opacity-80"
                        loading="lazy"
                        onClick={() => window.open(violationImageUrl(v.image_path), '_blank')}
                      />
                    ) : (
                      <span className="text-[var(--color-text-muted)]">—</span>
                    )}
                  </td>
                )}
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
