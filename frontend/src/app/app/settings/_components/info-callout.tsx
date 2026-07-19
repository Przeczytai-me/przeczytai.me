import { Info } from "lucide-react";
import type { ReactNode } from "react";

type InfoCalloutProps = {
  children: ReactNode;
  title?: string;
};

export const InfoCallout = ({ children, title }: InfoCalloutProps) => (
  <div className="flex gap-3 rounded-md border border-sky-200 bg-sky-50 p-4 text-sky-950 text-sm">
    <Info aria-hidden="true" className="mt-0.5 size-4 shrink-0 text-sky-700" />
    <div>
      {title ? <p className="font-medium">{title}</p> : null}
      <p className={title ? "mt-1 text-sky-900/80" : "text-sky-900/80"}>
        {children}
      </p>
    </div>
  </div>
);
