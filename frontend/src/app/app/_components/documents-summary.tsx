import { dictionary } from "@/i18n/dictionaries";
import type { Reading } from "@/lib/api";
import { getReadingStatusGroup, ReadingStatusGroup } from "@/lib/reading";

const copy = dictionary.app.documents.summary;

type DocumentsSummaryProps = {
  isLoading: boolean;
  readings: Reading[];
};

export const DocumentsSummary = ({
  isLoading,
  readings,
}: DocumentsSummaryProps) => {
  const processingCount = readings.filter(
    (reading) =>
      getReadingStatusGroup(reading.status) === ReadingStatusGroup.processing,
  ).length;
  const readyCount = readings.filter(
    (reading) =>
      getReadingStatusGroup(reading.status) === ReadingStatusGroup.ready,
  ).length;
  const exportCount = readings.reduce(
    (count, reading) =>
      count +
      Number(Boolean(reading.original_text_key)) +
      Number(Boolean(reading.corrected_text_key)) +
      Number(Boolean(reading.recording_key)),
    0,
  );

  return (
    <section aria-label={copy.label}>
      <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
        <SummaryItem
          label={copy.loaded}
          value={isLoading ? undefined : readings.length}
        />
        <SummaryItem
          label={copy.processing}
          value={isLoading ? undefined : processingCount}
        />
        <SummaryItem
          label={copy.ready}
          value={isLoading ? undefined : readyCount}
        />
        <SummaryItem
          label={copy.exports}
          value={isLoading ? undefined : exportCount}
        />
      </div>
      <p className="mt-2 text-muted-foreground text-xs">{copy.scope}</p>
    </section>
  );
};

const SummaryItem = ({ label, value }: { label: string; value?: number }) => (
  <div className="rounded-lg border border-border bg-background p-4">
    <p className="text-muted-foreground text-sm">{label}</p>
    <p className="mt-1 font-semibold text-2xl tabular-nums">
      {value ?? "\u2026"}
    </p>
  </div>
);
