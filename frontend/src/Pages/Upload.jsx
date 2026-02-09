import { useEffect, useState } from 'react';
import Menu from './Menu';
import '../styles/Upload.css';
import uploadIcon from '../images/upload.png';
import { apiFetch } from '../api';

/*
  Required columns for a valid dataset.
  Backend will reject uploads that don’t follow this schema,
  so the UI shows them clearly to reduce user mistakes.
*/
const SETUP_COLUMNS = [
  'Employee Name',
  'Role',
  'Department',
  'Skill Set',
  'Skill Experience (Years)',
];

const ASSIGNMENT_COLUMNS = [
  'Employee ID',
  'Task Title',
  'Start Date',
  'End Date',
  'Total Hours',
  'Remaining Hours',
  'Priority',
];

function UploadPage() {
  // stores the setup import file
  const [setupFile, setSetupFile] = useState(null);

  // stores the assignment upload file
  const [assignmentFile, setAssignmentFile] = useState(null);

  // handles success/error messages
  const [status, setStatus] = useState({ type: null, message: '' });

  // shows loading UI during upload
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isAssignmentSubmitting, setIsAssignmentSubmitting] = useState(false);

  // updates UI when user drags a file over the drop zone
  const [isDragging, setIsDragging] = useState(false);

  // tracks whether employee setup import is allowed
  const [setupStatus, setSetupStatus] = useState(null);

  // preview data for setup import
  const [preview, setPreview] = useState(null);

  // redirect users who aren’t logged in
  useEffect(() => {
    const storedUser = localStorage.getItem('user_id');
    if (!storedUser) window.location.href = '/';
  }, []);

  useEffect(() => {
    const userId = localStorage.getItem('user_id');
    if (!userId) return;

    const fetchStatus = async () => {
      try {
        const data = await apiFetch(`/setup/status?user_id=${userId}`);
        setSetupStatus(data);
      } catch (error) {
        setSetupStatus({ can_import: false, employee_count: 0 });
      }
    };

    fetchStatus();
  }, []);

  const isSetupMode = setupStatus?.can_import;
  const setupColumnsText = SETUP_COLUMNS.join(', ');
  const assignmentColumnsText = ASSIGNMENT_COLUMNS.join(', ');

  /*
    Validates uploaded file:
    - must exist
    - must be .xlsx
    Stores the file if valid.
  */
  const validateAndStoreFile = (incomingFile, setter) => {
    if (!incomingFile) return;

    const extension = incomingFile.name.split('.').pop()?.toLowerCase();
    if (extension !== 'xlsx' && extension !== 'xls') {
      setStatus({ type: 'error', message: 'Only .xlsx or .xls files are allowed.' });
      setter(null);
      return;
    }

    setStatus({ type: null, message: '' });
    setPreview(null);
    setter(incomingFile);
  };

  // fires when user selects a file via file input
  const handleSetupFileChange = (event) => {
    const selectedFile = event.target.files?.[0];
    validateAndStoreFile(selectedFile, setSetupFile);
  };

  const handleAssignmentFileChange = (event) => {
    const selectedFile = event.target.files?.[0];
    validateAndStoreFile(selectedFile, setAssignmentFile);
  };

  // fires when user drops a file into the drag area
  const handleSetupDrop = (event) => {
    event.preventDefault();
    setIsDragging(false);
    const droppedFile = event.dataTransfer.files?.[0];
    validateAndStoreFile(droppedFile, setSetupFile);
  };

  const handleAssignmentDrop = (event) => {
    event.preventDefault();
    setIsDragging(false);
    const droppedFile = event.dataTransfer.files?.[0];
    validateAndStoreFile(droppedFile, setAssignmentFile);
  };

  // triggers UI highlight while dragging
  const handleDragOver = (event) => {
    event.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = () => setIsDragging(false);

  /*
    Upload handler:
    - ensures user is logged in
    - ensures a valid file is chosen
    - sends FormData to backend
    - stores returned upload_id (required for recommendations later)
  */
  const handleSetupSubmit = async (event) => {
    event.preventDefault();

    if (!setupFile) {
      setStatus({ type: 'error', message: 'Please choose an Excel file first.' });
      return;
    }

    const userId = localStorage.getItem('user_id');
    if (!userId) {
      setStatus({ type: 'error', message: 'You need to be logged in before uploading.' });
      return;
    }

    setIsSubmitting(true);
    setStatus({ type: null, message: '' });

    try {
      const formData = new FormData();
      formData.append('user_id', userId);
      formData.append('file', setupFile);
      formData.append('preview', preview ? 'false' : 'true');
      const body = await apiFetch('/setup/import-employees', {
        method: 'POST',
        body: formData,
      });

      if (preview) {
        setStatus({
          type: 'success',
          message: `Employees imported successfully. Rows processed: ${body.row_count ?? 'Unknown'}.`,
        });
        setSetupFile(null);
        setPreview(null);
        setSetupStatus({ can_import: false, employee_count: body.row_count });
        return;
      }

      setPreview(body);
      if (body.errors && body.errors.length > 0) {
        setStatus({ type: 'error', message: body.errors.join(' ') });
      } else {
        setStatus({
          type: 'info',
          message: 'Preview generated. Review and confirm import.',
        });
      }
    } catch (error) {
      setStatus({ type: 'error', message: error.message });
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleAssignmentSubmit = async (event) => {
    event.preventDefault();

    if (!assignmentFile) {
      setStatus({ type: 'error', message: 'Please choose an Excel file first.' });
      return;
    }

    const userId = localStorage.getItem('user_id');
    if (!userId) {
      setStatus({ type: 'error', message: 'You need to be logged in before uploading.' });
      return;
    }

    setIsAssignmentSubmitting(true);
    setStatus({ type: null, message: '' });

    try {
      const formData = new FormData();
      formData.append('user_id', userId);
      formData.append('file', assignmentFile);

      const body = await apiFetch('/upload', {
        method: 'POST',
        body: formData,
      });

      setStatus({
        type: 'success',
        message: `File uploaded successfully. Rows processed: ${body.row_count ?? 'Unknown'}.`,
      });
      setAssignmentFile(null);
    } catch (error) {
      setStatus({ type: 'error', message: error.message });
    } finally {
      setIsAssignmentSubmitting(false);
    }
  };

  return (
    <>
      <Menu />

      <div className="upload-page">
        <div className="upload-grid">
          <form className="upload-card" onSubmit={handleSetupSubmit}>
            <h1>Import Employees (Setup Only)</h1>

            {/* Explains required spreadsheet structure */}
            <div className="upload-hint">
              <span>Accepted format: .xlsx — include columns:</span>
              <strong>{setupColumnsText}</strong>
            </div>

            {/* Drag and drop zone */}
            <label
              className={`drop-zone ${isDragging ? 'active' : ''}`}
              onDrop={handleSetupDrop}
              onDragOver={handleDragOver}
              onDragLeave={handleDragLeave}
            >
              <div className="drop-icon">
                <img src={uploadIcon} alt="Upload icon" />
              </div>

              <p>Drag and drop your Excel file here</p>
              <span>or</span>

              <button type="button" className="browse-button">
                Browse File
              </button>

              {/* Hidden input triggered by "Browse File" */}
              <input type="file" accept=".xlsx" onChange={handleSetupFileChange} />
            </label>

            {/* Displays selected file name */}
            {setupFile && <p className="file-name">Selected file: {setupFile.name}</p>}

            {/* Submit button */}
            <button
              type="submit"
              className="primary"
              disabled={!setupFile || isSubmitting || !setupStatus?.can_import}
            >
              {isSubmitting
                ? 'Uploading…'
                : preview
                ? 'Confirm Import'
                : 'Preview Import'}
            </button>

            {!setupStatus?.can_import && (
              <p className="status info">Employee setup import is disabled once employees exist.</p>
            )}

            {preview?.preview && (
              <div className="upload-preview">
                <h3>Preview</h3>
                <ul>
                  {preview.preview.map((row, index) => (
                    <li key={index}>
                      {row.name} ({row.role})
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </form>

          <form className="upload-card" onSubmit={handleAssignmentSubmit}>
            <h1>Upload Assignments</h1>

            {/* Explains required spreadsheet structure */}
            <div className="upload-hint">
              <span>Accepted format: .xlsx — include columns:</span>
              <strong>{assignmentColumnsText}</strong>
            </div>

            {/* Drag and drop zone */}
            <label
              className={`drop-zone ${isDragging ? 'active' : ''}`}
              onDrop={handleAssignmentDrop}
              onDragOver={handleDragOver}
              onDragLeave={handleDragLeave}
            >
              <div className="drop-icon">
                <img src={uploadIcon} alt="Upload icon" />
              </div>

              <p>Drag and drop your Excel file here</p>
              <span>or</span>

              <button type="button" className="browse-button">
                Browse File
              </button>

              {/* Hidden input triggered by "Browse File" */}
              <input type="file" accept=".xlsx" onChange={handleAssignmentFileChange} />
            </label>

            {/* Displays selected file name */}
            {assignmentFile && <p className="file-name">Selected file: {assignmentFile.name}</p>}

            {/* Submit button */}
            <button
              type="submit"
              className="primary"
              disabled={!assignmentFile || isAssignmentSubmitting}
            >
              {isAssignmentSubmitting ? 'Uploading…' : 'Upload File'}
            </button>

            {/* Status output */}
            {status.type && (
              <p className={`status ${status.type}`}>{status.message}</p>
            )}
          </form>
        </div>
      </div>
    </>
  );
}

export default UploadPage;
