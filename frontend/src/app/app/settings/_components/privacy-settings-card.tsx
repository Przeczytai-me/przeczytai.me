import { ExternalLink, Lock, RotateCcw, Trash2 } from "lucide-react";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { dictionary } from "@/i18n/dictionaries";
import { InfoCallout } from "./info-callout";
import { SettingsCard } from "./settings-card";

const copy = dictionary.app.settings;

type PrivacySettingsCardProps = {
  onReset: () => void;
};

export const PrivacySettingsCard = ({ onReset }: PrivacySettingsCardProps) => (
  <SettingsCard
    description={
      <span>
        {copy.sections.privacy.description}{" "}
        <Link
          className="inline-flex items-center gap-1 underline-offset-4 hover:underline"
          href="/privacy"
        >
          {copy.sections.privacy.linkLabel}
          <ExternalLink aria-hidden="true" className="size-3" />
        </Link>
      </span>
    }
    icon={<Lock aria-hidden="true" className="size-4" />}
    title={copy.sections.privacy.title}
  >
    <InfoCallout title={copy.privacyRetentionTitle}>
      {copy.privacyRetentionDescription}
    </InfoCallout>
    <Button
      type="button"
      className="border-amber-200 bg-amber-50 text-amber-900 hover:bg-amber-100 focus-visible:border-amber-400 focus-visible:ring-amber-200"
      variant="outline"
      onClick={onReset}
    >
      <RotateCcw aria-hidden="true" className="size-3.5" />
      {copy.actions.reset}
    </Button>
    <Button type="button" variant="destructive" disabled>
      <Trash2 aria-hidden="true" className="size-3.5" />
      {copy.actions.deleteAllDocuments}
    </Button>
    <p className="text-muted-foreground text-xs italic">
      {copy.unsupported.deleteAllDocuments}
    </p>
  </SettingsCard>
);
