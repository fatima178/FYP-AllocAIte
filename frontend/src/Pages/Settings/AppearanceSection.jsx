export default function AppearanceSection({ theme, fontSize, onThemeChange, onFontSizeChange }) {
  return (
    <div className="settings-card">
      <h2>Appearance</h2>

      <p><strong>Theme</strong></p>
      <div className="button-row">
        <button
          className={theme === "light" ? "primary" : ""}
          onClick={() => onThemeChange("light")}
        >
          Light
        </button>
        <button
          className={theme === "dark" ? "primary" : ""}
          onClick={() => onThemeChange("dark")}
        >
          Dark
        </button>
      </div>

      <p><strong>Font Size</strong></p>
      <div className="button-row">
        <button
          className={fontSize === "small" ? "primary" : ""}
          onClick={() => onFontSizeChange("small")}
        >
          Small
        </button>
        <button
          className={fontSize === "medium" ? "primary" : ""}
          onClick={() => onFontSizeChange("medium")}
        >
          Medium
        </button>
        <button
          className={fontSize === "large" ? "primary" : ""}
          onClick={() => onFontSizeChange("large")}
        >
          Large
        </button>
      </div>
    </div>
  );
}
