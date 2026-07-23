"use client";

import { ArrowRight, LoaderCircle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { dictionary } from "@/i18n/dictionaries";
import { useNewDocumentForm } from "../_hooks/use-new-document-form";
import { DocumentAbbreviationFields } from "./document-abbreviation-fields";
import { DocumentSourcePreview } from "./document-source-preview";
import { DocumentUploadDropzone } from "./document-upload-dropzone";

const copy = dictionary.app.newDocument;

export const NewDocumentForm = () => {
  const form = useNewDocumentForm();

  return (
    <form
      className="mx-auto flex w-full max-w-5xl flex-col gap-5 pb-12"
      onSubmit={(event) => {
        event.preventDefault();
        form.handleSubmit();
      }}
    >
      <header>
        <h1 className="font-semibold text-2xl">{copy.heading}</h1>
        <p className="text-muted-foreground text-sm">{copy.description}</p>
      </header>

      <DocumentUploadDropzone
        error={form.state.fileError}
        onFilesSelected={form.handleFilesSelected}
      />

      {form.state.selectedDocument ? (
        <DocumentSourcePreview
          document={form.state.selectedDocument}
          error={form.documentError}
          onRemove={form.removeDocument}
        />
      ) : null}

      <DocumentAbbreviationFields
        errors={form.abbreviationErrors}
        onAdd={form.addAbbreviationReading}
        onChange={form.updateAbbreviationReading}
        onRemove={form.removeAbbreviationReading}
        readings={form.state.abbreviationReadings}
      />

      <div className="flex flex-wrap items-center justify-between gap-4 rounded-xl border border-border bg-background p-4">
        <p className="max-w-2xl text-muted-foreground text-sm">
          {copy.submitNote}
        </p>
        <Button
          disabled={!form.canSubmit || form.isPending}
          size="lg"
          type="submit"
        >
          {form.isPending ? (
            <LoaderCircle className="animate-spin" aria-hidden="true" />
          ) : (
            <ArrowRight aria-hidden="true" />
          )}
          {form.isPending ? copy.creating : copy.create}
        </Button>
      </div>

      {form.error ? (
        <p className="text-destructive text-sm" role="alert">
          {copy.errors.submit}
        </p>
      ) : null}
    </form>
  );
};
