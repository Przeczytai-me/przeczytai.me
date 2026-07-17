"use client";

import { useInfiniteQuery } from "@tanstack/react-query";
import { RefreshCw } from "lucide-react";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { dictionary } from "@/i18n/dictionaries";
import { listReadings } from "@/lib/api";
import { ReadingRow } from "./reading-row";

export const ReadingsList = () => {
  const copy = dictionary.app.documents;

  const {
    data,
    error,
    fetchNextPage,
    hasNextPage,
    isFetching,
    isFetchingNextPage,
    isLoading,
    refetch,
  } = useInfiniteQuery({
    queryKey: ["readings"],
    queryFn: ({ pageParam }) => listReadings(20, pageParam),
    initialPageParam: null as string | null,
    getNextPageParam: (lastPage) => lastPage.next_cursor ?? undefined,
  });

  const readings = data?.pages.flatMap((page) => page.items) ?? [];

  return (
    <section className="flex flex-col gap-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="font-semibold text-2xl">{copy.heading}</h1>
          <p className="text-muted-foreground text-sm">{copy.description}</p>
        </div>
        <Link
          href="/app/new"
          className="inline-flex h-9 items-center rounded-md bg-primary px-3 text-primary-foreground text-sm hover:bg-primary/90"
        >
          {copy.newDocument}
        </Link>
      </div>

      <div className="grid gap-3 sm:grid-cols-3">
        <SummaryItem label={copy.summary.total} value={readings.length} />
        <SummaryItem
          label={copy.summary.processing}
          value={
            readings.filter((reading) => reading.status !== "completed").length
          }
        />
        <SummaryItem
          label={copy.summary.ready}
          value={
            readings.filter((reading) => reading.status === "completed").length
          }
        />
      </div>

      <div className="flex items-center justify-between gap-2 rounded-md border border-border bg-background px-3 py-2">
        <div className="flex min-w-0 gap-2">
          <input
            className="h-8 w-48 rounded-md border border-input bg-background px-3 text-sm"
            placeholder={copy.searchPlaceholder}
            type="search"
          />
          <select className="h-8 rounded-md border border-input bg-background px-2 text-sm">
            <option>{copy.statusFilter}</option>
          </select>
        </div>
        <Button
          type="button"
          onClick={() => refetch()}
          disabled={isFetching}
          variant="outline"
        >
          <RefreshCw className="size-3.5" aria-hidden="true" />
          {isFetching && !isFetchingNextPage ? copy.refreshing : copy.refresh}
        </Button>
      </div>

      {isLoading && (
        <p className="text-muted-foreground text-sm">{copy.loading}</p>
      )}
      {error && <p className="text-sm text-destructive">{String(error)}</p>}
      {!isLoading && readings.length === 0 && (
        <div className="rounded-md border border-dashed border-border bg-background p-8 text-center">
          <p className="font-medium">{copy.emptyTitle}</p>
          <Link
            href="/app/new"
            className="mt-3 inline-flex h-8 items-center rounded-md border border-border px-3 text-sm hover:bg-muted"
          >
            {copy.emptyAction}
          </Link>
        </div>
      )}
      <div className="grid gap-3">
        {readings.map((reading) => (
          <ReadingRow key={reading.id} reading={reading} />
        ))}
      </div>
      {hasNextPage && (
        <div className="flex items-center gap-2 pt-1">
          <Button
            type="button"
            onClick={() => fetchNextPage()}
            disabled={isFetchingNextPage}
            variant="outline"
          >
            {isFetchingNextPage ? copy.loadingMore : copy.next}
          </Button>
        </div>
      )}
    </section>
  );
};

const SummaryItem = ({ label, value }: { label: string; value?: number }) => (
  <div className="rounded-md border border-border bg-background p-4">
    <p className="text-muted-foreground text-sm">{label}</p>
    <p className="mt-1 font-semibold text-2xl">{value ?? "..."}</p>
  </div>
);
