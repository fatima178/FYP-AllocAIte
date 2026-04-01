import '../styles/Menu.css';
import { getCurrentPath, navigateTo } from '../lib/navigation';
import { clearSession, getSessionItem } from '../session';

function Menu() {
  // track the current URL so we can highlight the active page
  const currentPath = getCurrentPath();
  const accountType = getSessionItem('account_type') || 'manager';

  // list of navigation links shown in the menu bar
  const links = accountType === 'employee'
    ? [
        { label: 'Home', path: '/employee' },
        { label: 'My Calendar', path: '/employee-calendar' },
        { label: 'Settings', path: '/employee-settings' },
      ]
    : [
        { label: 'Dashboard', path: '/dashboard' },
        { label: 'Tasks', path: '/tasks' },
        { label: 'Upload', path: '/upload' },
        { label: 'Assignments', path: '/assignments' },
        { label: 'Chatbot', path: '/chatbot' },
        { label: 'Settings', path: '/settings' }
      ];

  // helper for navigation without refreshing the component
  // but still using a full redirect
  const goTo = (path) => {
    // prevents unnecessary redirect if user is already on the page
    if (currentPath === path) return;
    navigateTo(path);
  };

  // logout removes user session and returns to home page
  const handleLogout = () => {
    clearSession();
    navigateTo('/');
  };

  return (
    <header className="menu-bar">
      {/* logo / brand button that leads to dashboard */}
      <button
        type="button"
        className="brand"
        onClick={() => goTo(accountType === 'employee' ? '/employee' : '/dashboard')}
      >
        AllocAIte
      </button>

      {/* main navigation links */}
      <nav className="menu-links">
        {links.map((link) => (
          <button
            type="button"
            key={link.path}
            className={`menu-link ${currentPath === link.path ? 'active' : ''}`}
            onClick={() => goTo(link.path)}
          >
            {link.label}
          </button>
        ))}
      </nav>

      {/* logout button on the right side */}
      <button
        type="button"
        className="logout-button"
        onClick={handleLogout}
      >
        Logout
      </button>
    </header>
  );
}

export default Menu;
