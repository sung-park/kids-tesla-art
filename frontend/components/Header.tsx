"use client";

import Link from "next/link";
import { useLocale, useT } from "@/contexts/LocaleContext";
import type { Locale } from "@/lib/i18n";

export default function Header() {
  const { locale, setLocale } = useLocale();
  const t = useT();

  return (
    <header className="border-b border-gray-200 dark:border-gray-800">
      <div className="max-w-4xl mx-auto px-4 py-4 flex items-center justify-between">
        <Link href="/" className="flex items-center gap-2">
          <span className="text-tesla-red font-bold text-xl">Kids</span>
          <span className="font-semibold text-lg text-tesla-dark dark:text-white">
            Tesla Art
          </span>
        </Link>
        <nav className="flex items-center gap-6 text-sm text-gray-600 dark:text-gray-400">
          <Link href="/" className="hover:text-tesla-red transition-colors">
            {t.nav.create}
          </Link>
          <Link
            href="/guide"
            className="hover:text-tesla-red transition-colors"
          >
            {t.nav.howToApply}
          </Link>
          <a
            href="https://github.com/sung-park/kids-tesla-art"
            target="_blank"
            rel="noopener noreferrer"
            className="hover:text-tesla-red transition-colors"
          >
            GitHub
          </a>
          <div className="flex items-center gap-1 border border-gray-200 dark:border-gray-700 rounded-lg overflow-hidden text-xs font-medium">
            {(["ko", "en"] as Locale[]).map((lang) => (
              <button
                key={lang}
                type="button"
                onClick={() => setLocale(lang)}
                className={[
                  "px-2.5 py-1 transition-colors",
                  locale === lang
                    ? "bg-tesla-red text-white"
                    : "hover:bg-gray-100 dark:hover:bg-gray-800",
                ].join(" ")}
              >
                {lang.toUpperCase()}
              </button>
            ))}
          </div>
        </nav>
      </div>
    </header>
  );
}
