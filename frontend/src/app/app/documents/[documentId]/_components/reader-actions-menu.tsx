"use client";

import {
  FileDown,
  Highlighter,
  Info,
  MoreVertical,
  RefreshCw,
} from "lucide-react";
import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Dialog } from "@/components/ui/dialog";
import {
  DropdownMenu,
  DropdownMenuCheckboxItem,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { dictionary } from "@/i18n/dictionaries";
import type { Reading } from "@/lib/api";
import { downloadFile } from "@/lib/api";
import { ReaderDetailsDialog } from "./reader-details-dialog";
import { ReaderDownloadsDialog } from "./reader-downloads-dialog";
import { ReaderRegenerateDialog } from "./reader-regenerate-dialog";

const copy = dictionary.app.reader;
type ReaderDialog = "details" | "downloads" | "regenerate";

type ReaderActionsMenuProps = {
  autoHighlight: boolean;
  durationMs?: number;
  isOriginalAvailable: boolean;
  isRetrying: boolean;
  onAutoHighlightChange: (enabled: boolean) => void;
  onRetry: () => void;
  reading: Reading;
  retryError?: string;
};

export const ReaderActionsMenu = ({
  autoHighlight,
  durationMs,
  isOriginalAvailable,
  isRetrying,
  onAutoHighlightChange,
  onRetry,
  reading,
  retryError,
}: ReaderActionsMenuProps) => {
  const [activeDialog, setActiveDialog] = useState<ReaderDialog | null>(null);
  const [downloadError, setDownloadError] = useState("");

  const openDialog = (dialog: ReaderDialog) => {
    setDownloadError("");
    setActiveDialog(dialog);
  };

  const handleDownload = async (path: string, filename: string) => {
    setDownloadError("");
    try {
      await downloadFile(path, filename);
    } catch {
      setDownloadError(copy.details.downloadError);
    }
  };

  return (
    <>
      <DropdownMenu>
        <DropdownMenuTrigger
          render={
            <Button
              aria-label={copy.menu.label}
              size="icon"
              title={copy.menu.label}
              variant="outline"
            />
          }
        >
          <MoreVertical aria-hidden="true" />
        </DropdownMenuTrigger>
        <DropdownMenuContent>
          <DropdownMenuCheckboxItem
            checked={autoHighlight}
            onCheckedChange={onAutoHighlightChange}
          >
            <Highlighter aria-hidden="true" />
            {copy.menu.autoHighlight}
          </DropdownMenuCheckboxItem>
          <DropdownMenuSeparator />
          <DropdownMenuItem onClick={() => openDialog("details")}>
            <Info aria-hidden="true" />
            {copy.menu.details}
          </DropdownMenuItem>
          <DropdownMenuItem onClick={() => openDialog("downloads")}>
            <FileDown aria-hidden="true" />
            {copy.menu.downloads}
          </DropdownMenuItem>
          <DropdownMenuSeparator />
          <DropdownMenuItem
            onClick={() => openDialog("regenerate")}
            variant="destructive"
          >
            <RefreshCw aria-hidden="true" />
            {copy.menu.regenerate}
          </DropdownMenuItem>
        </DropdownMenuContent>
      </DropdownMenu>

      <Dialog
        open={activeDialog !== null}
        onOpenChange={(open) => {
          if (!open) setActiveDialog(null);
        }}
      >
        {activeDialog === "details" && (
          <ReaderDetailsDialog durationMs={durationMs} reading={reading} />
        )}
        {activeDialog === "downloads" && (
          <ReaderDownloadsDialog
            downloadError={downloadError}
            isOriginalAvailable={isOriginalAvailable}
            onDownload={handleDownload}
            reading={reading}
          />
        )}
        {activeDialog === "regenerate" && (
          <ReaderRegenerateDialog
            isRetrying={isRetrying}
            onRetry={onRetry}
            retryError={retryError}
          />
        )}
      </Dialog>
    </>
  );
};
