import { getSessionItem } from "../session";

export const DEFAULT_THEME = "light";
export const DEFAULT_FONT_SIZE = "medium";

export const resolveFontSizeValue = (size) =>
  size === "small" ? "16px" : size === "large" ? "20px" : "18px";

export const applyThemeClass = (value) => {
  document.body.classList.toggle("dark-theme", value === "dark");
};

export const applyFontSize = (value) => {
  document.documentElement.style.fontSize = resolveFontSizeValue(value);
};

export const getPreferenceKey = (base) => {
  const userId = getSessionItem("user_id");
  return userId ? `${base}_${userId}` : null;
};

export const readPreference = (base, fallback) => {
  const key = getPreferenceKey(base);
  if (!key) return fallback;
  return localStorage.getItem(key) || fallback;
};

export const writePreference = (base, value) => {
  const key = getPreferenceKey(base);
  if (!key) return;
  localStorage.setItem(key, value);
};

export const applyInitialPreferences = () => {
  if (typeof document === "undefined") {
    return;
  }

  const userId = getSessionItem("user_id");
  if (!userId) {
    document.body.classList.remove("dark-theme");
    applyFontSize(DEFAULT_FONT_SIZE);
    return;
  }

  const savedTheme = localStorage.getItem(`theme_${userId}`) || DEFAULT_THEME;
  const savedFontSize = localStorage.getItem(`fontSize_${userId}`) || DEFAULT_FONT_SIZE;

  applyThemeClass(savedTheme);
  applyFontSize(savedFontSize);
};
