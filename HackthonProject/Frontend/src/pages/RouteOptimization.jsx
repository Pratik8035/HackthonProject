import React, { useState, useEffect } from 'react';
import { useAnalysis } from '../contexts/AnalysisContext';
import { supplierApi } from '../services/supplierApi';
import { MapContainer, TileLayer, Marker, Popup, Polyline, useMap } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import {
  MdMap, MdLocationOn, MdDirectionsBoat, MdSchedule,
  MdCheckCircle, MdAnchor, MdSpeed, MdOutlineLocationOn,
} from 'react-icons/md';
import { motion } from 'framer-motion';
import L from 'leaflet';

/* ── All 8 actual ports from the dataset ─────────────────────────────────── */
const PORT_COORDS = {
  'Dubai Port':      [25.2769,  55.2962],
  'Jeddah Port':     [21.4858,  39.1925],
  'Santos Port':     [-23.9608,-46.3331],
  'Rotterdam Port':  [51.9244,   4.4777],
  'Singapore Port':  [ 1.2644, 103.8222],
  'Shanghai Port':   [31.2304, 121.4737],
  'Mumbai Port':     [18.9220,  72.8347],
  'Houston Port':    [29.7604, -95.3698],
};

/* ── Great-circle arc between two points (produces curved lines) ─────────── */
function gcArc(from, to, steps = 60) {
  const R2D = 180 / Math.PI, D2R = Math.PI / 180;
  const [φ1, λ1] = [from[0] * D2R, from[1] * D2R];
  const [φ2, λ2] = [to[0]   * D2R, to[1]   * D2R];
  const d = 2 * Math.asin(Math.sqrt(
    Math.sin((φ2 - φ1) / 2) ** 2 +
    Math.cos(φ1) * Math.cos(φ2) * Math.sin((λ2 - λ1) / 2) ** 2
  ));
  if (d < 0.0001) return [from, to];
  return Array.from({ length: steps + 1 }, (_, i) => {
    const f = i / steps;
    const a = Math.sin((1 - f) * d) / Math.sin(d);
    const b = Math.sin(f * d) / Math.sin(d);
    const x = a * Math.cos(φ1) * Math.cos(λ1) + b * Math.cos(φ2) * Math.cos(λ2);
    const y = a * Math.cos(φ1) * Math.sin(λ1) + b * Math.cos(φ2) * Math.sin(λ2);
    const z = a * Math.sin(φ1) + b * Math.sin(φ2);
    return [Math.atan2(z, Math.sqrt(x * x + y * y)) * R2D, Math.atan2(y, x) * R2D];
  });
}

function buildArc(coordList) {
  if (coordList.length < 2) return coordList;
  const out = [];
  for (let i = 0; i < coordList.length - 1; i++) {
    const seg = gcArc(coordList[i], coordList[i + 1]);
    if (i > 0) seg.shift();
    out.push(...seg);
  }
  return out;
}

/* ── Marker icons ─────────────────────────────────────────────────────────── */
const pinIcon = (bg, label, size = 38) => L.divIcon({
  className: '',
  html: `<div style="
    width:${size}px;height:${size}px;border-radius:50% 50% 50% 0;
    background:${bg};border:3px solid white;transform:rotate(-45deg);
    box-shadow:0 4px 12px rgba(0,0,0,0.35);
    display:flex;align-items:center;justify-content:center;">
    <span style="transform:rotate(45deg);color:white;font-size:${size * 0.37}px;
    font-weight:900;font-family:Inter,sans-serif;line-height:1;">${label}</span>
  </div>`,
  iconSize: [size, size], iconAnchor: [size / 2, size], popupAnchor: [0, -(size + 4)],
});

const stopIcon = (num) => L.divIcon({
  className: '',
  html: `<div style="
    width:28px;height:28px;border-radius:50%;
    background:#2563eb;border:3px solid white;
    box-shadow:0 2px 8px rgba(37,99,235,0.5);
    display:flex;align-items:center;justify-content:center;">
    <span style="color:white;font-size:11px;font-weight:800;font-family:Inter,sans-serif;">${num}</span>
  </div>`,
  iconSize: [28, 28], iconAnchor: [14, 14], popupAnchor: [0, -16],
});

const OriginIcon = pinIcon('#10b981', 'A');
const DestIcon   = pinIcon('#ef4444', 'B');

/* ── Auto-fit bounds ─────────────────────────────────────────────────────── */
const FitBounds = ({ coords }) => {
  const map = useMap();
  useEffect(() => {
    const valid = (coords || []).filter(c => c && !isNaN(c[0]) && !isNaN(c[1]));
    if (valid.length >= 2) {
      map.fitBounds(L.latLngBounds(valid), { padding: [60, 60], maxZoom: 7, animate: true });
    }
  }, [coords, map]);
  return null;
};

const RouteOptimization = () => {
  const { currentSupplier, selectedAlternative, setCurrentSupplier } = useAnalysis();
  const [suppliersList, setSuppliersList]   = useState([]);
  const [selectedName, setSelectedName]     = useState('');
  const [loading, setLoading]               = useState(false);
  const [routeData, setRouteData]           = useState(null);
  const [error, setError]                   = useState(null);

  useEffect(() => {
    supplierApi.getCurrentSuppliers()
      .then(r => setSuppliersList(r.data || []))
      .catch(() => {});
  }, []);

  const fetchRoute = async (name) => {
    if (!name) return;
    setLoading(true); setError(null); setRouteData(null);
    try {
      const res = await supplierApi.analyzeRoute({ selected_supplier: name });
      setRouteData(res.data);
    } catch {
      setError('Failed to fetch route for: ' + name);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    const s = selectedAlternative || currentSupplier;
    if (s) {
      const n = s.supplier_name || s.name || s.supplier_id;
      setSelectedName(n);
      fetchRoute(n);
    }
  }, [currentSupplier, selectedAlternative]);

  const handleChange = (e) => {
    const val = e.target.value;
    setSelectedName(val);
    const found = suppliersList.find(s => s.supplier_name === val || s.supplier_id === val);
    if (found) setCurrentSupplier(found);
    fetchRoute(val);
  };

  /* ── Parse route string into port list ── */
  const routeStr   = routeData?.['Best Route'] || '';
  const ports      = routeStr.split(' -> ').map(p => p.trim()).filter(Boolean);
  const coords     = ports.map(p => PORT_COORDS[p]).filter(Boolean);
  const arcPath    = buildArc(coords);

  const originPort = ports[0]    || '';
  const destPort   = ports[ports.length - 1] || '';
  const midPorts   = ports.slice(1, -1);
  const midCoords  = coords.slice(1, -1);

  const dist    = Number(routeData?.Distance || 0);
  const transit = routeData?.['Expected Delivery'] || 0;

  return (
    <div className="page-container" style={{ paddingTop: 20 }}>

      {/* ── Header ──────────────────────────────────────────── */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20, flexWrap: 'wrap', gap: 12 }}>
        <div>
          <h1 className="page-title">Route Optimization</h1>
          <p className="page-subtitle">Dijkstra shortest-path · great-circle arc · {ports.length} port{ports.length !== 1 ? 's' : ''}</p>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <label style={{ fontSize: 12, fontWeight: 600, color: 'var(--text-secondary)', whiteSpace: 'nowrap' }}>Supplier:</label>
          <select className="form-select-custom" style={{ minWidth: 280 }} value={selectedName} onChange={handleChange}>
            <option value="">— Choose a supplier —</option>
            {suppliersList.map((s, i) => (
              <option key={i} value={s.supplier_name || s.supplier_id}>
                {s.supplier_name} ({s.country})
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* ── Empty ───────────────────────────────────────────── */}
      {!selectedName && !loading && (
        <div className="glass-card" style={{ display:'flex', flexDirection:'column', alignItems:'center', justifyContent:'center', minHeight:'60vh', textAlign:'center' }}>
          <div style={{ width: 80, height: 80, borderRadius: '50%', background: 'rgba(37,99,235,0.08)', display: 'flex', alignItems: 'center', justifyContent: 'center', marginBottom: 20 }}>
            <MdMap size={40} color="var(--primary-color)" style={{ opacity: 0.5 }} />
          </div>
          <h3 style={{ fontWeight: 700, marginBottom: 8 }}>Select a Supplier</h3>
          <p style={{ color: 'var(--text-secondary)', maxWidth: 340, fontSize: 13 }}>
            Choose a supplier from the dropdown to compute and display the optimal maritime route on the map.
          </p>
        </div>
      )}

      {/* ── Loading ─────────────────────────────────────────── */}
      {loading && (
        <div className="glass-card" style={{ display:'flex', flexDirection:'column', alignItems:'center', justifyContent:'center', minHeight:'60vh', gap: 16 }}>
          <div className="spinner-border text-primary" style={{ width: '3rem', height: '3rem' }} role="status" />
          <div style={{ fontWeight: 700, color: 'var(--text-secondary)' }}>Computing shortest maritime path…</div>
          <div style={{ fontSize: 12, color: 'var(--text-secondary)' }}>Dijkstra algorithm · port graph · {selectedName}</div>
        </div>
      )}

      {/* ── Error ───────────────────────────────────────────── */}
      {error && !loading && (
        <div className="glass-card" style={{ textAlign: 'center', padding: 40 }}>
          <div style={{ color: 'var(--danger)', fontWeight: 700, fontSize: 15, marginBottom: 8 }}>Route Error</div>
          <p style={{ color: 'var(--text-secondary)', fontSize: 13, marginBottom: 16 }}>{error}</p>
          <button className="btn-primary-gradient" onClick={() => fetchRoute(selectedName)}>Retry</button>
        </div>
      )}

      {/* ── Map + Panels ────────────────────────────────────── */}
      {routeData && !loading && !error && (
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 320px', gap: 16, alignItems: 'start' }}>

          {/* ── MAP ─────────────────────────────────────────── */}
          <motion.div initial={{ opacity:0, y:16 }} animate={{ opacity:1, y:0 }} style={{ display:'flex', flexDirection:'column', gap: 0 }}>

            {/* Legend bar */}
            <div style={{ background: 'var(--bg-secondary)', border: '1px solid var(--border-color)', borderBottom: 'none', borderRadius: '16px 16px 0 0', padding: '10px 16px', display: 'flex', alignItems: 'center', gap: 16, flexWrap: 'wrap', fontSize: 12, fontWeight: 600 }}>
              <span style={{ display:'flex', alignItems:'center', gap:6 }}>
                <span style={{ width:12, height:12, borderRadius:'50%', background:'#10b981', border:'2px solid white', boxShadow:'0 1px 4px rgba(0,0,0,0.3)', display:'inline-block' }} />
                A · {originPort}
              </span>
              {midPorts.map((p, i) => (
                <span key={i} style={{ display:'flex', alignItems:'center', gap:6, color:'var(--primary-color)' }}>
                  <span style={{ width:10, height:10, borderRadius:'50%', background:'#2563eb', border:'2px solid white', display:'inline-block' }} />
                  Stop {i + 1} · {p}
                </span>
              ))}
              <span style={{ display:'flex', alignItems:'center', gap:6 }}>
                <span style={{ width:12, height:12, borderRadius:'50%', background:'#ef4444', border:'2px solid white', boxShadow:'0 1px 4px rgba(0,0,0,0.3)', display:'inline-block' }} />
                B · {destPort}
              </span>
              <span style={{ marginLeft:'auto', color:'var(--text-secondary)', fontWeight:500 }}>
                {dist.toLocaleString()} km · {transit} days
              </span>
            </div>

            {/* Map */}
            <div style={{ borderRadius: '0 0 16px 16px', overflow: 'hidden', border: '1px solid var(--border-color)' }}>
              <MapContainer center={[20, 60]} zoom={3} style={{ height: 540, width: '100%' }} scrollWheelZoom zoomControl>
                <TileLayer
                  attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OSM</a> &copy; <a href="https://carto.com/attributions">CARTO</a>'
                  url="https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png"
                  subdomains="abcd"
                />
                <FitBounds coords={coords} />

                {/* Route arc — shadow + main line */}
                {arcPath.length >= 2 && <>
                  <Polyline positions={arcPath} color="#1e40af" weight={8}  opacity={0.15} />
                  <Polyline positions={arcPath} color="#3b82f6" weight={4}  opacity={0.9} />
                </>}

                {/* Origin — green A pin */}
                {coords[0] && (
                  <Marker position={coords[0]} icon={OriginIcon}>
                    <Popup>
                      <div style={{ fontFamily:'Inter,sans-serif', minWidth:160 }}>
                        <div style={{ fontWeight:800, color:'#10b981', fontSize:13, marginBottom:4 }}>🟢 Departure (A)</div>
                        <div style={{ fontWeight:700, fontSize:13 }}>{originPort}</div>
                        <div style={{ fontSize:11, color:'#888', marginTop:2 }}>Starting port</div>
                      </div>
                    </Popup>
                  </Marker>
                )}

                {/* Intermediate stops — numbered blue circles */}
                {midCoords.map((coord, i) => (
                  <Marker key={i} position={coord} icon={stopIcon(i + 1)}>
                    <Popup>
                      <div style={{ fontFamily:'Inter,sans-serif', minWidth:160 }}>
                        <div style={{ fontWeight:800, color:'#2563eb', fontSize:12, marginBottom:4 }}>⚓ Port Stop {i + 1}</div>
                        <div style={{ fontWeight:700, fontSize:13 }}>{midPorts[i]}</div>
                        <div style={{ fontSize:11, color:'#888', marginTop:2 }}>Intermediate waypoint</div>
                      </div>
                    </Popup>
                  </Marker>
                ))}

                {/* Destination — red B pin */}
                {coords.length > 1 && coords[coords.length - 1] && (
                  <Marker position={coords[coords.length - 1]} icon={DestIcon}>
                    <Popup>
                      <div style={{ fontFamily:'Inter,sans-serif', minWidth:160 }}>
                        <div style={{ fontWeight:800, color:'#ef4444', fontSize:13, marginBottom:4 }}>🔴 Arrival (B)</div>
                        <div style={{ fontWeight:700, fontSize:13 }}>{destPort}</div>
                        <div style={{ fontSize:11, color:'#888', marginTop:2 }}>Destination port</div>
                      </div>
                    </Popup>
                  </Marker>
                )}
              </MapContainer>
            </div>
          </motion.div>

          {/* ── RIGHT PANEL ─────────────────────────────────── */}
          <motion.div initial={{ opacity:0, x:16 }} animate={{ opacity:1, x:0 }} transition={{ delay:0.1 }} style={{ display:'flex', flexDirection:'column', gap:12 }}>

            {/* KPI cards */}
            <div style={{ display:'grid', gridTemplateColumns:'1fr 1fr', gap:10 }}>
              {[
                { icon:<MdLocationOn size={18}/>,    label:'Distance',    val:`${dist.toLocaleString()} km`,   color:'var(--primary-color)', bg:'rgba(37,99,235,0.1)'   },
                { icon:<MdSchedule size={18}/>,      label:'Transit',     val:`${transit} days`,               color:'var(--warning)',       bg:'rgba(245,158,11,0.1)'  },
                { icon:<MdAnchor size={18}/>,        label:'Port Stops',  val:`${ports.length}`,               color:'var(--success)',       bg:'rgba(16,185,129,0.1)'  },
                { icon:<MdDirectionsBoat size={18}/>,label:'Route Hops',  val:`${Math.max(0,ports.length-1)}`, color:'var(--info)',          bg:'rgba(14,165,233,0.1)'  },
              ].map((k,i) => (
                <div key={i} className="glass-card" style={{ padding:'12px 14px', display:'flex', alignItems:'center', gap:10 }}>
                  <div style={{ width:36, height:36, borderRadius:10, background:k.bg, display:'flex', alignItems:'center', justifyContent:'center', color:k.color, flexShrink:0 }}>{k.icon}</div>
                  <div>
                    <div style={{ fontSize:10, fontWeight:600, color:'var(--text-secondary)', textTransform:'uppercase', letterSpacing:'0.4px' }}>{k.label}</div>
                    <div style={{ fontSize:16, fontWeight:800, color:k.color }}>{k.val}</div>
                  </div>
                </div>
              ))}
            </div>

            {/* Route timeline */}
            <div className="glass-card" style={{ padding:'16px' }}>
              <div style={{ fontWeight:700, fontSize:13, marginBottom:14, display:'flex', alignItems:'center', gap:6 }}>
                <MdDirectionsBoat size={16} color="var(--primary-color)" /> Port-to-Port Sequence
              </div>
              <div style={{ display:'flex', flexDirection:'column' }}>
                {ports.map((port, i) => {
                  const isFirst = i === 0, isLast = i === ports.length - 1;
                  const dotBg   = isFirst ? '#10b981' : isLast ? '#ef4444' : '#2563eb';
                  const label   = isFirst ? 'Departure' : isLast ? 'Arrival' : `Stop ${i}`;
                  return (
                    <div key={i} style={{ display:'flex', gap:12, alignItems:'stretch' }}>
                      {/* timeline spine */}
                      <div style={{ display:'flex', flexDirection:'column', alignItems:'center', width:22, flexShrink:0 }}>
                        <div style={{ width:14, height:14, borderRadius:'50%', background:dotBg, border:'2.5px solid white', boxShadow:`0 0 0 2px ${dotBg}40`, flexShrink:0, marginTop:4 }} />
                        {!isLast && <div style={{ width:2, flex:1, background:'var(--border-color)', margin:'3px 0', minHeight:18 }} />}
                      </div>
                      {/* label */}
                      <div style={{ paddingBottom: isLast ? 0 : 14 }}>
                        <div style={{ fontSize:13, fontWeight: isFirst||isLast ? 700 : 500, color: isFirst?'#10b981' : isLast?'#ef4444' : 'var(--text-primary)' }}>{port}</div>
                        <div style={{ fontSize:10, color:'var(--text-secondary)', marginTop:1 }}>{label}</div>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Supplier info */}
            <div className="glass-card" style={{ padding:'14px 16px', background:'linear-gradient(135deg,rgba(37,99,235,0.06),rgba(29,78,216,0.1))', border:'1px solid rgba(37,99,235,0.2)' }}>
              <div style={{ fontWeight:700, fontSize:12, color:'var(--text-secondary)', textTransform:'uppercase', letterSpacing:'0.5px', marginBottom:10 }}>Selected Supplier</div>
              <div style={{ fontWeight:800, fontSize:15, color:'var(--text-primary)', marginBottom:4 }}>{selectedName}</div>
              <div style={{ fontSize:12, color:'var(--text-secondary)' }}>
                {originPort} <span style={{ color:'var(--primary-color)', margin:'0 4px' }}>→</span>
                {midPorts.length > 0 && <>{midPorts.join(' → ')} <span style={{ color:'var(--primary-color)', margin:'0 4px' }}>→</span></>}
                {destPort}
              </div>
            </div>

            {/* Approve button */}
            <button
              className="btn-primary-gradient"
              style={{ width:'100%', padding:'12px', fontSize:13, display:'flex', alignItems:'center', justifyContent:'center', gap:8, borderRadius:12 }}
              onClick={() => alert(`Route approved: ${routeStr}\nDistance: ${dist.toLocaleString()} km · Transit: ${transit} days`)}
            >
              <MdCheckCircle size={18} /> Approve Logistics Path
            </button>

          </motion.div>
        </div>
      )}
    </div>
  );
};

export default RouteOptimization;
