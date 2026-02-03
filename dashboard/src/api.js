const API_BASE = import.meta.env.VITE_API_BASE || "http://localhost:8001";

export async function getOverview() {
  const r = await fetch(`${API_BASE}/stats/overview`);
  if (!r.ok) throw new Error("Error GET /stats/overview");
  return r.json();
}

export async function getApis() {
  const r = await fetch(`${API_BASE}/apis`);
  if (!r.ok) throw new Error("Error GET /apis");
  return r.json();
}

export async function addApi(name, url) {
  const r = await fetch(`${API_BASE}/apis`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ name, url })
  });
  if (!r.ok) {
    const body = await r.json().catch(() => ({}));
    throw new Error(body?.detail || "Error POST /apis");
  }
  return r.json();
}

export async function getLogs(apiId, limit = 200) {
  const r = await fetch(`${API_BASE}/apis/${apiId}/logs?limit=${limit}`);
  if (!r.ok) throw new Error("Error GET /apis/{id}/logs");
  return r.json();
}

export async function deleteApi(apiId) {
  const r = await fetch(`${API_BASE}/apis/${apiId}`, { method: "DELETE" });
  if (!r.ok) throw new Error("Error DELETE /apis/{id}");
  return r.json();
}

export async function uploadApisTxt(file) {
  const form = new FormData();
  form.append("file", file);

  const r = await fetch(`${API_BASE}/apis/upload`, {
    method: "POST",
    body: form
  });

  const body = await r.json().catch(() => ({}));
  if (!r.ok) {
    throw new Error(body?.detail?.message || body?.detail || "Error POST /apis/upload");
  }
  return body;
}
