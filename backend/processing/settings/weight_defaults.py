"""Shared default weighting configuration for ranking and settings."""

FIXED_SEMANTIC_WEIGHT = 0.35

# detailed weights are what the recommendation scoring code actually uses
DEFAULT_DETAIL_WEIGHTS = {
    "semantic": FIXED_SEMANTIC_WEIGHT,
    "skill": 0.22,
    "possible_skill": 0.005,
    "soft_skill": 0.02,
    "possible_soft_skill": 0.005,
    "experience": 0.130435,
    "role": 0.069565,
    "availability": 0.083333,
    "fairness": 0.016667,
    "preferences": 0.05,
    "feedback": 0.05,
}

# the settings page groups detailed values into friendlier slider categories
GROUP_TO_DETAIL_SHARES = {
    "skills_fit": {
        "skill": 0.88,
        "possible_skill": 0.02,
        "soft_skill": 0.08,
        "possible_soft_skill": 0.02,
    },
    "experience_role": {
        "experience": 0.652174,
        "role": 0.347826,
    },
    "availability_balance": {
        "availability": 0.833333,
        "fairness": 0.166667,
    },
    "growth_potential": {
        "preferences": 1.0,
    },
    "past_feedback": {
        "feedback": 1.0,
    },
}

WEIGHT_KEYS = (
    "semantic",
    "skill",
    "possible_skill",
    "soft_skill",
    "possible_soft_skill",
    "experience",
    "role",
    "availability",
    "fairness",
    "preferences",
    "feedback",
)

NON_SEMANTIC_WEIGHT_KEYS = tuple(key for key in WEIGHT_KEYS if key != "semantic")


def default_weight_tuple():
    return tuple(DEFAULT_DETAIL_WEIGHTS[key] for key in WEIGHT_KEYS)


def default_weight_map():
    return dict(DEFAULT_DETAIL_WEIGHTS)


def default_group_weight_map():
    # adds up the detailed defaults so the frontend starts with grouped defaults
    return {
        group_key: round(
            sum(DEFAULT_DETAIL_WEIGHTS[detail_key] for detail_key in detail_shares),
            6,
        )
        for group_key, detail_shares in GROUP_TO_DETAIL_SHARES.items()
    }


def weight_config():
    # returned to the frontend so backend and frontend use the same weight rules
    manager_weight_total = round(1 - FIXED_SEMANTIC_WEIGHT, 6)
    return {
        "fixed_semantic_weight": FIXED_SEMANTIC_WEIGHT,
        "manager_weight_total": manager_weight_total,
        "adjustable_weight_budget": manager_weight_total,
        "default_manager_weights": default_group_weight_map(),
        "group_to_detail_shares": GROUP_TO_DETAIL_SHARES,
    }


def resolve_effective_weight_map(raw_weights):
    # if the user has not saved custom weights, fall back to default values
    resolved = default_weight_map()
    if not isinstance(raw_weights, dict):
        return resolved

    normalized = {}
    for key in WEIGHT_KEYS:
        # convert database values into floats where possible
        value = raw_weights.get(key)
        try:
            normalized[key] = float(value) if value is not None else None
        except (TypeError, ValueError):
            normalized[key] = None

    non_semantic_values = [normalized[key] for key in NON_SEMANTIC_WEIGHT_KEYS]
    has_any_non_semantic_value = any(value is not None and value > 0 for value in non_semantic_values)
    if not has_any_non_semantic_value:
        return resolved

    for key, value in normalized.items():
        # keep default value for missing/zero fields, but use saved positive values
        if value is not None and value > 0:
            resolved[key] = value

    resolved["semantic"] = FIXED_SEMANTIC_WEIGHT
    return resolved
