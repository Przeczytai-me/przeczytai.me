"use client";

import { useQuery } from "@tanstack/react-query";
import { notFound } from "next/navigation";
import { ApiError } from "@/lib/api";
import { getCosts } from "@/lib/costs-api";
import { BudgetMeter, BurnUpChart } from "./_components/budget-panel";
import { ChartSkeleton } from "./_components/charts/chart-kit";
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

const MONTHS = 6;

export const CostsDashboard = () => {
  const { data, isLoading, error } = useQuery({
    queryKey: ["costs", MONTHS],
    queryFn: () => getCosts(MONTHS),
    retry: (count, err) =>
      err instanceof ApiError && err.status === 403 ? false : count < 2,
  });

  // A non-admin gets the ordinary not-found page. An "access denied" screen
  // would itself be new information about a feature they cannot use.
  if (
    error instanceof ApiError &&
    (error.status === 403 || error.status === 401)
  ) {
    notFound();
  }

  if (isLoading || !data) {
    return (
      <div className="space-y-6">
        <header>
          <h1 className="font-semibold text-xl">Costs</h1>
          <p className="mt-1 text-muted-foreground text-sm">
            Internal infrastructure cost estimates.
          </p>
        </header>
        <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-3 2xl:grid-cols-6">
          {["a", "b", "c", "d", "e", "f"].map((key) => (
            <ChartSkeleton key={key} height={96} />
          ))}
        </div>
        <div className="grid gap-3 lg:grid-cols-2">
          {["g", "h", "i", "j"].map((key) => (
            <ChartSkeleton key={key} height={220} />
          ))}
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="rounded-lg border border-destructive/40 bg-destructive/5 p-6">
        <h1 className="font-semibold text-lg">Costs unavailable</h1>
        <p className="mt-1 text-muted-foreground text-sm">
          The cost API could not be reached. {String(error)}
        </p>
      </div>
    );
  }

  const hasAnyData = data.totals.runs_all_time > 0;

  return (
    <div className="space-y-6 pb-10">
      <header>
        <div className="flex flex-wrap items-baseline justify-between gap-2">
          <h1 className="font-semibold text-xl">Costs</h1>
          <p className="text-muted-foreground text-xs">
            price book {data.price_book_version} · USD · last {MONTHS} months
          </p>
        </div>
        <p className="mt-1 max-w-3xl text-muted-foreground text-sm">
          Internal estimates of what running the system costs — infrastructure,
          not billing. Figures are computed from a versioned, unverified price
          book and are not customer charges.
        </p>
      </header>

      {!hasAnyData ? (
        <div className="rounded-lg border border-border border-dashed p-10 text-center">
          <h2 className="font-medium text-sm">No runs recorded yet</h2>
          <p className="mx-auto mt-2 max-w-md text-muted-foreground text-xs leading-relaxed">
            Once a document finishes processing, its cost is recorded and this
            page fills in: spend over time, the split across TTS, compute and
            storage, which vendors and documents drive it, and a per-run
            breakdown.
          </p>
        </div>
      ) : (
        <>
          <KpiTiles summary={data} />

          <div className="grid gap-3 lg:grid-cols-3">
            <BudgetMeter summary={data} />
            <div className="lg:col-span-2">
              <BurnUpChart summary={data} />
            </div>
          </div>

          <div className="grid gap-3 lg:grid-cols-2">
            <CostOverTime summary={data} />
            <CompositionDonut summary={data} />
          </div>

          <div className="grid gap-3 lg:grid-cols-2">
            <VendorBreakdown summary={data} />
            <CharsCostScatter summary={data} />
          </div>

          <div className="grid gap-3 lg:grid-cols-3">
            <DailyHeatmap summary={data} />
            <UnitEconomics summary={data} />
            <FreeVsPaid summary={data} />
          </div>

          <RunExplorer summary={data} />

          <div className="grid gap-3 lg:grid-cols-2">
            <UserDistribution summary={data} />
            <PriceBookPanel summary={data} />
          </div>

          <CostCalculator />
        </>
      )}
    </div>
  );
};
