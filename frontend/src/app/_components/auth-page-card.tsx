import { ArrowLeft } from "lucide-react";
import Link from "next/link";
import type { ReactNode } from "react";
import { buttonVariants } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { dictionary } from "@/i18n/dictionaries";
import { cn } from "@/lib/utils";

type AuthPageCardProps = {
  children: ReactNode;
  description: string;
  title: string;
};

export const AuthPageCard = ({
  children,
  description,
  title,
}: AuthPageCardProps) => {
  const t = dictionary.auth;

  return (
    <main className="flex min-h-screen flex-1 items-center justify-center bg-background px-5 py-10">
      <div className="flex w-full max-w-md flex-col gap-4">
        <Link
          href="/"
          className={cn(
            buttonVariants({ variant: "ghost", size: "sm" }),
            "w-fit",
          )}
        >
          <ArrowLeft data-icon="inline-start" />
          {t.backToLanding}
        </Link>

        <Card className="w-full border-primary border-t-4">
          <CardHeader>
            <CardTitle className="text-2xl text-primary">{title}</CardTitle>
            <CardDescription>{description}</CardDescription>
          </CardHeader>
          <CardContent>{children}</CardContent>
          <CardFooter>
            <p className="text-muted-foreground text-sm leading-6">
              {t.privateWorkspaceNote}
            </p>
          </CardFooter>
        </Card>
      </div>
    </main>
  );
};
