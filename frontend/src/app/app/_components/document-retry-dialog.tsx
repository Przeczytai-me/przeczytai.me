import { RefreshCw } from "lucide-react";
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

const copy = dictionary.app.documents;

type DocumentRetryDialogProps = {
  isError: boolean;
  isPending: boolean;
  onConfirm: () => void;
  title: string;
};

export const DocumentRetryDialog = ({
  isError,
  isPending,
  onConfirm,
  title,
}: DocumentRetryDialogProps) => (
  <DialogContent closeLabel={copy.dialog.close}>
    <DialogHeader>
      <DialogTitle>{copy.dialog.retry.title}</DialogTitle>
      <DialogDescription>
        {copy.dialog.retry.description(title)}
      </DialogDescription>
    </DialogHeader>
    {isError && (
      <p aria-live="polite" className="text-destructive text-sm" role="status">
        {copy.dialog.retry.error}
      </p>
    )}
    <DialogFooter>
      <DialogClose render={<Button variant="outline" />}>
        {copy.dialog.cancel}
      </DialogClose>
      <Button disabled={isPending} onClick={onConfirm} type="button">
        <RefreshCw
          aria-hidden="true"
          className={cn(isPending && "animate-spin")}
        />
        {isPending ? copy.actions.retrying : copy.dialog.retry.confirm}
      </Button>
    </DialogFooter>
  </DialogContent>
);
