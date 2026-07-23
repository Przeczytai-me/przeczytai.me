import { AlertTriangle } from "lucide-react";
import { dictionary } from "@/i18n/dictionaries";

const copy = dictionary.app.reader.failure;

export const RecordingUnavailableAlert = () => (
  <div
    className="mb-3 flex shrink-0 gap-3 rounded-xl border border-destructive/30 bg-destructive/5 p-4"
    role="alert"
  >
    <AlertTriangle
      className="mt-0.5 size-5 shrink-0 text-destructive"
      aria-hidden="true"
    />
    <div>
      <p className="font-medium">{copy.mp3Title}</p>
      <p className="mt-1 text-muted-foreground text-sm">
        {copy.mp3Description}
      </p>
    </div>
  </div>
);
