import type { TimingMap, TtsOptions, UserSettings } from "./types";

export const mockOriginalText = [
  "PrzeczytAI.me przygotowuje polskie dokumenty do wygodnego słuchania.",
  "Najpierw porządkuje tekst, a następnie tworzy nagranie.",
  "Użytkownik może wrócić do dokumentu, pobrać pliki i ponowić przetwarzanie.",
].join("\n\n");

export const mockTimingMapSegments: TimingMap["segments"] = [
  {
    id: "segment-1",
    text: "PrzeczytAI.me przygotowuje polskie dokumenty do wygodnego słuchania.",
    paragraph_index: 0,
    start_ms: 0,
    end_ms: 4_600,
  },
  {
    id: "segment-2",
    text: "Najpierw porządkuje tekst, a następnie tworzy nagranie.",
    paragraph_index: 1,
    start_ms: 4_600,
    end_ms: 8_500,
  },
  {
    id: "segment-3",
    text: "Użytkownik może wrócić do dokumentu, pobrać pliki i ponowić przetwarzanie.",
    paragraph_index: 2,
    start_ms: 8_500,
    end_ms: 14_200,
  },
];

export const mockTtsOptions: TtsOptions = {
  vendors: [{ id: "edge-tts", label: "Edge TTS" }],
  models: [{ id: "edge-tts", vendor_id: "edge-tts", label: "Edge TTS" }],
  voices: [
    {
      id: "Zofia",
      provider_id: "pl-PL-ZofiaNeural",
      label: "Zofia",
      language: "pl-PL",
      preview_url: null,
    },
    {
      id: "Marek",
      provider_id: "pl-PL-MarekNeural",
      label: "Marek",
      language: "pl-PL",
      preview_url: null,
    },
    {
      id: "Ava",
      provider_id: "en-US-AvaMultilingualNeural",
      label: "Ava",
      language: "multilingual",
      preview_url: null,
    },
    {
      id: "Andrew",
      provider_id: "en-US-AndrewMultilingualNeural",
      label: "Andrew",
      language: "multilingual",
      preview_url: null,
    },
    {
      id: "Brian",
      provider_id: "en-US-BrianMultilingualNeural",
      label: "Brian",
      language: "multilingual",
      preview_url: null,
    },
    {
      id: "Emma",
      provider_id: "en-US-EmmaMultilingualNeural",
      label: "Emma",
      language: "multilingual",
      preview_url: null,
    },
  ],
  pronunciation_styles: [
    { id: "natural", label: "Naturalny" },
    { id: "clear", label: "Wyraźny" },
  ],
  defaults: {
    model: "edge-tts",
    voice: "Zofia",
    pronunciation_style: "natural",
  },
};

export const defaultUserSettings: UserSettings = {
  reading_model: mockTtsOptions.defaults.model,
  fallback_model: null,
  voice: mockTtsOptions.defaults.voice,
  pronunciation_style: mockTtsOptions.defaults.pronunciation_style,
  playback_speed: 1,
  sentence_highlighting: true,
  custom_abbreviation_readings: [],
  exports: {
    filename_pattern: "{reading_id}",
    mp3_quality: "standard",
    text_format: "md",
  },
  updated_at: new Date(0).toISOString(),
};
