// build a clean base URL from environment or fallback
// ensures no trailing slash so `/api` appends correctly
const rawBaseUrl =
  (process.env.REACT_APP_API_URL || 'http://localhost:8001').replace(/\/$/, '');

// final API base used by all requests in the frontend
export const API_BASE_URL = `${rawBaseUrl}/api`;

// custom error class used to surface backend errors in a structured way
export class APIError extends Error {
  constructor(message, status, body) {
    super(message);            // parent error message
    this.name = 'APIError';    // helps identify error type
    this.status = status;      // HTTP status code
    this.body = body;          // parsed JSON from backend (if any)
  }
}

/*
  Unified fetch helper:
  - builds the correct API URL
  - parses JSON safely
  - throws APIError on non-2xx responses
  - always returns JSON for success responses
*/
export async function apiFetch(path, options = {}) {
  // allow full URLs or relative API paths
  const url = path.startsWith('http') ? path : `${API_BASE_URL}${path}`;

  const response = await fetch(url, options);

  // safely try to parse JSON (backend errors may return no body)
  const body = await response.json().catch(() => ({}));

  // throw structured error when status is not ok
  if (!response.ok) {
    const detail =
      typeof body.detail === 'string'
        ? body.detail
        : body.message || `Request failed with status ${response.status}`;

    throw new APIError(detail, response.status, body);
  }

  // success response: return the parsed JSON
  return body;
}
