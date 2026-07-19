import type { BaseLayoutProps } from "fumadocs-ui/layouts/shared";
import { dictionary } from "@/i18n/dictionaries";

export const docsLayoutOptions = (): BaseLayoutProps => ({
  nav: {
    title: dictionary.landing.productName,
    url: "/",
  },
  links: [
    {
      type: "button",
      text: dictionary.docs.backToHome,
      url: "/",
      secondary: true,
    },
  ],
  searchToggle: {
    enabled: false,
  },
  themeSwitch: {
    enabled: false,
  },
});
