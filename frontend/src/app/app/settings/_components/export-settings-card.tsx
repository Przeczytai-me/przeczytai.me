import { FileText } from "lucide-react";
import { dictionary } from "@/i18n/dictionaries";
import type { AppSettings } from "@/lib/settings-defaults";
import { settingOptions } from "@/lib/settings-defaults";
import { SelectField } from "./select-field";
import { SettingsCard } from "./settings-card";

const copy = dictionary.app.settings;

type ExportSettingsCardProps = {
  onChange: (key: "textFormat", value: string) => void;
  settings: Pick<AppSettings, "textFormat">;
};

export const ExportSettingsCard = ({
  onChange,
  settings,
}: ExportSettingsCardProps) => (
  <SettingsCard
    description={copy.sections.exports.description}
    icon={<FileText aria-hidden="true" className="size-4" />}
    title={copy.sections.exports.title}
  >
    <SelectField
      label={copy.fields.textFormat}
      value={settings.textFormat}
      options={settingOptions.textFormat}
      onChange={(value) => onChange("textFormat", value)}
    />
  </SettingsCard>
);
