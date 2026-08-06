"use client";

import { scale } from "./chart-kit";

const W = 80;
const H = 20;

/** Trend shape only - no axes, no labels. The KPI tile carries the number. */
export const Sparkline = ({
  values,
  color = "var(--cost-tts)",
  label,
}: {
  values: number[];
  color?: string;
  label: string;
}) => {
  if (values.length < 2) return null;
  const max = Math.max(...values);
  const min = Math.min(...values);
  const x = (index: number) => scale(index, [0, values.length - 1], [1, W - 1]);
  const y = (value: number) => scale(value, [min, max], [H - 2, 2]);
  const line = values
    .map((value, index) => `${x(index)},${y(value)}`)
    .join(" L");
  const last = values.at(-1) ?? 0;

  return (
    <svg
      viewBox={`0 0 ${W} ${H}`}
      className="h-5 w-20 overflow-visible"
      role="img"
      aria-label={label}
    >
      <title>{label}</title>
      <path
        d={`M${line}`}
        fill="none"
        stroke={color}
        strokeWidth={1.5}
        strokeLinejoin="round"
        strokeLinecap="round"
      />
      <circle cx={x(values.length - 1)} cy={y(last)} r={2} fill={color} />
    </svg>
  );
};
