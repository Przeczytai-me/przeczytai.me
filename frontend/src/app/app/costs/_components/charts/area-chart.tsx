"use client";

import { Fragment, useState } from "react";
import {
  ChartFigure,
  EmptyChart,
  Legend,
  niceMax,
  scale,
  Tooltip,
  useTooltip,
} from "./chart-kit";

const W = 320;
const H = 150;
const PAD = { top: 8, right: 6, bottom: 20, left: 34 };

export type Series = { key: string; label: string; color: string };

type AreaChartProps = {
  labels: string[];
  series: Series[];
  /** values[seriesIndex][pointIndex] */
  values: number[][];
  stacked?: boolean;
  formatValue: (value: number) => string;
  formatTick?: (value: number) => string;
  emptyMessage: string;
  summary: string;
};

export const AreaChart = ({
  labels,
  series,
  values,
  stacked = true,
  formatValue,
  formatTick,
  emptyMessage,
  summary,
}: AreaChartProps) => {
  const { tooltip, show, hide } = useTooltip();
  const [active, setActive] = useState<number | null>(null);

  if (labels.length === 0 || series.length === 0) {
    return <EmptyChart message={emptyMessage} />;
  }

  const totals = labels.map((_, index) =>
    stacked
      ? series.reduce(
          (sum, _s, sIndex) => sum + (values[sIndex]?.[index] ?? 0),
          0,
        )
      : Math.max(...series.map((_s, sIndex) => values[sIndex]?.[index] ?? 0)),
  );
  const max = niceMax(Math.max(...totals, 0));
  const x = (index: number) =>
    labels.length === 1
      ? (PAD.left + W - PAD.right) / 2
      : scale(index, [0, labels.length - 1], [PAD.left, W - PAD.right]);
  const y = (value: number) =>
    scale(value, [0, max], [H - PAD.bottom, PAD.top]);

  // Running baseline per point, so stacked bands sit on top of each other.
  const baselines = labels.map(() => 0);
  const bands = series.map((s, sIndex) => {
    const points = labels.map((_, index) => {
      const value = values[sIndex]?.[index] ?? 0;
      const bottom = stacked ? baselines[index] : 0;
      const top = bottom + value;
      if (stacked) baselines[index] = top;
      return { bottom, top };
    });
    const topLine = points.map((p, i) => `${x(i)},${y(p.top)}`).join(" L");
    const bottomLine = points
      .map((p, i) => `${x(i)},${y(p.bottom)}`)
      .reverse()
      .join(" L");
    return {
      series: s,
      area: `M${topLine} L${bottomLine} Z`,
      line: `M${topLine}`,
    };
  });

  const ticks = [0, max / 2, max];

  return (
    <div className="relative">
      <ChartFigure summary={summary} width={W} height={H}>
        {ticks.map((tick) => (
          <Fragment key={tick}>
            <line
              x1={PAD.left}
              x2={W - PAD.right}
              y1={y(tick)}
              y2={y(tick)}
              className="stroke-border"
              strokeWidth={0.5}
            />
            <text
              x={PAD.left - 4}
              y={y(tick) + 3}
              textAnchor="end"
              className="fill-muted-foreground text-[7px]"
            >
              {(formatTick ?? formatValue)(tick)}
            </text>
          </Fragment>
        ))}

        {bands.map((band) => (
          <g key={band.series.key}>
            {/* Unstacked means comparing series, so draw lines only - overlapping
                translucent fills would occlude each other and read as mud. */}
            {stacked ? (
              <>
                <path d={band.area} fill={band.series.color} opacity={0.75} />
                {/* Surface-coloured gap between stacked fills keeps them legible. */}
                <path
                  d={band.line}
                  fill="none"
                  stroke="var(--card)"
                  strokeWidth={1.5}
                />
              </>
            ) : (
              <path
                d={band.line}
                fill="none"
                stroke={band.series.color}
                strokeWidth={2}
                strokeLinejoin="round"
                strokeLinecap="round"
              />
            )}
          </g>
        ))}

        {active !== null ? (
          <line
            x1={x(active)}
            x2={x(active)}
            y1={PAD.top}
            y2={H - PAD.bottom}
            className="stroke-foreground"
            strokeWidth={0.75}
            strokeDasharray="2 2"
          />
        ) : null}

        {labels.map((label, index) => (
          <Fragment key={label}>
            <text
              x={x(index)}
              y={H - 6}
              textAnchor="middle"
              className="fill-muted-foreground text-[7px]"
            >
              {label}
            </text>
            {/* Hit target spans the full column, far larger than any mark. */}
            <rect
              x={x(index) - (W - PAD.left - PAD.right) / (labels.length * 2)}
              y={PAD.top}
              width={(W - PAD.left - PAD.right) / labels.length}
              height={H - PAD.bottom - PAD.top}
              fill="transparent"
              onMouseEnter={(event) => {
                setActive(index);
                show(
                  event,
                  <div>
                    <p className="mb-1 font-medium">{label}</p>
                    {series.map((s, sIndex) => (
                      <p
                        key={s.key}
                        className="flex items-center justify-between gap-3"
                      >
                        <span className="flex items-center gap-1.5">
                          <span
                            className="size-2 rounded-[2px]"
                            style={{ background: s.color }}
                          />
                          {s.label}
                        </span>
                        <span className="tabular-nums">
                          {formatValue(values[sIndex]?.[index] ?? 0)}
                        </span>
                      </p>
                    ))}
                  </div>,
                );
              }}
              onMouseLeave={() => {
                setActive(null);
                hide();
              }}
            />
          </Fragment>
        ))}
      </ChartFigure>
      <Legend items={series.map((s) => ({ label: s.label, color: s.color }))} />
      <Tooltip tooltip={tooltip} />
    </div>
  );
};
