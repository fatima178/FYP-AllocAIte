import '../styles/Menu.css';

function Menu() {
  const currentPath = window.location.pathname;

  const links = [
    { label: 'Dashboard', path: '/dashboard' },
    { label: 'Tasks', path: '/tasks' },
    { label: 'Upload', path: '/upload' },
    { label: 'Assignments', path: '/assignments' },
    { label: 'Chatbot', path: '/chatbot' },
  ];

  const goTo = (path) => {
    if (currentPath === path) {
      return;
    }
    window.location.href = path;
  };

  const handleLogout = () => {
    localStorage.removeItem('user_id');
    localStorage.removeItem('email');
    window.location.href = '/';
  };

  return (
    <header className="menu-bar">
      <button type="button" className="brand" onClick={() => goTo('/dashboard')}>
        AllocAIte
      </button>

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

      <button type="button" className="logout-button" onClick={handleLogout}>
        Logout
      </button>
    </header>
  );
}

export default Menu;
