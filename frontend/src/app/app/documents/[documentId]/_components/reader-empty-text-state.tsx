import { AlertCircle } from "lucide-react";

type ReaderEmptyTextStateProps = {
  description: string;
  title: string;
};

export const ReaderEmptyTextState = ({
  description,
  title,
}: ReaderEmptyTextStateProps) => (
  <div className="rounded-lg border border-dashed border-border p-8 text-center">
    <AlertCircle
      className="mx-auto size-6 text-muted-foreground"
      aria-hidden="true"
    />
    <p className="mt-3 font-medium">{title}</p>
    <p className="mx-auto mt-1 max-w-md text-muted-foreground text-sm">
      {description}
    </p>
  </div>
);
