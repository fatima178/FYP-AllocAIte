"""Shared default weighting configuration for ranking and settings."""

FIXED_SEMANTIC_WEIGHT = 0.35

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


def resolve_effective_weight_map(raw_weights):
    resolved = default_weight_map()
    if not isinstance(raw_weights, dict):
        return resolved

    normalized = {}
    for key in WEIGHT_KEYS:
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
        if value is not None and value > 0:
            resolved[key] = value

    resolved["semantic"] = FIXED_SEMANTIC_WEIGHT
    return resolved
