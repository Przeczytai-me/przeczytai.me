"use client";

import { PanelLeftClose, PanelLeftOpen } from "lucide-react";
import Link from "next/link";
import { dictionary } from "@/i18n/dictionaries";
import { cn } from "@/lib/utils";
import { appNavigationItems } from "../app-navigation";

const copy = dictionary.app.shell;

type AppSidebarProps = {
  isCollapsed: boolean;
  onToggle: () => void;
  onTransitionEnd: () => void;
  pathname: string;
  showLabels: boolean;
};

export const AppSidebar = ({
  isCollapsed,
  onToggle,
  onTransitionEnd,
  pathname,
  showLabels,
}: AppSidebarProps) => {
  return (
    <aside
      className={cn(
        "fixed inset-y-0 left-0 z-20 flex flex-col border-border border-r bg-background transition-[width]",
        isCollapsed ? "w-16" : "w-52",
      )}
      onTransitionEnd={(event) => {
        if (event.propertyName === "width") {
          onTransitionEnd();
        }
      }}
    >
      <div
        className={cn(
          "flex h-16 items-center border-border border-b px-3",
          showLabels ? "justify-start px-5" : "justify-center",
        )}
      >
        <Link
          href="/app"
          aria-label={copy.productName}
          className={cn(
            "flex h-9 items-center rounded-md font-semibold text-base",
            showLabels ? "w-full justify-start" : "w-10 justify-center",
          )}
          title={copy.productName}
        >
          {showLabels ? (
            <span>{copy.productName}</span>
          ) : (
            <span aria-hidden="true">P</span>
          )}
        </Link>
      </div>
      <nav className="flex flex-1 flex-col gap-1 px-3 py-4">
        {appNavigationItems.map((item) => {
          const Icon = item.icon;
          const active = item.exact
            ? pathname === item.href
            : pathname === item.href || pathname.startsWith(`${item.href}/`);

          return (
            <Link
              key={item.href}
              href={item.href}
              aria-label={item.label}
              className={cn(
                "flex h-9 items-center gap-3 rounded-md px-3 text-sm transition-colors",
                showLabels ? "w-full justify-start" : "w-10 justify-center",
                active
                  ? "bg-sidebar-accent font-medium text-sidebar-accent-foreground"
                  : "text-muted-foreground hover:bg-muted hover:text-foreground",
              )}
              title={item.label}
            >
              <Icon className="size-4" aria-hidden="true" />
              {showLabels && (
                <span className="whitespace-nowrap">{item.label}</span>
              )}
            </Link>
          );
        })}
      </nav>
      <div
        className={cn(
          "px-3 pb-4",
          isCollapsed ? "flex justify-center" : "flex justify-start",
        )}
      >
        <button
          type="button"
          aria-label={
            isCollapsed ? copy.sidebar.expandLabel : copy.sidebar.collapseLabel
          }
          className="flex h-9 w-10 shrink-0 items-center justify-center gap-3 rounded-md px-3 text-muted-foreground text-sm transition-colors hover:bg-muted hover:text-foreground focus-visible:border-ring focus-visible:ring-3 focus-visible:ring-ring/50"
          onClick={onToggle}
          title={
            isCollapsed ? copy.sidebar.expandLabel : copy.sidebar.collapseLabel
          }
        >
          {isCollapsed ? (
            <PanelLeftOpen className="size-4" aria-hidden="true" />
          ) : (
            <PanelLeftClose className="size-4" aria-hidden="true" />
          )}
        </button>
      </div>
    </aside>
  );
};
