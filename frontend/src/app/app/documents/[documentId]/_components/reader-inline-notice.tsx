import type { LucideIcon } from "lucide-react";

type ReaderInlineNoticeProps = {
  icon: LucideIcon;
  text: string;
};

export const ReaderInlineNotice = ({
  icon: Icon,
  text,
}: ReaderInlineNoticeProps) => (
  <div className="flex gap-2 rounded-lg border border-border bg-muted/50 p-3 text-muted-foreground text-sm">
    <Icon className="mt-0.5 size-4 shrink-0" aria-hidden="true" />
    <p>{text}</p>
  </div>
);
