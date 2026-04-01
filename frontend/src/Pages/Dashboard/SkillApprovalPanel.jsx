import { formatSkillLabel } from "../../lib/formatters";

export default function SkillApprovalPanel({
  visible,
  loading,
  error,
  requests,
  reviewingSkillId,
  onReview,
}) {
  if (!visible) return null;

  return (
    <div className="approval-panel">
      <div className="approval-panel__header">
        <div>
          <h2>Skill Approval</h2>
          <p>Review self reported employee skills before they affect recommendations.</p>
        </div>
      </div>

      {loading && <p className="approval-panel__message">Loading skill requests...</p>}
      {error && <p className="approval-panel__message error">{error}</p>}

      {!loading && requests.length > 0 && (
        <div className="approval-list">
          {requests.map((item) => (
            <div key={item.request_id} className="approval-card">
              <div>
                <strong>{formatSkillLabel(item.skill_name)}</strong>
                <p>{item.employee_name} • {item.skill_type} • {item.years_experience} years</p>
              </div>
              <div className="approval-actions">
                <button
                  type="button"
                  className="approval-btn secondary"
                  disabled={reviewingSkillId === item.request_id}
                  onClick={() => onReview(item.request_id, false)}
                >
                  Reject
                </button>
                <button
                  type="button"
                  className="approval-btn primary"
                  disabled={reviewingSkillId === item.request_id}
                  onClick={() => onReview(item.request_id, true)}
                >
                  {reviewingSkillId === item.request_id ? "Saving..." : "Approve"}
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
