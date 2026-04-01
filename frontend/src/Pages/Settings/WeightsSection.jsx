export default function WeightsSection({
  weightingFields,
  fixedSemanticWeight,
  totalAllocatedPoints,
  remainingWeightPoints,
  adjustableWeightBudget,
  weights,
  getWeightPoints,
  onWeightChange,
  onSave,
  onReset,
}) {
  return (
    <div className="settings-card">
      <div className="settings-card__header settings-card__header--with-info">
        <h2>Ranking Weightings</h2>
        <div className="info-popover">
          <button
            type="button"
            className="info-popover__trigger"
            aria-label="Show weighting category descriptions"
          >
            ?
          </button>
          <div className="info-popover__panel" role="tooltip">
            {weightingFields.map((item) => (
              <div className="info-popover__item" key={item.key}>
                <strong>{item.label}</strong>
                <span>{item.description}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className="weight-budget-summary">
        <div className="weight-budget-summary__item">
          <span>Semantic similarity</span>
          <strong>{Math.round(fixedSemanticWeight * 100)}%</strong>
        </div>
        <div className="weight-budget-summary__item">
          <span>Allocated</span>
          <strong>{totalAllocatedPoints}%</strong>
        </div>
        <div
          className={
            remainingWeightPoints === 0
              ? "weight-budget-summary__item weight-budget-summary__item--complete"
              : "weight-budget-summary__item weight-budget-summary__item--pending"
          }
        >
          <span>Remaining to allocate</span>
          <strong>{remainingWeightPoints}%</strong>
        </div>
      </div>

      <div className="weight-slider-list">
        {weightingFields.map((field) => {
          const currentPoints = getWeightPoints(weights[field.key]);
          return (
            <div className="weight-slider-card" key={field.key}>
              <div className="weight-slider-card__header">
                <h3>{field.label}</h3>
                <strong>{currentPoints} / {Math.round(adjustableWeightBudget * 100)}</strong>
              </div>
              <input
                type="range"
                min="0"
                max={Math.round(adjustableWeightBudget * 100)}
                step="1"
                value={currentPoints}
                onChange={(e) => onWeightChange(field.key, e.target.value)}
              />
            </div>
          );
        })}
      </div>

      <div className="button-row">
        <button
          className="primary"
          onClick={onSave}
          disabled={remainingWeightPoints !== 0}
        >
          Save Weightings
        </button>
        <button onClick={onReset}>Reset to Default</button>
      </div>
    </div>
  );
}
