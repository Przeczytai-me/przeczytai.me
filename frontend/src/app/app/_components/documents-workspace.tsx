"use client";

import { useInfiniteQuery } from "@tanstack/react-query";
import { AlertCircle, Plus, RefreshCw } from "lucide-react";
import Link from "next/link";
import { useMemo, useState } from "react";
import { Button, buttonVariants } from "@/components/ui/button";
import { dictionary } from "@/i18n/dictionaries";
import { listReadings } from "@/lib/api";
import { cn } from "@/lib/utils";
import {
  DocumentSort,
  DocumentStatusFilter,
  filterAndSortReadings,
} from "../_utils/documents-workspace";
import { DocumentsSummary } from "./documents-summary";
import { DocumentsTable } from "./documents-table";
import { DocumentsWorkspaceToolbar } from "./documents-workspace-toolbar";

const copy = dictionary.app.documents;
const DOCUMENTS_PAGE_SIZE = 20;

export const DocumentsWorkspace = () => {
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState<DocumentStatusFilter>(
    DocumentStatusFilter.all,
  );
  const [sort, setSort] = useState<DocumentSort>(DocumentSort.newest);

  const documentsQuery = useInfiniteQuery({
    queryKey: ["readings"],
    queryFn: ({ pageParam }) => listReadings(DOCUMENTS_PAGE_SIZE, pageParam),
    initialPageParam: null as string | null,
    getNextPageParam: (lastPage) => lastPage.next_cursor ?? undefined,
  });
  const readings =
    documentsQuery.data?.pages.flatMap((page) => page.items) ?? [];

  const visibleReadings = useMemo(
    () =>
      filterAndSortReadings(
        readings,
        search,
        statusFilter,
        sort,
        copy.titleFallback,
      ),
    [readings, search, statusFilter, sort],
  );

  const resetFilters = () => {
    setSearch("");
    setStatusFilter(DocumentStatusFilter.all);
  };

  return (
    <section className="flex min-w-0 w-full flex-col gap-5 pb-12">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h1 className="font-semibold text-2xl">{copy.heading}</h1>
          <p className="mt-1 text-muted-foreground text-sm">
            {copy.description}
          </p>
        </div>
        <Link
          className={cn(buttonVariants({ size: "lg" }), "gap-2")}
          href="/app/new"
        >
          <Plus aria-hidden="true" />
          {copy.newDocument}
        </Link>
      </div>

      <DocumentsSummary
        isLoading={documentsQuery.isLoading}
        readings={readings}
      />

      <DocumentsWorkspaceToolbar
        isFetching={
          documentsQuery.isFetching && !documentsQuery.isFetchingNextPage
        }
        onRefresh={() => documentsQuery.refetch()}
        onSearchChange={setSearch}
        onSortChange={setSort}
        onStatusFilterChange={setStatusFilter}
        search={search}
        sort={sort}
        statusFilter={statusFilter}
      />

      {documentsQuery.isError ? (
        <div
          className="flex flex-col items-start gap-3 rounded-lg border border-destructive/20 bg-destructive/5 p-5"
          role="alert"
        >
          <div className="flex items-start gap-3">
            <AlertCircle
              aria-hidden="true"
              className="mt-0.5 size-5 shrink-0 text-destructive"
            />
            <div>
              <h2 className="font-medium">{copy.error.title}</h2>
              <p className="mt-1 text-muted-foreground text-sm">
                {copy.error.description}
              </p>
            </div>
          </div>
          <Button
            onClick={() => documentsQuery.refetch()}
            type="button"
            variant="outline"
          >
            <RefreshCw aria-hidden="true" />
            {copy.error.retry}
          </Button>
        </div>
      ) : documentsQuery.isLoading ? (
        <DocumentsTable isLoading readings={[]} />
      ) : readings.length === 0 ? (
        <div className="rounded-lg border border-dashed border-border bg-background p-10 text-center">
          <h2 className="font-medium">{copy.emptyTitle}</h2>
          <p className="mx-auto mt-1 max-w-md text-muted-foreground text-sm">
            {copy.emptyDescription}
          </p>
          <Link
            className={cn(buttonVariants({ variant: "outline" }), "mt-4")}
            href="/app/new"
          >
            <Plus aria-hidden="true" />
            {copy.emptyAction}
          </Link>
        </div>
      ) : visibleReadings.length === 0 ? (
        <div className="rounded-lg border border-dashed border-border bg-background p-8 text-center">
          <h2 className="font-medium">{copy.filteredEmpty.title}</h2>
          <p className="mt-1 text-muted-foreground text-sm">
            {copy.filteredEmpty.description}
          </p>
          <Button
            className="mt-4"
            onClick={resetFilters}
            type="button"
            variant="outline"
          >
            {copy.filteredEmpty.reset}
          </Button>
        </div>
      ) : (
        <>
          <p aria-live="polite" className="text-muted-foreground text-xs">
            {copy.results(visibleReadings.length, readings.length)}
          </p>
          <DocumentsTable readings={visibleReadings} />
        </>
      )}

      {documentsQuery.hasNextPage && !documentsQuery.isError && (
        <div className="flex justify-center">
          <Button
            disabled={documentsQuery.isFetchingNextPage}
            onClick={() => documentsQuery.fetchNextPage()}
            type="button"
            variant="outline"
          >
            <RefreshCw
              aria-hidden="true"
              className={cn(
                documentsQuery.isFetchingNextPage && "animate-spin",
              )}
            />
            {documentsQuery.isFetchingNextPage
              ? copy.loadingMore
              : copy.loadMore}
          </Button>
        </div>
      )}
    </section>
  );
};
