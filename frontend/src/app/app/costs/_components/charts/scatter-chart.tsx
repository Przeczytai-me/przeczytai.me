"use client";

import { Fragment } from "react";
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
const H = 170;
const PAD = { top: 10, right: 10, bottom: 22, left: 38 };

export type ScatterPoint = {
  key: string;
  x: number;
  y: number;
  group: string;
  color: string;
  tooltip: React.ReactNode;
};

export const ScatterChart = ({
  points,
  groups,
  xLabel,
  yLabel,
  formatX,
  formatY,
  emptyMessage,
  summary,
}: {
  points: ScatterPoint[];
  groups: { label: string; color: string }[];
  xLabel: string;
  yLabel: string;
  formatX: (value: number) => string;
  formatY: (value: number) => string;
  emptyMessage: string;
  summary: string;
}) => {
  const { tooltip, show, hide } = useTooltip();
  if (points.length === 0) return <EmptyChart message={emptyMessage} />;

  const xMax = niceMax(Math.max(...points.map((p) => p.x)));
  const yMax = niceMax(Math.max(...points.map((p) => p.y)));
  const px = (value: number) =>
    scale(value, [0, xMax], [PAD.left, W - PAD.right]);
  const py = (value: number) =>
    scale(value, [0, yMax], [H - PAD.bottom, PAD.top]);

  return (
    <div className="relative">
      <ChartFigure summary={summary} width={W} height={H}>
        {[0, yMax / 2, yMax].map((tick) => (
          <Fragment key={tick}>
            <line
              x1={PAD.left}
              x2={W - PAD.right}
              y1={py(tick)}
              y2={py(tick)}
              className="stroke-border"
              strokeWidth={0.5}
            />
            <text
              x={PAD.left - 4}
              y={py(tick) + 3}
              textAnchor="end"
              className="fill-muted-foreground text-[7px]"
            >
              {formatY(tick)}
            </text>
          </Fragment>
        ))}
        {[0, xMax / 2, xMax].map((tick) => (
          <text
            key={tick}
            x={px(tick)}
            y={H - 12}
            textAnchor="middle"
            className="fill-muted-foreground text-[7px]"
          >
            {formatX(tick)}
          </text>
        ))}

        {points.map((point) => (
          <circle
            key={point.key}
            cx={px(point.x)}
            cy={py(point.y)}
            r={3.5}
            fill={point.color}
            fillOpacity={0.8}
            /* 2px surface ring so overlapping dots stay countable. */
            stroke="var(--card)"
            strokeWidth={1}
            onMouseEnter={(event) => show(event, point.tooltip)}
            onMouseLeave={hide}
          />
        ))}

        <text
          x={(W + PAD.left) / 2}
          y={H - 2}
          textAnchor="middle"
          className="fill-muted-foreground text-[7px]"
        >
          {xLabel}
        </text>
        <text
          x={-(H / 2)}
          y={8}
          transform="rotate(-90)"
          textAnchor="middle"
          className="fill-muted-foreground text-[7px]"
        >
          {yLabel}
        </text>
      </ChartFigure>
      <Legend items={groups} />
      <Tooltip tooltip={tooltip} />
    </div>
  );
};
