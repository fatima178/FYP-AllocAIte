import { useEffect, useState } from 'react';
import Menu from './Menu';
import '../styles/Dashboard.css';
import { apiFetch } from '../api';

function DashboardPage() {
  // holds the user_id of the logged-in user
  // this value is required for all dashboard API calls
  const [userId, setUserId] = useState(null);

  // text typed in the search bar
  // used to filter employees by name or job role
  const [searchTerm, setSearchTerm] = useState('');

  // list of all distinct skills in the dataset
  // used to populate the skill filter dropdown
  const [availableSkills, setAvailableSkills] = useState([]);

  // the currently selected skill to filter by
  const [selectedSkill, setSelectedSkill] = useState('');

  // current availability filter (available/partial/busy)
  const [availability, setAvailability] = useState('');

  // summary stats like total employees, active projects, available employees
  const [data, setData] = useState(null);

  // list of employees returned by the backend after filters/search are applied
  const [employees, setEmployees] = useState([]);

  // dashboard-wide error message, e.g. backend offline
  const [error, setError] = useState(null);

  // on mount, verify that a user is logged in
  // if not, instantly redirect them back to login page
  useEffect(() => {
    const storedUser = localStorage.getItem('user_id');
    if (!storedUser) {
      window.location.href = '/';
      return;
    }
    setUserId(storedUser);
  }, []);

  // fetch the dashboard summary once a valid userId is loaded
  // this data powers the "Total Employees / Active Projects / Available This Week" cards
  useEffect(() => {
    if (!userId) return;

    const fetchSummary = async () => {
      try {
        const json = await apiFetch(`/dashboard/summary?user_id=${userId}`);
        setData(json);
      } catch (err) {
        console.error('Error fetching dashboard data:', err);
        setError('Could not load dashboard data.');
      }
    };

    fetchSummary();
  }, [userId]);

  // fetch the employees list whenever:
  // - userId is available
  // - searchTerm changes
  // - selectedSkill changes
  // - availability filter changes
  // this ensures the UI updates immediately after the user interacts with filters
  useEffect(() => {
    if (!userId) return;

    const fetchEmployees = async () => {
      try {
        const params = new URLSearchParams({ user_id: userId });

        // include search filter if user typed anything
        if (searchTerm.trim()) params.append('search', searchTerm.trim());

        // include skill filter (only one skill at a time)
        if (selectedSkill) params.append('skills', selectedSkill);

        // include availability filter
        if (availability) params.append('availability', availability);

        const json = await apiFetch(`/dashboard/employees?${params.toString()}`);
        setEmployees(json.employees || []);
      } catch (err) {
        console.error('Error fetching employees:', err);
      }
    };

    fetchEmployees();
  }, [userId, searchTerm, selectedSkill, availability]);

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

  // handler for dropdown skill selection
  const handleSkillChange = (event) => {
    setSelectedSkill(event.target.value);
  };

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
                  <h3>Active Projects</h3>
                  <p>{data.active_projects}</p>
                </div>

                <div className="card">
                  <h3>Available This Week</h3>
                  <p>{data.available_this_week}</p>
                </div>
              </div>

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
                <select value={selectedSkill} onChange={handleSkillChange}>
                  <option value="">Filter by skills</option>
                  {availableSkills.map((skill) => (
                    <option key={skill} value={skill}>
                      {skill}
                    </option>
                  ))}
                </select>

                {/* filter by weekly availability */}
                <select value={availability} onChange={(e) => setAvailability(e.target.value)}>
                  <option value="">Filter by availability</option>
                  <option value="available">Available</option>
                  <option value="partial">Partial</option>
                  <option value="busy">Busy</option>
                </select>
              </div>

              {/* employee cards render after all filters are applied */}
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
                          emp.skills.map((skill, i) => (
                            <span key={i} className="skill-tag">
                              {skill.skill_name} ({skill.years_experience}y)
                            </span>
                          ))
                        ) : (
                          <p className="no-skills">No skills listed</p>
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
                              {a.title}{a.priority ? ` (${a.priority})` : ''}
                            </li>
                          ))}
                        </ul>
                      ) : (
                        <p>No active assignments</p>
                      )}
                    </div>

                    {/* numeric percentage showing availability */}
                    <div className="availability">
                      <h4>Weekly Availability</h4>
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
            </>
          )
        )}
      </div>
    </>
  );
}

export default DashboardPage;
