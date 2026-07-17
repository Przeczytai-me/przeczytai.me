export type Reading = {
  id: string;
  original_text_key: string;
  corrected_text_key: string | null;
  recording_key: string | null;
  vendor: string | null;
  voice: string | null;
  status: string;
  metadata: Record<string, unknown>;
  char_count: number;
  created_at: string;
  updated_at: string;
};

export type ReadingListResponse = {
  items: Reading[];
  next_cursor: string | null;
};

export type ReadingCreateRequest = {
  original_text: string;
  vendor?: string | null;
  voice?: string | null;
};

async function apiFetch(
  path: string,
  init: { method?: string; body?: string } = {},
) {
  const headers: Record<string, string> = {};
  if (init.body !== undefined) headers["Content-Type"] = "application/json";

  const res = await fetch(path, {
    method: init.method ?? "GET",
    body: init.body,
    headers,
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`API ${res.status}: ${text}`);
  }
  return res;
}

export async function getHealth(): Promise<Record<string, string>> {
  const res = await apiFetch("/api/v1/health");
  return res.json();
}

export async function listReadings(
  limit = 20,
  cursor?: string | null,
): Promise<ReadingListResponse> {
  const params = new URLSearchParams({ limit: String(limit) });
  if (cursor) params.set("cursor", cursor);
  const res = await apiFetch(`/api/v1/readings?${params}`);
  return res.json();
}

export async function createReading(
  body: ReadingCreateRequest,
): Promise<Reading> {
  const res = await apiFetch("/api/v1/readings", {
    method: "POST",
    body: JSON.stringify(body),
  });
  return res.json();
}

export async function deleteReading(id: string): Promise<void> {
  await apiFetch(`/api/v1/readings/${id}`, { method: "DELETE" });
}

export async function downloadFile(
  path: string,
  filename: string,
): Promise<void> {
  const res = await apiFetch(path);
  const contentType = res.headers.get("content-type") ?? "";
  if (contentType.includes("application/json")) {
    const data = await res.json();
    const url = data?.url ?? data?.download_url ?? data?.presigned_url;
    if (url) {
      triggerDownload(url, filename);
      return;
    }
    const blob = new Blob([JSON.stringify(data, null, 2)], {
      type: "application/json",
    });
    triggerDownload(URL.createObjectURL(blob), filename);
  } else {
    const blob = await res.blob();
    triggerDownload(URL.createObjectURL(blob), filename);
  }
}

function triggerDownload(url: string, filename: string) {
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.click();
  if (url.startsWith("blob:")) {
    window.setTimeout(() => URL.revokeObjectURL(url), 0);
  }
}
