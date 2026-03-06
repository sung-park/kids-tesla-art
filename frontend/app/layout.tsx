import type { Metadata } from "next";
import "./globals.css";
import { LocaleProvider } from "@/contexts/LocaleContext";
import Header from "@/components/Header";
import Footer from "@/components/Footer";

export const metadata: Metadata = {
  title: "Kids Tesla Art",
  description:
    "Transform your child's artwork into a custom Tesla wrap. Download a template, let your kids color it, upload a photo, and get a Tesla-ready PNG instantly.",
  keywords: ["Tesla", "custom wrap", "kids", "art", "Toybox", "Paint Shop"],
  openGraph: {
    title: "Kids Tesla Art",
    description: "Turn your child's drawing into a custom Tesla wrap",
    type: "website",
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="ko" suppressHydrationWarning>
      <body className="min-h-screen bg-white dark:bg-tesla-dark antialiased">
        <LocaleProvider>
          <Header />
          <main>{children}</main>
          <Footer />
        </LocaleProvider>
      </body>
    </html>
  );
}
