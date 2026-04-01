import React, { useState } from "react";

import Menu from "../Menu";
import "../../styles/Settings.css";
import AccountSection from "./AccountSection";
import AppearanceSection from "./AppearanceSection";
import EditDetailsModal from "./EditDetailsModal";
import ExportSection from "./ExportSection";
import HistorySection from "./HistorySection";
import PasswordModal from "./PasswordModal";
import SectionSidebar from "./SectionSidebar";
import TeamSection from "./TeamSection";
import {
  ADJUSTABLE_WEIGHT_BUDGET,
  FIXED_SEMANTIC_WEIGHT,
  WEIGHTING_FIELDS,
} from "./constants";
import {
  useRecommendationHistoryState,
  useSettingsCoreState,
  useTeamManagementState,
} from "./useSettingsState";
import WeightsSection from "./WeightsSection";

function SettingsPage() {
  const [activeSection, setActiveSection] = useState("account");
  const core = useSettingsCoreState();
  const team = useTeamManagementState();
  const history = useRecommendationHistoryState(activeSection);

  return (
    <div className="settings-page">
      <Menu />

      <div className="settings-content settings-layout">
        <SectionSidebar
          activeSection={activeSection}
          onChange={(section) => {
            if (section === "history") {
              history.setHistoryPage(1);
            }
            setActiveSection(section);
          }}
        />

        <div className="settings-main">
          <h1>Settings</h1>
          <p className="subtitle">Manage your account and preferences</p>
          {core.loading && <p>Loading settings...</p>}
          {core.error && <p className="error">{core.error}</p>}
          {core.status && <p className="status-message info">{core.status}</p>}

          {activeSection === "account" && (
            <AccountSection
              account={core.account}
              formatMemberSince={core.formatMemberSince}
              onEdit={core.openEditModal}
              onChangePassword={core.openPasswordModal}
            />
          )}

          {activeSection === "appearance" && (
            <AppearanceSection
              theme={core.theme}
              fontSize={core.fontSize}
              onThemeChange={core.changeTheme}
              onFontSizeChange={core.changeFontSize}
            />
          )}

          {activeSection === "weights" && (
            <WeightsSection
              weightingFields={WEIGHTING_FIELDS}
              fixedSemanticWeight={FIXED_SEMANTIC_WEIGHT}
              totalAllocatedPoints={core.totalAllocatedPoints}
              remainingWeightPoints={core.remainingWeightPoints}
              adjustableWeightBudget={ADJUSTABLE_WEIGHT_BUDGET}
              weights={core.weights}
              getWeightPoints={core.getWeightPoints}
              onWeightChange={core.updateWeightAllocation}
              onSave={core.saveWeights}
              onReset={core.resetWeights}
            />
          )}

          {activeSection === "team" && (
            <TeamSection
              employeeOptions={team.employeeOptions}
              existingEmployeeId={team.existingEmployeeId}
              setExistingEmployeeId={team.setExistingEmployeeId}
              existingEmployeeSkills={team.existingEmployeeSkills}
              setExistingEmployeeSkills={team.setExistingEmployeeSkills}
              existingSkillStatus={team.existingSkillStatus}
              existingSkillSaving={team.existingSkillSaving}
              onSubmitExistingSkills={team.onSubmitExistingSkills}
              employeeForm={team.employeeForm}
              onEmployeeChange={team.onEmployeeChange}
              employeeSkills={team.employeeSkills}
              setEmployeeSkills={team.setEmployeeSkills}
              skillError={team.skillError}
              employeeStatus={team.employeeStatus}
              employeeSaving={team.employeeSaving}
              onSubmitEmployee={team.onSubmitEmployee}
              inviteForm={team.inviteForm}
              inviteStatus={team.inviteStatus}
              inviteLink={team.inviteLink}
              inviteSaving={team.inviteSaving}
              onInviteFormChange={team.onInviteFormChange}
              onEmployeeSelect={team.onEmployeeSelect}
              onSubmitInvite={team.onSubmitInvite}
            />
          )}

          {activeSection === "history" && (
            <HistorySection
              loading={history.historyLoading}
              error={history.historyError}
              items={history.historyItems}
              historyStart={history.historyStart}
              historyEnd={history.historyEnd}
              historyTotal={history.historyTotal}
              historyPage={history.historyPage}
              historyTotalPages={history.historyTotalPages}
              expandedHistory={history.expandedHistory}
              onPrevious={() => history.setHistoryPage((prev) => Math.max(1, prev - 1))}
              onNext={() => history.setHistoryPage((prev) => Math.min(history.historyTotalPages, prev + 1))}
              onToggle={history.toggleHistoryCard}
              buildHistoryTitle={history.buildHistoryTitle}
              buildCollapsedHistoryTitle={history.buildCollapsedHistoryTitle}
              buildTopMatchesLabel={history.buildTopMatchesLabel}
            />
          )}

          {activeSection === "export" && (
            <ExportSection
              exporting={core.exporting}
              exportStatus={core.exportStatus}
              onExport={core.exportAllData}
            />
          )}
        </div>
      </div>

      <EditDetailsModal
        open={core.isEditModalOpen}
        detailsForm={core.detailsForm}
        detailsStatus={core.detailsStatus}
        onClose={core.closeEditModal}
        onChange={core.handleDetailsChange}
        onSubmit={core.submitDetails}
      />

      <PasswordModal
        open={core.isPasswordModalOpen}
        passwordVerified={core.passwordVerified}
        passwordForm={core.passwordForm}
        verifyStatus={core.verifyStatus}
        passwordStatus={core.passwordStatus}
        onClose={core.closePasswordModal}
        onChange={core.handlePasswordChange}
        onVerify={core.verifyCurrentPassword}
        onSubmit={core.submitPassword}
      />
    </div>
  );
}

export default SettingsPage;
