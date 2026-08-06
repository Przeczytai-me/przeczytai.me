"use client";

import { useState } from "react";
import type { CostRun, CostSummary } from "@/lib/costs-api";
import {
  COST_COMPONENT_COLOR,
  COST_COMPONENT_LABEL,
  COST_COMPONENTS,
  formatBytes,
  formatChars,
  formatDurationMs,
  formatUsd,
  vendorColor,
} from "@/lib/format-cost";
import { BarTrack } from "./charts/bar-list";
import { ChartCard } from "./charts/chart-kit";
import { HistogramChart } from "./charts/histogram-chart";
import { WaterfallChart } from "./charts/waterfall-chart";

const STAGE_COLOR: Record<string, string> = {
  normalize: "var(--cost-compute)",
  synthesize: "var(--cost-tts)",
  merge: "var(--cost-platform)",
};

const RunDetail = ({ run }: { run: CostRun }) => {
  const stages = Object.entries(run.usage.compute_ms_by_stage);
  return (
    <div className="grid gap-3 lg:grid-cols-2">
      <ChartCard
        title="How this run's cost accumulates"
        description={`${run.vendor} · ${formatChars(run.char_count)} chars`}
      >
        <WaterfallChart
          steps={COST_COMPONENTS.map((key) => ({
            key,
            label: COST_COMPONENT_LABEL[key],
            value: run.components[key],
            color: COST_COMPONENT_COLOR[key],
          }))}
          totalLabel="Total"
          formatValue={formatUsd}
          emptyMessage="This run has no recorded cost."
          summary={`Cost of run ${run.reading_id} accumulating to ${formatUsd(run.total_usd)}`}
        />
      </ChartCard>

      <ChartCard
        title="Where the time went"
        description="Stage durations — the long bar is the expensive one"
      >
        <div className="space-y-4">
          <BarTrack
            segments={stages.map(([stage, ms]) => ({
              key: stage,
              label: stage,
              value: ms,
              color: STAGE_COLOR[stage] ?? "var(--muted-foreground)",
            }))}
            ariaLabel="Processing stage durations"
            height={12}
          />
          <ul className="space-y-1.5">
            {stages.map(([stage, ms]) => (
              <li key={stage} className="flex items-center gap-2 text-xs">
                <span
                  className="size-2.5 shrink-0 rounded-[3px]"
                  style={{
                    background: STAGE_COLOR[stage] ?? "var(--muted-foreground)",
                  }}
                  aria-hidden="true"
                />
                <span className="flex-1 text-muted-foreground capitalize">
                  {stage}
                </span>
                <span className="font-medium tabular-nums">
                  {formatDurationMs(ms)}
                </span>
              </li>
            ))}
          </ul>

          <dl className="grid grid-cols-2 gap-x-4 gap-y-1.5 border-border border-t pt-3 text-xs">
            {[
              [
                "Characters synthesised",
                formatChars(run.usage.chars_synthesized),
              ],
              ["Chunks", String(run.usage.chunks)],
              ["Audio length", formatDurationMs(run.usage.audio_ms)],
              ["Stored", formatBytes(run.usage.stored_bytes)],
              ["Lambda memory", `${run.usage.lambda_memory_mb} MB`],
              ["Total cost", formatUsd(run.total_usd)],
            ].map(([label, value]) => (
              <div key={label} className="flex justify-between gap-2">
                <dt className="text-muted-foreground">{label}</dt>
                <dd className="font-medium tabular-nums">{value}</dd>
              </div>
            ))}
          </dl>
        </div>
      </ChartCard>
    </div>
  );
};

type SortKey = "cost" | "chars" | "date";

export const RunExplorer = ({ summary }: { summary: CostSummary }) => {
  const [sort, setSort] = useState<SortKey>("cost");
  const [selected, setSelected] = useState<string | null>(
    summary.runs[0]?.reading_id ?? null,
  );

  const vendors = [...new Set(summary.runs.map((run) => run.vendor))];
  const sorted = summary.runs.slice().sort((a, b) => {
    if (sort === "chars") return b.char_count - a.char_count;
    if (sort === "date") return b.created_at.localeCompare(a.created_at);
    return b.total_usd - a.total_usd;
  });
  const top = sorted.slice(0, 10);
  const maxCost = Math.max(...top.map((run) => run.total_usd), 0);
  const selectedRun =
    summary.runs.find((run) => run.reading_id === selected) ?? summary.runs[0];

  if (summary.runs.length === 0) return null;

  return (
    <div className="space-y-3">
      <div className="grid gap-3 lg:grid-cols-2">
        <ChartCard
          title="Runs"
          description="Select a row to break it down"
          action={
            <div className="flex gap-1">
              {(["cost", "chars", "date"] as SortKey[]).map((key) => (
                <button
                  type="button"
                  key={key}
                  onClick={() => setSort(key)}
                  className={`rounded-md border px-2 py-1 text-xs transition-colors ${
                    sort === key
                      ? "border-border bg-accent text-accent-foreground"
                      : "border-transparent text-muted-foreground hover:bg-accent/50"
                  }`}
                >
                  {key}
                </button>
              ))}
            </div>
          }
        >
          {/* The table view is also the relief the palette's light-mode contrast
              warning requires: every value is readable as text. */}
          <ul className="space-y-1">
            {top.map((run) => (
              <li key={run.reading_id}>
                <button
                  type="button"
                  onClick={() => setSelected(run.reading_id)}
                  className={`w-full rounded-md border px-2.5 py-2 text-left transition-colors ${
                    selectedRun?.reading_id === run.reading_id
                      ? "border-border bg-accent"
                      : "border-transparent hover:bg-accent/50"
                  }`}
                >
                  <div className="flex items-baseline justify-between gap-2 text-xs">
                    <span className="flex items-center gap-1.5 truncate">
                      <span
                        className="size-2 shrink-0 rounded-[2px]"
                        style={{ background: vendorColor(run.vendor, vendors) }}
                        aria-hidden="true"
                      />
                      <span className="truncate font-medium">{run.vendor}</span>
                      <span className="shrink-0 text-muted-foreground">
                        {formatChars(run.char_count)}
                      </span>
                    </span>
                    <span className="shrink-0 font-medium tabular-nums">
                      {formatUsd(run.total_usd)}
                    </span>
                  </div>
                  <div className="mt-1 h-1 w-full overflow-hidden rounded-full bg-muted">
                    <div
                      className="h-full rounded-full"
                      style={{
                        width:
                          maxCost > 0
                            ? `${(run.total_usd / maxCost) * 100}%`
                            : "0%",
                        background: vendorColor(run.vendor, vendors),
                      }}
                    />
                  </div>
                </button>
              </li>
            ))}
          </ul>
        </ChartCard>

        <ChartCard
          title="Run cost distribution"
          description="With the per-run cap drawn over it"
        >
          <HistogramChart
            values={summary.runs.map((run) => run.total_usd)}
            limit={summary.limits.max_run_cost_usd}
            limitLabel={`cap ${formatUsd(summary.limits.max_run_cost_usd)}`}
            formatValue={formatUsd}
            emptyMessage="No runs recorded yet."
            summary={`Distribution of ${summary.runs.length} run costs against a ${formatUsd(summary.limits.max_run_cost_usd)} cap`}
          />
        </ChartCard>
      </div>

      {selectedRun ? <RunDetail run={selectedRun} /> : null}
    </div>
  );
};
