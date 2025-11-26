import React, { useState, useEffect } from "react";
import Menu from "./Menu";
import "../styles/Settings.css";
import { apiFetch } from "../api";

const DEFAULT_THEME = "light";
const DEFAULT_FONT_SIZE = "medium";

const applyThemeClass = (value) => {
  document.body.classList.toggle("dark-theme", value === "dark");
};

const applyFontSize = (value) => {
  document.documentElement.style.fontSize =
    value === "small" ? "14px" : value === "large" ? "18px" : "16px";
};

const getPreferenceKey = (base) => {
  const userId = localStorage.getItem("user_id");
  return userId ? `${base}_${userId}` : null;
};

const readPreference = (base, fallback) => {
  const key = getPreferenceKey(base);
  if (!key) return fallback;
  return localStorage.getItem(key) || fallback;
};

const writePreference = (base, value) => {
  const key = getPreferenceKey(base);
  if (!key) return;
  localStorage.setItem(key, value);
};

function SettingsPage() {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [status, setStatus] = useState("");
  const [account, setAccount] = useState({
    name: localStorage.getItem("name") || "Unknown User",
    email: localStorage.getItem("email") || "unknown",
    member_since: localStorage.getItem("member_since") || "-",
  });
  const [isEditModalOpen, setEditModalOpen] = useState(false);
  const [isPasswordModalOpen, setPasswordModalOpen] = useState(false);
  const [detailsStatus, setDetailsStatus] = useState(null);
  const [passwordStatus, setPasswordStatus] = useState(null);
  const [verifyStatus, setVerifyStatus] = useState(null);
  const [passwordVerified, setPasswordVerified] = useState(false);
  const [detailsForm, setDetailsForm] = useState({
    name: account.name || "",
    email: account.email || "",
  });
  const [passwordForm, setPasswordForm] = useState({
    current: "",
    next: "",
    confirm: "",
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
  const [theme, setTheme] = useState(() => readPreference("theme", DEFAULT_THEME));
  const [fontSize, setFontSize] = useState(() => readPreference("fontSize", DEFAULT_FONT_SIZE));

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

  // Apply theme & font size on load
  useEffect(() => {
    applyThemeClass(theme);
    applyFontSize(fontSize);
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
    applyThemeClass(value);
    setTheme(value);
    writePreference("theme", value);
    updateSettings({ theme: value });
  };

  // Font size change handler
  const changeFontSize = (value) => {
    setFontSize(value);
    writePreference("fontSize", value);
    applyFontSize(value);
    updateSettings({ font_size: value });
  };

  const handleDetailsChange = (event) => {
    const { name, value } = event.target;
    setDetailsForm((prev) => ({ ...prev, [name]: value }));
  };

  useEffect(() => {
    setDetailsForm({
      name: account.name || "",
      email: account.email || "",
    });
  }, [account]);

  const openEditModal = () => {
    setDetailsStatus(null);
    setDetailsForm({
      name: account.name || "",
      email: account.email || "",
    });
    setEditModalOpen(true);
  };

  const closeEditModal = () => {
    setEditModalOpen(false);
    setDetailsStatus(null);
  };

  const openPasswordModal = () => {
    setPasswordStatus(null);
    setVerifyStatus(null);
    setPasswordVerified(false);
    setPasswordForm({ current: "", next: "", confirm: "" });
    setPasswordModalOpen(true);
  };

  const closePasswordModal = () => {
    setPasswordModalOpen(false);
    setPasswordStatus(null);
    setVerifyStatus(null);
    setPasswordVerified(false);
    setPasswordForm({ current: "", next: "", confirm: "" });
  };

  const submitDetails = async (event) => {
    event.preventDefault();
    setDetailsStatus(null);
    const userId = localStorage.getItem("user_id");

    if (!userId) {
      setDetailsStatus({ type: "error", message: "Please log in again." });
      return;
    }

    if (!detailsForm.name.trim() && !detailsForm.email.trim()) {
      setDetailsStatus({ type: "error", message: "Provide a new name or email." });
      return;
    }

    try {
      const payload = {
        user_id: Number(userId),
        name: detailsForm.name.trim() || undefined,
        email: detailsForm.email.trim() || undefined,
      };
      const data = await apiFetch("/settings/details", {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      setAccount({
        name: data.name,
        email: data.email,
        member_since: data.member_since,
      });
      localStorage.setItem("name", data.name);
      localStorage.setItem("email", data.email);
      if (data.member_since) {
        localStorage.setItem("member_since", data.member_since);
      }
      setDetailsStatus({ type: "success", message: data.message || "Account updated." });
    } catch (err) {
      setDetailsStatus({ type: "error", message: err.message || "Unable to update details." });
    }
  };

  const handlePasswordChange = (event) => {
    const { name, value } = event.target;
    setPasswordForm((prev) => ({ ...prev, [name]: value }));
  };

  const verifyCurrentPassword = async (event) => {
    event.preventDefault();
    setVerifyStatus(null);
    const userId = localStorage.getItem("user_id");
    if (!userId) {
      setVerifyStatus({ type: "error", message: "Please log in again." });
      return;
    }

    if (!passwordForm.current) {
      setVerifyStatus({ type: "error", message: "Enter your current password." });
      return;
    }

    try {
      const payload = {
        user_id: Number(userId),
        current_password: passwordForm.current,
      };
      const data = await apiFetch("/settings/password/verify", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      setPasswordVerified(true);
      setVerifyStatus({
        type: "success",
        message: data.message || "Password verified. Enter your new password.",
      });
    } catch (err) {
      setPasswordVerified(false);
      setVerifyStatus({ type: "error", message: err.message || "Unable to verify password." });
    }
  };

  const submitPassword = async (event) => {
    event.preventDefault();
    setPasswordStatus(null);
    const userId = localStorage.getItem("user_id");
    if (!userId) {
      setPasswordStatus({ type: "error", message: "Please log in again." });
      return;
    }

    if (!passwordForm.current || !passwordForm.next) {
      setPasswordStatus({ type: "error", message: "Fill in all password fields." });
      return;
    }

    if (passwordForm.next !== passwordForm.confirm) {
      setPasswordStatus({ type: "error", message: "New passwords do not match." });
      return;
    }

    if (!passwordVerified) {
      setPasswordStatus({ type: "error", message: "Verify your current password first." });
      return;
    }

    try {
      const payload = {
        user_id: Number(userId),
        current_password: passwordForm.current,
        new_password: passwordForm.next,
      };
      const data = await apiFetch("/settings/password", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      setPasswordStatus({ type: "success", message: data.message || "Password updated." });
      setPasswordForm({ current: "", next: "", confirm: "" });
    } catch (err) {
      setPasswordStatus({ type: "error", message: err.message || "Unable to update password." });
    }
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
            <button onClick={openEditModal}>Edit Details</button>
            <button onClick={openPasswordModal}>Change Password</button>
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

      {isEditModalOpen && (
        <div className="modal-backdrop" onClick={closeEditModal}>
          <div className="modal-card" onClick={(event) => event.stopPropagation()}>
            <div className="modal-header">
              <h3>Edit Account Details</h3>
              <button className="modal-close" type="button" onClick={closeEditModal} aria-label="Close edit details">
                ×
              </button>
            </div>
            <form className="settings-form" onSubmit={submitDetails}>
              <div className="form-grid">
                <label>
                  Name
                  <input
                    type="text"
                    name="name"
                    value={detailsForm.name}
                    onChange={handleDetailsChange}
                    placeholder="Your name"
                  />
                </label>
                <label>
                  Email
                  <input
                    type="email"
                    name="email"
                    value={detailsForm.email}
                    onChange={handleDetailsChange}
                    placeholder="you@email.com"
                  />
                </label>
              </div>
              <div className="modal-actions">
                <button type="submit" className="primary">Save Changes</button>
                <button type="button" className="cancel-button" onClick={closeEditModal}>Cancel</button>
              </div>
              {detailsStatus && (
                <p className={`status-message ${detailsStatus.type}`}>
                  {detailsStatus.message}
                </p>
              )}
            </form>
          </div>
        </div>
      )}

      {isPasswordModalOpen && (
        <div className="modal-backdrop" onClick={closePasswordModal}>
          <div className="modal-card" onClick={(event) => event.stopPropagation()}>
            <div className="modal-header">
              <h3>Change Password</h3>
              <button className="modal-close" type="button" onClick={closePasswordModal} aria-label="Close password modal">
                ×
              </button>
            </div>

            {!passwordVerified && (
              <form className="settings-form" onSubmit={verifyCurrentPassword}>
                <label>
                  Enter Current Password
                  <input
                    type="password"
                    name="current"
                    value={passwordForm.current}
                    onChange={handlePasswordChange}
                    placeholder="Current password"
                  />
                </label>
                <div className="modal-actions">
                  <button type="submit" className="primary">Verify Password</button>
                  <button type="button" className="cancel-button" onClick={closePasswordModal}>Cancel</button>
                </div>
                {verifyStatus && (
                  <p className={`status-message ${verifyStatus.type}`}>
                    {verifyStatus.message}
                  </p>
                )}
              </form>
            )}

            {passwordVerified && (
              <form className="settings-form" onSubmit={submitPassword}>
                {verifyStatus && (
                  <p className={`status-message ${verifyStatus.type}`}>
                    {verifyStatus.message}
                  </p>
                )}
                <div className="form-grid">
                  <label>
                    New Password
                    <input
                      type="password"
                      name="next"
                      value={passwordForm.next}
                      onChange={handlePasswordChange}
                      placeholder="New password"
                    />
                  </label>
                  <label>
                    Confirm New Password
                    <input
                      type="password"
                      name="confirm"
                      value={passwordForm.confirm}
                      onChange={handlePasswordChange}
                      placeholder="Confirm new password"
                    />
                  </label>
                </div>
                <p className="muted">Password must include an uppercase letter and special character.</p>
                <div className="modal-actions">
                  <button type="submit" className="primary">Update Password</button>
                  <button type="button" onClick={closePasswordModal}>Close</button>
                </div>
                {passwordStatus && (
                  <p className={`status-message ${passwordStatus.type}`}>
                    {passwordStatus.message}
                  </p>
                )}
              </form>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

export default SettingsPage;
