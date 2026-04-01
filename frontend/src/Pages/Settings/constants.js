export const FIXED_SEMANTIC_WEIGHT = 0.35;
export const MANAGER_WEIGHT_TOTAL = 0.65;
export const DEFAULT_MANAGER_WEIGHTS = {
  skills_fit: 0.25,
  experience_role: 0.2,
  availability_balance: 0.1,
  growth_potential: 0.05,
  past_feedback: 0.05,
};

export const WEIGHTING_FIELDS = [
  {
    key: "skills_fit",
    label: "Skills Fit",
    description: "Technical, possible, and soft skill signals",
  },
  {
    key: "experience_role",
    label: "Experience & Role",
    description: "Relevant experience and role match",
  },
  {
    key: "availability_balance",
    label: "Availability",
    description: "Availability and workload balance",
  },
  {
    key: "growth_potential",
    label: "Growth Potential",
    description: "Preferences and learning goals",
  },
  {
    key: "past_feedback",
    label: "Past Feedback",
    description: "Historical manager feedback on similar tasks",
  },
];

export const HISTORY_PAGE_SIZE = 5;
export const GROUP_TO_DETAIL_SHARES = {
  skills_fit: {
    skill: 0.88,
    possible_skill: 0.02,
    soft_skill: 0.08,
    possible_soft_skill: 0.02,
  },
  experience_role: {
    experience: 0.652174,
    role: 0.347826,
  },
  availability_balance: {
    availability: 0.833333,
    fairness: 0.166667,
  },
  growth_potential: {
    preferences: 1.0,
  },
  past_feedback: {
    feedback: 1.0,
  },
};

export const ADJUSTABLE_WEIGHT_BUDGET = MANAGER_WEIGHT_TOTAL;
