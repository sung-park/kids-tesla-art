"use client";

interface DownloadButtonProps {
  blobUrl: string;
  filename: string;
}

export default function DownloadButton({ blobUrl, filename }: DownloadButtonProps) {
  return (
    <div className="flex flex-col items-center gap-3">
      <a
        href={blobUrl}
        download={filename}
        className="inline-flex items-center gap-2 px-6 py-3 bg-tesla-red text-white font-semibold rounded-xl hover:bg-red-700 transition-colors"
      >
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5M16.5 12L12 16.5m0 0L7.5 12m4.5 4.5V3" />
        </svg>
        Download Wrap PNG
      </a>
      <a
        href="/guide"
        className="text-sm text-gray-500 dark:text-gray-400 underline hover:text-tesla-red transition-colors"
      >
        How to apply it to your Tesla →
      </a>
    </div>
  );
}
