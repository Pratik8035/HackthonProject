import React, { useState } from 'react';
import Sidebar from '../components/Sidebar';
import TopNavbar from '../components/TopNavbar';

const MainLayout = ({ children }) => {
  const [collapsed, setCollapsed] = useState(false);

  return (
    <div className="app-container">
      <Sidebar collapsed={collapsed} onToggle={() => setCollapsed(c => !c)} />
      <div className={`main-content ${collapsed ? 'collapsed' : ''}`}>
        <TopNavbar toggleSidebar={() => setCollapsed(c => !c)} />
        <div>
          {children}
        </div>
      </div>
    </div>
  );
};

export default MainLayout;
