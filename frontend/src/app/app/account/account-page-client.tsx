import { dictionary } from "@/i18n/dictionaries";
import { AccountDataCard } from "./_components/account-data-card";
import { AccountEmailCard } from "./_components/account-email-card";
import { AccountSessionCard } from "./_components/account-session-card";

const copy = dictionary.app.account;

export const AccountPageClient = () => {
  return (
    <section className="mx-auto flex w-full max-w-5xl flex-col gap-5 pb-8">
      <header className="space-y-1">
        <h1 className="font-semibold text-2xl tracking-tight">
          {copy.heading}
        </h1>
        <p className="text-muted-foreground text-sm">{copy.description}</p>
      </header>

      <AccountEmailCard />
      <AccountDataCard />
      <AccountSessionCard />
    </section>
  );
};
