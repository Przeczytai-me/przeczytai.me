import { FileText } from "lucide-react";
import Link from "next/link";
import { dictionary } from "@/i18n/dictionaries";
import type { Reading } from "@/lib/api";
import { formatPolishDateTime } from "@/lib/date-time";
import { formatDurationMs } from "@/lib/duration";
import { formatPolishCount } from "@/lib/pluralize";
import {
  getMetadataDurationMs,
  getReadingModel,
  getReadingSourceType,
  getReadingTitle,
  getReadingVoice,
} from "@/lib/reading";
import { DocumentActions } from "./document-actions";
import { ReadingStatusBadge } from "./reading-status-badge";

const copy = dictionary.app.documents.row;

export const DocumentTableRow = ({ reading }: { reading: Reading }) => {
  const title = getReadingTitle(
    reading.metadata,
    dictionary.app.documents.titleFallback(reading.id),
  );
  const sourceType = getReadingSourceType(reading);
  const voice = getReadingVoice(reading);
  const model = getReadingModel(reading);
  const durationMs = getMetadataDurationMs(reading.metadata);

  return (
    <tr className="align-middle hover:bg-muted/25">
      <th className="px-4 py-3 font-normal" scope="row">
        <Link
          className="group flex min-w-0 items-center gap-2 font-medium hover:underline"
          href={`/app/documents/${reading.id}`}
        >
          <FileText
            aria-hidden="true"
            className="size-4 shrink-0 text-muted-foreground"
          />
          <span className="min-w-0 truncate">{title}</span>
        </Link>
        {title !== reading.id && (
          <p className="mt-1 max-w-64 truncate text-muted-foreground text-xs">
            {reading.id}
          </p>
        )}
      </th>
      <td className="px-3 py-3">
        <p>{sourceType ?? copy.unavailable}</p>
        <p className="mt-1 whitespace-nowrap text-muted-foreground text-xs">
          {formatPolishDateTime(reading.created_at)}
        </p>
      </td>
      <td className="px-3 py-3">
        <ReadingStatusBadge status={reading.status} />
      </td>
      <td className="px-3 py-3">
        <p className="truncate">{voice ?? copy.unavailable}</p>
        <p className="mt-1 truncate text-muted-foreground text-xs">
          {model ?? copy.unavailable}
        </p>
      </td>
      <td className="px-3 py-3">
        <p className="whitespace-nowrap">
          {formatPolishCount(reading.char_count, {
            one: "znak",
            few: "znaki",
            many: "znaków",
          })}
        </p>
        <p className="mt-1 text-muted-foreground text-xs">
          {durationMs ? formatDurationMs(durationMs) : copy.durationUnavailable}
        </p>
      </td>
      <td className="px-4 py-3">
        <DocumentActions reading={reading} title={title} />
      </td>
    </tr>
  );
};
