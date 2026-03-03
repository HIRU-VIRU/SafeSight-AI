/**
 * Reusable stat card with icon, label, and value.
 */
export default function StatCard({ icon: Icon, label, value, color = 'var(--color-accent)' }) {
  return (
    <div
      className="card-hover bg-[var(--color-surface)] rounded-2xl border border-[var(--color-border)] p-5 flex items-center gap-4 shadow-sm overflow-hidden relative"
      style={{ borderLeft: `3px solid ${color}` }}
    >
      {/* gradient tint strip */}
      <div
        className="absolute inset-0 opacity-[0.03] pointer-events-none"
        style={{ background: `linear-gradient(135deg, ${color} 0%, transparent 70%)` }}
      />
      <div
        className="flex items-center justify-center w-12 h-12 rounded-2xl flex-shrink-0"
        style={{ background: `linear-gradient(135deg, ${color}22 0%, ${color}10 100%)` }}
      >
        <Icon size={21} style={{ color }} />
      </div>
      <div className="min-w-0">
        <p className="text-xs font-semibold text-[var(--color-text-muted)] uppercase tracking-widest truncate">{label}</p>
        <p className="text-2xl font-extrabold leading-tight mt-0.5" style={{ color }}>
          {value ?? '—'}
        </p>
      </div>
    </div>
  );
}
