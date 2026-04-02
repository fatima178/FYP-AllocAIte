export default function TaskFormModal({
  open,
  title,
  formData,
  error,
  saving,
  submitLabel,
  weekData,
  onClose,
  onChange,
  onSubmit,
  onDelete,
  deleting = false,
}) {
  if (!open) return null;

  return (
    <div className="task-modal">
      <div className="task-modal__content">
        <div className="task-modal__header">
          <h2>{title}</h2>
          <button type="button" onClick={onClose} aria-label="Close">×</button>
        </div>

        <form onSubmit={onSubmit}>
          <label>
            Task name
            <input
              type="text"
              value={formData.title}
              onChange={(e) => onChange('title', e.target.value)}
              required
            />
          </label>

          <label>
            Start date
            <input
              type="date"
              value={formData.startDate}
              onChange={(e) => onChange('startDate', e.target.value)}
              required
            />
          </label>

          <label>
            End date
            <input
              type="date"
              value={formData.endDate}
              onChange={(e) => onChange('endDate', e.target.value)}
              required
              min={formData.startDate}
            />
          </label>

          <label>
            Total hours
            <input
              type="number"
              min="0.5"
              step="0.5"
              value={formData.totalHours}
              onChange={(e) => onChange('totalHours', e.target.value)}
              required
            />
          </label>

          <label>
            Assign to
            <select value={formData.employeeId} onChange={(e) => onChange('employeeId', e.target.value)}>
              {(weekData.employee_options || []).map((option) => (
                <option
                  key={option.employee_id === null ? 'unassigned' : option.employee_id}
                  value={option.employee_id === null ? '' : option.employee_id}
                >
                  {option.name}
                </option>
              ))}
            </select>
          </label>

          {error && <p className="form-error">{error}</p>}

          <div className="modal-actions">
            <button type="button" className="ghost-btn" onClick={onClose}>Cancel</button>
            {onDelete ? (
              <button type="button" className="ghost-btn" onClick={onDelete} disabled={deleting}>
                {deleting ? 'Deleting...' : 'Delete'}
              </button>
            ) : null}
            <button type="submit" className="primary-btn" disabled={saving}>
              {saving ? 'Saving...' : submitLabel}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
