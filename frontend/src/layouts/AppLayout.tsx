import { useState } from "react";
import { NavLink, Outlet } from "react-router-dom";
import {
  Activity,
  BookOpen,
  Gauge,
  Menu,
  Shield,
  ShieldAlert,
  SlidersHorizontal,
  X,
  Zap,
} from "lucide-react";

const nav = [
  { to: "/", label: "Overview", icon: Gauge, end: true },
  { to: "/events", label: "Events", icon: Activity },
  { to: "/detection", label: "Detection", icon: ShieldAlert },
  { to: "/rate-limits", label: "Rate Limits", icon: SlidersHorizontal },
  { to: "/captcha", label: "CAPTCHA", icon: Shield },
  { to: "/simulator", label: "Simulator", icon: Zap },
  { to: "/about", label: "About", icon: BookOpen },
];

export function AppLayout() {
  const [open, setOpen] = useState(false);

  return (
    <div className="flex min-h-screen">
      {/* Mobile overlay */}
      {open && (
        <button
          type="button"
          className="fixed inset-0 z-30 bg-black/60 lg:hidden"
          aria-label="Close menu"
          onClick={() => setOpen(false)}
        />
      )}

      <aside
        className={`fixed inset-y-0 left-0 z-40 flex w-64 flex-col border-r border-white/5 bg-surface-900/95 backdrop-blur transition-transform lg:static lg:translate-x-0 ${
          open ? "translate-x-0" : "-translate-x-full"
        }`}
      >
        <div className="flex items-center gap-3 border-b border-white/5 px-5 py-5">
          <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-accent-soft text-accent">
            <Shield className="h-5 w-5" aria-hidden />
          </div>
          <div>
            <p className="text-sm font-semibold tracking-tight text-slate-50">BotShield Lab</p>
            <p className="text-xs text-slate-500">Anti-bot testing</p>
          </div>
          <button
            type="button"
            className="ml-auto rounded-lg p-1 text-slate-400 hover:bg-surface-800 lg:hidden"
            onClick={() => setOpen(false)}
            aria-label="Close navigation"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        <nav className="flex-1 space-y-1 p-3" aria-label="Main">
          {nav.map(({ to, label, icon: Icon, end }) => (
            <NavLink
              key={to}
              to={to}
              end={end}
              onClick={() => setOpen(false)}
              className={({ isActive }) =>
                `flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm transition ${
                  isActive
                    ? "bg-accent-soft text-accent"
                    : "text-slate-400 hover:bg-surface-800 hover:text-slate-200"
                }`
              }
            >
              <Icon className="h-4 w-4 shrink-0" aria-hidden />
              {label}
            </NavLink>
          ))}
        </nav>

        <div className="border-t border-white/5 p-4 text-xs text-slate-500">
          Local demo only · MIT License
        </div>
      </aside>

      <div className="flex min-w-0 flex-1 flex-col">
        <header className="sticky top-0 z-20 flex items-center gap-3 border-b border-white/5 bg-surface-950/80 px-4 py-3 backdrop-blur lg:px-8">
          <button
            type="button"
            className="rounded-lg p-2 text-slate-300 hover:bg-surface-800 lg:hidden"
            onClick={() => setOpen(true)}
            aria-label="Open navigation"
          >
            <Menu className="h-5 w-5" />
          </button>
          <div className="min-w-0">
            <p className="truncate text-sm font-medium text-slate-200">
              Controlled defensive demonstration
            </p>
            <p className="truncate text-xs text-slate-500">
              Not a production WAF — for learning and portfolio review
            </p>
          </div>
        </header>

        <main className="flex-1 px-4 py-6 lg:px-8">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
