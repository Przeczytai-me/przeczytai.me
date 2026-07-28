"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useRouter } from "next/navigation";
import { useRef, useState } from "react";
import { dictionary } from "@/i18n/dictionaries";
import {
  getOriginalText,
  getReading,
  getTimingMap,
  retryReading,
} from "@/lib/api";
import {
  getMetadataDurationMs,
  getReadingTitle,
  ReadingStatus,
} from "@/lib/reading";
import { AudioPlayer } from "./_components/audio-player";
import { ReaderActionsMenu } from "./_components/reader-actions-menu";
import { ReaderHeader } from "./_components/reader-header";
import { ReaderStatusPage } from "./_components/reader-status-page";
import { ReadingTextPanel } from "./_components/reading-text-panel";
import { RecordingUnavailableAlert } from "./_components/recording-unavailable-alert";
import { getCurrentSegmentIndex } from "./reader-utils";

const copy = dictionary.app.reader;

export const DocumentReader = ({ documentId }: { documentId: string }) => {
  const router = useRouter();
  const queryClient = useQueryClient();
  const audioRef = useRef<HTMLAudioElement>(null);
  const [currentTimeMs, setCurrentTimeMs] = useState(0);
  const [audioDurationMs, setAudioDurationMs] = useState(0);
  const [isPlaying, setIsPlaying] = useState(false);
  const [speed, setSpeed] = useState(1);
  const [highlightsEnabled, setHighlightsEnabled] = useState(true);
  const [audioError, setAudioError] = useState("");

  const readingQuery = useQuery({
    queryKey: ["reading", documentId],
    queryFn: () => getReading(documentId),
  });
  const reading = readingQuery.data;
  const isCompleted = reading?.status === ReadingStatus.completed;
  const isFailed =
    reading?.status === ReadingStatus.failed ||
    reading?.status === ReadingStatus.failedToStart;

  const originalTextQuery = useQuery({
    queryKey: ["reading", documentId, "original-text"],
    queryFn: () => getOriginalText(documentId),
    enabled: Boolean(reading),
    retry: false,
  });

  const timingMapQuery = useQuery({
    queryKey: ["reading", documentId, "timing-map"],
    queryFn: () => getTimingMap(documentId),
    enabled: Boolean(isCompleted && reading?.recording_key),
    retry: false,
  });

  const retryMutation = useMutation({
    mutationFn: () => retryReading(documentId),
    onSuccess: async () => {
      await queryClient.invalidateQueries({
        queryKey: ["reading", documentId],
      });
      router.push("/app/jobs");
    },
  });

  if (readingQuery.isLoading) {
    return <ReaderStatusPage description={copy.loading} />;
  }

  if (readingQuery.isError || !reading) {
    return (
      <ReaderStatusPage
        description={copy.loadError.description}
        isError
        onRetry={() => readingQuery.refetch()}
        retryLabel={copy.loadError.retry}
        secondaryAction={{
          href: "/app",
          label: copy.processing.documents,
        }}
        title={copy.loadError.title}
      />
    );
  }

  if (!isCompleted && !isFailed) {
    return (
      <ReaderStatusPage
        description={copy.processing.description}
        primaryAction={{
          href: "/app/jobs",
          label: copy.processing.jobs,
        }}
        secondaryAction={{
          href: "/app",
          label: copy.processing.documents,
        }}
        title={copy.processing.title}
      />
    );
  }

  const timingMap = timingMapQuery.data;
  const segments = timingMap?.segments ?? [];
  const durationMs =
    audioDurationMs ||
    timingMap?.duration_ms ||
    getMetadataDurationMs(reading.metadata);
  const currentSegmentIndex = getCurrentSegmentIndex(segments, currentTimeMs);
  const currentSegmentId =
    currentSegmentIndex >= 0 ? segments[currentSegmentIndex].id : undefined;
  const originalTextUnavailable = originalTextQuery.isError;
  const title = getReadingTitle(reading.metadata, reading.id);
  const recordingUnavailable = isFailed || !reading.recording_key;

  const handleSeek = (positionMs: number) => {
    if (audioRef.current) {
      audioRef.current.currentTime = positionMs / 1_000;
    }
    setCurrentTimeMs(positionMs);
  };

  return (
    <div className="mx-auto flex h-full min-h-0 max-w-368 flex-col">
      <ReaderHeader
        actions={
          <ReaderActionsMenu
            autoHighlight={highlightsEnabled}
            durationMs={durationMs}
            isOriginalAvailable={originalTextQuery.isSuccess}
            isRetrying={retryMutation.isPending}
            onAutoHighlightChange={setHighlightsEnabled}
            onRetry={() => retryMutation.mutate()}
            reading={reading}
            retryError={
              retryMutation.isError ? copy.details.retryError : undefined
            }
          />
        }
        title={title}
      />

      {recordingUnavailable && <RecordingUnavailableAlert />}

      <div className="min-h-0 flex-1">
        <ReadingTextPanel
          currentSegmentId={currentSegmentId}
          highlightsEnabled={highlightsEnabled}
          isLoading={originalTextQuery.isLoading}
          isSyncLoading={timingMapQuery.isLoading}
          onSeek={handleSeek}
          originalText={originalTextQuery.data}
          originalTextUnavailable={originalTextUnavailable}
          timingMap={timingMap}
        />
      </div>

      {!recordingUnavailable && (
        <>
          {audioError && (
            <p
              aria-live="polite"
              className="mt-2 shrink-0 text-destructive text-sm"
              role="status"
            >
              {audioError}
            </p>
          )}
          <AudioPlayer
            audioRef={audioRef}
            currentSegmentIndex={currentSegmentIndex}
            currentTimeMs={currentTimeMs}
            durationMs={durationMs}
            isPlaying={isPlaying}
            onAudioError={() => setAudioError(copy.player.audioError)}
            onDurationChange={setAudioDurationMs}
            onPlayingChange={setIsPlaying}
            onSeek={handleSeek}
            onSpeedChange={setSpeed}
            onTimeChange={setCurrentTimeMs}
            readingId={reading.id}
            segments={segments}
            speed={speed}
          />
        </>
      )}
    </div>
  );
};
