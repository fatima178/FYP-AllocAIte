export const getWeekStart = (inputDate) => {
  const date = new Date(inputDate);
  const day = date.getDay();
  const diff = (day === 0 ? -6 : 1) - day;
  date.setDate(date.getDate() + diff);
  date.setHours(0, 0, 0, 0);
  return date;
};

export const addDays = (date, days) => {
  const clone = new Date(date);
  clone.setDate(clone.getDate() + days);
  return clone;
};

export const formatDateInput = (date) => {
  const year = date.getFullYear();
  const month = `${date.getMonth() + 1}`.padStart(2, '0');
  const day = `${date.getDate()}`.padStart(2, '0');
  return `${year}-${month}-${day}`;
};

export const formatRangeLabel = (date) =>
  date.toLocaleDateString(undefined, { month: 'short', day: 'numeric' });

export const formatDayLabel = (date) =>
  date.toLocaleDateString(undefined, { weekday: 'short', day: 'numeric' });

export const initialWeekStart = getWeekStart(new Date());
export const defaultEmployeeOptions = [{ employee_id: null, name: 'Unassigned' }];
export const TIMELINE_MIN_HEIGHT = 70;
export const LANE_HEIGHT = 44;
export const LANE_GAP = 8;
export const LANE_BASE_OFFSET = 10;
export const OUTCOME_TAG_OPTIONS = [
  'Delivered on time',
  'High quality',
  'Needed support',
  'Exceeded expectations',
  'Communication issues',
  'Scope changed',
];
