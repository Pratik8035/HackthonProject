import React from 'react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { useAnalysis } from '../contexts/AnalysisContext';
import { MdPictureAsPdf, MdTableChart, MdPrint } from 'react-icons/md';

const FinalReport = () => {
  const { analysisResult } = useAnalysis();
  const navigate = useNavigate();

  if (!analysisResult) {
    return (
      <div className="py-5 text-center">
        <h3 className="text-muted mb-4">No Analysis Result Found</h3>
        <button className="btn btn-primary mt-3" onClick={() => navigate('/alternative-supplier')}>
          Start New Analysis
        </button>
      </div>
    );
  }

  // Handle case where it might be structured slightly differently depending on the backend version
  const { 
    Orchestration_Status,
    Risk_Phase,
    Simulation_Phase,
    Supplier_Phase,
    SPR_Phase,
    Final_Recommendation
  } = analysisResult;

  const handlePrint = () => window.print();

  return (
    <div className="py-4 print-container">
      <div className="d-flex justify-content-between align-items-center mb-4 flex-wrap gap-3">
        <h2 className="fw-bold gradient-text m-0">Final Supply Chain Report</h2>
        <div className="d-flex gap-2">
          <button className="btn btn-outline-danger d-flex align-items-center gap-2" onClick={() => alert("Exporting PDF...")}>
            <MdPictureAsPdf /> Export PDF
          </button>
          <button className="btn btn-outline-success d-flex align-items-center gap-2" onClick={() => alert("Exporting Excel...")}>
            <MdTableChart /> Export Excel
          </button>
          <button className="btn btn-primary d-flex align-items-center gap-2" onClick={handlePrint}>
            <MdPrint /> Print Report
          </button>
        </div>
      </div>

      <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}>
        <div className="row g-4">
          <div className="col-12">
            <div className="glass-card border-primary">
              <h5 className="fw-bold text-primary mb-3">Overall Recommendation</h5>
              <h4 className="fw-bold mb-0">{Final_Recommendation || Supplier_Phase?.['Final Recommendation'] || "Proceed with selected strategy."}</h4>
            </div>
          </div>

          <div className="col-md-6">
            <div className="glass-card h-100">
              <h5 className="fw-bold border-bottom border-secondary border-opacity-25 pb-2 mb-3">Risk & Scenario Summary</h5>
              <div className="mb-3">
                <p className="text-muted mb-1 small">Active High Risk Scenario</p>
                <p className="fw-medium mb-0">{Simulation_Phase?.['Scenario Name'] || 'None Detected'}</p>
              </div>
              <div className="mb-3">
                <p className="text-muted mb-1 small">Probability</p>
                <p className="fw-medium mb-0">{Simulation_Phase ? (Simulation_Phase.Probability * 100).toFixed(1) + '%' : 'N/A'}</p>
              </div>
              <div className="mb-3">
                <p className="text-muted mb-1 small">Projected Supply Shortage</p>
                <p className="fw-medium text-danger mb-0">{Simulation_Phase?.['Supply Shortage']?.toFixed(1) || 0} Units</p>
              </div>
              <div>
                <p className="text-muted mb-1 small">Recovery Time</p>
                <p className="fw-medium mb-0">{Simulation_Phase?.['Recovery Time']?.toFixed(1) || 0} Days</p>
              </div>
            </div>
          </div>

          <div className="col-md-6">
            <div className="glass-card h-100">
              <h5 className="fw-bold border-bottom border-secondary border-opacity-25 pb-2 mb-3">Supplier Intelligence</h5>
              <div className="mb-3">
                <p className="text-muted mb-1 small">Current Supplier Status</p>
                <p className="fw-medium text-danger mb-0">High Risk - Replacement Advised</p>
              </div>
              <div className="mb-3">
                <p className="text-muted mb-1 small">Recommended Alternative</p>
                <p className="fw-medium text-success mb-0">{Supplier_Phase?.['Selected Supplier'] || 'N/A'}</p>
              </div>
              <div className="mb-3">
                <p className="text-muted mb-1 small">Best Route</p>
                <p className="fw-medium mb-0">{Supplier_Phase?.['Best Route'] || 'N/A'}</p>
              </div>
              <div className="row g-2">
                <div className="col-6">
                  <p className="text-muted mb-1 small">Distance</p>
                  <p className="fw-medium mb-0">{Supplier_Phase?.['Shortest Distance'] || 'N/A'}</p>
                </div>
                <div className="col-6">
                  <p className="text-muted mb-1 small">Predicted Delay</p>
                  <p className="fw-medium text-warning mb-0">{Supplier_Phase?.['Predicted Delay']?.toFixed(1) || 0} Days</p>
                </div>
              </div>
            </div>
          </div>

          <div className="col-md-6">
            <div className="glass-card h-100">
              <h5 className="fw-bold border-bottom border-secondary border-opacity-25 pb-2 mb-3">Cost Analysis (Predicted)</h5>
              <table className="table table-borderless table-sm mb-0" style={{ color: 'var(--text-color)' }}>
                <tbody>
                  <tr>
                    <td className="text-muted">Transportation Cost</td>
                    <td className="text-end fw-medium">${Supplier_Phase?.['Transportation Cost']?.toLocaleString() || 0}</td>
                  </tr>
                  <tr>
                    <td className="text-muted">Fuel Cost</td>
                    <td className="text-end fw-medium">${Supplier_Phase?.['Fuel Cost']?.toLocaleString() || 0}</td>
                  </tr>
                  <tr>
                    <td className="text-muted">Insurance Cost</td>
                    <td className="text-end fw-medium">${Supplier_Phase?.['Insurance Cost']?.toLocaleString() || 0}</td>
                  </tr>
                  <tr>
                    <td className="text-muted">Logistics Cost</td>
                    <td className="text-end fw-medium">${Supplier_Phase?.['Logistics Cost']?.toLocaleString() || 0}</td>
                  </tr>
                  <tr className="border-top border-secondary border-opacity-25">
                    <td className="fw-bold pt-2">Total Predicted Cost</td>
                    <td className="text-end fw-bold gradient-text pt-2 fs-5">
                      ${Supplier_Phase?.['Predicted Total Cost']?.toLocaleString() || 0}
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>

          <div className="col-md-6">
            <div className="glass-card h-100">
              <h5 className="fw-bold border-bottom border-secondary border-opacity-25 pb-2 mb-3">Strategic Reserve Strategy</h5>
              {SPR_Phase ? (
                <>
                  <div className="alert alert-info border-0 mb-3 py-2">
                    {SPR_Phase.Recommendation}
                  </div>
                  <div className="row text-center mt-4">
                    <div className="col-6">
                      <p className="text-muted small mb-1">Release Volume</p>
                      <h4 className="fw-bold">{SPR_Phase['Recommended Release Volume']?.toLocaleString()}</h4>
                    </div>
                    <div className="col-6">
                      <p className="text-muted small mb-1">Est. Cost Savings</p>
                      <h4 className="fw-bold text-success">${SPR_Phase['Estimated Cost Savings']?.toLocaleString()}</h4>
                    </div>
                  </div>
                </>
              ) : (
                <p className="text-muted py-4 text-center">No reserve optimization data available for this analysis.</p>
              )}
            </div>
          </div>
        </div>
      </motion.div>
    </div>
  );
};

export default FinalReport;
