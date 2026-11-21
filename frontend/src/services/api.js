import { getPortalConfig } from "../utils/portalConfig";

const BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:5000/api";

export async function apiRequest(endpoint, options = {}) {
  // sessionStorage keeps auth isolated per browser tab and per port
  const token = sessionStorage.getItem("blood_token");
  const headers = { ...options.headers };

  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  // Handle FormData vs JSON payloads
  if (!(options.body instanceof FormData) && !headers["Content-Type"]) {
    headers["Content-Type"] = "application/json";
  }

  const config = {
    ...options,
    headers,
  };

  const url = `${BASE_URL}${endpoint.startsWith("/") ? endpoint : `/${endpoint}`}`;
  const response = await fetch(url, config);
  const contentType = response.headers.get("content-type");

  let data;
  if (contentType && contentType.includes("application/json")) {
    data = await response.json();
  } else {
    const text = await response.text();
    data = { message: text };
  }

  if (!response.ok) {
    const errorMessage = data?.error || data?.message || `HTTP error ${response.status}`;
    if (response.status === 401) {
      sessionStorage.removeItem("blood_token");
      sessionStorage.removeItem("blood_user");
      const portal = getPortalConfig();
      if (portal.isDirectAdmin) {
        if (!endpoint.includes("/auth/admin-portal")) {
          window.location.href = "/admin/dashboard";
        }
      } else if (!window.location.pathname.includes("/login")) {
        window.location.href = "/login?session_expired=true";
      }
    }
    throw new Error(errorMessage);
  }

  return data;
}

export const api = {
  get: (endpoint, options = {}) => apiRequest(endpoint, { ...options, method: "GET" }),
  post: (endpoint, body, options = {}) =>
    apiRequest(endpoint, {
      ...options,
      method: "POST",
      body: body instanceof FormData ? body : JSON.stringify(body),
    }),
  put: (endpoint, body, options = {}) =>
    apiRequest(endpoint, {
      ...options,
      method: "PUT",
      body: body instanceof FormData ? body : JSON.stringify(body),
    }),
  patch: (endpoint, body, options = {}) =>
    apiRequest(endpoint, {
      ...options,
      method: "PATCH",
      body: body instanceof FormData ? body : JSON.stringify(body),
    }),
  delete: (endpoint, options = {}) => apiRequest(endpoint, { ...options, method: "DELETE" }),
  fetchDocumentBlob: async (relativeDocPath) => {
    if (!relativeDocPath) {
      throw new Error("No document path provided.");
    }
    const cleanPath = relativeDocPath.replace(/\\/g, "/").replace(/^\/+/, "");
    const withoutUploads = cleanPath.startsWith("uploads/")
      ? cleanPath.slice("uploads/".length)
      : cleanPath;
    const segments = withoutUploads.split("/").filter(Boolean);
    if (segments.length < 2) {
      throw new Error("Invalid document path format.");
    }
    const category = encodeURIComponent(segments[0]);
    const filename = encodeURIComponent(segments.slice(1).join("/"));
    const url = `${BASE_URL}/requests/documents/${category}/${filename}`;

    const token = sessionStorage.getItem("blood_token");
    const headers = token ? { Authorization: `Bearer ${token}` } : {};
    const response = await fetch(url, { headers });

    if (!response.ok) {
      let errorMessage = `Unable to load document (HTTP ${response.status})`;
      try {
        const errJson = await response.json();
        errorMessage = errJson?.error || errJson?.message || errorMessage;
      } catch {
        // Non-JSON response body
      }
      throw new Error(errorMessage);
    }

    const blob = await response.blob();
    const blobUrl = URL.createObjectURL(blob);
    return {
      blobUrl,
      mimeType: blob.type || "application/octet-stream",
      filename: segments[segments.length - 1],
    };
  },
};
