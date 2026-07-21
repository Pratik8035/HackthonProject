import React, { Suspense, lazy } from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import MainLayout from './layouts/MainLayout';
import { ThemeProvider } from './contexts/ThemeContext';
import { AnalysisProvider } from './contexts/AnalysisContext';

// Lazy loading pages
const Dashboard = lazy(() => import('./pages/Dashboard'));
const LiveRisk = lazy(() => import('./pages/LiveRisk'));
const ScenarioImpact = lazy(() => import('./pages/ScenarioImpact'));
const AlternativeSupplier = lazy(() => import('./pages/AlternativeSupplier'));
const RouteOptimization = lazy(() => import('./pages/RouteOptimization'));
const DelayPrediction = lazy(() => import('./pages/DelayPrediction'));
const CostPrediction = lazy(() => import('./pages/CostPrediction'));
const StrategicReserve = lazy(() => import('./pages/StrategicReserve'));
const IntegratedAnalysis = lazy(() => import('./pages/IntegratedAnalysis'));
const ReportsPage = lazy(() => import('./pages/ReportsPage'));

const LoadingFallback = () => (
  <div className="d-flex justify-content-center align-items-center h-100" style={{ minHeight: '60vh' }}>
    <div className="spinner-border text-primary" role="status" style={{ width: '3rem', height: '3rem' }}>
      <span className="visually-hidden">Loading...</span>
    </div>
  </div>
);

function App() {
  return (
    <ThemeProvider>
      <AnalysisProvider>
        <Router>
          <MainLayout>
            <Suspense fallback={<LoadingFallback />}>
              <Routes>
                <Route path="/" element={<Dashboard />} />
                <Route path="/live-risk" element={<LiveRisk />} />
                <Route path="/scenario-impact" element={<ScenarioImpact />} />
                <Route path="/alternative-supplier" element={<AlternativeSupplier />} />
                <Route path="/route-optimization" element={<RouteOptimization />} />
                <Route path="/delay-prediction" element={<DelayPrediction />} />
                <Route path="/cost-prediction" element={<CostPrediction />} />
                <Route path="/strategic-reserve" element={<StrategicReserve />} />
                <Route path="/integrated-analysis" element={<IntegratedAnalysis />} />
                <Route path="/reports" element={<ReportsPage />} />
              </Routes>
            </Suspense>
          </MainLayout>
        </Router>
      </AnalysisProvider>
    </ThemeProvider>
  );
}

export default App;
