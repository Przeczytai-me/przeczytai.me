"use client";

import { ArrowDown, ArrowUp, Minus } from "lucide-react";
import type { CostSummary } from "@/lib/costs-api";
import {
  formatChars,
  formatCount,
  formatDurationMs,
  formatUsd,
} from "@/lib/format-cost";
import { Sparkline } from "./charts/sparkline";

const Delta = ({
  current,
  previous,
}: {
  current: number;
  previous: number;
}) => {
  if (previous <= 0) return null;
  const change = ((current - previous) / previous) * 100;
  const flat = Math.abs(change) < 1;
  const Icon = flat ? Minus : change > 0 ? ArrowUp : ArrowDown;
  return (
    <span className="flex items-center gap-0.5 text-[11px] text-muted-foreground tabular-nums">
      <Icon className="size-3" aria-hidden="true" />
      {flat ? "flat" : `${Math.abs(change).toFixed(0)}%`}
      <span className="sr-only">
        {change > 0 ? "up" : "down"} versus previous month
      </span>
    </span>
  );
};

const Tile = ({
  label,
  value,
  hint,
  spark,
  delta,
}: {
  label: string;
  value: string;
  hint?: string;
  spark?: React.ReactNode;
  delta?: React.ReactNode;
}) => (
  <div className="rounded-lg border border-border bg-card p-4">
    <p className="text-muted-foreground text-xs">{label}</p>
    <div className="mt-1 flex items-end justify-between gap-2">
      <p className="font-semibold text-2xl tabular-nums">{value}</p>
      {spark}
    </div>
    <div className="mt-1 flex items-center gap-2">
      {hint ? <p className="text-muted-foreground text-xs">{hint}</p> : null}
      {delta}
    </div>
  </div>
);

export const KpiTiles = ({ summary }: { summary: CostSummary }) => {
  const { totals, runs } = summary;
  const monthlySeries = summary.months.map((month) => month.total_usd);
  const runSeries = summary.months.map((month) => month.runs);
  const mostExpensive = runs.reduce(
    (max, run) => Math.max(max, run.total_usd),
    0,
  );

  return (
    <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-3 2xl:grid-cols-6">
      <Tile
        label="This month"
        value={formatUsd(totals.month_usd)}
        spark={<Sparkline values={monthlySeries} label="Monthly spend trend" />}
        delta={
          <Delta
            current={totals.month_usd}
            previous={totals.previous_month_usd}
          />
        }
      />
      <Tile
        label="All time"
        value={formatUsd(totals.all_time_usd)}
        hint={`${formatCount(totals.runs_all_time)} runs`}
      />
      <Tile
        label="Average per run"
        value={formatUsd(totals.avg_run_usd)}
        hint={`${formatChars(totals.chars_month)} chars this month`}
      />
      <Tile
        label="Most expensive run"
        value={formatUsd(mostExpensive)}
        hint="in the loaded window"
      />
      <Tile
        label="Runs this month"
        value={formatCount(totals.runs_month)}
        spark={
          <Sparkline
            values={runSeries}
            color="var(--cost-compute)"
            label="Runs per month trend"
          />
        }
      />
      <Tile
        label="Audio produced"
        value={formatDurationMs(totals.audio_ms_month)}
        hint={`${formatCount(totals.active_users_month)} active users`}
      />
    </div>
  );
};
