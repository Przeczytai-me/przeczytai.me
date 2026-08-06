"use client";

import type { ReactNode } from "react";
import { EmptyChart } from "./chart-kit";

export type BarListItem = {
  key: string;
  label: string;
  value: number;
  color?: string;
  meta?: ReactNode;
};

/**
 * Ranked horizontal bars. Bars are scaled to the largest item rather than to a
 * budget, so the comparison is between rows - the axis is the ranking itself.
 */
export const BarList = ({
  items,
  formatValue,
  emptyMessage,
}: {
  items: BarListItem[];
  formatValue: (value: number) => string;
  emptyMessage: string;
}) => {
  if (items.length === 0) return <EmptyChart message={emptyMessage} />;
  const max = Math.max(...items.map((item) => item.value), 0);

  return (
    <ul className="space-y-2.5">
      {items.map((item) => (
        <li key={item.key}>
          <div className="flex items-baseline justify-between gap-3 text-xs">
            <span className="truncate font-medium">{item.label}</span>
            <span className="shrink-0 tabular-nums">
              {formatValue(item.value)}
            </span>
          </div>
          <div className="mt-1 flex items-center gap-2">
            <div className="h-1.5 flex-1 overflow-hidden rounded-full bg-muted">
              <div
                className="h-full rounded-full"
                style={{
                  width: max > 0 ? `${(item.value / max) * 100}%` : "0%",
                  background: item.color ?? "var(--cost-tts)",
                }}
              />
            </div>
            {item.meta ? (
              <span className="shrink-0 text-muted-foreground text-[11px] tabular-nums">
                {item.meta}
              </span>
            ) : null}
          </div>
        </li>
      ))}
    </ul>
  );
};

/**
 * A single bar split into segments. Used for the budget meter, the free-vs-paid
 * split and per-run stage timings.
 */
export const BarTrack = ({
  segments,
  ariaLabel,
  height = 8,
}: {
  segments: { key: string; label: string; value: number; color: string }[];
  ariaLabel: string;
  height?: number;
}) => {
  const total = segments.reduce((sum, segment) => sum + segment.value, 0);
  if (total <= 0) {
    return (
      <div
        className="w-full rounded-full bg-muted"
        style={{ height }}
        role="img"
        aria-label={ariaLabel}
      />
    );
  }
  return (
    <div
      className="flex w-full gap-0.5 overflow-hidden rounded-full bg-muted"
      style={{ height }}
      role="img"
      aria-label={ariaLabel}
    >
      {segments
        .filter((segment) => segment.value > 0)
        .map((segment) => (
          <div
            key={segment.key}
            style={{
              width: `${(segment.value / total) * 100}%`,
              background: segment.color,
            }}
            title={`${segment.label}: ${((segment.value / total) * 100).toFixed(1)}%`}
          />
        ))}
    </div>
  );
};
