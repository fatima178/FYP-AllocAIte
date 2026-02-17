import { useEffect, useMemo, useState } from 'react';
import Menu from './Menu';
import '../styles/EmployeePortal.css';
import { apiFetch } from '../api';

function EmployeePortalPage() {
  const [userId, setUserId] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [profile, setProfile] = useState(null);

  const [selfSkills, setSelfSkills] = useState([{ skill_name: '', years_experience: '' }]);
  const [learningGoals, setLearningGoals] = useState([{ skill_name: '', priority: 3, notes: '' }]);
  const [preferences, setPreferences] = useState({
    preferred_roles: '',
    preferred_departments: '',
    preferred_projects: '',
    work_style: '',
  });

  const [skillStatus, setSkillStatus] = useState(null);
  const [goalStatus, setGoalStatus] = useState(null);
  const [prefStatus, setPrefStatus] = useState(null);

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
        setSelfSkills(data.self_skills && data.self_skills.length > 0
          ? data.self_skills
          : [{ skill_name: '', years_experience: '' }]);
        setLearningGoals(data.learning_goals && data.learning_goals.length > 0
          ? data.learning_goals
          : [{ skill_name: '', priority: 3, notes: '' }]);
        setPreferences({
          preferred_roles: data.preferences?.preferred_roles || '',
          preferred_departments: data.preferences?.preferred_departments || '',
          preferred_projects: data.preferences?.preferred_projects || '',
          work_style: data.preferences?.work_style || '',
        });
      } catch (err) {
        setError(err.message || 'Unable to load your profile.');
      } finally {
        setLoading(false);
      }
    };

    fetchProfile();
  }, [userId]);

  const orgSkills = useMemo(() => profile?.org_skills || [], [profile]);
  const currentAssignments = useMemo(() => profile?.current_assignments || [], [profile]);
  const pastAssignments = useMemo(() => profile?.past_assignments || [], [profile]);
  const history = useMemo(() => profile?.history || [], [profile]);

  const updateSkill = (index, field, value) => {
    setSelfSkills((prev) => {
      const updated = [...prev];
      updated[index] = { ...updated[index], [field]: value };
      return updated;
    });
  };

  const updateGoal = (index, field, value) => {
    setLearningGoals((prev) => {
      const updated = [...prev];
      updated[index] = { ...updated[index], [field]: value };
      return updated;
    });
  };

  const submitSkills = async (event) => {
    event.preventDefault();
    setSkillStatus(null);

    if (!userId) return;

    const payload = selfSkills
      .filter((item) => String(item.skill_name || '').trim())
      .map((item) => ({
        skill_name: item.skill_name,
        years_experience: item.years_experience,
      }));

    try {
      await apiFetch('/employee/skills', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_id: Number(userId), skills: payload }),
      });
      setSkillStatus({ type: 'success', message: 'Skills updated.' });
    } catch (err) {
      setSkillStatus({ type: 'error', message: err.message || 'Unable to update skills.' });
    }
  };

  const submitGoals = async (event) => {
    event.preventDefault();
    setGoalStatus(null);

    if (!userId) return;

    const payload = learningGoals
      .filter((item) => String(item.skill_name || '').trim())
      .map((item) => ({
        skill_name: item.skill_name,
        priority: item.priority,
        notes: item.notes,
      }));

    try {
      await apiFetch('/employee/learning-goals', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_id: Number(userId), learning_goals: payload }),
      });
      setGoalStatus({ type: 'success', message: 'Learning goals updated.' });
    } catch (err) {
      setGoalStatus({ type: 'error', message: err.message || 'Unable to update goals.' });
    }
  };

  const submitPreferences = async (event) => {
    event.preventDefault();
    setPrefStatus(null);

    if (!userId) return;

    try {
      await apiFetch('/employee/preferences', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_id: Number(userId), preferences }),
      });
      setPrefStatus({ type: 'success', message: 'Preferences saved.' });
    } catch (err) {
      setPrefStatus({ type: 'error', message: err.message || 'Unable to save preferences.' });
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
            <section className="panel">
              <h2>Organization Skills</h2>
              <p className="muted">These were loaded by your manager.</p>
              <div className="tags">
                {orgSkills.length > 0 ? (
                  orgSkills.map((skill, index) => (
                    <span key={index} className="tag">
                      {skill.skill_name} ({skill.years_experience}y)
                    </span>
                  ))
                ) : (
                  <p className="empty">No skills uploaded yet.</p>
                )}
              </div>
            </section>

            <section className="panel">
              <h2>Your Current Skills</h2>
              <p className="muted">Add or update skills you want reflected in recommendations.</p>
              <form onSubmit={submitSkills}>
                {selfSkills.map((skill, index) => (
                  <div key={index} className="row">
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
                    onClick={() => setSelfSkills((prev) => [...prev, { skill_name: '', years_experience: '' }])}
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

            <section className="panel">
              <h2>Learning Goals</h2>
              <p className="muted">These help shape future recommendations as a secondary signal.</p>
              <form onSubmit={submitGoals}>
                {learningGoals.map((goal, index) => (
                  <div key={index} className="row">
                    <input
                      type="text"
                      placeholder="Skill to develop"
                      value={goal.skill_name}
                      onChange={(e) => updateGoal(index, 'skill_name', e.target.value)}
                    />
                    <input
                      type="number"
                      min="1"
                      max="5"
                      value={goal.priority}
                      onChange={(e) => updateGoal(index, 'priority', e.target.value)}
                    />
                    <input
                      type="text"
                      placeholder="Notes"
                      value={goal.notes || ''}
                      onChange={(e) => updateGoal(index, 'notes', e.target.value)}
                    />
                    {learningGoals.length > 1 && (
                      <button
                        type="button"
                        className="ghost"
                        onClick={() => setLearningGoals((prev) => prev.filter((_, i) => i !== index))}
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
                    onClick={() => setLearningGoals((prev) => [...prev, { skill_name: '', priority: 3, notes: '' }])}
                  >
                    Add goal
                  </button>
                  <button className="primary" type="submit">Save goals</button>
                </div>

                {goalStatus && (
                  <p className={`status ${goalStatus.type || ''}`}>{goalStatus.message}</p>
                )}
              </form>
            </section>

            <section className="panel">
              <h2>Preferences</h2>
              <p className="muted">Share the kinds of work you want to grow into.</p>
              <form onSubmit={submitPreferences} className="form-grid">
                <label>
                  Preferred Roles
                  <input
                    type="text"
                    value={preferences.preferred_roles}
                    onChange={(e) => setPreferences((prev) => ({ ...prev, preferred_roles: e.target.value }))}
                  />
                </label>
                <label>
                  Preferred Departments
                  <input
                    type="text"
                    value={preferences.preferred_departments}
                    onChange={(e) => setPreferences((prev) => ({ ...prev, preferred_departments: e.target.value }))}
                  />
                </label>
                <label>
                  Preferred Projects
                  <input
                    type="text"
                    value={preferences.preferred_projects}
                    onChange={(e) => setPreferences((prev) => ({ ...prev, preferred_projects: e.target.value }))}
                  />
                </label>
                <label>
                  Work Style
                  <input
                    type="text"
                    value={preferences.work_style}
                    onChange={(e) => setPreferences((prev) => ({ ...prev, work_style: e.target.value }))}
                  />
                </label>

                <div className="actions full">
                  <button className="primary" type="submit">Save preferences</button>
                </div>

                {prefStatus && (
                  <p className={`status ${prefStatus.type || ''}`}>{prefStatus.message}</p>
                )}
              </form>
            </section>

            <section className="panel">
              <h2>Current Assignments</h2>
              {currentAssignments.length > 0 ? (
                <ul className="list">
                  {currentAssignments.map((item, index) => (
                    <li key={`${item.assignment_id || index}`}>
                      <strong>{item.title}</strong>
                      <span>{item.start_date} → {item.end_date}</span>
                    </li>
                  ))}
                </ul>
              ) : (
                <p className="empty">No current assignments.</p>
              )}
            </section>

            <section className="panel">
              <h2>Past Assignments</h2>
              {pastAssignments.length > 0 ? (
                <ul className="list">
                  {pastAssignments.map((item, index) => (
                    <li key={`${item.assignment_id || index}`}>
                      <strong>{item.title}</strong>
                      <span>{item.start_date} → {item.end_date}</span>
                    </li>
                  ))}
                </ul>
              ) : (
                <p className="empty">No past assignments.</p>
              )}
            </section>

            <section className="panel">
              <h2>Archived History</h2>
              {history.length > 0 ? (
                <ul className="list">
                  {history.map((item, index) => (
                    <li key={`${item.title}-${index}`}>
                      <strong>{item.title}</strong>
                      <span>{item.start_date} → {item.end_date}</span>
                    </li>
                  ))}
                </ul>
              ) : (
                <p className="empty">No archived history yet.</p>
              )}
            </section>
          </div>
        )}
      </div>
    </>
  );
}

export default EmployeePortalPage;
