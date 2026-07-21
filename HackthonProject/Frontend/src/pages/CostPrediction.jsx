import React, { useState, useEffect } from 'react';
import { useAnalysis } from '../contexts/AnalysisContext';
import { supplierApi } from '../services/supplierApi';
import { motion } from 'framer-motion';
import { 
  PieChart, Pie, Cell, ResponsiveContainer, Tooltip as RechartsTooltip, Legend
} from 'recharts';
import { MdAttachMoney, MdAccountBalanceWallet, MdArrowDropDown } from 'react-icons/md';
import ErrorCard from '../components/ErrorCard';

const parseMoney = (str) => {
  if (!str) return 0;
  if (typeof str === 'number') return str;
  return parseFloat(str.replace(/[^0-9.-]+/g, "")) || 0;
};

const CostPrediction = () => {
  const { currentSupplier, selectedAlternative, setCurrentSupplier } = useAnalysis();
  const [suppliersList, setSuppliersList] = useState([]);
  const [selectedSupplierName, setSelectedSupplierName] = useState('');
  const [loading, setLoading] = useState(false);
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);

  // Load all suppliers list to select from if none selected
  useEffect(() => {
    const loadSuppliers = async () => {
      try {
        const res = await supplierApi.getCurrentSuppliers();
        setSuppliersList(res.data || []);
      } catch (err) {
        console.error("Failed to load suppliers", err);
      }
    };
    loadSuppliers();
  }, []);

  const fetchCost = async (supplierName) => {
    if (!supplierName) return;
    setLoading(true);
    setError(null);
    try {
      const payload = {
        selected_supplier: supplierName,
      };
      const res = await supplierApi.predictCost(payload);
      setData(res.data);
    } catch (err) {
      setError("Failed to fetch cost predictions for supplier: " + supplierName);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    const supplierToUse = selectedAlternative || currentSupplier;
    if (supplierToUse) {
      const name = supplierToUse.supplier_name || supplierToUse.name || supplierToUse.Supplier || supplierToUse.supplier_id;
      setSelectedSupplierName(name);
      fetchCost(name);
    }
  }, [currentSupplier, selectedAlternative]);

  const handleSupplierChange = (e) => {
    const val = e.target.value;
    setSelectedSupplierName(val);
    const found = suppliersList.find(s => (s.supplier_name || s.Supplier || s.supplier_id) === val);
    if (found) {
      setCurrentSupplier(found);
    }
    fetchCost(val);
  };

  // Safe parsing values
  const transVal = parseMoney(data?.["Transportation Cost"]);
  const fuelVal = parseMoney(data?.["Fuel Cost"]);
  const insVal = parseMoney(data?.["Insurance Cost"]);
  const logVal = parseMoney(data?.["Logistics Cost"]);
  const totalVal = parseMoney(data?.["Predicted Total Cost"]) || (transVal + fuelVal + insVal + logVal);
  
  // Calculate additional if total exceeds sum
  const sumOfParts = transVal + fuelVal + insVal + logVal;
  const additionalVal = Math.max(0, totalVal - sumOfParts);

  const costBreakdown = [
    { name: 'Transportation', value: transVal, color: '#4318FF' },
    { name: 'Fuel', value: fuelVal, color: '#FFCE20' },
    { name: 'Insurance', value: insVal, color: '#05CD99' },
    { name: 'Logistics', value: logVal, color: '#39B8FF' },
    { name: 'Additional Charges', value: additionalVal, color: '#EE5D50' },
  ].filter(item => item.value > 0);

  return (
    <div className="page-container py-4">
      <div className="d-flex justify-content-between align-items-center mb-4 flex-wrap gap-3">
        <div>
          <h2 className="fw-bold gradient-text m-0">Dynamic Cost Prediction</h2>
          <p className="text-muted-custom mt-1">End-to-end supply chain cost forecasting using Random Forest regressions.</p>
        </div>
        
        {/* Supplier Selector Dropdown */}
        <div className="d-flex align-items-center gap-2">
          <label className="fw-bold text-muted-custom small text-nowrap m-0">Select Supplier:</label>
          <select 
            className="form-select glass-panel py-2 px-3 fw-bold text-primary"
            style={{ width: '260px', cursor: 'pointer' }}
            value={selectedSupplierName}
            onChange={handleSupplierChange}
          >
            <option value="" style={{ color: '#000' }}>-- Select Supplier --</option>
            {suppliersList.map((s, idx) => {
              const name = s.supplier_name || s.Supplier || s.supplier_id;
              return (
                <option key={idx} value={name} style={{ color: '#000' }}>
                  {name} ({s.country || s.Country})
                </option>
              );
            })}
          </select>
        </div>
      </div>

      {!selectedSupplierName ? (
        <div className="glass-card d-flex flex-column align-items-center justify-content-center py-5 text-center" style={{ minHeight: '50vh' }}>
          <MdAttachMoney size={80} className="text-muted-custom mb-4 opacity-50" />
          <h4 className="fw-bold">No Supplier Selected</h4>
          <p className="text-muted-custom max-w-md">Please select a supplier from the dropdown above or run an orchestration workflow to forecast logistics costs.</p>
        </div>
      ) : loading ? (
        <div className="glass-card d-flex flex-column align-items-center justify-content-center py-5" style={{ minHeight: '50vh' }}>
          <div className="spinner-border text-primary mb-3" role="status"><span className="visually-hidden">Loading...</span></div>
          <h5 className="fw-bold text-muted-custom">Computing Logistics Cost Breakdown...</h5>
        </div>
      ) : error ? (
        <div className="page-container py-2"><ErrorCard error={error} onRetry={() => fetchCost(selectedSupplierName)} /></div>
      ) : data ? (
        <div className="row g-4">
          <div className="col-lg-4">
            <motion.div className="glass-card h-100 d-flex flex-column justify-content-between p-4" initial={{ opacity: 0, y: 15 }} animate={{ opacity: 1, y: 0 }}>
              <div className="text-center py-4">
                <div className="mb-3 p-4 rounded-circle bg-success bg-opacity-10 text-success d-inline-block align-self-center">
                  <MdAccountBalanceWallet size={48} />
                </div>
                <h5 className="text-muted-custom mb-2 fw-semibold">Predicted Total Cost</h5>
                <h2 className="fw-bold text-success mb-0" style={{ fontSize: '2.5rem' }}>
                  ${totalVal.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                </h2>
              </div>
              
              <div className="p-3 bg-secondary bg-opacity-10 rounded mt-4">
                <div className="d-flex justify-content-between mb-2">
                  <span className="text-muted-custom small fw-medium">Base Cargo Cost</span>
                  <span className="fw-bold small">${(totalVal * 0.85).toLocaleString(undefined, { maximumFractionDigits: 0 })}</span>
                </div>
                <div className="d-flex justify-content-between">
                  <span className="text-muted-custom small fw-medium">Risk Premium Charge</span>
                  <span className="fw-bold text-danger small">+${(totalVal * 0.15).toLocaleString(undefined, { maximumFractionDigits: 0 })}</span>
                </div>
              </div>
            </motion.div>
          </div>

          <div className="col-lg-8">
            <motion.div className="glass-card h-100" initial={{ opacity: 0, y: 15 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }}>
              <h5 className="fw-bold mb-4 border-bottom border-secondary border-opacity-25 pb-2">Cost Breakdown Analysis</h5>
              <div className="row align-items-center h-100">
                <div className="col-md-6" style={{ minHeight: '260px' }}>
                  <ResponsiveContainer width="100%" height="100%">
                    <PieChart>
                      <Pie 
                        data={costBreakdown} 
                        innerRadius={65} 
                        outerRadius={95} 
                        paddingAngle={5} 
                        dataKey="value"
                      >
                        {costBreakdown.map((entry, index) => <Cell key={`cell-${index}`} fill={entry.color} />)}
                      </Pie>
                      <RechartsTooltip formatter={(value) => `$${value.toLocaleString(undefined, { minimumFractionDigits: 2 })}`} contentStyle={{ backgroundColor: 'var(--card-bg)', border: 'none', borderRadius: '12px' }} />
                    </PieChart>
                  </ResponsiveContainer>
                </div>
                <div className="col-md-6 d-flex flex-column justify-content-center gap-3">
                  {costBreakdown.map((item, i) => (
                    <div key={i} className="d-flex align-items-center justify-content-between p-2 rounded" style={{ backgroundColor: 'var(--bg-primary)', borderLeft: `4px solid ${item.color}` }}>
                      <div className="d-flex align-items-center gap-2 ps-1">
                        <span className="fw-semibold small" style={{ color: 'var(--text-primary)' }}>{item.name}</span>
                      </div>
                      <span className="fw-bold" style={{ color: 'var(--text-primary)' }}>${item.value.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</span>
                    </div>
                  ))}
                </div>
              </div>
            </motion.div>
          </div>
        </div>
      ) : null}
    </div>
  );
};

export default CostPrediction;
