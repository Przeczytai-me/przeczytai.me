import { dictionary } from "@/i18n/dictionaries";
import type { TimingMap } from "@/lib/api";
import { cn } from "@/lib/utils";

const copy = dictionary.app.reader;

type SyncedReadingTextProps = {
  currentSegmentId?: string;
  highlightsEnabled: boolean;
  onSeek: (positionMs: number) => void;
  segments: TimingMap["segments"];
};

export const SyncedReadingText = ({
  currentSegmentId,
  highlightsEnabled,
  onSeek,
  segments,
}: SyncedReadingTextProps) => {
  const paragraphs = Map.groupBy(
    segments,
    (segment) => segment.paragraph_index,
  );

  return (
    <div className="space-y-5 font-serif text-[1.05rem] leading-8">
      {[...paragraphs.entries()].map(([paragraphIndex, paragraphSegments]) => (
        <p key={paragraphIndex}>
          {paragraphSegments.map((segment, index) => {
            const isCurrent =
              highlightsEnabled && segment.id === currentSegmentId;
            return (
              <span key={segment.id}>
                {index > 0 && " "}
                <button
                  type="button"
                  aria-current={isCurrent ? "true" : undefined}
                  aria-label={
                    isCurrent
                      ? `${copy.text.currentSentence}: ${segment.text}`
                      : segment.text
                  }
                  data-current-sentence={isCurrent ? "true" : undefined}
                  className={cn(
                    "rounded-sm text-left outline-none transition-colors focus-visible:ring-3 focus-visible:ring-ring/50",
                    "hover:bg-primary/10",
                    isCurrent && "bg-primary/15",
                  )}
                  onClick={() => onSeek(segment.start_ms)}
                >
                  {segment.text}
                </button>
              </span>
            );
          })}
        </p>
      ))}
    </div>
  );
};
