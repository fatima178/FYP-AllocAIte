import { useState } from 'react';
import '../styles/Register.css';
import { apiFetch, APIError } from '../api';

function Register() {
  // stores the values typed in the form fields
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    password: '',
    confirmPassword: '',
  });

  // stores an error or success message (shown under the submit button)
  const [status, setStatus] = useState({ type: null, message: null });

  // used to disable the button + show loading state
  const [isSubmitting, setIsSubmitting] = useState(false);

  // sends the user back to login page
  const goToLogin = () => {
    window.location.href = '/';
  };

  // updates the form state every time user types something
  const handleChange = (event) => {
    const { name, value } = event.target;
    // override only the input that changed
    setFormData((prev) => ({ ...prev, [name]: value }));
  };

  // runs when the user presses "Sign up"
  const handleSubmit = async (event) => {
    event.preventDefault();
    setIsSubmitting(true);
    setStatus({ type: null, message: '' });

    // make sure the user typed first + last name
    if (formData.name.trim().split(/\s+/).length < 2) {
      setStatus({ type: 'error', message: 'Please enter your full name.' });
      setIsSubmitting(false);
      return;
    }

    // enforce password rule (capital letter + special character)
    const password = formData.password;
    if (!/[A-Z]/.test(password) || !/[^A-Za-z0-9]/.test(password)) {
      setStatus({
        type: 'error',
        message: 'Password must include an uppercase letter and special character.',
      });
      setIsSubmitting(false);
      return;
    }

    // ensure the 2 passwords match
    if (formData.password !== formData.confirmPassword) {
      setStatus({ type: 'error', message: 'Passwords do not match.' });
      setIsSubmitting(false);
      return;
    }

    // remove confirmPassword before sending to backend
    const { confirmPassword, ...payload } = formData;

    try {
      // send register request
      const body = await apiFetch('/register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });

      // if backend returns a user_id, registration succeeded
      if (body.user_id && payload.email) {
        localStorage.setItem('user_id', body.user_id);
        localStorage.setItem('email', payload.email);

        // after register, user goes to upload page
        window.location.href = '/upload';
        return;
      }

      // fallback success message (if backend doesn't return full object)
      setStatus({ type: 'success', message: 'Account created successfully.' });

      // reset form state
      setFormData({ name: '', email: '', password: '', confirmPassword: '' });
    } catch (error) {
      // handle special case: email already exists
      if (
        error instanceof APIError &&
        typeof error.body?.detail === 'string' &&
        error.body.detail.includes('Email already registered')
      ) {
        setStatus({
          type: 'error',
          message: (
            <>
              {error.body.detail}
              {/* quick link to login */}
              <button
                type="button"
                className="inline-link"
                onClick={goToLogin}
              >
                Go to login
              </button>
            </>
          ),
        });
        return;
      }

      // generic error message (network issues, etc.)
      setStatus({ type: 'error', message: error.message });
    } finally {
      // remove loading state
      setIsSubmitting(false);
    }
  };

  return (
    <div className="register-page">
      <form className="register-card" onSubmit={handleSubmit}>
        <h1>Create an account</h1>

        {/* full name field */}
        <label>
          Full name
          <input
            type="text"
            name="name"
            value={formData.name}
            onChange={handleChange}
            placeholder="Alex Anderson"
            required
          />
        </label>

        {/* email field */}
        <label>
          Email address
          <input
            type="email"
            name="email"
            value={formData.email}
            onChange={handleChange}
            placeholder="alex@example.com"
            required
          />
        </label>

        {/* password field */}
        <label>
          Password
          <input
            type="password"
            name="password"
            value={formData.password}
            onChange={handleChange}
            minLength={6}
            placeholder="At least 6 characters"
            required
          />
        </label>

        {/* confirm password */}
        <label>
          Confirm password
          <input
            type="password"
            name="confirmPassword"
            value={formData.confirmPassword}
            onChange={handleChange}
            minLength={6}
            placeholder="Repeat your password"
            required
          />
        </label>

        {/* submit button with loading state */}
        <button type="submit" disabled={isSubmitting}>
          {isSubmitting ? 'Creating account...' : 'Sign up'}
        </button>

        {/* success or error messages */}
        {status.type && (
          <p className={`status ${status.type}`}>{status.message}</p>
        )}
      </form>
    </div>
  );
}

export default Register;
