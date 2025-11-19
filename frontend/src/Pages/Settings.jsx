import React, { useState, useEffect } from "react";
import Menu from "./Menu";
import "../styles/Settings.css";

function SettingsPage() {
  const name = localStorage.getItem("name") || "Unknown User";
  const email = localStorage.getItem("email") || "unknown";
  const memberSince = localStorage.getItem("member_since") || "-";

  const formatMemberSince = (value) => {
    if (!value || value === "-") return "-";
    const parsed = new Date(value);
    if (Number.isNaN(parsed.getTime())) {
      return value;
    }
    return parsed.toLocaleDateString(undefined, {
      year: "numeric",
      month: "long",
      day: "numeric",
    });
  };

  // Theme + Font state
  const [theme, setTheme] = useState(localStorage.getItem("theme") || "light");
  const [fontSize, setFontSize] = useState(localStorage.getItem("fontSize") || "medium");

  // Apply theme & font size on load
  useEffect(() => {
    document.body.classList.toggle("dark-theme", theme === "dark");
    document.documentElement.style.fontSize =
      fontSize === "small" ? "14px" : fontSize === "large" ? "18px" : "16px";
  }, [theme, fontSize]);

  // Theme change handler
  const changeTheme = (value) => {
    setTheme(value);
    localStorage.setItem("theme", value);
  };

  // Font size change handler
  const changeFontSize = (value) => {
    setFontSize(value);
    localStorage.setItem("fontSize", value);
    document.documentElement.style.fontSize =
      value === "small" ? "14px" : value === "large" ? "18px" : "16px";
  };

  return (
    <div className="settings-page">
      <Menu />

      <div className="settings-content">
        <h1>Settings</h1>
        <p className="subtitle">Manage your account and preferences</p>

        {/* ACCOUNT DETAILS */}
        <div className="settings-card">
          <h2>Account Details</h2>

          <p><strong>Name:</strong> {name}</p>
          <p><strong>Email:</strong> {email}</p>
          <p><strong>Member Since:</strong> {formatMemberSince(memberSince)}</p>

          <div className="button-row">
            <button>Edit Details</button>
            <button>Change Password</button>
          </div>
        </div>

        {/* APPEARANCE */}
        <div className="settings-card">
          <h2>Appearance</h2>

          <p><strong>Theme</strong></p>
          <div className="button-row">
            <button
              className={theme === "light" ? "primary" : ""}
              onClick={() => changeTheme("light")}
            >
              Light
            </button>
            <button
              className={theme === "dark" ? "primary" : ""}
              onClick={() => changeTheme("dark")}
            >
              Dark
            </button>
          </div>

          <p><strong>Font Size</strong></p>
          <div className="button-row">
            <button
              className={fontSize === "small" ? "primary" : ""}
              onClick={() => changeFontSize("small")}
            >
              Small
            </button>
            <button
              className={fontSize === "medium" ? "primary" : ""}
              onClick={() => changeFontSize("medium")}
            >
              Medium
            </button>
            <button
              className={fontSize === "large" ? "primary" : ""}
              onClick={() => changeFontSize("large")}
            >
              Large
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

export default SettingsPage;
