import api from './api';

export const supplierApi = {
  getCurrentSuppliers: () => api.get('/api/v1/supplier/current'),
  recommendSupplier: (data) => api.post('/api/v1/supplier/recommend', data),
  analyzeRoute: (data) => api.post('/api/v1/supplier/route', data),
  predictDelay: (data) => api.post('/api/v1/supplier/delay', data),
  predictCost: (data) => api.post('/api/v1/supplier/cost', data),
  completeAnalysis: (data) => api.post('/api/v1/supplier/complete-analysis', data),
};
