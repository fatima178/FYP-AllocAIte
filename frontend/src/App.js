import { useEffect } from 'react';
import './App.css';

// individual route components
import LoginPage from './Pages/Login';
import UploadPage from './Pages/Upload';
import DashboardPage from './Pages/Dashboard';
import TasksPage from './Pages/Tasks';
import AssignmentsPage from './Pages/Assignments';
import ChatbotPage from './Pages/Chatbot';
import RecommendationsPage from './Pages/Recommendations';
import SettingsPage from "./Pages/Settings";
import ChatbotPopup from "./Pages/ChatbotPopup";
import EmployeePortalPage from './Pages/EmployeePortal';
import InvitePage from './Pages/Invite';

function App() {
  // apply user theme + font preferences on initial load
  useEffect(() => {
    // converts logical font sizes to actual CSS pixel values
    const resolveFontSizeValue = (size) =>
      size === 'small' ? '16px' : size === 'large' ? '20px' : '18px';

    const userId = localStorage.getItem('user_id');

    // if no user logged in, reset display preferences
    if (!userId) {
      document.body.classList.remove('dark-theme');
      document.documentElement.style.fontSize = resolveFontSizeValue('medium');
      return;
    }

    // apply saved theme (light/dark)
    const storedTheme = localStorage.getItem(`theme_${userId}`) || 'light';
    document.body.classList.toggle('dark-theme', storedTheme === 'dark');

    // apply saved font size
    const storedFontSize = localStorage.getItem(`fontSize_${userId}`) || 'medium';
    document.documentElement.style.fontSize = resolveFontSizeValue(storedFontSize);
  }, []);

  // determine current URL path
  const path = window.location.pathname || '/';

  if (path === '/invite') {
    return <InvitePage />;
  }

  // detect whether user is logged in
  const hasUser = Boolean(localStorage.getItem('user_id'));
  const accountType = localStorage.getItem('account_type') || 'manager';

  // if user is not authenticated, always send them to login
  if (!hasUser) {
    return <LoginPage />;
  }

  // employee accounts only see their own portal
  if (accountType === 'employee') {
    if (path !== '/employee') {
      window.location.replace('/employee');
      return null;
    }
    return <EmployeePortalPage />;
  }

  // root path redirects into the real app flow
  if (path === '/') {
    window.location.replace('/upload');
    return null;
  }

  // simple route map for static routing
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
      {/* render the selected page, fallback to UploadPage */}
      {pages[path] || <UploadPage />}

      {/* floating popup assistant available on all pages */}
      <ChatbotPopup /> 
    </>
  );
}

export default App;
