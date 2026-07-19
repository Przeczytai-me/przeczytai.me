import { Sparkles } from "lucide-react";
import { dictionary } from "@/i18n/dictionaries";
import type { AppSettings } from "@/lib/settings-defaults";
import { settingOptions } from "@/lib/settings-defaults";
import { SelectField } from "./select-field";
import { SettingsCard } from "./settings-card";

const copy = dictionary.app.settings;

type ReadingModelSettingsCardProps = {
  onChange: (key: "defaultModel" | "fallbackModel", value: string) => void;
  settings: Pick<AppSettings, "defaultModel" | "fallbackModel">;
};

export const ReadingModelSettingsCard = ({
  onChange,
  settings,
}: ReadingModelSettingsCardProps) => (
  <SettingsCard
    description={copy.sections.model.description}
    icon={<Sparkles aria-hidden="true" className="size-4" />}
    title={copy.sections.model.title}
  >
    <SelectField
      label={copy.fields.defaultModel}
      value={settings.defaultModel}
      options={settingOptions.defaultModel}
      onChange={(value) => onChange("defaultModel", value)}
    />
    <SelectField
      label={copy.fields.fallbackModel}
      value={settings.fallbackModel}
      options={settingOptions.fallbackModel}
      onChange={(value) => onChange("fallbackModel", value)}
    />
  </SettingsCard>
);
