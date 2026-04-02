import React, { useCallback, useEffect, useMemo, useState } from 'react';
import Menu from '../Menu';
import '../../styles/Tasks.css';
import { apiFetch } from '../../api';
import { getSessionItem } from '../../session';
import {
  addDays,
  buildWeekDays,
  formatDateInput,
  getWeekStart,
} from '../Tasks/utils';

const formatRangeLabel = (date) =>
  date.toLocaleDateString(undefined, { month: 'short', day: 'numeric' });

const initialWeekStart = getWeekStart(new Date());

const TIMELINE_MIN_HEIGHT = 70;
const LANE_HEIGHT = 44;
const LANE_GAP = 8;
const LANE_BASE_OFFSET = 10;

function EmployeeCalendarPage() {
  const userId = getSessionItem('user_id');

  const [weekStart, setWeekStart] = useState(initialWeekStart);
  const [calendarData, setCalendarData] = useState({ employee: null, items: [] });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const [showModal, setShowModal] = useState(false);
  const [saving, setSaving] = useState(false);
  const [formError, setFormError] = useState('');
  const [formData, setFormData] = useState({
    label: '',
    startDate: formatDateInput(initialWeekStart),
    endDate: formatDateInput(initialWeekStart),
  });

  const weekEnd = useMemo(() => addDays(weekStart, 6), [weekStart]);

  const weekDays = useMemo(() => buildWeekDays(weekStart, 7), [weekStart]);

  const fetchCalendar = useCallback(async () => {
    if (!userId) {
      setLoading(false);
      setError('No user session found.');
      return;
    }
    setLoading(true);
    setError('');
    try {
      const payload = await apiFetch(
        `/employee/calendar?user_id=${userId}&week_start=${formatDateInput(weekStart)}`
      );
      setCalendarData({
        employee: payload.employee || null,
        items: payload.items || [],
      });
    } catch (err) {
      setError(err.message || 'Unable to load calendar.');
      setCalendarData({ employee: null, items: [] });
    } finally {
      setLoading(false);
    }
  }, [userId, weekStart]);

  useEffect(() => {
    fetchCalendar();
  }, [fetchCalendar]);

  const changeWeek = (offset) => {
    setWeekStart((prev) => addDays(prev, offset));
  };

  const openModal = () => {
    setFormData({
      label: '',
      startDate: formatDateInput(weekStart),
      endDate: formatDateInput(weekStart),
    });
    setFormError('');
    setShowModal(true);
  };

  const closeModal = () => {
    if (saving) return;
    setShowModal(false);
    setFormError('');
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
      await apiFetch('/employee/calendar', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_id: Number(userId),
          label: formData.label,
          start_date: formData.startDate,
          end_date: formData.endDate,
        }),
      });
      setShowModal(false);
      fetchCalendar();
    } catch (err) {
      setFormError(err.message || 'Unable to save entry.');
    } finally {
      setSaving(false);
    }
  };

  const items = calendarData.items || [];
  const hasAnyItems = items.length > 0;

  return (
    <>
      <Menu />
      <div className="tasks-page employee-calendar-page">
        <div className="tasks-header">
          <div>
            <h1>My Calendar</h1>
            <p>See your assignments and add calendar entries.</p>
          </div>

          <div className="tasks-header__actions">
            <button type="button" className="primary-btn" onClick={openModal}>
              Add entry
            </button>
          </div>
        </div>

        <div className="tasks-calendar-card">
          <div className="tasks-calendar-nav">
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

          <div className="calendar-scroll">
            <div className="calendar-header">
              {weekDays.map((day) => (
                <div
                  key={day.label}
                  className={`day-col${day.isToday ? ' today' : ''}`}
                >
                  {day.label}
                </div>
              ))}
            </div>

            <div className="calendar-body">
              {loading && <div className="calendar-message">Loading calendar...</div>}
              {!loading && error && (
                <div className="calendar-message error">{error}</div>
              )}

              {!loading && !error && (
                <div className="calendar-row">
                  <div
                    className="timeline"
                    style={{
                      height: Math.max(
                        TIMELINE_MIN_HEIGHT,
                        LANE_BASE_OFFSET + items.length * (LANE_HEIGHT + LANE_GAP)
                      ),
                    }}
                    >
                    <div className="timeline-cells">
                      {weekDays.map((day) => (
                        <div
                          key={`day-${day.label}`}
                          className={`timeline-cell${day.isToday ? ' today' : ''}`}
                        />
                      ))}
                    </div>

                    {[...items]
                      .sort((a, b) =>
                        a.span === b.span
                          ? a.start_offset - b.start_offset
                          : a.span - b.span
                      )
                      .map((item, index) => {
                        const left = Math.max(0, Math.min((item.start_offset / 7) * 100, 100));
                        const width = Math.min((item.span / 7) * 100, 100 - left);
                        const top = LANE_BASE_OFFSET + index * (LANE_HEIGHT + LANE_GAP);

                        return (
                          <div
                            key={`${item.type}-${item.id}`}
                            className={`task-block ${item.type === 'personal' ? 'personal' : ''}`}
                            style={{
                              left: `${left}%`,
                              width: `${width}%`,
                              top: `${top}px`,
                              height: `${LANE_HEIGHT}px`,
                            }}
                            title={`${item.title} (${item.start_date} → ${item.end_date})`}
                          >
                            {item.title}
                          </div>
                        );
                      })}
                  </div>
                </div>
              )}

              {!loading && !error && !hasAnyItems && (
                <div className="calendar-message empty">
                  No assignments or calendar entries scheduled this week.
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      {showModal && (
        <div className="task-modal">
          <div className="task-modal__content">
              <div className="task-modal__header">
              <h2>Add calendar entry</h2>
              <button type="button" onClick={closeModal} aria-label="Close">
                ×
              </button>
            </div>

            <form onSubmit={handleSubmit}>
              <label>
                Label
                <input
                  type="text"
                  value={formData.label}
                  onChange={(e) => setFormData((prev) => ({ ...prev, label: e.target.value }))}
                  required
                />
              </label>

              <label>
                Start date
                <input
                  type="date"
                  value={formData.startDate}
                  onChange={(e) => setFormData((prev) => ({ ...prev, startDate: e.target.value }))}
                  required
                />
              </label>
              <label>
                End date
                <input
                  type="date"
                  value={formData.endDate}
                  onChange={(e) => setFormData((prev) => ({ ...prev, endDate: e.target.value }))}
                  required
                  min={formData.startDate}
                />
              </label>

              {formError && <p className="form-error">{formError}</p>}

              <div className="modal-actions">
                <button type="button" className="ghost-btn" onClick={closeModal}>
                  Cancel
                </button>
                <button type="submit" className="primary-btn" disabled={saving}>
                  {saving ? 'Saving...' : 'Save'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </>
  );
}

export default EmployeeCalendarPage;
