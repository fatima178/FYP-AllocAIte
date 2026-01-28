import { useState } from 'react';
import '../styles/Login.css';
import groupChat from '../images/group-chat.png';
import { apiFetch, APIError } from '../api';

// both login + register form fields stored together
// only one "mode" is active at any time
const initialState = {
  login: { email: '', password: '' },
  register: { name: '', email: '', password: '', confirmPassword: '' },
};

function LoginPage() {
  // determines which form the user sees: login or register
  const [mode, setMode] = useState('login');

  // stores typed input values for both modes
  const [formData, setFormData] = useState(initialState);

  // shows success/error messages to user
  const [status, setStatus] = useState({ type: null, message: null });

  // prevents double submissions by disabling the button during request
  const [isSubmitting, setIsSubmitting] = useState(false);

  // switch login/register tabs and clear any previous messages
  const switchMode = (value) => {
    setMode(value);
    setStatus({ type: null, message: null });
  };

  // update form fields when user types
  // dynamic: updates whichever "mode" is currently active
  const handleChange = (event) => {
    const { name, value } = event.target;

    setFormData((prev) => ({
      ...prev,
      [mode]: {
        ...prev[mode],
        [name]: value,
      },
    }));
  };

  // main form submission handler for login and register
  const handleSubmit = async (event) => {
    event.preventDefault();
    setIsSubmitting(true);
    setStatus({ type: null, message: null });

    // choose API endpoint depending on login/register
    const endpoint = mode === 'login' ? '/login' : '/register';

    // register-only validation
    if (mode === 'register') {
      // require a full name (first + last)
      if (formData.register.name.trim().split(/\s+/).length < 2) {
        setStatus({ type: 'error', message: 'Please enter your full name.' });
        setIsSubmitting(false);
        return;
      }

      // ensure password contains uppercase + special character
      if (
        !/[A-Z]/.test(formData.register.password) ||
        !/[^A-Za-z0-9]/.test(formData.register.password)
      ) {
        setStatus({
          type: 'error',
          message:
            'Password must include an uppercase letter and special character.',
        });
        setIsSubmitting(false);
        return;
      }

      // check that passwords match
      if (formData.register.password !== formData.register.confirmPassword) {
        setStatus({ type: 'error', message: 'Passwords do not match.' });
        setIsSubmitting(false);
        return;
      }
    }

    // prepare payload for API depending on login/register
    let payload;
    if (mode === 'login') {
      payload = {
        ...formData.login,
        email: formData.login.email.trim().toLowerCase(),
      };
    } else {
      const { confirmPassword, ...registerPayload } = formData.register;
      payload = {
        ...registerPayload,
        email: registerPayload.email.trim().toLowerCase(),
      };
    }

    try {
      // send login/register request
      const body = await apiFetch(endpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });

      // if user_id exists, login/register succeeded
      if (body.user_id) {
        const resolvedEmail = body.email || payload.email || '';
        const resolvedName =
          body.name || (mode === 'register' ? payload.name : null) || '';

        // store user session in local storage
        localStorage.setItem('user_id', body.user_id);

        if (resolvedEmail) localStorage.setItem('email', resolvedEmail);
        if (resolvedName) localStorage.setItem('name', resolvedName);
        if (body.created_at) localStorage.setItem('member_since', body.created_at);

        localStorage.removeItem('active_upload_id');

        // redirect user depending on whether they already uploaded a file
        const redirectPath =
          body.has_upload ? '/dashboard' : '/upload';
        window.location.href = redirectPath;
        return;
      }

      // show success message for register
      setStatus({ type: 'success', message: body.message || 'Success.' });

      // reset form inputs
      setFormData((prev) => ({ ...prev, [mode]: initialState[mode] }));
    } catch (error) {
      // special case: email already registered
      if (
        mode === 'register' &&
        error instanceof APIError &&
        typeof error.body?.detail === 'string' &&
        error.body.detail.includes('Email already registered')
      ) {
        setStatus({
          type: 'error',
          message: (
            <>
              {error.body.detail}
              <button
                type="button"
                className="inline-link"
                onClick={() => switchMode('login')}
              >
                Go to login
              </button>
            </>
          ),
        });
        return;
      }

      // generic backend/network error
      setStatus({ type: 'error', message: error.message });
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="auth-page">

      {/* HERO SECTION (left side) */}
      <section className="hero">
        <div className="hero-brand">
          <div className="logo">
            <img src={groupChat} alt="AllocAIte" />
          </div>

          <div>
            <h1>AllocAIte</h1>
            <p>Staffing Management for Tech Teams</p>
          </div>
        </div>

        {/* feature highlights displayed as bullet cards */}
        <div className="hero-points">
          <div>
            <span>✔</span>
            <div>
              <h3>Smarter Task Allocation</h3>
              <p>
                Automatically match the right employee to each project using AI
                that looks at their skills and availability.
              </p>
            </div>
          </div>

          <div>
            <span>✔</span>
            <div>
              <h3>Intelligent Insights</h3>
              <p>
                See team capacity clearly, find missing skills, and make quick,
                data-based staffing choices.
              </p>
            </div>
          </div>

          <div>
            <span>✔</span>
            <div>
              <h3>Seamless Integration</h3>
              <p>Easily upload your team data from Excel.</p>
            </div>
          </div>
        </div>
      </section>

      {/* RIGHT SIDE: AUTH PANEL (login/register) */}
      <section className="auth-panel">

        {/* tabs to switch between login + register */}
        <div className="tab-switcher">
          {['login', 'register'].map((value) => (
            <button
              key={value}
              type="button"
              className={mode === value ? 'active' : ''}
              onClick={() => switchMode(value)}
            >
              {value === 'login' ? 'Login' : 'Register'}
            </button>
          ))}
        </div>

        {/* actual form card */}
        <form className="auth-card" onSubmit={handleSubmit}>
          <div>
            <h2>{mode === 'login' ? 'Welcome back' : 'Create an account'}</h2>
            <p>
              {mode === 'login'
                ? 'Enter your credentials to access your account.'
                : 'Enter your information to get started.'}
            </p>
          </div>

          {/* full name required only in register mode */}
          {mode === 'register' && (
            <label>
              Full name
              <input
                type="text"
                name="name"
                placeholder="Alex Anderson"
                value={formData.register.name}
                onChange={handleChange}
                required
              />
            </label>
          )}

          {/* email input */}
          <label>
            Email
            <input
              type="email"
              name="email"
              placeholder="name@company.com"
              value={formData[mode].email}
              onChange={handleChange}
              required
            />
          </label>

          {/* password input */}
          <label>
            Password
            <input
              type="password"
              name="password"
              placeholder="Enter your password"
              value={formData[mode].password}
              onChange={handleChange}
              required
              minLength={mode === 'register' ? 6 : undefined}
            />
          </label>

          {/* confirm password for register mode */}
          {mode === 'register' && (
            <label>
              Confirm password
              <input
                type="password"
                name="confirmPassword"
                placeholder="Repeat your password"
                value={formData.register.confirmPassword}
                onChange={handleChange}
                required
                minLength={6}
              />
            </label>
          )}

          {/* submit button for login/register */}
          <button type="submit" className="primary" disabled={isSubmitting}>
            {isSubmitting
              ? 'Please wait…'
              : mode === 'login'
              ? 'Sign In'
              : 'Sign Up'}
          </button>

          {/* success or error messages */}
          {status.type && (
            <p className={`status ${status.type}`}>{status.message}</p>
          )}
        </form>
      </section>
    </div>
  );
}

export default LoginPage;
