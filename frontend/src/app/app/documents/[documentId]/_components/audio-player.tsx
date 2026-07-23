"use client";

import { Pause, Play, SkipBack, SkipForward, Volume2 } from "lucide-react";
import type { RefObject } from "react";
import { Button } from "@/components/ui/button";
import { dictionary } from "@/i18n/dictionaries";
import type { TimingMap } from "@/lib/api";
import { formatDurationMs } from "@/lib/duration";

const copy = dictionary.app.reader.player;
const speeds = [0.75, 1, 1.1, 1.25, 1.5, 2];

type AudioPlayerProps = {
  audioRef: RefObject<HTMLAudioElement | null>;
  currentSegmentIndex: number;
  currentTimeMs: number;
  durationMs: number;
  isPlaying: boolean;
  onAudioError: () => void;
  onDurationChange: (durationMs: number) => void;
  onPlayingChange: (isPlaying: boolean) => void;
  onSeek: (positionMs: number) => void;
  onSpeedChange: (speed: number) => void;
  onTimeChange: (positionMs: number) => void;
  readingId: string;
  segments: TimingMap["segments"];
  speed: number;
};

export const AudioPlayer = ({
  audioRef,
  currentSegmentIndex,
  currentTimeMs,
  durationMs,
  isPlaying,
  onAudioError,
  onDurationChange,
  onPlayingChange,
  onSeek,
  onSpeedChange,
  onTimeChange,
  readingId,
  segments,
  speed,
}: AudioPlayerProps) => {
  const handlePlayToggle = async () => {
    const audio = audioRef.current;
    if (!audio) return;

    if (!audio.paused) {
      audio.pause();
      return;
    }

    try {
      await audio.play();
    } catch {
      onAudioError();
    }
  };

  const seekBySentence = (offset: number) => {
    if (segments.length === 0) return;
    const baseIndex = currentSegmentIndex >= 0 ? currentSegmentIndex : 0;
    const nextIndex = Math.max(
      0,
      Math.min(segments.length - 1, baseIndex + offset),
    );
    onSeek(segments[nextIndex].start_ms);
  };

  const handleSpeedChange = (value: number) => {
    if (audioRef.current) audioRef.current.playbackRate = value;
    onSpeedChange(value);
  };

  return (
    <section
      aria-label={copy.label}
      className="z-20 mt-3 shrink-0 rounded-xl border border-border bg-background/95 p-3 shadow-lg backdrop-blur"
    >
      {/* biome-ignore lint/a11y/useMediaCaption: The narrated source text and synchronized current sentence are visible directly above the player. */}
      <audio
        ref={audioRef}
        preload="metadata"
        src={`/api/v1/readings/${readingId}/recording`}
        onDurationChange={(event) => {
          const seconds = event.currentTarget.duration;
          if (Number.isFinite(seconds)) onDurationChange(seconds * 1_000);
        }}
        onEnded={() => onPlayingChange(false)}
        onError={onAudioError}
        onPause={() => onPlayingChange(false)}
        onPlay={() => onPlayingChange(true)}
        onTimeUpdate={(event) =>
          onTimeChange(event.currentTarget.currentTime * 1_000)
        }
      />

      <div className="flex flex-wrap items-center gap-3">
        <div className="flex items-center gap-1">
          <Button
            aria-label={copy.previous}
            disabled={segments.length === 0 || currentSegmentIndex <= 0}
            onClick={() => seekBySentence(-1)}
            size="icon"
            title={copy.previous}
            type="button"
            variant="ghost"
          >
            <SkipBack aria-hidden="true" />
          </Button>
          <Button
            aria-label={isPlaying ? copy.pause : copy.play}
            onClick={handlePlayToggle}
            size="icon-lg"
            title={isPlaying ? copy.pause : copy.play}
            type="button"
          >
            {isPlaying ? (
              <Pause aria-hidden="true" />
            ) : (
              <Play aria-hidden="true" />
            )}
          </Button>
          <Button
            aria-label={copy.next}
            disabled={
              segments.length === 0 ||
              currentSegmentIndex >= segments.length - 1
            }
            onClick={() => seekBySentence(1)}
            size="icon"
            title={copy.next}
            type="button"
            variant="ghost"
          >
            <SkipForward aria-hidden="true" />
          </Button>
        </div>

        <div className="flex min-w-[12rem] flex-1 items-center gap-3">
          <span className="w-12 text-right font-mono text-xs">
            {formatDurationMs(currentTimeMs)}
          </span>
          <label className="sr-only" htmlFor="reader-audio-seek">
            {copy.seek}
          </label>
          <input
            className="h-2 min-w-0 flex-1 cursor-pointer accent-primary focus-visible:outline-none focus-visible:ring-3 focus-visible:ring-ring/50"
            disabled={durationMs <= 0}
            id="reader-audio-seek"
            max={Math.max(durationMs, 1)}
            min={0}
            onChange={(event) => onSeek(Number(event.currentTarget.value))}
            step={100}
            type="range"
            value={Math.min(currentTimeMs, Math.max(durationMs, 1))}
          />
          <span className="w-12 font-mono text-xs">
            {formatDurationMs(durationMs)}
          </span>
        </div>

        <div className="flex items-center gap-2">
          <Volume2
            className="size-4 text-muted-foreground"
            aria-hidden="true"
          />
          <label className="sr-only" htmlFor="reader-audio-speed">
            {copy.speed}
          </label>
          <select
            className="h-8 rounded-lg border border-input bg-background px-2 text-sm outline-none focus-visible:border-ring focus-visible:ring-3 focus-visible:ring-ring/50"
            id="reader-audio-speed"
            onChange={(event) =>
              handleSpeedChange(Number(event.currentTarget.value))
            }
            value={speed}
          >
            {speeds.map((option) => (
              <option key={option} value={option}>
                {option}
                {copy.speedValue}
              </option>
            ))}
          </select>
        </div>
      </div>
    </section>
  );
};
