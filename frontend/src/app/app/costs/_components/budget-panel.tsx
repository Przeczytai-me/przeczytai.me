"use client";

import type { CostSummary } from "@/lib/costs-api";
import { formatUsd } from "@/lib/format-cost";
import { AreaChart } from "./charts/area-chart";
import { ChartCard } from "./charts/chart-kit";

/**
 * Budget meter. Thresholds mirror the AWS Budget in
 * infrastructure/modules/budget so the dashboard and the email alerts tell the
 * same story; this reads the app's own rollups, not the AWS Budgets API.
 */
export const BudgetMeter = ({ summary }: { summary: CostSummary }) => {
  const { budget } = summary;
  const limit = budget.monthly_limit_usd;

  if (limit === null || limit <= 0) {
    return (
      <ChartCard
        title="Monthly budget"
        description="No budget configured (MONTHLY_BUDGET_USD)"
      >
        <div className="flex h-full flex-col justify-center gap-2">
          <p className="font-semibold text-2xl tabular-nums">
            {formatUsd(budget.month_spent_usd)}
          </p>
          <p className="text-muted-foreground text-xs">
            Spent this month. Set a budget to track utilisation against it —
            nothing is blocked either way, the monthly budget only warns.
          </p>
        </div>
      </ChartCard>
    );
  }

  const utilization = budget.utilization ?? 0;
  const state =
    utilization >= 95
      ? "text-destructive"
      : utilization >= 80
        ? "text-[var(--cost-storage)]"
        : "text-foreground";

  return (
    <ChartCard
      title="Monthly budget"
      description={`${formatUsd(budget.month_spent_usd)} of ${formatUsd(limit)}`}
    >
      <div className="flex flex-col">
        <p className={`font-semibold text-2xl tabular-nums ${state}`}>
          {utilization.toFixed(1)}%
        </p>
        <div className="relative mt-3">
          <div className="h-2.5 w-full overflow-hidden rounded-full bg-muted">
            <div
              className="h-full rounded-full transition-[width]"
              style={{
                width: `${Math.min(utilization, 100)}%`,
                background:
                  utilization >= 95
                    ? "var(--destructive)"
                    : utilization >= 80
                      ? "var(--cost-storage)"
                      : "var(--cost-compute)",
              }}
            />
          </div>
          {/* Ticks are positioned along the bar, so their labels have to be
              anchored to the same percentages rather than space-between. */}
          {budget.thresholds.map((threshold) => (
            <span key={threshold}>
              <span
                className="absolute -top-1 h-4.5 w-px bg-foreground/40"
                style={{ left: `${threshold}%` }}
                title={`${threshold}% alert threshold`}
              />
              <span
                className="-translate-x-1/2 absolute top-4 text-[10px] text-muted-foreground tabular-nums"
                style={{ left: `${threshold}%` }}
              >
                {threshold}
              </span>
            </span>
          ))}
        </div>
        <p className="mt-8 text-muted-foreground text-xs">
          Projected {formatUsd(budget.projected_month_usd)} by month end. Alert
          thresholds match the AWS Budget.
        </p>
      </div>
    </ChartCard>
  );
};

/**
 * Month-to-date burn-up: cumulative spend against a linear pace line. The gap
 * between the two is the answer to "are we going to overshoot?".
 */
export const BurnUpChart = ({ summary }: { summary: CostSummary }) => {
  const { days, budget } = summary;
  if (days.length === 0) {
    return (
      <ChartCard title="Month to date" description="Cumulative spend vs pace">
        <p className="py-8 text-center text-muted-foreground text-xs">
          No runs yet this month.
        </p>
      </ChartCard>
    );
  }

  let running = 0;
  const cumulative = days.map((day) => {
    running += day.total_usd;
    return running;
  });

  const daysInMonth = new Date(
    Number(days[0].date.slice(0, 4)),
    Number(days[0].date.slice(5, 7)),
    0,
  ).getDate();
  const target = budget.monthly_limit_usd ?? budget.projected_month_usd;
  const pace = days.map(
    (day) => (target / daysInMonth) * Number(day.date.slice(8, 10)),
  );

  return (
    <ChartCard
      title="Month to date"
      description={`Cumulative spend against ${
        budget.monthly_limit_usd === null ? "projected" : "budget"
      } pace`}
    >
      <AreaChart
        labels={days.map((day) => day.date.slice(8, 10))}
        series={[
          { key: "spend", label: "Cumulative spend", color: "var(--cost-tts)" },
          {
            key: "pace",
            label:
              budget.monthly_limit_usd === null ? "Projection" : "Budget pace",
            color: "var(--muted-foreground)",
          },
        ]}
        values={[cumulative, pace]}
        stacked={false}
        formatValue={formatUsd}
        emptyMessage="No runs yet this month."
        summary={`Cumulative spend reaches ${formatUsd(running)} by day ${days.at(-1)?.date.slice(8, 10)}`}
      />
    </ChartCard>
  );
};
