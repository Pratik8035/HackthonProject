import React, { useState } from 'react';
import { motion } from 'framer-motion';

const HistoryPage = () => {
  const [searchTerm, setSearchTerm] = useState('');
  
  // Dummy history data
  const historyData = [
    { id: 'AN-2026-07-01', date: '2026-07-01', supplier: 'TechCorp Asia', decision: 'Replaced', status: 'Completed' },
    { id: 'AN-2026-06-28', date: '2026-06-28', supplier: 'Global Logistics Inc', decision: 'Retained', status: 'Completed' },
    { id: 'AN-2026-06-15', date: '2026-06-15', supplier: 'EuroSemiconductors', decision: 'Replaced', status: 'Completed' },
  ];

  const filtered = historyData.filter(h => h.supplier.toLowerCase().includes(searchTerm.toLowerCase()) || h.id.includes(searchTerm));

  return (
    <div className="py-4">
      <h2 className="fw-bold gradient-text mb-4">Analysis History</h2>
      
      <div className="glass-card mb-4 d-flex justify-content-between align-items-center flex-wrap gap-3">
        <input 
          type="text" 
          className="form-control bg-transparent text-white border-secondary border-opacity-25" 
          placeholder="Search by ID or Supplier..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          style={{ width: '300px', color: 'var(--text-color)' }}
        />
        <div className="d-flex gap-2">
          <button className="btn btn-outline-secondary">Filter</button>
          <button className="btn btn-outline-secondary">Sort</button>
        </div>
      </div>

      <div className="glass-card p-0 overflow-auto">
        <table className="table table-hover table-borderless mb-0" style={{ color: 'var(--text-color)' }}>
          <thead style={{ backgroundColor: 'var(--card-bg)' }}>
            <tr>
              <th className="py-3 px-4">Analysis ID</th>
              <th className="py-3">Date</th>
              <th className="py-3">Current Supplier</th>
              <th className="py-3">Decision</th>
              <th className="py-3">Status</th>
              <th className="py-3 text-end px-4">Action</th>
            </tr>
          </thead>
          <tbody>
            {filtered.map((item, idx) => (
              <motion.tr 
                key={idx}
                initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: idx * 0.05 }}
                style={{ borderBottom: '1px solid var(--card-border)' }}
              >
                <td className="py-3 px-4 fw-medium text-primary">{item.id}</td>
                <td className="py-3">{item.date}</td>
                <td className="py-3">{item.supplier}</td>
                <td className="py-3">
                  <span className={`badge ${item.decision === 'Replaced' ? 'bg-warning text-dark' : 'bg-success'}`}>{item.decision}</span>
                </td>
                <td className="py-3"><span className="badge bg-secondary">{item.status}</span></td>
                <td className="py-3 text-end px-4">
                  <button className="btn btn-sm btn-outline-primary rounded-pill px-3">View Report</button>
                </td>
              </motion.tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default HistoryPage;
