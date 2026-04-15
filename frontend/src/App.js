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
    // apply saved theme/font choices as soon as the app loads
    applyInitialPreferences();
  }, []);

  // current path decides which page component to show
  const path = window.location.pathname || '/';

  // invite links must work before the employee has logged in
  if (path === '/invite') {
    return <InvitePage />;
  }

  // detect whether user is logged in
  const hasUser = Boolean(getSessionItem('user_id'));
  const accountType = getSessionItem('account_type') || 'manager';

  // if no user id is stored, keep the user on the login/register screen
  if (!hasUser) {
    return <LoginPage />;
  }

  // employee accounts are restricted to employee-only pages
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

  // managers start from upload because the rest of the app depends on data
  if (path === '/') {
    window.location.replace('/upload');
    return null;
  }

  // simple routing without a router library
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

      {/* floating assistant stays available across manager pages */}
      <ChatbotPopup /> 
    </>
  );
}

export default App;
