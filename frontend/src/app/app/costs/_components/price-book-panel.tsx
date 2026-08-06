"use client";

import { TriangleAlert } from "lucide-react";
import type { CostSummary } from "@/lib/costs-api";
import { formatChars, formatUsd } from "@/lib/format-cost";
import { ChartCard } from "./charts/chart-kit";

const OMISSIONS = [
  "Lambda cold start and init are excluded — compute is measured in-process, so the figure runs low.",
  "S3 storage is charged as one month at run time; ongoing retention accrues every month after.",
  "DynamoDB and API Gateway are a flat per-run constant, not counted per call.",
  "edge-tts is priced at zero: it is an unofficial free endpoint with no contract or SLA.",
];

export const PriceBookPanel = ({ summary }: { summary: CostSummary }) => (
  <ChartCard
    title="Assumptions"
    description={`Price book ${summary.price_book_version}`}
  >
    <div className="space-y-3">
      <div className="flex gap-2 rounded-md border border-border bg-muted/40 p-2.5">
        <TriangleAlert
          className="mt-0.5 size-3.5 shrink-0 text-[var(--cost-storage)]"
          aria-hidden="true"
        />
        <p className="text-muted-foreground text-xs">
          These are <strong className="text-foreground">estimates</strong>, not
          a bill, and the prices are{" "}
          <strong className="text-foreground">unverified</strong>. Verify them
          against vendor pricing pages before quoting any figure. Relative
          comparisons stay valid regardless.
        </p>
      </div>

      <dl className="space-y-1.5 text-xs">
        <div className="flex justify-between gap-3">
          <dt className="text-muted-foreground">Per-run cost cap</dt>
          <dd className="font-medium tabular-nums">
            {formatUsd(summary.limits.max_run_cost_usd)}
          </dd>
        </div>
        <div className="flex justify-between gap-3">
          <dt className="text-muted-foreground">Max text length</dt>
          <dd className="font-medium tabular-nums">
            {formatChars(summary.limits.max_text_chars)} chars
          </dd>
        </div>
        <div className="flex justify-between gap-3">
          <dt className="text-muted-foreground">Monthly budget</dt>
          <dd className="font-medium tabular-nums">
            {summary.limits.monthly_budget_usd === null
              ? "not set"
              : formatUsd(summary.limits.monthly_budget_usd)}
          </dd>
        </div>
        <div className="flex justify-between gap-3">
          <dt className="text-muted-foreground">Storage this month</dt>
          <dd className="font-medium tabular-nums">
            {formatUsd(summary.totals.retained_storage_usd_per_month)}
          </dd>
        </div>
      </dl>

      <div>
        <p className="mb-1.5 font-medium text-xs">Knowingly omitted</p>
        <ul className="space-y-1">
          {OMISSIONS.map((omission) => (
            <li
              key={omission}
              className="text-muted-foreground text-[11px] leading-relaxed"
            >
              • {omission}
            </li>
          ))}
        </ul>
      </div>
    </div>
  </ChartCard>
);
