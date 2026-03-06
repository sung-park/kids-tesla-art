import type { Metadata } from "next";
import Link from "next/link";
import "./globals.css";

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
    <html lang="en">
      <body className="min-h-screen bg-white dark:bg-tesla-dark antialiased">
        <header className="border-b border-gray-200 dark:border-gray-800">
          <div className="max-w-4xl mx-auto px-4 py-4 flex items-center justify-between">
            <Link href="/" className="flex items-center gap-2">
              <span className="text-tesla-red font-bold text-xl">Kids</span>
              <span className="font-semibold text-lg text-tesla-dark dark:text-white">
                Tesla Art
              </span>
            </Link>
            <nav className="flex gap-6 text-sm text-gray-600 dark:text-gray-400">
              <Link href="/" className="hover:text-tesla-red transition-colors">
                Create
              </Link>
              <Link
                href="/guide"
                className="hover:text-tesla-red transition-colors"
              >
                How to Apply
              </Link>
              <a
                href="https://github.com/sung-park/kids-tesla-art"
                target="_blank"
                rel="noopener noreferrer"
                className="hover:text-tesla-red transition-colors"
              >
                GitHub
              </a>
            </nav>
          </div>
        </header>
        <main>{children}</main>
        <footer className="border-t border-gray-200 dark:border-gray-800 mt-16 py-8">
          <div className="max-w-4xl mx-auto px-4 text-center text-sm text-gray-500">
            <p>
              Open source project. Not affiliated with Tesla, Inc.{" "}
              <a
                href="https://github.com/sung-park/kids-tesla-art"
                target="_blank"
                rel="noopener noreferrer"
                className="underline hover:text-tesla-red"
              >
                View source on GitHub
              </a>
            </p>
          </div>
        </footer>
      </body>
    </html>
  );
}
