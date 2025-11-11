import { useEffect, useState } from 'react';
import Menu from './Menu';
import '../styles/Dashboard.css';

function DashboardPage() {
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchSummary = async () => {
      try {
        const response = await fetch('http://127.0.0.1:8001/api/dashboard/summary');
        if (!response.ok) throw new Error('Server returned ' + response.status);
        const json = await response.json();
        setData(json);
      } catch (err) {
        console.error('Error fetching dashboard data:', err);
        setError('Could not load dashboard data.');
      }
    };
    fetchSummary();
  }, []);

  return (
    <>
      <Menu />
      <div className="dashboard-container">
        <h1>Team Overview</h1>

        {error ? (
          <p className="error">{error}</p>
        ) : (
          data && (
            <div className="dashboard-cards">
              <div className="card">
                <h3>Total Employees</h3>
                <p>{data.total_employees}</p>
              </div>
              <div className="card">
                <h3>Active Projects</h3>
                <p>{data.active_projects}</p>
              </div>
              <div className="card">
                <h3>Available This Week</h3>
                <p>{data.available_this_week}</p>
              </div>
            </div>
          )
        )}
      </div>
    </>
  );
}

export default DashboardPage;
