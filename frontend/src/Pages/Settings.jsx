import React, { useState, useEffect } from "react";
import Menu from "./Menu";
import "../styles/Settings.css";
import { apiFetch } from "../api";

// default values for UI appearance
const DEFAULT_THEME = "light";
const DEFAULT_FONT_SIZE = "medium";

// toggles a CSS class on <body> to switch between light/dark mode
const applyThemeClass = (value) => {
  document.body.classList.toggle("dark-theme", value === "dark");
};

// adjusts the base font size for the entire UI
const applyFontSize = (value) => {
  document.documentElement.style.fontSize =
    value === "small" ? "16px" : value === "large" ? "20px" : "18px";
};

// attaches user_id to localStorage keys so preferences are per-user
const getPreferenceKey = (base) => {
  const userId = localStorage.getItem("user_id");
  return userId ? `${base}_${userId}` : null;
};

// retrieves saved theme/font preferences
const readPreference = (base, fallback) => {
  const key = getPreferenceKey(base);
  if (!key) return fallback;
  return localStorage.getItem(key) || fallback;
};

// stores updated preferences
const writePreference = (base, value) => {
  const key = getPreferenceKey(base);
  if (!key) return;
  localStorage.setItem(key, value);
};

function SettingsPage() {
  // loading state while waiting for backend response
  const [loading, setLoading] = useState(true);

  // error messages for top-level fetch failures
  const [error, setError] = useState("");

  // temporary status text (e.g. “Settings updated”)
  const [status, setStatus] = useState("");

  // stores the user's account details from backend
  const [account, setAccount] = useState({
    name: localStorage.getItem("name") || "Unknown User",
    email: localStorage.getItem("email") || "unknown",
    member_since: localStorage.getItem("member_since") || "-",
  });

  // modal open/close states
  const [isEditModalOpen, setEditModalOpen] = useState(false);
  const [isPasswordModalOpen, setPasswordModalOpen] = useState(false);

  // form + validation states for edit modal
  const [detailsStatus, setDetailsStatus] = useState(null);
  const [detailsForm, setDetailsForm] = useState({
    name: account.name || "",
    email: account.email || "",
  });

  // states for password change modal
  const [passwordStatus, setPasswordStatus] = useState(null);
  const [verifyStatus, setVerifyStatus] = useState(null);
  const [passwordVerified, setPasswordVerified] = useState(false);
  const [passwordForm, setPasswordForm] = useState({
    current: "",
    next: "",
    confirm: "",
  });

  // employee creation form
  const [employeeForm, setEmployeeForm] = useState({
    name: "",
    role: "",
    department: "",
  });
  const [employeeSkills, setEmployeeSkills] = useState([
    { skill_name: "", years_experience: "" },
  ]);
  const [skillError, setSkillError] = useState(null);
  const [employeeStatus, setEmployeeStatus] = useState(null);
  const [employeeSaving, setEmployeeSaving] = useState(false);

  // display formatting for "member since"
  const formatMemberSince = (value) => {
    if (!value || value === "-") return "-";
    const parsed = new Date(value);
    if (Number.isNaN(parsed.getTime())) return value;
    return parsed.toLocaleDateString(undefined, {
      year: "numeric",
      month: "long",
      day: "numeric",
    });
  };

  // theme + font size states loaded from local storage
  const [theme, setTheme] = useState(() => readPreference("theme", DEFAULT_THEME));
  const [fontSize, setFontSize] = useState(() =>
    readPreference("fontSize", DEFAULT_FONT_SIZE)
  );

  // fetch account + appearance settings when page loads
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

        // update account info from backend
        setAccount({
          name: data.name,
          email: data.email,
          member_since: data.member_since,
        });

        // sync theme + size with DB (if saved)
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

  // apply theme + font size whenever they change
  useEffect(() => {
    applyThemeClass(theme);
    applyFontSize(fontSize);
  }, [theme, fontSize]);

  // sends updated UI preferences to the backend
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

  // theme change handler
  const changeTheme = (value) => {
    setTheme(value);
    applyThemeClass(value);
    writePreference("theme", value);
    updateSettings({ theme: value });
  };

  // font size change handler
  const changeFontSize = (value) => {
    setFontSize(value);
    applyFontSize(value);
    writePreference("fontSize", value);
    updateSettings({ font_size: value });
  };

  // update edit details fields
  const handleDetailsChange = (event) => {
    const { name, value } = event.target;
    setDetailsForm((prev) => ({ ...prev, [name]: value }));
  };

  // sync edit form with account data when account updates
  useEffect(() => {
    setDetailsForm({
      name: account.name || "",
      email: account.email || "",
    });
  }, [account]);

  // open/close account details modal
  const openEditModal = () => {
    setDetailsStatus(null);
    setDetailsForm({ name: account.name, email: account.email });
    setEditModalOpen(true);
  };
  const closeEditModal = () => {
    setEditModalOpen(false);
    setDetailsStatus(null);
  };

  // open/close password modal
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

  // submit updated name/email to backend
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

      // update UI + localStorage with updated info
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
      setDetailsStatus({
        type: "error",
        message: err.message || "Unable to update details.",
      });
    }
  };

  // handle manual employee creation
  const handleEmployeeChange = (event) => {
    const { name, value } = event.target;
    setEmployeeForm((prev) => ({ ...prev, [name]: value }));
  };

  const submitEmployee = async (event) => {
    event.preventDefault();
    setEmployeeStatus(null);
    setSkillError(null);

    const userId = localStorage.getItem("user_id");
    if (!userId) {
      setEmployeeStatus({ type: "error", message: "Please log in again." });
      return;
    }

    setEmployeeSaving(true);
    try {
      const skillsPayload = employeeSkills
        .filter((skill) => String(skill.skill_name || "").trim() || String(skill.years_experience || "").trim())
        .map((skill) => ({
          skill_name: skill.skill_name,
          years_experience: skill.years_experience,
        }));

      await apiFetch("/employees", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          user_id: Number(userId),
          name: employeeForm.name,
          role: employeeForm.role,
          department: employeeForm.department,
          skills: skillsPayload,
        }),
      });

      setEmployeeStatus({ type: "success", message: "Employee added successfully." });
      setEmployeeForm({
        name: "",
        role: "",
        department: "",
      });
      setEmployeeSkills([{ skill_name: "", years_experience: "" }]);
    } catch (err) {
      setEmployeeStatus({ type: "error", message: err.message || "Unable to add employee." });
    } finally {
      setEmployeeSaving(false);
    }
  };


  // update password form fields
  const handlePasswordChange = (event) => {
    const { name, value } = event.target;
    setPasswordForm((prev) => ({ ...prev, [name]: value }));
  };

  // verify current password before allowing user to set a new one
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
      setVerifyStatus({
        type: "error",
        message: err.message || "Unable to verify password.",
      });
    }
  };

  // submit the new password to backend
  const submitPassword = async (event) => {
    event.preventDefault();
    setPasswordStatus(null);

    const userId = localStorage.getItem("user_id");
    if (!userId) {
      setPasswordStatus({ type: "error", message: "Please log in again." });
      return;
    }

    // ensure all fields are filled
    if (!passwordForm.current || !passwordForm.next) {
      setPasswordStatus({ type: "error", message: "Fill in all password fields." });
      return;
    }

    // check new passwords match
    if (passwordForm.next !== passwordForm.confirm) {
      setPasswordStatus({ type: "error", message: "New passwords do not match." });
      return;
    }

    if (!passwordVerified) {
      setPasswordStatus({
        type: "error",
        message: "Verify your current password first.",
      });
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

      setPasswordStatus({
        type: "success",
        message: data.message || "Password updated.",
      });

      setPasswordForm({ current: "", next: "", confirm: "" });
    } catch (err) {
      setPasswordStatus({
        type: "error",
        message: err.message || "Unable to update password.",
      });
    }
  };

  return (
    <div className="settings-page">
      {/* top navigation bar */}
      <Menu />

      <div className="settings-content">
        <h1>Settings</h1>
        <p className="subtitle">Manage your account and preferences</p>
        {loading && <p>Loading settings...</p>}
        {error && <p className="error">{error}</p>}
        {status && <p className="status-message info">{status}</p>}

        {/* ACCOUNT DETAILS SECTION */}
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

        {/* THEME & FONT SIZE SECTION */}
        <div className="settings-card">
          <h2>Appearance</h2>

          {/* theme controls */}
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

          {/* font size controls */}
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

        {/* EMPLOYEE MANAGEMENT SECTION */}
        <div className="settings-card">
          <h2>Add Employee</h2>
          <p className="muted">Create employees directly in the system without Excel.</p>

          <form className="settings-form" onSubmit={submitEmployee}>
            <div className="form-grid">
              <label>
                Name
                <input
                  type="text"
                  name="name"
                  value={employeeForm.name}
                  onChange={handleEmployeeChange}
                  placeholder="Alex Johnson"
                />
              </label>

              <label>
                Role
                <input
                  type="text"
                  name="role"
                  value={employeeForm.role}
                  onChange={handleEmployeeChange}
                  placeholder="Backend Developer"
                />
              </label>

              <label>
                Department
                <input
                  type="text"
                  name="department"
                  value={employeeForm.department}
                  onChange={handleEmployeeChange}
                  placeholder="Engineering"
                />
              </label>

              {employeeSkills.map((skill, index) => (
                <div key={index} className="form-grid">
                  <label>
                    Skill Name
                    <input
                      type="text"
                      value={skill.skill_name}
                      onChange={(e) => {
                        const updated = [...employeeSkills];
                        updated[index] = {
                          ...updated[index],
                          skill_name: e.target.value,
                        };
                        setEmployeeSkills(updated);
                      }}
                      placeholder="Python"
                    />
                  </label>

                  <label>
                    Skill Experience (Years)
                    <input
                      type="number"
                      value={skill.years_experience}
                      onChange={(e) => {
                        const updated = [...employeeSkills];
                        updated[index] = {
                          ...updated[index],
                          years_experience: e.target.value,
                        };
                        setEmployeeSkills(updated);
                      }}
                      placeholder="3"
                      min="0"
                      step="0.1"
                    />
                  </label>

                  {employeeSkills.length > 1 && (
                    <label>
                      &nbsp;
                      <button
                        type="button"
                        className="ghost-btn"
                        onClick={() => {
                          const updated = employeeSkills.filter((_, i) => i !== index);
                          setEmployeeSkills(updated);
                        }}
                      >
                        Remove
                      </button>
                    </label>
                  )}
                </div>
              ))}
            </div>

            <div className="button-row">
              <button
                type="button"
                onClick={() => {
                  setSkillError(null);
                  setEmployeeSkills((prev) => [
                    ...prev,
                    { skill_name: "", years_experience: "" },
                  ]);
                }}
              >
                Add Skill
              </button>
            </div>

            {skillError && <p className="form-error">{skillError}</p>}

            {employeeSkills.length > 0 && (
              <p className="muted">
                Skills: {employeeSkills.map((s) => `${s.skill_name} (${s.years_experience}y)`).join(", ")}
              </p>
            )}

            <div className="button-row">
              <button className="primary" type="submit" disabled={employeeSaving}>
                {employeeSaving ? "Saving..." : "Add Employee"}
              </button>
            </div>

            {employeeStatus && (
              <p className={`status-message ${employeeStatus.type || ""}`}>
                {employeeStatus.message}
              </p>
            )}
          </form>
        </div>

      </div>

      {/* EDIT DETAILS MODAL */}
      {isEditModalOpen && (
        <div className="modal-backdrop" onClick={closeEditModal}>
          <div className="modal-card" onClick={(event) => event.stopPropagation()}>
            <div className="modal-header">
              <h3>Edit Account Details</h3>
              <button className="modal-close" type="button" onClick={closeEditModal}>
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
                <button type="button" className="cancel-button" onClick={closeEditModal}>
                  Cancel
                </button>
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

      {/* PASSWORD CHANGE MODAL */}
      {isPasswordModalOpen && (
        <div className="modal-backdrop" onClick={closePasswordModal}>
          <div className="modal-card" onClick={(event) => event.stopPropagation()}>
            <div className="modal-header">
              <h3>Change Password</h3>
              <button className="modal-close" type="button" onClick={closePasswordModal}>
                ×
              </button>
            </div>

            {/* STEP 1: verify current password */}
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
                  <button type="button" className="cancel-button" onClick={closePasswordModal}>
                    Cancel
                  </button>
                </div>

                {verifyStatus && (
                  <p className={`status-message ${verifyStatus.type}`}>
                    {verifyStatus.message}
                  </p>
                )}
              </form>
            )}

            {/* STEP 2: allow new password entry after verification */}
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

                <p className="muted">
                  Password must include an uppercase letter and special character.
                </p>

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
