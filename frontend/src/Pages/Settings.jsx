import React, { useState, useEffect } from "react";
import Menu from "./Menu";
import "../styles/Settings.css";
import { apiFetch, API_BASE_URL } from "../api";

// default values for UI appearance
const DEFAULT_THEME = "light";
const DEFAULT_FONT_SIZE = "medium";
const FIXED_SEMANTIC_WEIGHT = 0.35;
const DEFAULT_MANAGER_WEIGHTS = {
  skills_fit: 0.25,
  experience_role: 0.23,
  availability_balance: 0.12,
  growth_potential: 0.05,
  past_feedback: 0.03,
};
const HISTORY_PAGE_SIZE = 5;
const GROUP_TO_DETAIL_SHARES = {
  skills_fit: {
    skill: 0.88,
    possible_skill: 0.02,
    soft_skill: 0.08,
    possible_soft_skill: 0.02,
  },
  experience_role: {
    experience: 0.652174,
    role: 0.347826,
  },
  availability_balance: {
    availability: 0.833333,
    fairness: 0.166667,
  },
  growth_potential: {
    preferences: 1.0,
  },
  past_feedback: {
    feedback: 1.0,
  },
};
const ADJUSTABLE_WEIGHT_BUDGET = 1 - FIXED_SEMANTIC_WEIGHT;

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
  const [exportStatus, setExportStatus] = useState("");
  const [exporting, setExporting] = useState(false);

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
    { skill_name: "", years_experience: "", skill_type: "technical" },
  ]);
  const [existingEmployeeId, setExistingEmployeeId] = useState("");
  const [existingEmployeeSkills, setExistingEmployeeSkills] = useState([
    { skill_name: "", years_experience: "", skill_type: "technical" },
  ]);
  const [skillError, setSkillError] = useState(null);
  const [employeeStatus, setEmployeeStatus] = useState(null);
  const [employeeSaving, setEmployeeSaving] = useState(false);
  const [existingSkillStatus, setExistingSkillStatus] = useState(null);
  const [existingSkillSaving, setExistingSkillSaving] = useState(false);

  // employee invite form
  const [employeeOptions, setEmployeeOptions] = useState([]);
  const [inviteForm, setInviteForm] = useState({
    employee_id: "",
    name: "",
  });
  const [inviteStatus, setInviteStatus] = useState(null);
  const [inviteLink, setInviteLink] = useState("");
  const [inviteSaving, setInviteSaving] = useState(false);
  const [activeSection, setActiveSection] = useState("account");
  const [historyItems, setHistoryItems] = useState([]);
  const [historyLoading, setHistoryLoading] = useState(false);
  const [historyError, setHistoryError] = useState("");
  const [historyPage, setHistoryPage] = useState(1);
  const [historyTotal, setHistoryTotal] = useState(0);

  const buildHistoryTitle = (item) => {
    const assignmentTitle = String(item?.assignment_title || "").trim();
    if (assignmentTitle) return assignmentTitle;
    return String(item?.task_description || "").trim();
  };

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
  const [weights, setWeights] = useState({
    ...DEFAULT_MANAGER_WEIGHTS,
  });
  const [savedWeightBaseline, setSavedWeightBaseline] = useState({
    ...DEFAULT_MANAGER_WEIGHTS,
  });

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
        if (data.weights) {
          const groupedWeights = {
            skills_fit:
              (data.weights.skill ?? 0) +
              (data.weights.possible_skill ?? 0) +
              (data.weights.soft_skill ?? 0) +
              (data.weights.possible_soft_skill ?? 0),
            experience_role:
              (data.weights.experience ?? 0) +
              (data.weights.role ?? 0),
            availability_balance:
              (data.weights.availability ?? 0) +
              (data.weights.fairness ?? 0),
            growth_potential: data.weights.preferences ?? DEFAULT_MANAGER_WEIGHTS.growth_potential,
            past_feedback: data.weights.feedback ?? DEFAULT_MANAGER_WEIGHTS.past_feedback,
          };
          setWeights(groupedWeights);
          setSavedWeightBaseline(groupedWeights);
        }
      } catch (err) {
        setError(err.message || "Unable to load settings.");
      } finally {
        setLoading(false);
      }
    };

    fetchSettings();
  }, []);

  const fetchEmployees = async () => {
    const userId = localStorage.getItem("user_id");
    if (!userId) return;
    try {
      const data = await apiFetch(`/employees?user_id=${userId}`);
      setEmployeeOptions(data.employees || []);
    } catch (err) {
      setEmployeeOptions([]);
    }
  };

  // fetch employee list for login creation
  useEffect(() => {
    fetchEmployees();
  }, []);

  useEffect(() => {
    const userId = localStorage.getItem("user_id");
    if (!userId || activeSection !== "history") return;

    const fetchHistory = async () => {
      setHistoryLoading(true);
      setHistoryError("");
      try {
        const offset = (historyPage - 1) * HISTORY_PAGE_SIZE;
        const data = await apiFetch(
          `/settings/recommendation-history?user_id=${userId}&limit=${HISTORY_PAGE_SIZE}&offset=${offset}`
        );
        setHistoryItems(Array.isArray(data.history) ? data.history : []);
        setHistoryTotal(Number(data.total) || 0);
      } catch (err) {
        setHistoryError(err.message || "Unable to load recommendation history.");
        setHistoryItems([]);
        setHistoryTotal(0);
      } finally {
        setHistoryLoading(false);
      }
    };

    fetchHistory();
  }, [activeSection, historyPage]);

  // apply theme + font size whenever they change
  useEffect(() => {
    applyThemeClass(theme);
    applyFontSize(fontSize);
  }, [theme, fontSize]);

  // sends updated UI preferences to the backend
  const updateSettings = async (payload, successMessage = "Settings updated") => {
    const userId = localStorage.getItem("user_id");
    if (!userId) return;

    try {
      await apiFetch("/settings", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ user_id: Number(userId), ...payload }),
      });
      setStatus(successMessage);
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

  const formatWeight = (key, value) => {
    const num = Number(value);
    if (Number.isNaN(num)) return value;
    return num.toFixed(2);
  };

  const updateWeight = (key, value) => {
    setWeights((prev) => ({ ...prev, [key]: value }));
  };

  const validateWeights = (nextWeights) => {
    const entries = Object.entries(nextWeights);
    for (const [, value] of entries) {
      const num = Number(value);
      if (Number.isNaN(num)) {
        return "All weights must be valid numbers.";
      }
      if (num < 0) {
        return "Weights cannot be negative.";
      }
    }
    const total = entries.reduce((sum, [, value]) => sum + Number(value), 0);
    if (total <= 0) {
      return "Total weight must be greater than 0.";
    }
    return "";
  };

  const expandGroupedWeights = (groupedWeights) => {
    const detailed = { semantic: FIXED_SEMANTIC_WEIGHT };

    Object.entries(GROUP_TO_DETAIL_SHARES).forEach(([groupKey, mapping]) => {
      const groupValue = Number(groupedWeights[groupKey] || 0);
      Object.entries(mapping).forEach(([detailKey, share]) => {
        detailed[detailKey] = Number((groupValue * share).toFixed(6));
      });
    });

    return detailed;
  };

  const buildTradeoffPreview = (groupedWeights) => {
    const numericWeights = Object.keys(DEFAULT_MANAGER_WEIGHTS).reduce((acc, key) => {
      const parsed = Number(groupedWeights[key]);
      acc[key] = Number.isNaN(parsed) || parsed < 0 ? 0 : parsed;
      return acc;
    }, {});

    const total = Object.values(numericWeights).reduce((sum, value) => sum + value, 0);

    return Object.keys(DEFAULT_MANAGER_WEIGHTS).reduce((acc, key) => {
      const adjustableShare = total > 0 ? numericWeights[key] / total : 0;
      acc[key] = {
        raw: numericWeights[key],
        finalShare: adjustableShare * ADJUSTABLE_WEIGHT_BUDGET,
      };
      return acc;
    }, {});
  };

  const tradeoffPreview = buildTradeoffPreview(weights);
  const baselineTradeoffPreview = buildTradeoffPreview(savedWeightBaseline);

  const saveWeights = () => {
    const errorMessage = validateWeights(weights);
    if (errorMessage) {
      setStatus(errorMessage);
      setTimeout(() => setStatus(""), 2500);
      return;
    }
    updateSettings(
      { use_custom_weights: true, weights: expandGroupedWeights(weights) },
      "Weightings saved."
    );
    setSavedWeightBaseline({ ...weights });
  };

  const resetWeights = () => {
    const defaults = { ...DEFAULT_MANAGER_WEIGHTS };
    setWeights(defaults);
    setSavedWeightBaseline(defaults);
    updateSettings(
      { use_custom_weights: true, weights: expandGroupedWeights(defaults) },
      "Weightings reset."
    );
  };

  const exportAllData = async () => {
    const userId = localStorage.getItem("user_id");
    if (!userId) {
      setExportStatus("Please log in to export data.");
      return;
    }

    setExporting(true);
    setExportStatus("");
    try {
      const response = await fetch(
        `${API_BASE_URL}/settings/export?user_id=${userId}`,
        { method: "GET" }
      );

      if (!response.ok) {
        const detail = await response.text();
        throw new Error(detail || "Export failed.");
      }

      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement("a");
      const dateTag = new Date().toISOString().slice(0, 10);
      link.href = url;
      link.download = `allocaite_export_${dateTag}.xlsx`;
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
      setExportStatus("Export ready.");
    } catch (err) {
      setExportStatus(err.message || "Unable to export data.");
    } finally {
      setExporting(false);
    }
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
        .filter((skill) =>
          String(skill.skill_name || "").trim() ||
          String(skill.years_experience || "").trim()
        )
        .map((skill) => ({
          skill_name: skill.skill_name,
          years_experience: skill.years_experience,
          skill_type: skill.skill_type || "technical",
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
      setEmployeeSkills([{ skill_name: "", years_experience: "", skill_type: "technical" }]);
      await fetchEmployees();
    } catch (err) {
      setEmployeeStatus({ type: "error", message: err.message || "Unable to add employee." });
    } finally {
      setEmployeeSaving(false);
    }
  };

  const submitExistingEmployeeSkills = async (event) => {
    event.preventDefault();
    setExistingSkillStatus(null);
    setSkillError(null);

    const userId = localStorage.getItem("user_id");
    if (!userId) {
      setExistingSkillStatus({ type: "error", message: "Please log in again." });
      return;
    }
    if (!existingEmployeeId) {
      setExistingSkillStatus({ type: "error", message: "Please choose an employee." });
      return;
    }

    setExistingSkillSaving(true);
    try {
      const skillsPayload = existingEmployeeSkills
        .filter((skill) =>
          String(skill.skill_name || "").trim() ||
          String(skill.years_experience || "").trim()
        )
        .map((skill) => ({
          skill_name: skill.skill_name,
          years_experience: skill.years_experience,
          skill_type: skill.skill_type || "technical",
        }));

      await apiFetch(`/employees/${Number(existingEmployeeId)}/skills`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          user_id: Number(userId),
          skills: skillsPayload,
        }),
      });

      setExistingSkillStatus({ type: "success", message: "Skills added for existing employee." });
      setExistingEmployeeSkills([{ skill_name: "", years_experience: "", skill_type: "technical" }]);
      await fetchEmployees();
    } catch (err) {
      setExistingSkillStatus({
        type: "error",
        message: err.message || "Unable to update employee skills.",
      });
    } finally {
      setExistingSkillSaving(false);
    }
  };

  const handleInviteFormChange = (event) => {
    const { name, value } = event.target;
    setInviteForm((prev) => ({ ...prev, [name]: value }));
  };

  const handleEmployeeSelect = (event) => {
    const value = event.target.value;
    const selected = employeeOptions.find((emp) => String(emp.employee_id) === value);
    setInviteForm((prev) => ({
      ...prev,
      employee_id: value,
      name: selected?.name || prev.name,
    }));
  };

  const submitEmployeeInvite = async (event) => {
    event.preventDefault();
    setInviteStatus(null);
    setInviteLink("");

    const userId = localStorage.getItem("user_id");
    if (!userId) {
      setInviteStatus({ type: "error", message: "Please log in again." });
      return;
    }

    if (!inviteForm.employee_id) {
      setInviteStatus({ type: "error", message: "Employee is required." });
      return;
    }

    setInviteSaving(true);
    try {
      const data = await apiFetch("/invites", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          user_id: Number(userId),
          employee_id: Number(inviteForm.employee_id),
        }),
      });

      setInviteLink(data.invite_link || "");
      setInviteStatus({ type: "success", message: "Invite link created." });
      setInviteForm({ employee_id: "", name: "" });
    } catch (err) {
      setInviteStatus({ type: "error", message: err.message || "Unable to create invite." });
    } finally {
      setInviteSaving(false);
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

  const historyTotalPages = Math.max(1, Math.ceil(historyTotal / HISTORY_PAGE_SIZE));
  const historyStart = historyTotal === 0 ? 0 : (historyPage - 1) * HISTORY_PAGE_SIZE + 1;
  const historyEnd = Math.min(historyPage * HISTORY_PAGE_SIZE, historyTotal);

  return (
    <div className="settings-page">
      {/* top navigation bar */}
      <Menu />

      <div className="settings-content settings-layout">
        <aside className="settings-sidebar">
          <p className="sidebar-title">Sections</p>
          <button
            type="button"
            className={activeSection === "account" ? "active" : ""}
            onClick={() => setActiveSection("account")}
          >
            Account
          </button>
          <button
            type="button"
            className={activeSection === "appearance" ? "active" : ""}
            onClick={() => setActiveSection("appearance")}
          >
            Appearance
          </button>
          <button
            type="button"
            className={activeSection === "weights" ? "active" : ""}
            onClick={() => setActiveSection("weights")}
          >
            Weightings
          </button>
          <button
            type="button"
            className={activeSection === "team" ? "active" : ""}
            onClick={() => setActiveSection("team")}
          >
            Team
          </button>
          <button
            type="button"
            className={activeSection === "history" ? "active" : ""}
            onClick={() => {
              setHistoryPage(1);
              setActiveSection("history");
            }}
          >
            History
          </button>
          <button
            type="button"
            className={activeSection === "export" ? "active" : ""}
            onClick={() => setActiveSection("export")}
          >
            Export
          </button>
        </aside>

        <div className="settings-main">
        <h1>Settings</h1>
        <p className="subtitle">Manage your account and preferences</p>
        {loading && <p>Loading settings...</p>}
        {error && <p className="error">{error}</p>}
        {status && <p className="status-message info">{status}</p>}

        {/* ACCOUNT DETAILS SECTION */}
        {activeSection === "account" && (
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
        )}

        {/* THEME & FONT SIZE SECTION */}
        {activeSection === "appearance" && (
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
        )}

        {activeSection === "weights" && (
        <div className="settings-card">
          <h2>Ranking Weightings</h2>
          <p className="muted">Customise recommendation priorities using a simpler manager view.</p>

          <div className="form-grid">
            <label>
              Skills Fit
              <input
                type="number"
                step="0.01"
                min="0"
                value={formatWeight("skills_fit", weights.skills_fit)}
                onChange={(e) => updateWeight("skills_fit", e.target.value)}
              />
              <span className="weight-inline-hint">
                Now {(tradeoffPreview.skills_fit.finalShare * 100).toFixed(1)}% of manager pool
              </span>
              {Math.abs(
                tradeoffPreview.skills_fit.finalShare - baselineTradeoffPreview.skills_fit.finalShare
              ) > 0.0001 && (
                <span className="weight-inline-hint weight-inline-hint--secondary">
                  Was {(baselineTradeoffPreview.skills_fit.finalShare * 100).toFixed(1)}%
                </span>
              )}
            </label>
            <label>
              Experience & Role
              <input
                step="0.01"
                min="0"
                value={formatWeight("experience_role", weights.experience_role)}
                onChange={(e) => updateWeight("experience_role", e.target.value)}
              />
              <span className="weight-inline-hint">
                Now {(tradeoffPreview.experience_role.finalShare * 100).toFixed(1)}% of manager pool
              </span>
              {Math.abs(
                tradeoffPreview.experience_role.finalShare -
                  baselineTradeoffPreview.experience_role.finalShare
              ) > 0.0001 && (
                <span className="weight-inline-hint weight-inline-hint--secondary">
                  Was {(baselineTradeoffPreview.experience_role.finalShare * 100).toFixed(1)}%
                </span>
              )}
            </label>
            <label>
              Availability
              <input
                type="number"
                step="0.01"
                min="0"
                value={formatWeight("availability_balance", weights.availability_balance)}
                onChange={(e) => updateWeight("availability_balance", e.target.value)}
              />
              <span className="weight-inline-hint">
                Now {(tradeoffPreview.availability_balance.finalShare * 100).toFixed(1)}% of manager pool
              </span>
              {Math.abs(
                tradeoffPreview.availability_balance.finalShare -
                  baselineTradeoffPreview.availability_balance.finalShare
              ) > 0.0001 && (
                <span className="weight-inline-hint weight-inline-hint--secondary">
                  Was {(baselineTradeoffPreview.availability_balance.finalShare * 100).toFixed(1)}%
                </span>
              )}
            </label>
            <label>
              Growth Potential
              <input
                type="number"
                step="0.01"
                min="0"
                value={formatWeight("growth_potential", weights.growth_potential)}
                onChange={(e) => updateWeight("growth_potential", e.target.value)}
              />
              <span className="weight-inline-hint">
                Now {(tradeoffPreview.growth_potential.finalShare * 100).toFixed(1)}% of manager pool
              </span>
              {Math.abs(
                tradeoffPreview.growth_potential.finalShare -
                  baselineTradeoffPreview.growth_potential.finalShare
              ) > 0.0001 && (
                <span className="weight-inline-hint weight-inline-hint--secondary">
                  Was {(baselineTradeoffPreview.growth_potential.finalShare * 100).toFixed(1)}%
                </span>
              )}
            </label>
            <label>
              Past Feedback
              <input
                type="number"
                step="0.01"
                min="0"
                value={formatWeight("past_feedback", weights.past_feedback)}
                onChange={(e) => updateWeight("past_feedback", e.target.value)}
              />
              <span className="weight-inline-hint">
                Now {(tradeoffPreview.past_feedback.finalShare * 100).toFixed(1)}% of manager pool
              </span>
              {Math.abs(
                tradeoffPreview.past_feedback.finalShare -
                  baselineTradeoffPreview.past_feedback.finalShare
              ) > 0.0001 && (
                <span className="weight-inline-hint weight-inline-hint--secondary">
                  Was {(baselineTradeoffPreview.past_feedback.finalShare * 100).toFixed(1)}%
                </span>
              )}
            </label>
          </div>

          <p className="weighting-hint">
            Semantic similarity stays fixed. The remaining {Math.round(ADJUSTABLE_WEIGHT_BUDGET * 100)}% is shared across these five priorities, so when one goes up the others must come down.
          </p>

          <div className="weighting-summary">
            <div className="weighting-summary__item">
              <strong>Skills Fit</strong>
              <span>Technical, possible, and soft skill signals</span>
            </div>
            <div className="weighting-summary__item">
              <strong>Experience & Role</strong>
              <span>Relevant experience and role match</span>
            </div>
            <div className="weighting-summary__item">
              <strong>Availability</strong>
              <span>Availability and workload balance</span>
            </div>
            <div className="weighting-summary__item">
              <strong>Growth Potential</strong>
              <span>Preferences and learning goals</span>
            </div>
            <div className="weighting-summary__item">
              <strong>Past Feedback</strong>
              <span>Historical manager feedback on similar tasks</span>
            </div>
          </div>

          <div className="button-row">
            <button className="primary" onClick={saveWeights}>
              Save Weightings
            </button>
            <button onClick={resetWeights}>
              Reset to Default
            </button>
          </div>
        </div>
        )}

        {activeSection === "history" && (
        <div className="settings-card">
          <h2>Recommendation History</h2>
          <p className="muted">Revisit previous recommendation requests, selections, and later feedback.</p>

          {historyLoading && <p className="muted">Loading recommendation history...</p>}
          {historyError && <p className="status-message error">{historyError}</p>}

          {!historyLoading && !historyError && historyItems.length === 0 && (
            <p className="muted">No recommendation history yet.</p>
          )}

          {!historyLoading && historyItems.length > 0 && (
            <>
              <div className="history-pagination">
                <p className="muted">
                  Showing {historyStart}-{historyEnd} of {historyTotal} requests
                </p>
                <div className="history-pagination__actions">
                  <button
                    type="button"
                    onClick={() => setHistoryPage((prev) => Math.max(1, prev - 1))}
                    disabled={historyLoading || historyPage === 1}
                  >
                    Previous
                  </button>
                  <span className="history-page-indicator">
                    Page {historyPage} of {historyTotalPages}
                  </span>
                  <button
                    type="button"
                    onClick={() => setHistoryPage((prev) => Math.min(historyTotalPages, prev + 1))}
                    disabled={historyLoading || historyPage >= historyTotalPages}
                  >
                    Next
                  </button>
                </div>
              </div>

              <div className="history-list">
                {historyItems.map((item) => (
                  <div key={item.task_id} className="history-card">
                    <div className="history-card__header">
                      <div>
                        <h3>{buildHistoryTitle(item)}</h3>
                        <p className="history-meta">
                          {item.start_date} – {item.end_date}
                        </p>
                      </div>
                      <span className="history-badge">Request #{item.task_id}</span>
                    </div>

                    {item.assignment_title && item.assignment_title.trim() !== item.task_description?.trim() && (
                      <p className="history-description">{item.task_description}</p>
                    )}

                    <div className="history-grid">
                      <div>
                        <strong>Chosen employee</strong>
                        <p>{item.selected_employee_name || "Not assigned from recommendations"}</p>
                      </div>
                      <div>
                        <strong>Rating</strong>
                        <p>{item.performance_rating || "No rating yet"}</p>
                      </div>
                      <div>
                        <strong>Feedback date</strong>
                        <p>{item.feedback_at ? new Date(item.feedback_at).toLocaleString() : "No feedback yet"}</p>
                      </div>
                    </div>

                    {Array.isArray(item.outcome_tags) && item.outcome_tags.length > 0 && (
                      <div className="history-tags">
                        {item.outcome_tags.map((tag) => (
                          <span key={`${item.task_id}-${tag}`} className="history-tag">
                            {tag}
                          </span>
                        ))}
                      </div>
                    )}

                    {item.feedback_notes && (
                      <div className="history-notes">
                        <strong>Notes</strong>
                        <p>{item.feedback_notes}</p>
                      </div>
                    )}

                    {Array.isArray(item.top_candidates) && item.top_candidates.length > 0 && (
                      <div className="history-candidates">
                        <strong>Top recommendations</strong>
                        <div className="history-candidate-list">
                          {item.top_candidates.map((candidate) => (
                            <span key={`${item.task_id}-${candidate.rank}-${candidate.employee_id}`} className="history-candidate">
                              #{candidate.rank} {candidate.employee_name}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </>
          )}
        </div>
        )}

        {activeSection === "export" && (
        <div className="settings-card">
          <h2>Export Data</h2>
          <p className="muted">Download all your team data in the same Excel format as uploads.</p>
          <div className="button-row">
            <button className="primary" onClick={exportAllData} disabled={exporting}>
              {exporting ? "Exporting..." : "Export All Data"}
            </button>
          </div>
          {exportStatus && <p className="status-message info">{exportStatus}</p>}
        </div>
        )}

        {/* EMPLOYEE MANAGEMENT SECTION */}
        {activeSection === "team" && (
        <>
        <div className="settings-card">
          <h2>Add Skills To Existing Employee</h2>
          <p className="muted">Select an existing employee and add or update their technical or soft skills.</p>

          <form className="settings-form" onSubmit={submitExistingEmployeeSkills}>
            <div className="form-grid">
              <label>
                Employee
                <select
                  value={existingEmployeeId}
                  onChange={(e) => setExistingEmployeeId(e.target.value)}
                >
                  <option value="">Select employee</option>
                  {employeeOptions.map((emp) => (
                    <option key={emp.employee_id} value={emp.employee_id}>
                      {emp.name} (ID {emp.employee_id})
                    </option>
                  ))}
                </select>
              </label>

              <div className="skill-rows">
                {existingEmployeeSkills.map((skill, index) => (
                  <div key={index} className="form-grid skill-row">
                    <label>
                      Skill Type
                      <select
                        value={skill.skill_type || "technical"}
                        onChange={(e) => {
                          const updated = [...existingEmployeeSkills];
                          updated[index] = {
                            ...updated[index],
                            skill_type: e.target.value,
                          };
                          setExistingEmployeeSkills(updated);
                        }}
                      >
                        <option value="technical">Technical</option>
                        <option value="soft">Soft</option>
                      </select>
                    </label>

                    <label>
                      Skill Name
                      <input
                        type="text"
                        value={skill.skill_name}
                        onChange={(e) => {
                          const updated = [...existingEmployeeSkills];
                          updated[index] = {
                            ...updated[index],
                            skill_name: e.target.value,
                          };
                          setExistingEmployeeSkills(updated);
                        }}
                        placeholder="Skill"
                      />
                    </label>

                    <label>
                      Skill Experience (Years)
                      <input
                        type="number"
                        value={skill.years_experience}
                        onChange={(e) => {
                          const updated = [...existingEmployeeSkills];
                          updated[index] = {
                            ...updated[index],
                            years_experience: e.target.value,
                          };
                          setExistingEmployeeSkills(updated);
                        }}
                        placeholder="Years"
                        min="0"
                        step="0.1"
                      />
                    </label>

                    {existingEmployeeSkills.length > 1 && (
                      <label>
                        &nbsp;
                        <button
                          type="button"
                          className="ghost-btn"
                          onClick={() => {
                            const updated = existingEmployeeSkills.filter((_, i) => i !== index);
                            setExistingEmployeeSkills(updated);
                          }}
                        >
                          Remove
                        </button>
                      </label>
                    )}
                  </div>
                ))}
              </div>
            </div>

            <div className="button-row">
              <button
                type="button"
                onClick={() =>
                  setExistingEmployeeSkills((prev) => [
                    ...prev,
                    { skill_name: "", years_experience: "", skill_type: "technical" },
                  ])
                }
              >
                Add Skill
              </button>
            </div>

            {existingSkillStatus && (
              <p className={`status-message ${existingSkillStatus.type || ""}`}>
                {existingSkillStatus.message}
              </p>
            )}

            <div className="button-row">
              <button className="primary" type="submit" disabled={existingSkillSaving}>
                {existingSkillSaving ? "Saving..." : "Save Skills"}
              </button>
            </div>
          </form>
        </div>

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
                  placeholder="Name"
                />
              </label>

              <label>
                Role
                <input
                  type="text"
                  name="role"
                  value={employeeForm.role}
                  onChange={handleEmployeeChange}
                  placeholder="Role"
                />
              </label>

              <label>
                Department
                <input
                  type="text"
                  name="department"
                  value={employeeForm.department}
                  onChange={handleEmployeeChange}
                  placeholder="Department"
                />
              </label>

              <div className="skill-rows">
                {employeeSkills.map((skill, index) => (
                  <div key={index} className="form-grid skill-row">
                  <label>
                    Skill Type
                    <select
                      value={skill.skill_type || "technical"}
                      onChange={(e) => {
                        const updated = [...employeeSkills];
                        updated[index] = {
                          ...updated[index],
                          skill_type: e.target.value,
                        };
                        setEmployeeSkills(updated);
                      }}
                    >
                      <option value="technical">Technical</option>
                      <option value="soft">Soft</option>
                    </select>
                  </label>

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
                      placeholder="Skill"
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
                      placeholder="Years"
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
            </div>

            <div className="button-row">
              <button
                type="button"
                onClick={() => {
                  setSkillError(null);
                  setEmployeeSkills((prev) => [
                    ...prev,
                    { skill_name: "", years_experience: "", skill_type: "technical" },
                  ]);
                }}
              >
                Add Skill
              </button>
            </div>

            {skillError && <p className="form-error">{skillError}</p>}

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
        </>
        )}

        {/* EMPLOYEE INVITE SECTION */}
        {activeSection === "team" && (
        <div className="settings-card">
          <h2>Create Employee Invite</h2>
          <p className="muted">Generate a link for an employee to create their account.</p>

          <form className="settings-form" onSubmit={submitEmployeeInvite}>
            <div className="form-grid">
              <label>
                Employee
                <select
                  name="employee_id"
                  value={inviteForm.employee_id}
                  onChange={handleEmployeeSelect}
                >
                  <option value="">Select employee</option>
                  {employeeOptions.map((emp) => (
                    <option key={emp.employee_id} value={emp.employee_id}>
                      {emp.name} (ID {emp.employee_id})
                    </option>
                  ))}
                </select>
              </label>

              <label>
                Name
                <input
                  type="text"
                  name="name"
                  value={inviteForm.name}
                  onChange={handleInviteFormChange}
                  placeholder="Employee name"
                />
              </label>

            </div>

            <div className="button-row">
              <button className="primary" type="submit" disabled={inviteSaving}>
                {inviteSaving ? "Generating..." : "Generate Invite Link"}
              </button>
            </div>

            {inviteStatus && (
              <p className={`status-message ${inviteStatus.type || ""}`}>
                {inviteStatus.message}
              </p>
            )}

            {inviteLink && (
              <div className="invite-link">
                <p className="muted">Copy and share this link:</p>
                <div className="copy-row">
                  <input type="text" readOnly value={inviteLink} />
                  <button
                    type="button"
                    onClick={() => navigator.clipboard.writeText(inviteLink)}
                  >
                    Copy
                  </button>
                </div>
              </div>
            )}
          </form>
        </div>
        )}
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
