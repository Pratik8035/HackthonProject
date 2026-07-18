import React from 'react';
import { motion } from 'framer-motion';
import { MdErrorOutline, MdRefresh } from 'react-icons/md';

const ErrorCard = ({ error, onRetry }) => {
  return (
    <div className="d-flex justify-content-center align-items-center w-100 py-5">
      <motion.div 
        className="glass-card border border-danger border-opacity-50 text-center p-5"
        initial={{ opacity: 0, scale: 0.9 }}
        animate={{ opacity: 1, scale: 1 }}
        style={{ maxWidth: '500px', backgroundColor: 'rgba(238, 93, 80, 0.05)' }}
      >
        <div className="p-4 rounded-circle bg-danger bg-opacity-10 text-danger mb-4 d-inline-block">
          <MdErrorOutline size={48} />
        </div>
        <h4 className="fw-bold text-danger mb-3">Analysis Error</h4>
        <p className="text-muted-custom mb-4">
          {error?.message || typeof error === 'string' ? error : "An unexpected error occurred while communicating with the AI backend."}
        </p>
        
        {onRetry && (
          <button className="btn btn-outline-danger rounded-pill px-4 py-2 fw-bold d-flex align-items-center justify-content-center gap-2 mx-auto" onClick={onRetry}>
            <MdRefresh size={20} /> Retry Request
          </button>
        )}
      </motion.div>
    </div>
  );
};

export default ErrorCard;
