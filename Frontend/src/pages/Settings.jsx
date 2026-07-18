import React from 'react';
import { useTheme } from '../contexts/ThemeContext';
import { MdColorLens, MdApi, MdNotifications, MdLanguage, MdSave } from 'react-icons/md';
import { motion } from 'framer-motion';

const Settings = () => {
  const { theme, setTheme } = useTheme();

  return (
    <div className="page-container py-4">
      <div className="mb-4">
        <h2 className="fw-bold gradient-text m-0">Platform Settings</h2>
        <p className="text-muted-custom mt-1">Configure your AI dashboard preferences and global settings.</p>
      </div>
      
      <div className="row g-4 mb-5">
        <div className="col-lg-6">
          <motion.div className="glass-card h-100" whileHover={{ y: -5 }}>
            <h5 className="fw-bold mb-4 d-flex align-items-center gap-2">
              <MdColorLens className="text-primary" /> Appearance
            </h5>
            <div className="p-4 rounded glass-panel">
              <label className="form-label text-muted-custom fw-semibold mb-3">Theme Preference</label>
              <div className="d-flex gap-3">
                <button 
                  className={`btn flex-grow-1 py-2 ${theme === 'light' ? 'btn-primary' : 'btn-outline-secondary text-muted-custom'}`}
                  onClick={() => setTheme('light')}
                >
                  Light Mode
                </button>
                <button 
                  className={`btn flex-grow-1 py-2 ${theme === 'dark' ? 'btn-primary' : 'btn-outline-secondary text-muted-custom'}`}
                  onClick={() => setTheme('dark')}
                >
                  Dark Mode
                </button>
              </div>
            </div>
          </motion.div>
        </div>

        <div className="col-lg-6">
          <motion.div className="glass-card h-100" whileHover={{ y: -5 }}>
            <h5 className="fw-bold mb-4 d-flex align-items-center gap-2">
              <MdApi className="text-info" /> Backend Configuration
            </h5>
            <div className="p-4 rounded glass-panel">
              <label className="form-label text-muted-custom fw-semibold mb-2">API Base URL</label>
              <input 
                type="text" 
                className="form-control bg-transparent border-secondary border-opacity-25 text-primary fw-bold"
                defaultValue={import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8080'} 
              />
              <p className="text-muted-custom small mt-2 m-0">Restart application required for changes to take effect.</p>
            </div>
          </motion.div>
        </div>

        <div className="col-lg-12">
          <motion.div className="glass-card" whileHover={{ y: -2 }}>
            <h5 className="fw-bold mb-4 d-flex align-items-center gap-2">
              <MdNotifications className="text-warning" /> General Preferences
            </h5>
            
            <div className="row g-4">
              <div className="col-md-6">
                <div className="p-4 rounded glass-panel h-100">
                  <div className="d-flex align-items-center gap-2 mb-3">
                    <MdLanguage className="text-muted-custom" />
                    <label className="form-label text-muted-custom fw-semibold m-0">Interface Language</label>
                  </div>
                  <select 
                    className="form-select bg-transparent border-secondary border-opacity-25 text-primary fw-bold"
                  >
                    <option value="en" style={{ color: '#000' }}>English (United States)</option>
                    <option value="es" style={{ color: '#000' }}>Spanish</option>
                    <option value="fr" style={{ color: '#000' }}>French</option>
                  </select>
                </div>
              </div>

              <div className="col-md-6">
                <div className="p-4 rounded glass-panel h-100 d-flex flex-column justify-content-center gap-3">
                  <div className="form-check form-switch d-flex align-items-center justify-content-between p-0">
                    <label className="form-check-label text-primary fw-bold m-0" htmlFor="emailNotif">Email Alerts</label>
                    <input className="form-check-input ms-auto fs-5 m-0" type="checkbox" id="emailNotif" defaultChecked />
                  </div>
                  <div className="form-check form-switch d-flex align-items-center justify-content-between p-0">
                    <label className="form-check-label text-primary fw-bold m-0" htmlFor="pushNotif">Desktop Push Notifications</label>
                    <input className="form-check-input ms-auto fs-5 m-0" type="checkbox" id="pushNotif" defaultChecked />
                  </div>
                </div>
              </div>
            </div>
          </motion.div>
        </div>
      </div>
      
      <div className="d-flex justify-content-end mb-5">
        <button className="btn btn-primary-gradient rounded-pill px-5 py-3 fw-bold d-flex align-items-center gap-2 shadow-lg" onClick={() => alert('Settings Saved!')}>
          <MdSave size={20} /> Save Configuration
        </button>
      </div>
    </div>
  );
};

export default Settings;
