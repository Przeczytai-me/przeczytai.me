"use client";

import {
  ChartFigure,
  EmptyChart,
  scale,
  Tooltip,
  useTooltip,
} from "./chart-kit";

const H = 140;
const PAD = { top: 12, right: 8, bottom: 24, left: 30 };
const BINS = 18;

/**
 * Distribution of run costs with the per-run cap drawn over it. The point is to
 * make it obvious when the cap sits far outside the data - a guardrail that
 * cannot fire should look like one rather than being described as protection.
 */
export const HistogramChart = ({
  values,
  limit,
  limitLabel,
  formatValue,
  emptyMessage,
  summary,
}: {
  values: number[];
  limit: number;
  limitLabel: string;
  formatValue: (value: number) => string;
  emptyMessage: string;
  summary: string;
}) => {
  const { tooltip, show, hide } = useTooltip();
  if (values.length === 0) return <EmptyChart message={emptyMessage} />;

  const dataMax = Math.max(...values);
  // The axis must reach the limit, otherwise the cap line has nowhere to sit and
  // the gap this chart exists to show would be invisible.
  const axisMax = Math.max(dataMax, limit) * 1.05;
  const binWidth = axisMax / BINS;
  const bins = Array.from({ length: BINS }, () => 0);
  for (const value of values) {
    const index = Math.min(Math.floor(value / binWidth), BINS - 1);
    bins[index] += 1;
  }
  const countMax = Math.max(...bins, 1);
  const y = (count: number) =>
    scale(count, [0, countMax], [H - PAD.bottom, PAD.top]);
  const overLimit = values.filter((value) => value > limit).length;

  return (
    <div className="relative">
      <ChartFigure summary={summary} height={H}>
        {(W) => {
          const x = (value: number) =>
            scale(value, [0, axisMax], [PAD.left, W - PAD.right]);
          const barWidth = (W - PAD.left - PAD.right) / BINS;
          const limitX = x(limit);
          return (
            <>
              <line
                x1={PAD.left}
                x2={W - PAD.right}
                y1={y(0)}
                y2={y(0)}
                className="stroke-border"
              />
              {bins.map((count, index) => {
                const binStart = index * binWidth;
                return (
                  <rect
                    key={binStart}
                    x={x(binStart) + 0.5}
                    y={y(count)}
                    width={Math.max(barWidth - 1, 1)}
                    height={Math.max(y(0) - y(count), count > 0 ? 1 : 0)}
                    rx={1.5}
                    fill="var(--cost-tts)"
                    opacity={0.8}
                    onMouseEnter={(event) =>
                      show(
                        event,
                        <div>
                          <p className="font-medium tabular-nums">
                            {formatValue(binStart)} –{" "}
                            {formatValue(binStart + binWidth)}
                          </p>
                          <p className="tabular-nums">{count} runs</p>
                        </div>,
                      )
                    }
                    onMouseLeave={hide}
                  />
                );
              })}

              <line
                x1={limitX}
                x2={limitX}
                y1={PAD.top - 6}
                y2={y(0)}
                className="stroke-destructive"
                strokeWidth={1.25}
                strokeDasharray="3 2"
              />
              <text
                x={Math.min(limitX + 3, W - PAD.right - 2)}
                y={PAD.top - 1}
                textAnchor={limitX > W - 90 ? "end" : "start"}
                className="fill-destructive text-[9px] font-medium"
              >
                {limitLabel}
              </text>

              {[0, axisMax / 2, axisMax].map((tick) => (
                <text
                  key={tick}
                  x={x(tick)}
                  y={H - 12}
                  textAnchor="middle"
                  className="fill-muted-foreground text-[9px]"
                >
                  {formatValue(tick)}
                </text>
              ))}
              <text
                x={W / 2}
                y={H - 2}
                textAnchor="middle"
                className="fill-muted-foreground text-[9px]"
              >
                cost per run · {overLimit} of {values.length} runs above the cap
              </text>
            </>
          );
        }}
      </ChartFigure>
      <Tooltip tooltip={tooltip} />
    </div>
  );
};
