const rawBaseUrl =
  (process.env.REACT_APP_API_URL || 'http://localhost:8001').replace(/\/$/, '');

export const API_BASE_URL = `${rawBaseUrl}/api`;

export class APIError extends Error {
  constructor(message, status, body) {
    super(message);
    this.name = 'APIError';
    this.status = status;
    this.body = body;
  }
}

export async function apiFetch(path, options = {}) {
  const url = path.startsWith('http') ? path : `${API_BASE_URL}${path}`;
  const response = await fetch(url, options);
  const body = await response.json().catch(() => ({}));

  if (!response.ok) {
    const detail =
      typeof body.detail === 'string'
        ? body.detail
        : body.message || `Request failed with status ${response.status}`;
    throw new APIError(detail, response.status, body);
  }

  return body;
}
