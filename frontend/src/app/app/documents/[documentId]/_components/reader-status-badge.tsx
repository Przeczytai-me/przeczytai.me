import { dictionary } from "@/i18n/dictionaries";
import { cn } from "@/lib/utils";

const labels = dictionary.app.reader.details.statuses;

type ReaderStatusBadgeProps = {
  status: string;
};

export const ReaderStatusBadge = ({ status }: ReaderStatusBadgeProps) => {
  const failed = status === "failed" || status === "failed_to_start";
  const label =
    status === "completed"
      ? labels.completed
      : status === "failed_to_start"
        ? labels.failedToStart
        : failed
          ? labels.failed
          : labels.processing;

  return (
    <span
      className={cn(
        "inline-flex rounded-full px-2 py-0.5 font-medium text-xs",
        status === "completed"
          ? "bg-emerald-100 text-emerald-800"
          : failed
            ? "bg-destructive/10 text-destructive"
            : "bg-amber-100 text-amber-800",
      )}
    >
      {label}
    </span>
  );
};
