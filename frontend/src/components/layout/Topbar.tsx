import Button from '../ui/Button';
import { LogoutIcon, MenuIcon } from '../ui/icons';
import { useAuth } from '../../context/AuthContext';
import { useToast } from '../../context/ToastContext';

interface TopbarProps {
  onMenuClick: () => void;
}

export default function Topbar({ onMenuClick }: TopbarProps) {
  const { user, logout } = useAuth();
  const { showToast } = useToast();

  function handleLogout() {
    logout();
    showToast('You have been signed out.', 'info');
  }

  return (
    <header className="sticky top-0 z-20 flex h-16 items-center justify-between border-b border-slate-200 bg-white px-4 sm:px-6">
      <div className="flex items-center gap-3">
        <button
          type="button"
          onClick={onMenuClick}
          className="rounded-md p-2 text-slate-500 hover:bg-slate-100 hover:text-slate-700 lg:hidden"
          aria-label="Open sidebar"
        >
          <MenuIcon />
        </button>
        <span className="text-sm font-medium text-slate-500">
          Welcome back{user ? `, ${user.name}` : ''}
        </span>
      </div>

      <div className="flex items-center gap-3">
        {user && (
          <div className="hidden text-right sm:block">
            <p className="text-sm font-semibold text-slate-900">{user.name}</p>
            <p className="text-xs text-slate-500">{user.email}</p>
          </div>
        )}
        <span className="flex h-9 w-9 items-center justify-center rounded-full bg-indigo-100 text-sm font-semibold text-indigo-700">
          {user?.name?.charAt(0).toUpperCase() ?? '?'}
        </span>
        <Button variant="ghost" size="sm" onClick={handleLogout} aria-label="Log out">
          <LogoutIcon className="h-5 w-5" />
          <span className="hidden sm:inline">Log out</span>
        </Button>
      </div>
    </header>
  );
}
