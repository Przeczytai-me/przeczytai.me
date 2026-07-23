"use client";

import { Clock3, Unplug } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { dictionary } from "@/i18n/dictionaries";
import type { TimingMap } from "@/lib/api";
import { useActiveSentenceScroll } from "../_hooks/use-active-sentence-scroll";
import { ReaderEmptyTextState } from "./reader-empty-text-state";
import { ReaderInlineNotice } from "./reader-inline-notice";
import { SyncedReadingText } from "./synced-reading-text";

const copy = dictionary.app.reader;

type ReadingTextPanelProps = {
  currentSegmentId?: string;
  highlightsEnabled: boolean;
  isLoading: boolean;
  isSyncLoading: boolean;
  onSeek: (positionMs: number) => void;
  originalText?: string;
  originalTextUnavailable: boolean;
  timingMap: TimingMap | null | undefined;
};

export const ReadingTextPanel = ({
  currentSegmentId,
  highlightsEnabled,
  isLoading,
  isSyncLoading,
  onSeek,
  originalText,
  originalTextUnavailable,
  timingMap,
}: ReadingTextPanelProps) => {
  const segments = timingMap?.segments ?? [];
  const scrollViewportRef = useActiveSentenceScroll({
    activeSegmentId: currentSegmentId,
    enabled: highlightsEnabled,
  });

  return (
    <Card className="h-full min-h-0 min-w-0">
      <CardHeader className="shrink-0 border-b">
        <CardTitle>{copy.text.title}</CardTitle>
        <p className="text-muted-foreground text-sm">{copy.text.description}</p>
      </CardHeader>
      <CardContent className="min-h-0 flex-1">
        <div
          className="scrollbar-subtle h-full space-y-5 overflow-y-auto overscroll-contain scroll-smooth pr-2 pb-6"
          ref={scrollViewportRef}
        >
          {isSyncLoading && (
            <ReaderInlineNotice icon={Clock3} text={copy.text.syncLoading} />
          )}

          {!isSyncLoading &&
            !isLoading &&
            !originalTextUnavailable &&
            originalText?.trim() &&
            segments.length === 0 && (
              <ReaderInlineNotice
                icon={Unplug}
                text={`${copy.text.noSyncTitle}. ${copy.text.noSyncDescription}`}
              />
            )}

          {isLoading && (
            <p className="py-12 text-center text-muted-foreground text-sm">
              {copy.text.loading}
            </p>
          )}

          {!isLoading && originalTextUnavailable && (
            <ReaderEmptyTextState
              title={copy.text.unavailableTitle}
              description={copy.text.unavailableDescription}
            />
          )}

          {!isLoading && !originalTextUnavailable && !originalText?.trim() && (
            <ReaderEmptyTextState
              title={copy.text.emptyTitle}
              description={copy.text.emptyDescription}
            />
          )}

          {!isLoading &&
            !originalTextUnavailable &&
            originalText?.trim() &&
            segments.length === 0 && (
              <div className="whitespace-pre-wrap font-serif text-[1.05rem] leading-8">
                {originalText}
              </div>
            )}

          {!isLoading &&
            !originalTextUnavailable &&
            originalText?.trim() &&
            segments.length > 0 && (
              <SyncedReadingText
                currentSegmentId={currentSegmentId}
                highlightsEnabled={highlightsEnabled}
                onSeek={onSeek}
                segments={segments}
              />
            )}
        </div>
      </CardContent>
    </Card>
  );
};
