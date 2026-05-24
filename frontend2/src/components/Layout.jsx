import { useState } from 'react';
import { Outlet } from 'react-router-dom';
import Sidebar from './Sidebar';
import Player from './Player';
import { Menu } from 'lucide-react';

export default function Layout() {
  const [sidebarOpen, setSidebarOpen] = useState(false);

  return (
    <>
      <style>{`
        .mobile-header { position:sticky; top:0; z-index:50; background:var(--bg-secondary); border-bottom:1px solid var(--border-default); padding:12px 16px; display:flex; align-items:center; gap:12px; }
      `}</style>
      <div className="app-layout">
        <Sidebar isOpen={sidebarOpen} onClose={() => setSidebarOpen(false)} />
        <div className={`sidebar-overlay${sidebarOpen ? ' open' : ''}`} onClick={() => setSidebarOpen(false)} />
        <div className="app-main">
          <div className="mobile-header hamburger-btn" style={{ cursor: 'default' }}>
            <button className="btn btn-icon btn-ghost hamburger-btn"
              onClick={() => setSidebarOpen(true)} style={{ display: 'flex' }}>
              <Menu size={20} />
            </button>
            <span style={{ fontSize: '1.2rem' }}>🎵</span>
            <span className="gradient-text" style={{ fontWeight: 700, fontSize: '1.1rem' }}>Sun Leo</span>
          </div>
          <Outlet />
        </div>
        <Player />
      </div>
    </>
  );
}
