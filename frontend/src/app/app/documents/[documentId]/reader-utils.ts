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
