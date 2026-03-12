import { useEffect, useMemo, useState } from 'react';
import Menu from './Menu';
import '../styles/EmployeePortal.css';
import { apiFetch } from '../api';

function EmployeePortalPage() {
  const [userId, setUserId] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [profile, setProfile] = useState(null);

  const [selfSkills, setSelfSkills] = useState([
    { skill_name: '', years_experience: '', skill_type: 'technical' },
  ]);
  const [growthText, setGrowthText] = useState('');
  const [savedGrowthText, setSavedGrowthText] = useState('');
  const [showSavedModal, setShowSavedModal] = useState(false);

  const [skillStatus, setSkillStatus] = useState(null);
  const [growthStatus, setGrowthStatus] = useState(null);
  const [reasonStatus, setReasonStatus] = useState(null);
  const [reasonResult, setReasonResult] = useState(null);
  const [skillWarning, setSkillWarning] = useState(null);
  const [pendingSkills, setPendingSkills] = useState(null);
  const [deleteStatus, setDeleteStatus] = useState(null);
  const capSkill = (value) => {
    const text = String(value || "");
    return text ? text.charAt(0).toUpperCase() + text.slice(1) : text;
  };
  const [pendingDelete, setPendingDelete] = useState(null);
  const [reasonForm, setReasonForm] = useState({
    task_description: '',
    start_date: '',
    end_date: '',
  });

  useEffect(() => {
    const storedUser = localStorage.getItem('user_id');
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
      setSkillStatus({ type: 'success', message: 'Skills updated.' });
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
      setSkillStatus({ type: 'success', message: 'Skills updated.' });
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

  return (
    <>
      <Menu />
      <div className="employee-portal">
        <header className="employee-hero">
          <div>
            <p className="eyebrow">Employee Portal</p>
            <h1>{profile?.name || 'Your Profile'}</h1>
            <p className="sub">
              {profile?.role ? `${profile.role} · ${profile.department || 'Department'}` : 'Manage your growth signals'}
            </p>
          </div>
          <div className="employee-chip">ID #{profile?.employee_id || '-'}</div>
        </header>

        {loading && <p className="status">Loading profile…</p>}
        {error && <p className="status error">{error}</p>}

        {!loading && !error && (
          <div className="employee-grid">
            <section className="panel panel-intro">
              <h2>Recorded Skills</h2>
              <p className="muted">Technical and soft skills recorded in your profile.</p>
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
                  <p className="tag-title">Soft Skills</p>
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
            </section>

            <section className="panel">
              <h2>Your Current Skills</h2>
              <p className="muted">Add or update skills you want reflected in recommendations.</p>
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
                    Add skill
                  </button>
                  <button className="primary" type="submit">Save skills</button>
                </div>

                {skillStatus && (
                  <p className={`status ${skillStatus.type || ''}`}>{skillStatus.message}</p>
                )}
              </form>
            </section>

            <section className="panel panel-wide">
              <h2>Preferences & Learning Goals</h2>
              <p className="muted">
                Describe the work you want, the skills you want to build, and any growth goals.
                This text is used for semantic matching.
              </p>
              <div className="actions">
                <button
                  type="button"
                  className="ghost"
                  onClick={() => setShowSavedModal(true)}
                >
                  View saved
                </button>
              </div>
              <form onSubmit={submitGrowth} className="form-grid">
                <label className="full">
                  Growth Notes
                  <textarea
                    rows="6"
                    placeholder="Examples: Interested in data engineering projects, want to grow in Python and ML, prefer cross-functional work..."
                    value={growthText}
                    onChange={(e) => setGrowthText(e.target.value)}
                  />
                </label>

                <div className="actions full">
                  <button className="primary" type="submit">Save</button>
                </div>

                {growthStatus && (
                  <p className={`status ${growthStatus.type || ''}`}>{growthStatus.message}</p>
                )}
              </form>
            </section>

            <section className="panel panel-wide">
              <h2>Recommendation Reason</h2>
              <p className="muted">Check why you might be recommended for a task.</p>
              <form onSubmit={submitReasonCheck} className="form-grid">
                <label>
                  Task Description
                  <input
                    type="text"
                    value={reasonForm.task_description}
                    onChange={(e) =>
                      setReasonForm((prev) => ({ ...prev, task_description: e.target.value }))
                    }
                  />
                </label>
                <label>
                  Start Date
                  <input
                    type="date"
                    value={reasonForm.start_date}
                    onChange={(e) =>
                      setReasonForm((prev) => ({ ...prev, start_date: e.target.value }))
                    }
                  />
                </label>
                <label>
                  End Date
                  <input
                    type="date"
                    value={reasonForm.end_date}
                    onChange={(e) =>
                      setReasonForm((prev) => ({ ...prev, end_date: e.target.value }))
                    }
                  />
                </label>

                <div className="actions full">
                  <button className="primary" type="submit">Check fit</button>
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
            </section>

          </div>
        )}
      </div>

      {showSavedModal && (
        <div className="employee-modal" onClick={() => setShowSavedModal(false)}>
          <div className="employee-modal__content" onClick={(event) => event.stopPropagation()}>
            <div className="employee-modal__header">
              <h3>Current Saved Notes</h3>
              <button type="button" onClick={() => setShowSavedModal(false)} aria-label="Close">
                ×
              </button>
            </div>
            {savedGrowthText ? (
              <p className="muted">{savedGrowthText}</p>
            ) : (
              <p className="empty">No preferences or learning goals saved yet.</p>
            )}
            <div className="employee-modal__actions">
              <button
                type="button"
                className="ghost"
                onClick={() => {
                  setGrowthText(savedGrowthText || '');
                  setShowSavedModal(false);
                }}
                disabled={!savedGrowthText}
              >
                Edit
              </button>
              <button
                type="button"
                className="ghost"
                onClick={() => {
                  handleDeleteGrowth();
                  setShowSavedModal(false);
                }}
                disabled={!savedGrowthText}
              >
                Delete
              </button>
              <button
                type="button"
                className="primary"
                onClick={() => setShowSavedModal(false)}
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}

export default EmployeePortalPage;
