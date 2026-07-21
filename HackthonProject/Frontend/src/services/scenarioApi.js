import api from './api';

export const scenarioApi = {
  listScenarios: (riskScore = null) => {
    const params = riskScore != null ? `?risk_score=${riskScore}` : '';
    return api.get(`/api/v1/scenario/list${params}`);
  },
  runEffects: (scenarioId, scenarioName, probability) =>
    api.post(`/api/v1/scenario/effects?scenario_id=${scenarioId}&scenario_name=${scenarioName}&probability=${probability}`),
};
