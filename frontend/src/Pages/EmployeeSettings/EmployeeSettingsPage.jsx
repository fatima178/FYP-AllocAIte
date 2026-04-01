import React, { useEffect, useState } from "react";
import Menu from "../Menu";
import "../../styles/Settings.css";
import { apiFetch } from "../../api";
import { formatMemberSince } from "../../lib/formatters";
import { getSessionItem } from "../../session";
import {
  DEFAULT_FONT_SIZE,
  DEFAULT_THEME,
  applyFontSize,
  applyThemeClass,
  readPreference,
  writePreference,
} from "../../lib/preferences";

function EmployeeSettingsPage() {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [status, setStatus] = useState("");
  const [account, setAccount] = useState({
    name: getSessionItem("name") || "Unknown User",
    email: getSessionItem("email") || "unknown",
    member_since: getSessionItem("member_since") || "-",
    manager_name: "-",
    manager_email: "-",
  });

  const [theme, setTheme] = useState(() => readPreference("theme", DEFAULT_THEME));
  const [fontSize, setFontSize] = useState(() =>
    readPreference("fontSize", DEFAULT_FONT_SIZE)
  );

  useEffect(() => {
    const userId = getSessionItem("user_id");
    if (!userId) {
      setError("Please log in to view settings.");
      setLoading(false);
      return;
    }

    const fetchSettings = async () => {
      try {
        const data = await apiFetch(`/employee/settings?user_id=${userId}`);
        setAccount({
          name: data.name,
          email: data.email,
          member_since: data.member_since,
          manager_name: data.manager_name || "-",
          manager_email: data.manager_email || "-",
        });

        if (data.theme) {
          setTheme(data.theme);
          writePreference("theme", data.theme);
        }
        if (data.font_size) {
          setFontSize(data.font_size);
          writePreference("fontSize", data.font_size);
        }
      } catch (err) {
        setError(err.message || "Unable to load settings.");
      } finally {
        setLoading(false);
      }
    };

    fetchSettings();
  }, []);

  useEffect(() => {
    applyThemeClass(theme);
    applyFontSize(fontSize);
  }, [theme, fontSize]);

  const updateSettings = async (payload) => {
    const userId = getSessionItem("user_id");
    if (!userId) return;

    try {
      await apiFetch("/settings", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ user_id: Number(userId), ...payload }),
      });
      setStatus("Settings updated");
      setTimeout(() => setStatus(""), 2000);
    } catch (err) {
      setStatus(err.message || "Unable to save settings.");
      setTimeout(() => setStatus(""), 2000);
    }
  };

  const changeTheme = (value) => {
    setTheme(value);
    applyThemeClass(value);
    writePreference("theme", value);
    updateSettings({ theme: value });
  };

  const changeFontSize = (value) => {
    setFontSize(value);
    applyFontSize(value);
    writePreference("fontSize", value);
    updateSettings({ font_size: value });
  };

  return (
    <div className="settings-page">
      <Menu />

      <div className="settings-content">
        <h1>Settings</h1>
        <p className="subtitle">Manage your account and preferences</p>
        {loading && <p>Loading settings...</p>}
        {error && <p className="error">{error}</p>}
        {status && <p className="status-message info">{status}</p>}

        <div className="settings-card">
          <h2>Account Details</h2>
          <p><strong>Name:</strong> {account.name}</p>
          <p><strong>Email:</strong> {account.email}</p>
          <p><strong>Member Since:</strong> {formatMemberSince(account.member_since)}</p>
          <p><strong>Manager:</strong> {account.manager_name}</p>
          <p><strong>Manager Email:</strong> {account.manager_email}</p>
        </div>

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

export default EmployeeSettingsPage;
