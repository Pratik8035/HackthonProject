import React from 'react';
import { motion } from 'framer-motion';

const Loader = ({ message = "Loading AI Insights..." }) => {
  return (
    <div className="d-flex flex-column justify-content-center align-items-center h-100 py-5">
      <motion.div 
        animate={{ rotate: 360 }}
        transition={{ repeat: Infinity, duration: 2, ease: "linear" }}
        className="mb-4"
        style={{
          width: '60px',
          height: '60px',
          borderRadius: '50%',
          border: '4px solid rgba(67, 24, 255, 0.2)',
          borderTopColor: 'var(--primary-color)',
        }}
      />
      <motion.h5 
        initial={{ opacity: 0.5 }}
        animate={{ opacity: 1 }}
        transition={{ repeat: Infinity, duration: 1, repeatType: 'reverse' }}
        className="fw-bold text-primary gradient-text"
      >
        {message}
      </motion.h5>
    </div>
  );
};

export default Loader;
