/**
 * Reusable filter bar with camera, date, and severity selectors.
 */
export default function FilterBar({
  cameras = [],
  dates = [],
  selectedCamera,
  selectedDate,
  selectedSeverity,
  onCameraChange,
  onDateChange,
  onSeverityChange,
  showSeverity = true,
}) {
  const selectClass =
    'w-full sm:w-auto bg-[var(--color-surface)] border border-[var(--color-border)] text-[var(--color-text)] rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-[var(--color-accent)] cursor-pointer';

  return (
    <div className="grid grid-cols-2 sm:flex sm:flex-wrap gap-2 sm:gap-3 items-center">
      {/* Camera */}
      <select
        className={selectClass}
        value={selectedCamera}
        onChange={(e) => onCameraChange(e.target.value)}
      >
        <option value="">All Cameras</option>
        {cameras.map((c) => (
          <option key={c} value={c}>
            {c}
          </option>
        ))}
      </select>

      {/* Date */}
      <select
        className={selectClass}
        value={selectedDate}
        onChange={(e) => onDateChange(e.target.value)}
      >
        <option value="">All Dates</option>
        {dates.map((d) => (
          <option key={d} value={d}>
            {d}
          </option>
        ))}
      </select>

      {/* Severity */}
      {showSeverity && (
        <select
          className={`${selectClass} col-span-2 sm:col-span-1`}
          value={selectedSeverity}
          onChange={(e) => onSeverityChange(e.target.value)}
        >
          <option value="">All Severities</option>
          <option value="critical">🔴 Critical</option>
          <option value="warning">🟡 Warning</option>
        </select>
      )}
    </div>
  );
}
