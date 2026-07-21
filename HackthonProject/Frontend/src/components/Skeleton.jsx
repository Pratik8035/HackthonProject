import React from 'react';

export const DashboardSkeleton = () => (
  <div className="py-4 page-container">
    <div className="d-flex justify-content-between mb-4">
      <div className="placeholder-glow w-25"><span className="placeholder col-12 bg-secondary rounded" style={{ height: '32px' }}></span></div>
      <div className="placeholder-glow w-25 text-end"><span className="placeholder col-6 bg-secondary rounded" style={{ height: '32px' }}></span></div>
    </div>
    <div className="row g-4 mb-4">
      {[1, 2, 3, 4].map(i => (
        <div key={i} className="col-md-3">
          <div className="glass-card p-4 placeholder-glow" style={{ height: '120px' }}>
            <span className="placeholder col-4 bg-secondary rounded mb-3 d-block" style={{ height: '24px' }}></span>
            <span className="placeholder col-8 bg-secondary rounded" style={{ height: '32px' }}></span>
          </div>
        </div>
      ))}
    </div>
    <div className="row g-4">
      <div className="col-lg-4">
        <div className="glass-card placeholder-glow" style={{ height: '300px' }}>
          <span className="placeholder col-12 bg-secondary rounded h-100 opacity-25"></span>
        </div>
      </div>
      <div className="col-lg-8">
        <div className="glass-card placeholder-glow" style={{ height: '300px' }}>
          <span className="placeholder col-12 bg-secondary rounded h-100 opacity-25"></span>
        </div>
      </div>
    </div>
  </div>
);
