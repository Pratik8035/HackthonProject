import React, { useState } from 'react';
import { NavLink } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import {
  MdDashboard, MdPublic, MdWarning, MdCompareArrows,
  MdMap, MdTimer, MdAttachMoney, MdInventory, MdAssessment,
  MdDescription, MdChevronLeft, MdMenu, MdSecurity
} from 'react-icons/md';

const menuItems = [
  { path: '/',                    label: 'Dashboard',               icon: MdDashboard },
  { path: '/live-risk',           label: 'Live Risk Intelligence',   icon: MdPublic },
  { path: '/scenario-impact',     label: 'Scenario Impact',         icon: MdWarning },
  { path: '/alternative-supplier',label: 'Alternative Supplier',    icon: MdCompareArrows },
  { path: '/route-optimization',  label: 'Route Optimization',      icon: MdMap },
  { path: '/delay-prediction',    label: 'Delay Prediction',        icon: MdTimer },
  { path: '/cost-prediction',     label: 'Cost Prediction',         icon: MdAttachMoney },
  { path: '/strategic-reserve',   label: 'Strategic Reserve',       icon: MdInventory },
  { path: '/integrated-analysis', label: 'Integrated Analysis',     icon: MdAssessment },
  { path: '/reports',             label: 'Reports',                 icon: MdDescription },
];

const Sidebar = ({ collapsed, onToggle }) => {
  return (
    <div
      className={`sidebar ${collapsed ? 'collapsed' : ''}`}
      style={{ display: 'flex', flexDirection: 'column' }}
    >
      {/* Logo + Toggle */}
      <div
        style={{
          height: 'var(--navbar-height)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: collapsed ? 'center' : 'space-between',
          padding: collapsed ? '0 16px' : '0 14px 0 16px',
          borderBottom: '1px solid var(--border-color)',
          flexShrink: 0,
        }}
      >
        {!collapsed && (
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <div style={{
              width: 28, height: 28, borderRadius: 7,
              background: 'var(--primary-gradient)',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              flexShrink: 0
            }}>
              <MdSecurity size={16} color="white" />
            </div>
            <span style={{ fontSize: 13, fontWeight: 700, color: 'var(--text-primary)', letterSpacing: '-0.2px' }}>
              Supply Chain AI
            </span>
          </div>
        )}
        <button
          onClick={onToggle}
          style={{
            background: 'none', border: 'none', cursor: 'pointer',
            color: 'var(--text-secondary)', display: 'flex',
            alignItems: 'center', justifyContent: 'center',
            padding: 4, borderRadius: 6,
            transition: 'color 0.15s ease'
          }}
          title={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
        >
          {collapsed ? <MdMenu size={20} /> : <MdChevronLeft size={20} />}
        </button>
      </div>

      {/* Nav Links */}
      <nav
        style={{ flex: 1, overflowY: 'auto', overflowX: 'hidden', padding: '8px 0' }}
        className="custom-scrollbar"
      >
        {!collapsed && (
          <div style={{
            padding: '6px 20px 4px',
            fontSize: 10, fontWeight: 600,
            color: 'var(--text-secondary)',
            textTransform: 'uppercase',
            letterSpacing: '0.6px'
          }}>
            Navigation
          </div>
        )}
        {menuItems.map((item) => {
          const Icon = item.icon;
          return (
            <NavLink
              key={item.path}
              to={item.path}
              end={item.path === '/'}
              className={({ isActive }) =>
                `sidebar-nav-item ${isActive ? 'active' : ''}`
              }
              title={collapsed ? item.label : ''}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: collapsed ? 0 : 10,
                justifyContent: collapsed ? 'center' : 'flex-start',
                overflow: 'hidden',
              }}
            >
              <span className="nav-icon">
                <Icon size={18} />
              </span>
              {!collapsed && (
                <span className="sidebar-label" style={{ fontSize: 13, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                  {item.label}
                </span>
              )}
            </NavLink>
          );
        })}
      </nav>

      {/* Footer */}
      {!collapsed && (
        <div style={{
          padding: '12px 16px',
          borderTop: '1px solid var(--border-color)',
          fontSize: 11,
          color: 'var(--text-secondary)',
          flexShrink: 0
        }}>
          <div style={{ fontWeight: 600 }}>AI Platform v2.0</div>
          <div style={{ opacity: 0.7 }}>Risk & Resilience Engine</div>
        </div>
      )}
    </div>
  );
};

export default Sidebar;
