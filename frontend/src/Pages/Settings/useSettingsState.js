import { useCallback, useEffect, useMemo, useState } from "react";

import { apiDownload, apiFetch } from "../../api";
import { formatMemberSince } from "../../lib/formatters";
import { getSessionItem, setSessionItem } from "../../session";
import {
  applyFontSize,
  applyThemeClass,
  DEFAULT_FONT_SIZE,
  DEFAULT_THEME,
  readPreference,
  writePreference,
} from "../../lib/preferences";
import {
  ADJUSTABLE_WEIGHT_BUDGET,
  DEFAULT_MANAGER_WEIGHTS,
  FIXED_SEMANTIC_WEIGHT,
  GROUP_TO_DETAIL_SHARES,
  HISTORY_PAGE_SIZE,
  MANAGER_WEIGHT_TOTAL,
} from "./constants";

const DEFAULT_SKILL_ROW = { skill_name: "", years_experience: "", skill_type: "technical" };

const buildHistoryTitle = (item) => {
  const assignmentTitle = String(item?.assignment_title || "").trim();
  if (assignmentTitle) return assignmentTitle;
  return String(item?.task_description || "").trim();
};

const buildCollapsedHistoryTitle = (item) => {
  const title = buildHistoryTitle(item);
  if (title.length <= 60) return title;
  return `${title.slice(0, 57).trimEnd()}...`;
};

const buildTopMatchesLabel = (item) => {
  if (!Array.isArray(item?.top_candidates) || item.top_candidates.length === 0) {
    return "No recommendations";
  }
  return item.top_candidates
    .slice(0, 3)
    .map((candidate) => `#${candidate.rank} ${candidate.employee_name}`)
    .join("   ");
};

const getWeightPoints = (value) => Math.round(Number(value || 0) * 100);

const validateWeights = (nextWeights) => {
  const entries = Object.entries(nextWeights);
  for (const [, value] of entries) {
    const num = Number(value);
    if (Number.isNaN(num)) return "All weights must be valid numbers.";
    if (num < 0) return "Weights cannot be negative.";
  }
  const total = entries.reduce((sum, [, value]) => sum + Number(value), 0);
  if (Math.abs(total - MANAGER_WEIGHT_TOTAL) > 0.0001) {
    return "Weights must add up to 0.65 (65%).";
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

export function useSettingsCoreState() {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [status, setStatus] = useState("");
  const [exportStatus, setExportStatus] = useState("");
  const [exporting, setExporting] = useState(false);
  const [account, setAccount] = useState({
    name: getSessionItem("name") || "Unknown User",
    email: getSessionItem("email") || "unknown",
    member_since: getSessionItem("member_since") || "-",
  });
  const [theme, setTheme] = useState(() => readPreference("theme", DEFAULT_THEME));
  const [fontSize, setFontSize] = useState(() => readPreference("fontSize", DEFAULT_FONT_SIZE));
  const [weights, setWeights] = useState({ ...DEFAULT_MANAGER_WEIGHTS });
  const [isEditModalOpen, setEditModalOpen] = useState(false);
  const [isPasswordModalOpen, setPasswordModalOpen] = useState(false);
  const [detailsStatus, setDetailsStatus] = useState(null);
  const [detailsForm, setDetailsForm] = useState({
    name: getSessionItem("name") || "",
    email: getSessionItem("email") || "",
  });
  const [passwordStatus, setPasswordStatus] = useState(null);
  const [verifyStatus, setVerifyStatus] = useState(null);
  const [passwordVerified, setPasswordVerified] = useState(false);
  const [passwordForm, setPasswordForm] = useState({
    current: "",
    next: "",
    confirm: "",
  });

  const updateSettings = useCallback(async (payload, successMessage = "Settings updated") => {
    const userId = getSessionItem("user_id");
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
  }, []);

  useEffect(() => {
    const userId = getSessionItem("user_id");
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
        if (data.weights) {
          const groupedWeights = {
            skills_fit:
              (data.weights.skill ?? 0) +
              (data.weights.possible_skill ?? 0) +
              (data.weights.soft_skill ?? 0) +
              (data.weights.possible_soft_skill ?? 0),
            experience_role: (data.weights.experience ?? 0) + (data.weights.role ?? 0),
            availability_balance:
              (data.weights.availability ?? 0) + (data.weights.fairness ?? 0),
            growth_potential:
              data.weights.preferences ?? DEFAULT_MANAGER_WEIGHTS.growth_potential,
            past_feedback: data.weights.feedback ?? DEFAULT_MANAGER_WEIGHTS.past_feedback,
          };
          setWeights(
            Object.fromEntries(
              Object.entries(groupedWeights).map(([key, value]) => [key, Number(value.toFixed(2))])
            )
          );
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

  useEffect(() => {
    setDetailsForm({
      name: account.name || "",
      email: account.email || "",
    });
  }, [account]);

  const totalAllocatedPoints = useMemo(
    () => Object.values(weights).reduce((sum, value) => sum + getWeightPoints(value), 0),
    [weights]
  );
  const remainingWeightPoints = useMemo(
    () => Math.max(0, Math.round(ADJUSTABLE_WEIGHT_BUDGET * 100) - totalAllocatedPoints),
    [totalAllocatedPoints]
  );

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

  const updateWeightAllocation = (key, nextPoints) => {
    const safePoints = Math.max(0, Number(nextPoints) || 0);
    setWeights((prev) => {
      const otherPoints = Object.entries(prev).reduce((sum, [groupKey, value]) => {
        if (groupKey === key) return sum;
        return sum + getWeightPoints(value);
      }, 0);
      const maxAllowedPoints = Math.max(
        0,
        Math.round(ADJUSTABLE_WEIGHT_BUDGET * 100) - otherPoints
      );
      const clampedPoints = Math.min(safePoints, maxAllowedPoints);
      return {
        ...prev,
        [key]: Number((clampedPoints / 100).toFixed(2)),
      };
    });
  };

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
  };

  const resetWeights = () => {
    const defaults = { ...DEFAULT_MANAGER_WEIGHTS };
    setWeights(defaults);
    updateSettings(
      { use_custom_weights: true, weights: expandGroupedWeights(defaults) },
      "Weightings reset."
    );
  };

  const exportAllData = async () => {
    const userId = getSessionItem("user_id");
    if (!userId) {
      setExportStatus("Please log in to export data.");
      return;
    }

    setExporting(true);
    setExportStatus("");
    try {
      const blob = await apiDownload(`/settings/export?user_id=${userId}`, { method: "GET" });
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

  const handleDetailsChange = (event) => {
    const { name, value } = event.target;
    setDetailsForm((prev) => ({ ...prev, [name]: value }));
  };

  const openEditModal = () => {
    setDetailsStatus(null);
    setDetailsForm({ name: account.name, email: account.email });
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
    const userId = getSessionItem("user_id");

    if (!userId) {
      setDetailsStatus({ type: "error", message: "Please log in again." });
      return;
    }
    if (!detailsForm.name.trim() && !detailsForm.email.trim()) {
      setDetailsStatus({ type: "error", message: "Provide a new name or email." });
      return;
    }

    try {
      const data = await apiFetch("/settings/details", {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          user_id: Number(userId),
          name: detailsForm.name.trim() || undefined,
          email: detailsForm.email.trim() || undefined,
        }),
      });

      setAccount({
        name: data.name,
        email: data.email,
        member_since: data.member_since,
      });
      setSessionItem("name", data.name);
      setSessionItem("email", data.email);
      if (data.member_since) {
        setSessionItem("member_since", data.member_since);
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

    const userId = getSessionItem("user_id");
    if (!userId) {
      setVerifyStatus({ type: "error", message: "Please log in again." });
      return;
    }
    if (!passwordForm.current) {
      setVerifyStatus({ type: "error", message: "Enter your current password." });
      return;
    }

    try {
      const data = await apiFetch("/settings/password/verify", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          user_id: Number(userId),
          current_password: passwordForm.current,
        }),
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

    const userId = getSessionItem("user_id");
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
      const data = await apiFetch("/settings/password", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          user_id: Number(userId),
          current_password: passwordForm.current,
          new_password: passwordForm.next,
        }),
      });
      setPasswordStatus({ type: "success", message: data.message || "Password updated." });
      setPasswordForm({ current: "", next: "", confirm: "" });
    } catch (err) {
      setPasswordStatus({ type: "error", message: err.message || "Unable to update password." });
    }
  };

  return {
    loading,
    error,
    status,
    exportStatus,
    exporting,
    account,
    theme,
    fontSize,
    weights,
    totalAllocatedPoints,
    remainingWeightPoints,
    isEditModalOpen,
    isPasswordModalOpen,
    detailsStatus,
    detailsForm,
    passwordStatus,
    verifyStatus,
    passwordVerified,
    passwordForm,
    formatMemberSince,
    getWeightPoints,
    changeTheme,
    changeFontSize,
    updateWeightAllocation,
    saveWeights,
    resetWeights,
    exportAllData,
    handleDetailsChange,
    openEditModal,
    closeEditModal,
    openPasswordModal,
    closePasswordModal,
    submitDetails,
    handlePasswordChange,
    verifyCurrentPassword,
    submitPassword,
  };
}

export function useTeamManagementState() {
  const [employeeForm, setEmployeeForm] = useState({
    name: "",
    role: "",
    department: "",
  });
  const [employeeSkills, setEmployeeSkills] = useState([{ ...DEFAULT_SKILL_ROW }]);
  const [existingEmployeeId, setExistingEmployeeId] = useState("");
  const [existingEmployeeSkills, setExistingEmployeeSkills] = useState([{ ...DEFAULT_SKILL_ROW }]);
  const [skillError, setSkillError] = useState(null);
  const [employeeStatus, setEmployeeStatus] = useState(null);
  const [employeeSaving, setEmployeeSaving] = useState(false);
  const [existingSkillStatus, setExistingSkillStatus] = useState(null);
  const [existingSkillSaving, setExistingSkillSaving] = useState(false);
  const [employeeOptions, setEmployeeOptions] = useState([]);
  const [inviteForm, setInviteForm] = useState({
    employee_id: "",
    name: "",
  });
  const [inviteStatus, setInviteStatus] = useState(null);
  const [inviteLink, setInviteLink] = useState("");
  const [inviteSaving, setInviteSaving] = useState(false);

  const fetchEmployees = useCallback(async () => {
    const userId = getSessionItem("user_id");
    if (!userId) return;
    try {
      const data = await apiFetch(`/employees?user_id=${userId}`);
      setEmployeeOptions(data.employees || []);
    } catch {
      setEmployeeOptions([]);
    }
  }, []);

  useEffect(() => {
    fetchEmployees();
  }, [fetchEmployees]);

  const handleEmployeeChange = (event) => {
    const { name, value } = event.target;
    setEmployeeForm((prev) => ({ ...prev, [name]: value }));
  };

  const submitEmployee = async (event) => {
    event.preventDefault();
    setEmployeeStatus(null);
    setSkillError(null);
    const userId = getSessionItem("user_id");
    if (!userId) {
      setEmployeeStatus({ type: "error", message: "Please log in again." });
      return;
    }

    setEmployeeSaving(true);
    try {
      const skillsPayload = employeeSkills
        .filter(
          (skill) =>
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
      setEmployeeForm({ name: "", role: "", department: "" });
      setEmployeeSkills([{ ...DEFAULT_SKILL_ROW }]);
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
    const userId = getSessionItem("user_id");
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
        .filter(
          (skill) =>
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
      setExistingEmployeeSkills([{ ...DEFAULT_SKILL_ROW }]);
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
    const userId = getSessionItem("user_id");
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

  return {
    employeeForm,
    onEmployeeChange: handleEmployeeChange,
    employeeSkills,
    setEmployeeSkills,
    existingEmployeeId,
    setExistingEmployeeId,
    existingEmployeeSkills,
    setExistingEmployeeSkills,
    skillError,
    employeeStatus,
    employeeSaving,
    existingSkillStatus,
    existingSkillSaving,
    employeeOptions,
    inviteForm,
    inviteStatus,
    inviteLink,
    inviteSaving,
    onSubmitEmployee: submitEmployee,
    onSubmitExistingSkills: submitExistingEmployeeSkills,
    onInviteFormChange: handleInviteFormChange,
    onEmployeeSelect: handleEmployeeSelect,
    onSubmitInvite: submitEmployeeInvite,
  };
}

export function useRecommendationHistoryState(activeSection) {
  const [historyItems, setHistoryItems] = useState([]);
  const [historyLoading, setHistoryLoading] = useState(false);
  const [historyError, setHistoryError] = useState("");
  const [historyPage, setHistoryPage] = useState(1);
  const [historyTotal, setHistoryTotal] = useState(0);
  const [expandedHistory, setExpandedHistory] = useState({});

  useEffect(() => {
    const userId = getSessionItem("user_id");
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

  const historyTotalPages = Math.max(1, Math.ceil(historyTotal / HISTORY_PAGE_SIZE));
  const historyStart = historyTotal === 0 ? 0 : (historyPage - 1) * HISTORY_PAGE_SIZE + 1;
  const historyEnd = Math.min(historyPage * HISTORY_PAGE_SIZE, historyTotal);

  const toggleHistoryCard = (taskId) => {
    setExpandedHistory((prev) => ({
      ...prev,
      [taskId]: !prev[taskId],
    }));
  };

  return {
    historyItems,
    historyLoading,
    historyError,
    historyPage,
    historyTotal,
    historyTotalPages,
    historyStart,
    historyEnd,
    expandedHistory,
    setHistoryPage,
    toggleHistoryCard,
    buildHistoryTitle,
    buildCollapsedHistoryTitle,
    buildTopMatchesLabel,
  };
}
