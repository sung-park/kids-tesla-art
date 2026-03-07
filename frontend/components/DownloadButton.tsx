"use client";

import { useT } from "@/contexts/LocaleContext";

interface DownloadButtonProps {
  blobUrl: string;
  filename: string;
}

export default function DownloadButton({ blobUrl, filename }: DownloadButtonProps) {
  const t = useT();

  return (
    <div className="flex flex-col items-center gap-3">
      <a
        href={blobUrl}
        download={filename}
        className="w-full inline-flex items-center justify-center gap-2 px-6 py-4 rounded-2xl border-2 border-ink bg-crayon-mint text-ink font-bold text-base shadow-[4px_4px_0px_#1A1A1A] hover:-rotate-1 transition-transform duration-150"
      >
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5M16.5 12L12 16.5m0 0L7.5 12m4.5 4.5V3" />
        </svg>
        {t.download.button}
      </a>
      <a
        href="/guide"
        className="text-sm font-bold text-ink/50 underline hover:text-ink transition-colors"
      >
        {t.download.guideLink}
      </a>
    </div>
  );
}
