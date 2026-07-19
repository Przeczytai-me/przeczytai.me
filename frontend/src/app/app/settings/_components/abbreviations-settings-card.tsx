import { History, Plus, X } from "lucide-react";
import { Button } from "@/components/ui/button";
import { dictionary } from "@/i18n/dictionaries";
import type { AbbreviationReading } from "@/lib/settings-defaults";
import { SettingsCard } from "./settings-card";

const copy = dictionary.app.settings;

type AbbreviationsSettingsCardProps = {
  readings: AbbreviationReading[];
  onAdd: () => void;
  onChange: (
    index: number,
    key: "abbreviation" | "expansion",
    value: string,
  ) => void;
  onRemove: (index: number) => void;
};

export const AbbreviationsSettingsCard = ({
  readings,
  onAdd,
  onChange,
  onRemove,
}: AbbreviationsSettingsCardProps) => (
  <SettingsCard
    description={copy.sections.abbreviations.description}
    icon={<History aria-hidden="true" className="size-4" />}
    title={copy.sections.abbreviations.title}
  >
    <div className="grid gap-3">
      <div className="grid gap-2 sm:grid-cols-[1fr_1fr_2rem]">
        <span className="font-medium text-sm">{copy.fields.abbreviation}</span>
        <span className="font-medium text-sm">{copy.fields.expansion}</span>
        <span className="sr-only">{copy.fields.actions}</span>
      </div>
      {readings.length === 0 ? (
        <p className="rounded-md border border-dashed border-border bg-muted/30 p-4 text-muted-foreground text-sm">
          {copy.abbreviationsEmpty}
        </p>
      ) : (
        readings.map((reading, index) => (
          <div
            className="grid gap-2 sm:grid-cols-[1fr_1fr_2rem]"
            data-abbreviation-row
            key={reading.id}
          >
            <input
              className="h-9 rounded-md border border-input bg-background px-3 text-sm"
              aria-label={`${copy.fields.abbreviation} ${index + 1}`}
              data-abbreviation-field="abbreviation"
              value={reading.abbreviation}
              placeholder={copy.placeholders.abbreviation}
              onChange={(event) =>
                onChange(index, "abbreviation", event.target.value)
              }
            />
            <input
              className="h-9 rounded-md border border-input bg-background px-3 text-sm"
              aria-label={`${copy.fields.expansion} ${index + 1}`}
              data-abbreviation-field="expansion"
              value={reading.expansion}
              placeholder={copy.placeholders.expansion}
              onChange={(event) =>
                onChange(index, "expansion", event.target.value)
              }
            />
            <Button
              aria-label={`${copy.actions.removeAbbreviation} ${index + 1}`}
              type="button"
              variant="ghost"
              size="icon"
              onClick={() => onRemove(index)}
            >
              <X aria-hidden="true" className="size-3.5" />
            </Button>
          </div>
        ))
      )}
      <Button
        type="button"
        variant="outline"
        className="justify-self-start"
        onClick={onAdd}
      >
        <Plus aria-hidden="true" className="size-3.5" />
        {copy.actions.addAbbreviation}
      </Button>
    </div>
    <p className="text-muted-foreground text-xs italic">
      {copy.unsupported.abbreviations}
    </p>
  </SettingsCard>
);
