import type { Reading } from "@/lib/api";
import {
  getReadingModel,
  getReadingSourceType,
  getReadingStatusGroup,
  getReadingTitle,
  getReadingVoice,
  ReadingStatusGroup,
} from "@/lib/reading";

const POLISH_LOCALE = "pl";

export const DocumentStatusFilter = {
  all: "all",
  failed: ReadingStatusGroup.failed,
  processing: ReadingStatusGroup.processing,
  ready: ReadingStatusGroup.ready,
} as const;

export type DocumentStatusFilter =
  (typeof DocumentStatusFilter)[keyof typeof DocumentStatusFilter];

export const DocumentSort = {
  newest: "newest",
  oldest: "oldest",
  titleAscending: "titleAscending",
  titleDescending: "titleDescending",
} as const;

export type DocumentSort = (typeof DocumentSort)[keyof typeof DocumentSort];

export const filterAndSortReadings = (
  readings: Reading[],
  search: string,
  statusFilter: DocumentStatusFilter,
  sort: DocumentSort,
  titleFallback: (id: string) => string,
) => {
  const normalizedSearch = search.trim().toLocaleLowerCase(POLISH_LOCALE);

  return readings
    .filter((reading) => {
      if (
        statusFilter !== DocumentStatusFilter.all &&
        getReadingStatusGroup(reading.status) !== statusFilter
      ) {
        return false;
      }

      if (!normalizedSearch) return true;

      return [
        getReadingTitle(reading.metadata, titleFallback(reading.id)),
        reading.id,
        getReadingSourceType(reading),
        getReadingVoice(reading),
        getReadingModel(reading),
      ]
        .filter(Boolean)
        .some((value) =>
          value?.toLocaleLowerCase(POLISH_LOCALE).includes(normalizedSearch),
        );
    })
    .toSorted((left, right) => {
      if (sort === DocumentSort.newest || sort === DocumentSort.oldest) {
        const difference =
          new Date(right.created_at).getTime() -
          new Date(left.created_at).getTime();
        return sort === DocumentSort.newest ? difference : -difference;
      }

      const difference = getReadingTitle(
        left.metadata,
        titleFallback(left.id),
      ).localeCompare(
        getReadingTitle(right.metadata, titleFallback(right.id)),
        POLISH_LOCALE,
        { sensitivity: "base" },
      );
      return sort === DocumentSort.titleAscending ? difference : -difference;
    });
};
