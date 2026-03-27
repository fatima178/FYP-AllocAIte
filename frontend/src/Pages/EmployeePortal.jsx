import { useEffect, useMemo, useState } from 'react';
import Menu from './Menu';
import '../styles/EmployeePortal.css';
import { apiFetch } from '../api';
import { getSessionItem } from '../session';

function EmployeePortalPage() {
  const [userId, setUserId] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [profile, setProfile] = useState(null);
  const [activeTab, setActiveTab] = useState('profile');

  const [selfSkills, setSelfSkills] = useState([
    { skill_name: '', years_experience: '', skill_type: 'technical' },
  ]);
  const [growthText, setGrowthText] = useState('');
  const [savedGrowthText, setSavedGrowthText] = useState('');

  const [skillStatus, setSkillStatus] = useState(null);
  const [growthStatus, setGrowthStatus] = useState(null);
  const [reasonStatus, setReasonStatus] = useState(null);
  const [reasonResult, setReasonResult] = useState(null);
  const [skillWarning, setSkillWarning] = useState(null);
  const [pendingSkills, setPendingSkills] = useState(null);
  const [deleteStatus, setDeleteStatus] = useState(null);
  const [pendingDelete, setPendingDelete] = useState(null);
  const [showReasonPreview, setShowReasonPreview] = useState(false);
  const [reasonForm, setReasonForm] = useState({
    task_description: '',
    start_date: '',
    end_date: '',
  });

  const capSkill = (value) => {
    const text = String(value || '');
    return text ? text.charAt(0).toUpperCase() + text.slice(1) : text;
  };

  useEffect(() => {
    const storedUser = getSessionItem('user_id');
    if (!storedUser) {
      window.location.href = '/';
      return;
    }
    setUserId(storedUser);
  }, []);

  useEffect(() => {
    if (!userId) return;

    const fetchProfile = async () => {
      setLoading(true);
      setError('');
      try {
        const data = await apiFetch(`/employee/profile?user_id=${userId}`);
        setProfile(data);
        setSelfSkills([{ skill_name: '', years_experience: '', skill_type: 'technical' }]);
        setGrowthText('');
        setSavedGrowthText(
          data.preferences?.growth_text
            || data.preferences?.preferences_text
            || data.preferences_text
            || ''
        );
      } catch (err) {
        setError(err.message || 'Unable to load your profile.');
      } finally {
        setLoading(false);
      }
    };

    fetchProfile();
  }, [userId]);

  const refreshProfile = async () => {
    if (!userId) return;
    try {
      const data = await apiFetch(`/employee/profile?user_id=${userId}`);
      setProfile(data);
    } catch (err) {
      setError(err.message || 'Unable to load your profile.');
    }
  };

  const technicalSkills = useMemo(() => profile?.technical_skills || [], [profile]);
  const softSkills = useMemo(() => profile?.soft_skills || [], [profile]);
  const pendingSkillRequests = useMemo(() => profile?.pending_skill_requests || [], [profile]);
  const currentAssignments = useMemo(() => profile?.current_assignments || [], [profile]);
  const pastAssignments = useMemo(() => profile?.past_assignments || [], [profile]);
  const assignmentHistory = useMemo(() => profile?.history || [], [profile]);
  const approvedSkillCount = technicalSkills.length + softSkills.length;

  const existingSkillIndex = useMemo(() => {
    const index = new Map();
    const add = (skills, type) => {
      skills.forEach((item) => {
        const label = String(item.skill_name || '').trim();
        if (!label) return;
        const key = `${type}::${label.toLowerCase()}`;
        index.set(key, item.years_experience);
      });
    };
    add(technicalSkills, 'technical');
    add(softSkills, 'soft');
    return index;
  }, [technicalSkills, softSkills]);

  const updateSkill = (index, field, value) => {
    setSelfSkills((prev) => {
      const updated = [...prev];
      updated[index] = { ...updated[index], [field]: value };
      return updated;
    });
  };

  const submitSkills = async (event) => {
    event.preventDefault();
    setSkillStatus(null);
    setSkillWarning(null);
    setPendingSkills(null);
    setDeleteStatus(null);
    setPendingDelete(null);

    if (!userId) return;

    const payload = selfSkills
      .filter((item) => String(item.skill_name || '').trim())
      .map((item) => ({
        skill_name: item.skill_name,
        years_experience: item.years_experience,
        skill_type: item.skill_type || 'technical',
      }));

    const duplicates = payload
      .map((item) => {
        const key = `${item.skill_type}::${String(item.skill_name || '').trim().toLowerCase()}`;
        const existing = existingSkillIndex.get(key);
        if (existing == null) return null;
        return {
          name: item.skill_name,
          type: item.skill_type,
          from: existing,
          to: item.years_experience,
        };
      })
      .filter(Boolean);

    if (duplicates.length > 0) {
      setSkillWarning({ duplicates });
      setPendingSkills(payload);
      return;
    }

    try {
      await apiFetch('/employee/skills', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_id: Number(userId), skills: payload }),
      });
      setSkillStatus({ type: 'success', message: 'Skills submitted for manager approval.' });
      setSelfSkills([{ skill_name: '', years_experience: '', skill_type: 'technical' }]);
      await refreshProfile();
    } catch (err) {
      setSkillStatus({ type: 'error', message: err.message || 'Unable to update skills.' });
    }
  };

  const confirmSkillUpdate = async () => {
    if (!pendingSkills || !userId) return;
    setSkillWarning(null);
    try {
      await apiFetch('/employee/skills', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_id: Number(userId), skills: pendingSkills }),
      });
      setSkillStatus({ type: 'success', message: 'Skills submitted for manager approval.' });
      setSelfSkills([{ skill_name: '', years_experience: '', skill_type: 'technical' }]);
      setPendingSkills(null);
      await refreshProfile();
    } catch (err) {
      setSkillStatus({ type: 'error', message: err.message || 'Unable to update skills.' });
    }
  };

  const cancelSkillUpdate = () => {
    setSkillWarning(null);
    setPendingSkills(null);
  };

  const handleDeleteSkill = async (skill) => {
    if (!userId) return;
    setDeleteStatus(null);
    setPendingDelete(null);
    try {
      const response = await apiFetch(
        `/employee/skills?user_id=${Number(userId)}&skill_name=${encodeURIComponent(skill.skill_name)}&skill_type=${encodeURIComponent(skill.skill_type)}`,
        { method: 'DELETE' }
      );
      if (response.deleted) {
        setDeleteStatus({ type: 'success', message: `${skill.skill_name} removed.` });
        await refreshProfile();
      } else {
        setDeleteStatus({ type: 'info', message: 'Skill not found.' });
      }
    } catch (err) {
      setDeleteStatus({ type: 'error', message: err.message || 'Unable to delete skill.' });
    }
  };

  const requestDeleteSkill = (skill) => {
    setDeleteStatus(null);
    setPendingDelete(skill);
  };

  const cancelDeleteSkill = () => {
    setPendingDelete(null);
  };

  const submitGrowth = async (event) => {
    event.preventDefault();
    setGrowthStatus(null);

    if (!userId) return;

    try {
      await apiFetch('/employee/preferences', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_id: Number(userId), preferences_text: growthText }),
      });
      setSavedGrowthText(growthText);
      setGrowthText('');
      setGrowthStatus({ type: 'success', message: 'Preferences and learning goals saved.' });
    } catch (err) {
      setGrowthStatus({ type: 'error', message: err.message || 'Unable to save details.' });
    }
  };

  const handleDeleteGrowth = async () => {
    setGrowthStatus(null);
    if (!userId) return;

    try {
      await apiFetch('/employee/preferences', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_id: Number(userId), preferences_text: '' }),
      });
      setGrowthText('');
      setSavedGrowthText('');
      setGrowthStatus({ type: 'success', message: 'Preferences and learning goals cleared.' });
    } catch (err) {
      setGrowthStatus({ type: 'error', message: err.message || 'Unable to clear details.' });
    }
  };

  const submitReasonCheck = async (event) => {
    event.preventDefault();
    setReasonStatus(null);
    setReasonResult(null);

    if (!userId) return;

    if (!reasonForm.task_description.trim()) {
      setReasonStatus({ type: 'error', message: 'Task description is required.' });
      return;
    }
    if (!reasonForm.start_date || !reasonForm.end_date) {
      setReasonStatus({ type: 'error', message: 'Start and end dates are required.' });
      return;
    }

    try {
      const data = await apiFetch('/employee/recommendation-reason', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_id: Number(userId),
          task_description: reasonForm.task_description,
          start_date: reasonForm.start_date,
          end_date: reasonForm.end_date,
        }),
      });
      if (data.message) {
        setReasonStatus({ type: 'info', message: data.message });
      } else {
        setReasonResult(data);
      }
    } catch (err) {
      setReasonStatus({ type: 'error', message: err.message || 'Unable to check recommendation.' });
    }
  };

  const insertGrowthPrompt = (prompt) => {
    setGrowthText((prev) => (prev ? `${prev.trim()}\n${prompt}` : prompt));
  };

  return (
    <>
      <Menu />
      <div className="employee-portal">
        <header className="employee-hero">
          <div className="employee-hero__copy">
            <p className="eyebrow">Employee Portal</p>
            <h1>{profile?.name || 'Your Profile'}</h1>
            <p className="sub">
              {profile?.role
                ? `${profile.role} · ${profile.department || 'Department'}`
                : 'Manage your profile, growth, and work in one place'}
            </p>
            <div className="employee-summary">
              <div className="summary-pill">
                <strong>{approvedSkillCount}</strong>
                <span>approved skills</span>
              </div>
              <div className="summary-pill">
                <strong>{pendingSkillRequests.length}</strong>
                <span>pending approvals</span>
              </div>
              <div className="summary-pill">
                <strong>{currentAssignments.length}</strong>
                <span>active assignments</span>
              </div>
            </div>
          </div>
          <div className="employee-hero__aside">
            <div className="employee-chip">ID #{profile?.employee_id || '-'}</div>
          </div>
        </header>

        {loading && <p className="status">Loading profile…</p>}
        {error && <p className="status error">{error}</p>}

        {!loading && !error && (
          <>
            <div className="employee-tabs" role="tablist" aria-label="Employee portal sections">
              <button
                type="button"
                className={`employee-tab ${activeTab === 'profile' ? 'active' : ''}`}
                onClick={() => setActiveTab('profile')}
              >
                Skills
              </button>
              <button
                type="button"
                className={`employee-tab ${activeTab === 'growth' ? 'active' : ''}`}
                onClick={() => setActiveTab('growth')}
              >
                Growth
              </button>
              <button
                type="button"
                className={`employee-tab ${activeTab === 'work' ? 'active' : ''}`}
                onClick={() => setActiveTab('work')}
              >
                My Work
              </button>
            </div>

            {activeTab === 'profile' && (
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
                        <div className="tag-group">
                          <p className="tag-title">Technical</p>
                          {technicalSkills.length > 0 ? (
                            technicalSkills.map((skill, index) => (
                              <span key={`tech-${index}`} className="tag">
                                {capSkill(skill.skill_name)} ({skill.years_experience}y)
                                <button
                                  type="button"
                                  className="tag-delete"
                                  onClick={() => requestDeleteSkill({ ...skill, skill_type: 'technical' })}
                                  aria-label={`Delete ${skill.skill_name}`}
                                >
                                  ×
                                </button>
                              </span>
                            ))
                          ) : (
                            <p className="empty">No technical skills uploaded yet.</p>
                          )}
                        </div>
                        <div className="tag-group">
                          <p className="tag-title">Soft skills</p>
                          {softSkills.length > 0 ? (
                            softSkills.map((skill, index) => (
                              <span key={`soft-${index}`} className="tag">
                                {capSkill(skill.skill_name)} ({skill.years_experience}y)
                                <button
                                  type="button"
                                  className="tag-delete"
                                  onClick={() => requestDeleteSkill({ ...skill, skill_type: 'soft' })}
                                  aria-label={`Delete ${skill.skill_name}`}
                                >
                                  ×
                                </button>
                              </span>
                            ))
                          ) : (
                            <p className="empty">No soft skills uploaded yet.</p>
                          )}
                        </div>
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
                        <button type="button" className="ghost" onClick={cancelDeleteSkill}>
                          Cancel
                        </button>
                        <button
                          type="button"
                          className="primary danger"
                          onClick={() => handleDeleteSkill(pendingDelete)}
                        >
                          Delete
                        </button>
                      </div>
                    </div>
                  )}

                  {deleteStatus && (
                    <p className={`status ${deleteStatus.type || ''}`}>{deleteStatus.message}</p>
                  )}

                  <div className="skill-entry-panel">
                    <div>
                      <p className="section-label">Add skill</p>
                      <h3>Submit something new</h3>
                      <p className="muted">
                        Add skills that are missing or update experience levels. Duplicate matches will be flagged before submission.
                      </p>
                    </div>

                    <form onSubmit={submitSkills}>
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
                            <button type="button" className="ghost" onClick={cancelSkillUpdate}>
                              Cancel
                            </button>
                            <button type="button" className="primary" onClick={confirmSkillUpdate}>
                              Update anyway
                            </button>
                          </div>
                        </div>
                      )}

                      {selfSkills.map((skill, index) => (
                        <div key={index} className="row">
                          <select
                            value={skill.skill_type}
                            onChange={(e) => updateSkill(index, 'skill_type', e.target.value)}
                          >
                            <option value="technical">Technical</option>
                            <option value="soft">Soft</option>
                          </select>
                          <input
                            type="text"
                            placeholder="Skill name"
                            value={skill.skill_name}
                            onChange={(e) => updateSkill(index, 'skill_name', e.target.value)}
                          />
                          <input
                            type="number"
                            placeholder="Years"
                            min="0"
                            step="0.1"
                            value={skill.years_experience}
                            onChange={(e) => updateSkill(index, 'years_experience', e.target.value)}
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

                      {skillStatus && (
                        <p className={`status ${skillStatus.type || ''}`}>{skillStatus.message}</p>
                      )}
                    </form>
                  </div>
                </section>
              </div>
            )}

            {activeTab === 'growth' && (
              <div className="employee-grid">
                <section className="panel panel-wide">
                  <p className="section-label">Growth</p>
                  <h2>Where you want to grow next</h2>
                  <p className="muted">
                    Give the system clearer signals about the work you enjoy, the skills you want to build, and the kinds of projects you want to move toward.
                  </p>

                  <div className="prompt-row">
                    <button type="button" className="prompt-chip" onClick={() => insertGrowthPrompt('I want to develop: ')}>
                      What skills do you want to develop?
                    </button>
                    <button type="button" className="prompt-chip" onClick={() => insertGrowthPrompt('I enjoy work that involves: ')}>
                      What type of work do you enjoy?
                    </button>
                    <button type="button" className="prompt-chip" onClick={() => insertGrowthPrompt('Projects I am interested in: ')}>
                      What projects interest you?
                    </button>
                  </div>

                  <div className="growth-layout">
                    <form onSubmit={submitGrowth} className="growth-form">
                      <label>
                        Growth goals
                        <textarea
                          className="growth-textarea"
                          rows="8"
                          placeholder={'What skills do you want to develop?\nWhat type of work do you enjoy?\nWhat projects interest you?'}
                          value={growthText}
                          onChange={(e) => setGrowthText(e.target.value)}
                        />
                      </label>

                      <div className="actions">
                        <button className="primary" type="submit">Save goals</button>
                        <button
                          type="button"
                          className="ghost"
                          onClick={() => setGrowthText(savedGrowthText || '')}
                          disabled={!savedGrowthText}
                        >
                          Load saved
                        </button>
                      </div>

                      {growthStatus && (
                        <p className={`status ${growthStatus.type || ''}`}>{growthStatus.message}</p>
                      )}
                    </form>

                    <aside className="saved-growth-card">
                      <p className="section-label">Saved direction</p>
                      <h3>Current profile signal</h3>
                      {savedGrowthText ? (
                        <p className="muted saved-growth-text">{savedGrowthText}</p>
                      ) : (
                        <p className="empty">No preferences or learning goals saved yet.</p>
                      )}
                      <div className="actions">
                        <button
                          type="button"
                          className="ghost"
                          onClick={() => setGrowthText(savedGrowthText || '')}
                          disabled={!savedGrowthText}
                        >
                          Edit saved text
                        </button>
                        <button
                          type="button"
                          className="ghost"
                          onClick={handleDeleteGrowth}
                          disabled={!savedGrowthText}
                        >
                          Clear saved
                        </button>
                      </div>
                    </aside>
                  </div>
                </section>
              </div>
            )}

            {activeTab === 'work' && (
              <div className="employee-grid">
                <section className="panel">
                  <p className="section-label">My work</p>
                  <h2>What you are doing now</h2>
                  <p className="muted">
                    Use this area to track active assignments and jump into your calendar when your availability changes.
                  </p>
                  <div className="detail-list">
                    <div className="detail-item">
                      <span>Active assignments</span>
                      <strong>{currentAssignments.length}</strong>
                    </div>
                    <div className="detail-item">
                      <span>Completed assignments</span>
                      <strong>{pastAssignments.length + assignmentHistory.length}</strong>
                    </div>
                  </div>
                </section>

                <section className="panel">
                  <p className="section-label">Availability</p>
                  <h2>Manage your calendar</h2>
                  <p className="muted">
                    Personal time off and assignment windows live in your calendar. Keep that page updated so workload decisions stay accurate.
                  </p>
                  <div className="actions">
                    <button
                      type="button"
                      className="primary"
                      onClick={() => { window.location.href = '/employee-calendar'; }}
                    >
                      Open my calendar
                    </button>
                  </div>
                </section>

                <section className="panel panel-wide">
                  <p className="section-label">Assignments</p>
                  <h2>Current assignments</h2>
                  {currentAssignments.length > 0 ? (
                    <div className="assignment-list">
                      {currentAssignments.map((assignment) => (
                        <article key={assignment.assignment_id} className="assignment-card">
                          <div>
                            <h3>{assignment.title}</h3>
                            <p className="muted">
                              {assignment.start_date} to {assignment.end_date}
                            </p>
                          </div>
                          <div className="assignment-meta">
                            <span>{assignment.total_hours ?? 0}h total</span>
                            <span>{assignment.remaining_hours ?? 0}h remaining</span>
                          </div>
                        </article>
                      ))}
                    </div>
                  ) : (
                    <p className="empty">No active assignments right now.</p>
                  )}
                </section>

                <section className="panel panel-wide">
                  <div className="advanced-header">
                    <div>
                      <p className="section-label">Advanced</p>
                      <h2>Preview how you match a task</h2>
                      <p className="muted">
                        This is optional and kept out of the main flow on purpose.
                      </p>
                    </div>
                    <button
                      type="button"
                      className="ghost"
                      onClick={() => setShowReasonPreview((prev) => !prev)}
                    >
                      {showReasonPreview ? 'Hide preview' : 'Show preview'}
                    </button>
                  </div>

                  {showReasonPreview && (
                    <form onSubmit={submitReasonCheck} className="form-grid">
                      <label>
                        Task description
                        <input
                          type="text"
                          value={reasonForm.task_description}
                          onChange={(e) =>
                            setReasonForm((prev) => ({ ...prev, task_description: e.target.value }))
                          }
                        />
                      </label>
                      <label>
                        Start date
                        <input
                          type="date"
                          value={reasonForm.start_date}
                          onChange={(e) =>
                            setReasonForm((prev) => ({ ...prev, start_date: e.target.value }))
                          }
                        />
                      </label>
                      <label>
                        End date
                        <input
                          type="date"
                          value={reasonForm.end_date}
                          onChange={(e) =>
                            setReasonForm((prev) => ({ ...prev, end_date: e.target.value }))
                          }
                        />
                      </label>

                      <div className="actions full">
                        <button className="primary" type="submit">Preview task match</button>
                      </div>

                      {reasonStatus && (
                        <p className={`status ${reasonStatus.type || ''}`}>{reasonStatus.message}</p>
                      )}

                      {reasonResult && (
                        <div className="reason-card">
                          <p><strong>Score:</strong> {reasonResult.score_percent}%</p>
                          <p><strong>Availability:</strong> {reasonResult.availability_percent}%</p>
                          <p><strong>Reason:</strong> {reasonResult.reason}</p>
                        </div>
                      )}
                    </form>
                  )}
                </section>
              </div>
            )}
          </>
        )}
      </div>
    </>
  );
}

export default EmployeePortalPage;
