import {
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { dictionary } from "@/i18n/dictionaries";
import type { Reading } from "@/lib/api";
import { ReaderDownloadButton } from "./reader-download-button";

const copy = dictionary.app.reader;

type ReaderDownloadsDialogProps = {
  downloadError: string;
  isOriginalAvailable: boolean;
  onDownload: (path: string, filename: string) => Promise<void>;
  reading: Reading;
};

export const ReaderDownloadsDialog = ({
  downloadError,
  isOriginalAvailable,
  onDownload,
  reading,
}: ReaderDownloadsDialogProps) => (
  <DialogContent closeLabel={copy.dialog.close}>
    <DialogHeader>
      <DialogTitle>{copy.details.downloadsTitle}</DialogTitle>
      <DialogDescription>{copy.details.downloadsDescription}</DialogDescription>
    </DialogHeader>
    <div className="grid gap-2">
      <ReaderDownloadButton
        disabled={!reading.recording_key}
        label={copy.details.actions.downloadMp3}
        onClick={() =>
          void onDownload(
            `/api/v1/readings/${reading.id}/recording`,
            `${reading.id}-recording.mp3`,
          )
        }
      />
      <ReaderDownloadButton
        disabled={!reading.corrected_text_key}
        label={copy.details.actions.downloadCorrected}
        onClick={() =>
          void onDownload(
            `/api/v1/readings/${reading.id}/corrected-text`,
            `${reading.id}-corrected.md`,
          )
        }
      />
      <ReaderDownloadButton
        disabled={!isOriginalAvailable}
        label={copy.details.actions.downloadOriginal}
        onClick={() =>
          void onDownload(
            `/api/v1/readings/${reading.id}/original-text`,
            `${reading.id}-original.txt`,
          )
        }
      />
      {downloadError && (
        <p
          aria-live="polite"
          className="text-destructive text-xs"
          role="status"
        >
          {downloadError}
        </p>
      )}
    </div>
  </DialogContent>
);
