import { SlidersHorizontal } from "lucide-react";
import { dictionary } from "@/i18n/dictionaries";
import type { AppSettings } from "@/lib/settings-defaults";
import { settingOptions } from "@/lib/settings-defaults";
import { SelectField } from "./select-field";
import { SettingsCard } from "./settings-card";

const copy = dictionary.app.settings;

type PlaybackSettingsCardProps = {
  onChange: (key: "playbackSpeed" | "highlightBehavior", value: string) => void;
  settings: Pick<AppSettings, "playbackSpeed" | "highlightBehavior">;
};

export const PlaybackSettingsCard = ({
  onChange,
  settings,
}: PlaybackSettingsCardProps) => (
  <SettingsCard
    description={copy.sections.playback.description}
    icon={<SlidersHorizontal aria-hidden="true" className="size-4" />}
    title={copy.sections.playback.title}
  >
    <SelectField
      label={copy.fields.playbackSpeed}
      value={settings.playbackSpeed}
      options={settingOptions.playbackSpeed}
      onChange={(value) => onChange("playbackSpeed", value)}
    />
    <SelectField
      label={copy.fields.highlightBehavior}
      value={settings.highlightBehavior}
      options={settingOptions.highlightBehavior}
      onChange={(value) => onChange("highlightBehavior", value)}
    />
  </SettingsCard>
);
