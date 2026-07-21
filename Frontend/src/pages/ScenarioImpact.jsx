import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { scenarioApi } from '../services/scenarioApi';
import { useAnalysis } from '../contexts/AnalysisContext';
import Loader from '../components/Loader';
import ErrorCard from '../components/ErrorCard';
import {
  ResponsiveContainer, BarChart, Bar, XAxis, YAxis, CartesianGrid,
  Tooltip as RechartsTooltip, Cell
} from 'recharts';
import { MdPlayArrow, MdWarning, MdShowChart, MdOutlineSpeed, MdTimeline, MdInfo } from 'react-icons/md';

const safeNum = (v) => { const n = parseFloat(v); return isNaN(n) ? 0 : n; };

const BLUE_PALETTE = ['#2563eb', '#3b82f6', '#60a5fa', '#93c5fd', '#bfdbfe'];

const MetricCard = ({ label, value, unit = '', color = 'var(--primary-color)' }) => (
  <div style={{ background: 'var(--bg-primary)', borderRadius: 10, padding: '14px 16px', textAlign: 'center', border: '1px solid var(--border-color)' }}>
    <div style={{ fontSize: 10, fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.5px', color: 'var(--text-secondary)', marginBottom: 6 }}>{label}</div>
    <div style={{ fontSize: 22, fontWeight: 800, color }}>
      {value}<span style={{ fontSize: 13, fontWeight: 500, color: 'var(--text-secondary)', marginLeft: 4 }}>{unit}</span>
    </div>
  </div>
);

const ScenarioImpact = () => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [scenarios, setScenarios] = useState([]);
  const [selected, setSelected] = useState(null);
  const [effects, setEffects] = useState(null);
  const [simLoading, setSimLoading] = useState(false);
  const [simError, setSimError] = useState(null);

  // Pull live risk score from context so scenario probabilities are
  // weighted by the current risk assessment result.
  const { liveRiskResult, setScenarioEffects } = useAnalysis();
  const liveRiskScore = liveRiskResult?.risk_score ?? null;

  const fetchScenarios = async () => {
    setLoading(true);
    setError(null);
    try {
      // Pass live risk score so the backend scales scenario probabilities
      // against the current risk environment (e.g. HIGH risk inflates
      // geopolitical scenario probabilities).
      const res = await scenarioApi.listScenarios(liveRiskScore);
      const list = Array.isArray(res.data?.scenarios) ? res.data.scenarios : [];
      setScenarios(list);
    } catch (err) {
      setError(err);
    } finally {
      setLoading(false);
    }
  };

  // Re-fetch scenarios whenever live risk score changes
  useEffect(() => { fetchScenarios(); }, [liveRiskScore]);

  const handleSimulate = async () => {
    if (!selected) return;
    setSimLoading(true);
    setSimError(null);
    setEffects(null);
    try {
      const res = await scenarioApi.runEffects(
        selected.scenario_id ?? selected['Scenario ID'],
        selected.scenario_name ?? selected['Scenario Name'],
        selected.probability ?? selected.Probability ?? 0.5
      );
      const effectData = res.data || {};
      setEffects(effectData);
      // Save effects to shared context so AlternativeSupplier page can
      // use supply_reduction_pct, estimated_shipping_delay_days, etc.
      setScenarioEffects(effectData);
    } catch (err) {
      setSimError(err?.message || 'Failed to simulate scenario');
    } finally {
      setSimLoading(false);
    }
  };

  if (loading) return <div className="page-container"><Loader message="Loading Scenario Models…" /></div>;
  if (error)   return <div className="page-container"><ErrorCard error={error} onRetry={fetchScenarios} /></div>;

  // Bar chart data
  const impactData = effects ? [
    { name: 'Supply Drop',    value: safeNum(effects.supply_reduction_pct),          label: '%' },
    { name: 'Cost Jump',      value: safeNum(effects.transportation_cost_increase_pct), label: '%' },
    { name: 'Oil Price Rise', value: safeNum(effects.brent_oil_price_increase_pct),  label: '%' },
    { name: 'Demand Met',     value: safeNum(effects.demand_fulfillment_pct),         label: '%' },
  ].filter(d => d.value > 0) : [];



  return (
    <div className="page-container">
      <div style={{ marginBottom: 20 }}>
        <h1 className="page-title">Scenario Impact Analysis</h1>
        <p className="page-subtitle">Simulate global supply chain disruptions using machine learning downstream-effects models.</p>
        {liveRiskScore != null && (
          <div style={{
            display: 'inline-flex', alignItems: 'center', gap: 8, marginTop: 8,
            padding: '6px 14px', borderRadius: 20, fontSize: 12, fontWeight: 600,
            background: liveRiskScore > 70 ? 'rgba(238,93,80,0.1)' : liveRiskScore > 40 ? 'rgba(255,206,32,0.1)' : 'rgba(5,205,153,0.1)',
            border: `1px solid ${liveRiskScore > 70 ? 'rgba(238,93,80,0.3)' : liveRiskScore > 40 ? 'rgba(255,206,32,0.3)' : 'rgba(5,205,153,0.3)'}`,
            color: liveRiskScore > 70 ? 'var(--danger)' : liveRiskScore > 40 ? 'var(--warning)' : 'var(--success)',
          }}>
            <MdInfo size={14} />
            Scenario probabilities weighted by Live Risk Score: {liveRiskScore} ({liveRiskResult?.risk_class})
            {liveRiskResult?.scenario && <span style={{ opacity: 0.7 }}> · {liveRiskResult.scenario}</span>}
          </div>
        )}
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '280px 1fr', gap: 16, minHeight: 560 }}>
        {/* Left Panel */}
        <div className="glass-card" style={{ display: 'flex', flexDirection: 'column', padding: 0, overflow: 'hidden' }}>
          <div style={{ padding: '14px 16px', borderBottom: '1px solid var(--border-color)', display: 'flex', alignItems: 'center', gap: 8 }}>
            <MdWarning size={16} color="var(--warning)" />
            <span style={{ fontWeight: 700, fontSize: 14 }}>Disruption Scenarios</span>
            <span style={{ marginLeft: 'auto', background: 'rgba(37,99,235,0.1)', color: 'var(--primary-color)', borderRadius: 100, padding: '2px 8px', fontSize: 11, fontWeight: 700 }}>
              {scenarios.length}
            </span>
          </div>

          <div style={{ flex: 1, overflowY: 'auto', padding: '8px 0' }} className="custom-scrollbar">
            {scenarios.map((s, idx) => {
              const probVal = safeNum(s.probability ?? s.Probability);
              const probPct = probVal <= 1 ? probVal * 100 : probVal;
              const severity = (s.severity || s.Severity || '').toLowerCase();
              const isSelected = selected === s;
              return (
                <div
                  key={idx}
                  onClick={() => { setSelected(s); setEffects(null); setSimError(null); }}
                  style={{
                    padding: '10px 16px', margin: '2px 8px', borderRadius: 8, cursor: 'pointer',
                    border: `1px solid ${isSelected ? 'var(--primary-color)' : 'transparent'}`,
                    background: isSelected ? 'rgba(37,99,235,0.08)' : 'transparent',
                    transition: 'all 0.15s'
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 5 }}>
                    <div style={{ fontWeight: 600, fontSize: 13, color: isSelected ? 'var(--primary-color)' : 'var(--text-primary)', flex: 1, paddingRight: 8, lineHeight: 1.3 }}>
                      {s.scenario_name || s['Scenario Name']}
                    </div>
                    <span className={severity === 'high' ? 'badge-high' : 'badge-medium'} style={{ flexShrink: 0 }}>
                      {s.severity || s.Severity}
                    </span>
                  </div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                    <div style={{ flex: 1, height: 4, background: 'var(--border-color)', borderRadius: 100 }}>
                      <div style={{ width: `${probPct}%`, height: '100%', borderRadius: 100, background: severity === 'high' ? 'var(--danger)' : 'var(--primary-color)' }} />
                    </div>
                    <span style={{ fontSize: 11, fontWeight: 700, color: severity === 'high' ? 'var(--danger)' : 'var(--primary-color)', minWidth: 34, textAlign: 'right' }}>
                      {probPct.toFixed(1)}%
                    </span>
                  </div>
                </div>
              );
            })}
            {scenarios.length === 0 && (
              <div style={{ padding: 24, textAlign: 'center', color: 'var(--text-secondary)', fontSize: 13 }}>
                No scenario models found.
              </div>
            )}
          </div>

          <div style={{ padding: '12px 16px', borderTop: '1px solid var(--border-color)' }}>
            <button
              className="btn-primary-gradient"
              style={{ width: '100%', display: 'flex', justifyContent: 'center', alignItems: 'center', gap: 8, padding: '10px 16px', fontSize: 13 }}
              disabled={!selected || simLoading}
              onClick={handleSimulate}
            >
              {simLoading ? (
                <><span className="spinner-border spinner-border-sm" role="status" /> Simulating…</>
              ) : (
                <><MdPlayArrow size={18} /> Simulate Scenario</>
              )}
            </button>
          </div>
        </div>

        {/* Right Panel */}
        <div className="glass-card" style={{ padding: 0, overflow: 'hidden', display: 'flex', flexDirection: 'column' }}>
          {simLoading ? (
            <div style={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', gap: 12 }}>
              <div className="spinner-grow text-primary" style={{ width: '2.5rem', height: '2.5rem' }} role="status" />
              <div style={{ fontWeight: 700, fontSize: 15 }}>Running Predictive Model…</div>
              <div style={{ color: 'var(--text-secondary)', fontSize: 13 }}>Calculating downstream supply chain effects.</div>
            </div>
          ) : simError ? (
            <div style={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', padding: 32 }}>
              <div style={{ color: 'var(--danger)', fontWeight: 700, marginBottom: 8 }}>Simulation Error</div>
              <div style={{ color: 'var(--text-secondary)', fontSize: 13 }}>{simError}</div>
              <button className="btn-primary-gradient" style={{ marginTop: 16 }} onClick={handleSimulate}>Retry</button>
            </div>
          ) : effects ? (
            <AnimatePresence>
              <motion.div style={{ flex: 1, overflowY: 'auto', padding: 20 }} className="custom-scrollbar" initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
                {/* Header */}
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16, flexWrap: 'wrap', gap: 8 }}>
                  <div style={{ fontWeight: 700, fontSize: 16, display: 'flex', alignItems: 'center', gap: 8 }}>
                    <MdShowChart color="var(--primary-color)" />
                    Simulation Results: {selected?.scenario_name || selected?.['Scenario Name']}
                  </div>
                  <span
                    className={
                      String(selected?.severity || '').toLowerCase() === 'high'
                        ? 'badge-high'
                        : String(selected?.severity || '').toLowerCase() === 'low'
                        ? 'badge-low'
                        : 'badge-medium'
                    }
                    style={{ fontSize: 12 }}
                  >
                    Severity: {selected?.severity || effects.overall_risk || 'N/A'}
                  </span>
                </div>

                {/* Metric Cards */}
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 10, marginBottom: 20 }}>
                  <MetricCard label="Expected Delay" value={safeNum(effects.estimated_shipping_delay_days).toFixed(1)} unit="Days" color="var(--danger)" />
                  <MetricCard label="Extra Transit" value={safeNum(effects.extra_transit_time_days).toFixed(1)} unit="Days" color="var(--warning)" />
                  <MetricCard label="Inventory Buffer" value={safeNum(effects.inventory_remaining_days).toFixed(1)} unit="Days" color="var(--info)" />
                  <MetricCard label="Supply Drop" value={safeNum(effects.supply_reduction_pct).toFixed(1)} unit="%" color="var(--danger)" />
                  <MetricCard label="Demand Met" value={safeNum(effects.demand_fulfillment_pct).toFixed(1)} unit="%" color="var(--success)" />
                  <MetricCard label="Supplier Availability" value={safeNum(effects.supplier_availability_pct).toFixed(1)} unit="%" color="var(--primary-color)" />
                </div>

                {/* Charts */}
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
                  <div style={{ background: 'var(--bg-primary)', borderRadius: 12, padding: 16, border: '1px solid var(--border-color)' }}>
                    <div style={{ fontWeight: 600, fontSize: 13, marginBottom: 12 }}>Impact Distribution (%)</div>
                    <div style={{ height: 220 }}>
                      <ResponsiveContainer width="100%" height="100%">
                        <BarChart data={impactData} margin={{ top: 5, right: 10, left: -20, bottom: 5 }}>
                          <CartesianGrid strokeDasharray="3 3" opacity={0.08} vertical={false} />
                          <XAxis dataKey="name" tick={{ fontSize: 11 }} stroke="var(--text-secondary)" />
                          <YAxis tickFormatter={v => `${v}%`} stroke="var(--text-secondary)" tick={{ fontSize: 11 }} />
                          <RechartsTooltip formatter={v => `${v.toFixed(1)}%`} contentStyle={{ background: 'var(--bg-secondary)', border: '1px solid var(--border-color)', borderRadius: 8, fontSize: 12 }} />
                          <Bar dataKey="value" radius={[4, 4, 0, 0]}>
                            {impactData.map((_, i) => <Cell key={i} fill={BLUE_PALETTE[i % BLUE_PALETTE.length]} />)}
                          </Bar>
                        </BarChart>
                      </ResponsiveContainer>
                    </div>
                  </div>

                  <div style={{ background: 'var(--bg-primary)', borderRadius: 12, padding: 16, border: '1px solid var(--border-color)', display: 'flex', flexDirection: 'column', height: '100%' }}>
                    <div style={{ fontWeight: 600, fontSize: 13, marginBottom: 16, display: 'flex', alignItems: 'center', gap: 6 }}>
                      <MdTimeline color="var(--primary-color)" size={18} /> Scenario Impact Profile
                    </div>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: 12, flex: 1, justifyContent: 'center' }}>
                      {[
                        { label: 'Supply Reduction', val: safeNum(effects.supply_reduction_pct), color: 'var(--danger)' },
                        { label: 'Transportation Cost Increase', val: safeNum(effects.transportation_cost_increase_pct), color: 'var(--warning)' },
                        { label: 'Brent Oil Price Increase', val: safeNum(effects.brent_oil_price_increase_pct), color: 'var(--warning)' },
                        { label: 'Supplier Availability', val: safeNum(effects.supplier_availability_pct), color: 'var(--primary-color)' },
                        { label: 'Demand Fulfillment', val: safeNum(effects.demand_fulfillment_pct), color: 'var(--success)' },
                      ].map((item, idx) => (
                        <div key={idx}>
                          <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 11, fontWeight: 600, marginBottom: 4, color: 'var(--text-primary)' }}>
                            <span>{item.label}</span>
                            <span style={{ color: item.color }}>{item.val.toFixed(0)}%</span>
                          </div>
                          <div style={{ height: 6, background: 'var(--border-color)', borderRadius: 100, overflow: 'hidden' }}>
                            <div style={{ 
                              width: `${Math.min(100, item.val)}%`, 
                              height: '100%', 
                              borderRadius: 100, 
                              background: item.color,
                              transition: 'width 0.8s ease-in-out'
                            }} />
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              </motion.div>
            </AnimatePresence>
          ) : (
            <div className="empty-state" style={{ flex: 1 }}>
              <div className="empty-state-icon">
                <MdOutlineSpeed size={28} />
              </div>
              <h3 style={{ fontSize: 15, fontWeight: 600, marginBottom: 6 }}>Ready to Simulate</h3>
              <p style={{ maxWidth: 340, fontSize: 13 }}>
                Select a disruption scenario from the left panel and click <strong>Simulate Scenario</strong> to view AI-generated impact analysis.
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default ScenarioImpact;
