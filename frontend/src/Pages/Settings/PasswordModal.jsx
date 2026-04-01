export default function PasswordModal({
  open,
  passwordVerified,
  passwordForm,
  verifyStatus,
  passwordStatus,
  onClose,
  onChange,
  onVerify,
  onSubmit,
}) {
  if (!open) return null;

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="modal-card" onClick={(event) => event.stopPropagation()}>
        <div className="modal-header">
          <h3>Change Password</h3>
          <button className="modal-close" type="button" onClick={onClose}>×</button>
        </div>

        {!passwordVerified && (
          <form className="settings-form" onSubmit={onVerify}>
            <label>
              Enter Current Password
              <input
                type="password"
                name="current"
                value={passwordForm.current}
                onChange={onChange}
                placeholder="Current password"
              />
            </label>

            <div className="modal-actions">
              <button type="submit" className="primary">Verify Password</button>
              <button type="button" className="cancel-button" onClick={onClose}>Cancel</button>
            </div>

            {verifyStatus && (
              <p className={`status-message ${verifyStatus.type}`}>
                {verifyStatus.message}
              </p>
            )}
          </form>
        )}

        {passwordVerified && (
          <form className="settings-form" onSubmit={onSubmit}>
            {verifyStatus && (
              <p className={`status-message ${verifyStatus.type}`}>
                {verifyStatus.message}
              </p>
            )}

            <div className="form-grid">
              <label>
                New Password
                <input
                  type="password"
                  name="next"
                  value={passwordForm.next}
                  onChange={onChange}
                  placeholder="New password"
                />
              </label>

              <label>
                Confirm New Password
                <input
                  type="password"
                  name="confirm"
                  value={passwordForm.confirm}
                  onChange={onChange}
                  placeholder="Confirm new password"
                />
              </label>
            </div>

            <p className="muted">
              Password must include an uppercase letter and special character.
            </p>

            <div className="modal-actions">
              <button type="submit" className="primary">Update Password</button>
              <button type="button" onClick={onClose}>Close</button>
            </div>

            {passwordStatus && (
              <p className={`status-message ${passwordStatus.type}`}>
                {passwordStatus.message}
              </p>
            )}
          </form>
        )}
      </div>
    </div>
  );
}
