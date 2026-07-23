import { FileText, X } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardAction,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { dictionary } from "@/i18n/dictionaries";
import { cn } from "@/lib/utils";
import type { SelectedDocument } from "../_hooks/use-new-document-form";
import {
  formatFileSize,
  getDocumentPreview,
  newDocumentCharacterLimit,
} from "../utils";

const copy = dictionary.app.newDocument.preview;

type DocumentSourcePreviewProps = {
  document: SelectedDocument;
  error: string | null;
  onRemove: () => void;
};

export const DocumentSourcePreview = ({
  document,
  error,
  onRemove,
}: DocumentSourcePreviewProps) => {
  const preview = getDocumentPreview(document.text);

  return (
    <Card>
      <CardHeader>
        <CardTitle>{copy.title}</CardTitle>
        <CardDescription>{copy.description}</CardDescription>
        <CardAction>
          <Button
            aria-label={copy.removeFile}
            onClick={onRemove}
            size="icon"
            type="button"
            variant="ghost"
          >
            <X aria-hidden="true" />
          </Button>
        </CardAction>
      </CardHeader>
      <CardContent className="grid gap-4">
        <dl className="grid gap-3 rounded-lg border border-border bg-muted/20 p-4 sm:grid-cols-2 lg:grid-cols-4">
          <PreviewDetail label={copy.fileName} value={document.name} />
          <PreviewDetail
            label={copy.fileType}
            value={
              document.extension === ".md"
                ? copy.types.markdown
                : copy.types.text
            }
          />
          <PreviewDetail
            label={copy.fileSize}
            value={formatFileSize(document.size)}
          />
          <PreviewDetail
            invalid={document.text.length > newDocumentCharacterLimit}
            label={copy.characterCount}
            value={document.text.length.toLocaleString("pl-PL")}
          />
        </dl>

        {error ? (
          <p
            className="rounded-lg border border-destructive/30 bg-destructive/5 p-3 text-destructive text-sm"
            role="alert"
          >
            {error}
          </p>
        ) : null}

        <div className="grid gap-2">
          <div className="flex items-center gap-2 font-medium text-sm">
            <FileText aria-hidden="true" className="size-4" />
            {copy.content}
          </div>
          <pre className="max-h-64 overflow-auto whitespace-pre-wrap rounded-lg border border-border bg-muted/20 p-4 font-mono text-sm leading-6">
            {preview.text}
          </pre>
          {preview.isTruncated ? (
            <p className="text-muted-foreground text-xs">{copy.truncated}</p>
          ) : null}
        </div>
      </CardContent>
    </Card>
  );
};

const PreviewDetail = ({
  invalid = false,
  label,
  value,
}: {
  invalid?: boolean;
  label: string;
  value: string;
}) => (
  <div className="min-w-0">
    <dt className="text-muted-foreground text-xs">{label}</dt>
    <dd
      className={cn(
        "mt-1 truncate font-medium text-sm",
        invalid && "text-destructive",
      )}
      title={value}
    >
      {value}
    </dd>
  </div>
);
