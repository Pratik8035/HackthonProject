import React from 'react';
import { motion } from 'framer-motion';

const KPICard = ({ title, value, icon, color }) => {
  return (
    <motion.div 
      className="glass-card d-flex flex-column h-100 p-4"
      whileHover={{ y: -5, boxShadow: '0 10px 40px rgba(0,0,0,0.1)' }}
      transition={{ type: 'spring', stiffness: 300, damping: 20 }}
    >
      <div className="d-flex justify-content-between align-items-start mb-3">
        <div className={`p-3 rounded bg-${color} bg-opacity-10 text-${color}`}>
          {icon}
        </div>
      </div>
      <h6 className="text-muted-custom fw-semibold mb-2">{title}</h6>
      <h2 className={`fw-bold m-0 text-${color}`}>{value}</h2>
    </motion.div>
  );
};

export default KPICard;
