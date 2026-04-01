import React, { useEffect, useState } from "react";
import Menu from "../Menu";
import "../../styles/Assignments.css";
import { apiFetch } from "../../api";
import { navigateTo } from "../../lib/navigation";
import { saveRecommendationSession } from "../../lib/recommendationSession";
import { getSessionItem } from "../../session";

const quickPrompts = [
  "Develop an internal dashboard that combines React, Python APIs, and reporting workflows.",
  "Create a machine learning prototype for predicting support ticket urgency using historical data.",
  "Design and launch an employee portal that works well on mobile with secure login and profile updates.",
];

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
  const [hasEmployees, setHasEmployees] = useState(true);

  const taskLength = taskDescription.trim().length;

  useEffect(() => {
    const userId = getSessionItem("user_id");
    if (!userId) return;

    const checkEmployees = async () => {
      try {
        const data = await apiFetch(`/dashboard/summary?user_id=${userId}`);
        setHasEmployees((data?.total_employees || 0) > 0);
      } catch {
        setHasEmployees(true);
      }
    };

    checkEmployees();
  }, []);

  // main function that sends the recommendation request to the backend
  const generateRecommendations = async () => {
    setLoading(true);  
    setError("");

    // get logged in user id from local storage
    const userId = getSessionItem("user_id");
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

    if (!hasEmployees) {
      setError("Upload your Excel file first before generating recommendations.");
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

      // fetch recommendations from backend
      const data = await apiFetch("/recommend", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      const recommendations = Array.isArray(data)
        ? data
        : Array.isArray(data?.recommendations)
          ? data.recommendations
          : [];

      // store response so recommendation page can show results
      saveRecommendationSession({
        recommendations,
        context: {
          task_description: taskDescription.trim(),
          start_date: startDate,
          end_date: endDate,
          task_id: data?.task_id ?? null,
          gap_analysis: data?.gap_analysis ?? null,
        },
      });

      // navigate to recommendation results page
      navigateTo("/recommendations");
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
        <section className="assignments-layout">
          <div className="form-box">
            <div className="form-box__header form-box__header--split">
              <div className="form-box__titleblock">
                <p className="form-box__eyebrow">Assignment setup</p>
                <h2 className="page-title">Generate Recommendations</h2>
                <p className="form-box__subtitle">
                  Describe the assignment and set the project window to get ranked employee matches.
                </p>
              </div>
              <div className="assignment-help">
                <button
                  type="button"
                  className="assignment-help__trigger"
                  aria-label="Show assignment help"
                >
                  Help
                </button>
                <div className="assignment-help__panel">
                  <div className="assignment-help__section">
                    <p className="assignments-sidecard__eyebrow">Quick starts</p>
                    <h3>Use a sample brief</h3>
                    <p>Tap one to preload the description box, then adjust it to fit your real assignment.</p>
                    <div className="assignments-prompt-list">
                      {quickPrompts.map((prompt) => (
                        <button
                          key={prompt}
                          type="button"
                          className="assignments-prompt"
                          onClick={() => setTaskDescription(prompt)}
                        >
                          {prompt}
                        </button>
                      ))}
                    </div>
                  </div>

                  <div className="assignment-help__section assignment-help__section--tips">
                    <h3>Brief writing tips</h3>
                    <ul>
                      <li>Include the product area or business context.</li>
                      <li>Mention technical skills and the type of deliverable.</li>
                      <li>Avoid vague descriptions like "help with project work".</li>
                    </ul>
                  </div>
                </div>
              </div>
            </div>

            <div className="form-box__statusbar">
              {!hasEmployees && (
                <p className="error">Upload your Excel file first before generating recommendations.</p>
              )}
              <div className="form-box__meter">
                <span>Brief detail</span>
                <strong>{taskLength === 0 ? "Empty" : taskLength < 80 ? "Light" : "Strong"}</strong>
              </div>
            </div>

            <div className="form-section">
              <div className="form-label-row">
                <label htmlFor="task-description">Task Description</label>
                <span>{taskLength} characters</span>
              </div>
              <textarea
                id="task-description"
                placeholder="Describe the assignment, expected outcome, skills needed and any delivery context..."
                value={taskDescription}
                onChange={(e) => setTaskDescription(e.target.value)}
              />
            </div>

            <div className="form-section form-section--dates">
              <div className="form-section__header">
                <h3>Schedule</h3>
                <p>Select the window for this assignment.</p>
              </div>

              <div className="form-date-grid">
                <div className="form-field form-field--date">
                  <label htmlFor="start-date">Start Date</label>
                  <input
                    id="start-date"
                    type="date"
                    value={startDate}
                    onChange={(e) => setStartDate(e.target.value)}
                  />
                </div>

                <div className="form-field form-field--date">
                  <label htmlFor="end-date">End Date</label>
                  <input
                    id="end-date"
                    type="date"
                    value={endDate}
                    onChange={(e) => setEndDate(e.target.value)}
                  />
                </div>
              </div>
            </div>

            <div className="form-footer">
              <button
                type="button"
                disabled={loading || !hasEmployees}
                onClick={generateRecommendations}
              >
                {loading ? "Generating..." : "Generate Recommendations"}
              </button>
            </div>

            {error && <p className="error">{error}</p>}
          </div>
        </section>
      </div>
    </>
  );
}

export default AssignmentsPage;
