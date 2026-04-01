export default function EditDetailsModal({
  open,
  detailsForm,
  detailsStatus,
  onClose,
  onChange,
  onSubmit,
}) {
  if (!open) return null;

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="modal-card" onClick={(event) => event.stopPropagation()}>
        <div className="modal-header">
          <h3>Edit Account Details</h3>
          <button className="modal-close" type="button" onClick={onClose}>×</button>
        </div>

        <form className="settings-form" onSubmit={onSubmit}>
          <div className="form-grid">
            <label>
              Name
              <input
                type="text"
                name="name"
                value={detailsForm.name}
                onChange={onChange}
                placeholder="Your name"
              />
            </label>

            <label>
              Email
              <input
                type="email"
                name="email"
                value={detailsForm.email}
                onChange={onChange}
                placeholder="you@email.com"
              />
            </label>
          </div>

          <div className="modal-actions">
            <button type="submit" className="primary">Save Changes</button>
            <button type="button" className="cancel-button" onClick={onClose}>Cancel</button>
          </div>

          {detailsStatus && (
            <p className={`status-message ${detailsStatus.type}`}>
              {detailsStatus.message}
            </p>
          )}
        </form>
      </div>
    </div>
  );
}
