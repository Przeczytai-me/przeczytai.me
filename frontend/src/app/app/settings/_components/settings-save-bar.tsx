import { Save, Undo2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { dictionary } from "@/i18n/dictionaries";

const copy = dictionary.app.settings;

type SettingsSaveBarProps = {
  onDiscard: () => void;
  onSave: () => void;
};

export const SettingsSaveBar = ({
  onDiscard,
  onSave,
}: SettingsSaveBarProps) => (
  <div className="fixed right-4 bottom-4 left-20 z-40 rounded-md border border-border bg-background p-3 shadow-lg lg:left-68">
    <div className="flex flex-wrap items-center justify-between gap-3">
      <p className="text-sm">{copy.unsavedBar.message}</p>
      <div className="flex flex-wrap items-center gap-2">
        <Button type="button" variant="outline" onClick={onDiscard}>
          <Undo2 aria-hidden="true" className="size-3.5" />
          {copy.actions.discard}
        </Button>
        <Button type="button" onClick={onSave}>
          <Save aria-hidden="true" className="size-3.5" />
          {copy.actions.save}
        </Button>
      </div>
    </div>
  </div>
);
