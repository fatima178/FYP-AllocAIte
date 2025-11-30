import React, { useCallback, useEffect, useMemo, useState } from 'react';
import Menu from './Menu';
import '../styles/Tasks.css';
import { apiFetch } from '../api';

/* 
  Finds Monday of the week for any given date.
  Normalises calendar rendering so all weeks start consistently.
*/
const getWeekStart = (inputDate) => {
  const date = new Date(inputDate);
  const day = date.getDay();
  const diff = (day === 0 ? -6 : 1) - day;
  date.setDate(date.getDate() + diff);
  date.setHours(0, 0, 0, 0);
  return date;
};

// returns a new date offset by X days
const addDays = (date, days) => {
  const clone = new Date(date);
  clone.setDate(clone.getDate() + days);
  return clone;
};

// converts JS Date into yyyy-mm-dd (HTML "date" input format)
const formatDateInput = (date) => {
  const year = date.getFullYear();
  const month = `${date.getMonth() + 1}`.padStart(2, '0');
  const day = `${date.getDate()}`.padStart(2, '0');
  return `${year}-${month}-${day}`;
};

// label for the week range header
const formatRangeLabel = (date) =>
  date.toLocaleDateString(undefined, { month: 'short', day: 'numeric' });

// label for individual day columns
const formatDayLabel = (date) =>
  date.toLocaleDateString(undefined, { weekday: 'short', day: 'numeric' });

// default view is the current week
const initialWeekStart = getWeekStart(new Date());

// drop-down fallback if no employees available
const defaultEmployeeOptions = [{ employee_id: null, name: 'Unassigned' }];

/* 
  Constants that control the height/spacing of lanes inside the timeline grid
  Ensures consistent rendering regardless of number of tasks per employee.
*/
const TIMELINE_MIN_HEIGHT = 70;
const LANE_HEIGHT = 44;
const LANE_GAP = 8;
const LANE_BASE_OFFSET = 10;

function TasksPage() {
  const userId = localStorage.getItem('user_id');

  // starting Monday of currently selected week
  const [weekStart, setWeekStart] = useState(initialWeekStart);

  // data returned from backend (employees + tasks)
  const [weekData, setWeekData] = useState({
    employees: [],
    unassigned: [],
    employee_options: defaultEmployeeOptions,
  });

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  // modal for adding tasks
  const [showModal, setShowModal] = useState(false);

  // controlled form for "Add task"
  const [formData, setFormData] = useState({
    title: '',
    startDate: formatDateInput(initialWeekStart),
    endDate: formatDateInput(initialWeekStart),
    employeeId: '',
  });

  const [formError, setFormError] = useState('');
  const [saving, setSaving] = useState(false);

  // Monday + 6 = Sunday of that week
  const weekEnd = useMemo(() => addDays(weekStart, 6), [weekStart]);

  /* 
    Pre-computed array of all 7 days in the current week.
    Saves recalculating during rendering.
  */
  const weekDays = useMemo(() => {
    return Array.from({ length: 7 }).map((_, index) => {
      const date = addDays(weekStart, index);
      return {
        date,
        label: formatDayLabel(date),
      };
    });
  }, [weekStart]);

  /* 
    Flatten tasks into a row structure:
    - 1 row for unassigned tasks
    - 1 row per employee
  */
  const rows = useMemo(() => {
    const employeeRows = (weekData.employees || []).map((emp) => ({
      id: emp.employee_id,
      name: emp.name,
      tasks: emp.tasks || [],
    }));

    return [
      {
        id: 'unassigned',
        name: 'Unassigned',
        tasks: weekData.unassigned || [],
      },
      ...employeeRows,
    ];
  }, [weekData]);

  // used to decide if "No tasks scheduled this week" should appear
  const hasAnyTasks = rows.some((row) => row.tasks.length > 0);

  /* 
    Fetches all tasks for a given week.
    Triggered when:
      - weekStart changes
      - page loads
  */
  const fetchWeekData = useCallback(async () => {
    if (!userId) {
      setLoading(false);
      setError('No user session found.');
      return;
    }

    setLoading(true);
    setError('');

    try {
      const payload = await apiFetch(
        `/tasks/week?user_id=${userId}&week_start=${formatDateInput(weekStart)}`
      );

      setWeekData({
        employees: payload.employees || [],
        unassigned: payload.unassigned || [],
        employee_options:
          payload.employee_options && payload.employee_options.length > 0
            ? payload.employee_options
            : defaultEmployeeOptions,
      });
    } catch (err) {
      setError(err.message || 'Unable to load tasks.');
      setWeekData({
        employees: [],
        unassigned: [],
        employee_options: defaultEmployeeOptions,
      });
    } finally {
      setLoading(false);
    }
  }, [userId, weekStart]);

  // reload tasks whenever the selected week changes
  useEffect(() => {
    fetchWeekData();
  }, [fetchWeekData]);

  // allows moving forward/backward in increments of one week
  const changeWeek = (offset) => {
    setWeekStart((prev) => addDays(prev, offset));
  };

  // resets modal form and opens modal
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

  // closes the modal unless currently saving
  const closeModal = () => {
    if (saving) return;
    setShowModal(false);
    setFormError('');
  };

  // synchronises controlled form state
  const handleFormChange = (field, value) => {
    setFormData((prev) => ({
      ...prev,
      [field]: value,
    }));
  };

  /* 
    Sends a new task to backend:
      - validates required fields
      - handles loading state
      - refreshes calendar upon success
  */
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

      // reset modal form after saving
      setShowModal(false);
      setFormData({
        title: '',
        startDate: formatDateInput(weekStart),
        endDate: formatDateInput(weekStart),
        employeeId: '',
      });

      // reload week data
      fetchWeekData();
    } catch (err) {
      setFormError(err.message || 'Unable to save task.');
    } finally {
      setSaving(false);
    }
  };

  return (
    <>
      <Menu />
      <div className="tasks-page">

        {/* PAGE HEADER */}
        <div className="tasks-header">
          <div>
            <h1>Task Management</h1>
            <p>manage and track all your team tasks</p>
          </div>

          <div className="tasks-header__actions">
            <button type="button" className="ghost-btn">
              Filters
            </button>
            <button type="button" className="primary-btn" onClick={openModal}>
              Add task
            </button>
          </div>
        </div>

        {/* WEEK VIEW */}
        <div className="tasks-calendar-card">
          <div className="tasks-calendar-nav">

            {/* WEEK NAVIGATION */}
            <div className="nav-buttons">
              <button type="button" onClick={() => changeWeek(-7)}>
                &lt;
              </button>

              <span className="week-range">
                {formatRangeLabel(weekStart)} – {formatRangeLabel(weekEnd)}
              </span>

              <button type="button" onClick={() => changeWeek(7)}>
                &gt;
              </button>
            </div>
          </div>

          {/* COLUMN HEADERS */}
          <div className="calendar-header">
            <div className="name-col">Name</div>
            {weekDays.map((day) => (
              <div key={day.label} className="day-col">
                {day.label}
              </div>
            ))}
          </div>

          {/* TIMELINE GRID */}
          <div className="calendar-body">
            {loading && <div className="calendar-message">Loading tasks...</div>}
            {!loading && error && (
              <div className="calendar-message error">{error}</div>
            )}

            {/* RENDER ROW FOR EACH EMPLOYEE */}
            {!loading &&
              !error &&
              rows.map((row) => (
                <div key={row.id} className="calendar-row">
                  <div className="name-col">{row.name}</div>

                  <div
                    className="timeline"
                    style={{
                      height: Math.max(
                        TIMELINE_MIN_HEIGHT,
                        LANE_BASE_OFFSET + row.tasks.length * (LANE_HEIGHT + LANE_GAP)
                      ),
                    }}
                  >
                    {/* empty background cells */}
                    <div className="timeline-cells">
                      {weekDays.map((day) => (
                        <div key={`${row.id}-${day.label}`} className="timeline-cell" />
                      ))}
                    </div>

                    {/* TASK BLOCKS */}
                    {[...row.tasks]
                      .sort((a, b) =>
                        a.span === b.span
                          ? a.start_offset - b.start_offset
                          : a.span - b.span
                      )
                      .map((task, index) => {
                        const left = Math.max(0, Math.min((task.start_offset / 7) * 100, 100));
                        const width = Math.min((task.span / 7) * 100, 100 - left);
                        const top = LANE_BASE_OFFSET + index * (LANE_HEIGHT + LANE_GAP);

                        return (
                          <div
                            key={task.assignment_id}
                            className="task-block"
                            style={{
                              left: `${left}%`,
                              width: `${width}%`,
                              top: `${top}px`,
                              height: `${LANE_HEIGHT}px`,
                            }}
                            title={`${task.title} (${task.start_date} → ${task.end_date})`}
                          >
                            {task.title}
                          </div>
                        );
                      })}
                  </div>
                </div>
              ))}

            {/* EMPTY WEEK STATE */}
            {!loading && !error && !hasAnyTasks && (
              <div className="calendar-message empty">
                No tasks scheduled this week.
              </div>
            )}
          </div>
        </div>
      </div>

      {/* ADD TASK MODAL */}
      {showModal && (
        <div className="task-modal">
          <div className="task-modal__content">
            <div className="task-modal__header">
              <h2>Add task</h2>
              <button type="button" onClick={closeModal} aria-label="Close">
                ×
              </button>
            </div>

            <form onSubmit={handleSubmit}>
              <label>
                Task name
                <input
                  type="text"
                  value={formData.title}
                  onChange={(e) => handleFormChange('title', e.target.value)}
                  required
                />
              </label>

              <label>
                Start date
                <input
                  type="date"
                  value={formData.startDate}
                  onChange={(e) => handleFormChange('startDate', e.target.value)}
                  required
                />
              </label>

              <label>
                End date
                <input
                  type="date"
                  value={formData.endDate}
                  onChange={(e) => handleFormChange('endDate', e.target.value)}
                  required
                  min={formData.startDate}
                />
              </label>

              <label>
                Assign to
                <select
                  value={formData.employeeId}
                  onChange={(e) => handleFormChange('employeeId', e.target.value)}
                >
                  {(weekData.employee_options || []).map((option) => (
                    <option
                      key={option.employee_id === null ? 'unassigned' : option.employee_id}
                      value={option.employee_id === null ? '' : option.employee_id}
                    >
                      {option.name}
                    </option>
                  ))}
                </select>
              </label>

              {formError && <p className="form-error">{formError}</p>}

              <div className="modal-actions">
                <button type="button" className="ghost-btn" onClick={closeModal}>
                  Cancel
                </button>

                <button type="submit" className="primary-btn" disabled={saving}>
                  {saving ? 'Saving...' : 'Save task'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

    </>
  );
}

export default TasksPage;
