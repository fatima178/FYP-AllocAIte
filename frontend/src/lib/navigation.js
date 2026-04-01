export const getCurrentPath = () => window.location.pathname || "/";

export const navigateTo = (path, options = {}) => {
  const { replace = false } = options;
  if (replace) {
    window.location.replace(path);
    return;
  }
  window.location.href = path;
};

export const redirectToLogin = () => {
  navigateTo("/", { replace: true });
};
