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
  abbreviation_readings?: Array<{
    abbreviation: string;
    read_as: string;
  }> | null;
};

export type TimingMap = {
  reading_id: string;
  duration_ms: number;
  segments: Array<{
    id: string;
    text: string;
    paragraph_index: number;
    start_ms: number;
    end_ms: number;
  }>;
};

export type ProcessingJob = {
  id: string;
  reading_id: string;
  attempt: number;
  status: string;
  progress: number | null;
  current_step: string;
  error: {
    code: string;
    message: string;
    step: string;
  } | null;
  created_at: string;
  updated_at: string;
};

export class ApiError extends Error {
  status: number;

  constructor(status: number, body: string) {
    super(`API ${status}: ${body}`);
    this.name = "ApiError";
    this.status = status;
  }
}

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
    throw new ApiError(res.status, text);
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

export async function getReading(id: string): Promise<Reading> {
  const res = await apiFetch(`/api/v1/readings/${id}`);
  return res.json();
}

export async function getOriginalText(id: string): Promise<string> {
  const res = await apiFetch(`/api/v1/readings/${id}/original-text`);
  return res.text();
}

export async function getTimingMap(id: string): Promise<TimingMap | null> {
  try {
    const res = await apiFetch(`/api/v1/readings/${id}/timing-map`);
    return res.json();
  } catch (error) {
    if (
      error instanceof ApiError &&
      (error.status === 404 || error.status === 409)
    ) {
      return null;
    }
    throw error;
  }
}

export async function retryReading(id: string): Promise<ProcessingJob> {
  const res = await apiFetch(`/api/v1/readings/${id}/retry`, {
    method: "POST",
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
  const responseFilename =
    filenameFromContentDisposition(res.headers.get("content-disposition")) ??
    filename;
  const contentType = res.headers.get("content-type") ?? "";
  if (contentType.includes("application/json")) {
    const data = await res.json();
    const url = data?.url ?? data?.download_url ?? data?.presigned_url;
    if (url) {
      triggerDownload(url, responseFilename);
      return;
    }
    const blob = new Blob([JSON.stringify(data, null, 2)], {
      type: "application/json",
    });
    triggerDownload(URL.createObjectURL(blob), responseFilename);
  } else {
    const blob = await res.blob();
    triggerDownload(URL.createObjectURL(blob), responseFilename);
  }
}

function filenameFromContentDisposition(value: string | null) {
  if (!value) return null;
  const utf8Match = value.match(/filename\*=UTF-8''([^;]+)/i);
  if (utf8Match) {
    try {
      return decodeURIComponent(utf8Match[1]);
    } catch {
      return utf8Match[1];
    }
  }
  return value.match(/filename="?([^";]+)"?/i)?.[1] ?? null;
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
