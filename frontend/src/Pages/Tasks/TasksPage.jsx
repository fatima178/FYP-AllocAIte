import React, { useCallback, useEffect, useMemo, useState } from 'react';

import Menu from '../Menu';
import '../../styles/Tasks.css';
import { apiFetch } from '../../api';
import { getSessionItem } from '../../session';
import CompletedTasksPanel from './CompletedTasksPanel';
import FeedbackModal from './FeedbackModal';
import TaskFormModal from './TaskFormModal';
import TasksCalendar from './TasksCalendar';
import {
  addDays,
  defaultEmployeeOptions,
  formatDateInput,
  formatDayLabel,
  initialWeekStart,
} from './utils';

function TasksPage() {
  const userId = getSessionItem('user_id');
  const [weekStart, setWeekStart] = useState(initialWeekStart);
  const [weekData, setWeekData] = useState({
    employees: [],
    unassigned: [],
    employee_options: defaultEmployeeOptions,
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [viewWeeks, setViewWeeks] = useState(1);
  const [peopleSearch, setPeopleSearch] = useState('');
  const [showModal, setShowModal] = useState(false);
  const [editModalOpen, setEditModalOpen] = useState(false);
  const [formData, setFormData] = useState({
    title: '',
    startDate: formatDateInput(initialWeekStart),
    endDate: formatDateInput(initialWeekStart),
    employeeId: '',
  });
  const [editForm, setEditForm] = useState({
    title: '',
    startDate: formatDateInput(initialWeekStart),
    endDate: formatDateInput(initialWeekStart),
    employeeId: '',
  });
  const [editTaskId, setEditTaskId] = useState(null);
  const [editError, setEditError] = useState('');
  const [updating, setUpdating] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [formError, setFormError] = useState('');
  const [saving, setSaving] = useState(false);
  const [completedTasks, setCompletedTasks] = useState([]);
  const [completedLoading, setCompletedLoading] = useState(false);
  const [completedError, setCompletedError] = useState('');
  const [feedbackOpen, setFeedbackOpen] = useState(false);
  const [feedbackTarget, setFeedbackTarget] = useState(null);
  const [feedbackRating, setFeedbackRating] = useState('');
  const [feedbackNotes, setFeedbackNotes] = useState('');
  const [feedbackOutcomeTags, setFeedbackOutcomeTags] = useState([]);
  const [feedbackSubmitting, setFeedbackSubmitting] = useState(false);
  const [feedbackPanelOpen, setFeedbackPanelOpen] = useState(false);

  const viewDays = useMemo(() => viewWeeks * 7, [viewWeeks]);
  const weekEnd = useMemo(() => addDays(weekStart, viewDays - 1), [weekStart, viewDays]);
  const weekDays = useMemo(
    () => Array.from({ length: viewDays }).map((_, index) => {
      const date = addDays(weekStart, index);
      return { date, label: formatDayLabel(date) };
    }),
    [weekStart, viewDays]
  );

  const rows = useMemo(() => {
    const employeeRows = (weekData.employees || []).map((emp) => ({
      id: emp.employee_id,
      name: emp.name,
      tasks: emp.tasks || [],
    }));
    return [{ id: 'unassigned', name: 'Unassigned', tasks: weekData.unassigned || [] }, ...employeeRows];
  }, [weekData]);

  const filteredRows = useMemo(() => {
    const term = peopleSearch.trim().toLowerCase();
    if (!term) return rows;
    return rows.filter((row) => row.name.toLowerCase().includes(term));
  }, [rows, peopleSearch]);

  const hasAnyTasks = filteredRows.some((row) => row.tasks.length > 0);
  const hasEmployees = (weekData.employee_options || []).length > 1;

  const fetchWeekData = useCallback(async () => {
    if (!userId) {
      setLoading(false);
      setError('No user session found.');
      return;
    }
    setLoading(true);
    setError('');
    try {
      const payload = await apiFetch(`/tasks/week?user_id=${userId}&week_start=${formatDateInput(weekStart)}&weeks=${viewWeeks}`);
      setWeekData({
        employees: payload.employees || [],
        unassigned: payload.unassigned || [],
        employee_options: payload.employee_options?.length ? payload.employee_options : defaultEmployeeOptions,
      });
    } catch (err) {
      setError(err.message || 'Unable to load tasks.');
      setWeekData({ employees: [], unassigned: [], employee_options: defaultEmployeeOptions });
    } finally {
      setLoading(false);
    }
  }, [userId, weekStart, viewWeeks]);

  const fetchCompletedTasks = useCallback(async () => {
    if (!userId) return;
    setCompletedLoading(true);
    setCompletedError('');
    try {
      const payload = await apiFetch(`/tasks/completed?user_id=${userId}&limit=20`);
      setCompletedTasks(Array.isArray(payload.completed) ? payload.completed : []);
    } catch (err) {
      setCompletedError(err.message || 'Unable to load completed tasks.');
      setCompletedTasks([]);
    } finally {
      setCompletedLoading(false);
    }
  }, [userId]);

  useEffect(() => { fetchWeekData(); }, [fetchWeekData]);
  useEffect(() => { fetchCompletedTasks(); }, [fetchCompletedTasks]);

  const changeWeek = (pageOffset) => setWeekStart((prev) => addDays(prev, pageOffset * viewDays));
  const openModal = () => {
    setFormData({
      title: '',
      startDate: formatDateInput(weekStart),
      endDate: formatDateInput(weekStart),
      employeeId: '',
    });
    setFormError('');
    setShowModal(true);
  };
  const closeModal = () => {
    if (saving) return;
    setShowModal(false);
    setFormError('');
  };
  const openFeedbackModal = (task) => {
    setFeedbackTarget(task);
    setFeedbackRating(task?.performance_rating || '');
    setFeedbackNotes(task?.feedback_notes || '');
    setFeedbackOutcomeTags(Array.isArray(task?.outcome_tags) ? task.outcome_tags : []);
    setFeedbackPanelOpen(false);
    setFeedbackOpen(true);
  };

  const submitFeedback = async () => {
    if (!feedbackTarget || !feedbackTarget.task_id) return;
    if (!feedbackRating) {
      setCompletedError('Please select a performance rating.');
      return;
    }
    setFeedbackSubmitting(true);
    setCompletedError('');
    try {
      await apiFetch('/recommend/feedback', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_id: Number(userId),
          task_id: Number(feedbackTarget.task_id),
          employee_id: Number(feedbackTarget.employee_id),
          performance_rating: feedbackRating,
          feedback_notes: feedbackNotes.trim() || null,
          outcome_tags: feedbackOutcomeTags,
        }),
      });
      setFeedbackOpen(false);
      setFeedbackTarget(null);
      await fetchCompletedTasks();
    } catch (err) {
      setCompletedError(err.message || 'Unable to submit feedback.');
    } finally {
      setFeedbackSubmitting(false);
    }
  };

  const clearFeedback = async () => {
    if (!feedbackTarget?.task_id || !feedbackTarget?.employee_id || feedbackSubmitting) return;
    setFeedbackSubmitting(true);
    setCompletedError('');
    try {
      await apiFetch(
        `/recommend/feedback?user_id=${Number(userId)}&task_id=${Number(feedbackTarget.task_id)}&employee_id=${Number(feedbackTarget.employee_id)}`,
        { method: 'DELETE' }
      );
      setFeedbackRating('');
      setFeedbackNotes('');
      setFeedbackOutcomeTags([]);
      setFeedbackOpen(false);
      setFeedbackTarget(null);
      await fetchCompletedTasks();
    } catch (err) {
      setCompletedError(err.message || 'Unable to clear feedback.');
    } finally {
      setFeedbackSubmitting(false);
    }
  };

  const openEditModal = (task) => {
    setEditTaskId(task.assignment_id);
    setEditForm({
      title: task.title || '',
      startDate: task.start_date,
      endDate: task.end_date,
      employeeId: task.employee_id ? String(task.employee_id) : '',
    });
    setEditError('');
    setEditModalOpen(true);
  };

  const closeEditModal = () => {
    if (updating || deleting) return;
    setEditModalOpen(false);
    setEditTaskId(null);
    setEditError('');
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    if (!userId) {
      setFormError('No user session found.');
      return;
    }
    setSaving(true);
    setFormError('');
    try {
      await apiFetch('/tasks', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_id: Number(userId),
          title: formData.title,
          start_date: formData.startDate,
          end_date: formData.endDate,
          employee_id: formData.employeeId ? Number(formData.employeeId) : null,
        }),
      });
      setShowModal(false);
      setFormData({
        title: '',
        startDate: formatDateInput(weekStart),
        endDate: formatDateInput(weekStart),
        employeeId: '',
      });
      fetchWeekData();
    } catch (err) {
      setFormError(err.message || 'Unable to save task.');
    } finally {
      setSaving(false);
    }
  };

  const handleUpdateTask = async (event) => {
    event.preventDefault();
    if (!userId || !editTaskId) return;
    setUpdating(true);
    setEditError('');
    try {
      await apiFetch(`/tasks/${editTaskId}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_id: Number(userId),
          title: editForm.title,
          start_date: editForm.startDate,
          end_date: editForm.endDate,
          employee_id: editForm.employeeId ? Number(editForm.employeeId) : null,
        }),
      });
      setEditModalOpen(false);
      setEditTaskId(null);
      fetchWeekData();
    } catch (err) {
      setEditError(err.message || 'Unable to update task.');
    } finally {
      setUpdating(false);
    }
  };

  const handleDeleteTask = async () => {
    if (!userId || !editTaskId) return;
    setDeleting(true);
    setEditError('');
    try {
      await apiFetch(`/tasks/${editTaskId}?user_id=${userId}`, { method: 'DELETE' });
      setEditModalOpen(false);
      setEditTaskId(null);
      fetchWeekData();
    } catch (err) {
      setEditError(err.message || 'Unable to delete task.');
    } finally {
      setDeleting(false);
    }
  };

  return (
    <>
      <Menu />
      <div className="tasks-page">
        <div className="tasks-header">
          <div>
            <h1>Task Management</h1>
            <p>manage and track all your team tasks</p>
          </div>
          <div className="tasks-header__actions">
            <button type="button" className="ghost-btn" onClick={() => setFeedbackPanelOpen(true)} disabled={!hasEmployees}>Feedback</button>
            <button type="button" className="primary-btn" onClick={openModal} disabled={!hasEmployees}>Add task</button>
          </div>
        </div>

        {!loading && !error && !hasEmployees ? (
          <div className="calendar-message empty">
            No employee data found. Upload your Excel file first before creating tasks or generating recommendations.
          </div>
        ) : (
          <>
            <div className="tasks-filters">
              <div className="filter-group">
                <label htmlFor="task-view">View</label>
                <select id="task-view" value={viewWeeks} onChange={(e) => setViewWeeks(Number(e.target.value))}>
                  <option value={1}>Weekly view</option>
                  <option value={2}>2 week view</option>
                  <option value={4}>4 week view</option>
                  <option value={6}>6 week view</option>
                </select>
              </div>

              <div className="filter-group filter-search">
                <label htmlFor="task-search">Search people</label>
                <input
                  id="task-search"
                  type="text"
                  placeholder="Search by name..."
                  value={peopleSearch}
                  onChange={(e) => setPeopleSearch(e.target.value)}
                />
              </div>
            </div>

            <TasksCalendar
              viewDays={viewDays}
              weekStart={weekStart}
              weekEnd={weekEnd}
              weekDays={weekDays}
              loading={loading}
              error={error}
              filteredRows={filteredRows}
              hasAnyTasks={hasAnyTasks}
              onChangeWeek={changeWeek}
              onEditTask={openEditModal}
            />
          </>
        )}
      </div>

      <TaskFormModal
        open={showModal}
        title="Add task"
        formData={formData}
        error={formError}
        saving={saving}
        submitLabel="Save task"
        weekData={weekData}
        onClose={closeModal}
        onChange={(field, value) => setFormData((prev) => ({ ...prev, [field]: value }))}
        onSubmit={handleSubmit}
      />

      <TaskFormModal
        open={editModalOpen}
        title="Edit task"
        formData={editForm}
        error={editError}
        saving={updating}
        submitLabel="Save changes"
        weekData={weekData}
        onClose={closeEditModal}
        onChange={(field, value) => setEditForm((prev) => ({ ...prev, [field]: value }))}
        onSubmit={handleUpdateTask}
        onDelete={handleDeleteTask}
        deleting={deleting}
      />

      <FeedbackModal
        open={feedbackOpen}
        feedbackTarget={feedbackTarget}
        feedbackRating={feedbackRating}
        feedbackNotes={feedbackNotes}
        feedbackOutcomeTags={feedbackOutcomeTags}
        feedbackSubmitting={feedbackSubmitting}
        onClose={() => setFeedbackOpen(false)}
        onRatingChange={setFeedbackRating}
        onNotesChange={setFeedbackNotes}
        onOutcomeTagsChange={setFeedbackOutcomeTags}
        onSubmit={submitFeedback}
        onClear={clearFeedback}
      />

      <CompletedTasksPanel
        open={feedbackPanelOpen}
        completedLoading={completedLoading}
        completedError={completedError}
        completedTasks={completedTasks}
        onClose={() => setFeedbackPanelOpen(false)}
        onOpenFeedback={openFeedbackModal}
      />
    </>
  );
}

export default TasksPage;
