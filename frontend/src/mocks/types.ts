import type { ReadingCreateRequest } from "@/lib/api";

export type { TimingMap } from "@/lib/api";

export type AbbreviationReading = {
  abbreviation: string;
  read_as: string;
};

export type MockReadingCreateRequest = ReadingCreateRequest & {
  abbreviation_readings?: AbbreviationReading[];
};

export type ProcessingJobStatus =
  | "uploaded"
  | "extracting_text"
  | "generating_ssml"
  | "generating_audio"
  | "ready"
  | "failed";

export type ProcessingJob = {
  id: string;
  reading_id: string;
  attempt: number;
  status: ProcessingJobStatus;
  progress: number | null;
  current_step: string;
  error: {
    code: string;
    message: string;
    step: string;
  } | null;
  created_at: string;
  updated_at: string;
};

export type ProcessingJobListResponse = {
  items: ProcessingJob[];
  next_cursor: string | null;
};

export type UserSettings = {
  reading_model: string;
  fallback_model: string | null;
  voice: string;
  pronunciation_style: string;
  playback_speed: number;
  sentence_highlighting: boolean;
  custom_abbreviation_readings: AbbreviationReading[];
  exports: {
    filename_pattern: string;
    mp3_quality: string;
    text_format: string;
  };
  updated_at: string;
};

export type TtsOptions = {
  vendors: Array<{
    id: string;
    label: string;
  }>;
  models: Array<{
    id: string;
    vendor_id: string;
    label: string;
  }>;
  voices: Array<{
    id: string;
    provider_id: string;
    label: string;
    language: string;
    preview_url: string | null;
  }>;
  pronunciation_styles: Array<{
    id: string;
    label: string;
  }>;
  defaults: {
    model: string;
    voice: string;
    pronunciation_style: string;
  };
};
