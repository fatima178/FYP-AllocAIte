function SkillRows({ skills, setSkills }) {
  return (
    <div className="skill-rows">
      {skills.map((skill, index) => (
        <div key={index} className="form-grid skill-row">
          <label>
            Skill Type
            <select
              value={skill.skill_type || "technical"}
              onChange={(e) => {
                const updated = [...skills];
                updated[index] = { ...updated[index], skill_type: e.target.value };
                setSkills(updated);
              }}
            >
              <option value="technical">Technical</option>
              <option value="soft">Soft</option>
            </select>
          </label>

          <label>
            Skill Name
            <input
              type="text"
              value={skill.skill_name}
              onChange={(e) => {
                const updated = [...skills];
                updated[index] = { ...updated[index], skill_name: e.target.value };
                setSkills(updated);
              }}
              placeholder="Skill"
            />
          </label>

          <label>
            Skill Experience (Years)
            <input
              type="number"
              value={skill.years_experience}
              onChange={(e) => {
                const updated = [...skills];
                updated[index] = { ...updated[index], years_experience: e.target.value };
                setSkills(updated);
              }}
              placeholder="Years"
              min="0"
              step="0.1"
            />
          </label>

          {skills.length > 1 && (
            <label>
              &nbsp;
              <button
                type="button"
                className="ghost-btn"
                onClick={() => setSkills(skills.filter((_, i) => i !== index))}
              >
                Remove
              </button>
            </label>
          )}
        </div>
      ))}
    </div>
  );
}

export default function TeamSection(props) {
  const {
    employeeOptions,
    existingEmployeeId,
    setExistingEmployeeId,
    existingEmployeeSkills,
    setExistingEmployeeSkills,
    existingSkillStatus,
    existingSkillSaving,
    onSubmitExistingSkills,
    employeeForm,
    onEmployeeChange,
    employeeSkills,
    setEmployeeSkills,
    skillError,
    employeeStatus,
    employeeSaving,
    onSubmitEmployee,
    inviteForm,
    inviteStatus,
    inviteLink,
    inviteSaving,
    onInviteFormChange,
    onEmployeeSelect,
    onSubmitInvite,
  } = props;

  return (
    <>
      <div className="settings-card">
        <h2>Add Skills To Existing Employee</h2>
        <p className="muted">Select an existing employee and add or update their technical or soft skills.</p>

        <form className="settings-form" onSubmit={onSubmitExistingSkills}>
          <div className="form-grid">
            <label>
              Employee
              <select value={existingEmployeeId} onChange={(e) => setExistingEmployeeId(e.target.value)}>
                <option value="">Select employee</option>
                {employeeOptions.map((emp) => (
                  <option key={emp.employee_id} value={emp.employee_id}>
                    {emp.name} (ID {emp.employee_id})
                  </option>
                ))}
              </select>
            </label>

            <SkillRows skills={existingEmployeeSkills} setSkills={setExistingEmployeeSkills} />
          </div>

          <div className="button-row">
            <button
              type="button"
              onClick={() =>
                setExistingEmployeeSkills((prev) => [
                  ...prev,
                  { skill_name: "", years_experience: "", skill_type: "technical" },
                ])
              }
            >
              Add Skill
            </button>
          </div>

          {existingSkillStatus && (
            <p className={`status-message ${existingSkillStatus.type || ""}`}>
              {existingSkillStatus.message}
            </p>
          )}

          <div className="button-row">
            <button className="primary" type="submit" disabled={existingSkillSaving}>
              {existingSkillSaving ? "Saving..." : "Save Skills"}
            </button>
          </div>
        </form>
      </div>

      <div className="settings-card">
        <h2>Add Employee</h2>
        <p className="muted">Create employees directly in the system without Excel.</p>

        <form className="settings-form" onSubmit={onSubmitEmployee}>
          <div className="form-grid">
            <label>
              Name
              <input type="text" name="name" value={employeeForm.name} onChange={onEmployeeChange} placeholder="Name" />
            </label>
            <label>
              Role
              <input type="text" name="role" value={employeeForm.role} onChange={onEmployeeChange} placeholder="Role" />
            </label>
            <label>
              Department
              <input
                type="text"
                name="department"
                value={employeeForm.department}
                onChange={onEmployeeChange}
                placeholder="Department"
              />
            </label>

            <SkillRows skills={employeeSkills} setSkills={setEmployeeSkills} />
          </div>

          <div className="button-row">
            <button
              type="button"
              onClick={() =>
                setEmployeeSkills((prev) => [
                  ...prev,
                  { skill_name: "", years_experience: "", skill_type: "technical" },
                ])
              }
            >
              Add Skill
            </button>
          </div>

          {skillError && <p className="form-error">{skillError}</p>}

          <div className="button-row">
            <button className="primary" type="submit" disabled={employeeSaving}>
              {employeeSaving ? "Saving..." : "Add Employee"}
            </button>
          </div>

          {employeeStatus && (
            <p className={`status-message ${employeeStatus.type || ""}`}>
              {employeeStatus.message}
            </p>
          )}
        </form>
      </div>

      <div className="settings-card">
        <h2>Create Employee Invite</h2>
        <p className="muted">Generate a link for an employee to create their account.</p>

        <form className="settings-form" onSubmit={onSubmitInvite}>
          <div className="form-grid">
            <label>
              Employee
              <select name="employee_id" value={inviteForm.employee_id} onChange={onEmployeeSelect}>
                <option value="">Select employee</option>
                {employeeOptions.map((emp) => (
                  <option key={emp.employee_id} value={emp.employee_id}>
                    {emp.name} (ID {emp.employee_id})
                  </option>
                ))}
              </select>
            </label>

            <label>
              Name
              <input
                type="text"
                name="name"
                value={inviteForm.name}
                onChange={onInviteFormChange}
                placeholder="Employee name"
              />
            </label>
          </div>

          <div className="button-row">
            <button className="primary" type="submit" disabled={inviteSaving}>
              {inviteSaving ? "Generating..." : "Generate Invite Link"}
            </button>
          </div>

          {inviteStatus && (
            <p className={`status-message ${inviteStatus.type || ""}`}>
              {inviteStatus.message}
            </p>
          )}

          {inviteLink && (
            <div className="invite-link">
              <p className="muted">Copy and share this link:</p>
              <div className="copy-row">
                <input type="text" readOnly value={inviteLink} />
                <button type="button" onClick={() => navigator.clipboard.writeText(inviteLink)}>
                  Copy
                </button>
              </div>
            </div>
          )}
        </form>
      </div>
    </>
  );
}
