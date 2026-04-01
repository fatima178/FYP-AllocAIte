export default function ExportSection({ exporting, exportStatus, onExport }) {
  return (
    <div className="settings-card">
      <h2>Export Data</h2>
      <p className="muted">Download all your team data in the same Excel format as uploads.</p>
      <div className="button-row">
        <button className="primary" onClick={onExport} disabled={exporting}>
          {exporting ? "Exporting..." : "Export All Data"}
        </button>
      </div>
      {exportStatus && <p className="status-message info">{exportStatus}</p>}
    </div>
  );
}
