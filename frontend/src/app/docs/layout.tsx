import { DocsLayout } from "fumadocs-ui/layouts/docs";
import type { ReactNode } from "react";
import { docsLayoutOptions } from "@/lib/docs-layout";
import { docsSource } from "@/lib/docs-source";

type HelpCenterLayoutProps = {
  children: ReactNode;
};

const HelpCenterLayout = ({ children }: HelpCenterLayoutProps) => (
  <DocsLayout
    {...docsLayoutOptions()}
    tree={docsSource.getPageTree()}
    tabs={false}
  >
    {children}
  </DocsLayout>
);

export default HelpCenterLayout;
