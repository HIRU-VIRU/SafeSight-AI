/**
 * Reusable stat card with icon, label, and value.
 */
export default function StatCard({ icon: Icon, label, value, color = 'var(--color-accent)' }) {
  return (
    <div className="bg-[var(--color-surface)] rounded-xl border border-[var(--color-border)] p-5 flex items-center gap-4 shadow-sm hover:shadow-md transition-shadow">
      <div
        className="flex items-center justify-center w-12 h-12 rounded-lg"
        style={{ backgroundColor: `${color}20` }}
      >
        <Icon size={22} style={{ color }} />
      </div>
      <div>
        <p className="text-sm text-[var(--color-text-muted)]">{label}</p>
        <p className="text-2xl font-bold" style={{ color }}>
          {value ?? '—'}
        </p>
      </div>
    </div>
  );
}
