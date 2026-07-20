import { dictionary } from "@/i18n/dictionaries";

const copy = dictionary.app.settings;

export const SettingsPageHeader = () => (
  <header>
    <h1 className="font-semibold text-2xl">{copy.heading}</h1>
    <p className="max-w-2xl text-muted-foreground text-sm">
      {copy.description}{" "}
      <span className="italic">{copy.temporaryDescription}</span>
    </p>
  </header>
);
