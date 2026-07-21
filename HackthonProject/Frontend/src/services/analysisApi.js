import api from './api';

export const analysisApi = {
  orchestrate: (data) => api.post('/api/v1/orchestrate', data),
};
