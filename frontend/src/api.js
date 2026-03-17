function normalizeHost(hostname) {
  return hostname || "localhost";
}

export function backendBaseUrl() {
  const envBackendBaseUrl = import.meta.env.VITE_BACKEND_BASE_URL;
  if (envBackendBaseUrl) {
    return envBackendBaseUrl;
  }

  const host = normalizeHost(window.location.hostname);
  const proto = window.location.protocol || "http:";

  if (host === "localhost" || host === "127.0.0.1") {
    return "http://localhost:8200";
  }

  if (host.endsWith(".local") || host.endsWith(".dev")) {
    if (host.startsWith("api-")) {
      return `${proto}//${host}`;
    }
    return `${proto}//api-${host}`;
  }

  return "http://localhost:8200";
}

export async function fetchJson(path, options = {}) {
  const url = `${backendBaseUrl()}${path}`;
  const response = await fetch(url, {
    headers: {
      "Content-Type": "application/json",
      ...(options.headers || {})
    },
    ...options
  });

  const contentType = response.headers.get("content-type") || "";
  let body;
  try {
    body = contentType.includes("application/json") ? await response.json() : null;
  } catch (_) {
    body = null;
  }

  if (!response.ok) {
    const detail = body?.detail || body?.error || `Request failed: ${response.status}`;
    throw new Error(detail);
  }

  if (body === null) {
    throw new Error(
      `Expected JSON response from ${url}, but received '${contentType || "unknown"}'. ` +
      "Check backend routing and container status."
    );
  }

  return body;
}
