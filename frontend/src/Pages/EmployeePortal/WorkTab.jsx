export default function WorkTab({
  currentAssignments,
  pastAssignments,
  assignmentHistory,
  showReasonPreview,
  reasonForm,
  reasonStatus,
  reasonResult,
  onToggleReasonPreview,
  onReasonFormChange,
  onSubmitReasonCheck,
  onOpenCalendar,
}) {
  return (
    <div className="employee-grid">
      <section className="panel">
        <p className="section-label">My work</p>
        <h2>What you are doing now</h2>
        <p className="muted">
          Use this area to track active assignments and jump into your calendar when your availability changes.
        </p>
        <div className="detail-list">
          <div className="detail-item">
            <span>Active assignments</span>
            <strong>{currentAssignments.length}</strong>
          </div>
          <div className="detail-item">
            <span>Completed assignments</span>
            <strong>{pastAssignments.length + assignmentHistory.length}</strong>
          </div>
        </div>
      </section>

      <section className="panel">
        <p className="section-label">Availability</p>
        <h2>Manage your calendar</h2>
        <p className="muted">
          Personal time off and assignment windows live in your calendar. Keep that page updated so workload decisions stay accurate.
        </p>
        <div className="actions">
          <button type="button" className="primary" onClick={onOpenCalendar}>Open my calendar</button>
        </div>
      </section>

      <section className="panel panel-wide">
        <p className="section-label">Assignments</p>
        <h2>Current assignments</h2>
        {currentAssignments.length > 0 ? (
          <div className="assignment-list">
            {currentAssignments.map((assignment) => (
              <article key={assignment.assignment_id} className="assignment-card">
                <div>
                  <h3>{assignment.title}</h3>
                  <p className="muted">
                    {assignment.start_date} to {assignment.end_date}
                  </p>
                </div>
                <div className="assignment-meta">
                  <span>{assignment.total_hours ?? 0}h total</span>
                  <span>{assignment.remaining_hours ?? 0}h remaining</span>
                </div>
              </article>
            ))}
          </div>
        ) : (
          <p className="empty">No active assignments right now.</p>
        )}
      </section>

      <section className="panel panel-wide">
        <div className="advanced-header">
          <div>
            <p className="section-label">Advanced</p>
            <h2>Preview how you match a task</h2>
            <p className="muted">This is optional and kept out of the main flow on purpose.</p>
          </div>
          <button type="button" className="ghost" onClick={onToggleReasonPreview}>
            {showReasonPreview ? 'Hide preview' : 'Show preview'}
          </button>
        </div>

        {showReasonPreview && (
          <form onSubmit={onSubmitReasonCheck} className="form-grid">
            <label>
              Task description
              <input
                type="text"
                value={reasonForm.task_description}
                onChange={(e) => onReasonFormChange("task_description", e.target.value)}
              />
            </label>
            <label>
              Start date
              <input
                type="date"
                value={reasonForm.start_date}
                onChange={(e) => onReasonFormChange("start_date", e.target.value)}
              />
            </label>
            <label>
              End date
              <input
                type="date"
                value={reasonForm.end_date}
                onChange={(e) => onReasonFormChange("end_date", e.target.value)}
              />
            </label>

            <div className="actions full">
              <button className="primary" type="submit">Preview task match</button>
            </div>

            {reasonStatus && <p className={`status ${reasonStatus.type || ''}`}>{reasonStatus.message}</p>}

            {reasonResult && (
              <div className="reason-card">
                <p><strong>Score:</strong> {reasonResult.score_percent}%</p>
                <p><strong>Availability:</strong> {reasonResult.availability_percent}%</p>
                <p><strong>Reason:</strong> {reasonResult.reason}</p>
              </div>
            )}
          </form>
        )}
      </section>
    </div>
  );
}
