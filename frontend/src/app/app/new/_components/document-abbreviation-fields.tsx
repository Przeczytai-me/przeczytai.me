import { Languages, Plus, Trash2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { dictionary } from "@/i18n/dictionaries";
import type { AbbreviationReadingDraft } from "../_hooks/use-new-document-form";

const copy = dictionary.app.newDocument.abbreviations;

type DocumentAbbreviationFieldsProps = {
  errors: Array<string | null>;
  onAdd: () => void;
  onChange: (
    id: string,
    field: "abbreviation" | "readAs",
    value: string,
  ) => void;
  onRemove: (id: string) => void;
  readings: AbbreviationReadingDraft[];
};

export const DocumentAbbreviationFields = ({
  errors,
  onAdd,
  onChange,
  onRemove,
  readings,
}: DocumentAbbreviationFieldsProps) => (
  <Card>
    <CardHeader>
      <CardTitle className="flex items-center gap-2">
        <Languages aria-hidden="true" className="size-4" />
        {copy.title}
      </CardTitle>
      <CardDescription>{copy.description}</CardDescription>
    </CardHeader>
    <CardContent className="grid gap-4">
      {readings.length === 0 ? (
        <p className="rounded-lg border border-dashed border-border bg-muted/20 p-4 text-muted-foreground text-sm">
          {copy.empty}
        </p>
      ) : (
        <div className="grid gap-3">
          {readings.map((reading, index) => {
            const error = errors[index];
            const errorId = `abbreviation-error-${reading.id}`;

            return (
              <div
                className="grid gap-2 rounded-lg border border-border p-3 sm:grid-cols-[1fr_1fr_auto]"
                key={reading.id}
              >
                <label className="grid gap-1.5 text-sm">
                  <span className="font-medium">{copy.abbreviationLabel}</span>
                  <input
                    aria-describedby={error ? errorId : undefined}
                    aria-invalid={Boolean(error)}
                    className="h-9 rounded-md border border-input bg-background px-3 text-sm outline-none focus-visible:border-ring focus-visible:ring-3 focus-visible:ring-ring/50 aria-invalid:border-destructive aria-invalid:ring-3 aria-invalid:ring-destructive/20"
                    maxLength={50}
                    onChange={(event) =>
                      onChange(reading.id, "abbreviation", event.target.value)
                    }
                    placeholder={copy.abbreviationPlaceholder}
                    value={reading.abbreviation}
                  />
                </label>
                <label className="grid gap-1.5 text-sm">
                  <span className="font-medium">{copy.readAsLabel}</span>
                  <input
                    aria-describedby={error ? errorId : undefined}
                    aria-invalid={Boolean(error)}
                    className="h-9 rounded-md border border-input bg-background px-3 text-sm outline-none focus-visible:border-ring focus-visible:ring-3 focus-visible:ring-ring/50 aria-invalid:border-destructive aria-invalid:ring-3 aria-invalid:ring-destructive/20"
                    maxLength={200}
                    onChange={(event) =>
                      onChange(reading.id, "readAs", event.target.value)
                    }
                    placeholder={copy.readAsPlaceholder}
                    value={reading.readAs}
                  />
                </label>
                <Button
                  aria-label={`${copy.remove} ${index + 1}`}
                  className="self-end"
                  onClick={() => onRemove(reading.id)}
                  size="icon"
                  type="button"
                  variant="ghost"
                >
                  <Trash2 aria-hidden="true" />
                </Button>
                {error ? (
                  <p
                    className="text-destructive text-xs sm:col-span-3"
                    id={errorId}
                    role="alert"
                  >
                    {error}
                  </p>
                ) : null}
              </div>
            );
          })}
        </div>
      )}

      <Button
        className="justify-self-start"
        onClick={onAdd}
        type="button"
        variant="outline"
      >
        <Plus aria-hidden="true" />
        {copy.add}
      </Button>

      <p className="text-muted-foreground text-xs">{copy.scope}</p>
    </CardContent>
  </Card>
);
