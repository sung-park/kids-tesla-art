"use client";

import { useT } from "@/contexts/LocaleContext";

export default function Footer() {
  const t = useT();

  return (
    <footer className="border-t border-gray-200 dark:border-gray-800 mt-16 py-8">
      <div className="max-w-4xl mx-auto px-4 text-center text-sm text-gray-500">
        <p>
          {t.footer.openSource}{" "}
          <a
            href="https://github.com/sung-park/kids-tesla-art"
            target="_blank"
            rel="noopener noreferrer"
            className="underline hover:text-tesla-red"
          >
            {t.footer.viewSource}
          </a>
        </p>
      </div>
    </footer>
  );
}
