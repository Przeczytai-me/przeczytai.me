"use client";

import {
  ChartFigure,
  EmptyChart,
  niceMax,
  scale,
  Tooltip,
  useTooltip,
} from "./chart-kit";

const W = 320;
const H = 150;
const PAD = { top: 10, right: 8, bottom: 26, left: 40 };

export type WaterfallStep = {
  key: string;
  label: string;
  value: number;
  color: string;
};

/**
 * How one run's cost accumulates. Each bar floats from the running total, so the
 * question "which stage made this expensive?" is answered by bar height rather
 * than by reading five separate numbers.
 */
export const WaterfallChart = ({
  steps,
  totalLabel,
  formatValue,
  emptyMessage,
  summary,
}: {
  steps: WaterfallStep[];
  totalLabel: string;
  formatValue: (value: number) => string;
  emptyMessage: string;
  summary: string;
}) => {
  const { tooltip, show, hide } = useTooltip();
  const contributing = steps.filter((step) => step.value > 0);
  if (contributing.length === 0) return <EmptyChart message={emptyMessage} />;

  const total = contributing.reduce((sum, step) => sum + step.value, 0);
  const max = niceMax(total);
  const y = (value: number) =>
    scale(value, [0, max], [H - PAD.bottom, PAD.top]);
  const columns = contributing.length + 1;
  const slot = (W - PAD.left - PAD.right) / columns;
  const barWidth = Math.min(slot * 0.62, 30);

  let running = 0;
  const bars = contributing.map((step, index) => {
    const bottom = running;
    running += step.value;
    return {
      step,
      x: PAD.left + slot * index + (slot - barWidth) / 2,
      yTop: y(running),
      height: Math.max(y(bottom) - y(running), 1),
      connectorY: y(running),
    };
  });

  const totalX = PAD.left + slot * contributing.length + (slot - barWidth) / 2;

  return (
    <div className="relative">
      <ChartFigure summary={summary} width={W} height={H}>
        <line
          x1={PAD.left}
          x2={W - PAD.right}
          y1={y(0)}
          y2={y(0)}
          className="stroke-border"
        />
        {bars.map((bar, index) => (
          <g key={bar.step.key}>
            {index < bars.length - 1 ? (
              <line
                x1={bar.x + barWidth}
                x2={bars[index + 1].x}
                y1={bar.connectorY}
                y2={bar.connectorY}
                className="stroke-muted-foreground"
                strokeWidth={0.5}
                strokeDasharray="2 2"
              />
            ) : (
              <line
                x1={bar.x + barWidth}
                x2={totalX}
                y1={bar.connectorY}
                y2={bar.connectorY}
                className="stroke-muted-foreground"
                strokeWidth={0.5}
                strokeDasharray="2 2"
              />
            )}
            <rect
              x={bar.x}
              y={bar.yTop}
              width={barWidth}
              height={bar.height}
              rx={2}
              fill={bar.step.color}
              onMouseEnter={(event) =>
                show(
                  event,
                  <div>
                    <p className="font-medium">{bar.step.label}</p>
                    <p className="tabular-nums">
                      {formatValue(bar.step.value)}
                    </p>
                  </div>,
                )
              }
              onMouseLeave={hide}
            />
            <text
              x={bar.x + barWidth / 2}
              y={H - 14}
              textAnchor="middle"
              className="fill-muted-foreground text-[7px]"
            >
              {bar.step.label}
            </text>
          </g>
        ))}

        <rect
          x={totalX}
          y={y(total)}
          width={barWidth}
          height={Math.max(y(0) - y(total), 1)}
          rx={2}
          className="fill-foreground"
          opacity={0.85}
        />
        <text
          x={totalX + barWidth / 2}
          y={H - 14}
          textAnchor="middle"
          className="fill-foreground text-[7px] font-medium"
        >
          {totalLabel}
        </text>
        <text
          x={totalX + barWidth / 2}
          y={y(total) - 4}
          textAnchor="middle"
          className="fill-foreground text-[8px] font-semibold tabular-nums"
        >
          {formatValue(total)}
        </text>
      </ChartFigure>
      <Tooltip tooltip={tooltip} />
    </div>
  );
};
