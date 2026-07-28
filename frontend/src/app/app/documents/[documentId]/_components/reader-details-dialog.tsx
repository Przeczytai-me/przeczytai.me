import { CalendarClock, FileAudio, FileText, Sparkles } from "lucide-react";
import { ReadingStatusBadge } from "@/app/app/_components/reading-status-badge";
import {
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { dictionary } from "@/i18n/dictionaries";
import type { Reading } from "@/lib/api";
import { formatPolishDateTime } from "@/lib/date-time";
import { formatDurationMs } from "@/lib/duration";
import { formatPolishCount } from "@/lib/pluralize";
import { ReaderDetailRow } from "./reader-detail-row";

const copy = dictionary.app.reader;

type ReaderDetailsDialogProps = {
  durationMs?: number;
  reading: Reading;
};

export const ReaderDetailsDialog = ({
  durationMs,
  reading,
}: ReaderDetailsDialogProps) => (
  <DialogContent className="sm:max-w-lg" closeLabel={copy.dialog.close}>
    <DialogHeader>
      <DialogTitle>{copy.details.title}</DialogTitle>
      <DialogDescription>{copy.details.description}</DialogDescription>
    </DialogHeader>
    <dl className="grid gap-3 sm:grid-cols-2">
      <ReaderDetailRow
        icon={Sparkles}
        label={copy.details.status}
        value={<ReadingStatusBadge status={reading.status} />}
      />
      <ReaderDetailRow
        icon={FileText}
        label={copy.details.characters}
        value={formatPolishCount(reading.char_count, {
          one: "znak",
          few: "znaki",
          many: "znaków",
        })}
      />
      <ReaderDetailRow
        icon={CalendarClock}
        label={copy.details.created}
        value={formatPolishDateTime(reading.created_at)}
      />
      <ReaderDetailRow
        icon={CalendarClock}
        label={copy.details.updated}
        value={formatPolishDateTime(reading.updated_at)}
      />
      <ReaderDetailRow
        icon={Sparkles}
        label={copy.details.voice}
        value={reading.voice || copy.details.unknown}
      />
      <ReaderDetailRow
        icon={Sparkles}
        label={copy.details.model}
        value={reading.vendor || copy.details.unknown}
      />
      <ReaderDetailRow
        icon={FileAudio}
        label={copy.details.duration}
        value={durationMs ? formatDurationMs(durationMs) : copy.details.unknown}
      />
    </dl>
  </DialogContent>
);
