import { ArrowLeft } from "lucide-react";
import Link from "next/link";
import type { ReactNode } from "react";
import { dictionary } from "@/i18n/dictionaries";

const copy = dictionary.app.reader.header;

type ReaderHeaderProps = {
  actions: ReactNode;
  title: string;
};

export const ReaderHeader = ({ actions, title }: ReaderHeaderProps) => (
  <header className="mb-3 flex shrink-0 items-start justify-between gap-4">
    <div className="min-w-0">
      <Link
        className="inline-flex items-center gap-1 text-muted-foreground text-sm hover:text-foreground"
        href="/app"
      >
        <ArrowLeft className="size-4" aria-hidden="true" />
        {copy.back}
      </Link>
      <h1 className="mt-2 wrap-break-word font-semibold text-2xl">{title}</h1>
    </div>
    {actions}
  </header>
);
