import type { ReactNode } from "react";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";

type SettingsCardProps = {
  children: ReactNode;
  description: ReactNode;
  icon: ReactNode;
  title: string;
};

export const SettingsCard = ({
  children,
  description,
  icon,
  title,
}: SettingsCardProps) => (
  <Card className="rounded-md">
    <CardHeader>
      <CardTitle className="flex items-center gap-2">
        <span className="flex size-8 items-center justify-center rounded-md bg-muted text-muted-foreground">
          {icon}
        </span>
        {title}
      </CardTitle>
      <CardDescription>{description}</CardDescription>
    </CardHeader>
    <CardContent className="grid gap-4">{children}</CardContent>
  </Card>
);
