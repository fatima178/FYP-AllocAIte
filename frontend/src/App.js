import { useEffect } from 'react';

// individual route components
import LoginPage from './Pages/Login';
import UploadPage from './Pages/Upload';
import DashboardPage from './Pages/Dashboard';
import TasksPage from './Pages/Tasks';
import AssignmentsPage from './Pages/Assignments';
import ChatbotPage from './Pages/Chatbot';
import RecommendationsPage from './Pages/Recommendations';
import SettingsPage from "./Pages/Settings";
import ChatbotPopup from "./Pages/Chatbot/ChatbotPopup";
import EmployeePortalPage from './Pages/EmployeePortal';
import EmployeeCalendarPage from './Pages/EmployeeCalendar';
import EmployeeSettingsPage from './Pages/EmployeeSettings';
import InvitePage from './Pages/Invite';
import { getSessionItem } from './session';
import { applyInitialPreferences } from './lib/preferences';

function App() {
  useEffect(() => {
    applyInitialPreferences();
  }, []);

  // determine current URL path
  const path = window.location.pathname || '/';

  if (path === '/invite') {
    return <InvitePage />;
  }

  // detect whether user is logged in
  const hasUser = Boolean(getSessionItem('user_id'));
  const accountType = getSessionItem('account_type') || 'manager';

  // if user is not authenticated, always send them to login
  if (!hasUser) {
    return <LoginPage />;
  }

  // employee accounts only see their own portal
  if (accountType === 'employee') {
    if (path === '/employee-calendar') {
      return <EmployeeCalendarPage />;
    }
    if (path === '/employee-settings') {
      return <EmployeeSettingsPage />;
    }
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
