import { ChevronDown } from "lucide-react";

type Option = {
  label: string;
  value: string;
};

type SelectFieldProps = {
  label: string;
  onChange: (value: string) => void;
  options: readonly Option[];
  value: string;
};

export const SelectField = ({
  label,
  onChange,
  options,
  value,
}: SelectFieldProps) => (
  <label className="grid gap-2 text-sm">
    <span className="font-medium">{label}</span>
    <span className="relative">
      <select
        className="h-9 w-full appearance-none rounded-md border border-input bg-background px-3 pr-10 text-sm"
        value={value}
        onChange={(event) => onChange(event.target.value)}
      >
        {options.map((option) => (
          <option key={option.value} value={option.value}>
            {option.label}
          </option>
        ))}
      </select>
      <ChevronDown
        aria-hidden="true"
        className="-translate-y-1/2 pointer-events-none absolute top-1/2 right-3 size-4 text-muted-foreground"
      />
    </span>
  </label>
);
