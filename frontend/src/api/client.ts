import axios, { AxiosError, type AxiosInstance, type InternalAxiosRequestConfig } from "axios";

// ============================================================
// Axios client with JWT auth, refresh-token rotation, and
// global error normalisation.
// ============================================================

const BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000/api/v1";

const ACCESS_TOKEN_KEY = "nume.access";
const REFRESH_TOKEN_KEY = "nume.refresh";

export const apiClient: AxiosInstance = axios.create({
  baseURL: BASE_URL,
  timeout: 30_000,
  headers: { "Content-Type": "application/json" },
});

// --------------------------------------------------------------------------- //
// Token helpers
// --------------------------------------------------------------------------- //
export const tokenStorage = {
  getAccess(): string | null {
    return localStorage.getItem(ACCESS_TOKEN_KEY);
  },
  getRefresh(): string | null {
    return localStorage.getItem(REFRESH_TOKEN_KEY);
  },
  set(access: string, refresh: string): void {
    localStorage.setItem(ACCESS_TOKEN_KEY, access);
    localStorage.setItem(REFRESH_TOKEN_KEY, refresh);
  },
  clear(): void {
    localStorage.removeItem(ACCESS_TOKEN_KEY);
    localStorage.removeItem(REFRESH_TOKEN_KEY);
  },
};

// --------------------------------------------------------------------------- //
// Request interceptor — attach Bearer token
// --------------------------------------------------------------------------- //
apiClient.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    const token = tokenStorage.getAccess();
    if (token && !config.headers.Authorization) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (err) => Promise.reject(err)
);

// --------------------------------------------------------------------------- //
// Response interceptor — auto-refresh on 401
// --------------------------------------------------------------------------- //
let isRefreshing = false;
let refreshSubscribers: Array<(token: string | null) => void> = [];

function subscribeTokenRefresh(cb: (token: string | null) => void) {
  refreshSubscribers.push(cb);
}

function onRefreshed(token: string | null) {
  refreshSubscribers.forEach((cb) => cb(token));
  refreshSubscribers = [];
}

async function doRefresh(): Promise<string | null> {
  const refresh = tokenStorage.getRefresh();
  if (!refresh) return null;
  try {
    // Use a bare axios call so we don't recurse into the interceptor
    const res = await axios.post(`${BASE_URL}/auth/refresh`, { refresh_token: refresh });
    const { access_token, refresh_token } = res.data;
    tokenStorage.set(access_token, refresh_token);
    return access_token;
  } catch {
    tokenStorage.clear();
    return null;
  }
}

apiClient.interceptors.response.use(
  (res) => res,
  async (error: AxiosError) => {
    const original = error.config as InternalAxiosRequestConfig & { _retry?: boolean };

    // If 401 and not from /auth/* endpoints, try refresh
    if (
      error.response?.status === 401 &&
      original &&
      !original._retry &&
      !original.url?.includes("/auth/login") &&
      !original.url?.includes("/auth/refresh") &&
      !original.url?.includes("/auth/register")
    ) {
      // If already refreshing, queue this request
      if (isRefreshing) {
        return new Promise((resolve, reject) => {
          subscribeTokenRefresh((token) => {
            if (!token) return reject(error);
            original.headers!.Authorization = `Bearer ${token}`;
            resolve(apiClient(original));
          });
        });
      }

      original._retry = true;
      isRefreshing = true;
      try {
        const newToken = await doRefresh();
        isRefreshing = false;
        onRefreshed(newToken);
        if (!newToken) {
          // Refresh failed — kick to login
          tokenStorage.clear();
          window.dispatchEvent(new CustomEvent("nume:unauthorized"));
          return Promise.reject(error);
        }
        original.headers!.Authorization = `Bearer ${newToken}`;
        return apiClient(original);
      } catch (err) {
        isRefreshing = false;
        onRefreshed(null);
        tokenStorage.clear();
        window.dispatchEvent(new CustomEvent("nume:unauthorized"));
        return Promise.reject(err);
      }
    }

    // Surface a normalised error
    return Promise.reject(error);
  }
);

// --------------------------------------------------------------------------- //
// Error normalisation helper
// --------------------------------------------------------------------------- //
export interface ApiError {
  status: number;
  code: string;
  message: string;
  details?: unknown;
  raw: AxiosError;
}

export function normalizeError(err: unknown): ApiError {
  if (axios.isAxiosError(err)) {
    const data = (err.response?.data as any)?.error ?? (err.response?.data as any);
    return {
      status: err.response?.status ?? 0,
      code: data?.code ?? "network_error",
      message: data?.message ?? err.message ?? "Network error",
      details: data?.details,
      raw: err,
    };
  }
  return {
    status: 0,
    code: "unknown",
    message: (err as Error)?.message ?? "Unknown error",
    raw: err as any,
  };
}
