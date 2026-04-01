import React, { useMemo, useState } from "react";
import Menu from "../Menu";
import "../../styles/Recommendations.css";
import { apiFetch } from "../../api";
import { formatSkillLabel } from "../../lib/formatters";
import { navigateTo } from "../../lib/navigation";
import {
  loadRecommendationContext,
  loadRecommendations,
} from "../../lib/recommendationSession";
import { getSessionItem } from "../../session";

function RecommendationsPage() {
  const recommendations = useMemo(() => loadRecommendations(), []);
  const taskContext = useMemo(() => loadRecommendationContext(), []);

  const gapAnalysis = taskContext?.gap_analysis || null;

  // general status messages (error, success, info)
  const [status, setStatus] = useState({ type: null, message: "" });

  // modal / assignment state
  const [modalOpen, setModalOpen] = useState(false);
  const [selectedEmployee, setSelectedEmployee] = useState(null);

  // loading state during assignment API request
  const [assignLoading, setAssignLoading] = useState(false);

  // editable label shown in the modal before confirming assignment
  const [taskLabel, setTaskLabel] = useState("");

  // score display mode: absolute vs relative to top recommendation
  const [scoreMode, setScoreMode] = useState("absolute");
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
    const userId = getSessionItem("user_id");
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

    const userId = getSessionItem("user_id");
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
        task_id: taskContext.task_id ?? null,
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

        {gapAnalysis && (
          <div className={`gap-alert ${gapAnalysis.severity || "medium"}`}>
            <div className="gap-alert-header">
              <h3>Team Coverage Alert</h3>
              {typeof gapAnalysis.top_score === "number" && (
                <span className="gap-score">Top match {gapAnalysis.top_score}%</span>
              )}
            </div>
            <p>{gapAnalysis.message}</p>
            {Array.isArray(gapAnalysis.missing_skills) && gapAnalysis.missing_skills.length > 0 && (
              <p>
                <strong>Missing skills:</strong>{" "}
                {gapAnalysis.missing_skills.map(formatSkillLabel).join(", ")}
              </p>
            )}
            {Array.isArray(gapAnalysis.suggested_roles) && gapAnalysis.suggested_roles.length > 0 && (
              <p>
                <strong>Suggested hire profiles:</strong>{" "}
                {gapAnalysis.suggested_roles.join(", ")}
              </p>
            )}
          </div>
        )}

        <div className="recommendations-actions">
          <button
            type="button"
            className="ghost-btn"
            onClick={() => {
              navigateTo("/assignments");
            }}
          >
            New Recommendation
          </button>
        </div>

        <div className="score-toggle">
          <span>Score display:</span>
          <button
            type="button"
            className={scoreMode === "absolute" ? "primary" : ""}
            onClick={() => setScoreMode("absolute")}
          >
            Absolute
          </button>
          <button
            type="button"
            className={scoreMode === "relative" ? "primary" : ""}
            onClick={() => setScoreMode("relative")}
          >
            Relative to Top
          </button>
        </div>

        {/* list of recommendation cards */}
        <div className="recommendations-list">
          {recommendations.map((emp, index) => {
            // defensive parsing of backend values
            const scorePercent =
              typeof emp.score_percent === "number" ? emp.score_percent : 0;
            const maxScore = Math.max(
              1,
              ...recommendations.map((item) =>
                typeof item.score_percent === "number" ? item.score_percent : 0
              )
            );
            const relativeScorePercent = Math.round((scorePercent / maxScore) * 100);
            const displayScore =
              scoreMode === "relative" ? relativeScorePercent : scorePercent;

            const availabilityPercent =
              typeof emp.availability_percent === "number"
                ? emp.availability_percent
                : 0;

            const availabilityLabel = emp.availability_label || "Availability";

            const skills = Array.isArray(emp.skills) ? emp.skills : [];
            const softSkills = Array.isArray(emp.soft_skills) ? emp.soft_skills : [];
            const possibleSkills = Array.isArray(emp.possible_skills) ? emp.possible_skills : [];
            const possibleSoftSkills = Array.isArray(emp.possible_soft_skills)
              ? emp.possible_soft_skills
              : [];

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
                  <div className="score-circle">{displayScore}%</div>
                </div>

                {/* availability line */}
                <p>
                  <strong>Availability:</strong>{" "}
                  {availabilityLabel} ({availabilityPercent}%)
                </p>

                {/* skills summary */}
                <p>
                  <strong>Applicable Skills:</strong>{" "}
                  {skills.length > 0 ? skills.map(formatSkillLabel).join(", ") : "None matched"}
                </p>

                {skills.length === 0 && possibleSkills.length > 0 && (
                  <p>
                    <strong>Possible matches (low confidence):</strong>{" "}
                    {possibleSkills.map(formatSkillLabel).join(", ")}
                  </p>
                )}

                <p>
                  <strong>Soft Skills:</strong>{" "}
                  {softSkills.length > 0 ? softSkills.map(formatSkillLabel).join(", ") : "None matched"}
                </p>

                {softSkills.length === 0 && possibleSoftSkills.length > 0 && (
                  <p>
                    <strong>Possible soft skills (low confidence):</strong>{" "}
                    {possibleSoftSkills.map(formatSkillLabel).join(", ")}
                  </p>
                )}

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
