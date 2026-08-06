"use client";

import { EmptyChart, Tooltip, useTooltip } from "./chart-kit";

const SIZE = 160;
const R_OUTER = 68;
const R_INNER = 46;
const GAP_DEGREES = 2;

export type DonutSlice = {
  key: string;
  label: string;
  color: string;
  value: number;
};

const arc = (startDeg: number, endDeg: number) => {
  const toXY = (deg: number, radius: number) => {
    const rad = ((deg - 90) * Math.PI) / 180;
    return [
      SIZE / 2 + radius * Math.cos(rad),
      SIZE / 2 + radius * Math.sin(rad),
    ];
  };
  const large = endDeg - startDeg > 180 ? 1 : 0;
  const [x1, y1] = toXY(startDeg, R_OUTER);
  const [x2, y2] = toXY(endDeg, R_OUTER);
  const [x3, y3] = toXY(endDeg, R_INNER);
  const [x4, y4] = toXY(startDeg, R_INNER);
  return [
    `M${x1} ${y1}`,
    `A${R_OUTER} ${R_OUTER} 0 ${large} 1 ${x2} ${y2}`,
    `L${x3} ${y3}`,
    `A${R_INNER} ${R_INNER} 0 ${large} 0 ${x4} ${y4}`,
    "Z",
  ].join(" ");
};

export const DonutChart = ({
  slices,
  centerLabel,
  centerValue,
  formatValue,
  emptyMessage,
  summary,
}: {
  slices: DonutSlice[];
  centerLabel: string;
  centerValue: string;
  formatValue: (value: number) => string;
  emptyMessage: string;
  summary: string;
}) => {
  const { tooltip, show, hide } = useTooltip();
  const total = slices.reduce((sum, slice) => sum + slice.value, 0);

  if (total <= 0) return <EmptyChart message={emptyMessage} />;

  let cursor = 0;
  const drawn = slices
    .filter((slice) => slice.value > 0)
    .map((slice) => {
      const sweep = (slice.value / total) * 360;
      const start = cursor;
      cursor += sweep;
      // Only inset a gap when the slice is wide enough to survive it.
      const gap = sweep > GAP_DEGREES * 2 ? GAP_DEGREES : 0;
      return {
        slice,
        d: arc(start + gap / 2, start + sweep - gap / 2),
        share: (slice.value / total) * 100,
      };
    });

  return (
    <div className="flex flex-col items-center gap-3 sm:flex-row sm:items-center">
      <figure className="m-0 shrink-0">
        <svg
          viewBox={`0 0 ${SIZE} ${SIZE}`}
          className="h-40 w-40"
          role="img"
          aria-label={summary}
        >
          <title>{summary}</title>
          {drawn.map(({ slice, d, share }) => (
            <path
              key={slice.key}
              d={d}
              fill={slice.color}
              onMouseEnter={(event) =>
                show(
                  event,
                  <div>
                    <p className="font-medium">{slice.label}</p>
                    <p className="tabular-nums">
                      {formatValue(slice.value)} · {share.toFixed(1)}%
                    </p>
                  </div>,
                )
              }
              onMouseLeave={hide}
            />
          ))}
          <text
            x={SIZE / 2}
            y={SIZE / 2 - 2}
            textAnchor="middle"
            className="fill-foreground font-semibold text-[15px] tabular-nums"
          >
            {centerValue}
          </text>
          <text
            x={SIZE / 2}
            y={SIZE / 2 + 12}
            textAnchor="middle"
            className="fill-muted-foreground text-[8px]"
          >
            {centerLabel}
          </text>
        </svg>
      </figure>
      {/* Direct value labels, not a bare colour key: three palette slots sit
          below 3:1 on the light surface and require this relief. */}
      <ul className="w-full space-y-1.5">
        {drawn.map(({ slice, share }) => (
          <li key={slice.key} className="flex items-center gap-2 text-xs">
            <span
              className="size-2.5 shrink-0 rounded-[3px]"
              style={{ background: slice.color }}
              aria-hidden="true"
            />
            <span className="flex-1 text-muted-foreground">{slice.label}</span>
            <span className="font-medium tabular-nums">
              {formatValue(slice.value)}
            </span>
            <span className="w-11 text-right text-muted-foreground tabular-nums">
              {share.toFixed(1)}%
            </span>
          </li>
        ))}
      </ul>
      <Tooltip tooltip={tooltip} />
    </div>
  );
};
