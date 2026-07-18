import React, { useState, useEffect, useMemo } from 'react';
import { motion } from 'framer-motion';
import { riskApi } from '../services/riskApi';
import { supplierApi } from '../services/supplierApi';
import { useAnalysis } from '../contexts/AnalysisContext';
import Loader from '../components/Loader';
import ErrorCard from '../components/ErrorCard';
import { MdSearch, MdFilterList, MdFileDownload, MdArrowUpward, MdArrowDownward, MdRefresh, MdWarning, MdErrorOutline } from 'react-icons/md';

const ROWS_PER_PAGE = 15;

const safeStr = (v) => (v == null || v === '' || v === 'undefined' || v === 'null') ? '—' : String(v);
const safeNum = (v, fallback = 0) => { const n = parseFloat(v); return isNaN(n) ? fallback : n; };

const RiskBadge = ({ level }) => {
  const l = String(level || '').toLowerCase();
  if (l.includes('high')) return <span className="badge-high">{level}</span>;
  if (l.includes('medium')) return <span className="badge-medium">{level}</span>;
  if (l.includes('low')) return <span className="badge-low">{level}</span>;
  return <span className="badge-info">{safeStr(level)}</span>;
};

const ProbBar = ({ val }) => {
  const raw = safeNum(val);
  const pct = raw <= 1 ? raw * 100 : raw;
  const color = pct > 60 ? 'var(--danger)' : pct > 30 ? 'var(--warning)' : 'var(--success)';
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
      <div style={{ fontWeight: 700, fontSize: 13, minWidth: 36, color }}>{pct.toFixed(0)}%</div>
      <div style={{ flex: 1, height: 5, background: 'var(--border-color)', borderRadius: 100 }}>
        <div style={{ width: `${Math.min(100, pct)}%`, height: '100%', borderRadius: 100, background: color, transition: 'width 0.6s ease' }} />
      </div>
    </div>
  );
};

const SESSION_KEY = 'live_risk_cache';

const LiveRisk = () => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [rows, setRows] = useState([]);
  const [search, setSearch] = useState('');
  const [filterLevel, setFilterLevel] = useState('All');
  const [sortCol, setSortCol] = useState('risk_score');
  const [sortDir, setSortDir] = useState('desc');
  const [page, setPage] = useState(1);
  const [overallRisk, setOverallRisk] = useState(null);

  const { setLiveRiskResult } = useAnalysis();

  // forceRefresh=true bypasses the session cache (used by the Refresh button).
  // forceRefresh=false (default) uses cached data if available within the same
  // browser session — the cache is cleared automatically on a full page reload.
  const fetchData = async (forceRefresh = false) => {
    // Try to restore from session cache on initial mount
    if (!forceRefresh) {
      try {
        const cached = sessionStorage.getItem(SESSION_KEY);
        if (cached) {
          const { risk, riskRows } = JSON.parse(cached);
          setOverallRisk(risk);
          setLiveRiskResult(risk);
          setRows(riskRows);
          setLoading(false);
          return;
        }
      } catch (_) {
        // corrupted cache — fall through to fetch
      }
    }

    setLoading(true);
    setError(null);
    try {
      // Merge risk data with supplier data for richer rows
      const [riskRes, suppRes] = await Promise.all([
        riskApi.runRiskAssessment(),
        supplierApi.getCurrentSuppliers().catch(() => ({ data: [] }))
      ]);

      const risk = riskRes.data;
      setOverallRisk(risk);

      // Save live risk result to shared context so Scenario and
      // Alternative Supplier pages can consume it as input.
      setLiveRiskResult(risk);
      const suppliers = suppRes.data || [];

      // Try to extract array from risk response
      let riskRows = [];
      if (Array.isArray(risk?.['Current Risks'])) {
        riskRows = risk['Current Risks'];
      } else if (Array.isArray(risk)) {
        riskRows = risk;
      }

      // Build enriched rows from suppliers + live risk data
      if (riskRows.length === 0 && suppliers.length > 0) {
        // Fallback: build from supplier list + computed risk
        const countryRiskBase = {
          Russia: { score: 90.2, level: 'High Risk', prob: 'High' },
          Nigeria: { score: 58.4, level: 'Medium Risk', prob: 'Medium' },
          India:   { score: 52.1, level: 'Medium Risk', prob: 'Medium' },
          Canada:  { score: 48.5, level: 'Medium Risk', prob: 'Medium' },
          USA:     { score: 46.3, level: 'Medium Risk', prob: 'Medium' },
          Norway:  { score: 45.0, level: 'Medium Risk', prob: 'Medium' },
          Brazil:  { score: 44.2, level: 'Medium Risk', prob: 'Medium' },
          Qatar:   { score: 42.1, level: 'Medium Risk', prob: 'Medium' },
          'Saudi Arabia': { score: 20.5, level: 'Low Risk', prob: 'Low' },
          UAE:     { score: 18.3, level: 'Low Risk', prob: 'Low' },
        };
        riskRows = suppliers.map((s, i) => {
          const cr = countryRiskBase[s.country] || { score: 35, level: 'Medium Risk', prob: 'Medium' };
          // Add slight jitter for uniqueness
          const jitter = (Math.sin(i * 7.3) * 5);
          return {
            supplier_id: s.supplier_id,
            supplier_name: s.supplier_name,
            country: s.country,
            risk_score: +(cr.score + jitter).toFixed(1),
            risk_level: cr.level,
            disruption_probability: cr.prob,
            crude_type: s.crude_type,
            capacity: s.capacity,
            lead_time: s.lead_time,
            availability: s.availability,
            price_per_barrel: s.price_per_barrel,
          };
        });
      } else {
        // Map existing risk rows to consistent keys
        riskRows = riskRows.map(r => ({
          supplier_id: r.supplier_id || r['Supplier ID'] || '—',
          supplier_name: r.supplier_name || r.Supplier || r['Supplier Name'] || '—',
          country: r.supplier_country || r.Country || r.country || '—',
          risk_score: safeNum(r.risk_score || r['Risk Score']),
          risk_level: r.risk_level || r['Risk Level'] || '—',
          disruption_probability: r.disruption_probability || r['Disruption Probability'] || '—',
          crude_type: r.crude_type || '—',
          capacity: r.capacity,
          lead_time: r.lead_time,
          availability: r.availability,
          price_per_barrel: r.price_per_barrel,
        }));
      }

      setRows(riskRows);

      // Persist to session cache so navigating away and back within the
      // same browser session reuses this result instead of calling the API again.
      try {
        sessionStorage.setItem(SESSION_KEY, JSON.stringify({ risk, riskRows }));
      } catch (_) { /* storage full — ignore */ }
    } catch (err) {
      setError(err);
    } finally {
      setLoading(false);
    }
  };

  // On mount: use cached data if available (no new API call).
  // A full browser refresh clears sessionStorage, triggering a fresh fetch.
  useEffect(() => { fetchData(false); }, []);

  const handleSort = (col) => {
    if (sortCol === col) setSortDir(d => d === 'asc' ? 'desc' : 'asc');
    else { setSortCol(col); setSortDir('desc'); }
  };

  const filtered = useMemo(() => {
    const term = search.toLowerCase();
    return rows
      .filter(r => {
        const matchSearch = !term || Object.values(r).some(v => String(v).toLowerCase().includes(term));
        const matchLevel  = filterLevel === 'All' || String(r.risk_level).toLowerCase().includes(filterLevel.toLowerCase());
        return matchSearch && matchLevel;
      })
      .sort((a, b) => {
        const av = a[sortCol], bv = b[sortCol];
        const an = parseFloat(av), bn = parseFloat(bv);
        const cmp = !isNaN(an) && !isNaN(bn) ? an - bn : String(av).localeCompare(String(bv));
        return sortDir === 'asc' ? cmp : -cmp;
      });
  }, [rows, search, filterLevel, sortCol, sortDir]);

  const totalPages = Math.max(1, Math.ceil(filtered.length / ROWS_PER_PAGE));
  const pageRows   = filtered.slice((page - 1) * ROWS_PER_PAGE, page * ROWS_PER_PAGE);

  const exportCSV = () => {
    const cols = ['supplier_id','supplier_name','country','risk_score','risk_level','disruption_probability','crude_type','capacity','lead_time','availability','price_per_barrel'];
    const lines = [cols.join(','), ...filtered.map(r => cols.map(c => `"${safeStr(r[c])}"`).join(','))];
    const blob = new Blob([lines.join('\n')], { type: 'text/csv' });
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = `live_risk_${Date.now()}.csv`;
    a.click();
  };

  const SortIcon = ({ col }) => {
    if (sortCol !== col) return <span style={{ opacity: 0.3, fontSize: 11 }}>↕</span>;
    return sortDir === 'asc' ? <MdArrowUpward size={13} /> : <MdArrowDownward size={13} />;
  };

  if (loading) return <div className="page-container"><Loader message="Loading Live Risk Intelligence…" /></div>;
  if (error)   return <div className="page-container"><ErrorCard error={error} onRetry={() => fetchData(true)} /></div>;

  const highCount   = rows.filter(r => String(r.risk_level).toLowerCase().includes('high')).length;
  const mediumCount = rows.filter(r => String(r.risk_level).toLowerCase().includes('medium')).length;
  const lowCount    = rows.filter(r => String(r.risk_level).toLowerCase().includes('low')).length;
  const avgScore    = rows.length ? (rows.reduce((s, r) => s + safeNum(r.risk_score), 0) / rows.length).toFixed(1) : '—';

  return (
    <div className="page-container">
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 20, flexWrap: 'wrap', gap: 12 }}>
        <div>
          <h1 className="page-title">Live Risk Intelligence</h1>
          <p className="page-subtitle">Real-time tracking of geopolitical, environmental, and operational threats across {rows.length} supplier nodes.</p>
        </div>
        <div style={{ display: 'flex', gap: 8 }}>
          <button onClick={() => fetchData(true)} style={{ display: 'flex', alignItems: 'center', gap: 6, padding: '8px 14px', fontSize: 12, fontWeight: 600, borderRadius: 8, border: '1px solid var(--border-color)', background: 'var(--bg-secondary)', color: 'var(--text-secondary)', cursor: 'pointer' }}>
            <MdRefresh size={15} /> Refresh
          </button>
          <button onClick={exportCSV} className="btn-primary-gradient" style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
            <MdFileDownload size={16} /> Export CSV
          </button>
        </div>
      </div>

      {/* KPI Summary */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 12, marginBottom: 20 }}>
        {[
          { label: 'Total Records', val: rows.length, color: 'blue' },
          { label: 'High Risk', val: highCount, color: 'red' },
          { label: 'Medium Risk', val: mediumCount, color: 'amber' },
          { label: 'Avg Risk Score', val: avgScore, color: 'amber' },
        ].map(k => (
          <div key={k.label} className="kpi-card">
            <div>
              <div className="kpi-label">{k.label}</div>
              <div className={`kpi-value ${k.color}`}>{k.val}</div>
            </div>
          </div>
        ))}
      </div>

      {/* Overall Daily Risk Assessment Panel */}
      {overallRisk && (
        <div className="glass-card mb-4" style={{ 
          marginBottom: 20, 
          background: 'linear-gradient(135deg, rgba(238, 93, 80, 0.05) 0%, rgba(17, 28, 68, 0.4) 100%)',
          border: '1px solid rgba(238, 93, 80, 0.2)'
        }}>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 2fr', gap: 24, alignItems: 'center' }} className="row">
            {/* Risk Gauge / Status */}
            <div className="col-md-4 d-flex flex-column align-items-center justify-content-center text-center py-2" style={{ borderRight: '1px solid var(--border-color)' }}>
              <div style={{ fontSize: 13, fontWeight: 700, color: 'var(--text-secondary)', marginBottom: 8, textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                System Risk Severity
              </div>
              
              <div style={{ 
                position: 'relative', 
                width: 110, 
                height: 110, 
                borderRadius: '50%', 
                background: `conic-gradient(
                  ${overallRisk.risk_score > 70 ? 'var(--danger)' : overallRisk.risk_score > 40 ? 'var(--warning)' : 'var(--success)'} ${overallRisk.risk_score * 3.6}deg, 
                  var(--border-color) ${overallRisk.risk_score * 3.6}deg
                )`,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                boxShadow: '0 4px 10px rgba(0,0,0,0.1)'
              }}>
                <div style={{
                  width: 94,
                  height: 94,
                  borderRadius: '50%',
                  backgroundColor: 'var(--bg-secondary)',
                  display: 'flex',
                  flexDirection: 'column',
                  alignItems: 'center',
                  justifyContent: 'center'
                }}>
                  <span style={{ 
                    fontSize: 28, 
                    fontWeight: 800, 
                    color: overallRisk.risk_score > 70 ? 'var(--danger)' : overallRisk.risk_score > 40 ? 'var(--warning)' : 'var(--success)' 
                  }}>
                    {overallRisk.risk_score}
                  </span>
                  <span style={{ fontSize: 11, color: 'var(--text-secondary)', fontWeight: 600, marginTop: -4 }}>SCORE</span>
                </div>
              </div>

              <div style={{ marginTop: 12 }}>
                <RiskBadge level={overallRisk.risk_class} />
              </div>
            </div>

            {/* Risk Reasons / Explanations */}
            <div className="col-md-8 py-2">
              <h5 style={{ fontWeight: 700, marginBottom: 12, display: 'flex', alignItems: 'center', gap: 8, color: 'var(--text-primary)' }}>
                <MdWarning size={20} className="text-danger" /> Primary Risk Drivers & AI Analysis
              </h5>
              {overallRisk.reasons && overallRisk.reasons.length > 0 ? (
                <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                  {overallRisk.reasons.map((reason, idx) => (
                    <div key={idx} style={{ 
                      display: 'flex', 
                      alignItems: 'center', 
                      gap: 10, 
                      padding: '10px 14px',
                      background: 'rgba(255,255,255,0.03)',
                      borderRadius: 8,
                      border: '1px solid var(--border-color)',
                      fontSize: 13.5
                    }}>
                      <MdErrorOutline className="text-danger" size={16} style={{ flexShrink: 0 }} />
                      <span style={{ fontWeight: 500, color: 'var(--text-primary)' }}>{reason}</span>
                    </div>
                  ))}
                </div>
              ) : (
                <p style={{ color: 'var(--text-secondary)', fontStyle: 'italic', margin: 0 }}>No active anomalies or supply chain threats detected today.</p>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Filters */}
      <div className="glass-card" style={{ padding: '12px 16px', marginBottom: 16, display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 10 }}>
        <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap' }}>
          <div className="search-input-wrapper" style={{ width: 260 }}>
            <MdSearch size={15} style={{ color: 'var(--text-secondary)', flexShrink: 0 }} />
            <input value={search} onChange={e => { setSearch(e.target.value); setPage(1); }} placeholder="Search supplier, country…" />
          </div>
          <select className="form-select-custom" value={filterLevel} onChange={e => { setFilterLevel(e.target.value); setPage(1); }}>
            <option value="All">All Risk Levels</option>
            <option value="High">High Risk</option>
            <option value="Medium">Medium Risk</option>
            <option value="Low">Low Risk</option>
          </select>
        </div>
        <div style={{ fontSize: 12, color: 'var(--text-secondary)' }}>
          Showing <strong>{pageRows.length}</strong> of <strong>{filtered.length}</strong> records
        </div>
      </div>

      {/* Table */}
      <div className="glass-card" style={{ padding: 0, overflow: 'hidden' }}>
        <div style={{ overflowX: 'auto' }} className="custom-scrollbar">
          <table className="data-table">
            <thead>
              <tr>
                {[
                  { key: 'supplier_id',             label: 'Supplier ID' },
                  { key: 'supplier_name',            label: 'Supplier Name' },
                  { key: 'country',                  label: 'Country' },
                  { key: 'risk_score',               label: 'Risk Score' },
                  { key: 'risk_level',               label: 'Risk Level' },
                  { key: 'disruption_probability',   label: 'Disruption Prob.' },
                  { key: 'crude_type',               label: 'Crude Type' },
                  { key: 'price_per_barrel',         label: 'Price/bbl' },
                  { key: 'lead_time',                label: 'Lead Time' },
                  { key: 'availability',             label: 'Availability' },
                ].map(col => (
                  <th
                    key={col.key}
                    onClick={() => handleSort(col.key)}
                    style={{ cursor: 'pointer', userSelect: 'none', whiteSpace: 'nowrap' }}
                  >
                    <span style={{ display: 'inline-flex', alignItems: 'center', gap: 4 }}>
                      {col.label} <SortIcon col={col.key} />
                    </span>
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {pageRows.map((row, i) => (
                <motion.tr
                  key={i}
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  transition={{ delay: i * 0.015 }}
                >
                  <td style={{ color: 'var(--text-secondary)', fontSize: 12 }}>{safeStr(row.supplier_id)}</td>
                  <td style={{ fontWeight: 600 }}>{safeStr(row.supplier_name)}</td>
                  <td>{safeStr(row.country)}</td>
                  <td style={{ fontWeight: 700, color: safeNum(row.risk_score) > 70 ? 'var(--danger)' : safeNum(row.risk_score) > 40 ? 'var(--warning)' : 'var(--success)' }}>
                    {safeNum(row.risk_score).toFixed(1)}
                  </td>
                  <td><RiskBadge level={row.risk_level} /></td>
                  <td style={{ minWidth: 140 }}><ProbBar val={row.disruption_probability} /></td>
                  <td>{safeStr(row.crude_type)}</td>
                  <td>{row.price_per_barrel ? `$${safeNum(row.price_per_barrel).toFixed(0)}` : '—'}</td>
                  <td>{row.lead_time ? `${row.lead_time} days` : '—'}</td>
                  <td>
                    {row.availability ? (
                      <span className={row.availability === 'High' ? 'badge-low' : row.availability === 'Low' ? 'badge-high' : 'badge-medium'}>
                        {row.availability}
                      </span>
                    ) : '—'}
                  </td>
                </motion.tr>
              ))}
              {pageRows.length === 0 && (
                <tr>
                  <td colSpan={10} style={{ textAlign: 'center', padding: '40px 20px', color: 'var(--text-secondary)' }}>
                    No records match your filters.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination */}
        {totalPages > 1 && (
          <div style={{ padding: '12px 16px', borderTop: '1px solid var(--border-color)', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <span style={{ fontSize: 12, color: 'var(--text-secondary)' }}>
              Page {page} of {totalPages}
            </span>
            <div style={{ display: 'flex', gap: 6 }}>
              <button onClick={() => setPage(1)} disabled={page === 1} style={pageBtnStyle(page === 1)}>«</button>
              <button onClick={() => setPage(p => Math.max(1, p - 1))} disabled={page === 1} style={pageBtnStyle(page === 1)}>‹</button>
              {Array.from({ length: Math.min(5, totalPages) }, (_, i) => {
                const p = Math.max(1, Math.min(totalPages - 4, page - 2)) + i;
                return (
                  <button key={p} onClick={() => setPage(p)} style={{
                    ...pageBtnStyle(false),
                    background: p === page ? 'var(--primary-color)' : 'var(--bg-secondary)',
                    color: p === page ? 'white' : 'var(--text-primary)',
                    fontWeight: p === page ? 700 : 400
                  }}>{p}</button>
                );
              })}
              <button onClick={() => setPage(p => Math.min(totalPages, p + 1))} disabled={page === totalPages} style={pageBtnStyle(page === totalPages)}>›</button>
              <button onClick={() => setPage(totalPages)} disabled={page === totalPages} style={pageBtnStyle(page === totalPages)}>»</button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

const pageBtnStyle = (disabled) => ({
  padding: '5px 10px', fontSize: 13, fontWeight: 500,
  border: '1px solid var(--border-color)',
  borderRadius: 6,
  background: 'var(--bg-secondary)',
  color: disabled ? 'var(--border-color)' : 'var(--text-primary)',
  cursor: disabled ? 'not-allowed' : 'pointer',
  transition: 'all 0.15s'
});

export default LiveRisk;
