"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";
import {
  Download,
  ExternalLink,
  FileDown,
  FileInput,
  RefreshCw,
  Trash2,
} from "lucide-react";
import Link from "next/link";
import type { ReactNode } from "react";
import { useState } from "react";
import { Button, buttonVariants } from "@/components/ui/button";
import { Dialog } from "@/components/ui/dialog";
import { dictionary } from "@/i18n/dictionaries";
import type { Reading } from "@/lib/api";
import { deleteReading, downloadFile, retryReading } from "@/lib/api";
import {
  getReadingOriginalExtension,
  getReadingStatusGroup,
  ReadingStatusGroup,
} from "@/lib/reading";
import { cn } from "@/lib/utils";
import { DocumentDeleteDialog } from "./document-delete-dialog";
import { DocumentRetryDialog } from "./document-retry-dialog";

const copy = dictionary.app.documents;
const DocumentActionDialog = {
  delete: "delete",
  retry: "retry",
} as const;

type ActiveDialog =
  | (typeof DocumentActionDialog)[keyof typeof DocumentActionDialog]
  | null;

type DocumentActionsProps = {
  reading: Reading;
  title: string;
};

export const DocumentActions = ({ reading, title }: DocumentActionsProps) => {
  const queryClient = useQueryClient();
  const [activeDialog, setActiveDialog] = useState<ActiveDialog>(null);
  const [downloadError, setDownloadError] = useState("");
  const isProcessing =
    getReadingStatusGroup(reading.status) === ReadingStatusGroup.processing;

  const retryMutation = useMutation({
    mutationFn: () => retryReading(reading.id),
    onSuccess: async () => {
      setActiveDialog(null);
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ["readings"] }),
        queryClient.invalidateQueries({ queryKey: ["reading", reading.id] }),
      ]);
    },
  });

  const deleteMutation = useMutation({
    mutationFn: () => deleteReading(reading.id),
    onSuccess: async () => {
      setActiveDialog(null);
      await queryClient.invalidateQueries({ queryKey: ["readings"] });
    },
  });

  const handleDownload = async (path: string, filename: string) => {
    setDownloadError("");
    try {
      await downloadFile(path, filename);
    } catch {
      setDownloadError(copy.actions.downloadError);
    }
  };

  return (
    <>
      <fieldset className="flex min-w-max flex-wrap items-center justify-end gap-1">
        <legend className="sr-only">{copy.actions.label(title)}</legend>
        <Link
          aria-label={copy.actions.open}
          className={buttonVariants({ size: "icon-sm", variant: "ghost" })}
          href={`/app/documents/${reading.id}`}
          title={copy.actions.open}
        >
          <ExternalLink aria-hidden="true" />
        </Link>
        <IconAction
          disabled={!reading.recording_key}
          disabledReason={copy.actions.mp3Unavailable}
          icon={<Download aria-hidden="true" />}
          label={copy.actions.downloadMp3}
          onClick={() =>
            void handleDownload(
              `/api/v1/readings/${reading.id}/recording`,
              `${reading.id}-recording.mp3`,
            )
          }
        />
        <IconAction
          disabled={!reading.corrected_text_key}
          disabledReason={copy.actions.correctedUnavailable}
          icon={<FileDown aria-hidden="true" />}
          label={copy.actions.downloadCorrected}
          onClick={() =>
            void handleDownload(
              `/api/v1/readings/${reading.id}/corrected-text`,
              `${reading.id}-corrected.md`,
            )
          }
        />
        <IconAction
          disabled={!reading.original_text_key}
          disabledReason={copy.actions.originalUnavailable}
          icon={<FileInput aria-hidden="true" />}
          label={copy.actions.downloadOriginal}
          onClick={() =>
            void handleDownload(
              `/api/v1/readings/${reading.id}/original-text`,
              `${reading.id}-original${getReadingOriginalExtension(reading)}`,
            )
          }
        />
        <IconAction
          disabled={isProcessing || retryMutation.isPending}
          disabledReason={
            retryMutation.isPending
              ? copy.actions.retrying
              : copy.actions.retryUnavailable
          }
          icon={
            <RefreshCw
              aria-hidden="true"
              className={cn(retryMutation.isPending && "animate-spin")}
            />
          }
          label={copy.actions.retry}
          onClick={() => setActiveDialog(DocumentActionDialog.retry)}
        />
        <IconAction
          disabled={deleteMutation.isPending}
          disabledReason={copy.actions.deleting}
          icon={
            <Trash2
              aria-hidden="true"
              className={cn(deleteMutation.isPending && "animate-pulse")}
            />
          }
          label={copy.actions.delete}
          onClick={() => setActiveDialog(DocumentActionDialog.delete)}
          variant="destructive"
        />
      </fieldset>

      {downloadError && (
        <p
          aria-live="polite"
          className="mt-1 text-right text-destructive text-xs"
          role="status"
        >
          {downloadError}
        </p>
      )}

      <Dialog
        onOpenChange={(open) => {
          if (!open) setActiveDialog(null);
        }}
        open={activeDialog !== null}
      >
        {activeDialog === DocumentActionDialog.retry && (
          <DocumentRetryDialog
            isError={retryMutation.isError}
            isPending={retryMutation.isPending}
            onConfirm={() => retryMutation.mutate()}
            title={title}
          />
        )}

        {activeDialog === DocumentActionDialog.delete && (
          <DocumentDeleteDialog
            isError={deleteMutation.isError}
            isPending={deleteMutation.isPending}
            onConfirm={() => deleteMutation.mutate()}
            title={title}
          />
        )}
      </Dialog>
    </>
  );
};

type IconActionProps = {
  disabled?: boolean;
  disabledReason?: string;
  icon: ReactNode;
  label: string;
  onClick?: () => void;
  variant?: "ghost" | "destructive";
};

const IconAction = ({
  disabled = false,
  disabledReason,
  icon,
  label,
  onClick,
  variant = "ghost",
}: IconActionProps) => (
  <span
    className="inline-flex"
    title={disabled && disabledReason ? disabledReason : label}
  >
    <Button
      aria-label={label}
      disabled={disabled}
      onClick={onClick}
      size="icon-sm"
      type="button"
      variant={variant}
    >
      {icon}
    </Button>
  </span>
);
