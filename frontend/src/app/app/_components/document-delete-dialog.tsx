import { Trash2 } from "lucide-react";
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

const copy = dictionary.app.documents;

type DocumentDeleteDialogProps = {
  isError: boolean;
  isPending: boolean;
  onConfirm: () => void;
  title: string;
};

export const DocumentDeleteDialog = ({
  isError,
  isPending,
  onConfirm,
  title,
}: DocumentDeleteDialogProps) => (
  <DialogContent closeLabel={copy.dialog.close}>
    <DialogHeader>
      <DialogTitle>{copy.dialog.delete.title}</DialogTitle>
      <DialogDescription>
        {copy.dialog.delete.description(title)}
      </DialogDescription>
    </DialogHeader>
    {isError && (
      <p aria-live="polite" className="text-destructive text-sm" role="status">
        {copy.dialog.delete.error}
      </p>
    )}
    <DialogFooter>
      <DialogClose render={<Button variant="outline" />}>
        {copy.dialog.cancel}
      </DialogClose>
      <Button
        disabled={isPending}
        onClick={onConfirm}
        type="button"
        variant="destructive"
      >
        <Trash2 aria-hidden="true" />
        {isPending ? copy.actions.deleting : copy.dialog.delete.confirm}
      </Button>
    </DialogFooter>
  </DialogContent>
);
