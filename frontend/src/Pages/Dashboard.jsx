import { useEffect, useRef, useState } from 'react';
import Menu from './Menu';
import '../styles/Dashboard.css';
import { apiFetch } from '../api';
import { getSessionItem } from '../session';

function DashboardPage() {
  const accountType = getSessionItem('account_type') || 'manager';
  // holds the user_id of the logged-in user
  // this value is required for all dashboard API calls
  const [userId, setUserId] = useState(null);

  // text typed in the search bar
  // used to filter employees by name or job role
  const [searchTerm, setSearchTerm] = useState('');

  // list of all distinct skills in the dataset
  // used to populate the skill filter dropdown
  const [availableSkills, setAvailableSkills] = useState([]);

  // the currently selected skills to filter by
  const [selectedSkills, setSelectedSkills] = useState([]);
  const [skillSearch, setSkillSearch] = useState('');

  // current availability filter (available/partial/busy)
  const [availability, setAvailability] = useState('');

  // optional dashboard window for calculations (applied on button click)
  const [rangeStartInput, setRangeStartInput] = useState('');
  const [rangeEndInput, setRangeEndInput] = useState('');
  const [appliedRange, setAppliedRange] = useState({ start: '', end: '' });

  // summary stats like total employees, active projects, available employees
  const [data, setData] = useState(null);

  // list of employees returned by the backend after filters/search are applied
  const [employees, setEmployees] = useState([]);

  // dashboard-wide error message, e.g. backend offline
  const [error, setError] = useState(null);
  const [pendingSkillRequests, setPendingSkillRequests] = useState([]);
  const [pendingSkillLoading, setPendingSkillLoading] = useState(false);
  const [pendingSkillError, setPendingSkillError] = useState('');
  const [reviewingSkillId, setReviewingSkillId] = useState(null);

  const [skillsOpen, setSkillsOpen] = useState(false);
  const capSkill = (value) => {
    const text = String(value || "");
    return text ? text.charAt(0).toUpperCase() + text.slice(1) : text;
  };
  const [rangeOpen, setRangeOpen] = useState(false);
  const skillsRef = useRef(null);
  const rangeRef = useRef(null);

  // on mount, verify that a user is logged in
  // if not, instantly redirect them back to login page
  useEffect(() => {
    const storedUser = getSessionItem('user_id');
    if (!storedUser) {
      window.location.href = '/';
      return;
    }
    setUserId(storedUser);
  }, []);

  // close dropdowns on outside click
  useEffect(() => {
    const handleClick = (event) => {
      if (skillsRef.current && !skillsRef.current.contains(event.target)) {
        setSkillsOpen(false);
      }
      if (rangeRef.current && !rangeRef.current.contains(event.target)) {
        setRangeOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClick);
    return () => document.removeEventListener('mousedown', handleClick);
  }, []);

  // fetch the dashboard summary once a valid userId is loaded
  // this data powers the "Total Employees / Active Projects / Available This Week" cards
  useEffect(() => {
    if (!userId) return;

    const fetchSummary = async () => {
      try {
        const params = new URLSearchParams({ user_id: userId });
        if (appliedRange.start && appliedRange.end) {
          params.append('start_date', appliedRange.start);
          params.append('end_date', appliedRange.end);
        }
        const json = await apiFetch(`/dashboard/summary?${params.toString()}`);
        setData(json);
      } catch (err) {
        console.error('Error fetching dashboard data:', err);
        setError('Could not load dashboard data.');
      }
    };

    fetchSummary();
  }, [userId, appliedRange]);

  // fetch the employees list whenever:
  // - userId is available
  // - searchTerm changes
  // - selectedSkills changes
  // - availability filter changes
  // - applied date range changes
  // this ensures the UI updates immediately after the user interacts with filters
  useEffect(() => {
    if (!userId) return;

    const fetchEmployees = async () => {
      try {
        const params = new URLSearchParams({ user_id: userId });

        // include search filter if user typed anything
        if (searchTerm.trim()) params.append('search', searchTerm.trim());

        // include skill filter (multiple skills)
        selectedSkills.forEach((skill) => {
          params.append('skills', skill);
        });

        // include availability filter
        if (availability) params.append('availability', availability);

        // include optional dashboard window
        if (appliedRange.start && appliedRange.end) {
          params.append('start_date', appliedRange.start);
          params.append('end_date', appliedRange.end);
        }

        const json = await apiFetch(`/dashboard/employees?${params.toString()}`);
        setEmployees(json.employees || []);
      } catch (err) {
        console.error('Error fetching employees:', err);
      }
    };

    fetchEmployees();
  }, [userId, searchTerm, selectedSkills, availability, appliedRange]);

  // fetch all distinct skills from backend
  // so the user can filter employees by a specific skill
  useEffect(() => {
    if (!userId) return;

    const fetchSkills = async () => {
      try {
        const json = await apiFetch(`/dashboard/skills?user_id=${userId}`);
        setAvailableSkills(json.skills || []);
      } catch (err) {
        console.error('Error fetching skills:', err);
      }
    };

    fetchSkills();
  }, [userId]);

  useEffect(() => {
    if (!userId || accountType !== 'manager') return;

    const fetchPendingSkillRequests = async () => {
      setPendingSkillLoading(true);
      setPendingSkillError('');
      try {
        const payload = await apiFetch(`/employee/skills/pending?user_id=${userId}`);
        setPendingSkillRequests(
          Array.isArray(payload.pending_skill_requests) ? payload.pending_skill_requests : []
        );
      } catch (err) {
        setPendingSkillError(err.message || 'Unable to load skill requests.');
        setPendingSkillRequests([]);
      } finally {
        setPendingSkillLoading(false);
      }
    };

    fetchPendingSkillRequests();
  }, [userId, accountType]);

  // handler for multi-select skill selection
  const handleSkillChange = (event) => {
    const { value, checked } = event.target;
    setSelectedSkills((prev) => {
      if (checked) return [...prev, value];
      return prev.filter((s) => s !== value);
    });
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
      setAppliedRange({ start: '', end: '' });
    }
  };

  const clearDateRange = () => {
    setRangeStartInput('');
    setRangeEndInput('');
    setAppliedRange({ start: '', end: '' });
  };

  const reviewSkillRequest = async (requestId, approve) => {
    if (!userId || !requestId) return;
    setReviewingSkillId(requestId);
    setPendingSkillError('');
    try {
      await apiFetch('/employee/skills/review', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_id: Number(userId),
          request_id: Number(requestId),
          approve,
        }),
      });

      setPendingSkillRequests((prev) =>
        prev.filter((item) => item.request_id !== requestId)
      );
    } catch (err) {
      setPendingSkillError(err.message || 'Unable to review skill request.');
    } finally {
      setReviewingSkillId(null);
    }
  };

  const availabilityLabel = appliedRange.start && appliedRange.end
    ? `Availability (${appliedRange.start} → ${appliedRange.end})`
    : 'Weekly Availability';

  const summaryAvailabilityLabel = appliedRange.start && appliedRange.end
    ? 'Available in Range'
    : 'Available This Week';

  const summaryProjectsLabel = appliedRange.start && appliedRange.end
    ? 'Active Projects (Range)'
    : 'Active Projects';

  const selectedSkillsLabel = selectedSkills.length
    ? `${selectedSkills.length} skills selected`
    : 'Filter by skills';

  const selectedRangeLabel = appliedRange.start && appliedRange.end
    ? `${appliedRange.start} → ${appliedRange.end}`
    : 'Filter by date range';

  const filteredAvailableSkills = availableSkills.filter((skill) =>
    String(skill || "").toLowerCase().includes(skillSearch.trim().toLowerCase())
  );

  return (
    <>
      {/* top navigation bar */}
      <Menu />

      <div className="dashboard-container">
        {/* page title */}
        <h1>Team Overview</h1>

        {/* display error if summary request failed */}
        {error ? (
          <p className="error">{error}</p>
        ) : (
          data && (
            <>
              {/* summary cards show key numeric indicators */}
              <div className="dashboard-cards">
                <div className="card">
                  <h3>Total Employees</h3>
                  <p>{data.total_employees}</p>
                </div>

                <div className="card">
                  <h3>{summaryProjectsLabel}</h3>
                  <p>{data.active_projects}</p>
                </div>

                <div className="card">
                  <h3>{summaryAvailabilityLabel}</h3>
                  <p>{data.available_this_week}</p>
                </div>
              </div>

              {accountType === 'manager' && (pendingSkillLoading || pendingSkillError || pendingSkillRequests.length > 0) && (
                <div className="approval-panel">
                  <div className="approval-panel__header">
                    <div>
                      <h2>Skill Approval</h2>
                      <p>Review self reported employee skills before they affect recommendations.</p>
                    </div>
                  </div>

                  {pendingSkillLoading && (
                    <p className="approval-panel__message">Loading skill requests...</p>
                  )}
                  {pendingSkillError && (
                    <p className="approval-panel__message error">{pendingSkillError}</p>
                  )}

                  {!pendingSkillLoading && pendingSkillRequests.length > 0 && (
                    <div className="approval-list">
                      {pendingSkillRequests.map((item) => (
                        <div key={item.request_id} className="approval-card">
                          <div>
                            <strong>{capSkill(item.skill_name)}</strong>
                            <p>{item.employee_name} • {item.skill_type} • {item.years_experience} years</p>
                          </div>
                          <div className="approval-actions">
                            <button
                              type="button"
                              className="approval-btn secondary"
                              disabled={reviewingSkillId === item.request_id}
                              onClick={() => reviewSkillRequest(item.request_id, false)}
                            >
                              Reject
                            </button>
                            <button
                              type="button"
                              className="approval-btn primary"
                              disabled={reviewingSkillId === item.request_id}
                              onClick={() => reviewSkillRequest(item.request_id, true)}
                            >
                              {reviewingSkillId === item.request_id ? 'Saving...' : 'Approve'}
                            </button>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}

              {/* search bar and filters */}
              <div className="dashboard-filters">
                {/* text search for name or role */}
                <input
                  type="text"
                  placeholder="Search by name or role..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                />

                {/* filter employees by selected skill */}
                <div className="filter-dropdown" ref={skillsRef}>
                  <button
                    type="button"
                    className="filter-trigger"
                    onClick={() => setSkillsOpen((open) => !open)}
                    aria-expanded={skillsOpen}
                  >
                    {selectedSkillsLabel}
                  </button>
                  {skillsOpen && (
                    <div className="filter-panel" role="listbox" aria-label="Filter by skills">
                      <div className="filter-panel-header">Filter by skills</div>
                      <input
                        type="text"
                        className="skill-search-input"
                        placeholder="Search skills..."
                        value={skillSearch}
                        onChange={(e) => setSkillSearch(e.target.value)}
                      />
                      {availableSkills.length === 0 ? (
                        <div className="skills-empty">No skills available</div>
                      ) : filteredAvailableSkills.length === 0 ? (
                        <div className="skills-empty">No skills match your search</div>
                      ) : (
                        <div className="skills-filter-list">
                          {filteredAvailableSkills.map((skill) => (
                            <label key={skill} className="skill-option">
                              <input
                                type="checkbox"
                                value={skill}
                                checked={selectedSkills.includes(skill)}
                                onChange={handleSkillChange}
                              />
                              <span>{capSkill(skill)}</span>
                            </label>
                          ))}
                        </div>
                      )}
                    </div>
                  )}
                </div>

                {/* filter by weekly availability */}
                <select value={availability} onChange={(e) => setAvailability(e.target.value)}>
                  <option value="">Filter by availability</option>
                  <option value="available">Available</option>
                  <option value="partial">Partial</option>
                  <option value="busy">Busy</option>
                </select>

                <div className="filter-dropdown range-filter" ref={rangeRef}>
                  <button
                    type="button"
                    className="filter-trigger"
                    onClick={() => setRangeOpen((open) => !open)}
                    aria-expanded={rangeOpen}
                  >
                    {selectedRangeLabel}
                  </button>
                  {rangeOpen && (
                    <div className="filter-panel">
                      <div className="filter-panel-header">Availability date range</div>
                      <div className="availability-range">
                        <div className="date-field">
                          <label htmlFor="availability-start">Start date</label>
                          <input
                            id="availability-start"
                            type="date"
                            value={rangeStartInput}
                            onChange={(e) => setRangeStartInput(e.target.value)}
                          />
                        </div>

                        <div className="date-field">
                          <label htmlFor="availability-end">End date</label>
                          <input
                            id="availability-end"
                            type="date"
                            value={rangeEndInput}
                            onChange={(e) => setRangeEndInput(e.target.value)}
                          />
                        </div>

                        <button
                          type="button"
                          className="apply-range"
                          onClick={applyDateRange}
                          disabled={!rangeStartInput || !rangeEndInput}
                        >
                          Apply range
                        </button>

                        <button
                          type="button"
                          className="clear-range"
                          onClick={clearDateRange}
                          disabled={!rangeStartInput && !rangeEndInput && !appliedRange.start && !appliedRange.end}
                        >
                          Clear range
                        </button>
                      </div>
                    </div>
                  )}
                </div>
              </div>

              {selectedSkills.length > 0 && (
                <div className="selected-skills">
                  <span className="selected-label">Selected skills:</span>
                  <div className="selected-skill-list">
                    {selectedSkills.map((skill) => (
                      <button
                        key={skill}
                        type="button"
                        className="selected-skill"
                        onClick={() => removeSelectedSkill(skill)}
                        title="Remove skill"
                      >
                        {capSkill(skill)}
                        <span className="remove-x">×</span>
                      </button>
                    ))}
                  </div>
                </div>
              )}

              {/* employee cards render after all filters are applied */}
              {employees.length === 0 ? (
                <div className="empty-state">
                  <h3>No results</h3>
                  <p>Try adjusting your filters or date range.</p>
                </div>
              ) : (
                <div className="employee-grid">
                  {employees.map((emp) => (
                    <div key={emp.employee_id} className="employee-card">

                      {/* employee card header containing avatar, name, and role */}
                      <div className="employee-header">
                        <div className="avatar">
                          {(emp.initials || emp.name?.slice(0, 2) || '').toUpperCase()}
                        </div>

                        <div className="info">
                          <h3>{emp.name}</h3>
                          <p className="role">{emp.role}</p>
                        </div>

                        {/* availability badge, dynamically styled */}
                        <span className={`status ${emp.availability_status?.toLowerCase?.() || 'available'}`}>
                          {emp.availability_status}
                        </span>
                      </div>

                      {/* skill list */}
                    <div className="skills-section">
                      <h4>Skills</h4>

                      <div className="skills">
                        {emp.skills && emp.skills.length > 0 ? (
                          emp.skills.filter((skill) => !skill.derived).map((skill, i) => (
                            <span key={i} className="skill-tag">
                              {capSkill(skill.skill_name)} ({skill.years_experience}y)
                            </span>
                          ))
                        ) : (
                          <p className="no-skills">No skills listed</p>
                        )}
                      </div>
                    </div>

                    <div className="skills-section">
                      <h4>Soft Skills</h4>

                      <div className="skills">
                        {emp.soft_skills && emp.soft_skills.length > 0 ? (
                          emp.soft_skills.map((skill, i) => (
                            <span key={i} className="skill-tag">
                              {capSkill(skill.skill_name)} ({skill.years_experience}y)
                            </span>
                          ))
                        ) : (
                          <p className="no-skills">No soft skills listed</p>
                        )}
                      </div>
                    </div>

                      {/* active assignments section */}
                      <div className="active-assignments">
                        <h4>Active Assignments</h4>

                        {/* each assignment displayed as bullet list item */}
                        {emp.active_assignments && emp.active_assignments.length > 0 ? (
                          <ul>
                            {emp.active_assignments.map((a, i) => (
                              <li key={i}>
                                {a.title}
                              </li>
                            ))}
                          </ul>
                        ) : (
                          <p>No active assignments</p>
                        )}
                      </div>

                      {/* numeric percentage showing availability */}
                      <div className="availability">
                        <h4>{availabilityLabel}</h4>
                        <p className="availability-percent">
                          {typeof emp.availability_percent === 'number'
                            ? emp.availability_percent
                            : 0}
                          %
                        </p>
                      </div>

                    </div>
                  ))}
                </div>
              )}
            </>
          )
        )}
      </div>
    </>
  );
}

export default DashboardPage;
