import { NavLink } from 'react-router-dom';

import { useAuth } from '../../context/AuthContext';
import { CloseIcon, DashboardIcon, IssueIcon, UsersIcon } from '../ui/icons';

interface SidebarProps {
  isOpen: boolean;
  onClose: () => void;
}

const NAV_ITEMS = [
  { to: '/', label: 'Dashboard', icon: DashboardIcon, end: true, adminOnly: false },
  { to: '/issues', label: 'Issues', icon: IssueIcon, end: false, adminOnly: false },
  { to: '/users', label: 'Users', icon: UsersIcon, end: false, adminOnly: true },
];

function SidebarContent({ onNavigate }: { onNavigate?: () => void }) {
  const { isAdmin } = useAuth();
  const navItems = NAV_ITEMS.filter((item) => !item.adminOnly || isAdmin);

  return (
    <div className="flex h-full flex-col">
      <div className="flex h-16 items-center gap-2 border-b border-slate-800 px-6">
        <span className="flex h-8 w-8 items-center justify-center rounded-md bg-indigo-600 text-sm font-bold text-white">
          IT
        </span>
        <span className="text-lg font-semibold text-white">Issue Tracker</span>
      </div>

      <nav className="flex-1 space-y-1 px-3 py-4">
        {navItems.map(({ to, label, icon: Icon, end }) => (
          <NavLink
            key={to}
            to={to}
            end={end}
            onClick={onNavigate}
            className={({ isActive }) =>
              `flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition ${
                isActive
                  ? 'bg-slate-800 text-white'
                  : 'text-slate-300 hover:bg-slate-800 hover:text-white'
              }`
            }
          >
            <Icon className="h-5 w-5" />
            {label}
          </NavLink>
        ))}
      </nav>

      <div className="border-t border-slate-800 px-6 py-4">
        <p className="text-xs text-slate-500">Full-stack development test</p>
        <p className="text-xs text-slate-500">React · FastAPI · SQLite</p>
      </div>
    </div>
  );
}

export default function Sidebar({ isOpen, onClose }: SidebarProps) {
  return (
    <>
      {/* Desktop sidebar */}
      <aside className="fixed inset-y-0 left-0 z-30 hidden w-64 bg-slate-900 lg:block">
        <SidebarContent />
      </aside>

      {/* Mobile drawer */}
      {isOpen && (
        <div className="fixed inset-0 z-40 lg:hidden" role="dialog" aria-modal="true">
          <div
            className="absolute inset-0 bg-slate-900/60"
            aria-hidden="true"
            onClick={onClose}
          />
          <div className="absolute inset-y-0 left-0 flex w-64 flex-col bg-slate-900">
            <button
              type="button"
              onClick={onClose}
              className="absolute right-2 top-2 rounded-md p-2 text-slate-400 hover:bg-slate-800 hover:text-white"
              aria-label="Close sidebar"
            >
              <CloseIcon />
            </button>
            <SidebarContent onNavigate={onClose} />
          </div>
        </div>
      )}
    </>
  );
}
