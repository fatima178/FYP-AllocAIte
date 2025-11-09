import { useEffect, useState } from 'react';
import '../styles/Upload.css';
import uploadIcon from '../images/upload.png';

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
  const [file, setFile] = useState(null);
  const [status, setStatus] = useState({ type: null, message: '' });
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isDragging, setIsDragging] = useState(false);

  // Guard the page so only authenticated users (with cached ids) can access it
  useEffect(() => {
    const storedUser = localStorage.getItem('user_id');
    if (!storedUser) {
      window.location.href = '/';
    }
  }, []);

  // Make sure we nudge users toward providing the spreadsheet we expect
  const acceptedColumnsText = REQUIRED_COLUMNS.join(', ');

  const validateAndStoreFile = (incomingFile) => {
    if (!incomingFile) {
      return;
    }

    const extension = incomingFile.name.split('.').pop()?.toLowerCase();
    if (extension !== 'xlsx') {
      setStatus({ type: 'error', message: 'Only .xlsx files are allowed.' });
      setFile(null);
      return;
    }

    setStatus({ type: null, message: '' });
    setFile(incomingFile);
  };

  // Handle the standard file picker workflow
  const handleFileChange = (event) => {
    const selectedFile = event.target.files?.[0];
    validateAndStoreFile(selectedFile);
  };

  // Support drag-and-drop for convenience
  const handleDrop = (event) => {
    event.preventDefault();
    setIsDragging(false);
    const droppedFile = event.dataTransfer.files?.[0];
    validateAndStoreFile(droppedFile);
  };

  const handleDragOver = (event) => {
    event.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = () => setIsDragging(false);

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

      const response = await fetch('http://localhost:8001/api/upload', {
        method: 'POST',
        body: formData,
      });

      const body = await response.json();

      if (!response.ok) {
        throw new Error(body.detail || 'Unable to upload file.');
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
    <div className="upload-page">
      <form className="upload-card" onSubmit={handleSubmit}>
        <h1>Upload Employee Data</h1>

        <div className="upload-hint">
          <span>Accepted format: .xlsx — include columns:</span>
          <strong>{acceptedColumnsText}</strong>
        </div>

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
          <input type="file" accept=".xlsx" onChange={handleFileChange} />
        </label>

        {file && <p className="file-name">Selected file: {file.name}</p>}

        <button type="submit" className="primary" disabled={!file || isSubmitting}>
          {isSubmitting ? 'Uploading…' : 'Upload File'}
        </button>

        {status.type && (
          <p className={`status ${status.type}`}>{status.message}</p>
        )}
      </form>
    </div>
  );
}

export default UploadPage;
