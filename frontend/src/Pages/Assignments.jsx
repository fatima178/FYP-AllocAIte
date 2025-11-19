import React, { useState } from "react";
import Menu from "./Menu";
import "../styles/Assignments.css";

function AssignmentsPage() {
  const [taskDescription, setTaskDescription] = useState("");
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const generateRecommendations = async () => {
    setLoading(true);
    setError("");

    try {
      const res = await fetch("http://localhost:8001/api/recommend", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          task_description: taskDescription,
          start_date: startDate,
          end_date: endDate
        })
      });

      if (!res.ok) throw new Error("Recommendation request failed");

      const data = await res.json();
      localStorage.setItem("recommendations", JSON.stringify(data));

      window.location.href = "/recommendations";

    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      <Menu />

      <div className="assignments-container">
        <h2 className="page-title">Generate Recommendations</h2>

        <div className="form-box">
          <label>Task Description</label>
          <textarea
            placeholder="Describe the task in detail..."
            value={taskDescription}
            onChange={(e) => setTaskDescription(e.target.value)}
          />

          <label>Start Date</label>
          <input
            type="date"
            value={startDate}
            onChange={(e) => setStartDate(e.target.value)}
          />

          <label>End Date</label>
          <input
            type="date"
            value={endDate}
            onChange={(e) => setEndDate(e.target.value)}
          />

          <button
            type="button"
            disabled={loading}
            onClick={generateRecommendations}
          >
            {loading ? "Loading..." : "Generate Recommendations"}
          </button>

          {error && <p className="error">{error}</p>}
        </div>
      </div>
    </>
  );
}

export default AssignmentsPage;
