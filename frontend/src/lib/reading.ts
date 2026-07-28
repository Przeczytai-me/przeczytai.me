import type { Reading } from "@/lib/api";

const READING_METADATA_KEYS = {
  duration: "duration_ms",
  model: ["model"],
  sourceType: ["source_type", "file_type"],
  title: ["title", "file_name", "filename"],
  voice: ["voice"],
} as const;

const FILE_EXTENSION = {
  markdown: ".md",
  text: ".txt",
} as const;

const SOURCE_TYPE_LABEL = {
  markdown: "Markdown",
  text: "Tekst",
} as const;

export const ReadingStatus = {
  completed: "completed",
  failed: "failed",
  failedToStart: "failed_to_start",
  generatingAudio: "generating_audio",
  mergingAudio: "merging_audio",
  normalizing: "normalizing",
  processing: "processing",
  uploaded: "uploaded",
} as const;

export type ReadingStatus = (typeof ReadingStatus)[keyof typeof ReadingStatus];

export const ReadingStatusGroup = {
  failed: "failed",
  processing: "processing",
  ready: "ready",
} as const;

export type ReadingStatusGroup =
  (typeof ReadingStatusGroup)[keyof typeof ReadingStatusGroup];

type ReadingStatusLabels = Readonly<{
  completed: string;
  failed: string;
  failedToStart: string;
  processing: string;
}>;

const metadataString = (
  metadata: Record<string, unknown>,
  keys: readonly string[],
) => {
  for (const key of keys) {
    const value = metadata[key];
    if (typeof value === "string" && value.trim()) return value.trim();
  }
  return null;
};

export const getReadingTitle = (
  metadata: Record<string, unknown>,
  fallback: string,
) => metadataString(metadata, READING_METADATA_KEYS.title) ?? fallback;

export const getMetadataDurationMs = (metadata: Record<string, unknown>) => {
  const value = metadata[READING_METADATA_KEYS.duration];
  return typeof value === "number" && Number.isFinite(value) ? value : 0;
};

export const getReadingModel = (reading: Reading) =>
  metadataString(reading.metadata, READING_METADATA_KEYS.model) ??
  reading.vendor;

export const getReadingVoice = (reading: Reading) =>
  metadataString(reading.metadata, READING_METADATA_KEYS.voice) ??
  reading.voice;

export const getReadingSourceType = (reading: Reading) => {
  const metadataType = metadataString(
    reading.metadata,
    READING_METADATA_KEYS.sourceType,
  );
  if (metadataType) return metadataType;

  const extension = getFileExtension(reading.original_text_key);

  if (extension === FILE_EXTENSION.markdown) return SOURCE_TYPE_LABEL.markdown;
  if (extension === FILE_EXTENSION.text) return SOURCE_TYPE_LABEL.text;
  return null;
};

export const getReadingOriginalExtension = (reading: Reading) => {
  const extension = getFileExtension(reading.original_text_key);
  return extension === FILE_EXTENSION.markdown
    ? FILE_EXTENSION.markdown
    : FILE_EXTENSION.text;
};

export const isFailedReading = (status: string) =>
  status === ReadingStatus.failed || status === ReadingStatus.failedToStart;

export const getReadingStatusGroup = (status: string): ReadingStatusGroup => {
  if (status === ReadingStatus.completed) return ReadingStatusGroup.ready;
  if (isFailedReading(status)) return ReadingStatusGroup.failed;
  return ReadingStatusGroup.processing;
};

export const createReadingStatusLabel =
  (labels: ReadingStatusLabels) => (status: string) => {
    if (status === ReadingStatus.completed) return labels.completed;
    if (status === ReadingStatus.failedToStart) return labels.failedToStart;
    if (getReadingStatusGroup(status) === ReadingStatusGroup.failed) {
      return labels.failed;
    }
    return labels.processing;
  };

const getFileExtension = (path: string) =>
  path
    .split("/")
    .at(-1)
    ?.match(/\.[^.]+$/)?.[0]
    ?.toLowerCase();
