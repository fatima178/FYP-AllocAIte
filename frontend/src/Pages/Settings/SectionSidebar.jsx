const SECTIONS = [
  { key: "account", label: "Account" },
  { key: "appearance", label: "Appearance" },
  { key: "weights", label: "Weightings" },
  { key: "team", label: "Team" },
  { key: "history", label: "History" },
  { key: "export", label: "Export" },
];

export default function SectionSidebar({ activeSection, onChange }) {
  return (
    <aside className="settings-sidebar">
      <p className="sidebar-title">Sections</p>
      {SECTIONS.map((section) => (
        <button
          key={section.key}
          type="button"
          className={activeSection === section.key ? "active" : ""}
          onClick={() => onChange(section.key)}
        >
          {section.label}
        </button>
      ))}
    </aside>
  );
}
