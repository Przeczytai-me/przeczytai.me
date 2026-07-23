"use client";

import { useEffect, useRef } from "react";

type UseActiveSentenceScrollOptions = {
  activeSegmentId?: string;
  enabled: boolean;
};

export const useActiveSentenceScroll = ({
  activeSegmentId,
  enabled,
}: UseActiveSentenceScrollOptions) => {
  const scrollViewportRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!enabled || !activeSegmentId) return;
    const viewport = scrollViewportRef.current;
    const activeSentence = viewport?.querySelector<HTMLElement>(
      '[data-current-sentence="true"]',
    );
    if (!viewport || !activeSentence) return;

    const viewportRect = viewport.getBoundingClientRect();
    const sentenceRect = activeSentence.getBoundingClientRect();
    const scrollMargin = Math.min(96, viewportRect.height * 0.2);
    const isOutsideReadingArea =
      sentenceRect.top < viewportRect.top + scrollMargin ||
      sentenceRect.bottom > viewportRect.bottom - scrollMargin;

    if (isOutsideReadingArea) {
      activeSentence.scrollIntoView({
        behavior: window.matchMedia("(prefers-reduced-motion: reduce)").matches
          ? "auto"
          : "smooth",
        block: "center",
      });
    }
  }, [activeSegmentId, enabled]);

  return scrollViewportRef;
};
