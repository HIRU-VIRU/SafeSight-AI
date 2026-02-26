/**
 * Reusable stat card with icon, label, and value.
 */
export default function StatCard({ icon: Icon, label, value, color = 'var(--color-accent)' }) {
  return (
    <div
      className="bg-[var(--color-surface)] rounded-xl border border-[var(--color-border)] p-5 flex items-center gap-4 shadow-sm hover:shadow-md transition-all overflow-hidden relative"
      style={{ borderLeft: `4px solid ${color}` }}
    >
      {/* subtle tinted bg strip */}
      <div
        className="absolute inset-0 opacity-[0.04] pointer-events-none"
        style={{ background: color }}
      />
      <div
        className="flex items-center justify-center w-11 h-11 rounded-xl flex-shrink-0"
        style={{ backgroundColor: `${color}18` }}
      >
        <Icon size={20} style={{ color }} />
      </div>
      <div className="min-w-0">
        <p className="text-xs font-medium text-[var(--color-text-muted)] uppercase tracking-wide truncate">{label}</p>
        <p className="text-2xl font-bold leading-tight" style={{ color }}>
          {value ?? '—'}
        </p>
      </div>
    </div>
  );
}
