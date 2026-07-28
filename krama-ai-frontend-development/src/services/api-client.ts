/**
 * Isolated HTTP client for the Krama AI FastAPI backend.
 *
 * Handles auth bearer tokens, organization headers (X-Organization-ID),
 * error normalization, and 401 session expiration handling.
 */

export const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "/api/v1";

export class ApiError extends Error {
  constructor(
    public readonly status: number,
    public readonly detail: string,
    public readonly requestId?: string
  ) {
    super(`API ${status}: ${detail}`);
    this.name = "ApiError";
  }
}

// Token & Org storage helpers
export const authTokens = {
  getAccessToken(): string | null {
    if (typeof window === "undefined") return null;
    return localStorage.getItem("krama_access_token");
  },
  getRefreshToken(): string | null {
    if (typeof window === "undefined") return null;
    return localStorage.getItem("krama_refresh_token");
  },
  getOrganizationId(): string {
    if (typeof window === "undefined") return "00000000-0000-0000-0000-000000000001";
    return localStorage.getItem("krama_org_id") || "00000000-0000-0000-0000-000000000001";
  },
  setTokens(accessToken: string, refreshToken?: string) {
    if (typeof window === "undefined") return;
    localStorage.setItem("krama_access_token", accessToken);
    if (refreshToken) {
      localStorage.setItem("krama_refresh_token", refreshToken);
    }
  },
  setOrganizationId(orgId: string) {
    if (typeof window === "undefined") return;
    localStorage.setItem("krama_org_id", orgId);
  },
  clearTokens() {
    if (typeof window === "undefined") return;
    localStorage.removeItem("krama_access_token");
    localStorage.removeItem("krama_refresh_token");
  },
};

interface RequestOptions extends Omit<RequestInit, "body"> {
  body?: unknown;
  /** Query string parameters, serialized automatically. */
  params?: Record<string, string | number | boolean | undefined>;
}

async function request<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const { body, params, headers, ...init } = options;

  const url = new URL(
    path.startsWith("http") ? path : `${API_BASE_URL}${path}`,
    typeof window === "undefined" ? "http://localhost:8000" : window.location.origin
  );

  if (params) {
    for (const [key, value] of Object.entries(params)) {
      if (value !== undefined) url.searchParams.set(key, String(value));
    }
  }

  const token = authTokens.getAccessToken();
  const orgId = authTokens.getOrganizationId();

  const reqHeaders: Record<string, string> = {
    "X-Organization-ID": orgId,
    ...(headers as Record<string, string>),
  };

  if (token) {
    reqHeaders["Authorization"] = `Bearer ${token}`;
  }

  if (body !== undefined && !(body instanceof FormData)) {
    reqHeaders["Content-Type"] = "application/json";
  }

  const response = await fetch(url.toString(), {
    ...init,
    headers: reqHeaders,
    body: body instanceof FormData ? body : body !== undefined ? JSON.stringify(body) : undefined,
  });

  if (response.status === 401) {
    // Session expired handling
    if (typeof window !== "undefined" && !window.location.pathname.startsWith("/login")) {
      authTokens.clearTokens();
    }
  }

  if (!response.ok) {
    const detail = await response
      .json()
      .then((data: { detail?: string; message?: string }) => data.detail || data.message || response.statusText)
      .catch(() => response.statusText);
    throw new ApiError(response.status, detail, response.headers.get("x-request-id") ?? undefined);
  }

  if (response.status === 204) return undefined as T;
  return response.json() as Promise<T>;
}

export const apiClient = {
  get: <T>(path: string, options?: RequestOptions) =>
    request<T>(path, { ...options, method: "GET" }),
  post: <T>(path: string, body?: unknown, options?: RequestOptions) =>
    request<T>(path, { ...options, method: "POST", body }),
  put: <T>(path: string, body?: unknown, options?: RequestOptions) =>
    request<T>(path, { ...options, method: "PUT", body }),
  patch: <T>(path: string, body?: unknown, options?: RequestOptions) =>
    request<T>(path, { ...options, method: "PATCH", body }),
  delete: <T>(path: string, options?: RequestOptions) =>
    request<T>(path, { ...options, method: "DELETE" }),
  upload: <T>(path: string, formData: FormData, options?: RequestOptions) =>
    request<T>(path, { ...options, method: "POST", body: formData }),
};
