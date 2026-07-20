import { LogOut } from "lucide-react";
import { SignOutButton } from "@/components/sign-out-button";
import { buttonVariants } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { dictionary } from "@/i18n/dictionaries";

const copy = dictionary.app.account.session;

export const AccountSessionCard = () => (
  <Card className="rounded-md">
    <CardHeader>
      <CardTitle className="flex items-center gap-2">
        <span className="flex size-8 items-center justify-center rounded-md bg-muted text-muted-foreground">
          <LogOut aria-hidden="true" className="size-4" />
        </span>
        {copy.title}
      </CardTitle>
      <CardDescription>{copy.description}</CardDescription>
    </CardHeader>
    <CardContent>
      <SignOutButton className={buttonVariants({ variant: "outline" })}>
        <LogOut aria-hidden="true" className="size-4" />
        {copy.signOut}
      </SignOutButton>
    </CardContent>
  </Card>
);
