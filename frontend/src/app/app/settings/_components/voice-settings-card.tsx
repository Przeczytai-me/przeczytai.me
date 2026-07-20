import { FileAudio, Play } from "lucide-react";
import { Button } from "@/components/ui/button";
import { dictionary } from "@/i18n/dictionaries";
import type { AppSettings } from "@/lib/settings-defaults";
import { settingOptions } from "@/lib/settings-defaults";
import { SelectField } from "./select-field";
import { SettingsCard } from "./settings-card";

const copy = dictionary.app.settings;

type VoiceSettingsCardProps = {
  onChange: (key: "defaultVoice" | "pronunciationStyle", value: string) => void;
  settings: Pick<AppSettings, "defaultVoice" | "pronunciationStyle">;
};

export const VoiceSettingsCard = ({
  onChange,
  settings,
}: VoiceSettingsCardProps) => (
  <SettingsCard
    description={copy.sections.voice.description}
    icon={<FileAudio aria-hidden="true" className="size-4" />}
    title={copy.sections.voice.title}
  >
    <SelectField
      label={copy.fields.defaultVoice}
      value={settings.defaultVoice}
      options={settingOptions.defaultVoice}
      onChange={(value) => onChange("defaultVoice", value)}
    />
    <SelectField
      label={copy.fields.pronunciationStyle}
      value={settings.pronunciationStyle}
      options={settingOptions.pronunciationStyle}
      onChange={(value) => onChange("pronunciationStyle", value)}
    />
    <Button type="button" variant="outline" disabled>
      <Play aria-hidden="true" className="size-3.5" />
      {copy.actions.previewVoice}
    </Button>
    <p className="text-muted-foreground text-xs italic">
      {copy.unsupported.voicePreview}
    </p>
  </SettingsCard>
);
