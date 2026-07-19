"use client";

import { useState } from "react";
import { useOnce } from "@/hooks/use-once";

type UseLocalStorageOptions<T> = {
  defaultValue: T;
  parse: (value: string | null) => T;
  serialize?: (value: T) => string;
};

export const useLocalStorage = <T>(
  key: string,
  {
    defaultValue,
    parse,
    serialize = JSON.stringify,
  }: UseLocalStorageOptions<T>,
) => {
  const [value, setValueState] = useState(defaultValue);
  const [hasHydrated, setHasHydrated] = useState(false);

  useOnce(() => {
    setValueState(parse(window.localStorage.getItem(key)));
    setHasHydrated(true);
  });

  const setValue = (nextValue: T) => {
    window.localStorage.setItem(key, serialize(nextValue));
    setValueState(nextValue);
  };

  return [value, setValue, hasHydrated] as const;
};
