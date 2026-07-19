"use client";

import { useClerk, useUser } from "@clerk/nextjs";
import { Mail, UserRoundCog } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { dictionary } from "@/i18n/dictionaries";

const copy = dictionary.app.account.email;

export const AccountEmailCard = () => {
  const { openUserProfile } = useClerk();
  const { isLoaded, user } = useUser();
  const emailAddress =
    user?.primaryEmailAddress?.emailAddress ??
    user?.emailAddresses[0]?.emailAddress;

  return (
    <Card className="rounded-md">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <span className="flex size-8 items-center justify-center rounded-md bg-muted text-muted-foreground">
            <Mail aria-hidden="true" className="size-4" />
          </span>
          {copy.title}
        </CardTitle>
        <CardDescription>{copy.description}</CardDescription>
      </CardHeader>
      <CardContent className="flex flex-col items-start gap-4">
        <div>
          <p className="text-muted-foreground text-xs uppercase tracking-wide">
            {copy.label}
          </p>
          <p className="mt-1 font-medium text-sm">
            {isLoaded ? (emailAddress ?? copy.unavailable) : copy.loading}
          </p>
        </div>
        <Button
          type="button"
          variant="outline"
          onClick={() => openUserProfile()}
        >
          <UserRoundCog aria-hidden="true" className="size-4" />
          {copy.manageAccount}
        </Button>
      </CardContent>
    </Card>
  );
};
