import { dictionary } from "@/i18n/dictionaries";
import {
  createReadingStatusLabel,
  getReadingStatusGroup,
  ReadingStatusGroup,
} from "@/lib/reading";
import { cn } from "@/lib/utils";

const labels = dictionary.app.reader.details.statuses;
const getStatusLabel = createReadingStatusLabel(labels);

type ReadingStatusBadgeProps = {
  status: string;
};

export const ReadingStatusBadge = ({ status }: ReadingStatusBadgeProps) => {
  const statusGroup = getReadingStatusGroup(status);
  const label = getStatusLabel(status);

  return (
    <span
      className={cn(
        "inline-flex rounded-full px-2 py-0.5 font-medium text-xs",
        statusGroup === ReadingStatusGroup.ready
          ? "bg-emerald-100 text-emerald-800"
          : statusGroup === ReadingStatusGroup.failed
            ? "bg-destructive/10 text-destructive"
            : "bg-amber-100 text-amber-800",
      )}
    >
      {label}
    </span>
  );
};
