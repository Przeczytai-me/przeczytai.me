"use client";

import { usePathname } from "next/navigation";
import { useState } from "react";
import { useOnce } from "@/hooks/use-once";
import { dictionary } from "@/i18n/dictionaries";
import { localStorageKeys } from "@/lib/local-storage-keys";
import { getDocumentId } from "@/lib/routes";
import { cn } from "@/lib/utils";
import { AppSidebar } from "./_components/app-sidebar";
import { AppTopbar } from "./_components/app-topbar";
import { appNavigationItems } from "./app-navigation";

const copy = dictionary.app.shell;

type AppShellProps = {
  children: React.ReactNode;
};

export const AppShell = ({ children }: AppShellProps) => {
  const pathname = usePathname();
  const [isCollapsed, setIsCollapsed] = useState(false);
  const [isSidebarTransitioning, setIsSidebarTransitioning] = useState(false);
  const documentId = getDocumentId(pathname);
  const isDocumentReader = Boolean(documentId);
  const currentTitle = getCurrentTitle(pathname, documentId);
  const showSidebarLabels = !(isCollapsed || isSidebarTransitioning);

  useOnce(() => {
    const storedValue = window.localStorage.getItem(
      localStorageKeys.sidebarCollapsed,
    );

    if (storedValue === "true" || storedValue === "false") {
      setIsCollapsed(storedValue === "true");
      return;
    }

    setIsCollapsed(window.innerWidth < 1024);
  });

  const handleSidebarToggle = () => {
    setIsSidebarTransitioning(true);
    setIsCollapsed((value) => {
      const nextValue = !value;
      window.localStorage.setItem(
        localStorageKeys.sidebarCollapsed,
        String(nextValue),
      );
      return nextValue;
    });
  };

  return (
    <div
      className={cn(
        "bg-muted/30 text-foreground",
        isDocumentReader ? "h-dvh overflow-hidden" : "min-h-screen",
      )}
    >
      <AppSidebar
        isCollapsed={isCollapsed}
        onToggle={handleSidebarToggle}
        onTransitionEnd={() => setIsSidebarTransitioning(false)}
        pathname={pathname}
        showLabels={showSidebarLabels}
      />

      <div
        className={cn(
          "min-w-0 flex flex-col transition-[padding-left]",
          isDocumentReader ? "h-dvh min-h-0" : "min-h-screen",
          isCollapsed ? "pl-16" : "pl-52",
        )}
      >
        <AppTopbar currentTitle={currentTitle} documentId={documentId} />

        <main
          className={cn(
            "min-w-0 flex-1 px-4 lg:px-8",
            isDocumentReader
              ? "min-h-0 overflow-hidden py-4"
              : "overflow-auto py-6",
          )}
        >
          {children}
        </main>
      </div>

      <div
        aria-live="polite"
        id="app-toast-region"
        role="status"
        className="fixed right-4 bottom-4 z-30 flex w-[min(22rem,calc(100vw-2rem))] flex-col gap-2"
      />
    </div>
  );
};

const getCurrentTitle = (pathname: string, documentId?: string) => {
  if (documentId) {
    return `${copy.documentTitlePrefix} ${documentId}`;
  }

  if (pathname === "/app/account" || pathname.startsWith("/app/account/")) {
    return copy.navigation.account;
  }

  const item = appNavigationItems
    .filter((navItem) => navItem.href !== "/docs")
    .find((navItem) =>
      navItem.exact
        ? pathname === navItem.href
        : pathname === navItem.href || pathname.startsWith(`${navItem.href}/`),
    );

  return item?.label ?? copy.navigation.documents;
};
