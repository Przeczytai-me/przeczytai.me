"use client";

import { type ReactNode, useCallback, useState } from "react";
import { cn } from "@/lib/utils";

export type Point = { x: number; y: number };

/** Linear scale. Domains are collapsed defensively: a flat series is common
 *  here (a month of pure edge-tts is genuinely all zero) and must not divide by
 *  zero or render marks at NaN. */
export const scale = (
  value: number,
  domain: [number, number],
  range: [number, number],
): number => {
  const [d0, d1] = domain;
  const [r0, r1] = range;
  if (d1 === d0) return (r0 + r1) / 2;
  return r0 + ((value - d0) / (d1 - d0)) * (r1 - r0);
};

export const niceMax = (max: number): number => {
  if (max <= 0) return 1;
  const magnitude = 10 ** Math.floor(Math.log10(max));
  const normalized = max / magnitude;
  const step =
    normalized <= 1 ? 1 : normalized <= 2 ? 2 : normalized <= 5 ? 5 : 10;
  return step * magnitude;
};

type TooltipState = { x: number; y: number; content: ReactNode } | null;

export const useTooltip = () => {
  const [tooltip, setTooltip] = useState<TooltipState>(null);
  const show = useCallback(
    (event: { clientX: number; clientY: number }, content: ReactNode) => {
      setTooltip({ x: event.clientX, y: event.clientY, content });
    },
    [],
  );
  const hide = useCallback(() => setTooltip(null), []);
  return { tooltip, show, hide };
};

export const Tooltip = ({ tooltip }: { tooltip: TooltipState }) => {
  if (!tooltip) return null;
  return (
    <div
      className="pointer-events-none fixed z-50 max-w-64 rounded-md border border-border bg-popover px-2.5 py-1.5 text-popover-foreground text-xs shadow-md"
      style={{
        left: Math.min(tooltip.x + 12, globalThis.innerWidth - 260),
        top: tooltip.y + 12,
      }}
      role="status"
    >
      {tooltip.content}
    </div>
  );
};

type ChartCardProps = {
  title: string;
  description?: string;
  action?: ReactNode;
  children: ReactNode;
  className?: string;
};

export const ChartCard = ({
  title,
  description,
  action,
  children,
  className,
}: ChartCardProps) => (
  <section
    className={cn(
      "flex flex-col rounded-lg border border-border bg-card p-4",
      className,
    )}
    aria-label={title}
  >
    <header className="mb-3 flex items-start justify-between gap-3">
      <div>
        <h3 className="font-medium text-sm">{title}</h3>
        {description ? (
          <p className="mt-0.5 text-muted-foreground text-xs">{description}</p>
        ) : null}
      </div>
      {action}
    </header>
    <div className="flex-1">{children}</div>
  </section>
);

export const EmptyChart = ({ message }: { message: string }) => (
  <div className="flex h-full min-h-32 items-center justify-center rounded-md border border-border border-dashed p-4">
    <p className="text-center text-muted-foreground text-xs">{message}</p>
  </div>
);

export const ChartSkeleton = ({ height = 160 }: { height?: number }) => (
  <div
    className="animate-pulse rounded-md bg-muted"
    style={{ height }}
    aria-hidden="true"
  />
);

/** Every chart carries a text alternative. A chart no screen reader can read is
 *  not finished, and it doubles as the relief the palette's light-mode contrast
 *  warning requires. */
export const ChartFigure = ({
  summary,
  children,
  width = 320,
  height = 160,
}: {
  summary: string;
  children: ReactNode;
  width?: number;
  height?: number;
}) => (
  <figure className="m-0">
    {/* Uniform scaling only: preserveAspectRatio="none" would stretch strokes
        and turn scatter dots into ellipses. */}
    <svg
      viewBox={`0 0 ${width} ${height}`}
      className="h-auto w-full overflow-visible"
      role="img"
      aria-label={summary}
    >
      <title>{summary}</title>
      {children}
    </svg>
  </figure>
);

export const Legend = ({
  items,
}: {
  items: { label: string; color: string; value?: string }[];
}) => (
  <ul className="mt-3 flex flex-wrap gap-x-4 gap-y-1.5">
    {items.map((item) => (
      <li key={item.label} className="flex items-center gap-1.5 text-xs">
        <span
          className="size-2.5 shrink-0 rounded-[3px]"
          style={{ background: item.color }}
          aria-hidden="true"
        />
        <span className="text-muted-foreground">{item.label}</span>
        {item.value ? (
          <span className="font-medium tabular-nums">{item.value}</span>
        ) : null}
      </li>
    ))}
  </ul>
);
