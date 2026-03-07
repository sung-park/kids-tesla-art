"use client";

import Link from "next/link";
import { useLocale, useT } from "@/contexts/LocaleContext";
import type { Locale } from "@/lib/i18n";

export default function Header() {
  const { locale, setLocale } = useLocale();
  const t = useT();

  return (
    <header className="border-b-4 border-ink bg-ivory">
      <div className="max-w-4xl mx-auto px-4 py-3 flex items-center justify-between">
        <Link href="/" className="flex items-center gap-1 hover:-rotate-1 transition-transform duration-150">
          <span className="text-lg sm:text-2xl font-bold text-crayon-pink">Kids</span>
          <span className="text-lg sm:text-2xl font-bold text-ink">Tesla Art</span>
          <span className="text-base sm:text-xl">🎨</span>
        </Link>
        <nav className="flex items-center gap-2 sm:gap-4 text-sm font-bold text-ink">
          <Link href="/" className="hover:text-crayon-pink transition-colors">
            {t.nav.create}
          </Link>
          <Link
            href="/guide"
            className="hover:text-crayon-sky transition-colors whitespace-nowrap"
          >
            <span className="hidden sm:inline">{t.nav.howToApply}</span>
            <span className="sm:hidden">Guide</span>
          </Link>
          <a
            href="https://github.com/sung-park/kids-tesla-art"
            target="_blank"
            rel="noopener noreferrer"
            className="hidden sm:block hover:text-crayon-mint transition-colors"
          >
            GitHub
          </a>
          <div className="flex items-center gap-1 border-2 border-ink rounded-xl overflow-hidden text-xs font-bold shadow-[2px_2px_0px_#1A1A1A]">
            {(["ko", "en"] as Locale[]).map((lang) => (
              <button
                key={lang}
                type="button"
                onClick={() => setLocale(lang)}
                className={[
                  "px-3 py-1.5 transition-colors",
                  locale === lang
                    ? "bg-crayon-yellow text-ink"
                    : "bg-ivory hover:bg-pastel-yellow",
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
