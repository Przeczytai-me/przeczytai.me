"use client";

import type { CostSummary } from "@/lib/costs-api";
import { BudgetMeter, BurnUpChart } from "./_components/budget-panel";
import { CostCalculator } from "./_components/cost-calculator";
import {
  CharsCostScatter,
  CompositionDonut,
  CostOverTime,
  DailyHeatmap,
  FreeVsPaid,
  UnitEconomics,
  UserDistribution,
  VendorBreakdown,
} from "./_components/driver-panels";
import { KpiTiles } from "./_components/kpi-tiles";
import { PriceBookPanel } from "./_components/price-book-panel";
import { RunExplorer } from "./_components/run-explorer";

/**
 * Data is fetched and authorised on the server (see page.tsx), so this
 * component is purely presentational and needs no loading or forbidden state.
 */
export const CostsDashboard = ({
  summary,
  months,
}: {
  summary: CostSummary;
  months: number;
}) => {
  const hasAnyData = summary.totals.runs_all_time > 0;

  return (
    <div className="space-y-6 pb-10">
      <header>
        <div className="flex flex-wrap items-baseline justify-between gap-2">
          <h1 className="font-semibold text-xl">Costs</h1>
          <p className="text-muted-foreground text-xs">
            price book {summary.price_book_version} · USD · last {months} months
          </p>
        </div>
        <p className="mt-1 max-w-3xl text-muted-foreground text-sm">
          Internal estimates of what running the system costs — infrastructure,
          not billing. Figures are computed from a versioned, unverified price
          book and are not customer charges.
        </p>
      </header>

      {hasAnyData ? (
        <>
          <KpiTiles summary={summary} />

          <div className="grid gap-3 lg:grid-cols-3">
            <BudgetMeter summary={summary} />
            <div className="lg:col-span-2">
              <BurnUpChart summary={summary} />
            </div>
          </div>

          <div className="grid gap-3 lg:grid-cols-2">
            <CostOverTime summary={summary} />
            <CompositionDonut summary={summary} />
          </div>

          <div className="grid gap-3 lg:grid-cols-2">
            <VendorBreakdown summary={summary} />
            <CharsCostScatter summary={summary} />
          </div>

          <div className="grid gap-3 lg:grid-cols-3">
            <DailyHeatmap summary={summary} />
            <UnitEconomics summary={summary} />
            <FreeVsPaid summary={summary} />
          </div>

          <RunExplorer summary={summary} />

          <div className="grid gap-3 lg:grid-cols-2">
            <UserDistribution summary={summary} />
            <PriceBookPanel summary={summary} />
          </div>
        </>
      ) : (
        <div className="rounded-lg border border-border border-dashed p-10 text-center">
          <h2 className="font-medium text-sm">No runs recorded yet</h2>
          <p className="mx-auto mt-2 max-w-md text-muted-foreground text-xs leading-relaxed">
            Once a document finishes processing, its cost is recorded and this
            page fills in: spend over time, the split across TTS, compute and
            storage, which vendors and documents drive it, and a per-run
            breakdown.
          </p>
        </div>
      )}

      <CostCalculator />
    </div>
  );
};
