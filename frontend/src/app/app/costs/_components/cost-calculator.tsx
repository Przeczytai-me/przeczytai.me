"use client";

import { useQuery } from "@tanstack/react-query";
import { useEffect, useState } from "react";
import { estimateCost } from "@/lib/costs-api";
import {
  COST_COMPONENT_COLOR,
  COST_COMPONENT_LABEL,
  COST_COMPONENTS,
  formatChars,
  formatDurationMs,
  formatUsd,
} from "@/lib/format-cost";
import { BarTrack } from "./charts/bar-list";
import { ChartCard } from "./charts/chart-kit";

const SAMPLE = "Ala ma kota. ".repeat(400);

/**
 * Developer calculator: what would this text cost, on each vendor? Prices the
 * same text across every configured vendor with that vendor's own input limit
 * applied, so a rejection shows up as a rejection rather than as a number.
 */
export const CostCalculator = () => {
  const [text, setText] = useState(SAMPLE);
  const [debounced, setDebounced] = useState(SAMPLE);

  useEffect(() => {
    const timer = setTimeout(() => setDebounced(text), 400);
    return () => clearTimeout(timer);
  }, [text]);

  const { data, isFetching } = useQuery({
    queryKey: ["cost-estimate", debounced],
    queryFn: () => estimateCost(debounced),
    enabled: debounced.trim().length > 0,
  });

  return (
    <ChartCard
      title="Cost calculator"
      description="Price arbitrary text across every vendor before running it"
    >
      <div className="grid gap-3 lg:grid-cols-2">
        <div>
          <label
            htmlFor="calculator-text"
            className="mb-1.5 block text-muted-foreground text-xs"
          >
            Text to price
          </label>
          <textarea
            id="calculator-text"
            value={text}
            onChange={(event) => setText(event.target.value)}
            rows={8}
            className="scrollbar-subtle w-full resize-y rounded-md border border-border bg-background p-2.5 font-mono text-xs"
            spellCheck={false}
          />
          <p className="mt-1.5 text-muted-foreground text-xs tabular-nums">
            {formatChars(text.length)} characters
            {data ? ` · ${data.chunk_count} chunks` : ""}
            {isFetching ? " · estimating…" : ""}
          </p>
        </div>

        <div>
          {data ? (
            <ul className="space-y-3">
              {data.vendors.map((vendor) => (
                <li
                  key={`${vendor.vendor}-${vendor.voice}`}
                  className="rounded-md border border-border p-2.5"
                >
                  <div className="flex items-baseline justify-between gap-2">
                    <span className="font-medium text-xs">
                      {vendor.vendor}
                      <span className="ml-1.5 text-muted-foreground">
                        {vendor.voice}
                      </span>
                    </span>
                    <span className="font-semibold text-sm tabular-nums">
                      {formatUsd(vendor.cost.total_usd)}
                    </span>
                  </div>
                  <div className="mt-1.5">
                    <BarTrack
                      segments={COST_COMPONENTS.map((key) => ({
                        key,
                        label: COST_COMPONENT_LABEL[key],
                        value: vendor.cost.components[key],
                        color: COST_COMPONENT_COLOR[key],
                      }))}
                      ariaLabel={`${vendor.vendor} cost components`}
                      height={6}
                    />
                  </div>
                  <p className="mt-1.5 text-[11px] text-muted-foreground tabular-nums">
                    ≈ {formatDurationMs(vendor.estimated_audio_ms)} of audio
                  </p>
                  {vendor.allowed ? null : (
                    <p className="mt-1.5 text-[11px] text-destructive">
                      Rejected — {vendor.rejection?.message}
                    </p>
                  )}
                </li>
              ))}
            </ul>
          ) : (
            <p className="py-8 text-center text-muted-foreground text-xs">
              {debounced.trim()
                ? "Estimating…"
                : "Enter some text to price it."}
            </p>
          )}
        </div>
      </div>
    </ChartCard>
  );
};
