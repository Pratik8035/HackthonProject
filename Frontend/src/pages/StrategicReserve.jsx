import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { reserveApi } from '../services/reserveApi';
import { useAnalysis } from '../contexts/AnalysisContext';
import ErrorCard from '../components/ErrorCard';
import { MdInventory, MdTrendingUp, MdSavings, MdOutlineAssessment, MdPlayArrow, MdCheckCircle, MdWarning, MdInfo } from 'react-icons/md';
import {
  AreaChart, Area, XAxis, YAxis, CartesianGrid,
  Tooltip as RechartsTooltip, ResponsiveContainer, Legend, BarChart, Bar
} from 'recharts';

const safeNum = (v, fallback = 0) => { const n = parseFloat(v); return isNaN(n) ? fallback : n; };
const fmt = (n) => safeNum(n).toLocaleString(undefined, { maximumFractionDigits: 1 });

/**
 * Build optimizer input scaled to the current live risk score (0–100).
 *
 * Risk drives:
 *  - daily_gap        : bigger gaps at higher risk (more supply disruption)
 *  - confidence       : lower confidence at higher risk (more uncertainty)
 *  - current_inventory: starts lower at high risk (reserves already drawn)
 *  - max_daily_drawdown: larger allowed drawdown at high risk (emergency mode)
 *  - procurement_cost : higher spot prices at high risk
 *  - expected_incoming_shipments: fewer arrivals at high risk (delays)
 */
const buildInput = (riskScore = 50) => {
  const r = Math.max(0, Math.min(100, riskScore));
  // Normalise to 0–1
  const t = r / 100;

  // Supply gap grows from ~10 at low risk to ~80 at max risk
  const baseGap = 10 + t * 70;
  // Add daily variation that worsens with risk
  const gapVariation = (i) => baseGap + (Math.sin(i * 1.3) * baseGap * 0.3 * t);

  const horizon = 7;
  const daily_gap = Array.from({ length: horizon }, (_, i) =>
    parseFloat((gapVariation(i)).toFixed(1))
  );

  // Inventory: 2500 at low risk → 900 at high risk
  const current_inventory = parseFloat((2500 - t * 1600).toFixed(0));
  // Max drawdown: 60 at low risk → 150 at high risk
  const max_daily_drawdown = parseFloat((60 + t * 90).toFixed(0));
  // Min reserve floor stays constant
  const min_reserve_level = 400;

  // Procurement cost: $82 at low risk → $110 at high risk
  const baseCost = 82 + t * 28;
  const procurement_cost = Array.from({ length: horizon }, (_, i) =>
    parseFloat((baseCost + i * 0.5 * t).toFixed(1))
  );

  // Incoming shipments: plentiful at low risk, scarce at high risk
  const shipBase = parseFloat((8 - t * 7).toFixed(1));   // 8 → 1
  const expected_incoming_shipments = Array.from({ length: horizon }, (_, i) =>
    parseFloat(Math.max(0, shipBase - i * 0.3 * t).toFixed(1))
  );

  // Confidence drops with risk
  const confidence = parseFloat((0.95 - t * 0.25).toFixed(2));

  // Refinery demands scale slightly with risk (more consumption in crisis)
  const demandScale = 1 + t * 0.3;
  return {
    gap_data: { daily_gap, horizon, confidence },
    demand_data: [
      { id: 'Refinery_A', daily_demand: Array(horizon).fill(parseFloat((100 * demandScale).toFixed(1))), priority: 2.0 },
      { id: 'Refinery_B', daily_demand: Array(horizon).fill(parseFloat((80  * demandScale).toFixed(1))), priority: 1.5 },
      { id: 'Refinery_C', daily_demand: Array(horizon).fill(parseFloat((50  * demandScale).toFixed(1))), priority: 1.0 },
    ],
    spr_data: { current_inventory, max_daily_drawdown, min_reserve_level },
    procurement_data: { expected_incoming_shipments, procurement_cost, replenishment_lead_time: 2 },
  };
};

const StrategicReserve = () => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [result, setResult] = useState(null);
  const [ran, setRan] = useState(false);
  const [usedInput, setUsedInput] = useState(null);

  // Pull live risk score from context so optimizer input scales with current risk
  const { liveRiskResult } = useAnalysis();
  const liveRiskScore = liveRiskResult?.risk_score ?? 50;
  const liveRiskClass = liveRiskResult?.risk_class ?? 'MEDIUM';

  const runOptimization = async () => {
    setLoading(true);
    setError(null);
    try {
      const input = buildInput(liveRiskScore);
      setUsedInput(input);
      const res = await reserveApi.optimize(input);
      setResult(res.data);
      setRan(true);
    } catch (err) {
      setError(err);
    } finally {
      setLoading(false);
    }
  };

  // Build chart data from result
  const buildChartData = () => {
    if (!result || !usedInput) return [];
    const schedule = result.drawdown_schedule || [];
    const replenishment = result.replenishment_plan || [];
    const horizon = usedInput.gap_data.horizon;
    return Array.from({ length: horizon }, (_, i) => ({
      day: `Day ${i + 1}`,
      drawdown: safeNum(schedule[i]),
      replenishment: safeNum(replenishment[i]),
      gap: safeNum(usedInput.gap_data.daily_gap[i]),
    }));
  };

  const refineryAlloc = result?.refinery_allocation || {};
  const refineryChartData = Object.entries(refineryAlloc).map(([refId, allocArr]) => ({
    refinery: refId.replace('_', ' '),
    total: allocArr.reduce((s, v) => s + safeNum(v), 0).toFixed(1),
  }));

  const chartData = buildChartData();
  const remainingReserve = safeNum(result?.remaining_reserve, 1500);
  const optimScore = safeNum(result?.optimization_score, 0);
  const estimatedCost = safeNum(result?.estimated_total_cost, 0);
  const releaseSPR = result?.release_spr ?? false;
  const sprInventory = safeNum(usedInput?.spr_data?.current_inventory ?? 2000);
  const minLevel = safeNum(usedInput?.spr_data?.min_reserve_level ?? 500);
  const reserveUtilPct = Math.min(100, Math.round((remainingReserve / sprInventory) * 100));

  // Preview input for display (before run)
  const previewInput = buildInput(liveRiskScore);

  return (
    <div className="page-container">
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 20, flexWrap: 'wrap', gap: 12 }}>
        <div>
          <h1 className="page-title">Strategic Reserve Optimization</h1>
          <p className="page-subtitle">Linear programming (MILP/SCIP) solver for daily SPR release scheduling and procurement planning.</p>
          {/* Live risk context chip */}
          <div style={{
            display: 'inline-flex', alignItems: 'center', gap: 7, marginTop: 8,
            padding: '5px 14px', borderRadius: 20, fontSize: 12, fontWeight: 600,
            background: liveRiskScore > 70 ? 'rgba(239,68,68,0.1)' : liveRiskScore > 40 ? 'rgba(245,158,11,0.1)' : 'rgba(16,185,129,0.1)',
            border: `1px solid ${liveRiskScore > 70 ? 'rgba(239,68,68,0.3)' : liveRiskScore > 40 ? 'rgba(245,158,11,0.3)' : 'rgba(16,185,129,0.3)'}`,
            color: liveRiskScore > 70 ? 'var(--danger)' : liveRiskScore > 40 ? 'var(--warning)' : 'var(--success)',
          }}>
            <MdInfo size={14} />
            Optimizer input scaled to Live Risk Score: {liveRiskScore} ({liveRiskClass})
            {!liveRiskResult && <span style={{ opacity: 0.7 }}> — run Live Risk first for best results</span>}
          </div>
        </div>
        <button
          className="btn-primary-gradient"
          onClick={runOptimization}
          disabled={loading}
          style={{ display: 'flex', alignItems: 'center', gap: 8 }}
        >
          {loading ? <span className="spinner-border spinner-border-sm" role="status" /> : <MdPlayArrow size={18} />}
          {loading ? 'Optimizing…' : ran ? 'Re-run Optimization' : 'Run MILP Optimization'}
        </button>
      </div>

      {loading && (
        <div className="glass-card" style={{ textAlign: 'center', padding: '60px 24px', marginBottom: 20 }}>
          <div className="spinner-border text-primary mb-3" style={{ width: '2.5rem', height: '2.5rem' }} role="status" />
          <div style={{ fontWeight: 700, fontSize: 15, marginBottom: 6 }}>Running MILP Optimization…</div>
          <div style={{ color: 'var(--text-secondary)', fontSize: 13 }}>SCIP solver computing optimal SPR release schedule across {usedInput?.gap_data?.horizon ?? 7} days · Risk Score {liveRiskScore}.</div>
        </div>
      )}

      {error && !loading && (
        <div style={{ marginBottom: 20 }}>
          <ErrorCard error={error} onRetry={runOptimization} />
        </div>
      )}

      {!ran && !loading && !error && (
        <div className="glass-card" style={{ marginBottom: 20 }}>
          <div style={{ fontWeight: 700, fontSize: 14, marginBottom: 16, display: 'flex', alignItems: 'center', gap: 8 }}>
            <MdInventory color="var(--primary-color)" /> Optimization Parameters — Scaled to Risk Score {liveRiskScore}
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))', gap: 12, marginBottom: 20 }}>
            {[
              { label: 'Current SPR Inventory',  val: `${fmt(previewInput.spr_data.current_inventory)} kMT` },
              { label: 'Max Daily Drawdown',      val: `${fmt(previewInput.spr_data.max_daily_drawdown)} kMT` },
              { label: 'Min Reserve Level',       val: `${fmt(previewInput.spr_data.min_reserve_level)} kMT` },
              { label: 'Planning Horizon',        val: `${previewInput.gap_data.horizon} Days` },
              { label: 'Optimizer Confidence',    val: `${(previewInput.gap_data.confidence * 100).toFixed(0)}%` },
              { label: 'Peak Daily Supply Gap',   val: `${Math.max(...previewInput.gap_data.daily_gap).toFixed(1)} kMT` },
              { label: 'Refineries Served',       val: `${previewInput.demand_data.length}` },
              { label: 'Avg Procurement Cost',    val: `$${(previewInput.procurement_data.procurement_cost.reduce((a,b)=>a+b,0)/previewInput.procurement_data.procurement_cost.length).toFixed(1)}` },
            ].map(({ label, val }) => (
              <div key={label} style={{ background: 'var(--bg-primary)', borderRadius: 10, padding: '12px 14px', border: '1px solid var(--border-color)' }}>
                <div style={{ fontSize: 10, fontWeight: 600, color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.4px', marginBottom: 4 }}>{label}</div>
                <div style={{ fontSize: 16, fontWeight: 700, color: 'var(--primary-color)' }}>{val}</div>
              </div>
            ))}
          </div>
          <div style={{ textAlign: 'center' }}>
            <p style={{ color: 'var(--text-secondary)', fontSize: 13, marginBottom: 16 }}>
              Click <strong>Run MILP Optimization</strong> to execute the solver with inputs calibrated to the current live risk environment.
            </p>
          </div>
        </div>
      )}

      {result && !loading && (
        <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }}>
          {/* KPI Cards */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))', gap: 12, marginBottom: 20 }}>
            <div className="kpi-card" style={{ borderLeft: `4px solid ${releaseSPR ? 'var(--warning)' : 'var(--success)'}` }}>
              <div className={`kpi-icon ${releaseSPR ? 'amber' : 'green'}`}>
                {releaseSPR ? <MdWarning size={22} /> : <MdCheckCircle size={22} />}
              </div>
              <div>
                <div className="kpi-label">SPR Release Decision</div>
                <div className={`kpi-value ${releaseSPR ? 'amber' : 'green'}`}>{releaseSPR ? 'Release Required' : 'No Release'}</div>
              </div>
            </div>
            <div className="kpi-card">
              <div className="kpi-icon blue"><MdInventory size={22} /></div>
              <div>
                <div className="kpi-label">Remaining Reserve</div>
                <div className="kpi-value blue">{fmt(remainingReserve)} <span style={{ fontSize: 12, fontWeight: 500, color: 'var(--text-secondary)' }}>kMT</span></div>
              </div>
            </div>
            <div className="kpi-card">
              <div className="kpi-icon green"><MdOutlineAssessment size={22} /></div>
              <div>
                <div className="kpi-label">Optimization Score</div>
                <div className="kpi-value green">{optimScore.toFixed(1)}<span style={{ fontSize: 12, fontWeight: 500, color: 'var(--text-secondary)' }}>/100</span></div>
              </div>
            </div>
            <div className="kpi-card">
              <div className="kpi-icon amber"><MdSavings size={22} /></div>
              <div>
                <div className="kpi-label">Estimated Total Cost</div>
                <div className="kpi-value amber">${fmt(estimatedCost)}</div>
              </div>
            </div>
          </div>

          {/* Reserve Utilization Bar */}
          <div className="glass-card" style={{ marginBottom: 16 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 8 }}>
              <span style={{ fontWeight: 600, fontSize: 14 }}>Reserve Utilization After Optimization</span>
              <span style={{ fontWeight: 700, fontSize: 14, color: 'var(--primary-color)' }}>{reserveUtilPct}%</span>
            </div>
            <div className="progress-slim" style={{ height: 10 }}>
              <div className="progress-slim-bar" style={{ width: `${reserveUtilPct}%`, background: reserveUtilPct < 40 ? 'var(--danger)' : 'var(--primary-gradient)' }} />
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: 6, fontSize: 11, color: 'var(--text-secondary)' }}>
              <span>Min Reserve: {fmt(minLevel)} kMT</span>
              <span>Initial: {fmt(sprInventory)} kMT → Remaining: {fmt(remainingReserve)} kMT</span>
            </div>
          </div>

          {/* Charts */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16, marginBottom: 16 }}>
            <div className="glass-card">
              <div style={{ fontWeight: 700, fontSize: 14, marginBottom: 14 }}>Daily Release & Replenishment Schedule</div>
              <div style={{ height: 240 }}>
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={chartData} margin={{ top: 5, right: 10, left: -10, bottom: 5 }}>
                    <CartesianGrid strokeDasharray="3 3" opacity={0.08} vertical={false} />
                    <XAxis dataKey="day" tick={{ fontSize: 11 }} stroke="var(--text-secondary)" />
                    <YAxis tick={{ fontSize: 11 }} stroke="var(--text-secondary)" />
                    <RechartsTooltip contentStyle={{ background: 'var(--bg-secondary)', border: '1px solid var(--border-color)', borderRadius: 8, fontSize: 12 }} />
                    <Legend wrapperStyle={{ fontSize: 12 }} />
                    <Bar dataKey="drawdown" name="SPR Drawdown" fill="#2563eb" radius={[3, 3, 0, 0]} />
                    <Bar dataKey="replenishment" name="Replenishment" fill="#10b981" radius={[3, 3, 0, 0]} />
                    <Bar dataKey="gap" name="Supply Gap" fill="rgba(245,158,11,0.5)" radius={[3, 3, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>

            <div className="glass-card">
              <div style={{ fontWeight: 700, fontSize: 14, marginBottom: 14 }}>Refinery Allocation Totals (kMT)</div>
              {refineryChartData.length > 0 ? (
                <div style={{ height: 240 }}>
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={refineryChartData} margin={{ top: 5, right: 10, left: -10, bottom: 5 }}>
                      <CartesianGrid strokeDasharray="3 3" opacity={0.08} vertical={false} />
                      <XAxis dataKey="refinery" tick={{ fontSize: 11 }} stroke="var(--text-secondary)" />
                      <YAxis tick={{ fontSize: 11 }} stroke="var(--text-secondary)" />
                      <RechartsTooltip contentStyle={{ background: 'var(--bg-secondary)', border: '1px solid var(--border-color)', borderRadius: 8, fontSize: 12 }} />
                      <Bar dataKey="total" name="Total Allocated (kMT)" fill="#3b82f6" radius={[4, 4, 0, 0]} />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              ) : (
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: 240, color: 'var(--text-secondary)', fontSize: 13 }}>
                  No refinery allocation data (no SPR release required).
                </div>
              )}
            </div>
          </div>

          {/* Explanation */}
          {result.explanation && (
            <div className="glass-card" style={{ borderLeft: '4px solid var(--primary-color)' }}>
              <div style={{ fontWeight: 700, fontSize: 14, marginBottom: 8, display: 'flex', alignItems: 'center', gap: 8 }}>
                <MdOutlineAssessment color="var(--primary-color)" /> AI Optimizer Explanation
              </div>
              <p style={{ fontSize: 13, color: 'var(--text-secondary)', lineHeight: 1.7, margin: 0 }}>
                {result.explanation}
              </p>
            </div>
          )}
        </motion.div>
      )}
    </div>
  );
};

export default StrategicReserve;
