"use client";

import { useEffect, useMemo, useState } from "react";
import { useLocalStorage } from "@/hooks/use-local-storage";
import { dictionary } from "@/i18n/dictionaries";
import { localStorageKeys } from "@/lib/local-storage-keys";
import {
  type AppSettings,
  createAbbreviationReading,
  defaultAppSettings,
  parseAppSettings,
} from "@/lib/settings-defaults";
import { AbbreviationsSettingsCard } from "./_components/abbreviations-settings-card";
import { ExportSettingsCard } from "./_components/export-settings-card";
import { InfoCallout } from "./_components/info-callout";
import { PlaybackSettingsCard } from "./_components/playback-settings-card";
import { PrivacySettingsCard } from "./_components/privacy-settings-card";
import { ReadingModelSettingsCard } from "./_components/reading-model-settings-card";
import { SettingsPageHeader } from "./_components/settings-page-header";
import { SettingsSaveBar } from "./_components/settings-save-bar";
import { VoiceSettingsCard } from "./_components/voice-settings-card";

const copy = dictionary.app.settings;

export const SettingsPageClient = () => {
  const [savedSettings, setSavedSettings, hasHydratedSettings] =
    useLocalStorage(localStorageKeys.settings, {
      defaultValue: defaultAppSettings,
      parse: parseAppSettings,
    });
  const [draftSettings, setDraftSettings] =
    useState<AppSettings>(defaultAppSettings);
  const [status, setStatus] = useState<string>(copy.status.ready);
  const [hasHydratedDraft, setHasHydratedDraft] = useState(false);

  useEffect(() => {
    if (hasHydratedSettings && !hasHydratedDraft) {
      setDraftSettings(savedSettings);
      setHasHydratedDraft(true);
    }
  }, [hasHydratedDraft, hasHydratedSettings, savedSettings]);

  const hasUnsavedChanges = useMemo(
    () => JSON.stringify(savedSettings) !== JSON.stringify(draftSettings),
    [savedSettings, draftSettings],
  );

  const updateSetting = (key: keyof AppSettings, value: string) => {
    setDraftSettings((settings) => ({ ...settings, [key]: value }));
    setStatus(copy.status.editing);
  };

  const updateAbbreviationReading = (
    index: number,
    key: "abbreviation" | "expansion",
    value: string,
  ) => {
    setDraftSettings((settings) => ({
      ...settings,
      abbreviationReadings: settings.abbreviationReadings.map((reading, i) =>
        i === index ? { ...reading, [key]: value } : reading,
      ),
    }));
    setStatus(copy.status.editing);
  };

  const addAbbreviationReading = () => {
    setDraftSettings((settings) => ({
      ...settings,
      abbreviationReadings: [
        ...settings.abbreviationReadings,
        createAbbreviationReading(),
      ],
    }));
    setStatus(copy.status.editing);
  };

  const removeAbbreviationReading = (index: number) => {
    setDraftSettings((settings) => ({
      ...settings,
      abbreviationReadings: settings.abbreviationReadings.filter(
        (_reading, i) => i !== index,
      ),
    }));
    setStatus(copy.status.editing);
  };

  const saveSettings = () => {
    setSavedSettings(draftSettings);
    setStatus(copy.status.saved);
  };

  const discardChanges = () => {
    setDraftSettings(savedSettings);
    setStatus(copy.status.discarded);
  };

  const resetDefaults = () => {
    if (!window.confirm(copy.resetConfirm)) {
      return;
    }

    setDraftSettings(defaultAppSettings);
    setSavedSettings(defaultAppSettings);
    setStatus(copy.status.reset);
  };

  return (
    <section className="mx-auto flex w-full max-w-5xl flex-col gap-5 pb-24">
      <SettingsPageHeader />

      <InfoCallout>{copy.futureOnlyNotice}</InfoCallout>

      <div className="grid gap-4 lg:grid-cols-2">
        <ReadingModelSettingsCard
          settings={draftSettings}
          onChange={updateSetting}
        />
        <VoiceSettingsCard settings={draftSettings} onChange={updateSetting} />
        <PlaybackSettingsCard
          settings={draftSettings}
          onChange={updateSetting}
        />
        <ExportSettingsCard settings={draftSettings} onChange={updateSetting} />
      </div>

      <AbbreviationsSettingsCard
        readings={draftSettings.abbreviationReadings}
        onAdd={addAbbreviationReading}
        onChange={updateAbbreviationReading}
        onRemove={removeAbbreviationReading}
      />

      <PrivacySettingsCard onReset={resetDefaults} />

      <div className="sr-only" aria-live="polite">
        {status}
      </div>

      {hasUnsavedChanges && (
        <SettingsSaveBar onDiscard={discardChanges} onSave={saveSettings} />
      )}
    </section>
  );
};
