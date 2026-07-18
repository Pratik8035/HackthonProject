import React from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';

const SupplierDetails = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const supplier = location.state?.supplier;

  if (!supplier) {
    return (
      <div className="py-5 text-center">
        <h3 className="text-muted mb-4">Supplier Not Found</h3>
        <button className="btn btn-primary" onClick={() => navigate('/alternative-supplier')}>Go Back</button>
      </div>
    );
  }

  return (
    <div className="py-4">
      <button className="btn btn-link text-decoration-none mb-4 ps-0" style={{ color: 'var(--text-color)' }} onClick={() => navigate(-1)}>
        &larr; Back to Recommendations
      </button>
      
      <h2 className="fw-bold gradient-text mb-4">Supplier Details</h2>
      
      <motion.div className="glass-card" initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}>
        <div className="row g-4">
          <div className="col-md-6">
            <h4 className="fw-bold mb-4">{supplier.Supplier}</h4>
            <table className="table table-borderless" style={{ color: 'var(--text-color)' }}>
              <tbody>
                <tr><td className="text-muted w-50">Ranking</td><td className="fw-bold text-success">#{supplier.Rank}</td></tr>
                <tr><td className="text-muted">Country</td><td className="fw-medium">{supplier.Country}</td></tr>
                <tr><td className="text-muted">Reliability</td><td className="fw-medium">{(supplier.Reliability * 100).toFixed(0)}%</td></tr>
                <tr><td className="text-muted">Lead Time</td><td className="fw-medium">{supplier['Lead Time']} Days</td></tr>
                <tr><td className="text-muted">Capacity</td><td className="fw-medium">{supplier.Capacity} Units</td></tr>
                <tr><td className="text-muted">Price</td><td className="fw-medium">${supplier.Price}</td></tr>
                <tr className="border-top border-secondary border-opacity-25">
                  <td className="pt-3 text-muted">Final Ranking Score</td>
                  <td className="pt-3 fw-bold gradient-text">{supplier['Final Ranking Score'].toFixed(2)}</td>
                </tr>
              </tbody>
            </table>
          </div>
          
          <div className="col-md-6 border-start border-secondary border-opacity-25 ps-md-4">
            <h5 className="fw-bold mb-3">Recommendation Context</h5>
            <div className="alert alert-info border-0 mb-4">
              <strong>Why this supplier?</strong><br/>
              Highly rated for reliability and capacity, compensating for the projected supply shortage in the active risk scenario.
            </div>
            
            <h5 className="fw-bold mb-3">Risk Assessment</h5>
            <div className="d-flex align-items-center mb-2">
              <span className="me-3 text-muted" style={{ width: '100px' }}>Geopolitical</span>
              <div className="progress flex-grow-1" style={{ height: '8px' }}>
                <div className="progress-bar bg-success" style={{ width: '85%' }}></div>
              </div>
            </div>
            <div className="d-flex align-items-center mb-2">
              <span className="me-3 text-muted" style={{ width: '100px' }}>Financial</span>
              <div className="progress flex-grow-1" style={{ height: '8px' }}>
                <div className="progress-bar bg-success" style={{ width: '92%' }}></div>
              </div>
            </div>
            <div className="d-flex align-items-center mb-4">
              <span className="me-3 text-muted" style={{ width: '100px' }}>Operational</span>
              <div className="progress flex-grow-1" style={{ height: '8px' }}>
                <div className="progress-bar bg-warning" style={{ width: '70%' }}></div>
              </div>
            </div>
            
            <button className="btn btn-primary w-100 py-2 fw-bold" onClick={() => navigate('/strategic-reserve')}>
              Select & Proceed to Reserve Optimization
            </button>
          </div>
        </div>
      </motion.div>
    </div>
  );
};

export default SupplierDetails;
