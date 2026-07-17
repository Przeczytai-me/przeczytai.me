import type { LucideIcon } from "lucide-react";
import {
  ArrowRight,
  Check,
  Clock,
  Download,
  FileText,
  Highlighter,
  Mic2,
  Sparkles,
} from "lucide-react";
import Link from "next/link";
import { buttonVariants } from "@/components/ui/button";
import { dictionary } from "@/i18n/dictionaries";
import { cn } from "@/lib/utils";

const capabilities: Array<{
  copy: (typeof dictionary.landing.capabilities.items)[keyof typeof dictionary.landing.capabilities.items];
  icon: LucideIcon;
}> = [
  {
    copy: dictionary.landing.capabilities.items.cleanup,
    icon: Sparkles,
  },
  {
    copy: dictionary.landing.capabilities.items.ssml,
    icon: FileText,
  },
  {
    copy: dictionary.landing.capabilities.items.voice,
    icon: Mic2,
  },
  {
    copy: dictionary.landing.capabilities.items.highlighting,
    icon: Highlighter,
  },
  {
    copy: dictionary.landing.capabilities.items.downloads,
    icon: Download,
  },
];

const supportedInputs = dictionary.landing.supportedInputs.items;

type LandingPageProps = {
  isSignedIn: boolean;
};

export const LandingPage = ({ isSignedIn }: LandingPageProps) => {
  return (
    <main className="min-h-screen bg-background">
      <LandingHeader isSignedIn={isSignedIn} />

      <div className="mx-auto flex w-full max-w-5xl flex-col px-5 sm:px-8 lg:px-10">
        <HeroSection />
        <CapabilitiesSection />
        <SupportedInputsSection />
      </div>

      <LandingFooter />
    </main>
  );
};

const LandingHeader = ({ isSignedIn }: LandingPageProps) => {
  const t = dictionary.landing;

  return (
    <header className="w-full border-border border-b">
      <div className="mx-auto flex min-h-14 w-full items-center justify-between gap-4 px-5 py-2 sm:px-8 lg:px-10">
        <Link href="/" className="font-semibold text-lg">
          {t.productName}
        </Link>

        <nav className="flex items-center gap-2" aria-label="Główna nawigacja">
          {isSignedIn ? (
            <Link
              href="/app"
              className={cn(buttonVariants({ size: "sm" }), "min-w-fit px-3")}
            >
              {t.actions.openApp}
            </Link>
          ) : (
            <>
              <Link
                href="/sign-in"
                className={cn(
                  buttonVariants({ variant: "ghost", size: "sm" }),
                  "min-w-fit px-3",
                )}
              >
                {t.actions.signIn}
              </Link>
              <Link
                href="/sign-up"
                className={cn(buttonVariants({ size: "sm" }), "min-w-fit px-3")}
              >
                {t.actions.signUp}
              </Link>
            </>
          )}
        </nav>
      </div>
    </header>
  );
};

const HeroSection = () => {
  const t = dictionary.landing;

  return (
    <section className="flex flex-col gap-7 border-border border-b pt-8 pb-10 sm:gap-8 sm:pt-10 sm:pb-12">
      <div className="flex flex-col gap-5">
        <div className="flex flex-col gap-4">
          <h1 className="text-balance font-semibold text-5xl tracking-normal sm:text-6xl">
            {t.productName}
          </h1>
          <p className="text-lg text-muted-foreground leading-8 sm:text-xl">
            {t.valueProposition}
          </p>
        </div>
      </div>

      <div
        id="demo"
        className="overflow-hidden rounded-lg border border-border bg-card shadow-sm"
      >
        <video
          className="aspect-video w-full bg-muted object-cover"
          src="/landing-demo.mp4"
          autoPlay
          loop
          muted
          playsInline
          preload="metadata"
          aria-label={t.demo.label}
        />
      </div>

      <div className="flex flex-col gap-3 rounded-lg border border-primary/20 bg-primary/5 p-4 sm:flex-row sm:items-center sm:justify-between">
        <p className="text-foreground/75 text-sm leading-6">
          {t.docsCallout.text}
        </p>
        <Link
          href="/docs"
          className={cn(buttonVariants({ size: "lg" }), "w-full sm:w-fit")}
        >
          {t.actions.viewDocs}
          <ArrowRight data-icon="inline-end" />
        </Link>
      </div>
    </section>
  );
};

const CapabilitiesSection = () => {
  const t = dictionary.landing;

  return (
    <section className="flex flex-col gap-8 border-border border-b py-14 sm:py-16">
      <div className="flex flex-col gap-3">
        <h2 className="font-semibold text-3xl tracking-normal sm:text-4xl">
          {t.capabilities.heading}
        </h2>
        <p className="text-muted-foreground leading-7">
          {t.capabilities.description}
        </p>
      </div>

      <div className="grid gap-3">
        {capabilities.map((capability) => (
          <CapabilityItem key={capability.copy.title} {...capability} />
        ))}
      </div>
    </section>
  );
};

const CapabilityItem = ({
  copy,
  icon: Icon,
}: (typeof capabilities)[number]) => {
  return (
    <article className="grid gap-4 rounded-lg border border-border bg-card p-5 sm:grid-cols-[2rem_1fr] sm:items-start">
      <div className="flex size-8 items-center justify-center rounded-md bg-muted text-foreground">
        <Icon className="size-4" aria-hidden="true" />
      </div>
      <div className="flex flex-col gap-1">
        <h3 className="font-medium text-base">{copy.title}</h3>
        <p className="text-muted-foreground text-sm leading-6">
          {copy.description}
        </p>
      </div>
    </article>
  );
};

const SupportedInputsSection = () => {
  const t = dictionary.landing;

  return (
    <section className="py-14 sm:py-16">
      <div className="flex flex-col gap-4">
        <h2 className="font-semibold text-2xl tracking-normal">
          {t.supportedInputs.heading}
        </h2>
        <div className="flex flex-wrap gap-2">
          {supportedInputs.map((input) => (
            <SupportedInputItem key={input.extension} input={input} />
          ))}
        </div>
      </div>
    </section>
  );
};

const SupportedInputItem = ({
  input,
}: {
  input: (typeof supportedInputs)[number];
}) => {
  const t = dictionary.landing;
  const isAvailable = input.status === "available";

  return (
    <span
      className={cn(
        "inline-flex items-center gap-2 rounded-md border bg-card px-3 py-2 font-mono text-sm",
        isAvailable ? "border-primary/20" : "border-border",
      )}
    >
      {isAvailable ? (
        <Check className="size-4 text-primary" aria-hidden="true" />
      ) : (
        <Clock className="size-4 text-muted-foreground" aria-hidden="true" />
      )}
      {input.extension}
      <span className="font-sans text-muted-foreground text-xs">
        {isAvailable
          ? t.supportedInputs.availableLabel
          : t.supportedInputs.plannedLabel}
      </span>
    </span>
  );
};

const LandingFooter = () => {
  const t = dictionary.landing;

  return (
    <footer className="w-full border-border border-t">
      <div className="mx-auto flex w-full flex-col gap-2 px-5 py-6 text-muted-foreground text-sm sm:flex-row sm:items-center sm:justify-between sm:px-8 lg:px-10">
        <p>{t.footer.copyright}</p>
        <p>
          {t.footer.contactLabel}{" "}
          <a
            href={`mailto:${t.footer.contactEmail}`}
            className="text-foreground underline-offset-4 hover:underline"
          >
            {t.footer.contactEmail}
          </a>
        </p>
      </div>
    </footer>
  );
};
