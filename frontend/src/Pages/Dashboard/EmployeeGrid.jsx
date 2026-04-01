import { formatSkillLabel } from "../../lib/formatters";

export default function EmployeeGrid({ employees, availabilityLabel }) {
  if (employees.length === 0) {
    return (
      <div className="empty-state">
        <h3>No results</h3>
        <p>Try adjusting your filters or date range.</p>
      </div>
    );
  }

  return (
    <div className="employee-grid">
      {employees.map((emp) => (
        <div key={emp.employee_id} className="employee-card">
          <div className="employee-header">
            <div className="avatar">
              {(emp.initials || emp.name?.slice(0, 2) || "").toUpperCase()}
            </div>
            <div className="info">
              <h3>{emp.name}</h3>
              <p className="role">{emp.role}</p>
            </div>
            <span className={`status ${emp.availability_status?.toLowerCase?.() || "available"}`}>
              {emp.availability_status}
            </span>
          </div>

          <div className="skills-section">
            <h4>Skills</h4>
            <div className="skills">
              {emp.skills && emp.skills.length > 0 ? (
                emp.skills.filter((skill) => !skill.derived).map((skill, i) => (
                  <span key={i} className="skill-tag">
                    {formatSkillLabel(skill.skill_name)} ({skill.years_experience}y)
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
                    {formatSkillLabel(skill.skill_name)} ({skill.years_experience}y)
                  </span>
                ))
              ) : (
                <p className="no-skills">No soft skills listed</p>
              )}
            </div>
          </div>

          <div className="active-assignments">
            <h4>Active Assignments</h4>
            {emp.active_assignments && emp.active_assignments.length > 0 ? (
              <ul>
                {emp.active_assignments.map((a, i) => (
                  <li key={i}>{a.title}</li>
                ))}
              </ul>
            ) : (
              <p>No active assignments</p>
            )}
          </div>

          <div className="availability">
            <h4>{availabilityLabel}</h4>
            <p className="availability-percent">
              {typeof emp.availability_percent === "number" ? emp.availability_percent : 0}%
            </p>
          </div>
        </div>
      ))}
    </div>
  );
}
