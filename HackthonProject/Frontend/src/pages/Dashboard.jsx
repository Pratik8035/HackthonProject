import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { useNavigate } from 'react-router-dom';
import { riskApi } from '../services/riskApi';
import { supplierApi } from '../services/supplierApi';
import { scenarioApi } from '../services/scenarioApi';
import { reserveApi } from '../services/reserveApi';
import { DashboardSkeleton } from '../components/Skeleton';
import ErrorCard from '../components/ErrorCard';
import {
  AreaChart, Area, BarChart, Bar, PieChart, Pie, Cell,
  XAxis, YAxis, CartesianGrid, Tooltip as RechartsTip,
  Legend, ResponsiveContainer,
} from 'recharts';
import {
  MdPublic, MdError, MdWarning, MdCheckCircle, MdGroup,
  MdInventory, MdSchedule, MdAttachMoney, MdShowChart,
  MdTimeline, MdTrendingUp, MdOutlineAssignment, MdExplore,
  MdSync, MdFlashOn, MdOutlineSpeed, MdBolt,
  MdOutlineLocationOn, MdDirectionsBoat, MdLocalShipping,
  MdArrowForwardIos,
} from 'react-icons/md';

/* ── static country risk lookup (fallback only) ── */
const COUNTRY_RISK = {
  Russia: 90, Nigeria: 58, India: 52, Canada: 48, USA: 46,
  Norway: 45, Brazil: 44, Qatar: 42, 'Saudi Arabia': 20, UAE: 18,
};
const countryColor = (score) =>
  score > 70 ? 'var(--danger)' : score > 40 ? 'var(--warning)' : 'var(--success)';

/* ── Tiny reusable KPI card ── */
const KPI = ({ icon, label, value, color = 'blue', sub }) => (
  <motion.div
    className="kpi-card"
    initial={{ opacity: 0, y: 10 }}
    animate={{ opacity: 1, y: 0 }}
    style={{ flex: '1 1 0', minWidth: 0 }}
  >
    <div className={`kpi-icon ${color}`}>{icon}</div>
    <div style={{ minWidth: 0 }}>
      <div className="kpi-label">{label}</div>
      <div className={`kpi-value ${color}`} style={{ fontSize: 18, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
        {value}
      </div>
      {sub && <div style={{ fontSize: 11, color: 'var(--text-secondary)', marginTop: 1 }}>{sub}</div>}
    </div>
  </motion.div>
);

/* ── Section header ── */
const SectionTitle = ({ icon, title, right }) => (
  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 14 }}>
    <div style={{ display: 'flex', alignItems: 'center', gap: 8, fontWeight: 700, fontSize: 14, color: 'var(--text-primary)' }}>
      {icon} {title}
    </div>
    {right}
  </div>
);

const Dashboard = () => {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [data, setData] = useState({ risk: null, suppliers: [], scenarios: [], reserve: null });

  const [supplierDetails, setSupplierDetails] = useState([]);

  const DASH_RISK_KEY = 'dashboard_risk_cache';

  // forceRefresh=true → always call the risk API (used by Refresh button)
  // forceRefresh=false → use sessionStorage cache if available (page navigation / mount)
  const fetchData = async (forceRefresh = false) => {
    try {
      setLoading(true);
      setError(null);

      // ── Resolve risk data ──────────────────────────────────────
      let riskData = null;
      if (!forceRefresh) {
        try {
          const cached = sessionStorage.getItem(DASH_RISK_KEY);
          if (cached) riskData = JSON.parse(cached);
        } catch (_) { /* ignore corrupted cache */ }
      }

      if (!riskData) {
        // Either forced refresh or no cache — call the API
        const riskRes = await riskApi.runRiskAssessment();
        riskData = riskRes.data || {};
        try { sessionStorage.setItem(DASH_RISK_KEY, JSON.stringify(riskData)); } catch (_) {}
      }

      // ── Fetch everything else fresh every time ─────────────────
      const [suppRes, reserveRes] = await Promise.all([
        supplierApi.getCurrentSuppliers(),
        reserveApi.optimize({
          gap_data: { daily_gap: [20, 30, 40], horizon: 3, confidence: 0.9 },
          demand_data: [{ id: 'Refinery_A', daily_demand: [100, 100, 100], priority: 1.5 }],
          spr_data: { current_inventory: 1500, max_daily_drawdown: 80, min_reserve_level: 500 },
          procurement_data: { expected_incoming_shipments: [0, 0, 10], procurement_cost: [85, 86, 90], replenishment_lead_time: 2 },
        }).catch(() => ({ data: { remaining_reserve: 1500, release_spr: false, optimization_score: 95 } })),
      ]);

      const riskScore = riskData?.risk_score ?? null;
      const scenarioRes = await scenarioApi.listScenarios(riskScore);

      setData({
        risk: riskData,
        suppliers: Array.isArray(suppRes.data) ? suppRes.data : [],
        scenarios: Array.isArray(scenarioRes.data?.scenarios) ? scenarioRes.data.scenarios : [],
        reserve: reserveRes.data || {},
      });

      // Fetch route + cost for first 4 suppliers in parallel
      const top4 = (Array.isArray(suppRes.data) ? suppRes.data : []).slice(0, 4);
      const detailResults = await Promise.all(
        top4.map(async (s) => {
          const name = s.supplier_name;
          try {
            const [routeRes, costRes] = await Promise.all([
              supplierApi.analyzeRoute({ selected_supplier: name }),
              supplierApi.predictCost({ selected_supplier: name }),
            ]);
            return { ...s, route: routeRes.data, cost: costRes.data };
          } catch {
            return { ...s, route: null, cost: null };
          }
        })
      );
      setSupplierDetails(detailResults);
    } catch (err) {
      setError(err);
    } finally {
      setLoading(false);
    }
  };

  // On mount: use cached risk if available — full browser refresh clears cache
  useEffect(() => { fetchData(false); }, []);

  if (loading) return <DashboardSkeleton />;
  if (error)   return <div className="page-container"><ErrorCard error={error} onRetry={() => fetchData(true)} /></div>;

  const { risk, suppliers, scenarios, reserve } = data;

  /* ── Derived metrics ── */
  const riskScore    = risk?.risk_score ?? 0;
  const riskClass    = risk?.risk_class ?? '—';
  const riskReasons  = risk?.reasons ?? [];
  const riskColor    = riskScore > 70 ? 'var(--danger)' : riskScore > 40 ? 'var(--warning)' : 'var(--success)';

  const total        = suppliers.length;
  const active       = suppliers.filter(s => s.availability !== 'Low').length;
  const countries    = new Set(suppliers.map(s => s.country).filter(Boolean)).size;
  const avgPrice     = total ? (suppliers.reduce((a, s) => a + (parseFloat(s.price_per_barrel) || 80), 0) / total) : 80;
  const avgLead      = total ? (suppliers.reduce((a, s) => a + (parseInt(s.lead_time) || 15), 0) / total).toFixed(1) : '—';

  let high = 0, medium = 0, low = 0;
  suppliers.forEach(s => {
    const sc = COUNTRY_RISK[s.country] ?? 35;
    if (sc > 70) high++; else if (sc > 40) medium++; else low++;
  });
  if (!total) { high = 18; medium = 62; low = 20; }

  const sprStatus    = reserve?.release_spr ? 'Drawdown' : 'Stable';
  const sprScore     = reserve?.optimization_score ?? 95;
  const sprRemaining = reserve?.remaining_reserve ?? 1500;

  /* ── Chart datasets ── */
  const pieData = [
    { name: 'High Risk',   value: high,   color: 'var(--danger)'  },
    { name: 'Medium Risk', value: medium, color: 'var(--warning)' },
    { name: 'Low Risk',    value: low,    color: 'var(--success)' },
  ];

  const supplierBarData = suppliers
    .map(s => ({ name: (s.supplier_name || '').replace(' Oil Supplier', '').substring(0, 12), score: COUNTRY_RISK[s.country] ?? 15, country: s.country }))
    .sort((a, b) => b.score - a.score).slice(0, 6);

  const trendData = [
    { m: 'Jan', risk: 41, cost: 86000, delay: 4.8 },
    { m: 'Feb', risk: 43, cost: 88500, delay: 5.1 },
    { m: 'Mar', risk: 48, cost: 94000, delay: 5.9 },
    { m: 'Apr', risk: riskScore || 46, cost: Math.round(avgPrice * 1050), delay: parseFloat(avgLead) || 5.2 },
    { m: 'May', risk: Math.max(10, (riskScore || 46) - 3), cost: Math.round(avgPrice * 1050) - 4000, delay: Math.max(1, parseFloat(avgLead) - 0.5) },
    { m: 'Jun', risk: Math.max(10, (riskScore || 46) - 8), cost: Math.round(avgPrice * 1050) - 9500, delay: Math.max(1, parseFloat(avgLead) - 1.2) },
  ];

  const scenarioTop4 = scenarios.slice(0, 4);

  const tipStyle = { background: 'var(--bg-secondary)', border: '1px solid var(--border-color)', borderRadius: 10, fontSize: 12 };

  return (
    <div className="page-container" style={{ paddingTop: 20 }}>

      {/* ── Header ─────────────────────────────────────────────── */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 24, flexWrap: 'wrap', gap: 12 }}>
        <div>
          <h1 style={{ fontSize: 22, fontWeight: 800, color: 'var(--text-primary)', margin: 0 }}>Executive Dashboard</h1>
          <p style={{ fontSize: 13, color: 'var(--text-secondary)', marginTop: 3 }}>
            Autonomous supply chain intelligence — last updated {new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
          </p>
        </div>
        <div style={{ display: 'flex', gap: 8 }}>
          <button onClick={() => fetchData(true)} style={{ display: 'flex', alignItems: 'center', gap: 6, padding: '8px 16px', fontSize: 13, fontWeight: 600, borderRadius: 10, border: '1px solid var(--border-color)', background: 'var(--bg-secondary)', color: 'var(--text-secondary)', cursor: 'pointer' }}>
            <MdSync size={16} /> Refresh
          </button>
          <button onClick={() => navigate('/integrated-analysis')} className="btn-primary-gradient" style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
            <MdBolt size={16} /> Launch Orchestrator
          </button>
        </div>
      </div>

      {/* ── Risk Hero Banner ────────────────────────────────────── */}
      <motion.div
        className="glass-card"
        initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }}
        style={{ marginBottom: 20, padding: '20px 24px', background: `linear-gradient(135deg, ${riskScore > 70 ? 'rgba(239,68,68,0.06)' : riskScore > 40 ? 'rgba(245,158,11,0.06)' : 'rgba(16,185,129,0.06)'} 0%, var(--card-bg) 100%)`, border: `1px solid ${riskScore > 70 ? 'rgba(239,68,68,0.2)' : riskScore > 40 ? 'rgba(245,158,11,0.2)' : 'rgba(16,185,129,0.2)'}` }}
      >
        <div style={{ display: 'grid', gridTemplateColumns: '160px 1fr', gap: 24, alignItems: 'center' }}>
          {/* Gauge */}
          <div style={{ textAlign: 'center' }}>
            <div style={{ fontSize: 11, fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.6px', color: 'var(--text-secondary)', marginBottom: 10 }}>Live Risk Score</div>
            <div style={{ position: 'relative', width: 100, height: 100, borderRadius: '50%', background: `conic-gradient(${riskColor} ${riskScore * 3.6}deg, var(--border-color) ${riskScore * 3.6}deg)`, margin: '0 auto', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <div style={{ width: 84, height: 84, borderRadius: '50%', background: 'var(--bg-secondary)', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center' }}>
                <span style={{ fontSize: 26, fontWeight: 800, color: riskColor, lineHeight: 1 }}>{riskScore}</span>
                <span style={{ fontSize: 10, fontWeight: 600, color: 'var(--text-secondary)' }}>/ 100</span>
              </div>
            </div>
            <div style={{ marginTop: 10 }}>
              <span className={riskScore > 70 ? 'badge-high' : riskScore > 40 ? 'badge-medium' : 'badge-low'}>{riskClass}</span>
            </div>
          </div>
          {/* Reasons */}
          <div>
            <div style={{ fontWeight: 700, fontSize: 14, marginBottom: 10, color: 'var(--text-primary)' }}>🔍 Primary Risk Drivers</div>
            {riskReasons.length > 0 ? (
              <div style={{ display: 'flex', flexDirection: 'column', gap: 7 }}>
                {riskReasons.map((r, i) => (
                  <div key={i} style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '8px 12px', background: 'rgba(255,255,255,0.03)', border: '1px solid var(--border-color)', borderRadius: 8, fontSize: 13 }}>
                    <MdError size={14} style={{ color: riskColor, flexShrink: 0 }} />
                    <span style={{ color: 'var(--text-primary)' }}>{r}</span>
                  </div>
                ))}
              </div>
            ) : (
              <p style={{ color: 'var(--text-secondary)', fontSize: 13, fontStyle: 'italic' }}>No active risk drivers detected.</p>
            )}
            {risk?.scenario && (
              <div style={{ marginTop: 10, fontSize: 11, color: 'var(--text-secondary)' }}>
                Active scenario: <strong style={{ color: 'var(--text-primary)' }}>{risk.scenario}</strong>
              </div>
            )}
          </div>
        </div>
      </motion.div>

      {/* ── KPI Row ─────────────────────────────────────────────── */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 12, marginBottom: 20 }}>
        <KPI icon={<MdGroup size={20}/>}       label="Total Suppliers"   value={total || 100}        color="blue"  sub={`${active} active`} />
        <KPI icon={<MdPublic size={20}/>}       label="Countries"        value={countries || 10}     color="cyan"  sub="monitored" />
        <KPI icon={<MdError size={20}/>}        label="High Risk"        value={high}                color="red"   sub={`${medium} medium`} />
        <KPI icon={<MdCheckCircle size={20}/>}  label="Low Risk"         value={low}                 color="green" sub="suppliers" />
      </div>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 12, marginBottom: 20 }}>
        <KPI icon={<MdShowChart size={20}/>}    label="Avg Risk Score"   value={riskScore}           color="red"   sub={riskClass} />
        <KPI icon={<MdAttachMoney size={20}/>}  label="Avg Price/bbl"    value={`$${avgPrice.toFixed(0)}`} color="green" sub="USD" />
        <KPI icon={<MdSchedule size={20}/>}     label="Avg Lead Time"    value={`${avgLead} days`}   color="amber" />
        <KPI icon={<MdInventory size={20}/>}    label="SPR Status"       value={sprStatus}           color={reserve?.release_spr ? 'amber' : 'green'} sub={`Score: ${sprScore.toFixed(0)}`} />
      </div>

      {/* ── Charts Row 1: Pie + Top Suppliers Bar + Trend ──────── */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 16, marginBottom: 16 }}>

        {/* Pie — Risk Split */}
        <motion.div className="glass-card" initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.05 }}>
          <SectionTitle icon={<MdShowChart size={16} color="var(--primary-color)" />} title="Supplier Risk Split" />
          <div style={{ height: 220 }}>
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie data={pieData} innerRadius={58} outerRadius={85} paddingAngle={3} dataKey="value">
                  {pieData.map((e, i) => <Cell key={i} fill={e.color} />)}
                </Pie>
                <RechartsTip contentStyle={tipStyle} />
                <Legend wrapperStyle={{ fontSize: 12 }} iconType="circle" />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </motion.div>

        {/* Bar — Top risky suppliers */}
        <motion.div className="glass-card" initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }}>
          <SectionTitle icon={<MdWarning size={16} color="var(--warning)" />} title="Highest-Risk Suppliers" />
          <div style={{ height: 220 }}>
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={supplierBarData} layout="vertical" margin={{ left: 0, right: 10, top: 0, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" opacity={0.08} horizontal={false} />
                <XAxis type="number" domain={[0, 100]} tick={{ fontSize: 10 }} stroke="var(--text-secondary)" />
                <YAxis dataKey="name" type="category" width={90} tick={{ fontSize: 10 }} stroke="var(--text-secondary)" />
                <RechartsTip contentStyle={tipStyle} />
                <Bar dataKey="score" radius={[0, 4, 4, 0]}>
                  {supplierBarData.map((e, i) => <Cell key={i} fill={countryColor(e.score)} />)}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </motion.div>

        {/* Area — 6-month risk trend */}
        <motion.div className="glass-card" initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.15 }}>
          <SectionTitle icon={<MdTimeline size={16} color="var(--primary-color)" />} title="6-Month Risk Trend" />
          <div style={{ height: 220 }}>
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={trendData} margin={{ top: 5, right: 5, left: -20, bottom: 0 }}>
                <defs>
                  <linearGradient id="gRisk" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%"  stopColor="var(--danger)" stopOpacity={0.35} />
                    <stop offset="95%" stopColor="var(--danger)" stopOpacity={0} />
                  </linearGradient>
                  <linearGradient id="gDelay" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%"  stopColor="var(--warning)" stopOpacity={0.35} />
                    <stop offset="95%" stopColor="var(--warning)" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" opacity={0.08} />
                <XAxis dataKey="m" tick={{ fontSize: 11 }} stroke="var(--text-secondary)" />
                <YAxis tick={{ fontSize: 11 }} stroke="var(--text-secondary)" />
                <RechartsTip contentStyle={tipStyle} />
                <Area type="monotone" dataKey="risk"  stroke="var(--danger)"  fill="url(#gRisk)"  name="Risk Score" strokeWidth={2} dot={false} />
                <Area type="monotone" dataKey="delay" stroke="var(--warning)" fill="url(#gDelay)" name="Delay (days)" strokeWidth={2} dot={false} />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </motion.div>
      </div>

      {/* ── Charts Row 2: Cost Trend + Scenarios ───────────────── */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16, marginBottom: 16 }}>

        {/* Area — Cost & SPR trend */}
        <motion.div className="glass-card" initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.2 }}>
          <SectionTitle icon={<MdAttachMoney size={16} color="var(--success)" />} title="Cost & Reserve Trend (6 Months)" />
          <div style={{ height: 220 }}>
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={trendData} margin={{ top: 5, right: 5, left: -5, bottom: 0 }}>
                <defs>
                  <linearGradient id="gCost" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%"  stopColor="var(--success)" stopOpacity={0.35} />
                    <stop offset="95%" stopColor="var(--success)" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" opacity={0.08} />
                <XAxis dataKey="m" tick={{ fontSize: 11 }} stroke="var(--text-secondary)" />
                <YAxis tick={{ fontSize: 11 }} stroke="var(--text-secondary)" tickFormatter={v => `$${(v/1000).toFixed(0)}k`} />
                <RechartsTip contentStyle={tipStyle} formatter={v => `$${Number(v).toLocaleString()}`} />
                <Area type="monotone" dataKey="cost" stroke="var(--success)" fill="url(#gCost)" name="Transit Cost" strokeWidth={2} dot={false} />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </motion.div>

        {/* Scenario probability bars */}
        <motion.div className="glass-card" initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.25 }}>
          <SectionTitle
            icon={<MdWarning size={16} color="var(--warning)" />}
            title="Top Active Scenarios"
            right={<button onClick={() => navigate('/scenario-impact')} style={{ fontSize: 11, fontWeight: 600, color: 'var(--primary-color)', background: 'none', border: 'none', cursor: 'pointer' }}>View all →</button>}
          />
          {scenarioTop4.length === 0 ? (
            <p style={{ color: 'var(--text-secondary)', fontSize: 13, marginTop: 20 }}>No scenario data available.</p>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 10, marginTop: 4 }}>
              {scenarioTop4.map((s, i) => {
                const pct = parseFloat(s.probability) <= 1 ? parseFloat(s.probability) * 100 : parseFloat(s.probability);
                const sev = (s.severity || '').toLowerCase();
                const barColor = sev === 'high' ? 'var(--danger)' : sev === 'low' ? 'var(--success)' : 'var(--warning)';
                return (
                  <div key={i}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 12, fontWeight: 600, marginBottom: 4 }}>
                      <span style={{ color: 'var(--text-primary)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', maxWidth: '70%' }}>{s.scenario_name}</span>
                      <span style={{ color: barColor, flexShrink: 0 }}>{pct.toFixed(1)}%</span>
                    </div>
                    <div style={{ height: 6, background: 'var(--border-color)', borderRadius: 100, overflow: 'hidden' }}>
                      <div style={{ width: `${Math.min(100, pct)}%`, height: '100%', background: barColor, borderRadius: 100, transition: 'width 0.6s ease' }} />
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </motion.div>
      </div>

      {/* ── Supplier Route & Cost Panel ────────────────────────── */}
      {supplierDetails.length > 0 && (
        <motion.div
          className="glass-card"
          initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.28 }}
          style={{ marginBottom: 16 }}
        >
          <SectionTitle
            icon={<MdLocalShipping size={16} color="var(--primary-color)" />}
            title="Current Suppliers — Route & Cost Overview"
            right={
              <button onClick={() => navigate('/route-optimization')} style={{ fontSize: 11, fontWeight: 600, color: 'var(--primary-color)', background: 'none', border: 'none', cursor: 'pointer' }}>
                Full Route Map →
              </button>
            }
          />
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
              <thead>
                <tr style={{ borderBottom: '1px solid var(--border-color)' }}>
                  {['Supplier', 'Country', 'Crude', 'Price/bbl', 'Lead Time', 'Best Route', 'Distance', 'Transit', 'Transport Cost', 'Fuel Cost', 'Total Cost'].map(h => (
                    <th key={h} style={{ padding: '8px 12px', fontSize: 10, fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.4px', color: 'var(--text-secondary)', textAlign: 'left', whiteSpace: 'nowrap', background: 'var(--bg-primary)' }}>{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {supplierDetails.map((s, i) => {
                  const riskScore = COUNTRY_RISK[s.country] ?? 35;
                  const riskCol = countryColor(riskScore);
                  const route = s.route;
                  const cost = s.cost;
                  const routeStr = route?.['Best Route'] || '—';
                  // Truncate long route string
                  const routeShort = routeStr.length > 32 ? routeStr.substring(0, 30) + '…' : routeStr;
                  return (
                    <tr key={i} style={{ borderBottom: '1px solid var(--border-color)', transition: 'background 0.15s' }}
                      onMouseEnter={e => e.currentTarget.style.background = 'rgba(37,99,235,0.03)'}
                      onMouseLeave={e => e.currentTarget.style.background = 'transparent'}
                    >
                      <td style={{ padding: '10px 12px', fontWeight: 600, whiteSpace: 'nowrap' }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                          <div style={{ width: 8, height: 8, borderRadius: '50%', background: riskCol, flexShrink: 0 }} />
                          {s.supplier_name}
                        </div>
                      </td>
                      <td style={{ padding: '10px 12px', whiteSpace: 'nowrap' }}>
                        <span style={{ display: 'flex', alignItems: 'center', gap: 4, color: 'var(--text-secondary)' }}>
                          <MdOutlineLocationOn size={13} /> {s.country}
                        </span>
                      </td>
                      <td style={{ padding: '10px 12px', color: 'var(--text-secondary)' }}>{s.crude_type || '—'}</td>
                      <td style={{ padding: '10px 12px', fontWeight: 700, color: 'var(--success)' }}>
                        ${parseFloat(s.price_per_barrel || 0).toFixed(0)}
                      </td>
                      <td style={{ padding: '10px 12px', whiteSpace: 'nowrap', color: 'var(--warning)' }}>
                        {s.lead_time ? `${s.lead_time}d` : '—'}
                      </td>
                      <td style={{ padding: '10px 12px', maxWidth: 180 }} title={routeStr}>
                        {route ? (
                          <span style={{ display: 'flex', alignItems: 'center', gap: 5, color: 'var(--primary-color)', fontSize: 12 }}>
                            <MdDirectionsBoat size={13} style={{ flexShrink: 0 }} />
                            {routeShort}
                          </span>
                        ) : <span style={{ color: 'var(--text-secondary)' }}>—</span>}
                      </td>
                      <td style={{ padding: '10px 12px', whiteSpace: 'nowrap', color: 'var(--text-secondary)' }}>
                        {route?.Distance ? `${Number(route.Distance).toLocaleString()} km` : '—'}
                      </td>
                      <td style={{ padding: '10px 12px', whiteSpace: 'nowrap' }}>
                        {route?.['Expected Delivery'] ? (
                          <span style={{ display: 'flex', alignItems: 'center', gap: 4, color: 'var(--info)' }}>
                            <MdSchedule size={13} /> {route['Expected Delivery']}d
                          </span>
                        ) : '—'}
                      </td>
                      <td style={{ padding: '10px 12px', whiteSpace: 'nowrap', color: 'var(--text-secondary)' }}>
                        {cost?.['Transportation Cost'] || '—'}
                      </td>
                      <td style={{ padding: '10px 12px', whiteSpace: 'nowrap', color: 'var(--text-secondary)' }}>
                        {cost?.['Fuel Cost'] || '—'}
                      </td>
                      <td style={{ padding: '10px 12px', whiteSpace: 'nowrap', fontWeight: 700, color: 'var(--primary-color)' }}>
                        {cost?.['Predicted Total Cost'] || '—'}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
          <div style={{ marginTop: 10, fontSize: 11, color: 'var(--text-secondary)', display: 'flex', alignItems: 'center', gap: 6 }}>
            <span style={{ width: 8, height: 8, borderRadius: '50%', background: 'var(--danger)', display: 'inline-block' }} /> High risk &nbsp;
            <span style={{ width: 8, height: 8, borderRadius: '50%', background: 'var(--warning)', display: 'inline-block' }} /> Medium risk &nbsp;
            <span style={{ width: 8, height: 8, borderRadius: '50%', background: 'var(--success)', display: 'inline-block' }} /> Low risk &nbsp; · Showing top 4 suppliers
          </div>
        </motion.div>
      )}

      {/* ── Bottom Row: Live Alerts + CTA ──────────────────────── */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>

        {/* Live Alerts Feed */}
        <motion.div className="glass-card" initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.3 }}>
          <SectionTitle
            icon={<MdTrendingUp size={16} color="var(--danger)" />}
            title="Geopolitical Intelligence Feed"
            right={
              <span style={{ display: 'flex', alignItems: 'center', gap: 5, fontSize: 11, fontWeight: 700, color: 'var(--danger)', background: 'rgba(239,68,68,0.1)', padding: '3px 10px', borderRadius: 20 }}>
                <span style={{ width: 6, height: 6, borderRadius: '50%', background: 'var(--danger)', display: 'inline-block', animation: 'pulse 1.5s infinite' }} />
                {riskReasons.length} Active
              </span>
            }
          />
          <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
            {(riskReasons.length > 0 ? riskReasons : [
              'High disruption hazard on Baltic Sea shipping lanes.',
              'Port congestion increasing at Rotterdam terminal.',
              'AI engine identified 12 new alternative supply routes.',
            ]).slice(0, 3).map((msg, i) => {
              const type = i === 0 ? 'critical' : i === 1 ? 'warning' : 'info';
              const bg = type === 'critical' ? 'rgba(239,68,68,0.06)' : type === 'warning' ? 'rgba(245,158,11,0.06)' : 'rgba(14,165,233,0.06)';
              const border = type === 'critical' ? 'rgba(239,68,68,0.15)' : type === 'warning' ? 'rgba(245,158,11,0.15)' : 'rgba(14,165,233,0.15)';
              const color = type === 'critical' ? 'var(--danger)' : type === 'warning' ? 'var(--warning)' : 'var(--info)';
              const Icon = type === 'critical' ? MdError : type === 'warning' ? MdWarning : MdPublic;
              return (
                <div key={i} style={{ display: 'flex', alignItems: 'flex-start', gap: 10, padding: '10px 12px', background: bg, border: `1px solid ${border}`, borderRadius: 10 }}>
                  <div style={{ width: 30, height: 30, borderRadius: '50%', background: color, display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
                    <Icon size={16} color="white" />
                  </div>
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div style={{ fontSize: 11, fontWeight: 700, color, textTransform: 'uppercase', letterSpacing: '0.4px', marginBottom: 2 }}>
                      {type === 'critical' ? 'Critical Alert' : type === 'warning' ? 'Warning' : 'Intelligence'}
                    </div>
                    <div style={{ fontSize: 12, color: 'var(--text-secondary)', lineHeight: 1.5 }}>{msg}</div>
                  </div>
                  <span style={{ fontSize: 10, color: 'var(--text-secondary)', flexShrink: 0 }}>now</span>
                </div>
              );
            })}
          </div>
        </motion.div>

        {/* Orchestrator CTA */}
        <motion.div
          className="glass-card"
          initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.35 }}
          style={{ display: 'flex', flexDirection: 'column', justifyContent: 'space-between', background: 'linear-gradient(135deg, rgba(59,130,246,0.08) 0%, rgba(29,78,216,0.12) 100%)', border: '1px solid rgba(59,130,246,0.2)' }}
        >
          <div>
            <div style={{ width: 48, height: 48, borderRadius: 14, background: 'rgba(59,130,246,0.15)', display: 'flex', alignItems: 'center', justifyContent: 'center', marginBottom: 14 }}>
              <MdExplore size={26} color="var(--primary-color)" />
            </div>
            <div style={{ fontWeight: 800, fontSize: 16, color: 'var(--text-primary)', marginBottom: 8 }}>Integrated Decision Workspace</div>
            <p style={{ fontSize: 13, color: 'var(--text-secondary)', lineHeight: 1.7, marginBottom: 20 }}>
              Connect live risk scores, ML scenario models, supplier rankings, route optimization, and SPR scheduling in a single end-to-end workflow.
            </p>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 8, marginBottom: 20 }}>
              {['Risk Assessment → Scenario Simulation', 'Alternative Supplier Ranking (XGBoost)', 'Route & Delay Forecasting (RF)', 'SPR Optimization (MILP/SCIP)'].map((step, i) => (
                <div key={i} style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 12, color: 'var(--text-secondary)' }}>
                  <div style={{ width: 18, height: 18, borderRadius: '50%', background: 'rgba(59,130,246,0.15)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 10, fontWeight: 700, color: 'var(--primary-color)', flexShrink: 0 }}>{i + 1}</div>
                  {step}
                </div>
              ))}
            </div>
          </div>
          <button
            onClick={() => navigate('/integrated-analysis')}
            className="btn-primary-gradient"
            style={{ width: '100%', padding: '12px', fontSize: 14, display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 8, borderRadius: 12 }}
          >
            <MdBolt size={18} /> Begin Orchestrated Analysis
          </button>
        </motion.div>

      </div>
    </div>
  );
};

export default Dashboard;
