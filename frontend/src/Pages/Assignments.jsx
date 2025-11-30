import React, { useState } from "react";
import Menu from "./Menu";
import "../styles/Assignments.css";
import { apiFetch } from "../api";

function AssignmentsPage() {
  // stores what the user types as the task description
  const [taskDescription, setTaskDescription] = useState("");

  // stores the user selected start and end dates
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");

  // used to show a loading state while recommendations are being generated
  const [loading, setLoading] = useState(false);

  // holds validation errors or server-side errors
  const [error, setError] = useState("");

  // main function that sends the recommendation request to the backend
  const generateRecommendations = async () => {
    setLoading(true);  
    setError("");

    // get logged in user id from local storage
    const userId = localStorage.getItem("user_id");
    if (!userId) {
      setError("Please log in before requesting recommendations.");
      setLoading(false);
      return;
    }

    // validate that the task description has content
    if (!taskDescription.trim()) {
      setError("Task description is required.");
      setLoading(false);
      return;
    }

    // both dates must be selected
    if (!startDate || !endDate) {
      setError("Please provide both start and end dates.");
      setLoading(false);
      return;
    }

    try {
      // prepare request body for backend
      const payload = {
        task_description: taskDescription,
        start_date: startDate,
        end_date: endDate,
        user_id: Number(userId),
      };

      // add upload id if available
      const uploadId = localStorage.getItem("active_upload_id");
      if (uploadId) {
        payload.upload_id = Number(uploadId);
      }

      // fetch recommendations from backend
      const data = await apiFetch("/recommend", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      // store response so recommendation page can show results
      localStorage.setItem("recommendations", JSON.stringify(data));

      // store user context for next page
      localStorage.setItem(
        "recommendations_context",
        JSON.stringify({
          task_description: taskDescription.trim(),
          start_date: startDate,
          end_date: endDate,
        })
      );

      // navigate to recommendation results page
      window.location.href = "/recommendations";
    } catch (err) {
      // catch backend or network errors
      setError(err.message || "Recommendation request failed.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      {/* render top navigation menu */}
      <Menu />

      <div className="assignments-container">

        {/* page title */}
        <h2 className="page-title">Generate Recommendations</h2>

        <div className="form-box">

          {/* textarea for the task description */}
          <label>Task Description</label>
          <textarea
            placeholder="Describe the task in detail..."
            value={taskDescription}
            onChange={(e) => setTaskDescription(e.target.value)}
          />

          {/* start date selector */}
          <label>Start Date</label>
          <input
            type="date"
            value={startDate}
            onChange={(e) => setStartDate(e.target.value)}
          />

          {/* end date selector */}
          <label>End Date</label>
          <input
            type="date"
            value={endDate}
            onChange={(e) => setEndDate(e.target.value)}
          />

          {/* button to trigger recommendation generation */}
          <button
            type="button"
            disabled={loading}
            onClick={generateRecommendations}
          >
            {loading ? "Loading..." : "Generate Recommendations"}
          </button>

          {/* display any user or backend errors */}
          {error && <p className="error">{error}</p>}

        </div>
      </div>
    </>
  );
}

export default AssignmentsPage;
