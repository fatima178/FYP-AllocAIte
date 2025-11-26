import { useEffect } from 'react';
import './App.css';

import LoginPage from './Pages/Login';
import UploadPage from './Pages/Upload';
import DashboardPage from './Pages/Dashboard';
import TasksPage from './Pages/Tasks';
import AssignmentsPage from './Pages/Assignments';
import ChatbotPage from './Pages/Chatbot';
import RecommendationsPage from './Pages/Recommendations';
import SettingsPage from "./Pages/Settings";
import ChatbotPopup from "./Pages/ChatbotPopup";

function App() {
  useEffect(() => {
    const resolveFontSizeValue = (size) =>
      size === 'small' ? '14px' : size === 'large' ? '18px' : '16px';
    const userId = localStorage.getItem('user_id');
    if (!userId) {
      document.body.classList.remove('dark-theme');
      document.documentElement.style.fontSize = resolveFontSizeValue('medium');
      return;
    }
    const storedTheme = localStorage.getItem(`theme_${userId}`) || 'light';
    document.body.classList.toggle('dark-theme', storedTheme === 'dark');

    const storedFontSize = localStorage.getItem(`fontSize_${userId}`) || 'medium';
    document.documentElement.style.fontSize = resolveFontSizeValue(storedFontSize);
  }, []);

  const path = window.location.pathname || '/';
  const hasUser = Boolean(localStorage.getItem('user_id'));

  if (!hasUser) {
    return <LoginPage />;
  }

  if (path === '/') {
    window.location.replace('/upload');
    return null;
  }

  const pages = {
    '/dashboard': <DashboardPage />,
    '/tasks': <TasksPage />,
    '/upload': <UploadPage />,
    '/assignments': <AssignmentsPage />,
    '/chatbot': <ChatbotPage />,
    '/recommendations': <RecommendationsPage />,
    '/settings': <SettingsPage />
  };

  return (
    <>
      {pages[path] || <UploadPage />}
      <ChatbotPopup /> 
    </>
  );
}

export default App;
