import { useEffect, useState } from 'react';
import Menu from './Menu';
import '../styles/Dashboard.css';

function DashboardPage() {
  const [data, setData] = useState(null);
  const [employees, setEmployees] = useState([]);
  const [error, setError] = useState(null);

  // fetch summary
  useEffect(() => {
    const fetchSummary = async () => {
      try {
        const response = await fetch('http://127.0.0.1:8001/api/dashboard/summary');
        if (!response.ok) throw new Error('Server returned ' + response.status);
        const json = await response.json();
        setData(json);
      } catch (err) {
        console.error('Error fetching dashboard data:', err);
        setError('Could not load dashboard data.');
      }
    };
    fetchSummary();
  }, []);

  // fetch employees
  useEffect(() => {
    const fetchEmployees = async () => {
      try {
        const response = await fetch('http://127.0.0.1:8001/api/dashboard/employees');
        if (!response.ok) throw new Error('Server returned ' + response.status);
        const json = await response.json();
        setEmployees(json.employees || []);
      } catch (err) {
        console.error('Error fetching employees:', err);
      }
    };
    fetchEmployees();
  }, []);

  const getAvailabilityPercentage = (employee) => {
    if (typeof employee?.availability_percent === 'number') {
      return employee.availability_percent;
    }
    const status = employee?.availability_status?.toLowerCase?.() || '';
    if (status === 'available') return 100;
    if (status === 'partial') return 50;
    return 20;
  };

  return (
    <>
      <Menu />
      <div className="dashboard-container">
        <h1>Team Overview</h1>

        {error ? (
          <p className="error">{error}</p>
        ) : (
          data && (
            <>
              {/* SUMMARY CARDS */}
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

              {/* EMPLOYEE CARDS */}
              <div className="employee-grid">
                {employees.map((emp) => (
                  <div key={emp.employee_id} className="employee-card">
                    <div className="employee-header">
                      <div className="avatar">
                        {(emp.initials || emp.name?.slice(0, 2) || '').toUpperCase()}
                      </div>
                      <div className="info">
                        <h3>{emp.name}</h3>
                        <p className="role">{emp.role}</p>
                      </div>
                      <span className={`status ${emp.availability_status?.toLowerCase?.() || 'available'}`}>
                        {emp.availability_status}
                      </span>
                    </div>

                    {/* Skills */}
                    <div className="skills-section">
                    <h4>Skills</h4>
                    <div className="skills">
                        {emp.skills && emp.skills.length > 0 ? (
                        emp.skills.map((skill, i) => (
                            <span key={i} className="skill-tag">
                            {skill}
                            </span>
                        ))
                        ) : (
                        <p className="no-skills">No skills listed</p>
                        )}
                    </div>
                    </div>


                    <p className="experience">
                      Experience: {emp.experience_years} years
                    </p>

                    {/* Active Assignments */}
                    <div className="active-assignments">
                      <h4>Active Assignments</h4>
                      {emp.active_assignments && emp.active_assignments.length > 0 ? (
                        <ul>
                          {emp.active_assignments.map((a, i) => (
                            <li key={i}>
                              {a.title} ({a.priority})
                            </li>
                          ))}
                        </ul>
                      ) : (
                        <p>No active assignments</p>
                      )}
                    </div>

                    {/* Availability */}
                    <div className="availability">
                      <h4>Weekly Availability</h4>
                      <p className="availability-percent">
                        {getAvailabilityPercentage(emp)}%
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
