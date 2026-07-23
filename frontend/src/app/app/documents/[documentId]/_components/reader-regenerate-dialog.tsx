import { AlertTriangle, RefreshCw } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  DialogClose,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { dictionary } from "@/i18n/dictionaries";
import { cn } from "@/lib/utils";

const copy = dictionary.app.reader;

type ReaderRegenerateDialogProps = {
  isRetrying: boolean;
  onRetry: () => void;
  retryError?: string;
};

export const ReaderRegenerateDialog = ({
  isRetrying,
  onRetry,
  retryError,
}: ReaderRegenerateDialogProps) => (
  <DialogContent closeLabel={copy.dialog.close}>
    <DialogHeader>
      <div className="mb-1 flex size-10 items-center justify-center rounded-full bg-destructive/10 text-destructive">
        <AlertTriangle className="size-5" aria-hidden="true" />
      </div>
      <DialogTitle>{copy.regenerate.title}</DialogTitle>
      <DialogDescription>{copy.regenerate.description}</DialogDescription>
    </DialogHeader>
    <p className="rounded-lg border border-destructive/20 bg-destructive/5 p-3 text-sm">
      {copy.regenerate.warning}
    </p>
    {retryError && (
      <p aria-live="polite" className="text-destructive text-xs" role="status">
        {retryError}
      </p>
    )}
    <DialogFooter>
      <DialogClose render={<Button variant="outline" />}>
        {copy.regenerate.cancel}
      </DialogClose>
      <Button
        disabled={isRetrying}
        onClick={onRetry}
        type="button"
        variant="destructive"
      >
        <RefreshCw
          aria-hidden="true"
          className={cn(isRetrying && "animate-spin")}
        />
        {isRetrying ? copy.details.actions.retrying : copy.regenerate.confirm}
      </Button>
    </DialogFooter>
  </DialogContent>
);
