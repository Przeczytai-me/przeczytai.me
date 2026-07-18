import { bypass, HttpResponse, http } from "msw";
import type { Reading, ReadingListResponse } from "@/lib/api";
import {
  defaultUserSettings,
  mockOriginalText,
  mockTimingMapSegments,
  mockTtsOptions,
} from "./data";
import {
  createRetryJob,
  getRetryJobs,
  getUserSettings,
  saveUserSettings,
} from "./store";
import type {
  AbbreviationReading,
  MockReadingCreateRequest,
  ProcessingJob,
  ProcessingJobListResponse,
  TimingMap,
  UserSettings,
} from "./types";

const MAX_ABBREVIATION_READINGS = 50;
const MAX_ABBREVIATION_LENGTH = 80;
const MAX_READING_LENGTH = 240;

export const handlers = [
  http.post("/api/v1/readings", handleCreateReading),
  http.get("/api/v1/jobs", handleListJobs),
  http.post("/api/v1/readings/:readingId/retry", handleRetryReading),
  http.get("/api/v1/readings/:readingId/original-text", handleOriginalText),
  http.get("/api/v1/readings/:readingId/timing-map", handleTimingMap),
  http.get("/api/v1/settings", () => HttpResponse.json(getUserSettings())),
  http.put("/api/v1/settings", handleSaveSettings),
  http.get("/api/v1/tts-options", () => HttpResponse.json(mockTtsOptions)),
];

async function handleCreateReading({ request }: { request: Request }) {
  const originalRequest = request.clone();
  let body: MockReadingCreateRequest;

  try {
    body = (await request.json()) as MockReadingCreateRequest;
  } catch {
    return validationError("Request body must be valid JSON");
  }

  const parsedAbbreviations = parseAbbreviationReadings(
    body.abbreviation_readings,
  );
  if (!parsedAbbreviations.ok) {
    return validationError(parsedAbbreviations.message);
  }

  if (body.abbreviation_readings === undefined) {
    return fetch(bypass(originalRequest));
  }

  const headers = new Headers(request.headers);
  headers.delete("content-length");
  const upstreamBody = {
    original_text: body.original_text,
    vendor: body.vendor,
    voice: body.voice,
  };
  const upstreamRequest = new Request(request.url, {
    method: "POST",
    body: JSON.stringify(upstreamBody),
    headers,
    credentials: request.credentials,
    redirect: request.redirect,
  });
  const upstreamResponse = await fetch(bypass(upstreamRequest));

  if (!upstreamResponse.ok) {
    return upstreamResponse;
  }

  const reading = (await upstreamResponse.json()) as Reading;
  return HttpResponse.json(
    {
      ...reading,
      metadata: {
        ...reading.metadata,
        abbreviation_readings: parsedAbbreviations.value,
      },
    },
    { status: upstreamResponse.status },
  );
}

async function handleListJobs({ request }: { request: Request }) {
  const requestUrl = new URL(request.url);
  const limit = clamp(
    Number(requestUrl.searchParams.get("limit") ?? 20),
    1,
    50,
  );
  const readingsUrl = new URL("/api/v1/readings", requestUrl.origin);
  readingsUrl.searchParams.set("limit", String(limit));
  const cursor = requestUrl.searchParams.get("cursor");
  if (cursor) readingsUrl.searchParams.set("cursor", cursor);

  const readingsResponse = await fetch(
    bypass(createAuthenticatedGetRequest(readingsUrl, request)),
  );
  if (!readingsResponse.ok) return readingsResponse;

  const readings = (await readingsResponse.json()) as ReadingListResponse;
  const jobs = readings.items.map(readingToJob);
  if (!cursor) jobs.unshift(...getRetryJobs());
  jobs.sort((left, right) => right.created_at.localeCompare(left.created_at));

  const response: ProcessingJobListResponse = {
    items: jobs,
    next_cursor: readings.next_cursor,
  };
  return HttpResponse.json(response);
}

async function handleRetryReading({
  params,
  request,
}: {
  params: Record<string, string | readonly string[] | undefined>;
  request: Request;
}) {
  const readingId = singleParam(params.readingId);
  const readingResponse = await fetchRealReading(readingId, request);
  if (!readingResponse.ok) return readingResponse;

  const job = createRetryJob(readingId);
  return HttpResponse.json({ job }, { status: 202 });
}

async function handleOriginalText({
  params,
  request,
}: {
  params: Record<string, string | readonly string[] | undefined>;
  request: Request;
}) {
  const readingId = singleParam(params.readingId);
  const readingResponse = await fetchRealReading(readingId, request);
  if (!readingResponse.ok) return readingResponse;

  return HttpResponse.text(mockOriginalText, {
    headers: {
      "Content-Disposition": `attachment; filename="${safeFilename(readingId)}-original.txt"`,
      "Content-Type": "text/plain; charset=utf-8",
    },
  });
}

async function handleTimingMap({
  params,
  request,
}: {
  params: Record<string, string | readonly string[] | undefined>;
  request: Request;
}) {
  const readingId = singleParam(params.readingId);
  const readingResponse = await fetchRealReading(readingId, request);
  if (!readingResponse.ok) return readingResponse;

  const reading = (await readingResponse.json()) as Reading;
  if (reading.status !== "completed" || !reading.recording_key) {
    return HttpResponse.json(
      {
        error: {
          code: "timing_map_not_ready",
          message: "Timing map is not available until processing completes",
        },
      },
      { status: 409 },
    );
  }

  const timingMap: TimingMap = {
    reading_id: readingId,
    duration_ms: 14_200,
    segments: mockTimingMapSegments,
  };
  return HttpResponse.json(timingMap);
}

async function handleSaveSettings({ request }: { request: Request }) {
  let body: unknown;
  try {
    body = await request.json();
  } catch {
    return validationError("Request body must be valid JSON");
  }

  const parsedSettings = parseSettings(body);
  if (!parsedSettings.ok) return validationError(parsedSettings.message);
  return HttpResponse.json(saveUserSettings(parsedSettings.value));
}

async function fetchRealReading(readingId: string, request: Request) {
  const url = new URL(
    `/api/v1/readings/${encodeURIComponent(readingId)}`,
    request.url,
  );
  return fetch(bypass(createAuthenticatedGetRequest(url, request)));
}

function createAuthenticatedGetRequest(url: URL, request: Request) {
  return new Request(url, {
    method: "GET",
    headers: request.headers,
    credentials: request.credentials,
    redirect: request.redirect,
  });
}

function readingToJob(reading: Reading): ProcessingJob {
  const state = readingJobState(reading);
  return {
    id: `reading-${reading.id}-attempt-1`,
    reading_id: reading.id,
    attempt: 1,
    ...state,
    error:
      state.status === "failed"
        ? {
            code: "processing_failed",
            message: "Nie udało się rozpocząć przetwarzania",
            step: "uploaded",
          }
        : null,
    created_at: reading.created_at,
    updated_at: reading.updated_at,
  };
}

function readingJobState(
  reading: Reading,
): Pick<ProcessingJob, "status" | "progress" | "current_step"> {
  if (reading.status === "completed") {
    return {
      status: "ready",
      progress: 100,
      current_step: "Nagranie jest gotowe",
    };
  }
  if (reading.status === "failed" || reading.status === "failed_to_start") {
    return {
      status: "failed",
      progress: null,
      current_step: "Przetwarzanie nie powiodło się",
    };
  }
  return {
    status: "generating_audio",
    progress: 75,
    current_step: "Generowanie nagrania",
  };
}

function parseAbbreviationReadings(
  value: unknown,
): { ok: true; value: AbbreviationReading[] } | { ok: false; message: string } {
  if (value === undefined) return { ok: true, value: [] };
  if (!Array.isArray(value)) {
    return { ok: false, message: "abbreviation_readings must be an array" };
  }
  if (value.length > MAX_ABBREVIATION_READINGS) {
    return {
      ok: false,
      message: `abbreviation_readings supports at most ${MAX_ABBREVIATION_READINGS} entries`,
    };
  }

  const normalized: AbbreviationReading[] = [];
  const seen = new Set<string>();
  for (const entry of value) {
    if (!isRecord(entry)) {
      return {
        ok: false,
        message: "Each abbreviation reading must be an object",
      };
    }
    const abbreviation =
      typeof entry.abbreviation === "string" ? entry.abbreviation.trim() : "";
    const readAs =
      typeof entry.read_as === "string" ? entry.read_as.trim() : "";
    if (!abbreviation || !readAs) {
      return {
        ok: false,
        message: "Each abbreviation reading requires abbreviation and read_as",
      };
    }
    if (
      abbreviation.length > MAX_ABBREVIATION_LENGTH ||
      readAs.length > MAX_READING_LENGTH
    ) {
      return { ok: false, message: "Abbreviation reading is too long" };
    }
    const key = abbreviation.toLocaleLowerCase("pl-PL");
    if (seen.has(key)) {
      return { ok: false, message: `Duplicate abbreviation: ${abbreviation}` };
    }
    seen.add(key);
    normalized.push({ abbreviation, read_as: readAs });
  }

  return { ok: true, value: normalized };
}

function parseSettings(
  value: unknown,
): { ok: true; value: UserSettings } | { ok: false; message: string } {
  if (!isRecord(value)) {
    return { ok: false, message: "Settings must be an object" };
  }

  const current = getUserSettings();
  const readingModel = defaultedString(
    value.reading_model,
    current.reading_model,
    defaultUserSettings.reading_model,
  );
  if (!readingModel.ok) return readingModel;
  if (!mockTtsOptions.models.some((model) => model.id === readingModel.value)) {
    return { ok: false, message: "Unsupported reading_model" };
  }

  const fallbackModel = nullableModel(
    value.fallback_model,
    current.fallback_model,
  );
  if (!fallbackModel.ok) return fallbackModel;
  if (
    fallbackModel.value !== null &&
    !mockTtsOptions.models.some((model) => model.id === fallbackModel.value)
  ) {
    return { ok: false, message: "Unsupported fallback_model" };
  }

  const voice = defaultedString(
    value.voice,
    current.voice,
    defaultUserSettings.voice,
  );
  if (!voice.ok) return voice;
  if (!mockTtsOptions.voices.some((option) => option.id === voice.value)) {
    return { ok: false, message: "Unsupported voice" };
  }

  const pronunciationStyle = defaultedString(
    value.pronunciation_style,
    current.pronunciation_style,
    defaultUserSettings.pronunciation_style,
  );
  if (!pronunciationStyle.ok) return pronunciationStyle;
  if (
    !mockTtsOptions.pronunciation_styles.some(
      (style) => style.id === pronunciationStyle.value,
    )
  ) {
    return { ok: false, message: "Unsupported pronunciation_style" };
  }

  const playbackSpeed = defaultedNumber(
    value.playback_speed,
    current.playback_speed,
    defaultUserSettings.playback_speed,
  );
  if (!playbackSpeed.ok) return playbackSpeed;
  if (playbackSpeed.value < 0.5 || playbackSpeed.value > 2) {
    return { ok: false, message: "playback_speed must be between 0.5 and 2" };
  }

  const sentenceHighlighting = defaultedBoolean(
    value.sentence_highlighting,
    current.sentence_highlighting,
    defaultUserSettings.sentence_highlighting,
  );
  if (!sentenceHighlighting.ok) return sentenceHighlighting;

  const abbreviationInput =
    value.custom_abbreviation_readings === null
      ? defaultUserSettings.custom_abbreviation_readings
      : (value.custom_abbreviation_readings ??
        current.custom_abbreviation_readings);
  const abbreviations = parseAbbreviationReadings(abbreviationInput);
  if (!abbreviations.ok) return abbreviations;

  const exportsResult = parseExports(value.exports, current);
  if (!exportsResult.ok) return exportsResult;

  return {
    ok: true,
    value: {
      reading_model: readingModel.value,
      fallback_model: fallbackModel.value,
      voice: voice.value,
      pronunciation_style: pronunciationStyle.value,
      playback_speed: playbackSpeed.value,
      sentence_highlighting: sentenceHighlighting.value,
      custom_abbreviation_readings: abbreviations.value,
      exports: exportsResult.value,
      updated_at: new Date().toISOString(),
    },
  };
}

function parseExports(
  value: unknown,
  current: UserSettings,
):
  | { ok: true; value: UserSettings["exports"] }
  | { ok: false; message: string } {
  if (value === undefined) return { ok: true, value: current.exports };
  if (value === null) {
    return { ok: true, value: defaultUserSettings.exports };
  }
  if (!isRecord(value)) {
    return { ok: false, message: "exports must be an object" };
  }

  const filename = defaultedString(
    value.filename_pattern,
    current.exports.filename_pattern,
    defaultUserSettings.exports.filename_pattern,
  );
  if (!filename.ok) return filename;
  const quality = defaultedString(
    value.mp3_quality,
    current.exports.mp3_quality,
    defaultUserSettings.exports.mp3_quality,
  );
  if (!quality.ok) return quality;
  if (!new Set(["standard", "high"]).has(quality.value)) {
    return { ok: false, message: "Unsupported mp3_quality" };
  }
  const format = defaultedString(
    value.text_format,
    current.exports.text_format,
    defaultUserSettings.exports.text_format,
  );
  if (!format.ok) return format;
  if (!new Set(["md", "txt", "ssml"]).has(format.value)) {
    return { ok: false, message: "Unsupported text_format" };
  }

  return {
    ok: true,
    value: {
      filename_pattern: filename.value,
      mp3_quality: quality.value,
      text_format: format.value,
    },
  };
}

function defaultedString(
  value: unknown,
  current: string,
  fallback: string,
): { ok: true; value: string } | { ok: false; message: string } {
  if (value === undefined) return { ok: true, value: current };
  if (value === null) return { ok: true, value: fallback };
  if (typeof value !== "string" || !value.trim()) {
    return { ok: false, message: "Setting must be a non-empty string" };
  }
  return { ok: true, value: value.trim() };
}

function nullableModel(
  value: unknown,
  current: string | null,
): { ok: true; value: string | null } | { ok: false; message: string } {
  if (value === undefined) return { ok: true, value: current };
  if (value === null) return { ok: true, value: null };
  if (typeof value !== "string" || !value.trim()) {
    return { ok: false, message: "fallback_model must be a string or null" };
  }
  return { ok: true, value: value.trim() };
}

function defaultedNumber(
  value: unknown,
  current: number,
  fallback: number,
): { ok: true; value: number } | { ok: false; message: string } {
  if (value === undefined) return { ok: true, value: current };
  if (value === null) return { ok: true, value: fallback };
  if (typeof value !== "number" || !Number.isFinite(value)) {
    return { ok: false, message: "Setting must be a finite number" };
  }
  return { ok: true, value };
}

function defaultedBoolean(
  value: unknown,
  current: boolean,
  fallback: boolean,
): { ok: true; value: boolean } | { ok: false; message: string } {
  if (value === undefined) return { ok: true, value: current };
  if (value === null) return { ok: true, value: fallback };
  if (typeof value !== "boolean") {
    return { ok: false, message: "Setting must be a boolean" };
  }
  return { ok: true, value };
}

function validationError(message: string) {
  return HttpResponse.json(
    { error: { code: "validation_error", message } },
    { status: 422 },
  );
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function singleParam(value: string | readonly string[] | undefined) {
  return Array.isArray(value) ? (value[0] ?? "") : (value ?? "");
}

function safeFilename(value: string) {
  return value.replace(/[^a-zA-Z0-9_-]/g, "-");
}

function clamp(value: number, minimum: number, maximum: number) {
  if (!Number.isFinite(value)) return minimum;
  return Math.min(Math.max(Math.trunc(value), minimum), maximum);
}
