// TODO: Remove this local settings fallback once backend-backed settings are available.

export type AbbreviationReading = {
  abbreviation: string;
  expansion: string;
  id: string;
};

export type AppSettings = {
  defaultModel: string;
  fallbackModel: string;
  defaultVoice: string;
  pronunciationStyle: string;
  playbackSpeed: string;
  highlightBehavior: string;
  abbreviationReadings: AbbreviationReading[];
  textFormat: string;
};

export const defaultAppSettings: AppSettings = {
  defaultModel: "edge-tts",
  fallbackModel: "none",
  defaultVoice: "Zofia",
  pronunciationStyle: "natural",
  playbackSpeed: "1.0",
  highlightBehavior: "sentence",
  abbreviationReadings: [],
  textFormat: "md",
};

export const settingOptions = {
  defaultModel: [
    { value: "edge-tts", label: "Edge TTS" },
    { value: "openai", label: "OpenAI TTS" },
  ],
  fallbackModel: [
    { value: "none", label: "Bez modelu zapasowego" },
    { value: "edge-tts", label: "Edge TTS" },
    { value: "openai", label: "OpenAI TTS" },
  ],
  defaultVoice: [
    { value: "Zofia", label: "Zofia" },
    { value: "Marek", label: "Marek" },
    { value: "Ava", label: "Ava" },
    { value: "Andrew", label: "Andrew" },
    { value: "Brian", label: "Brian" },
    { value: "Emma", label: "Emma" },
  ],
  pronunciationStyle: [
    { value: "natural", label: "Naturalny" },
    { value: "clear", label: "Wyraźny" },
  ],
  playbackSpeed: [
    { value: "0.9", label: "0.9x" },
    { value: "1.0", label: "1.0x" },
    { value: "1.1", label: "1.1x" },
    { value: "1.25", label: "1.25x" },
  ],
  highlightBehavior: [
    { value: "sentence", label: "Podświetlaj aktualne zdanie" },
    { value: "completed", label: "Pokazuj przeczytane zdania" },
    { value: "off", label: "Nie podświetlaj automatycznie" },
  ],
  textFormat: [
    { value: "txt", label: "TXT" },
    { value: "md", label: "Markdown" },
    { value: "ssml", label: "SSML" },
  ],
} as const;

export const parseAppSettings = (value: string | null): AppSettings => {
  if (!value) {
    return defaultAppSettings;
  }

  try {
    const parsed = JSON.parse(value) as Partial<AppSettings>;
    return {
      defaultModel: parsed.defaultModel ?? defaultAppSettings.defaultModel,
      fallbackModel: parsed.fallbackModel ?? defaultAppSettings.fallbackModel,
      defaultVoice: parsed.defaultVoice ?? defaultAppSettings.defaultVoice,
      pronunciationStyle:
        parsed.pronunciationStyle ?? defaultAppSettings.pronunciationStyle,
      playbackSpeed: parsed.playbackSpeed ?? defaultAppSettings.playbackSpeed,
      highlightBehavior:
        parsed.highlightBehavior ?? defaultAppSettings.highlightBehavior,
      abbreviationReadings: normalizeAbbreviationReadings(
        parsed.abbreviationReadings,
      ),
      textFormat: parsed.textFormat ?? defaultAppSettings.textFormat,
    };
  } catch {
    return defaultAppSettings;
  }
};

export const createAbbreviationReading = (): AbbreviationReading => ({
  abbreviation: "",
  expansion: "",
  id:
    typeof crypto === "undefined" || !crypto.randomUUID
      ? `abbreviation-${Date.now()}`
      : crypto.randomUUID(),
});

const normalizeAbbreviationReadings = (
  value: unknown,
): AbbreviationReading[] => {
  if (!Array.isArray(value)) {
    return defaultAppSettings.abbreviationReadings;
  }

  return value
    .map((item, index) => {
      if (!item || typeof item !== "object") {
        return null;
      }

      const reading = item as Partial<AbbreviationReading>;
      return {
        abbreviation: String(reading.abbreviation ?? ""),
        expansion: String(reading.expansion ?? ""),
        id:
          typeof reading.id === "string" && reading.id
            ? reading.id
            : `stored-abbreviation-${index}`,
      };
    })
    .filter((item): item is AbbreviationReading => item !== null);
};
