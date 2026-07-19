"use client";

import { UserButton } from "@clerk/nextjs";
import { ChevronRight } from "lucide-react";
import Link from "next/link";
import { dictionary } from "@/i18n/dictionaries";

const copy = dictionary.app.shell;

type AppTopbarProps = {
  currentTitle: string;
  documentId?: string;
};

export const AppTopbar = ({ currentTitle, documentId }: AppTopbarProps) => {
  return (
    <header className="sticky top-0 z-10 flex min-h-16 items-center justify-between gap-4 border-border border-b bg-background/95 px-4 backdrop-blur lg:px-8">
      <div className="min-w-0">
        {documentId ? (
          <nav
            aria-label={copy.breadcrumbs.label}
            className="flex min-w-0 items-center gap-2 text-sm"
          >
            <Link
              href="/app"
              className="text-muted-foreground hover:text-foreground"
            >
              {copy.breadcrumbs.documents}
            </Link>
            <ChevronRight
              className="size-3.5 text-muted-foreground"
              aria-hidden="true"
            />
            <span className="truncate font-medium">{currentTitle}</span>
          </nav>
        ) : (
          <p className="truncate font-medium">{currentTitle}</p>
        )}
      </div>

      <div className="flex items-center gap-3">
        <div className="hidden items-center gap-2 rounded-md border border-border px-2.5 py-1.5 text-xs md:flex">
          <span className="size-2 rounded-full bg-emerald-500" />
          <span>{copy.processingStatus}</span>
        </div>
        <UserButton
          userProfileMode="navigation"
          userProfileUrl="/app/account"
        />
      </div>
    </header>
  );
};
