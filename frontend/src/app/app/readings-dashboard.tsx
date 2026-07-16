"use client";

import { ReadingsList } from "./readings-list";

export const ReadingsDashboard = () => {
  return (
    <div className="flex w-full flex-col gap-6 pb-12">
      <ReadingsList />
    </div>
  );
};
