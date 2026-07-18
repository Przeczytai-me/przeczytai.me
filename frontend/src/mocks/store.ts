import { defaultUserSettings } from "./data";
import type { ProcessingJob, ProcessingJobStatus, UserSettings } from "./types";

const retryJobs: ProcessingJob[] = [];
let userSettings = structuredClone(defaultUserSettings);

export const createRetryJob = (readingId: string): ProcessingJob => {
  const now = new Date().toISOString();
  const attempt =
    retryJobs.filter((job) => job.reading_id === readingId).length + 2;
  const job: ProcessingJob = {
    id: `mock-retry-${crypto.randomUUID()}`,
    reading_id: readingId,
    attempt,
    status: "uploaded",
    progress: 5,
    current_step: "Dokument oczekuje na przetwarzanie",
    error: null,
    created_at: now,
    updated_at: now,
  };
  retryJobs.unshift(job);
  return structuredClone(job);
};

export const getRetryJobs = (): ProcessingJob[] =>
  retryJobs.map(simulateJobProgress);

export const getUserSettings = (): UserSettings =>
  structuredClone(userSettings);

export const saveUserSettings = (settings: UserSettings): UserSettings => {
  userSettings = structuredClone(settings);
  return getUserSettings();
};

const simulateJobProgress = (job: ProcessingJob): ProcessingJob => {
  const elapsedSeconds = (Date.now() - Date.parse(job.created_at)) / 1_000;
  const stage = getSimulatedStage(elapsedSeconds);

  return {
    ...job,
    ...stage,
    updated_at: new Date().toISOString(),
  };
};

const getSimulatedStage = (
  elapsedSeconds: number,
): Pick<ProcessingJob, "status" | "progress" | "current_step"> => {
  const stages: Array<{
    until: number;
    status: ProcessingJobStatus;
    progress: number;
    current_step: string;
  }> = [
    {
      until: 3,
      status: "uploaded",
      progress: 5,
      current_step: "Dokument oczekuje na przetwarzanie",
    },
    {
      until: 6,
      status: "extracting_text",
      progress: 25,
      current_step: "Odczytywanie tekstu",
    },
    {
      until: 9,
      status: "generating_ssml",
      progress: 50,
      current_step: "Przygotowywanie tekstu do nagrania",
    },
    {
      until: 12,
      status: "generating_audio",
      progress: 75,
      current_step: "Generowanie nagrania",
    },
  ];

  return (
    stages.find((stage) => elapsedSeconds < stage.until) ?? {
      status: "ready",
      progress: 100,
      current_step: "Nagranie jest gotowe",
    }
  );
};
