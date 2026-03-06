"use client";

import { useRef } from "react";
import { useT } from "@/contexts/LocaleContext";

interface PreviewModalProps {
  blobUrl: string;
  filename: string;
  onConfirm: () => void;
  onRedo: () => void;
}

export default function PreviewModal({
  blobUrl,
  filename,
  onConfirm,
  onRedo,
}: PreviewModalProps) {
  const t = useT();
  const anchorRef = useRef<HTMLAnchorElement>(null);

  const handleDownload = () => {
    anchorRef.current?.click();
    onConfirm();
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4">
      <div className="bg-white dark:bg-gray-900 rounded-2xl shadow-2xl w-full max-w-lg flex flex-col overflow-hidden">
        {/* Header */}
        <div className="px-6 pt-6 pb-4 border-b border-gray-100 dark:border-gray-800">
          <h2 className="text-lg font-bold text-gray-900 dark:text-white">
            {t.preview.title}
          </h2>
          <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
            {t.preview.subtitle}
          </p>
        </div>

        {/* Preview image */}
        <div className="flex items-center justify-center bg-gray-50 dark:bg-gray-800 p-4">
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img
            src={blobUrl}
            alt="Tesla wrap preview"
            className="max-h-72 w-auto object-contain rounded-lg shadow"
          />
        </div>

        {/* Actions */}
        <div className="px-6 py-5 flex flex-col gap-3">
          {/* Hidden anchor for triggering download */}
          <a ref={anchorRef} href={blobUrl} download={filename} className="hidden" aria-hidden="true" />

          <button
            type="button"
            onClick={handleDownload}
            className="w-full flex items-center justify-center gap-2 px-6 py-3 bg-tesla-red text-white font-semibold rounded-xl hover:bg-red-700 transition-colors"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5M16.5 12L12 16.5m0 0L7.5 12m4.5 4.5V3" />
            </svg>
            {t.preview.download}
          </button>

          <button
            type="button"
            onClick={onRedo}
            className="w-full py-2.5 text-sm font-medium text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-200 transition-colors rounded-xl border border-gray-200 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-800"
          >
            {t.preview.tryAgain}
          </button>
        </div>

        <div className="px-6 pb-5 text-center">
          <a
            href="/guide"
            className="text-xs text-gray-400 hover:text-tesla-red transition-colors underline"
          >
            {t.preview.guideLink}
          </a>
        </div>
      </div>
    </div>
  );
}
