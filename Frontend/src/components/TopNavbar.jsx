import React from 'react';
import { MdSearch, MdDarkMode, MdLightMode, MdSecurity } from 'react-icons/md';
import { useTheme } from '../contexts/ThemeContext';

const TopNavbar = ({ toggleSidebar }) => {
  const { theme, setTheme } = useTheme();

  return (
    <div className="top-navbar">
      {/* Left: Logo */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
        <div style={{
          width: 30, height: 30, borderRadius: 8,
          background: 'var(--primary-gradient)',
          display: 'flex', alignItems: 'center', justifyContent: 'center'
        }}>
          <MdSecurity size={17} color="white" />
        </div>
        <div>
          <div style={{ fontSize: 13, fontWeight: 700, color: 'var(--text-primary)', letterSpacing: '-0.2px', lineHeight: 1.2 }}>
            Supply Chain AI
          </div>
          <div style={{ fontSize: 10, color: 'var(--text-secondary)', fontWeight: 500 }}>
            Risk Management Platform
          </div>
        </div>
      </div>

      {/* Center: Search */}
      <div className="search-input-wrapper" style={{ width: '320px' }}>
        <MdSearch size={16} style={{ color: 'var(--text-secondary)', flexShrink: 0 }} />
        <input
          type="text"
          placeholder="Search suppliers, risks, scenarios…"
          style={{ fontSize: 13 }}
        />
      </div>

      {/* Right: Theme Toggle */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
        <button
          onClick={() => setTheme(theme === 'dark' ? 'light' : 'dark')}
          title={theme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'}
          style={{
            width: 34, height: 34, border: '1px solid var(--border-color)',
            borderRadius: 8, background: 'var(--bg-secondary)',
            color: 'var(--text-secondary)', cursor: 'pointer',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            transition: 'color 0.15s ease, border-color 0.15s ease'
          }}
        >
          {theme === 'dark' ? <MdLightMode size={17} /> : <MdDarkMode size={17} />}
        </button>
      </div>
    </div>
  );
};

export default TopNavbar;
