import api from './api';

export const riskApi = {
  runRiskAssessment: () => api.get('/api/v1/risk/run'),
};
