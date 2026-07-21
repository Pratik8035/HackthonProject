import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { supplierApi } from '../services/supplierApi';
import { useAnalysis } from '../contexts/AnalysisContext';
import Loader from '../components/Loader';
import ErrorCard from '../components/ErrorCard';
import {
  MdCheckCircle, MdWarning, MdInfo, MdCompareArrows, MdChevronRight,
  MdOutlineLocationOn, MdSpeed, MdInventory, MdSchedule, MdTrendingUp
} from 'react-icons/md';

const safeNum = (v, fallback = 0) => {
  const n = parseFloat(v);
  return isNaN(n) ? fallback : n;
};

const AlternativeSupplier = () => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [currentSuppliers, setCurrentSuppliers] = useState([]);
  const [selectedId, setSelectedId] = useState('');
  const [result, setResult] = useState(null);
  const [recLoading, setRecLoading] = useState(false);
  const [compareList, setCompareList] = useState([]);

  const { setCurrentSupplier, setSelectedAlternative, liveRiskResult, scenarioEffects } = useAnalysis();
  const navigate = useNavigate();

  // Risk score from Live Risk page — used to bias supplier ranking
  const liveRiskScore = liveRiskResult?.risk_score ?? null;

  useEffect(() => {
    supplierApi.getCurrentSuppliers()
      .then(r => setCurrentSuppliers(r.data || []))
      .catch(err => setError(err))
      .finally(() => setLoading(false));
  }, []);

  const handleSelectCurrent = async (supplierId) => {
    setSelectedId(supplierId);
    setResult(null);
    setCompareList([]);
    if (!supplierId) return;

    const supplierObj = currentSuppliers.find(s => s.supplier_id === supplierId || s.id === supplierId);
    setCurrentSupplier(supplierObj || { name: supplierId });

    setRecLoading(true);
    try {
      // Pass live risk score so the backend uses the current risk
      // environment (from Live Risk page) to drive replacement logic
      // and alternative ranking instead of stale dataset averages.
      const payload = { current_supplier_id: supplierId };
      if (liveRiskScore != null) payload.risk_score = liveRiskScore;
      const res = await supplierApi.recommendSupplier(payload);
      setResult(res.data);
    } catch (err) {
      setError(err);
    } finally {
      setRecLoading(false);
    }
  };

  const handleSelectAlt = (alt) => {
    setSelectedAlternative({ name: alt.supplier_name, supplier_name: alt.supplier_name, country: alt.country });
    navigate('/route-optimization');
  };

  const toggleCompare = (name) => {
    setCompareList(prev =>
      prev.includes(name) ? prev.filter(n => n !== name) : [...prev, name].slice(0, 2)
    );
  };

  const getRiskColor = (score) => {
    if (score > 70) return 'red';
    if (score > 40) return 'amber';
    return 'green';
  };

  if (loading) return <div className="page-container"><Loader message="Loading Supplier Database…" /></div>;
  if (error)   return <div className="page-container"><ErrorCard error={error} onRetry={() => window.location.reload()} /></div>;

  const rankedSuppliers = result?.['Top 4 Ranked Suppliers'] || [];
  const riskAssessment   = result?.['Risk Assessment'] || {};
  const riskScore        = safeNum(riskAssessment['Risk Score']);
  const riskColor        = getRiskColor(riskScore);

  return (
    <div className="page-container">
      {/* Header */}
      <div style={{ marginBottom: 20 }}>
        <h1 className="page-title">Alternative Supplier Recommendation</h1>
        <p className="page-subtitle">XGBoost-powered supplier ranking based on risk, capacity, reliability, and lead time.</p>
        {/* Context chips — show which upstream data is feeding this page */}
        <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', marginTop: 8 }}>
          {liveRiskScore != null && (
            <div style={{
              display: 'inline-flex', alignItems: 'center', gap: 6,
              padding: '5px 12px', borderRadius: 20, fontSize: 12, fontWeight: 600,
              background: liveRiskScore > 70 ? 'rgba(238,93,80,0.1)' : liveRiskScore > 40 ? 'rgba(255,206,32,0.1)' : 'rgba(5,205,153,0.1)',
              border: `1px solid ${liveRiskScore > 70 ? 'rgba(238,93,80,0.3)' : liveRiskScore > 40 ? 'rgba(255,206,32,0.3)' : 'rgba(5,205,153,0.3)'}`,
              color: liveRiskScore > 70 ? 'var(--danger)' : liveRiskScore > 40 ? 'var(--warning)' : 'var(--success)',
            }}>
              <MdInfo size={13} />
              Live Risk Score: {liveRiskScore} ({liveRiskResult?.risk_class})
            </div>
          )}
          {scenarioEffects && (
            <div style={{
              display: 'inline-flex', alignItems: 'center', gap: 6,
              padding: '5px 12px', borderRadius: 20, fontSize: 12, fontWeight: 600,
              background: 'rgba(37,99,235,0.08)', border: '1px solid rgba(37,99,235,0.25)',
              color: 'var(--primary-color)',
            }}>
              <MdInfo size={13} />
              Scenario Context: {scenarioEffects.scenario_name} · Supply Drop {scenarioEffects.supply_reduction_pct}%
            </div>
          )}
          {liveRiskScore == null && !scenarioEffects && (
            <div style={{
              display: 'inline-flex', alignItems: 'center', gap: 6,
              padding: '5px 12px', borderRadius: 20, fontSize: 12, fontWeight: 500,
              background: 'var(--bg-secondary)', border: '1px solid var(--border-color)',
              color: 'var(--text-secondary)',
            }}>
              <MdInfo size={13} />
              Tip: Run Live Risk first for risk-weighted recommendations
            </div>
          )}
        </div>
      </div>

      {/* Supplier selector */}
      <div className="glass-card" style={{ marginBottom: 20 }}>
        <label style={{ fontSize: 11, fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.5px', color: 'var(--text-secondary)', display: 'block', marginBottom: 8 }}>
          Select Current Supplier to Analyze
        </label>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12, flexWrap: 'wrap' }}>
          <select
            className="form-select-custom"
            value={selectedId}
            onChange={e => handleSelectCurrent(e.target.value)}
            style={{ minWidth: 320 }}
          >
            <option value="">— Choose a Supplier —</option>
            {currentSuppliers.map((s, i) => (
              <option key={i} value={s.supplier_id || s.id}>
                {s.supplier_name} ({s.country}) — ${safeNum(s.price_per_barrel).toFixed(0)}/bbl
              </option>
            ))}
          </select>
          {recLoading && (
            <span style={{ display: 'flex', alignItems: 'center', gap: 6, color: 'var(--text-secondary)', fontSize: 13 }}>
              <span className="spinner-border spinner-border-sm text-primary" role="status" />
              Running AI ranking model…
            </span>
          )}
        </div>
      </div>

      {/* Risk Summary + Context */}
      {result && !recLoading && (
        <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }}>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16, marginBottom: 20 }}>
            {/* Current Supplier Risk */}
            <div className="glass-card" style={{ borderLeft: `4px solid var(--${riskColor === 'red' ? 'danger' : riskColor === 'amber' ? 'warning' : 'success'})` }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 12 }}>
                <MdWarning size={18} color={riskColor === 'red' ? 'var(--danger)' : riskColor === 'amber' ? 'var(--warning)' : 'var(--success)'} />
                <span style={{ fontWeight: 700, fontSize: 14 }}>Current Supplier Risk Analysis</span>
              </div>
              <div style={{ fontSize: 17, fontWeight: 800, marginBottom: 4 }}>{result['Current Supplier']}</div>
              <div style={{ fontSize: 13, color: 'var(--text-secondary)', marginBottom: 14 }}>
                <MdOutlineLocationOn size={14} style={{ verticalAlign: 'middle' }} /> {result['Current Supplier Country']}
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8 }}>
                {[
                  { label: 'Risk Score', val: riskAssessment['Risk Score'], accent: riskColor === 'red' ? 'var(--danger)' : 'var(--warning)' },
                  { label: 'Risk Level', val: riskAssessment['Risk Level'] },
                  { label: 'Disruption Prob.', val: riskAssessment['Disruption Probability'] },
                  { label: 'Supply Shortage', val: riskAssessment['Supply Shortage'] },
                  { label: 'Production Loss', val: riskAssessment['Production Loss'] },
                  { label: 'Decision', val: result.Decision?.['Replacement Required'] === 'Yes' ? '⚠ Replace' : '✓ Stable' },
                ].map(({ label, val, accent }) => (
                  <div key={label} style={{ background: 'var(--bg-primary)', borderRadius: 8, padding: '8px 12px' }}>
                    <div style={{ fontSize: 10, fontWeight: 600, color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.4px', marginBottom: 2 }}>{label}</div>
                    <div style={{ fontSize: 14, fontWeight: 700, color: accent || 'var(--text-primary)' }}>{val || '—'}</div>
                  </div>
                ))}
              </div>
            </div>

            {/* AI Context */}
            <div className="glass-card" style={{ borderLeft: '4px solid var(--primary-color)' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 12 }}>
                <MdInfo size={18} color="var(--primary-color)" />
                <span style={{ fontWeight: 700, fontSize: 14 }}>AI Decision Context</span>
              </div>
              <p style={{ fontSize: 13, color: 'var(--text-secondary)', lineHeight: 1.6, marginBottom: 16 }}>
                {riskAssessment['Conclusion'] || 'Based on the analysis, alternative suppliers are recommended.'}
              </p>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10 }}>
                <div style={{ background: 'rgba(37,99,235,0.07)', borderRadius: 10, padding: '12px 14px', textAlign: 'center' }}>
                  <div style={{ fontSize: 10, fontWeight: 600, color: 'var(--text-secondary)', textTransform: 'uppercase', marginBottom: 4 }}>XGBoost Score</div>
                  <div style={{ fontSize: 20, fontWeight: 800, color: 'var(--primary-color)' }}>
                    {rankedSuppliers.length > 0
                      ? `${Math.min(100, Math.round(safeNum(rankedSuppliers[0]?.ranking_score) * 100))}%`
                      : '—'}
                  </div>
                </div>
                <div style={{ background: 'rgba(16,185,129,0.07)', borderRadius: 10, padding: '12px 14px', textAlign: 'center' }}>
                  <div style={{ fontSize: 10, fontWeight: 600, color: 'var(--text-secondary)', textTransform: 'uppercase', marginBottom: 4 }}>Risk Level</div>
                  <div style={{ fontSize: 20, fontWeight: 800, color: riskColor === 'red' ? 'var(--danger)' : riskColor === 'amber' ? 'var(--warning)' : 'var(--success)' }}>
                    {riskAssessment['Risk Level'] || '—'}
                  </div>
                </div>
                <div style={{ background: 'rgba(14,165,233,0.07)', borderRadius: 10, padding: '12px 14px', textAlign: 'center' }}>
                  <div style={{ fontSize: 10, fontWeight: 600, color: 'var(--text-secondary)', textTransform: 'uppercase', marginBottom: 4 }}>Disruption Prob.</div>
                  <div style={{ fontSize: 20, fontWeight: 800, color: 'var(--info)' }}>
                    {riskAssessment['Disruption Probability'] || '—'}
                  </div>
                </div>
                <div style={{ background: 'rgba(245,158,11,0.07)', borderRadius: 10, padding: '12px 14px', textAlign: 'center' }}>
                  <div style={{ fontSize: 10, fontWeight: 600, color: 'var(--text-secondary)', textTransform: 'uppercase', marginBottom: 4 }}>Top Picks Shown</div>
                  <div style={{ fontSize: 20, fontWeight: 800, color: 'var(--warning)' }}>{rankedSuppliers.length}</div>
                </div>
              </div>
            </div>
          </div>

          {/* Ranked Suppliers Grid */}
          {rankedSuppliers.length > 0 && (
            <>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 14 }}>
                <h2 style={{ fontSize: 16, fontWeight: 700 }}>
                  <MdCompareArrows style={{ verticalAlign: 'middle', color: 'var(--primary-color)', marginRight: 6 }} />
                  Top {rankedSuppliers.length} AI-Recommended Alternatives
                </h2>
                {compareList.length >= 2 && (
                  <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                    <span style={{ fontSize: 12, color: 'var(--text-secondary)', fontWeight: 500 }}>
                      {compareList.length} suppliers selected
                    </span>
                    <button
                      className="btn-primary-gradient"
                      onClick={() => {
                        const el = document.getElementById('comparison-panel');
                        if (el) el.scrollIntoView({ behavior: 'smooth' });
                      }}
                    >
                      <MdCompareArrows size={15} style={{ marginRight: 4 }} />
                      View Comparison ↓
                    </button>
                    <button
                      onClick={() => setCompareList([])}
                      style={{ padding: '8px 12px', fontSize: 12, borderRadius: 8, border: '1px solid var(--border-color)', background: 'transparent', color: 'var(--text-secondary)', cursor: 'pointer', fontWeight: 600 }}
                    >
                      Clear
                    </button>
                  </div>
                )}
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: 16 }}>
                {rankedSuppliers.map((alt, idx) => {
                  const isCompared = compareList.includes(alt.supplier_name);
                  const score = safeNum(alt.ranking_score);
                  const pct = Math.min(100, Math.round(score * 100));

                  return (
                    <motion.div
                      key={idx}
                      className="glass-card hover-lift"
                      style={{
                        padding: 0, overflow: 'hidden',
                        border: idx === 0 ? '1.5px solid var(--primary-color)' : 'var(--glass-border)',
                        display: 'flex', flexDirection: 'column'
                      }}
                      initial={{ opacity: 0, y: 16 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: idx * 0.07 }}
                    >
                      {/* Rank Header */}
                      <div style={{
                        background: idx === 0 ? 'var(--primary-gradient)' : 'var(--bg-primary)',
                        padding: '10px 16px',
                        display: 'flex', alignItems: 'center', justifyContent: 'space-between'
                      }}>
                        <span style={{
                          fontSize: 11, fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.5px',
                          color: idx === 0 ? 'rgba(255,255,255,0.9)' : 'var(--text-secondary)'
                        }}>
                          {idx === 0 ? '🏆 Best Match' : `Rank #${alt.rank || idx + 1}`}
                        </span>
                        <span style={{
                          fontSize: 13, fontWeight: 800,
                          color: idx === 0 ? 'white' : 'var(--primary-color)'
                        }}>
                          {pct}% match
                        </span>
                      </div>

                      {/* Body */}
                      <div style={{ padding: 16, flex: 1, display: 'flex', flexDirection: 'column', gap: 12 }}>
                        <div>
                          <div style={{ fontSize: 16, fontWeight: 700, marginBottom: 2 }}>{alt.supplier_name}</div>
                          <div style={{ fontSize: 12, color: 'var(--text-secondary)' }}>
                            <MdOutlineLocationOn size={12} style={{ verticalAlign: 'middle' }} /> {alt.country}
                            {alt.supplier_id && <span style={{ marginLeft: 6, opacity: 0.7 }}>· {alt.supplier_id}</span>}
                          </div>
                        </div>

                        {/* Score bar */}
                        <div>
                          <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 11, fontWeight: 600, color: 'var(--text-secondary)', marginBottom: 4 }}>
                            <span>Recommendation Score</span>
                            <span style={{ color: 'var(--primary-color)' }}>{score.toFixed(4)}</span>
                          </div>
                          <div className="progress-slim">
                            <div className="progress-slim-bar" style={{ width: `${pct}%` }} />
                          </div>
                        </div>

                        {/* Reason */}
                        <div style={{ background: 'var(--bg-primary)', borderRadius: 8, padding: '8px 10px' }}>
                          <div style={{ fontSize: 10, fontWeight: 600, color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.4px', marginBottom: 3 }}>AI Reasoning</div>
                          <div style={{ fontSize: 12, color: 'var(--text-primary)', lineHeight: 1.5 }}>
                            {alt.Reason || 'Optimal balance of cost, risk, and capacity.'}
                          </div>
                        </div>

                        {/* Action Buttons */}
                        <div style={{ display: 'flex', gap: 8, marginTop: 'auto' }}>
                          <button
                            onClick={() => toggleCompare(alt.supplier_name)}
                            style={{
                              flex: 1, padding: '8px 12px', fontSize: 12, fontWeight: 600,
                              borderRadius: 8, cursor: 'pointer', transition: 'all 0.15s',
                              border: `1.5px solid ${isCompared ? 'var(--primary-color)' : 'var(--border-color)'}`,
                              background: isCompared ? 'rgba(37,99,235,0.08)' : 'var(--bg-secondary)',
                              color: isCompared ? 'var(--primary-color)' : 'var(--text-secondary)'
                            }}
                          >
                            {isCompared ? '✓ Comparing' : 'Compare'}
                          </button>
                          <button
                            className="btn-primary-gradient"
                            onClick={() => handleSelectAlt(alt)}
                            style={{ flex: 1, padding: '8px 12px', fontSize: 12, display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 4 }}
                          >
                            Select <MdChevronRight size={16} />
                          </button>
                        </div>
                      </div>
                    </motion.div>
                  );
                })}
              </div>

              {/* Side-by-side Comparison Panel */}
              {compareList.length >= 2 && (() => {
                const suppA = rankedSuppliers.find(s => s.supplier_name === compareList[0]);
                const suppB = rankedSuppliers.find(s => s.supplier_name === compareList[1]);
                if (!suppA || !suppB) return null;

                const scoreA = safeNum(suppA.ranking_score);
                const scoreB = safeNum(suppB.ranking_score);

                const metrics = [
                  { label: 'Rank', keyA: suppA.rank || 1, keyB: suppB.rank || 2, lowerIsBetter: true },
                  { label: 'Recommendation Score', keyA: scoreA.toFixed(4), keyB: scoreB.toFixed(4), numA: scoreA, numB: scoreB, lowerIsBetter: false },
                  { label: 'Country', keyA: suppA.country, keyB: suppB.country, noCompare: true },
                  { label: 'AI Reasoning', keyA: suppA.Reason || '—', keyB: suppB.Reason || '—', noCompare: true, small: true },
                ];

                return (
                  <motion.div
                    id="comparison-panel"
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    style={{ marginTop: 28 }}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 16 }}>
                      <MdCompareArrows size={20} color="var(--primary-color)" />
                      <h2 style={{ fontSize: 16, fontWeight: 700, margin: 0 }}>Side-by-Side Comparison</h2>
                      <span style={{ background: 'rgba(37,99,235,0.1)', color: 'var(--primary-color)', fontSize: 11, fontWeight: 700, padding: '3px 10px', borderRadius: 100 }}>
                        AI Analysis
                      </span>
                    </div>

                    <div className="glass-card" style={{ padding: 0, overflow: 'hidden' }}>
                      {/* Header row */}
                      <div style={{ display: 'grid', gridTemplateColumns: '160px 1fr 1fr', background: 'var(--bg-primary)', borderBottom: '1px solid var(--border-color)' }}>
                        <div style={{ padding: '14px 16px', fontSize: 11, fontWeight: 700, textTransform: 'uppercase', color: 'var(--text-secondary)', letterSpacing: '0.5px' }}>Metric</div>
                        {[suppA, suppB].map((s, i) => (
                          <div key={i} style={{ padding: '14px 16px', borderLeft: '1px solid var(--border-color)', background: i === 0 ? 'rgba(37,99,235,0.04)' : 'transparent' }}>
                            <div style={{ fontWeight: 800, fontSize: 14, marginBottom: 2 }}>{s.supplier_name}</div>
                            <div style={{ fontSize: 11, color: 'var(--text-secondary)' }}>
                              {i === 0 ? '🏆 ' : ''}{Math.min(100, Math.round(safeNum(s.ranking_score) * 100))}% match · Rank #{s.rank || i + 1}
                            </div>
                          </div>
                        ))}
                      </div>

                      {/* Metric rows */}
                      {metrics.map((m, mi) => {
                        const numA = m.numA !== undefined ? m.numA : safeNum(m.keyA);
                        const numB = m.numB !== undefined ? m.numB : safeNum(m.keyB);
                        const aWins = !m.noCompare && (m.lowerIsBetter ? numA < numB : numA > numB);
                        const bWins = !m.noCompare && (m.lowerIsBetter ? numB < numA : numB > numA);

                        return (
                          <div key={mi} style={{ display: 'grid', gridTemplateColumns: '160px 1fr 1fr', borderBottom: mi < metrics.length - 1 ? '1px solid var(--border-color)' : 'none' }}>
                            <div style={{ padding: '12px 16px', fontSize: 11, fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.4px', color: 'var(--text-secondary)', display: 'flex', alignItems: 'center' }}>
                              {m.label}
                            </div>
                            {[{ val: m.keyA, wins: aWins }, { val: m.keyB, wins: bWins }].map((cell, ci) => (
                              <div key={ci} style={{
                                padding: '12px 16px',
                                borderLeft: '1px solid var(--border-color)',
                                background: cell.wins ? 'rgba(16,185,129,0.06)' : ci === 0 ? 'rgba(37,99,235,0.02)' : 'transparent',
                                display: 'flex', alignItems: 'center', gap: 6
                              }}>
                                {cell.wins && <MdCheckCircle size={14} color="var(--success)" style={{ flexShrink: 0 }} />}
                                <span style={{
                                  fontSize: m.small ? 12 : 13,
                                  fontWeight: cell.wins ? 700 : 500,
                                  color: cell.wins ? 'var(--success)' : 'var(--text-primary)',
                                  lineHeight: 1.4
                                }}>
                                  {cell.val}
                                </span>
                              </div>
                            ))}
                          </div>
                        );
                      })}

                      {/* Action footer */}
                      <div style={{ display: 'grid', gridTemplateColumns: '160px 1fr 1fr', background: 'var(--bg-primary)', borderTop: '1px solid var(--border-color)' }}>
                        <div style={{ padding: '12px 16px' }} />
                        {[suppA, suppB].map((s, i) => (
                          <div key={i} style={{ padding: '12px 16px', borderLeft: '1px solid var(--border-color)' }}>
                            <button
                              className="btn-primary-gradient"
                              onClick={() => handleSelectAlt(s)}
                              style={{ width: '100%', padding: '9px 14px', fontSize: 12, display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 4 }}
                            >
                              Select {s.supplier_name.split(' ').slice(-1)} <MdChevronRight size={15} />
                            </button>
                          </div>
                        ))}
                      </div>
                    </div>
                  </motion.div>
                );
              })()}
            </>
          )}

          {rankedSuppliers.length === 0 && result.Decision?.['Replacement Required'] === 'No' && (
            <div className="glass-card" style={{ textAlign: 'center', padding: '40px 24px' }}>
              <MdCheckCircle size={48} color="var(--success)" style={{ marginBottom: 12 }} />
              <h3 style={{ fontWeight: 700, marginBottom: 8 }}>Current Supplier is Safe</h3>
              <p style={{ color: 'var(--text-secondary)', maxWidth: 400, margin: '0 auto' }}>
                The AI analysis determined no replacement is needed. The supplier meets all risk thresholds.
              </p>
            </div>
          )}
        </motion.div>
      )}

      {/* Empty state */}
      {!result && !recLoading && !selectedId && (
        <div className="empty-state">
          <div className="empty-state-icon">
            <MdCompareArrows size={28} />
          </div>
          <h3 style={{ fontSize: 16, fontWeight: 600, marginBottom: 6 }}>Select a Supplier to Begin</h3>
          <p style={{ maxWidth: 380, fontSize: 13 }}>
            Choose a current supplier from the dropdown above. The AI will rank the best alternative suppliers using XGBoost scoring.
          </p>
        </div>
      )}
    </div>
  );
};

export default AlternativeSupplier;
