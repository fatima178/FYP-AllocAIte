import Menu from '../Menu';
import '../../styles/Dashboard.css';
import EmployeeGrid from './EmployeeGrid';
import FiltersBar from './FiltersBar';
import SkillApprovalPanel from './SkillApprovalPanel';
import SummaryCards from './SummaryCards';
import { useDashboardState } from './useDashboardState';

function DashboardPage() {
  const dashboard = useDashboardState();

  return (
    <>
      <Menu />
      <div className="dashboard-container">
        <h1>Team Overview</h1>
        {dashboard.error ? (
          <p className="error">{dashboard.error}</p>
        ) : (
          dashboard.data && (
            <>
              <SummaryCards
                data={dashboard.data}
                summaryProjectsLabel={dashboard.labels.summaryProjectsLabel}
                summaryAvailabilityLabel={dashboard.labels.summaryAvailabilityLabel}
              />

              <SkillApprovalPanel
                visible={
                  dashboard.accountType === "manager" &&
                  (
                    dashboard.pendingSkillLoading ||
                    dashboard.pendingSkillError ||
                    dashboard.pendingSkillRequests.length > 0
                  )
                }
                loading={dashboard.pendingSkillLoading}
                error={dashboard.pendingSkillError}
                requests={dashboard.pendingSkillRequests}
                reviewingSkillId={dashboard.reviewingSkillId}
                onReview={dashboard.reviewSkillRequest}
              />

              <FiltersBar
                searchTerm={dashboard.searchTerm}
                setSearchTerm={dashboard.setSearchTerm}
                skillsOpen={dashboard.skillsOpen}
                setSkillsOpen={dashboard.setSkillsOpen}
                selectedSkillsLabel={dashboard.labels.selectedSkillsLabel}
                selectedSkills={dashboard.selectedSkills}
                skillSearch={dashboard.skillSearch}
                setSkillSearch={dashboard.setSkillSearch}
                availableSkills={dashboard.availableSkills}
                filteredAvailableSkills={dashboard.filteredAvailableSkills}
                handleSkillChange={dashboard.handleSkillChange}
                availability={dashboard.availability}
                setAvailability={dashboard.setAvailability}
                rangeOpen={dashboard.rangeOpen}
                setRangeOpen={dashboard.setRangeOpen}
                selectedRangeLabel={dashboard.labels.selectedRangeLabel}
                rangeStartInput={dashboard.rangeStartInput}
                setRangeStartInput={dashboard.setRangeStartInput}
                rangeEndInput={dashboard.rangeEndInput}
                setRangeEndInput={dashboard.setRangeEndInput}
                applyDateRange={dashboard.applyDateRange}
                clearDateRange={dashboard.clearDateRange}
                appliedRange={dashboard.appliedRange}
                skillsRef={dashboard.skillsRef}
                rangeRef={dashboard.rangeRef}
                removeSelectedSkill={dashboard.removeSelectedSkill}
              />

              <EmployeeGrid
                employees={dashboard.employees}
                availabilityLabel={dashboard.labels.availabilityLabel}
              />
            </>
          )
        )}
      </div>
    </>
  );
}

export default DashboardPage;
