function SkillTagGroup({ title, skills, skillType, onDelete, capSkill, emptyText }) {
  return (
    <div className="tag-group">
      <p className="tag-title">{title}</p>
      {skills.length > 0 ? (
        skills.map((skill, index) => (
          <span key={`${skillType}-${index}`} className="tag">
            {capSkill(skill.skill_name)} ({skill.years_experience}y)
            <button
              type="button"
              className="tag-delete"
              onClick={() => onDelete({ ...skill, skill_type: skillType })}
              aria-label={`Delete ${skill.skill_name}`}
            >
              ×
            </button>
          </span>
        ))
      ) : (
        <p className="empty">{emptyText}</p>
      )}
    </div>
  );
}

export default function ProfileTab(props) {
  const {
    technicalSkills,
    softSkills,
    pendingSkillRequests,
    pendingDelete,
    deleteStatus,
    skillWarning,
    selfSkills,
    setSelfSkills,
    skillStatus,
    capSkill,
    onRequestDelete,
    onCancelDelete,
    onDeleteSkill,
    onCancelSkillUpdate,
    onConfirmSkillUpdate,
    onUpdateSkill,
    onSubmitSkills,
  } = props;

  return (
    <div className="employee-grid">
      <section className="panel panel-wide">
        <p className="section-label">Skills</p>
        <h2>Approved and pending skill signals</h2>
        <p className="muted">
          Approved skills are used in recommendations. New skill submissions stay pending until your manager reviews them.
        </p>

        <div className="skill-columns">
          <div className="skill-column">
            <p className="tag-title">Approved</p>
            <div className="tags">
              <SkillTagGroup
                title="Technical"
                skills={technicalSkills}
                skillType="technical"
                onDelete={onRequestDelete}
                capSkill={capSkill}
                emptyText="No technical skills uploaded yet."
              />
              <SkillTagGroup
                title="Soft skills"
                skills={softSkills}
                skillType="soft"
                onDelete={onRequestDelete}
                capSkill={capSkill}
                emptyText="No soft skills uploaded yet."
              />
            </div>
          </div>

          <div className="skill-column skill-column--pending">
            <p className="tag-title">Pending approval</p>
            {pendingSkillRequests.length > 0 ? (
              <div className="tags">
                {pendingSkillRequests.map((skill) => (
                  <span key={skill.request_id} className="tag pending-tag">
                    {capSkill(skill.skill_name)} ({skill.years_experience}y, {skill.skill_type})
                  </span>
                ))}
              </div>
            ) : (
              <p className="empty">No pending skill requests.</p>
            )}
          </div>
        </div>

        {pendingDelete && (
          <div className="inline-warning">
            <div>
              <p className="warning-title">Delete skill?</p>
              <p className="warning-text">
                {pendingDelete.skill_name} ({pendingDelete.skill_type})
              </p>
            </div>
            <div className="warning-actions">
              <button type="button" className="ghost" onClick={onCancelDelete}>Cancel</button>
              <button type="button" className="primary danger" onClick={() => onDeleteSkill(pendingDelete)}>
                Delete
              </button>
            </div>
          </div>
        )}

        {deleteStatus && <p className={`status ${deleteStatus.type || ''}`}>{deleteStatus.message}</p>}

        <div className="skill-entry-panel">
          <div>
            <p className="section-label">Add skill</p>
            <h3>Submit something new</h3>
            <p className="muted">
              Add skills that are missing or update experience levels. Duplicate matches will be flagged before submission.
            </p>
          </div>

          <form onSubmit={onSubmitSkills}>
            {skillWarning && (
              <div className="inline-warning">
                <div>
                  <p className="warning-title">Skill already exists</p>
                  <ul className="warning-list">
                    {skillWarning.duplicates.map((dup, idx) => (
                      <li key={`${dup.name}-${idx}`}>
                        {dup.name} ({dup.type}) {dup.from ?? '?'}y → {dup.to}y
                      </li>
                    ))}
                  </ul>
                </div>
                <div className="warning-actions">
                  <button type="button" className="ghost" onClick={onCancelSkillUpdate}>Cancel</button>
                  <button type="button" className="primary" onClick={onConfirmSkillUpdate}>Update anyway</button>
                </div>
              </div>
            )}

            {selfSkills.map((skill, index) => (
              <div key={index} className="row">
                <select value={skill.skill_type} onChange={(e) => onUpdateSkill(index, 'skill_type', e.target.value)}>
                  <option value="technical">Technical</option>
                  <option value="soft">Soft</option>
                </select>
                <input
                  type="text"
                  placeholder="Skill name"
                  value={skill.skill_name}
                  onChange={(e) => onUpdateSkill(index, 'skill_name', e.target.value)}
                />
                <input
                  type="number"
                  placeholder="Years"
                  min="0"
                  step="0.1"
                  value={skill.years_experience}
                  onChange={(e) => onUpdateSkill(index, 'years_experience', e.target.value)}
                />
                {selfSkills.length > 1 && (
                  <button
                    type="button"
                    className="ghost"
                    onClick={() => setSelfSkills((prev) => prev.filter((_, i) => i !== index))}
                  >
                    Remove
                  </button>
                )}
              </div>
            ))}

            <div className="actions">
              <button
                type="button"
                className="ghost"
                onClick={() =>
                  setSelfSkills((prev) => [
                    ...prev,
                    { skill_name: '', years_experience: '', skill_type: 'technical' },
                  ])
                }
              >
                Add another
              </button>
              <button className="primary" type="submit">Submit for approval</button>
            </div>

            {skillStatus && <p className={`status ${skillStatus.type || ''}`}>{skillStatus.message}</p>}
          </form>
        </div>
      </section>
    </div>
  );
}
