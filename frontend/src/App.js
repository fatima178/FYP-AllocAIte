import './App.css';
import LoginPage from './Pages/Login';
import UploadPage from './Pages/Upload';

function App() {
  const path = window.location.pathname;
  const hasUser = Boolean(localStorage.getItem('user_id'));

  if (path === '/upload') {
    return hasUser ? <UploadPage /> : <LoginPage />;
  }

  return <LoginPage />;
}

export default App;
