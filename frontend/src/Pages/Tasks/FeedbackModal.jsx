import { OUTCOME_TAG_OPTIONS } from "./utils";

export default function FeedbackModal({
  open,
  feedbackTarget,
  feedbackRating,
  feedbackNotes,
  feedbackOutcomeTags,
  feedbackSubmitting,
  onClose,
  onRatingChange,
  onNotesChange,
  onOutcomeTagsChange,
  onSubmit,
  onClear,
}) {
  if (!open || !feedbackTarget) return null;

  return (
    <div className="task-modal">
      <div className="task-modal__content task-modal__content--feedback">
        <div className="task-modal__header">
          <h2>Assignment Feedback</h2>
          <button type="button" onClick={onClose} aria-label="Close">×</button>
        </div>
        <form>
          <label>
            Performance rating
            <select value={feedbackRating} onChange={(e) => onRatingChange(e.target.value)} disabled={feedbackSubmitting}>
              <option value="">Select rating</option>
              <option value="Excellent">Excellent</option>
              <option value="Good">Good</option>
              <option value="Average">Average</option>
              <option value="Poor">Poor</option>
            </select>
          </label>
          <label>
            Optional feedback notes
            <textarea rows={3} value={feedbackNotes} onChange={(e) => onNotesChange(e.target.value)} disabled={feedbackSubmitting} />
          </label>
          <div className="outcome-tags-group">
            <p className="outcome-tags-title">Outcome tags</p>
            <div className="outcome-tags-options">
              {OUTCOME_TAG_OPTIONS.map((tag) => (
                <label key={tag} className="outcome-tag-option">
                  <input
                    type="checkbox"
                    checked={feedbackOutcomeTags.includes(tag)}
                    onChange={(e) => {
                      onOutcomeTagsChange((prev) => {
                        if (e.target.checked) return [...prev, tag];
                        return prev.filter((item) => item !== tag);
                      });
                    }}
                    disabled={feedbackSubmitting}
                  />
                  <span>{tag}</span>
                </label>
              ))}
            </div>
          </div>
          <div className="modal-actions">
            {feedbackTarget.performance_rating ? (
              <button type="button" className="ghost-btn" onClick={onClear} disabled={feedbackSubmitting}>
                Clear Feedback
              </button>
            ) : null}
            <button type="button" className="ghost-btn" onClick={onClose} disabled={feedbackSubmitting}>Cancel</button>
            <button type="button" className="primary-btn" onClick={onSubmit} disabled={feedbackSubmitting}>
              {feedbackSubmitting ? 'Submitting...' : 'Submit Feedback'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
