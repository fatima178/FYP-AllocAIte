export default function GrowthTab({
  growthText,
  savedGrowthText,
  growthStatus,
  onGrowthChange,
  onInsertPrompt,
  onSubmitGrowth,
  onLoadSaved,
  onClearSaved,
}) {
  return (
    <div className="employee-grid">
      <section className="panel panel-wide">
        <p className="section-label">Growth</p>
        <h2>Where you want to grow next</h2>
        <p className="muted">
          Give the system clearer signals about the work you enjoy, the skills you want to build, and the kinds of projects you want to move toward.
        </p>

        <div className="prompt-row">
          <button type="button" className="prompt-chip" onClick={() => onInsertPrompt('I want to develop: ')}>
            What skills do you want to develop?
          </button>
          <button type="button" className="prompt-chip" onClick={() => onInsertPrompt('I enjoy work that involves: ')}>
            What type of work do you enjoy?
          </button>
          <button type="button" className="prompt-chip" onClick={() => onInsertPrompt('Projects I am interested in: ')}>
            What projects interest you?
          </button>
        </div>

        <div className="growth-layout">
          <form onSubmit={onSubmitGrowth} className="growth-form">
            <label>
              Growth goals
              <textarea
                className="growth-textarea"
                rows="8"
                placeholder={'What skills do you want to develop?\nWhat type of work do you enjoy?\nWhat projects interest you?'}
                value={growthText}
                onChange={(e) => onGrowthChange(e.target.value)}
              />
            </label>

            <div className="actions">
              <button className="primary" type="submit">Save goals</button>
              <button type="button" className="ghost" onClick={onLoadSaved} disabled={!savedGrowthText}>
                Load saved
              </button>
            </div>

            {growthStatus && <p className={`status ${growthStatus.type || ''}`}>{growthStatus.message}</p>}
          </form>

          <aside className="saved-growth-card">
            <p className="section-label">Saved direction</p>
            <h3>Current profile signal</h3>
            {savedGrowthText ? (
              <p className="muted saved-growth-text">{savedGrowthText}</p>
            ) : (
              <p className="empty">No preferences or learning goals saved yet.</p>
            )}
            <div className="actions">
              <button type="button" className="ghost" onClick={onLoadSaved} disabled={!savedGrowthText}>
                Edit saved text
              </button>
              <button type="button" className="ghost" onClick={onClearSaved} disabled={!savedGrowthText}>
                Clear saved
              </button>
            </div>
          </aside>
        </div>
      </section>
    </div>
  );
}
