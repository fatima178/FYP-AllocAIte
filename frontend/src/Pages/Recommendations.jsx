import React, { useMemo } from "react";
import Menu from "./Menu";
import "../styles/Recommendations.css";

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
              </div>
            );
          })}
        </div>
      </div>
    </>
  );
}

export default RecommendationsPage;
