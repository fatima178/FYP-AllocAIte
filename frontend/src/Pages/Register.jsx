import { useState } from 'react';
import '../styles/Register.css';
import { apiFetch, APIError } from '../api';

function Register() {
  // stores user input from the form
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    password: '',
    confirmPassword: '',
  });

  // handles success/error messages
  const [status, setStatus] = useState({ type: null, message: null });

  // shows loading state while the form is being submitted
  const [isSubmitting, setIsSubmitting] = useState(false);

  // takes the user to the login page when they click the link
  const goToLogin = () => {
    window.location.href = '/';
  };

  // updates form values as the user types
  const handleChange = (event) => {
    const { name, value } = event.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
  };

  // handles everything that happens when the user clicks "Sign up"
  const handleSubmit = async (event) => {
    event.preventDefault();
    setIsSubmitting(true);
    setStatus({ type: null, message: '' });

    // basic name validation (checks if both first and last name are entered)
    if (formData.name.trim().split(/\s+/).length < 2) {
      setStatus({ type: 'error', message: 'Please enter your full name.' });
      setIsSubmitting(false);
      return;
    }

    // checks password strength (must include a capital letter + special character)
    if (!/[A-Z]/.test(formData.password) || !/[^A-Za-z0-9]/.test(formData.password)) {
      setStatus({
        type: 'error',
        message: 'Password must include an uppercase letter and special character.',
      });
      setIsSubmitting(false);
      return;
    }

    // makes sure the two password fields match
    if (formData.password !== formData.confirmPassword) {
      setStatus({ type: 'error', message: 'Passwords do not match.' });
      setIsSubmitting(false);
      return;
    }

    // removes confirmPassword before sending to backend
    const { confirmPassword, ...payload } = formData;

    try {
      // send the data to backend API
      const body = await apiFetch('/register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });

      if (body.user_id && payload.email) {
        localStorage.setItem('user_id', body.user_id);
        localStorage.setItem('email', payload.email);
        window.location.href = '/upload';
        return;
      }

      setStatus({ type: 'success', message: 'Account created successfully.' });
      setFormData({ name: '', email: '', password: '', confirmPassword: '' });
    } catch (error) {
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
              <button type="button" className="inline-link" onClick={goToLogin}>
                Go to login
              </button>
            </>
          ),
        });
        return;
      }

      // catch any network or unexpected error
      setStatus({ type: 'error', message: error.message });
    } finally {
      // stop loading state after process finishes
      setIsSubmitting(false);
    }
  };

  return (
    <div className="register-page">
      {/* the main registration form card */}
      <form className="register-card" onSubmit={handleSubmit}>
        <h1>Create an account</h1>

        {/* full name input */}
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

        {/* email input */}
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

        {/* password input */}
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

        {/* confirm password input */}
        <label>
          Confirm password
          <input
            type="password"
            name="confirmPassword"
            value={formData.confirmPassword}
            onChange={handleChange}
            placeholder="Repeat your password"
            required
            minLength={6}
          />
        </label>

        {/* submit button */}
        <button type="submit" disabled={isSubmitting}>
          {isSubmitting ? 'Creating account...' : 'Sign up'}
        </button>

        {/* feedback messages for user */}
        {status.type && (
          <p className={`status ${status.type}`}>{status.message}</p>
        )}
      </form>
    </div>
  );
}

export default Register;
