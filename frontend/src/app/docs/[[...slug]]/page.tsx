import {
  DocsBody,
  DocsDescription,
  DocsPage,
  DocsTitle,
} from "fumadocs-ui/layouts/docs/page";
import { createRelativeLink } from "fumadocs-ui/mdx";
import type { Metadata } from "next";
import { notFound } from "next/navigation";
import { getMDXComponents } from "@/components/mdx";
import { dictionary } from "@/i18n/dictionaries";
import { docsSource } from "@/lib/docs-source";

type HelpCenterPageProps = {
  params: Promise<{
    slug?: string[];
  }>;
};

const HelpCenterPage = async ({ params }: HelpCenterPageProps) => {
  const { slug } = await params;
  const page = docsSource.getPage(slug);

  if (!page) {
    notFound();
  }

  const MDXContent = page.data.body;

  return (
    <DocsPage
      toc={page.data.toc}
      full={page.data.full}
      footer={{ enabled: false }}
    >
      <DocsTitle>{page.data.title}</DocsTitle>
      <DocsDescription>{page.data.description}</DocsDescription>
      <DocsBody>
        <MDXContent
          components={getMDXComponents({
            a: createRelativeLink(docsSource, page),
          })}
        />
      </DocsBody>
    </DocsPage>
  );
};

export const generateStaticParams = () => docsSource.generateParams();

export const generateMetadata = async ({
  params,
}: HelpCenterPageProps): Promise<Metadata> => {
  const { slug } = await params;
  const page = docsSource.getPage(slug);

  if (!page) {
    notFound();
  }

  return {
    title: `${page.data.title} | ${dictionary.metadata.title}`,
    description: page.data.description,
  };
};

export default HelpCenterPage;
