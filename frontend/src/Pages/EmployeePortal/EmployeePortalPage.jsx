import { useEffect, useMemo, useState } from 'react';

import Menu from '../Menu';
import '../../styles/EmployeePortal.css';
import { apiFetch } from '../../api';
import { formatSkillLabel } from '../../lib/formatters';
import { navigateTo, redirectToLogin } from '../../lib/navigation';
import { getSessionItem } from '../../session';
import GrowthTab from './GrowthTab';
import ProfileTab from './ProfileTab';
import WorkTab from './WorkTab';

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

  useEffect(() => {
    const storedUser = getSessionItem('user_id');
    if (!storedUser) {
      redirectToLogin();
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
          data.preferences?.growth_text || data.preferences?.preferences_text || data.preferences_text || ''
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
        index.set(`${type}::${label.toLowerCase()}`, item.years_experience);
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
        const existing = existingSkillIndex.get(
          `${item.skill_type}::${String(item.skill_name || '').trim().toLowerCase()}`
        );
        if (existing == null) return null;
        return { name: item.skill_name, type: item.skill_type, from: existing, to: item.years_experience };
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
        body: JSON.stringify({ user_id: Number(userId), ...reasonForm }),
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
          <div className="employee-hero__copy">
            <p className="eyebrow">Employee Portal</p>
            <h1>{profile?.name || 'Your Profile'}</h1>
            <p className="sub">
              {profile?.role ? `${profile.role} · ${profile.department || 'Department'}` : 'Manage your profile, growth, and work in one place'}
            </p>
            <div className="employee-summary">
              <div className="summary-pill"><strong>{approvedSkillCount}</strong><span>approved skills</span></div>
              <div className="summary-pill"><strong>{pendingSkillRequests.length}</strong><span>pending approvals</span></div>
              <div className="summary-pill"><strong>{currentAssignments.length}</strong><span>active assignments</span></div>
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
              <button type="button" className={`employee-tab ${activeTab === 'profile' ? 'active' : ''}`} onClick={() => setActiveTab('profile')}>Skills</button>
              <button type="button" className={`employee-tab ${activeTab === 'growth' ? 'active' : ''}`} onClick={() => setActiveTab('growth')}>Growth</button>
              <button type="button" className={`employee-tab ${activeTab === 'work' ? 'active' : ''}`} onClick={() => setActiveTab('work')}>My Work</button>
            </div>

            {activeTab === 'profile' && (
              <ProfileTab
                technicalSkills={technicalSkills}
                softSkills={softSkills}
                pendingSkillRequests={pendingSkillRequests}
                pendingDelete={pendingDelete}
                deleteStatus={deleteStatus}
                skillWarning={skillWarning}
                selfSkills={selfSkills}
                setSelfSkills={setSelfSkills}
                skillStatus={skillStatus}
                capSkill={formatSkillLabel}
                onRequestDelete={setPendingDelete}
                onCancelDelete={() => setPendingDelete(null)}
                onDeleteSkill={handleDeleteSkill}
                onCancelSkillUpdate={() => {
                  setSkillWarning(null);
                  setPendingSkills(null);
                }}
                onConfirmSkillUpdate={confirmSkillUpdate}
                onUpdateSkill={updateSkill}
                onSubmitSkills={submitSkills}
              />
            )}

            {activeTab === 'growth' && (
              <GrowthTab
                growthText={growthText}
                savedGrowthText={savedGrowthText}
                growthStatus={growthStatus}
                onGrowthChange={setGrowthText}
                onInsertPrompt={(prompt) => setGrowthText((prev) => (prev ? `${prev.trim()}\n${prompt}` : prompt))}
                onSubmitGrowth={submitGrowth}
                onLoadSaved={() => setGrowthText(savedGrowthText || '')}
                onClearSaved={handleDeleteGrowth}
              />
            )}

            {activeTab === 'work' && (
              <WorkTab
                currentAssignments={currentAssignments}
                pastAssignments={pastAssignments}
                assignmentHistory={assignmentHistory}
                showReasonPreview={showReasonPreview}
                reasonForm={reasonForm}
                reasonStatus={reasonStatus}
                reasonResult={reasonResult}
                onToggleReasonPreview={() => setShowReasonPreview((prev) => !prev)}
                onReasonFormChange={(field, value) => setReasonForm((prev) => ({ ...prev, [field]: value }))}
                onSubmitReasonCheck={submitReasonCheck}
                onOpenCalendar={() => navigateTo('/employee-calendar')}
              />
            )}
          </>
        )}
      </div>
    </>
  );
}

export default EmployeePortalPage;
