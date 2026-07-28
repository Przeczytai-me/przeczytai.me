import { dictionary } from "@/i18n/dictionaries";
import type { Reading } from "@/lib/api";
import { DocumentTableRow } from "./document-table-row";

const copy = dictionary.app.documents.table;
const loadingRows = ["loading-1", "loading-2", "loading-3", "loading-4"];

type DocumentsTableProps = {
  isLoading?: boolean;
  readings: Reading[];
};

export const DocumentsTable = ({
  isLoading = false,
  readings,
}: DocumentsTableProps) => (
  <div className="overflow-x-auto rounded-lg border border-border bg-background">
    <table className="w-full min-w-260 border-collapse text-left text-sm">
      <caption className="sr-only">{copy.caption}</caption>
      <thead className="border-border border-b bg-muted/40 text-muted-foreground text-xs">
        <tr>
          <th className="w-[24%] px-4 py-3 font-medium" scope="col">
            {copy.document}
          </th>
          <th className="w-[15%] px-3 py-3 font-medium" scope="col">
            {copy.source}
          </th>
          <th className="w-[12%] px-3 py-3 font-medium" scope="col">
            {copy.status}
          </th>
          <th className="w-[17%] px-3 py-3 font-medium" scope="col">
            {copy.voiceModel}
          </th>
          <th className="w-[12%] px-3 py-3 font-medium" scope="col">
            {copy.size}
          </th>
          <th className="px-4 py-3 text-right font-medium" scope="col">
            {copy.actions}
          </th>
        </tr>
      </thead>
      <tbody className="divide-y divide-border">
        {isLoading
          ? loadingRows.map((row) => (
              <tr key={row}>
                <td className="px-4 py-4" colSpan={6}>
                  <div className="h-8 animate-pulse rounded-md bg-muted" />
                </td>
              </tr>
            ))
          : readings.map((reading) => (
              <DocumentTableRow key={reading.id} reading={reading} />
            ))}
      </tbody>
    </table>
  </div>
);
