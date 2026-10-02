import axios, { AxiosError } from 'axios';

const TOKEN_STORAGE_KEY = 'issue_tracker.token';

/** Minimal localStorage wrapper so the rest of the app never touches the key directly. */
export const tokenStorage = {
  get: (): string | null => localStorage.getItem(TOKEN_STORAGE_KEY),
  set: (token: string): void => localStorage.setItem(TOKEN_STORAGE_KEY, token),
  clear: (): void => localStorage.removeItem(TOKEN_STORAGE_KEY),
};

/**
 * Shared axios instance.
 * - Development: baseURL is "/api" and the Vite dev server proxies it to the
 *   FastAPI backend (see vite.config.ts).
 * - Production: override with VITE_API_URL, e.g. "https://api.example.com/api".
 */
export const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_URL || '/api',
  headers: { 'Content-Type': 'application/json' },
});

apiClient.interceptors.request.use((config) => {
  const token = tokenStorage.get();
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// A 401 with a stored token means the session expired: reset and re-login.
// The "expired" query flag lets the login page explain what happened.
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (axios.isAxiosError(error) && error.response?.status === 401 && tokenStorage.get()) {
      tokenStorage.clear();
      window.location.assign('/login?expired=1');
    }
    return Promise.reject(error);
  },
);

/** Extract a human-readable message from an API error. */
export function getApiErrorMessage(error: unknown): string {
  if (axios.isAxiosError(error)) {
    const axiosError = error as AxiosError<{ detail?: unknown }>;
    const detail = axiosError.response?.data?.detail;

    if (typeof detail === 'string') {
      return detail;
    }
    if (Array.isArray(detail)) {
      // FastAPI validation errors: [{ loc, msg, type }, ...]
      return detail
        .map((item) => {
          const message =
            typeof item === 'object' && item !== null && 'msg' in item
              ? String((item as { msg: unknown }).msg)
              : String(item);
          return message.replace(/^Value error,\s*/, '');
        })
        .join('; ');
    }
    if (axiosError.request && !axiosError.response) {
      const target = import.meta.env.VITE_API_URL || '/api';
      return target.startsWith('/')
        ? 'Cannot reach the server. Make sure the backend is running on port 8000.'
        : `Cannot reach the server. Make sure the API is reachable at ${target}`;
    }
  }
  return 'Something went wrong. Please try again.';
}
