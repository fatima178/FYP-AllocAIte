import {
  LANE_BASE_OFFSET,
  LANE_GAP,
  LANE_HEIGHT,
  TIMELINE_MIN_HEIGHT,
  formatRangeLabel,
} from "./utils";

export default function TasksCalendar({
  viewDays,
  weekStart,
  weekEnd,
  weekDays,
  loading,
  error,
  filteredRows,
  hasAnyTasks,
  onChangeWeek,
  onEditTask,
}) {
  return (
    <div className="tasks-calendar-card" style={{ '--task-days': viewDays }}>
      <div className="tasks-calendar-nav">
        <div className="nav-buttons">
          <button type="button" onClick={() => onChangeWeek(-1)}>&lt;</button>
          <span className="week-range">
            {formatRangeLabel(weekStart)} – {formatRangeLabel(weekEnd)}
          </span>
          <button type="button" onClick={() => onChangeWeek(1)}>&gt;</button>
        </div>
      </div>

      <div className="calendar-scroll">
        <div className="calendar-header">
          <div className="name-col">Name</div>
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
          {loading && <div className="calendar-message">Loading tasks...</div>}
          {!loading && error && <div className="calendar-message error">{error}</div>}

          {!loading && !error && filteredRows.map((row) => (
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
                <div className="timeline-cells">
                  {weekDays.map((day) => (
                    <div
                      key={`${row.id}-${day.label}`}
                      className={`timeline-cell${day.isToday ? ' today' : ''}`}
                    />
                  ))}
                </div>

                {[...row.tasks]
                  .sort((a, b) => (a.span === b.span ? a.start_offset - b.start_offset : a.span - b.span))
                  .map((task, index) => {
                    const left = Math.max(0, Math.min((task.start_offset / viewDays) * 100, 100));
                    const width = Math.min((task.span / viewDays) * 100, 100 - left);
                    const top = LANE_BASE_OFFSET + index * (LANE_HEIGHT + LANE_GAP);
                    const isUnassignedRow = row.id === 'unassigned';

                    return (
                      <div
                        key={task.assignment_id}
                        className={`task-block${isUnassignedRow ? ' unassigned' : ''}`}
                        onClick={() => onEditTask(task)}
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

          {!loading && !error && !hasAnyTasks && (
            <div className="calendar-message empty">No tasks scheduled for this view.</div>
          )}
        </div>
      </div>
    </div>
  );
}
