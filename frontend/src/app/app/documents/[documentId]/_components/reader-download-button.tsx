import { Download } from "lucide-react";
import { Button } from "@/components/ui/button";

type ReaderDownloadButtonProps = {
  disabled: boolean;
  label: string;
  onClick: () => void;
};

export const ReaderDownloadButton = ({
  disabled,
  label,
  onClick,
}: ReaderDownloadButtonProps) => (
  <Button
    className="w-full justify-start"
    disabled={disabled}
    onClick={onClick}
    type="button"
    variant="outline"
  >
    <Download aria-hidden="true" />
    {label}
  </Button>
);
