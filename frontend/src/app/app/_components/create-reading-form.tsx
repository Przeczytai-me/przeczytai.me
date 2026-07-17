"use client";

import { Button } from "@/components/ui/button";
import { dictionary } from "@/i18n/dictionaries";
import { supportedDocumentAccept } from "@/lib/file-constants";

const copy = dictionary.app.newDocument;

export type CreateReadingFormState = {
  text: string;
  vendor: string;
  voice: string;
  selectedFileName: string | null;
  fileError: string | null;
};

type CreateReadingFormProps = {
  error?: unknown;
  isPending: boolean;
  isSuccess: boolean;
  onFileChange: (event: React.ChangeEvent<HTMLInputElement>) => void;
  onSubmit: () => void;
  onTextChange: (value: string) => void;
  onVendorChange: (value: string) => void;
  onVoiceChange: (value: string) => void;
  readingId?: string;
  state: CreateReadingFormState;
};

export const CreateReadingForm = ({
  error,
  isPending,
  isSuccess,
  onFileChange,
  onSubmit,
  onTextChange,
  onVendorChange,
  onVoiceChange,
  readingId,
  state,
}: CreateReadingFormProps) => {
  return (
    <section className="mx-auto flex w-full max-w-3xl flex-col gap-4 rounded-md border border-border bg-background p-5">
      <div>
        <h1 className="font-semibold text-2xl">{copy.heading}</h1>
        <p className="text-muted-foreground text-sm">{copy.description}</p>
      </div>
      <label className="grid gap-2 rounded-md border border-dashed border-border bg-muted/30 p-4 text-sm">
        <span className="font-medium">{copy.fileLabel}</span>
        <span className="text-muted-foreground text-xs">
          {copy.fileDescription}
        </span>
        <input
          accept={supportedDocumentAccept}
          className="text-sm file:mr-3 file:rounded-md file:border-0 file:bg-primary file:px-3 file:py-1.5 file:text-primary-foreground file:text-sm"
          onChange={onFileChange}
          type="file"
        />
        {state.selectedFileName && (
          <span className="text-muted-foreground text-xs">
            {copy.selectedFile}: {state.selectedFileName}
          </span>
        )}
        {state.fileError && (
          <span className="text-destructive text-xs">{state.fileError}</span>
        )}
      </label>
      <textarea
        className="min-h-45 resize-y rounded-md border border-input p-3 font-mono text-sm"
        placeholder={copy.textPlaceholder}
        value={state.text}
        onChange={(event) => onTextChange(event.target.value)}
      />
      <div className="flex gap-2">
        <input
          className="flex-1 rounded-md border border-input px-3 py-2 text-sm"
          placeholder={copy.vendorPlaceholder}
          value={state.vendor}
          onChange={(event) => onVendorChange(event.target.value)}
        />
        <input
          className="flex-1 rounded-md border border-input px-3 py-2 text-sm"
          placeholder={copy.voicePlaceholder}
          value={state.voice}
          onChange={(event) => onVoiceChange(event.target.value)}
        />
      </div>
      <div className="rounded-md border border-border bg-muted/40 p-3 text-muted-foreground text-sm">
        {copy.limitNote} {state.text.length}/10000
      </div>
      <div className="flex flex-wrap items-center gap-3">
        <Button
          type="button"
          onClick={onSubmit}
          disabled={isPending || !state.text.trim()}
        >
          {isPending ? copy.creating : copy.create}
        </Button>
        {isSuccess && (
          <span className="text-emerald-700 text-xs">
            {copy.created}: {readingId}
          </span>
        )}
        {error ? (
          <span className="text-destructive text-xs">{String(error)}</span>
        ) : null}
      </div>
    </section>
  );
};
