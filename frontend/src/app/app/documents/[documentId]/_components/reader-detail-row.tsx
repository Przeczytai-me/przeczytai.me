import type { LucideIcon } from "lucide-react";
import type { ReactNode } from "react";

type ReaderDetailRowProps = {
  icon: LucideIcon;
  label: string;
  value: ReactNode;
};

export const ReaderDetailRow = ({
  icon: Icon,
  label,
  value,
}: ReaderDetailRowProps) => (
  <div className="rounded-lg border border-border bg-muted/30 p-3">
    <dt className="flex items-center gap-2 text-muted-foreground text-xs">
      <Icon className="size-3.5 shrink-0" aria-hidden="true" />
      {label}
    </dt>
    <dd className="mt-1 wrap-break-word font-medium text-sm">{value}</dd>
  </div>
);
