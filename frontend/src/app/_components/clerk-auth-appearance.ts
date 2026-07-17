import type { SignIn, SignUp } from "@clerk/nextjs";
import type { ComponentProps } from "react";

type ClerkAuthAppearance = NonNullable<
  | ComponentProps<typeof SignIn>["appearance"]
  | ComponentProps<typeof SignUp>["appearance"]
>;

export const clerkAuthAppearance = {
  elements: {
    card: "w-full border-0 bg-transparent p-0 shadow-none",
    footerActionLink: "text-primary hover:text-primary/80",
    footerActionText: "text-muted-foreground",
    formButtonPrimary:
      "h-8 rounded-lg bg-primary text-primary-foreground text-sm font-medium shadow-none hover:bg-primary/90",
    formFieldInput:
      "h-9 rounded-lg border-border bg-background text-foreground shadow-none focus-visible:ring-3 focus-visible:ring-ring/50",
    header: "hidden",
    rootBox: "w-full",
    socialButtonsBlockButton:
      "h-9 rounded-lg border-border bg-background text-foreground shadow-none hover:bg-muted",
  },
  variables: {
    borderRadius: "0.45rem",
    colorPrimary: "var(--primary)",
    fontFamily: "var(--font-inter), Arial, sans-serif",
  },
} satisfies ClerkAuthAppearance;
