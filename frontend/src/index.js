import React from 'react';
import ReactDOM from 'react-dom/client';
import './index.css';
import App from './App';
import reportWebVitals from './reportWebVitals';

const resolveFontSizeValue = (size) =>
  size === 'small' ? '14px' : size === 'large' ? '18px' : '16px';

const applyInitialPreferences = () => {
  if (typeof document === 'undefined') {
    return;
  }
  const userId = localStorage.getItem('user_id');
  if (!userId) {
    document.body.classList.remove('dark-theme');
    document.documentElement.style.fontSize = resolveFontSizeValue('medium');
    return;
  }

  const savedTheme = localStorage.getItem(`theme_${userId}`) || 'light';
  document.body.classList.toggle('dark-theme', savedTheme === 'dark');

  const savedFontSize = localStorage.getItem(`fontSize_${userId}`) || 'medium';
  document.documentElement.style.fontSize = resolveFontSizeValue(savedFontSize);
};

applyInitialPreferences();

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);

// If you want to start measuring performance in your app, pass a function
// to log results (for example: reportWebVitals(console.log))
// or send to an analytics endpoint. Learn more: https://bit.ly/CRA-vitals
reportWebVitals();
