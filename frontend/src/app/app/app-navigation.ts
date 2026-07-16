import {
  BookOpen,
  BriefcaseBusiness,
  FolderOpen,
  type LucideIcon,
  Plus,
  Settings,
} from "lucide-react";
import { dictionary } from "@/i18n/dictionaries";

const copy = dictionary.app.shell;

export type AppNavigationItem = {
  href: string;
  label: string;
  icon: LucideIcon;
  exact?: boolean;
};

export const appNavigationItems: AppNavigationItem[] = [
  {
    href: "/app",
    label: copy.navigation.documents,
    icon: FolderOpen,
    exact: true,
  },
  {
    href: "/app/new",
    label: copy.navigation.newDocument,
    icon: Plus,
  },
  {
    href: "/app/jobs",
    label: copy.navigation.jobs,
    icon: BriefcaseBusiness,
  },
  {
    href: "/app/settings",
    label: copy.navigation.settings,
    icon: Settings,
  },
  {
    href: "/docs",
    label: copy.navigation.documentation,
    icon: BookOpen,
  },
];
