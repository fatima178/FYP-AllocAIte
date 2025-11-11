import './App.css';
import LoginPage from './Pages/Login';
import UploadPage from './Pages/Upload';
import DashboardPage from './Pages/Dashboard';
import TasksPage from './Pages/Tasks';
import AssignmentsPage from './Pages/Assignments';
import ChatbotPage from './Pages/Chatbot';

function App() {
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
  };

  return pages[path] || <UploadPage />;
}

export default App;
