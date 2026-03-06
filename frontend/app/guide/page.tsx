"use client";

import Link from "next/link";
import { useT } from "@/contexts/LocaleContext";

export default function GuidePage() {
  const t = useT();

  return (
    <div className="max-w-2xl mx-auto px-4 py-12">
      <div className="mb-10">
        <h1 className="text-3xl font-bold text-tesla-dark dark:text-white mb-3">
          {t.guide.title}
        </h1>
        <p className="text-gray-600 dark:text-gray-400">
          {t.guide.subtitle}
        </p>
      </div>

      <div className="space-y-6">
        {t.guide.steps.map((step, i) => (
          <div
            key={i}
            className="flex gap-4 p-5 rounded-xl bg-gray-50 dark:bg-gray-800"
          >
            <div className="shrink-0 w-8 h-8 rounded-full bg-tesla-red text-white text-sm font-bold flex items-center justify-center">
              {i + 1}
            </div>
            <div className="min-w-0">
              <h2 className="font-semibold text-tesla-dark dark:text-white">
                {step.title}
              </h2>
              <p className="text-gray-700 dark:text-gray-300 text-sm mt-1">
                {step.description}
              </p>
              {"detailMac" in step && (
                <>
                  <p className="text-sm text-gray-600 dark:text-gray-400 mt-2">
                    <strong>{step.detailMac}</strong>
                  </p>
                  <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                    <strong>{step.detailWindows}</strong>
                  </p>
                </>
              )}
              {"detail" in step && step.detail && (
                <p className="text-sm text-gray-600 dark:text-gray-400 mt-2">
                  {step.detail}
                </p>
              )}
            </div>
          </div>
        ))}
      </div>

      <div className="mt-10 p-5 rounded-xl border border-amber-200 bg-amber-50 dark:border-amber-800 dark:bg-amber-950">
        <h3 className="font-semibold text-amber-800 dark:text-amber-300 mb-2">
          {t.guide.importantTitle}
        </h3>
        <ul className="text-sm text-amber-700 dark:text-amber-400 space-y-1.5 list-disc list-inside">
          {t.guide.importantNotes.map((note) => (
            <li key={note}>{note}</li>
          ))}
        </ul>
      </div>

      <div className="mt-8 text-center">
        <Link
          href="/"
          className="inline-flex items-center gap-2 text-sm text-tesla-red hover:underline"
        >
          {t.guide.backLink}
        </Link>
      </div>
    </div>
  );
}
