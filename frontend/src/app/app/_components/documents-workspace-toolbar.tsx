import { RefreshCw, Search } from "lucide-react";
import { Button } from "@/components/ui/button";
import { dictionary } from "@/i18n/dictionaries";
import { cn } from "@/lib/utils";
import {
  DocumentSort,
  type DocumentSort as DocumentSortValue,
  DocumentStatusFilter,
  type DocumentStatusFilter as DocumentStatusFilterValue,
} from "../_utils/documents-workspace";

const copy = dictionary.app.documents;

type DocumentsWorkspaceToolbarProps = {
  isFetching: boolean;
  onRefresh: () => void;
  onSearchChange: (value: string) => void;
  onSortChange: (value: DocumentSortValue) => void;
  onStatusFilterChange: (value: DocumentStatusFilterValue) => void;
  search: string;
  sort: DocumentSortValue;
  statusFilter: DocumentStatusFilterValue;
};

export const DocumentsWorkspaceToolbar = ({
  isFetching,
  onRefresh,
  onSearchChange,
  onSortChange,
  onStatusFilterChange,
  search,
  sort,
  statusFilter,
}: DocumentsWorkspaceToolbarProps) => (
  <search
    aria-label={copy.toolbar.label}
    className="flex flex-col gap-3 rounded-lg border border-border bg-background p-3 lg:flex-row lg:items-center"
  >
    <label className="relative min-w-0 flex-1">
      <span className="sr-only">{copy.toolbar.searchLabel}</span>
      <Search
        aria-hidden="true"
        className="absolute top-1/2 left-3 size-4 -translate-y-1/2 text-muted-foreground"
      />
      <input
        className="h-9 w-full rounded-md border border-input bg-background pr-3 pl-9 text-sm outline-none placeholder:text-muted-foreground focus-visible:border-ring focus-visible:ring-3 focus-visible:ring-ring/50"
        onChange={(event) => onSearchChange(event.target.value)}
        placeholder={copy.searchPlaceholder}
        type="search"
        value={search}
      />
    </label>

    <label className="grid gap-1 lg:min-w-44">
      <span className="sr-only">{copy.toolbar.statusLabel}</span>
      <select
        className="h-9 rounded-md border border-input bg-background px-3 text-sm outline-none focus-visible:border-ring focus-visible:ring-3 focus-visible:ring-ring/50"
        onChange={(event) =>
          onStatusFilterChange(event.target.value as DocumentStatusFilterValue)
        }
        value={statusFilter}
      >
        <option value={DocumentStatusFilter.all}>{copy.filters.all}</option>
        <option value={DocumentStatusFilter.processing}>
          {copy.filters.processing}
        </option>
        <option value={DocumentStatusFilter.ready}>{copy.filters.ready}</option>
        <option value={DocumentStatusFilter.failed}>
          {copy.filters.failed}
        </option>
      </select>
    </label>

    <label className="grid gap-1 lg:min-w-48">
      <span className="sr-only">{copy.toolbar.sortLabel}</span>
      <select
        className="h-9 rounded-md border border-input bg-background px-3 text-sm outline-none focus-visible:border-ring focus-visible:ring-3 focus-visible:ring-ring/50"
        onChange={(event) =>
          onSortChange(event.target.value as DocumentSortValue)
        }
        value={sort}
      >
        <option value={DocumentSort.newest}>{copy.sort.newest}</option>
        <option value={DocumentSort.oldest}>{copy.sort.oldest}</option>
        <option value={DocumentSort.titleAscending}>
          {copy.sort.titleAscending}
        </option>
        <option value={DocumentSort.titleDescending}>
          {copy.sort.titleDescending}
        </option>
      </select>
    </label>

    <Button
      disabled={isFetching}
      onClick={onRefresh}
      type="button"
      variant="outline"
    >
      <RefreshCw
        aria-hidden="true"
        className={cn(isFetching && "animate-spin")}
      />
      {isFetching ? copy.refreshing : copy.refresh}
    </Button>
  </search>
);
