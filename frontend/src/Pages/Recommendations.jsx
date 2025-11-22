import React, { useMemo, useState } from "react";
import Menu from "./Menu";
import "../styles/Recommendations.css";
import { apiFetch } from "../api";

function RecommendationsPage() {
  const recommendations = useMemo(() => {
    const saved = localStorage.getItem("recommendations");
    if (!saved) return [];

    try {
      const parsed = JSON.parse(saved);
      return Array.isArray(parsed) ? parsed : [];
    } catch {
      return [];
    }
  }, []);

  const taskContext = useMemo(() => {
    const saved = localStorage.getItem("recommendations_context");
    if (!saved) return null;
    try {
      const parsed = JSON.parse(saved);
      if (
        parsed &&
        typeof parsed.task_description === "string" &&
        parsed.start_date &&
        parsed.end_date
      ) {
        return parsed;
      }
      return null;
    } catch {
      return null;
    }
  }, []);

  const [status, setStatus] = useState({ type: null, message: "" });
  const [modalOpen, setModalOpen] = useState(false);
  const [selectedEmployee, setSelectedEmployee] = useState(null);
  const [assignLoading, setAssignLoading] = useState(false);
  const [taskLabel, setTaskLabel] = useState("");

  const openAssignModal = (emp) => {
    if (!taskContext) {
      setStatus({
        type: "error",
        message: "Missing task details. Please regenerate recommendations.",
      });
      return;
    }

    const userId = localStorage.getItem("user_id");
    if (!userId) {
      setStatus({
        type: "error",
        message: "Please log in before assigning a task.",
      });
      return;
    }

    setStatus({ type: null, message: "" });
    setSelectedEmployee(emp);
    setTaskLabel(taskContext.task_description || "");
    setModalOpen(true);
  };

  const handleCloseModal = () => {
    if (assignLoading) return;
    setModalOpen(false);
    setSelectedEmployee(null);
    setTaskLabel("");
  };

  const confirmAssign = async () => {
    if (!selectedEmployee || !taskContext) return;

    const cleanedLabel = (taskLabel || "").trim();
    if (!cleanedLabel) {
      setStatus({
        type: "error",
        message: "Please enter a short task label before assigning.",
      });
      return;
    }

    const userId = localStorage.getItem("user_id");
    if (!userId) {
      setStatus({
        type: "error",
        message: "Please log in before assigning a task.",
      });
      return;
    }

    setAssignLoading(true);
    setStatus({ type: "info", message: "Assigning task..." });
    try {
      const payload = {
        user_id: Number(userId),
        employee_id: selectedEmployee.employee_id,
        task_description: cleanedLabel,
        start_date: taskContext.start_date,
        end_date: taskContext.end_date,
      };

      const uploadId = localStorage.getItem("active_upload_id");
      if (uploadId) {
        payload.upload_id = Number(uploadId);
      }

      const response = await apiFetch("/recommend/assign", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      setStatus({
        type: "success",
        message: response.message || "Task assigned successfully.",
      });
      setModalOpen(false);
      setSelectedEmployee(null);
      setTaskLabel("");
    } catch (err) {
      setStatus({
        type: "error",
        message: err.message || "Unable to assign task.",
      });
    } finally {
      setAssignLoading(false);
    }
  };

  if (recommendations.length === 0) {
    return (
      <>
        <Menu />
        <div className="recommendations-container">
          <div className="no-recommendations">
            <h2>No Recommendations Yet</h2>
            <p>Go to Assignments to generate recommendations.</p>
          </div>
        </div>
      </>
    );
  }

  return (
    <>
      <Menu />

      <div className="recommendations-container">
        <h2>Recommended Employees</h2>
        {status.message && (
          <p className={`status-message ${status.type || ""}`}>
            {status.message}
          </p>
        )}

        <div className="recommendations-list">
          {recommendations.map((emp, index) => {
            const scorePercent =
              typeof emp.score_percent === "number" ? emp.score_percent : 0;
            const availabilityPercent =
              typeof emp.availability_percent === "number"
                ? emp.availability_percent
                : 0;
            const availabilityLabel =
              emp.availability_label || "Availability";
            const skills = Array.isArray(emp.skills) ? emp.skills : [];
            const reason =
              typeof emp.reason === "string" && emp.reason.trim().length > 0
                ? emp.reason
                : "Relevant profile for this task.";

            return (
              <div
                key={emp.employee_id || index}
                className="rec-card"
              >
                <div className="rec-header">
                  <div>
                    <h3>{emp.name || "Unknown employee"}</h3>
                    <p className="role">{emp.role || "Not specified"}</p>
                  </div>
                  <div className="score-circle">{scorePercent}%</div>
                </div>

                <p>
                  <strong>Availability:</strong>{" "}
                  {availabilityLabel} ({availabilityPercent}%)
                </p>

                <p>
                  <strong>Applicable Skills:</strong>{" "}
                  {skills.length > 0 ? skills.join(", ") : "None matched"}
                </p>

                <div className="reason-box">
                  <strong>Why this match:</strong>
                  <p>{reason}</p>
                </div>

                <button
                  type="button"
                  className="assign-btn"
                  onClick={() => openAssignModal(emp)}
                >
                  Assign
                </button>
              </div>
            );
          })}
        </div>
      </div>

      {modalOpen && selectedEmployee && (
        <div className="assign-modal-overlay">
          <div className="assign-modal">
            <h3>Confirm Assignment</h3>
            <p>
              Are you sure you want to assign{" "}
              <strong>{selectedEmployee.name}</strong> to this task?
            </p>
            <label className="modal-label">
              Task label (appears on Tasks page)
              <input
                type="text"
                value={taskLabel}
                onChange={(e) => setTaskLabel(e.target.value)}
                placeholder="e.g., UI Mockups for Sprint 5"
                disabled={assignLoading}
              />
            </label>
            <div className="modal-task-details">
              <p>{taskContext?.task_description}</p>
              {taskContext?.start_date && taskContext?.end_date && (
                <p>
                  <strong>
                    {taskContext.start_date} – {taskContext.end_date}
                  </strong>
                </p>
              )}
            </div>
            <div className="modal-actions">
              <button
                type="button"
                className="ghost-btn"
                onClick={handleCloseModal}
                disabled={assignLoading}
              >
                Cancel
              </button>
              <button
                type="button"
                className="primary-btn"
                onClick={confirmAssign}
                disabled={assignLoading}
              >
                {assignLoading ? "Assigning..." : "Confirm"}
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}

export default RecommendationsPage;
