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
    const storedTheme = localStorage.getItem('theme') || 'light';
    document.body.classList.toggle('dark-theme', storedTheme === 'dark');

    const storedFontSize = localStorage.getItem('fontSize') || 'medium';
    document.documentElement.style.fontSize =
      storedFontSize === 'small' ? '14px' :
      storedFontSize === 'large' ? '18px' :
      '16px';
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
      <ChatbotPopup />   {/* Always visible on every page */}
    </>
  );
}

export default App;
