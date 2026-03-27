const SESSION_KEYS = [
  "user_id",
  "account_type",
  "employee_id",
  "email",
  "name",
  "member_since",
  "active_upload_id",
  "login_role",
];

export const getSessionItem = (key) => sessionStorage.getItem(key);

export const setSessionItem = (key, value) => {
  if (value === undefined || value === null) {
    sessionStorage.removeItem(key);
    return;
  }
  sessionStorage.setItem(key, String(value));
};

export const removeSessionItem = (key) => {
  sessionStorage.removeItem(key);
};

export const clearSession = () => {
  SESSION_KEYS.forEach((key) => sessionStorage.removeItem(key));
};
