import { formatSkillLabel } from "../../lib/formatters";

export default function FiltersBar({
  searchTerm,
  setSearchTerm,
  skillsOpen,
  setSkillsOpen,
  selectedSkillsLabel,
  selectedSkills,
  skillSearch,
  setSkillSearch,
  availableSkills,
  filteredAvailableSkills,
  handleSkillChange,
  availability,
  setAvailability,
  rangeOpen,
  setRangeOpen,
  selectedRangeLabel,
  rangeStartInput,
  setRangeStartInput,
  rangeEndInput,
  setRangeEndInput,
  applyDateRange,
  clearDateRange,
  appliedRange,
  skillsRef,
  rangeRef,
  removeSelectedSkill,
}) {
  return (
    <>
      <div className="dashboard-filters">
        <input
          type="text"
          placeholder="Search by name or role..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
        />

        <div className="filter-dropdown" ref={skillsRef}>
          <button
            type="button"
            className="filter-trigger"
            onClick={() => setSkillsOpen((open) => !open)}
            aria-expanded={skillsOpen}
          >
            {selectedSkillsLabel}
          </button>
          {skillsOpen && (
            <div className="filter-panel" role="listbox" aria-label="Filter by skills">
              <div className="filter-panel-header">Filter by skills</div>
              <input
                type="text"
                className="skill-search-input"
                placeholder="Search skills..."
                value={skillSearch}
                onChange={(e) => setSkillSearch(e.target.value)}
              />
              {availableSkills.length === 0 ? (
                <div className="skills-empty">No skills available</div>
              ) : filteredAvailableSkills.length === 0 ? (
                <div className="skills-empty">No skills match your search</div>
              ) : (
                <div className="skills-filter-list">
                  {filteredAvailableSkills.map((skill) => (
                    <label key={skill} className="skill-option">
                      <input
                        type="checkbox"
                        value={skill}
                        checked={selectedSkills.includes(skill)}
                        onChange={handleSkillChange}
                      />
                      <span>{formatSkillLabel(skill)}</span>
                    </label>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>

        <select value={availability} onChange={(e) => setAvailability(e.target.value)}>
          <option value="">Filter by availability</option>
          <option value="available">Available</option>
          <option value="partial">Partial</option>
          <option value="busy">Busy</option>
        </select>

        <div className="filter-dropdown range-filter" ref={rangeRef}>
          <button
            type="button"
            className="filter-trigger"
            onClick={() => setRangeOpen((open) => !open)}
            aria-expanded={rangeOpen}
          >
            {selectedRangeLabel}
          </button>
          {rangeOpen && (
            <div className="filter-panel">
              <div className="filter-panel-header">Availability date range</div>
              <div className="availability-range">
                <div className="date-field">
                  <label htmlFor="availability-start">Start date</label>
                  <input
                    id="availability-start"
                    type="date"
                    value={rangeStartInput}
                    onChange={(e) => setRangeStartInput(e.target.value)}
                  />
                </div>

                <div className="date-field">
                  <label htmlFor="availability-end">End date</label>
                  <input
                    id="availability-end"
                    type="date"
                    value={rangeEndInput}
                    onChange={(e) => setRangeEndInput(e.target.value)}
                  />
                </div>

                <button
                  type="button"
                  className="apply-range"
                  onClick={applyDateRange}
                  disabled={!rangeStartInput || !rangeEndInput}
                >
                  Apply range
                </button>

                <button
                  type="button"
                  className="clear-range"
                  onClick={clearDateRange}
                  disabled={!rangeStartInput && !rangeEndInput && !appliedRange.start && !appliedRange.end}
                >
                  Clear range
                </button>
              </div>
            </div>
          )}
        </div>
      </div>

      {selectedSkills.length > 0 && (
        <div className="selected-skills">
          <span className="selected-label">Selected skills:</span>
          <div className="selected-skill-list">
            {selectedSkills.map((skill) => (
              <button
                key={skill}
                type="button"
                className="selected-skill"
                onClick={() => removeSelectedSkill(skill)}
                title="Remove skill"
              >
                {formatSkillLabel(skill)}
                <span className="remove-x">×</span>
              </button>
            ))}
          </div>
        </div>
      )}
    </>
  );
}
