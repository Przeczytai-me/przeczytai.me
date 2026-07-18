"use client";

import { type PropsWithChildren, useEffect, useState } from "react";

const isMockingEnabled =
  process.env.NODE_ENV === "development" &&
  process.env.NEXT_PUBLIC_API_MOCKING === "true";

export const MockingProvider = ({ children }: PropsWithChildren) => {
  const [isReady, setIsReady] = useState(!isMockingEnabled);

  useEffect(() => {
    if (!isMockingEnabled) return;

    let isMounted = true;
    import("@/mocks/browser")
      .then(({ startMockWorker }) => startMockWorker())
      .catch((error: unknown) => {
        console.error("Failed to start frontend API mocks", error);
      })
      .finally(() => {
        if (isMounted) setIsReady(true);
      });

    return () => {
      isMounted = false;
    };
  }, []);

  if (!isReady) return null;
  return children;
};
