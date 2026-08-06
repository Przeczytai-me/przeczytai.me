"use client";

import { EmptyChart, Tooltip, useTooltip } from "./chart-kit";

/**
 * Calendar heatmap for one month. Magnitude is a job for a single hue stepped
 * light to dark - never the categorical component colours.
 */
export const HeatmapChart = ({
  days,
  formatValue,
  emptyMessage,
}: {
  days: { date: string; total_usd: number; runs: number }[];
  formatValue: (value: number) => string;
  emptyMessage: string;
}) => {
  const { tooltip, show, hide } = useTooltip();
  if (days.length === 0) return <EmptyChart message={emptyMessage} />;

  const byDate = new Map(days.map((day) => [day.date, day]));
  const max = Math.max(...days.map((day) => day.total_usd), 0);
  const first = new Date(`${days[0].date}T00:00:00Z`);
  const year = first.getUTCFullYear();
  const month = first.getUTCMonth();
  const daysInMonth = new Date(Date.UTC(year, month + 1, 0)).getUTCDate();
  // Monday-first columns, matching how the rest of the product reads dates.
  const leading = (new Date(Date.UTC(year, month, 1)).getUTCDay() + 6) % 7;

  const cells = Array.from({ length: daysInMonth }, (_, index) => {
    const dayNumber = index + 1;
    const date = `${year}-${String(month + 1).padStart(2, "0")}-${String(dayNumber).padStart(2, "0")}`;
    return { date, dayNumber, entry: byDate.get(date) };
  });

  return (
    <div>
      <div
        className="grid grid-cols-7 gap-1"
        role="img"
        aria-label="Daily spend"
      >
        {["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"].map((label) => (
          <span
            key={label}
            className="text-center text-[10px] text-muted-foreground"
          >
            {label.slice(0, 1)}
          </span>
        ))}
        {Array.from({ length: leading }, (_, index) => `pad-${index}`).map(
          (key) => (
            <span key={key} />
          ),
        )}
        {cells.map((cell) => {
          const value = cell.entry?.total_usd ?? 0;
          const intensity = max > 0 ? value / max : 0;
          return (
            <button
              type="button"
              key={cell.date}
              className="aspect-square rounded-[3px] border border-border text-[9px] tabular-nums transition-transform hover:scale-110"
              style={{
                background:
                  value > 0
                    ? `color-mix(in oklch, var(--cost-tts) ${15 + intensity * 85}%, var(--card))`
                    : "var(--muted)",
                color: intensity > 0.55 ? "white" : "var(--muted-foreground)",
              }}
              onMouseEnter={(event) =>
                show(
                  event,
                  <div>
                    <p className="font-medium">{cell.date}</p>
                    <p className="tabular-nums">
                      {cell.entry
                        ? `${formatValue(value)} · ${cell.entry.runs} runs`
                        : "No runs"}
                    </p>
                  </div>,
                )
              }
              onMouseLeave={hide}
              onFocus={(event) =>
                show(
                  {
                    clientX: event.currentTarget.getBoundingClientRect().left,
                    clientY: event.currentTarget.getBoundingClientRect().bottom,
                  },
                  <div>
                    <p className="font-medium">{cell.date}</p>
                    <p>{cell.entry ? formatValue(value) : "No runs"}</p>
                  </div>,
                )
              }
              onBlur={hide}
            >
              {cell.dayNumber}
            </button>
          );
        })}
      </div>
      <div className="mt-3 flex items-center justify-end gap-1.5 text-[10px] text-muted-foreground">
        <span>Less</span>
        {[0.15, 0.4, 0.65, 0.9, 1].map((step) => (
          <span
            key={step}
            className="size-2.5 rounded-[3px] border border-border"
            style={{
              background: `color-mix(in oklch, var(--cost-tts) ${step * 100}%, var(--card))`,
            }}
          />
        ))}
        <span>More</span>
      </div>
      <Tooltip tooltip={tooltip} />
    </div>
  );
};
