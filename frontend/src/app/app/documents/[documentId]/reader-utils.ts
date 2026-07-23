import type { TimingMap } from "@/lib/api";

export const getCurrentSegmentIndex = (
  segments: TimingMap["segments"],
  currentTimeMs: number,
) => {
  const activeIndex = segments.findIndex(
    (segment) =>
      currentTimeMs >= segment.start_ms && currentTimeMs < segment.end_ms,
  );
  if (activeIndex >= 0) return activeIndex;
  const lastSegment = segments.at(-1);
  if (lastSegment && currentTimeMs >= lastSegment.end_ms) {
    return segments.length - 1;
  }
  return -1;
};

export const getReadingTitle = (
  metadata: Record<string, unknown>,
  fallback: string,
) => {
  for (const key of ["title", "file_name", "filename"]) {
    const value = metadata[key];
    if (typeof value === "string" && value.trim()) return value;
  }
  return fallback;
};

export const getMetadataDurationMs = (metadata: Record<string, unknown>) => {
  const value = metadata.duration_ms;
  return typeof value === "number" && Number.isFinite(value) ? value : 0;
};
