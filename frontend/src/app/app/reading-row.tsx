"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";
import { Download, FileText, Trash2 } from "lucide-react";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { dictionary } from "@/i18n/dictionaries";
import type { Reading } from "@/lib/api";
import { deleteReading, downloadFile } from "@/lib/api";
import { formatPolishCount } from "@/lib/pluralize";

export const ReadingRow = ({ reading }: { reading: Reading }) => {
  const copy = dictionary.app.documents.row;
  const queryClient = useQueryClient();

  const deleteMutation = useMutation({
    mutationFn: () => deleteReading(reading.id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["readings"] });
    },
  });

  const handleDownload = async (path: string, filename: string) => {
    try {
      await downloadFile(path, filename);
    } catch (e) {
      alert(`${copy.downloadFailed}: ${e}`);
    }
  };

  return (
    <div className="grid gap-3 rounded-md border border-border bg-background p-4 text-sm lg:grid-cols-[minmax(16rem,1fr)_12rem_16rem] lg:items-center">
      <div className="min-w-0">
        <Link
          href={`/app/documents/${reading.id}`}
          className="flex min-w-0 items-center gap-2 font-medium hover:underline"
        >
          <FileText className="size-4 shrink-0 text-muted-foreground" />
          <span className="truncate">{reading.id}</span>
        </Link>
        <p className="mt-1 text-muted-foreground text-xs">
          {copy.created}: {new Date(reading.created_at).toLocaleString("pl-PL")}
        </p>
      </div>

      <div className="flex flex-wrap items-center gap-2">
        <span
          className={`text-xs px-2 py-0.5 rounded-full font-medium ${
            reading.status === "completed"
              ? "bg-green-100 text-green-800"
              : reading.status === "failed"
                ? "bg-red-100 text-red-800"
                : "bg-yellow-100 text-yellow-800"
          }`}
        >
          {reading.status}
        </span>
        <span className="text-muted-foreground text-xs">
          {formatPolishCount(reading.char_count, {
            one: "znak",
            few: "znaki",
            many: "znaków",
          })}
        </span>
      </div>

      <div className="flex flex-wrap items-center justify-start gap-2 lg:justify-end">
        <Button
          type="button"
          onClick={() =>
            handleDownload(
              `/api/v1/readings/${reading.id}/recording`,
              `${reading.id}-recording.mp3`,
            )
          }
          disabled={!reading.recording_key}
          size="xs"
          variant="outline"
        >
          <Download className="size-3" aria-hidden="true" />
          {copy.downloadRecording}
        </Button>
        <Button
          type="button"
          onClick={() =>
            handleDownload(
              `/api/v1/readings/${reading.id}/corrected-text`,
              `${reading.id}-corrected.md`,
            )
          }
          disabled={!reading.corrected_text_key}
          size="xs"
          variant="outline"
        >
          <Download className="size-3" aria-hidden="true" />
          {copy.downloadText}
        </Button>
        <Button
          type="button"
          onClick={() => deleteMutation.mutate()}
          disabled={deleteMutation.isPending}
          size="xs"
          variant="destructive"
        >
          <Trash2 className="size-3" aria-hidden="true" />
          {deleteMutation.isPending ? copy.deleting : copy.delete}
        </Button>
      </div>
    </div>
  );
};
