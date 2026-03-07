"use client";

import { useT } from "@/contexts/LocaleContext";

export default function Footer() {
  const t = useT();

  return (
    <footer className="border-t-4 border-ink bg-ivory mt-16 py-8">
      <div className="max-w-4xl mx-auto px-4 text-center text-sm text-ink/60 font-bold">
        <p>
          {t.footer.openSource}{" "}
          <a
            href="https://github.com/sung-park/kids-tesla-art"
            target="_blank"
            rel="noopener noreferrer"
            className="underline hover:text-crayon-pink transition-colors"
          >
            {t.footer.viewSource}
          </a>
        </p>
      </div>
    </footer>
  );
}
