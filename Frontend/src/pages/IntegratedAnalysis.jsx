import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { supplierApi } from '../services/supplierApi';
import { analysisApi } from '../services/analysisApi';
import { useAnalysis } from '../contexts/AnalysisContext';
import Loader from '../components/Loader';
import ErrorCard from '../components/ErrorCard';
import { 
  MdCheckCircle, MdChevronRight, MdSettingsSuggest, MdAssignment, 
  MdWarning, MdCompareArrows, MdMap, MdTimer, MdAttachMoney, MdInventory, MdDoneAll,
  MdOutlineAssessment
} from 'react-icons/md';

const IntegratedAnalysis = () => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [currentSuppliers, setCurrentSuppliers] = useState([]);
  const [selectedCurrent, setSelectedCurrent] = useState('');
  
  const [step, setStep] = useState(0);
  const [orchestrationData, setOrchestrationData] = useState(null);
  const [selectedAlternative, setSelectedAlt] = useState('');
  
  const { setAnalysisResult } = useAnalysis();
  const navigate = useNavigate();

  const workflowSteps = [
    { id: 0, name: 'Select Supplier', icon: <MdAssignment /> },
    { id: 1, name: 'Risk & Scenario', icon: <MdWarning /> },
    { id: 2, name: 'Alternatives', icon: <MdCompareArrows /> },
    { id: 3, name: 'Logistics Predict', icon: <MdMap /> },
    { id: 4, name: 'Strategic Reserve', icon: <MdInventory /> },
    { id: 5, name: 'Final Decision', icon: <MdDoneAll /> }
  ];

  const fetchSuppliers = async () => {
    try {
      setLoading(true);
      setError(null);
      const res = await supplierApi.getCurrentSuppliers();
      setCurrentSuppliers(res.data || []);
    } catch (err) {
      setError(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSuppliers();
  }, []);

  const handleRunInitial = async () => {
    if (!selectedCurrent) return;
    try {
      setLoading(true);
      setError(null);
      setStep(1); // Moving to Risk
      // Fake delay for UI
      await new Promise(r => setTimeout(r, 1500));
      const res = await supplierApi.recommendSupplier({ current_supplier_id: selectedCurrent });
      
      const recommendationData = res.data;
      setOrchestrationData({ recommendation: recommendationData });
      
      if (recommendationData?.Decision?.['Replacement Required'] === 'Yes') {
        setStep(2); // Automatically move to alternatives after risk check
      } else {
        // If replacement is not required, immediately proceed with the current supplier
        const currentSupplierName = recommendationData['Current Supplier'];
        setSelectedAlt(currentSupplierName);
        
        setStep(3);
        await new Promise(r => setTimeout(r, 1000)); // Simulating Logistics predict
        
        const orchRes = await analysisApi.orchestrate({
          current_supplier_id: selectedCurrent,
          selected_supplier: currentSupplierName,
          horizon_days: 7
        });
        const data = orchRes.data;
        
        setOrchestrationData(prev => ({ ...prev, final: data }));
        setAnalysisResult(data);
        
        setStep(4);
        await new Promise(r => setTimeout(r, 1000));
        setStep(5);
      }
    } catch (err) {
      setError(err);
      setStep(0);
    } finally {
      setLoading(false);
    }
  };

  const handleSelectAlternative = async (altSupplierName) => {
    setSelectedAlt(altSupplierName);
    try {
      setLoading(true);
      setError(null);
      setStep(3);
      await new Promise(r => setTimeout(r, 1000)); // Simulating Logistics predict
      
      const res = await analysisApi.orchestrate({
        current_supplier_id: selectedCurrent,
        selected_supplier: altSupplierName,
        horizon_days: 7
      });
      const data = res.data;
      
      setOrchestrationData(prev => ({ ...prev, final: data }));
      setAnalysisResult(data);
      
      setStep(4);
      await new Promise(r => setTimeout(r, 1000));
      setStep(5);
    } catch (err) {
      setError(err);
      setStep(2);
    } finally {
      setLoading(false);
    }
  };

  if (error) return <div className="page-container py-5"><ErrorCard error={error} onRetry={() => { setError(null); setStep(0); }} /></div>;

  return (
    <div className="page-container py-4">
      <div className="mb-5">
        <h2 className="fw-bold gradient-text m-0">Integrated Supply Chain Analysis</h2>
        <p className="text-muted-custom mt-1">End-to-end guided workflow for supplier risk mitigation.</p>
      </div>

      {/* Progress Tracker */}
      <div className="glass-card mb-5 p-4 position-relative overflow-hidden">
        <div className="d-flex justify-content-between position-relative z-index-1">
          {workflowSteps.map((s, i) => (
            <div key={i} className="d-flex flex-column align-items-center" style={{ width: '100px', zIndex: 2 }}>
              <motion.div 
                className={`rounded-circle d-flex justify-content-center align-items-center mb-2 shadow-sm ${step >= i ? 'bg-primary text-white' : 'bg-secondary bg-opacity-25 text-muted-custom'}`} 
                style={{ width: '48px', height: '48px', border: step === i ? '3px solid rgba(255,255,255,0.5)' : 'none' }}
                animate={{ scale: step === i ? 1.1 : 1 }}
              >
                {step > i ? <MdCheckCircle size={24} /> : s.icon}
              </motion.div>
              <span className={`small fw-bold text-center ${step >= i ? 'text-primary' : 'text-muted-custom'}`} style={{ fontSize: '11px', letterSpacing: '0.5px' }}>
                {s.name}
              </span>
            </div>
          ))}
        </div>
        <div className="position-absolute top-50 start-0 translate-middle-y w-100" style={{ padding: '0 50px', zIndex: 0, marginTop: '-12px' }}>
          <div className="progress" style={{ height: '4px', backgroundColor: 'var(--border-color)' }}>
            <motion.div 
              className="progress-bar bg-primary" 
              initial={{ width: '0%' }}
              animate={{ width: `${(step / (workflowSteps.length - 1)) * 100}%` }}
              transition={{ duration: 0.5 }}
            ></motion.div>
          </div>
        </div>
      </div>

      {loading && (
        <div className="glass-card py-5 d-flex flex-column align-items-center justify-content-center" style={{ minHeight: '400px' }}>
          <div className="spinner-border text-primary mb-4" role="status" style={{ width: '3rem', height: '3rem' }}></div>
          <h4 className="fw-bold gradient-text mb-2">
            {step === 1 ? 'Running Risk & Scenario Models...' : step === 3 ? 'Predicting Routes & Delays...' : 'Generating Final Decision...'}
          </h4>
          <p className="text-muted-custom">Please wait while the AI models process live data.</p>
        </div>
      )}

      {!loading && step === 0 && (
        <motion.div className="glass-card d-flex flex-column align-items-center p-5 text-center" initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}>
          <div className="p-4 rounded-circle bg-primary bg-opacity-10 text-primary mb-4">
            <MdSettingsSuggest size={48} />
          </div>
          <h4 className="fw-bold mb-3">Initiate Analysis Workflow</h4>
          <p className="text-muted-custom max-w-md mb-4">Select a current supplier from your network to run a complete risk assessment, scenario simulation, and alternative recommendation process.</p>
          
          <select 
            className="form-select glass-panel py-3 px-4 mb-4 fw-bold text-primary w-100"
            style={{ maxWidth: '400px', cursor: 'pointer' }}
            value={selectedCurrent}
            onChange={(e) => setSelectedCurrent(e.target.value)}
          >
            <option value="" style={{ color: '#000' }}>-- Choose Supplier to Analyze --</option>
            {currentSuppliers.map((s, idx) => (
              <option key={idx} value={s['supplier_id'] || s['id'] || s['Supplier']} style={{ color: '#000' }}>
                {s['supplier_name'] || s['Supplier']} ({s.country || s.Country})
              </option>
            ))}
          </select>
          
          <button 
            className="btn btn-primary-gradient px-5 py-3 rounded-pill fw-bold fs-5 d-flex align-items-center gap-2" 
            onClick={handleRunInitial} 
            disabled={!selectedCurrent}
          >
            Run Complete Analysis <MdChevronRight size={24} />
          </button>
        </motion.div>
      )}

      {!loading && step === 2 && orchestrationData?.recommendation && (
        <motion.div initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }}>
          <div className="row g-4 mb-4">
            <div className="col-md-6">
              <div className="glass-card h-100 border-danger border-opacity-50">
                <h5 className="fw-bold mb-4 text-danger d-flex align-items-center gap-2">
                  <MdWarning /> Live Risk Detected
                </h5>
                <h4 className="fw-bold">{orchestrationData.recommendation['Current Supplier']}</h4>
                <div className="mt-4 p-3 glass-panel rounded bg-danger bg-opacity-10 border-danger border-opacity-25">
                  <div className="d-flex justify-content-between mb-2">
                    <span className="fw-semibold">Risk Score</span>
                    <span className="fw-bold text-danger fs-5">{orchestrationData.recommendation['Risk Assessment']?.['Risk Score']}</span>
                  </div>
                  <div className="d-flex justify-content-between">
                    <span className="fw-semibold">Level</span>
                    <span className="fw-bold text-danger">{orchestrationData.recommendation['Risk Assessment']?.['Risk Level']}</span>
                  </div>
                </div>
              </div>
            </div>
            
            <div className="col-md-6">
              <div className="glass-card h-100 border-warning border-opacity-50">
                <h5 className="fw-bold mb-4 text-warning d-flex align-items-center gap-2">
                  <MdOutlineAssessment /> Scenario Impact
                </h5>
                <div className="d-flex justify-content-between mb-3 border-bottom border-secondary border-opacity-25 pb-2">
                  <span className="text-muted-custom">Supply Shortage</span>
                  <span className="fw-bold text-warning">{orchestrationData.recommendation['Risk Assessment']?.['Supply Shortage']}</span>
                </div>
                <div className="d-flex justify-content-between mb-3 border-bottom border-secondary border-opacity-25 pb-2">
                  <span className="text-muted-custom">Production Loss</span>
                  <span className="fw-bold text-warning">{orchestrationData.recommendation['Risk Assessment']?.['Production Loss']}</span>
                </div>
                <p className="small text-muted-custom mt-3 fst-italic">
                  {orchestrationData.recommendation['Risk Assessment']?.['Conclusion']}
                </p>
              </div>
            </div>
          </div>

          <div className="glass-card border-primary border-opacity-50">
            <h5 className="fw-bold mb-4">Select Alternative Supplier to Proceed</h5>
            <div className="row g-4">
              {(orchestrationData.recommendation['Top 4 Ranked Suppliers'] || []).slice(0,3).map((alt, i) => (
                <div className="col-lg-4" key={i}>
                  <div className="p-4 border border-secondary border-opacity-25 rounded h-100 d-flex flex-column transition-all hover-bg-primary-light" style={{backgroundColor: 'var(--bg-secondary)'}}>
                    <div className="d-flex justify-content-between align-items-start mb-3">
                      <h5 className="fw-bold text-truncate m-0" title={alt.supplier_name}>{alt.supplier_name}</h5>
                      <span className={`badge ${i===0 ? 'bg-success' : 'bg-secondary'}`}>#{alt.rank || (i+1)}</span>
                    </div>
                    <p className="text-muted-custom small mb-4 d-flex align-items-center gap-1">
                      <MdMap /> {alt.country}
                    </p>
                    <p className="small text-muted-custom flex-grow-1">{alt.Reason}</p>
                    <button className="btn btn-outline-primary w-100 py-2 rounded-pill fw-bold mt-3" onClick={() => handleSelectAlternative(alt.supplier_name)}>
                      Select & Predict Routes
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </motion.div>
      )}

      {!loading && step === 5 && orchestrationData?.final && (
        <motion.div initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }}>
          <div className="glass-card mb-4 text-center p-5 position-relative overflow-hidden" style={{ background: 'var(--primary-gradient)' }}>
            <div className="position-absolute top-50 start-50 translate-middle w-100 h-100" style={{ background: 'radial-gradient(circle, rgba(255,255,255,0.2) 0%, rgba(255,255,255,0) 70%)', opacity: 0.5 }}></div>
            <MdDoneAll size={64} className="text-white mb-3 position-relative z-index-1" />
            <h2 className="fw-bold text-white mb-2 position-relative z-index-1">Final Decision Generated</h2>
            <p className="text-white text-opacity-75 fs-5 m-0 position-relative z-index-1">Optimal resilience plan compiled successfully.</p>
          </div>

          <div className="row g-4 mb-4">
            <div className="col-md-6">
              <div className="glass-card h-100">
                <h5 className="fw-bold mb-4 d-flex align-items-center gap-2"><MdMap className="text-primary"/> Predicted Logistics</h5>
                <div className="p-3 bg-secondary bg-opacity-10 rounded mb-3">
                  <span className="d-block text-muted-custom small mb-1">Recommended Route</span>
                  <span className="fw-bold fs-6">{orchestrationData.final.alternative_analysis?.best_route || 'Direct Sea Freight'}</span>
                </div>
                <div className="d-flex justify-content-between align-items-center p-3 border-bottom border-secondary border-opacity-25">
                  <span className="text-muted-custom"><MdTimer className="me-2"/>Expected Time</span>
                  <span className="fw-bold">{orchestrationData.final.alternative_analysis?.expected_delivery_days} Days</span>
                </div>
                <div className="d-flex justify-content-between align-items-center p-3 border-bottom border-secondary border-opacity-25">
                  <span className="text-muted-custom"><MdWarning className="me-2"/>Predicted Delay</span>
                  <span className="fw-bold text-warning">{orchestrationData.final.alternative_analysis?.predicted_delay}</span>
                </div>
              </div>
            </div>
            
            <div className="col-md-6">
              <div className="glass-card h-100">
                <h5 className="fw-bold mb-4 d-flex align-items-center gap-2"><MdAttachMoney className="text-success"/> Cost Implications</h5>
                <div className="d-flex justify-content-between align-items-center p-3 border-bottom border-secondary border-opacity-25">
                  <span className="text-muted-custom">Transportation</span>
                  <span className="fw-medium">{orchestrationData.final.alternative_analysis?.transportation_cost}</span>
                </div>
                <div className="d-flex justify-content-between align-items-center p-3 border-bottom border-secondary border-opacity-25">
                  <span className="text-muted-custom">Logistics</span>
                  <span className="fw-medium">{orchestrationData.final.alternative_analysis?.logistics_cost}</span>
                </div>
                <div className="mt-4 p-4 rounded text-center" style={{ background: 'rgba(5, 205, 153, 0.1)', border: '1px solid rgba(5, 205, 153, 0.2)' }}>
                  <span className="d-block text-success fw-bold text-uppercase small mb-1">Total Predicted Cost</span>
                  <h3 className="fw-bold text-success m-0">{orchestrationData.final.alternative_analysis?.predicted_total_cost}</h3>
                </div>
              </div>
            </div>
            
            <div className="col-12">
              <div className="glass-card border-info border-opacity-50">
                <h5 className="fw-bold mb-4 d-flex align-items-center gap-2"><MdInventory className="text-info"/> Strategic Reserve Action</h5>
                <p className="text-muted-custom fs-5 mb-4 line-height-lg fst-italic">"{orchestrationData.final.spr_optimization?.explanation || "Optimize inventory based on selected supplier lead time."}"</p>
                <div className="row g-4">
                  <div className="col-md-4">
                    <div className="p-3 glass-panel text-center">
                      <span className="d-block text-muted-custom small mb-2">Release Reserve</span>
                      <h4 className={`fw-bold m-0 ${orchestrationData.final.spr_optimization?.release_spr ? 'text-danger' : 'text-success'}`}>
                        {orchestrationData.final.spr_optimization?.release_spr ? 'YES' : 'NO'}
                      </h4>
                    </div>
                  </div>
                  <div className="col-md-4">
                    <div className="p-3 glass-panel text-center">
                      <span className="d-block text-muted-custom small mb-2">Optimization Score</span>
                      <h4 className="fw-bold text-info m-0">{orchestrationData.final.spr_optimization?.optimization_score?.toFixed(1) || '95.0'}/100</h4>
                    </div>
                  </div>
                  <div className="col-md-4">
                    <div className="p-3 glass-panel text-center">
                      <span className="d-block text-muted-custom small mb-2">Cost Impact</span>
                      <h4 className="fw-bold m-0">${(orchestrationData.final.spr_optimization?.estimated_total_cost || 0).toLocaleString()}</h4>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
          
          <div className="text-center mb-5">
            <button className="btn btn-primary-gradient px-5 py-3 rounded-pill fw-bold fs-5 shadow-lg" onClick={() => navigate('/reports', { state: { autoGenerate: 'complete', data: orchestrationData } })}>
              Save & Generate Formal Report
            </button>
          </div>
        </motion.div>
      )}
    </div>
  );
};

export default IntegratedAnalysis;
