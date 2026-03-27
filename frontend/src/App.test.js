import { render, screen } from '@testing-library/react';
import App from './App';

test('renders the login screen when no user is signed in', () => {
  render(<App />);
  expect(screen.getByRole('heading', { name: /allocaite/i })).toBeInTheDocument();
  expect(screen.getByRole('button', { name: /sign in/i })).toBeInTheDocument();
});
