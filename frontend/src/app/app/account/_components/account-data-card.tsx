import { ExternalLink, ShieldCheck } from "lucide-react";
import Link from "next/link";
import { buttonVariants } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { dictionary } from "@/i18n/dictionaries";
import { cn } from "@/lib/utils";

const copy = dictionary.app.account.data;
const contactEmail = dictionary.landing.footer.contactEmail;
const deletionRequestUrl = `mailto:${contactEmail}?subject=${encodeURIComponent(copy.deletionRequestSubject)}`;

export const AccountDataCard = () => (
  <Card className="rounded-md">
    <CardHeader>
      <CardTitle className="flex items-center gap-2">
        <span className="flex size-8 items-center justify-center rounded-md bg-muted text-muted-foreground">
          <ShieldCheck aria-hidden="true" className="size-4" />
        </span>
        {copy.title}
      </CardTitle>
      <CardDescription>{copy.description}</CardDescription>
    </CardHeader>
    <CardContent className="flex flex-col gap-3">
      <div className="flex flex-wrap gap-2">
        <Link
          className={buttonVariants({ variant: "outline" })}
          href="/privacy"
        >
          {copy.privacyPolicy}
          <ExternalLink aria-hidden="true" className="size-3.5" />
        </Link>
        <a
          className={cn(
            buttonVariants({ variant: "destructive" }),
            "no-underline",
          )}
          href={deletionRequestUrl}
        >
          {copy.deletionRequest}
        </a>
      </div>
      <p className="text-muted-foreground text-xs italic">
        {copy.deletionRequestNote}
      </p>
    </CardContent>
  </Card>
);
