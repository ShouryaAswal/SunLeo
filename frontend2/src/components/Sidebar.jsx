import { NavLink } from 'react-router-dom';
import { Home, Search, Bot, ListMusic, Download, Sliders, MessageSquare, LogIn, LogOut } from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';

const links = [
  { to: '/', icon: Home, label: 'Home' },
  { to: '/discover', icon: Search, label: 'Discovery' },
  { to: '/chat', icon: Bot, label: 'DJ Chat' },
  { to: '/playlists', icon: ListMusic, label: 'Playlists' },
  { to: '/downloads', icon: Download, label: 'Downloads' },
  { to: '/editor', icon: Sliders, label: 'Audio Editor' },
  { to: '/feedback', icon: MessageSquare, label: 'Feedback' },
];

export default function Sidebar({ isOpen, onClose }) {
  const { user, loginWithGoogle, logout } = useAuth();

  return (
    <>
      <style>{`
        .sidebar-brand { padding: 1.2rem 1.2rem 1.5rem; display: flex; align-items: center; gap: 10px; }
        .sidebar-brand span { font-size: 1.3rem; font-weight: 700; }
        .sidebar-nav { display: flex; flex-direction: column; gap: 2px; padding: 0 8px; flex: 1; }
        .sidebar-link { display: flex; align-items: center; gap: 12px; padding: 10px 16px; border-radius: 8px; color: var(--text-secondary); transition: all 0.2s; font-size: 0.9rem; text-decoration: none; }
        .sidebar-link:hover { background: var(--bg-surface-hover); color: var(--text-primary); }
        .sidebar-link.active { background: var(--accent-violet-dim); color: var(--accent-violet-light); font-weight: 600; }
        .sidebar-bottom { padding: 12px; border-top: 1px solid var(--border-default); margin-top: auto; }
        .sidebar-user { display: flex; align-items: center; gap: 10px; }
        .sidebar-user-name { font-size: 0.85rem; color: var(--text-secondary); flex: 1; min-width: 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
        .sidebar-logout { background: none; border: none; color: var(--text-dim); cursor: pointer; padding: 4px; border-radius: 4px; transition: color 0.2s; display:flex; }
        .sidebar-logout:hover { color: var(--color-danger); }
      `}</style>
      <div className={`app-sidebar${isOpen ? ' open' : ''}`}>
        <div className="sidebar-brand">
          <span style={{ fontSize: '1.5rem' }}>🎵</span>
          <span className="gradient-text">Sun Leo</span>
        </div>
        <nav className="sidebar-nav">
          {links.map(({ to, icon: Icon, label }) => (
            <NavLink key={to} to={to} end={to === '/'}
              className={({ isActive }) => `sidebar-link${isActive ? ' active' : ''}`}
              onClick={onClose}>
              <Icon size={18} /> {label}
            </NavLink>
          ))}
        </nav>
        <div className="sidebar-bottom">
          {user ? (
            <div className="sidebar-user">
              <div className="user-avatar">{user.displayName?.[0]?.toUpperCase() || '?'}</div>
              <span className="sidebar-user-name">{user.displayName || user.email}</span>
              <button className="sidebar-logout" onClick={logout} title="Sign out"><LogOut size={16} /></button>
            </div>
          ) : (
            <button className="btn btn-primary btn-full btn-sm" onClick={loginWithGoogle}>
              <LogIn size={16} /> Sign In
            </button>
          )}
        </div>
      </div>
    </>
  );
}
