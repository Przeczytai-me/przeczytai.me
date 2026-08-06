"use client";

import { useState } from "react";
import type { CostSummary } from "@/lib/costs-api";
import {
  COST_COMPONENT_COLOR,
  COST_COMPONENT_LABEL,
  COST_COMPONENTS,
  formatChars,
  formatMonth,
  formatUsd,
  formatUsdShort,
  vendorColor,
} from "@/lib/format-cost";
import { AreaChart } from "./charts/area-chart";
import { BarList } from "./charts/bar-list";
import { ChartCard } from "./charts/chart-kit";
import { DonutChart } from "./charts/donut-chart";
import { HeatmapChart } from "./charts/heatmap-chart";
import { ScatterChart } from "./charts/scatter-chart";

export const CostOverTime = ({ summary }: { summary: CostSummary }) => {
  const [stacked, setStacked] = useState(true);
  return (
    <ChartCard
      title="Cost over time"
      description="By component, per month"
      action={
        <button
          type="button"
          onClick={() => setStacked((value) => !value)}
          className="rounded-md border border-border px-2 py-1 text-muted-foreground text-xs transition-colors hover:bg-accent hover:text-accent-foreground"
        >
          {stacked ? "Stacked" : "Lines"}
        </button>
      }
    >
      <AreaChart
        labels={summary.months.map((month) => formatMonth(month.month))}
        series={COST_COMPONENTS.map((key) => ({
          key,
          label: COST_COMPONENT_LABEL[key],
          color: COST_COMPONENT_COLOR[key],
        }))}
        values={COST_COMPONENTS.map((key) =>
          summary.months.map((month) => month.components[key]),
        )}
        stacked={stacked}
        formatValue={formatUsd}
        formatTick={formatUsdShort}
        emptyMessage="No cost history yet."
        summary={`Monthly cost by component across ${summary.months.length} months`}
      />
    </ChartCard>
  );
};

export const CompositionDonut = ({ summary }: { summary: CostSummary }) => (
  <ChartCard
    title="Where the money goes"
    description="Current month by component"
  >
    <DonutChart
      slices={COST_COMPONENTS.map((key) => ({
        key,
        label: COST_COMPONENT_LABEL[key],
        color: COST_COMPONENT_COLOR[key],
        value: summary.components[key],
      }))}
      centerLabel="this month"
      centerValue={formatUsd(summary.totals.month_usd)}
      formatValue={formatUsd}
      emptyMessage="No cost recorded this month."
      summary={`Component split of ${formatUsd(summary.totals.month_usd)} this month`}
    />
  </ChartCard>
);

export const VendorBreakdown = ({ summary }: { summary: CostSummary }) => {
  const vendors = [...new Set(summary.vendors.map((v) => v.vendor))];
  return (
    <ChartCard title="By vendor and voice" description="Current month">
      <BarList
        items={summary.vendors
          .slice()
          .sort((a, b) => b.total_usd - a.total_usd)
          .map((vendor) => ({
            key: `${vendor.vendor}-${vendor.voice}`,
            label: `${vendor.vendor} · ${vendor.voice}`,
            value: vendor.total_usd,
            color: vendorColor(vendor.vendor, vendors),
            meta: `${vendor.runs} runs`,
          }))}
        formatValue={formatUsd}
        emptyMessage="No vendor activity this month."
      />
    </ChartCard>
  );
};

/**
 * Free vs paid. The two bars disagreeing is the whole point: edge-tts carries
 * most of the traffic and almost none of the cost.
 */
/**
 * Free vs paid. Classification is on the TTS component, not the run total:
 * an edge-tts run still incurs compute, storage and platform cost, so keying
 * on total_usd would file every real edge run as "paid" and the panel would
 * always read 100% paid, which is the opposite of the insight it exists for.
 */
export const FreeVsPaid = ({ summary }: { summary: CostSummary }) => {
  const free = summary.runs.filter((run) => run.components.tts === 0);
  const paid = summary.runs.filter((run) => run.components.tts > 0);
  const freeSpend = free.reduce((sum, run) => sum + run.total_usd, 0);
  const paidSpend = paid.reduce((sum, run) => sum + run.total_usd, 0);
  const totalRuns = summary.runs.length;

  if (totalRuns === 0) {
    return (
      <ChartCard title="Free vs paid" description="Share of runs and of spend">
        <p className="py-8 text-center text-muted-foreground text-xs">
          No runs this month.
        </p>
      </ChartCard>
    );
  }

  const rows = [
    {
      label: "Share of runs",
      freeValue: free.length,
      paidValue: paid.length,
      format: (value: number) =>
        `${((value / totalRuns) * 100).toFixed(0)}% (${value})`,
    },
    {
      label: "Share of spend",
      freeValue: freeSpend,
      paidValue: paidSpend,
      format: (value: number) => formatUsd(value),
    },
  ];

  return (
    <ChartCard
      title="Free vs paid"
      description="Free means a zero TTS component, not a zero total"
    >
      <div className="space-y-4 pt-1">
        {rows.map((row) => {
          const total = row.freeValue + row.paidValue;
          return (
            <div key={row.label}>
              <p className="mb-1.5 text-muted-foreground text-xs">
                {row.label}
              </p>
              <div className="flex h-2.5 w-full gap-0.5 overflow-hidden rounded-full bg-muted">
                <div
                  style={{
                    width:
                      total > 0 ? `${(row.freeValue / total) * 100}%` : "0%",
                    background: "var(--cost-compute)",
                  }}
                />
                <div
                  style={{
                    width:
                      total > 0 ? `${(row.paidValue / total) * 100}%` : "0%",
                    background: "var(--cost-llm)",
                  }}
                />
              </div>
              <div className="mt-1 flex justify-between text-[11px] tabular-nums">
                <span className="text-muted-foreground">
                  free {row.format(row.freeValue)}
                </span>
                <span className="text-muted-foreground">
                  paid {row.format(row.paidValue)}
                </span>
              </div>
            </div>
          );
        })}
      </div>
    </ChartCard>
  );
};

export const CharsCostScatter = ({ summary }: { summary: CostSummary }) => {
  const vendors = [...new Set(summary.runs.map((run) => run.vendor))];
  return (
    <ChartCard
      title="Characters vs cost"
      description="One dot per run — the slope is the vendor's price"
    >
      <ScatterChart
        points={summary.runs.map((run) => ({
          key: run.reading_id,
          x: run.char_count,
          y: run.total_usd,
          group: run.vendor,
          color: vendorColor(run.vendor, vendors),
          tooltip: (
            <div>
              <p className="font-medium">{run.vendor}</p>
              <p className="tabular-nums">
                {formatChars(run.char_count)} chars · {formatUsd(run.total_usd)}
              </p>
            </div>
          ),
        }))}
        groups={vendors.map((vendor) => ({
          label: vendor,
          color: vendorColor(vendor, vendors),
        }))}
        xLabel="characters"
        yLabel="USD"
        formatX={formatChars}
        formatY={formatUsdShort}
        emptyMessage="No runs recorded yet."
        summary={`${summary.runs.length} runs plotted by character count against cost`}
      />
    </ChartCard>
  );
};

export const DailyHeatmap = ({ summary }: { summary: CostSummary }) => (
  <ChartCard title="Daily spend" description="Current month">
    <HeatmapChart
      days={summary.days}
      formatValue={formatUsd}
      emptyMessage="No runs yet this month."
    />
  </ChartCard>
);

export const UnitEconomics = ({ summary }: { summary: CostSummary }) => {
  const perThousandChars = summary.months.map((month) =>
    month.chars > 0 ? (month.total_usd / month.chars) * 1000 : 0,
  );
  const perAudioMinute = summary.months.map((month) =>
    month.audio_ms > 0 ? month.total_usd / (month.audio_ms / 60000) : 0,
  );

  return (
    <ChartCard
      title="Unit economics"
      description="What a thousand characters and a minute of audio actually cost"
    >
      <AreaChart
        labels={summary.months.map((month) => formatMonth(month.month))}
        series={[
          {
            key: "chars",
            label: "USD per 1k chars",
            color: "var(--cost-tts)",
          },
          {
            key: "audio",
            label: "USD per audio minute",
            color: "var(--cost-storage)",
          },
        ]}
        values={[perThousandChars, perAudioMinute]}
        stacked={false}
        formatValue={formatUsd}
        formatTick={formatUsdShort}
        emptyMessage="Not enough history yet."
        summary="Cost per thousand characters and per minute of audio, by month"
      />
    </ChartCard>
  );
};

export const UserDistribution = ({ summary }: { summary: CostSummary }) => (
  <ChartCard
    title="By user"
    description="Anonymised references — spend concentration across accounts"
  >
    <BarList
      items={summary.users
        .slice()
        .sort((a, b) => b.total_usd - a.total_usd)
        .slice(0, 10)
        .map((user) => ({
          key: user.user_ref,
          label: user.user_ref,
          value: user.total_usd,
          color: "var(--cost-platform)",
          meta: `${user.runs} runs`,
        }))}
      formatValue={formatUsd}
      emptyMessage="No user activity this month."
    />
  </ChartCard>
);
