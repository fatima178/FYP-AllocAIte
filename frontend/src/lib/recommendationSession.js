const RECOMMENDATIONS_KEY = "recommendations";
const RECOMMENDATION_CONTEXT_KEY = "recommendations_context";

export const loadRecommendations = () => {
  const saved = localStorage.getItem(RECOMMENDATIONS_KEY);
  if (!saved) return [];

  try {
    const parsed = JSON.parse(saved);
    return Array.isArray(parsed) ? parsed : [];
  } catch {
    return [];
  }
};

export const loadRecommendationContext = () => {
  const saved = localStorage.getItem(RECOMMENDATION_CONTEXT_KEY);
  if (!saved) return null;

  try {
    const parsed = JSON.parse(saved);
    if (
      parsed &&
      typeof parsed.task_description === "string" &&
      parsed.start_date &&
      parsed.end_date
    ) {
      return parsed;
    }
  } catch {
    return null;
  }

  return null;
};

export const saveRecommendationSession = ({ recommendations, context }) => {
  localStorage.setItem(RECOMMENDATIONS_KEY, JSON.stringify(recommendations));
  localStorage.setItem(RECOMMENDATION_CONTEXT_KEY, JSON.stringify(context));
};

export const clearRecommendationSession = () => {
  localStorage.removeItem(RECOMMENDATIONS_KEY);
  localStorage.removeItem(RECOMMENDATION_CONTEXT_KEY);
};
