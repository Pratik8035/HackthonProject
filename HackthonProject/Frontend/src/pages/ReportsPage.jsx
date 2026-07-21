import React, { useState, useEffect } from 'react';
import { useLocation } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  MdPictureAsPdf, MdTableChart, MdInsertDriveFile, MdPrint, 
  MdAssessment, MdPublic, MdWarning, MdCompareArrows, MdInventory, MdClose
} from 'react-icons/md';
import { jsPDF } from 'jspdf';
import './ReportPreview.css';
import { riskApi } from '../services/riskApi';
import { scenarioApi } from '../services/scenarioApi';
import { supplierApi } from '../services/supplierApi';

const ReportsPage = () => {
  const [selectedReport, setSelectedReport] = useState(null);
  const [loading, setLoading] = useState(false);
  const [previewData, setPreviewData] = useState(null);
  const [showPreview, setShowPreview] = useState(false);
  const location = useLocation();

  const reportTypes = [
    { id: 'complete', title: 'Complete Analysis Report', icon: <MdAssessment size={32} className="text-primary"/>, desc: 'End-to-end supply chain resiliency overview.', color: 'primary' },
    { id: 'supplier', title: 'Supplier Recommendation Report', icon: <MdCompareArrows size={32} className="text-info"/>, desc: 'Detailed AI rankings of alternative suppliers.', color: 'info' },
    { id: 'risk', title: 'Risk Report', icon: <MdPublic size={32} className="text-danger"/>, desc: 'Global geopolitical and operational risk tracking.', color: 'danger' },
    { id: 'scenario', title: 'Scenario Report', icon: <MdWarning size={32} className="text-warning"/>, desc: 'Simulated impacts of supply chain disruptions.', color: 'warning' },
    { id: 'reserve', title: 'Reserve Report', icon: <MdInventory size={32} className="text-success"/>, desc: 'Strategic inventory optimization and savings.', color: 'success' },
  ];

  useEffect(() => {
    if (location.state && location.state.autoGenerate) {
      const report = reportTypes.find(r => r.id === location.state.autoGenerate);
      if (report) {
         handleGenerate(report, location.state.data);
      }
    }
  }, [location.state]);

  const handleGenerate = async (report, prefilledData = null) => {
    setSelectedReport(report);
    setLoading(true);
    setPreviewData(null);
    setShowPreview(true);
    
    try {
      let dataObj = null;
      // Simulate fetching different report data from backend
      if (prefilledData) {
        dataObj = prefilledData;
        await new Promise(r => setTimeout(r, 800)); // fake delay for UI consistency
      } else if (report.id === 'risk' || report.id === 'complete') {
        const res = await riskApi.runRiskAssessment();
        dataObj = res.data;
      } else if (report.id === 'scenario') {
        const res = await scenarioApi.listScenarios();
        dataObj = res.data;
      } else if (report.id === 'supplier') {
        const res = await supplierApi.getCurrentSuppliers();
        dataObj = res.data;
      } else {
        // Mock a simple object for reserve/other reports
        await new Promise(r => setTimeout(r, 1000));
        dataObj = {
          status: "Generated",
          module: report.title,
          timestamp: new Date().toISOString(),
        };
      }
      // Convert object to plain‑text lines (key: value)
      const formatReportData = (obj, indent = 0) => {
          if (!obj) return "";
          const pad = ' '.repeat(indent);
          const formatValue = (value, level) => {
            if (Array.isArray(value)) {
              // Render each array element on its own line without dash symbols
              return value
                .map((item) => `${pad}  ${formatValue(item, level + 2)}`)
                .join('\n');
            }
            if (value && typeof value === 'object') {
              return Object.entries(value)
                .map(([k, v]) => `${pad}  ${k}: ${formatValue(v, level + 2)}`)
                .join('\n');
            }
            return `${value}`;
          };
          return Object.entries(obj)
            .map(([k, v]) => {
              const formatted = formatValue(v, indent + 2);
              if (formatted.includes('\n')) {
                return `${pad}${k}:\n${formatted}`;
              }
              return `${pad}${k}: ${formatted}`;
            })
            .join('\n');
        };
      const formatted = formatReportData(dataObj);
      setPreviewData(formatted);
    } catch (err) {
      setPreviewData("Error fetching report data from backend API: " + err.message);
    } finally {
      setLoading(false);
    } };

  const handleExport = (format) => {
    if (!previewData) return;
    
    if (format === 'pdf') {
      // Create a real PDF using jsPDF
      const doc = new jsPDF();
      const lines = previewData.split('\n');
      let y = 10;
      lines.forEach((line) => {
        doc.text(line, 10, y);
        y += 7; // line height
        if (y > 280) { // page break
          doc.addPage();
          y = 10;
        }
      });
      doc.save(`${selectedReport.id}_report_${Date.now()}.pdf`);
      return;
    }
    
    let content = previewData;
    let type = 'text/plain';
    let ext = 'txt';
    
    if (format === 'csv') {
      type = 'text/csv';
      ext = 'csv';
      content = "Report Type,Timestamp\n" + selectedReport.title + "," + new Date().toISOString();
    } else if (format === 'excel') {
      type = 'application/vnd.ms-excel';
      ext = 'xls';
    }
    
    const blob = new Blob([content], { type });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${selectedReport.id}_report_${new Date().getTime()}.${ext}`;
    a.click();
  };

  const handlePrint = () => {
    window.print();
  };

  return (
    <div className="page-container py-4">
      <div className="mb-5">
        <h2 className="fw-bold gradient-text m-0">Generate Enterprise Reports</h2>
        <p className="text-muted-custom mt-1">Export AI-driven analytics for stakeholder presentations and compliance.</p>
      </div>
      
      <div className="row g-4 mb-5">
        {reportTypes.map((report) => (
          <div className="col-lg-4 col-md-6" key={report.id}>
            <motion.div 
              className={`glass-card p-4 h-100 d-flex flex-column border border-${report.color} border-opacity-25 transition-all hover-bg-primary-light`}
              whileHover={{ y: -5, boxShadow: `0 10px 30px rgba(0,0,0,0.1)` }}
              onClick={() => handleGenerate(report)}
              style={{ cursor: 'pointer' }}
            >
              <div className={`p-3 rounded-circle bg-${report.color} bg-opacity-10 d-inline-block mb-3 align-self-start`}>
                {report.icon}
              </div>
              <h5 className={`fw-bold text-${report.color} mb-2`}>{report.title}</h5>
              <p className="text-muted-custom small mb-4 flex-grow-1">{report.desc}</p>
              
              <button className={`btn btn-outline-${report.color} w-100 rounded-pill fw-bold mt-auto`}>
                Generate & Preview
              </button>
            </motion.div>
          </div>
        ))}
      </div>

      <AnimatePresence>
        {showPreview && (
          <motion.div 
            className="position-fixed top-0 start-0 w-100 h-100 d-flex align-items-center justify-content-center"
            style={{ zIndex: 1050, background: 'rgba(0,0,0,0.6)', backdropFilter: 'blur(5px)' }}
            initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
          >
            <motion.div 
              className="glass-card p-0 overflow-hidden d-flex flex-column"
              style={{ width: '80%', maxWidth: '900px', height: '80vh', backgroundColor: 'var(--bg-primary)' }}
              initial={{ scale: 0.9, y: 50 }} animate={{ scale: 1, y: 0 }} exit={{ scale: 0.9, y: 50 }}
            >
              <div className="d-flex justify-content-between align-items-center p-4 border-bottom border-secondary border-opacity-25" style={{ backgroundColor: 'var(--bg-secondary)' }}>
                <div>
                  <h4 className="fw-bold m-0">{selectedReport?.title}</h4>
                  <span className="text-muted-custom small">Preview Mode</span>
                </div>
                <button className="btn btn-link text-muted-custom p-0" onClick={() => setShowPreview(false)}>
                  <MdClose size={28} />
                </button>
              </div>
              
              <div className="p-4 flex-grow-1 overflow-auto custom-scrollbar" style={{ backgroundColor: 'var(--bg-primary)' }}>
                {loading ? (
                  <div className="h-100 d-flex flex-column justify-content-center align-items-center">
                    <div className="spinner-border text-primary mb-3" role="status" style={{ width: '3rem', height: '3rem' }}></div>
                    <h5 className="fw-bold text-muted-custom">Compiling Report Data...</h5>
                  </div>
                ) : (
                  <div className="report-preview">
                    <div className="position-absolute top-0 end-0 p-2 opacity-50"><small>CONFIDENTIAL</small></div>
                    <div className="report-content">
                      {previewData?.split('\n').map((line, idx) => (
                        <p key={idx} className="report-line">{line}</p>
                      ))}
                    </div>
                  </div>
                )}
              </div>
              
              <div className="p-4 border-top border-secondary border-opacity-25 d-flex justify-content-between flex-wrap gap-3" style={{ backgroundColor: 'var(--bg-secondary)' }}>
                <button className="btn btn-outline-secondary px-4 fw-bold" onClick={handlePrint} disabled={loading}>
                  <MdPrint className="me-2"/> Print
                </button>
                <div className="d-flex gap-2">
                  <button className="btn btn-danger d-flex align-items-center gap-2 px-4" onClick={() => handleExport('pdf')} disabled={loading}>
                    <MdPictureAsPdf /> PDF
                  </button>
                  <button className="btn btn-success d-flex align-items-center gap-2 px-4" onClick={() => handleExport('excel')} disabled={loading}>
                    <MdTableChart /> Excel
                  </button>
                  <button className="btn btn-primary d-flex align-items-center gap-2 px-4" onClick={() => handleExport('csv')} disabled={loading}>
                    <MdInsertDriveFile /> CSV
                  </button>
                </div>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};

export default ReportsPage;
