import type { TimingMap, TtsOptions, UserSettings } from "./types";

const mockDocumentSegments = [
  "PrzeczytAI.me przygotowuje polskie dokumenty do wygodnego słuchania.",
  "Najpierw porządkuje tekst, a następnie tworzy nagranie.",
  "Użytkownik może wrócić do dokumentu, pobrać pliki i ponowić przetwarzanie.",
  "W czytniku dokumentu tekst pozostaje dostępny przez cały czas odtwarzania.",
  "Aktualnie czytane zdanie jest wyraźnie podświetlane i automatycznie przesuwane do środka widoku.",
  "Przyciski poprzedniego i następnego zdania pozwalają szybko poruszać się po dłuższym materiale.",
  "Menu dokumentu udostępnia szczegóły, gotowe pliki oraz bezpieczną opcję ponownego generowania.",
  "Nagranie można zatrzymać w dowolnym momencie, zmienić jego prędkość albo wybrać pozycję na osi czasu.",
  "Jeżeli dane synchronizacji nie są dostępne, aplikacja pokazuje tekst bez zgadywania czasu poszczególnych zdań.",
  "Po zakończeniu słuchania wszystkie wyniki pozostają dostępne w prywatnej przestrzeni dokumentów.",
  "Każde zdanie ma własny przedział czasu, dzięki czemu podświetlenie podąża za głosem bez opóźnień.",
  "Dłuższy przykładowy dokument pomaga także sprawdzić zachowanie czytnika na mniejszych ekranach.",
  "Przewijanie odbywa się wyłącznie wewnątrz pola tekstowego, więc nagłówek i odtwarzacz pozostają na miejscu.",
  "Automatyczne przewijanie można wyłączyć w menu, jeżeli użytkownik chce samodzielnie przeglądać tekst.",
  "Po ponownym włączeniu funkcji aktywne zdanie wraca do widocznego obszaru podczas dalszego odtwarzania.",
  "Ten fragment kończy dane testowe i ułatwia sprawdzenie zachowania czytnika blisko końca dokumentu.",
];

export const mockOriginalText = mockDocumentSegments.join("\n\n");

const mockRecordingDurationMs = 3_500;

export const mockTimingMapSegments: TimingMap["segments"] =
  mockDocumentSegments.map((text, index) => ({
    id: `segment-${index + 1}`,
    text,
    paragraph_index: index,
    start_ms: Math.round(
      (index * mockRecordingDurationMs) / mockDocumentSegments.length,
    ),
    end_ms: Math.round(
      ((index + 1) * mockRecordingDurationMs) / mockDocumentSegments.length,
    ),
  }));

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
