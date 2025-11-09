import { useState } from 'react';
import '../styles/Login.css';
import groupChat from '../images/group-chat.png';

// if there’s no environment variable set, use the local backend
const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8001';

// keeping both forms (login + register) in one state
const initialState = {
  login: { email: '', password: '' },
  register: { name: '', email: '', password: '', confirmPassword: '' },
};

function LoginPage() {
  // handles whether user is on login or register mode
  const [mode, setMode] = useState('login');

  // stores form input values for both modes
  const [formData, setFormData] = useState(initialState);

  // handles any success or error messages shown to user
  const [status, setStatus] = useState({ type: null, message: null });

  // shows loading state when form is being submitted
  const [isSubmitting, setIsSubmitting] = useState(false);

  // switch between login and register tabs
  const switchMode = (value) => {
    setMode(value);
    setStatus({ type: null, message: null });
  };

  // updates input fields when user types
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

  // handles form submission (works for both login + register)
  const handleSubmit = async (event) => {
    event.preventDefault();
    setIsSubmitting(true);
    setStatus({ type: null, message: null });

    const endpoint = mode === 'login' ? '/login' : '/register';

    // basic validation for register form only
    if (mode === 'register') {
      // check if user entered both first and last name
      if (formData.register.name.trim().split(/\s+/).length < 2) {
        setStatus({ type: 'error', message: 'Please enter your full name.' });
        setIsSubmitting(false);
        return;
      }

      // password strength: one capital and one special char
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

      // make sure both password fields match
      if (formData.register.password !== formData.register.confirmPassword) {
        setStatus({ type: 'error', message: 'Passwords do not match.' });
        setIsSubmitting(false);
        return;
      }
    }

    // create payload depending on which mode we’re in
    let payload;
    if (mode === 'login') {
      payload = formData.login;
    } else {
      const { confirmPassword, ...registerPayload } = formData.register;
      payload = registerPayload;
    }

    try {
      // send request to backend
      const response = await fetch(`${API_BASE_URL}${endpoint}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });

      // parse response 
      const body = await response.json().catch(() => ({}));

      if (!response.ok) {
        const detail = body.detail || `Unable to ${mode}.`;

        // handle case where email already exists
        if (mode === 'register' && detail.includes('Email already registered')) {
          setStatus({
            type: 'error',
            message: (
              <>
                {detail}
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
        } else {
          throw new Error(detail);
        }
        return;
      }

      if (body.user_id && payload.email) {
        localStorage.setItem('user_id', body.user_id);
        localStorage.setItem('email', payload.email);
        window.location.href = '/upload';
        return;
      }

      // if everything works, show success message
      setStatus({ type: 'success', message: body.message || 'Success.' });

      // reset form fields after submission
      setFormData((prev) => ({ ...prev, [mode]: initialState[mode] }));
    } catch (error) {
      // handles network or backend errors
      setStatus({ type: 'error', message: error.message });
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="auth-page">
      {/* left side - hero section */}
      <section className="hero">
        <div className="brand">
          <div className="logo">
            <img src={groupChat} alt="AllocAIte" />
          </div>
          <div>
            <h1>AllocAIte</h1>
            <p>Staffing Management for Tech Teams</p>
          </div>
        </div>

        {/* feature highlights */}
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

      {/* right side - login/register panel */}
      <section className="auth-panel">
        {/* switch between login/register */}
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

        {/* form section */}
        <form className="auth-card" onSubmit={handleSubmit}>
          <div>
            <h2>{mode === 'login' ? 'Welcome back' : 'Create an account'}</h2>
            <p>
              {mode === 'login'
                ? 'Enter your credentials to access your account.'
                : 'Enter your information to get started.'}
            </p>
          </div>

          {/* register form shows full name */}
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

          {/* confirm password only shows on register */}
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

          {/* submit button */}
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
