export default function AccountSection({ account, formatMemberSince, onEdit, onChangePassword }) {
  return (
    <div className="settings-card">
      <h2>Account Details</h2>
      <p><strong>Name:</strong> {account.name}</p>
      <p><strong>Email:</strong> {account.email}</p>
      <p><strong>Member Since:</strong> {formatMemberSince(account.member_since)}</p>

      <div className="button-row">
        <button onClick={onEdit}>Edit Details</button>
        <button onClick={onChangePassword}>Change Password</button>
      </div>
    </div>
  );
}
