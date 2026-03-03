import { useState } from 'react';
import { NavLink, Outlet } from 'react-router-dom';
import {
  LayoutDashboard,
  AlertTriangle,
  Image,
  Play,
  ShieldAlert,
  Menu,
  X,
  Film,
} from 'lucide-react';

const NAV = [
  { to: '/', icon: LayoutDashboard, label: 'Dashboard' },
  { to: '/demo', icon: Film, label: 'Demo' },
  { to: '/alerts', icon: AlertTriangle, label: 'Alerts' },
  { to: '/incidents', icon: Image, label: 'Incidents' },
  { to: '/inference', icon: Play, label: 'Inference' },
];

export default function Layout() {
  const [open, setOpen] = useState(false);

  return (
    <div className="flex h-screen overflow-hidden">
      {/* Mobile overlay */}
      {open && (
        <div
          className="fixed inset-0 bg-black/20 backdrop-blur-sm z-20 md:hidden"
          onClick={() => setOpen(false)}
        />
      )}

      {/* Sidebar */}
      <aside
        className={`
          fixed md:static inset-y-0 left-0 z-30
          w-64 flex-shrink-0 flex flex-col
          bg-[var(--color-surface)] border-r border-[var(--color-border)]
          shadow-lg md:shadow-none
          transition-transform duration-200
          ${open ? 'translate-x-0' : '-translate-x-full md:translate-x-0'}
        `}
      >
        {/* Logo */}
        <div className="flex items-center justify-between px-5 py-5 border-b border-[var(--color-border)]">
          <div className="flex items-center gap-2.5">
            <div
              className="w-9 h-9 rounded-xl flex items-center justify-center shadow-md"
              style={{ background: 'var(--grad-primary)' }}
            >
              <ShieldAlert className="text-white" size={18} />
            </div>
            <div>
              <span className="text-base font-extrabold tracking-tight text-[var(--color-text)]">SafeSight</span>
              <span
                className="text-base font-extrabold tracking-tight ml-1"
                style={{ background: 'var(--grad-primary)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}
              >AI</span>
            </div>
          </div>
          <button
            className="md:hidden p-1 rounded-md text-[var(--color-text-muted)] hover:bg-[var(--color-surface-alt)] transition-colors"
            onClick={() => setOpen(false)}
          >
            <X size={18} />
          </button>
        </div>

        {/* Nav links */}
        <nav className="flex-1 py-4 space-y-0.5 px-3">
          {NAV.map(({ to, icon: Icon, label }) => (
            <NavLink
              key={to}
              to={to}
              end={to === '/'}
              onClick={() => setOpen(false)}
              className={({ isActive }) =>
                `relative flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-all ${
                  isActive
                    ? 'nav-active'
                    : 'nav-idle text-[var(--color-text-muted)] hover:text-[var(--color-text)]'
                }`
              }
            >
              <Icon size={17} />
              {label}
            </NavLink>
          ))}
        </nav>

        {/* Footer */}
        <div className="px-4 py-4 border-t border-[var(--color-border)]">
          <div
            className="flex items-center gap-2 rounded-lg px-3 py-2"
            style={{ background: 'linear-gradient(135deg,rgba(79,70,229,.06) 0%,rgba(124,58,237,.06) 100%)' }}
          >
            <div className="relative">
              <div className="w-2 h-2 rounded-full bg-[var(--color-success)]"></div>
              <div className="absolute inset-0 w-2 h-2 rounded-full bg-[var(--color-success)] animate-ping opacity-60"></div>
            </div>
            <span className="text-xs font-medium text-[var(--color-text-muted)]">SafeSight AI v1.0 · Live</span>
          </div>
        </div>
      </aside>

      {/* Content area */}
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
        {/* Mobile top bar */}
        <header className="md:hidden flex items-center gap-3 px-4 py-3 bg-[var(--color-surface)] border-b border-[var(--color-border)] shadow-sm flex-shrink-0">
          <button
            onClick={() => setOpen(true)}
            className="p-1.5 rounded-md text-[var(--color-text-muted)] hover:bg-[var(--color-surface-alt)] transition-colors"
          >
            <Menu size={20} />
          </button>
          <div className="w-6 h-6 rounded-md bg-[var(--color-accent)] flex items-center justify-center">
            <ShieldAlert className="text-white" size={13} />
          </div>
          <span className="font-bold text-sm text-[var(--color-text)]">SafeSight AI</span>
        </header>

        {/* Main content */}
        <main className="flex-1 overflow-y-auto p-4 md:p-6">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
