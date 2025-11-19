import React from "react";
import Menu from "./Menu";
import "../styles/Recommendations.css";

function RecommendationsPage() {
  const saved = localStorage.getItem("recommendations");
  const recommendations = saved ? JSON.parse(saved) : [];

  if (!recommendations || recommendations.length === 0) {
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
          {recommendations.map((emp) => (
            <div key={emp.employee_id} className="rec-card">

              <div className="rec-header">
                <div>
                  <h3>{emp.name}</h3>
                  <p className="role">{emp.role}</p>
                </div>
                <div className="score-circle">
                  {Math.round(emp.score * 100)}%
                </div>
              </div>

              <p>
                <strong>Availability:</strong> 
                {" "}{emp.availability.status} ({emp.availability.percent}%)
              </p>

              <p>
                <strong>Matched Skills:</strong>{" "}
                {emp.matched_skills.length > 0
                  ? emp.matched_skills.join(", ")
                  : "None"}
              </p>

              <div className="reason-box">
                <strong>Reason:</strong>
                <p>{emp.reason}</p>
              </div>

            </div>
          ))}
        </div>
      </div>
    </>
  );
}

export default RecommendationsPage;
