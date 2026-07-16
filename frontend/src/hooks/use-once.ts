"use client";

import { useEffect, useRef } from "react";

export const useOnce = (effect: () => void) => {
  const effectRef = useRef(effect);
  effectRef.current = effect;

  useEffect(() => {
    effectRef.current();
  }, []);
};
