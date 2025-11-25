import React, { useState, useEffect } from "react";
import Menu from "./Menu";
import "../styles/Settings.css";
import { apiFetch } from "../api";

function SettingsPage() {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [status, setStatus] = useState("");
  const [account, setAccount] = useState({
    name: localStorage.getItem("name") || "Unknown User",
    email: localStorage.getItem("email") || "unknown",
    member_since: localStorage.getItem("member_since") || "-",
  });

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

  useEffect(() => {
    const userId = localStorage.getItem("user_id");
    if (!userId) {
      setError("Please log in to view settings.");
      setLoading(false);
      return;
    }

    const fetchSettings = async () => {
      try {
        const data = await apiFetch(`/settings?user_id=${userId}`);
        setAccount({
          name: data.name,
          email: data.email,
          member_since: data.member_since,
        });
        if (data.theme) {
          setTheme(data.theme);
          localStorage.setItem("theme", data.theme);
        }
        if (data.font_size) {
          setFontSize(data.font_size);
          localStorage.setItem("fontSize", data.font_size);
        }
      } catch (err) {
        setError(err.message || "Unable to load settings.");
      } finally {
        setLoading(false);
      }
    };

    fetchSettings();
  }, []);

  // Apply theme & font size on load
  useEffect(() => {
    document.body.classList.toggle("dark-theme", theme === "dark");
    document.documentElement.style.fontSize =
      fontSize === "small" ? "14px" : fontSize === "large" ? "18px" : "16px";
  }, [theme, fontSize]);

  // Theme change handler
  const updateSettings = async (payload) => {
    const userId = localStorage.getItem("user_id");
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
    localStorage.setItem("theme", value);
    updateSettings({ theme: value });
  };

  // Font size change handler
  const changeFontSize = (value) => {
    setFontSize(value);
    localStorage.setItem("fontSize", value);
    document.documentElement.style.fontSize =
      value === "small" ? "14px" : value === "large" ? "18px" : "16px";
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

        {/* ACCOUNT DETAILS */}
        <div className="settings-card">
          <h2>Account Details</h2>

          <p><strong>Name:</strong> {account.name}</p>
          <p><strong>Email:</strong> {account.email}</p>
          <p><strong>Member Since:</strong> {formatMemberSince(account.member_since)}</p>

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
