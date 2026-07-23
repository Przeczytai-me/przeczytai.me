"use client";

import { FileUp } from "lucide-react";
import { useState } from "react";
import { dictionary } from "@/i18n/dictionaries";
import { supportedDocumentAccept } from "@/lib/file-constants";
import { cn } from "@/lib/utils";

const copy = dictionary.app.newDocument.upload;

type DocumentUploadDropzoneProps = {
  error: string | null;
  onFilesSelected: (files: File[]) => void;
};

export const DocumentUploadDropzone = ({
  error,
  onFilesSelected,
}: DocumentUploadDropzoneProps) => {
  const [isDragging, setIsDragging] = useState(false);

  return (
    <fieldset
      className={cn(
        "grid min-w-0 gap-3 rounded-xl border border-dashed bg-muted/20 p-6 text-center transition-colors",
        isDragging
          ? "border-primary bg-primary/5"
          : "border-border hover:border-muted-foreground/60",
        error && "border-destructive/60",
      )}
      onDragEnter={(event) => {
        event.preventDefault();
        setIsDragging(true);
      }}
      onDragLeave={(event) => {
        if (
          !(event.relatedTarget instanceof Node) ||
          !event.currentTarget.contains(event.relatedTarget)
        ) {
          setIsDragging(false);
        }
      }}
      onDragOver={(event) => {
        event.preventDefault();
        event.dataTransfer.dropEffect = "copy";
      }}
      onDrop={(event) => {
        event.preventDefault();
        setIsDragging(false);
        onFilesSelected(Array.from(event.dataTransfer.files));
      }}
    >
      <legend className="sr-only">{copy.title}</legend>
      <FileUp
        aria-hidden="true"
        className="mx-auto size-8 text-muted-foreground"
      />
      <div className="grid gap-1">
        <p className="font-medium">{copy.title}</p>
        <p className="text-muted-foreground text-sm">{copy.description}</p>
      </div>
      <input
        accept={supportedDocumentAccept}
        aria-describedby={
          error
            ? "document-upload-help document-upload-error"
            : "document-upload-help"
        }
        className="mx-auto w-full min-w-0 max-w-full text-sm file:mr-3 file:rounded-lg file:border file:border-border file:bg-background file:px-3 file:py-2 file:font-medium file:text-foreground file:text-sm hover:file:bg-muted sm:w-auto"
        id="document-file"
        type="file"
        onChange={(event) => {
          onFilesSelected(Array.from(event.currentTarget.files ?? []));
          event.currentTarget.value = "";
        }}
      />
      <div
        className="grid gap-1 text-muted-foreground text-xs"
        id="document-upload-help"
      >
        <span>{copy.inputLabel}</span>
        <span>{copy.supportedFormats}</span>
        <span>{copy.limitNote}</span>
      </div>
      {error ? (
        <p
          className="text-destructive text-sm"
          id="document-upload-error"
          role="alert"
        >
          {error}
        </p>
      ) : null}
    </fieldset>
  );
};
