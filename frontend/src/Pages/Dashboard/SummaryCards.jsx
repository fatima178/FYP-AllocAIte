export default function SummaryCards({ data, summaryProjectsLabel, summaryAvailabilityLabel }) {
  if (!data) return null;

  return (
    <div className="dashboard-cards">
      <div className="card">
        <h3>Total Employees</h3>
        <p>{data.total_employees}</p>
      </div>
      <div className="card">
        <h3>{summaryProjectsLabel}</h3>
        <p>{data.active_projects}</p>
      </div>
      <div className="card">
        <h3>{summaryAvailabilityLabel}</h3>
        <p>{data.available_this_week}</p>
      </div>
    </div>
  );
}
