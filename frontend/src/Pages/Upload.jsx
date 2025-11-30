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
  'Experience (Years)',
  'Skill Level (1–5)',
  'Current Project',
  'Start Date',
  'End Date',
  'Total Hours',
  'Remaining Hours',
  'Priority',
];

function UploadPage() {
  // stores the file the user selects/drops
  const [file, setFile] = useState(null);

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

  const acceptedColumnsText = REQUIRED_COLUMNS.join(', ');

  /*
    Validates uploaded file:
    - must exist
    - must be .xlsx
    Stores the file if valid.
  */
  const validateAndStoreFile = (incomingFile) => {
    if (!incomingFile) return;

    const extension = incomingFile.name.split('.').pop()?.toLowerCase();
    if (extension !== 'xlsx') {
      setStatus({ type: 'error', message: 'Only .xlsx files are allowed.' });
      setFile(null);
      return;
    }

    setStatus({ type: null, message: '' });
    setFile(incomingFile);
  };

  // fires when user selects a file via file input
  const handleFileChange = (event) => {
    const selectedFile = event.target.files?.[0];
    validateAndStoreFile(selectedFile);
  };

  // fires when user drops a file into the drag area
  const handleDrop = (event) => {
    event.preventDefault();
    setIsDragging(false);
    const droppedFile = event.dataTransfer.files?.[0];
    validateAndStoreFile(droppedFile);
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
  const handleSubmit = async (event) => {
    event.preventDefault();

    if (!file) {
      setStatus({ type: 'error', message: 'Please choose an .xlsx file first.' });
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
      formData.append('file', file);

      const body = await apiFetch('/upload', {
        method: 'POST',
        body: formData,
      });

      // system-wide active dataset used for recommendations
      if (body.upload_id) {
        localStorage.setItem('active_upload_id', body.upload_id);
      }

      setStatus({
        type: 'success',
        message: `File uploaded successfully. Rows processed: ${body.rows}.`,
      });
      setFile(null);
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
        <form className="upload-card" onSubmit={handleSubmit}>
          <h1>Upload Employee Data</h1>

          {/* Explains required spreadsheet structure */}
          <div className="upload-hint">
            <span>Accepted format: .xlsx — include columns:</span>
            <strong>{acceptedColumnsText}</strong>
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
            <input type="file" accept=".xlsx" onChange={handleFileChange} />
          </label>

          {/* Displays selected file name */}
          {file && <p className="file-name">Selected file: {file.name}</p>}

          {/* Submit button */}
          <button
            type="submit"
            className="primary"
            disabled={!file || isSubmitting}
          >
            {isSubmitting ? 'Uploading…' : 'Upload File'}
          </button>

          {/* Status output */}
          {status.type && (
            <p className={`status ${status.type}`}>{status.message}</p>
          )}
        </form>
      </div>
    </>
  );
}

export default UploadPage;
