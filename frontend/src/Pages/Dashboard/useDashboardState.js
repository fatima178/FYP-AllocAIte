import { useEffect, useMemo, useRef, useState } from "react";

import { apiFetch } from "../../api";
import { redirectToLogin } from "../../lib/navigation";
import { getSessionItem } from "../../session";


export function useDashboardState() {
  const accountType = getSessionItem("account_type") || "manager";
  const [userId, setUserId] = useState(null);
  const [searchTerm, setSearchTerm] = useState("");
  const [availableSkills, setAvailableSkills] = useState([]);
  const [selectedSkills, setSelectedSkills] = useState([]);
  const [skillSearch, setSkillSearch] = useState("");
  const [availability, setAvailability] = useState("");
  const [rangeStartInput, setRangeStartInput] = useState("");
  const [rangeEndInput, setRangeEndInput] = useState("");
  const [appliedRange, setAppliedRange] = useState({ start: "", end: "" });
  const [data, setData] = useState(null);
  const [employees, setEmployees] = useState([]);
  const [error, setError] = useState(null);
  const [pendingSkillRequests, setPendingSkillRequests] = useState([]);
  const [pendingSkillLoading, setPendingSkillLoading] = useState(false);
  const [pendingSkillError, setPendingSkillError] = useState("");
  const [reviewingSkillId, setReviewingSkillId] = useState(null);
  const [skillsOpen, setSkillsOpen] = useState(false);
  const [rangeOpen, setRangeOpen] = useState(false);
  const skillsRef = useRef(null);
  const rangeRef = useRef(null);

  useEffect(() => {
    const storedUser = getSessionItem("user_id");
    if (!storedUser) {
      redirectToLogin();
      return;
    }
    setUserId(storedUser);
  }, []);

  useEffect(() => {
    const handleClick = (event) => {
      if (skillsRef.current && !skillsRef.current.contains(event.target)) {
        setSkillsOpen(false);
      }
      if (rangeRef.current && !rangeRef.current.contains(event.target)) {
        setRangeOpen(false);
      }
    };

    document.addEventListener("mousedown", handleClick);
    return () => document.removeEventListener("mousedown", handleClick);
  }, []);

  useEffect(() => {
    if (!userId) return;

    const fetchSummary = async () => {
      try {
        const params = new URLSearchParams({ user_id: userId });
        if (appliedRange.start && appliedRange.end) {
          params.append("start_date", appliedRange.start);
          params.append("end_date", appliedRange.end);
        }
        const json = await apiFetch(`/dashboard/summary?${params.toString()}`);
        setData(json);
      } catch (err) {
        setError("Could not load dashboard data.");
      }
    };

    fetchSummary();
  }, [userId, appliedRange]);

  useEffect(() => {
    if (!userId) return;

    const fetchEmployees = async () => {
      try {
        const params = new URLSearchParams({ user_id: userId });
        if (searchTerm.trim()) params.append("search", searchTerm.trim());
        selectedSkills.forEach((skill) => params.append("skills", skill));
        if (availability) params.append("availability", availability);
        if (appliedRange.start && appliedRange.end) {
          params.append("start_date", appliedRange.start);
          params.append("end_date", appliedRange.end);
        }
        const json = await apiFetch(`/dashboard/employees?${params.toString()}`);
        setEmployees(json.employees || []);
      } catch {
        setEmployees([]);
      }
    };

    fetchEmployees();
  }, [userId, searchTerm, selectedSkills, availability, appliedRange]);

  useEffect(() => {
    if (!userId) return;
    const fetchSkills = async () => {
      try {
        const json = await apiFetch(`/dashboard/skills?user_id=${userId}`);
        setAvailableSkills(json.skills || []);
      } catch {
        setAvailableSkills([]);
      }
    };
    fetchSkills();
  }, [userId]);

  useEffect(() => {
    if (!userId || accountType !== "manager") return;

    const fetchPendingSkillRequests = async () => {
      setPendingSkillLoading(true);
      setPendingSkillError("");
      try {
        const payload = await apiFetch(`/employee/skills/pending?user_id=${userId}`);
        setPendingSkillRequests(
          Array.isArray(payload.pending_skill_requests) ? payload.pending_skill_requests : []
        );
      } catch (err) {
        setPendingSkillError(err.message || "Unable to load skill requests.");
        setPendingSkillRequests([]);
      } finally {
        setPendingSkillLoading(false);
      }
    };

    fetchPendingSkillRequests();
  }, [userId, accountType]);

  const handleSkillChange = (event) => {
    const { value, checked } = event.target;
    setSelectedSkills((prev) => (checked ? [...prev, value] : prev.filter((s) => s !== value)));
  };

  const removeSelectedSkill = (skill) => {
    setSelectedSkills((prev) => prev.filter((s) => s !== skill));
  };

  const applyDateRange = () => {
    if (rangeStartInput && rangeEndInput) {
      setAppliedRange({ start: rangeStartInput, end: rangeEndInput });
      return;
    }
    if (!rangeStartInput && !rangeEndInput) {
      setAppliedRange({ start: "", end: "" });
    }
  };

  const clearDateRange = () => {
    setRangeStartInput("");
    setRangeEndInput("");
    setAppliedRange({ start: "", end: "" });
  };

  const reviewSkillRequest = async (requestId, approve) => {
    if (!userId || !requestId) return;
    setReviewingSkillId(requestId);
    setPendingSkillError("");
    try {
      await apiFetch("/employee/skills/review", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          user_id: Number(userId),
          request_id: Number(requestId),
          approve,
        }),
      });
      setPendingSkillRequests((prev) => prev.filter((item) => item.request_id !== requestId));
    } catch (err) {
      setPendingSkillError(err.message || "Unable to review skill request.");
    } finally {
      setReviewingSkillId(null);
    }
  };

  const filteredAvailableSkills = useMemo(
    () =>
      availableSkills.filter((skill) =>
        String(skill || "").toLowerCase().includes(skillSearch.trim().toLowerCase())
      ),
    [availableSkills, skillSearch]
  );

  const labels = useMemo(
    () => ({
      availabilityLabel:
        appliedRange.start && appliedRange.end
          ? `Availability (${appliedRange.start} → ${appliedRange.end})`
          : "Weekly Availability",
      summaryAvailabilityLabel:
        appliedRange.start && appliedRange.end ? "Available in Range" : "Available This Week",
      summaryProjectsLabel:
        appliedRange.start && appliedRange.end ? "Active Projects (Range)" : "Active Projects",
      selectedSkillsLabel: selectedSkills.length
        ? `${selectedSkills.length} skills selected`
        : "Filter by skills",
      selectedRangeLabel:
        appliedRange.start && appliedRange.end
          ? `${appliedRange.start} → ${appliedRange.end}`
          : "Filter by date range",
    }),
    [appliedRange, selectedSkills.length]
  );

  const isNewUser = (data?.total_employees || 0) === 0;

  return {
    accountType,
    data,
    isNewUser,
    employees,
    error,
    searchTerm,
    setSearchTerm,
    availableSkills,
    selectedSkills,
    skillSearch,
    setSkillSearch,
    availability,
    setAvailability,
    rangeStartInput,
    setRangeStartInput,
    rangeEndInput,
    setRangeEndInput,
    appliedRange,
    labels,
    filteredAvailableSkills,
    handleSkillChange,
    removeSelectedSkill,
    applyDateRange,
    clearDateRange,
    skillsOpen,
    setSkillsOpen,
    rangeOpen,
    setRangeOpen,
    skillsRef,
    rangeRef,
    pendingSkillRequests,
    pendingSkillLoading,
    pendingSkillError,
    reviewingSkillId,
    reviewSkillRequest,
  };
}
