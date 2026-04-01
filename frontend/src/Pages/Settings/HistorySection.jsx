export default function HistorySection({
  loading,
  error,
  items,
  historyStart,
  historyEnd,
  historyTotal,
  historyPage,
  historyTotalPages,
  expandedHistory,
  onPrevious,
  onNext,
  onToggle,
  buildHistoryTitle,
  buildCollapsedHistoryTitle,
  buildTopMatchesLabel,
}) {
  return (
    <div className="settings-card">
      <h2>Recommendation History</h2>
      <p className="muted">Revisit previous recommendation requests, selections, and later feedback.</p>

      {loading && <p className="muted">Loading recommendation history...</p>}
      {error && <p className="status-message error">{error}</p>}

      {!loading && !error && items.length === 0 && (
        <p className="muted">No recommendation history yet.</p>
      )}

      {!loading && items.length > 0 && (
        <>
          <div className="history-pagination">
            <p className="muted">
              Showing {historyStart}-{historyEnd} of {historyTotal} requests
            </p>
            <div className="history-pagination__actions">
              <button type="button" onClick={onPrevious} disabled={loading || historyPage === 1}>
                Previous
              </button>
              <span className="history-page-indicator">
                Page {historyPage} of {historyTotalPages}
              </span>
              <button type="button" onClick={onNext} disabled={loading || historyPage >= historyTotalPages}>
                Next
              </button>
            </div>
          </div>

          <div className="history-list">
            {items.map((item) => (
              <div
                key={item.task_id}
                className={`history-card${expandedHistory[item.task_id] ? " history-card--expanded" : ""}`}
              >
                <button
                  type="button"
                  className="history-card__toggle"
                  onClick={() => onToggle(item.task_id)}
                  aria-expanded={Boolean(expandedHistory[item.task_id])}
                >
                  <div className="history-card__header">
                    <div>
                      <h3>
                        {expandedHistory[item.task_id]
                          ? buildHistoryTitle(item)
                          : buildCollapsedHistoryTitle(item)}
                      </h3>
                      {expandedHistory[item.task_id] && (
                        <p className="history-meta">
                          {item.start_date} - {item.end_date}
                        </p>
                      )}
                    </div>
                    <div className="history-card__header-right">
                      <span className="history-badge">Request #{item.task_id}</span>
                      <span className="history-chevron" aria-hidden="true">
                        {expandedHistory[item.task_id] ? "-" : "+"}
                      </span>
                    </div>
                  </div>

                  {!expandedHistory[item.task_id] && (
                    <div className="history-summary">
                      <div className="history-summary__row">
                        <strong>Top matches:</strong>
                        <span>{buildTopMatchesLabel(item)}</span>
                      </div>
                      <div className="history-summary__row">
                        <span>👤 {item.selected_employee_name || "Not assigned"}</span>
                        <span>⭐ {item.performance_rating || "No rating"}</span>
                      </div>
                    </div>
                  )}
                </button>

                {expandedHistory[item.task_id] && (
                  <>
                    {item.assignment_title && item.assignment_title.trim() !== item.task_description?.trim() && (
                      <p className="history-description">{item.task_description}</p>
                    )}

                    <div className="history-grid">
                      <div>
                        <strong>Chosen employee</strong>
                        <p>{item.selected_employee_name || "Not assigned from recommendations"}</p>
                      </div>
                      <div>
                        <strong>Rating</strong>
                        <p>{item.performance_rating || "No rating yet"}</p>
                      </div>
                      <div>
                        <strong>Feedback date</strong>
                        <p>{item.feedback_at ? new Date(item.feedback_at).toLocaleString() : "No feedback yet"}</p>
                      </div>
                    </div>

                    {Array.isArray(item.outcome_tags) && item.outcome_tags.length > 0 && (
                      <div className="history-tags">
                        {item.outcome_tags.map((tag) => (
                          <span key={`${item.task_id}-${tag}`} className="history-tag">
                            {tag}
                          </span>
                        ))}
                      </div>
                    )}

                    {item.feedback_notes && (
                      <div className="history-notes">
                        <strong>Notes</strong>
                        <p>{item.feedback_notes}</p>
                      </div>
                    )}

                    {Array.isArray(item.top_candidates) && item.top_candidates.length > 0 && (
                      <div className="history-candidates">
                        <strong>Top recommendations</strong>
                        <div className="history-candidate-list">
                          {item.top_candidates.map((candidate) => (
                            <span
                              key={`${item.task_id}-${candidate.rank}-${candidate.employee_id}`}
                              className="history-candidate"
                            >
                              #{candidate.rank} {candidate.employee_name}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}
                  </>
                )}
              </div>
            ))}
          </div>
        </>
      )}
    </div>
  );
}
