export default function CompletedTasksPanel({
  open,
  completedLoading,
  completedError,
  completedTasks,
  onClose,
  onOpenFeedback,
}) {
  if (!open) return null;

  return (
    <div className="task-modal">
      <div className="task-modal__content task-modal__content--feedback-list">
        <div className="task-modal__header">
          <h2>Completed Tasks Feedback</h2>
          <button type="button" onClick={onClose} aria-label="Close">×</button>
        </div>

        {completedLoading && <p className="calendar-message">Loading completed tasks...</p>}
        {completedError && <p className="calendar-message error">{completedError}</p>}
        {!completedLoading && !completedError && completedTasks.length === 0 && (
          <p className="calendar-message empty">No completed tasks yet.</p>
        )}

        <p className="calendar-message">
          Feedback can be submitted for recommendation-generated tasks, even if they are still in progress.
        </p>

        <div className="completed-list">
          {completedTasks.filter((task) => task.task_id).map((task) => (
            <div key={task.history_id} className="completed-card">
              <div>
                <h4>{task.title}</h4>
                <p className="completed-meta">
                  {task.employee_name} • {task.start_date} – {task.end_date}
                </p>
                {Array.isArray(task.outcome_tags) && task.outcome_tags.length > 0 && (
                  <div className="outcome-tag-list">
                    {task.outcome_tags.map((tag) => (
                      <span key={`${task.task_id}-${tag}`} className="outcome-tag-pill">
                        {tag}
                      </span>
                    ))}
                  </div>
                )}
              </div>
              <div className="completed-actions">
                {(task.source_type === 'current' || task.is_completed) ? (
                  task.performance_rating ? (
                    <button type="button" className="ghost-btn" onClick={() => onOpenFeedback(task)}>
                      Edit Feedback ({task.performance_rating})
                    </button>
                  ) : (
                    <button type="button" className="primary-btn" onClick={() => onOpenFeedback(task)}>
                      Add Feedback
                    </button>
                  )
                ) : (
                  <span className="muted">No feedback for removed tasks</span>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
