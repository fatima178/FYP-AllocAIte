import React, { useMemo, useState } from "react";
import Menu from "./Menu";
import "../styles/Recommendations.css";
import { apiFetch } from "../api";

function RecommendationsPage() {
  // load saved recommendations from localStorage (generated on previous page)
  // useMemo so it doesn't re-parse on every re-render
  const recommendations = useMemo(() => {
    const saved = localStorage.getItem("recommendations");
    if (!saved) return [];

    try {
      const parsed = JSON.parse(saved);
      return Array.isArray(parsed) ? parsed : [];
    } catch {
      // corrupted JSON -> return empty list
      return [];
    }
  }, []);

  // load the context: task description + start/end dates from the request that generated recs
  const taskContext = useMemo(() => {
    const saved = localStorage.getItem("recommendations_context");
    if (!saved) return null;

    try {
      const parsed = JSON.parse(saved);

      // validate the stored object structure
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

  // general status messages (error, success, info)
  const [status, setStatus] = useState({ type: null, message: "" });

  // modal / assignment state
  const [modalOpen, setModalOpen] = useState(false);
  const [selectedEmployee, setSelectedEmployee] = useState(null);

  // loading state during assignment API request
  const [assignLoading, setAssignLoading] = useState(false);

  // editable label shown in the modal before confirming assignment
  const [taskLabel, setTaskLabel] = useState("");

  // opens modal for assigning employee
  const openAssignModal = (emp) => {
    // recommendations depend on saved taskContext, so ensure we have it
    if (!taskContext) {
      setStatus({
        type: "error",
        message: "Missing task details. Please regenerate recommendations.",
      });
      return;
    }

    // require login to assign tasks
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

    // default pre-filled label is the original task description
    setTaskLabel(taskContext.task_description || "");
    setModalOpen(true);
  };

  // close modal safely
  const handleCloseModal = () => {
    if (assignLoading) return; // prevent closing mid-request
    setModalOpen(false);
    setSelectedEmployee(null);
    setTaskLabel("");
  };

  // send assignment request to backend
  const confirmAssign = async () => {
    if (!selectedEmployee || !taskContext) return;

    // meaningful label required
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

      // call backend API to create assignment
      const response = await apiFetch("/recommend/assign", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      setStatus({
        type: "success",
        message: response.message || "Task assigned successfully.",
      });

      // reset modal
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

  // if user visits this page with no stored recommendations
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

        {/* show messages above recommendation list */}
        {status.message && (
          <p className={`status-message ${status.type || ""}`}>
            {status.message}
          </p>
        )}

        {/* list of recommendation cards */}
        <div className="recommendations-list">
          {recommendations.map((emp, index) => {
            // defensive parsing of backend values
            const scorePercent =
              typeof emp.score_percent === "number" ? emp.score_percent : 0;

            const availabilityPercent =
              typeof emp.availability_percent === "number"
                ? emp.availability_percent
                : 0;

            const availabilityLabel = emp.availability_label || "Availability";

            const skills = Array.isArray(emp.skills) ? emp.skills : [];

            const reason =
              typeof emp.reason === "string" && emp.reason.trim().length > 0
                ? emp.reason
                : "Relevant profile for this task.";

            const reasonItems = reason
              .split(/(?<=[.!?])\s+/)
              .map((item) => item.trim())
              .filter(Boolean);

            return (
              <div
                key={emp.employee_id || index}
                className="rec-card"
              >
                {/* card header with name + score */}
                <div className="rec-header">
                  <div>
                    <h3>{emp.name || "Unknown employee"}</h3>
                    <p className="role">{emp.role || "Not specified"}</p>
                  </div>
                  <div className="score-circle">{scorePercent}%</div>
                </div>

                {/* availability line */}
                <p>
                  <strong>Availability:</strong>{" "}
                  {availabilityLabel} ({availabilityPercent}%)
                </p>

                {/* skills summary */}
                <p>
                  <strong>Applicable Skills:</strong>{" "}
                  {skills.length > 0 ? skills.join(", ") : "None matched"}
                </p>

                {/* explanation box from NLP engine */}
                <div className="reason-box">
                  <strong>Why this match:</strong>
                  <ul className="reason-list">
                    {reasonItems.map((item, idx) => (
                      <li key={idx}>{item}</li>
                    ))}
                  </ul>
                </div>

                {/* open modal to assign */}
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

      {/* assignment modal */}
      {modalOpen && selectedEmployee && (
        <div className="assign-modal-overlay">
          <div className="assign-modal">
            <h3>Confirm Assignment</h3>

            {/* employee being assigned */}
            <p>
              Are you sure you want to assign{" "}
              <strong>{selectedEmployee.name}</strong> to this task?
            </p>

            {/* user enters visible label for Tasks page */}
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

            {/* show original task description + dates underneath */}
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

            {/* modal actions: cancel + confirm */}
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
