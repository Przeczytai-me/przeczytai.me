import { ClerkProvider } from "@clerk/nextjs";
import type { Metadata } from "next";
import { Geist_Mono, Inter } from "next/font/google";
import { Providers } from "@/components/providers";
import { dictionary } from "@/i18n/dictionaries";
import { defaultLocale } from "@/i18n/locales";
import { cn } from "@/lib/utils";
import "./globals.css";

const inter = Inter({
  variable: "--font-inter",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: dictionary.metadata.title,
  description: dictionary.metadata.description,
};

const RootLayout = ({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) => {
  return (
    <ClerkProvider>
      <html
        lang={defaultLocale}
        className={cn(
          "h-full antialiased",
          inter.className,
          inter.variable,
          geistMono.variable,
        )}
      >
        <body className="flex min-h-full flex-col">
          <Providers>{children}</Providers>
        </body>
      </html>
    </ClerkProvider>
  );
};

export default RootLayout;
