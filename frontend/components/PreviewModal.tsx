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
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-ink/70 p-4">
      <div className="bg-ivory rounded-3xl border-2 border-ink shadow-[8px_8px_0px_#1A1A1A] w-full max-w-lg flex flex-col overflow-hidden">
        {/* Header */}
        <div className="px-6 pt-6 pb-4 border-b-2 border-ink">
          <h2 className="text-xl font-bold text-ink">
            {t.preview.title}
          </h2>
          <p className="text-sm text-ink/60 mt-1">
            {t.preview.subtitle}
          </p>
        </div>

        {/* Preview image */}
        <div className="flex items-center justify-center bg-white p-4 border-b-2 border-ink">
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img
            src={blobUrl}
            alt="Tesla wrap preview"
            className="max-h-72 w-auto object-contain rounded-2xl border-2 border-ink"
          />
        </div>

        {/* Actions */}
        <div className="px-6 py-5 flex flex-col gap-3">
          <a ref={anchorRef} href={blobUrl} download={filename} className="hidden" aria-hidden="true" />

          <button
            type="button"
            onClick={handleDownload}
            className="w-full flex items-center justify-center gap-2 px-6 py-4 rounded-2xl border-2 border-ink bg-crayon-mint text-ink font-bold shadow-[4px_4px_0px_#1A1A1A] hover:-rotate-1 transition-transform duration-150"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5M16.5 12L12 16.5m0 0L7.5 12m4.5 4.5V3" />
            </svg>
            {t.preview.download}
          </button>

          <button
            type="button"
            onClick={onRedo}
            className="w-full py-3 text-sm font-bold text-ink/60 hover:text-ink transition-colors rounded-2xl border-2 border-ink bg-white hover:bg-ivory"
          >
            {t.preview.tryAgain}
          </button>
        </div>

        <div className="px-6 pb-5 text-center">
          <a
            href="/guide"
            className="text-xs font-bold text-ink/40 hover:text-ink transition-colors underline"
          >
            {t.preview.guideLink}
          </a>
        </div>
      </div>
    </div>
  );
}
