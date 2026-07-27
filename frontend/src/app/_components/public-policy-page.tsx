import { AlertTriangle, ArrowLeft, Mail } from "lucide-react";
import Link from "next/link";
import { buttonVariants } from "@/components/ui/button";
import { dictionary } from "@/i18n/dictionaries";
import { cn } from "@/lib/utils";
import { PublicFooter } from "./public-footer";

type PolicySection = {
  id: string;
  title: string;
  paragraphs: readonly string[];
};

type PublicPolicyPageProps = {
  copy: {
    eyebrow: string;
    title: string;
    description: string;
    sections: readonly PolicySection[];
  };
};

const common = dictionary.legal.common;
const contactEmail = dictionary.landing.footer.contactEmail;

export const PublicPolicyPage = ({ copy }: PublicPolicyPageProps) => (
  <div className="flex min-h-screen flex-col bg-muted/20">
    <header className="border-border border-b bg-background">
      <div className="mx-auto flex w-full max-w-6xl flex-wrap items-center justify-between gap-4 px-5 py-4 sm:px-8">
        <Link
          className="font-semibold tracking-tight underline-offset-4 hover:underline"
          href="/"
        >
          {common.productName}
        </Link>
        <nav
          aria-label={common.navigationLabel}
          className="flex flex-wrap items-center gap-2"
        >
          <Link
            className={buttonVariants({ size: "sm", variant: "ghost" })}
            href="/docs"
          >
            {common.helpCenter}
          </Link>
          <Link
            className={buttonVariants({ size: "sm", variant: "outline" })}
            href="/sign-in"
          >
            {common.signIn}
          </Link>
        </nav>
      </div>
    </header>

    <main className="mx-auto grid w-full max-w-6xl flex-1 gap-10 px-5 py-10 sm:px-8 sm:py-14 lg:grid-cols-[13rem_minmax(0,1fr)] lg:gap-16">
      <aside className="hidden lg:block">
        <nav aria-label={common.onThisPage} className="sticky top-8 space-y-3">
          <p className="font-medium text-foreground text-sm">
            {common.onThisPage}
          </p>
          <ul className="space-y-2 border-border border-l pl-4 text-muted-foreground text-sm">
            {copy.sections.map((section) => (
              <li key={section.id}>
                <a
                  className="transition-colors hover:text-foreground"
                  href={`#${section.id}`}
                >
                  {section.title}
                </a>
              </li>
            ))}
          </ul>
        </nav>
      </aside>

      <article className="min-w-0 max-w-3xl">
        <Link
          className="mb-8 inline-flex items-center gap-2 text-muted-foreground text-sm underline-offset-4 hover:text-foreground hover:underline"
          href="/"
        >
          <ArrowLeft aria-hidden="true" className="size-4" />
          {common.backToHome}
        </Link>

        <header className="space-y-5">
          <p className="font-semibold text-primary text-sm uppercase tracking-[0.16em]">
            {copy.eyebrow}
          </p>
          <h1 className="max-w-2xl text-balance font-semibold text-4xl tracking-tight sm:text-5xl">
            {copy.title}
          </h1>
          <p className="max-w-2xl text-pretty text-lg text-muted-foreground leading-8">
            {copy.description}
          </p>
          <p className="text-muted-foreground text-sm">
            {common.updatedLabel}:{" "}
            <span className="text-foreground">{common.updatedAt}</span>
          </p>
        </header>

        <aside className="my-10 rounded-lg border border-amber-200 bg-amber-50 p-5 text-amber-950">
          <div className="flex gap-3">
            <AlertTriangle
              aria-hidden="true"
              className="mt-0.5 size-5 shrink-0"
            />
            <div className="space-y-1">
              <p className="font-semibold text-sm">{common.draftLabel}</p>
              <h2 className="font-semibold text-base">{common.draftTitle}</h2>
              <p className="text-amber-900 text-sm leading-6">
                {common.draftDescription}
              </p>
            </div>
          </div>
        </aside>

        <div>
          {copy.sections.map((section) => (
            <section
              className="scroll-mt-8 border-border border-t py-8 first:border-t-0 first:pt-0"
              id={section.id}
              key={section.id}
            >
              <h2 className="font-semibold text-2xl tracking-tight">
                {section.title}
              </h2>
              <div className="mt-4 space-y-4 text-base text-muted-foreground leading-7">
                {section.paragraphs.map((paragraph) => (
                  <p key={paragraph}>{paragraph}</p>
                ))}
              </div>
            </section>
          ))}
        </div>

        <aside className="mt-4 rounded-lg border bg-background p-6">
          <h2 className="font-semibold text-xl">{common.contactTitle}</h2>
          <p className="mt-2 max-w-2xl text-muted-foreground leading-7">
            {common.contactDescription}
          </p>
          <a
            className={cn(
              buttonVariants({ variant: "outline" }),
              "mt-5 no-underline",
            )}
            href={`mailto:${contactEmail}`}
          >
            <Mail aria-hidden="true" className="size-4" />
            {common.contactAction}
          </a>
        </aside>
      </article>
    </main>

    <PublicFooter />
  </div>
);
