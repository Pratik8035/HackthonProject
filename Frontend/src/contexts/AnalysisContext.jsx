import React, { createContext, useState, useContext } from 'react';

const AnalysisContext = createContext();

export const AnalysisProvider = ({ children }) => {
  const [currentSupplier, setCurrentSupplier] = useState(null);
  const [selectedAlternative, setSelectedAlternative] = useState(null);
  const [analysisResult, setAnalysisResult] = useState(null);
  const [loading, setLoading] = useState(false);

  // Shared live risk result — populated by LiveRisk page, consumed by
  // ScenarioImpact (for risk-weighted scenario probabilities) and
  // AlternativeSupplier (for risk-score-driven supplier ranking).
  const [liveRiskResult, setLiveRiskResult] = useState(null);

  // Shared scenario effects result — populated by ScenarioImpact page,
  // consumed by AlternativeSupplier to inform supplier recommendations.
  const [scenarioEffects, setScenarioEffects] = useState(null);

  return (
    <AnalysisContext.Provider value={{
      currentSupplier, setCurrentSupplier,
      selectedAlternative, setSelectedAlternative,
      analysisResult, setAnalysisResult,
      loading, setLoading,
      liveRiskResult, setLiveRiskResult,
      scenarioEffects, setScenarioEffects,
    }}>
      {children}
    </AnalysisContext.Provider>
  );
};

export const useAnalysis = () => useContext(AnalysisContext);
