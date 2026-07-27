import Link from "next/link";
import { dictionary } from "@/i18n/dictionaries";

export const PublicFooter = () => {
  const copy = dictionary.landing.footer;

  return (
    <footer className="w-full border-border border-t">
      <div className="mx-auto flex w-full flex-col gap-4 px-5 py-6 text-muted-foreground text-sm sm:px-8 lg:flex-row lg:items-center lg:justify-between lg:px-10">
        <p>{copy.copyright}</p>
        <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:gap-5">
          <nav
            aria-label={copy.navigationLabel}
            className="flex flex-wrap items-center gap-x-4 gap-y-2"
          >
            <Link
              className="text-foreground underline-offset-4 hover:underline"
              href="/privacy"
            >
              {copy.privacy}
            </Link>
            <Link
              className="text-foreground underline-offset-4 hover:underline"
              href="/terms"
            >
              {copy.terms}
            </Link>
          </nav>
          <p>
            {copy.contactLabel}{" "}
            <a
              href={`mailto:${copy.contactEmail}`}
              className="text-foreground underline-offset-4 hover:underline"
            >
              {copy.contactEmail}
            </a>
          </p>
        </div>
      </div>
    </footer>
  );
};
