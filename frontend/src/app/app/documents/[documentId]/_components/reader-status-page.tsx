import { AlertCircle, Clock3 } from "lucide-react";
import Link from "next/link";
import { Button, buttonVariants } from "@/components/ui/button";
import { cn } from "@/lib/utils";

type ReaderStatusPageProps = {
  description?: string;
  isError?: boolean;
  onRetry?: () => void;
  primaryAction?: {
    href: string;
    label: string;
  };
  secondaryAction?: {
    href: string;
    label: string;
  };
  retryLabel?: string;
  title?: string;
};

export const ReaderStatusPage = ({
  description,
  isError = false,
  onRetry,
  primaryAction,
  secondaryAction,
  retryLabel,
  title,
}: ReaderStatusPageProps) => {
  const Icon = isError ? AlertCircle : Clock3;

  return (
    <section className="flex h-full min-h-0 items-center justify-center">
      <div className="w-full max-w-xl rounded-xl border border-border bg-background p-8 text-center shadow-sm">
        <div
          className={cn(
            "mx-auto flex size-12 items-center justify-center rounded-full",
            isError
              ? "bg-destructive/10 text-destructive"
              : "bg-primary/10 text-primary",
          )}
        >
          <Icon className="size-6" aria-hidden="true" />
        </div>
        {title && <h1 className="mt-5 font-semibold text-2xl">{title}</h1>}
        {description && (
          <p className="mx-auto mt-2 max-w-md text-muted-foreground text-sm leading-6">
            {description}
          </p>
        )}
        <div className="mt-6 flex flex-wrap justify-center gap-2">
          {onRetry && (
            <Button type="button" onClick={onRetry}>
              {retryLabel}
            </Button>
          )}
          {!onRetry && primaryAction && (
            <Link
              href={primaryAction.href}
              className={buttonVariants({ variant: "default" })}
            >
              {primaryAction.label}
            </Link>
          )}
          {secondaryAction && (
            <Link
              href={secondaryAction.href}
              className={buttonVariants({ variant: "outline" })}
            >
              {secondaryAction.label}
            </Link>
          )}
        </div>
      </div>
    </section>
  );
};
