import api from './api';

export const reserveApi = {
  // Full SPR optimization - expects the structured input from the orchestrator
  optimize: (data) => api.post('/api/v1/optimize', data),
};
