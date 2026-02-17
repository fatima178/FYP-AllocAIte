import { useEffect, useState } from 'react';
import '../styles/Invite.css';
import { apiFetch } from '../api';

function InvitePage() {
  const [token, setToken] = useState('');
  const [form, setForm] = useState({ name: '', email: '', password: '', confirm: '' });
  const [status, setStatus] = useState(null);
  const [submitting, setSubmitting] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const tokenParam = params.get('token') || '';
    setToken(tokenParam);
    if (!tokenParam) {
      setStatus({ type: 'error', message: 'Invite token is missing.' });
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (!token) return;
    const loadInfo = async () => {
      setLoading(true);
      try {
        const data = await apiFetch(`/invites/info?token=${encodeURIComponent(token)}`);
        setForm((prev) => ({ ...prev, name: data.name || '' }));
      } catch (err) {
        setStatus({ type: 'error', message: err.message || 'Unable to load invite.' });
      } finally {
        setLoading(false);
      }
    };
    loadInfo();
  }, [token]);

  const handleChange = (event) => {
    const { name, value } = event.target;
    setForm((prev) => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    setStatus(null);

    if (!token) {
      setStatus({ type: 'error', message: 'Invite token is missing.' });
      return;
    }

    if (!form.email.trim()) {
      setStatus({ type: 'error', message: 'Email is required.' });
      return;
    }

    if (!form.password) {
      setStatus({ type: 'error', message: 'Password is required.' });
      return;
    }

    if (form.password !== form.confirm) {
      setStatus({ type: 'error', message: 'Passwords do not match.' });
      return;
    }

    setSubmitting(true);
    try {
      const data = await apiFetch('/invites/accept', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          token,
          email: form.email,
          password: form.password,
        }),
      });

      if (data.user_id) {
        localStorage.removeItem('user_id');
        localStorage.removeItem('account_type');
        localStorage.removeItem('employee_id');
        localStorage.setItem('login_role', 'employee');
        setStatus({ type: 'success', message: 'Account created. Redirecting to login…' });
        setTimeout(() => {
          window.location.href = '/';
        }, 800);
      }
    } catch (err) {
      setStatus({ type: 'error', message: err.message || 'Unable to accept invite.' });
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="invite-page">
      <div className="invite-card">
        <h1>Activate Your Employee Account</h1>
        <p>Create your login to access your employee portal.</p>

        <form onSubmit={handleSubmit}>
          <label>
            Full name
            <input
              type="text"
              name="name"
              value={form.name}
              readOnly
              disabled={loading}
            />
          </label>

          <label>
            Email
            <input
              type="email"
              name="email"
              value={form.email}
              onChange={handleChange}
              placeholder="you@company.com"
              required
            />
          </label>

          <label>
            Password
            <input
              type="password"
              name="password"
              value={form.password}
              onChange={handleChange}
              placeholder="Create a password"
              required
            />
          </label>

          <label>
            Confirm password
            <input
              type="password"
              name="confirm"
              value={form.confirm}
              onChange={handleChange}
              placeholder="Repeat password"
              required
            />
          </label>

          <button type="submit" className="primary" disabled={submitting || loading || !token}>
            {submitting ? 'Creating...' : 'Create account'}
          </button>

          {status && (
            <p className={`status ${status.type || ''}`}>{status.message}</p>
          )}
        </form>
      </div>
    </div>
  );
}

export default InvitePage;
