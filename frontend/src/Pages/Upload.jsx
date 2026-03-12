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
const REQUIRED_COLUMNS = [
  'Employee Name',
  'Role',
  'Department',
  'Skill Set',
  'Skill Experience (Years)',
  'Skill Level (1–5)',
  'Current Project',
  'Start Date',
  'End Date',
  'Total Hours',
  'Remaining Hours',
  'Soft Skill Set',
  'Soft Skill Experience (Years)',
];

function UploadPage() {
  // stores the upload file
  const [uploadFile, setUploadFile] = useState(null);

  // handles success/error messages
  const [status, setStatus] = useState({ type: null, message: '' });

  // shows loading UI during upload
  const [isSubmitting, setIsSubmitting] = useState(false);

  // updates UI when user drags a file over the drop zone
  const [isDragging, setIsDragging] = useState(false);

  // redirect users who aren’t logged in
  useEffect(() => {
    const storedUser = localStorage.getItem('user_id');
    if (!storedUser) window.location.href = '/';
  }, []);

  const columnsText = REQUIRED_COLUMNS.join(', ');

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
    setter(incomingFile);
  };

  // fires when user selects a file via file input
  const handleFileChange = (event) => {
    const selectedFile = event.target.files?.[0];
    validateAndStoreFile(selectedFile, setUploadFile);
  };

  // fires when user drops a file into the drag area
  const handleDrop = (event) => {
    event.preventDefault();
    setIsDragging(false);
    const droppedFile = event.dataTransfer.files?.[0];
    validateAndStoreFile(droppedFile, setUploadFile);
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
  const handleUploadSubmit = async (event) => {
    event.preventDefault();

    if (!uploadFile) {
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
      formData.append('file', uploadFile);
      const body = await apiFetch('/upload', {
        method: 'POST',
        body: formData,
      });

      setStatus({
        type: 'success',
        message: `File uploaded successfully. Rows processed: ${body.row_count ?? 'Unknown'}.`,
      });
      setUploadFile(null);
    } catch (error) {
      setStatus({ type: 'error', message: error.message });
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <>
      <Menu />

      <div className="upload-page">
        <div className="upload-grid">
          <form className="upload-card" onSubmit={handleUploadSubmit}>
            <h1>Upload Team & Assignments</h1>

            {/* Explains required spreadsheet structure */}
            <div className="upload-hint">
              <span>Accepted format: .xlsx — required columns:</span>
              <strong>{columnsText}</strong>
            </div>

            {/* Drag and drop zone */}
            <label
              className={`drop-zone ${isDragging ? 'active' : ''}`}
              onDrop={handleDrop}
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
              <input type="file" accept=".xlsx,.xls" onChange={handleFileChange} />
            </label>

            {/* Displays selected file name */}
            {uploadFile && <p className="file-name">Selected file: {uploadFile.name}</p>}

            {/* Submit button */}
            <button
              type="submit"
              className="primary"
              disabled={!uploadFile || isSubmitting}
            >
              {isSubmitting ? 'Uploading…' : 'Upload File'}
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
