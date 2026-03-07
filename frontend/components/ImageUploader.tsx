"use client";

import { useCallback, useRef, useState } from "react";
import { useT } from "@/contexts/LocaleContext";

const ACCEPTED_TYPES = ["image/jpeg", "image/png", "image/webp", "image/heic", "image/heif"];
const MAX_SIZE_BYTES = 20 * 1024 * 1024; // 20MB

interface ImageUploaderProps {
  onFileSelected: (file: File) => void;
  disabled?: boolean;
}

export default function ImageUploader({
  onFileSelected,
  disabled = false,
}: ImageUploaderProps) {
  const t = useT();
  const [isDragging, setIsDragging] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const cameraInputRef = useRef<HTMLInputElement>(null);

  const validateAndSelect = useCallback(
    (file: File) => {
      setError(null);
      if (!ACCEPTED_TYPES.includes(file.type) && !file.name.toLowerCase().match(/\.(heic|heif)$/)) {
        setError(t.uploader.invalidType);
        return;
      }
      if (file.size > MAX_SIZE_BYTES) {
        setError(t.uploader.tooLarge);
        return;
      }
      onFileSelected(file);
    },
    [onFileSelected, t]
  );

  const handleDrop = useCallback(
    (e: React.DragEvent<HTMLDivElement>) => {
      e.preventDefault();
      setIsDragging(false);
      const file = e.dataTransfer.files[0];
      if (file) validateAndSelect(file);
    },
    [validateAndSelect]
  );

  const handleFileChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const file = e.target.files?.[0];
      if (file) validateAndSelect(file);
      e.target.value = "";
    },
    [validateAndSelect]
  );

  return (
    <div className="space-y-3">
      <div
        role="button"
        tabIndex={disabled ? -1 : 0}
        aria-label="Drop image here or click to upload"
        onDragOver={(e) => { e.preventDefault(); if (!disabled) setIsDragging(true); }}
        onDragLeave={() => setIsDragging(false)}
        onDrop={disabled ? undefined : handleDrop}
        onClick={() => !disabled && fileInputRef.current?.click()}
        onKeyDown={(e) => { if ((e.key === "Enter" || e.key === " ") && !disabled) fileInputRef.current?.click(); }}
        className={[
          "relative border-4 border-dashed rounded-3xl p-10 text-center cursor-pointer select-none transition-transform duration-150",
          isDragging
            ? "border-crayon-pink bg-pastel-pink -rotate-1"
            : "border-ink/30 hover:border-crayon-yellow hover:-rotate-1",
          disabled ? "opacity-50 cursor-not-allowed" : "",
        ].join(" ")}
      >
        <div className="flex flex-col items-center gap-3">
          <span className="text-5xl">🎨</span>
          <div>
            <p className="font-bold text-ink text-base">
              {t.uploader.dropHere}
            </p>
            <p className="text-sm text-ink/60 mt-1">
              {t.uploader.clickToBrowse}
            </p>
          </div>
          <p className="text-xs text-ink/40">{t.uploader.fileTypes}</p>
        </div>
      </div>

      {/* Hidden file inputs */}
      <input
        ref={fileInputRef}
        type="file"
        accept="image/jpeg,image/png,image/webp,image/heic,image/heif,.heic,.heif"
        className="hidden"
        onChange={handleFileChange}
        aria-hidden="true"
      />
      <input
        ref={cameraInputRef}
        type="file"
        accept="image/*"
        capture="environment"
        className="hidden"
        onChange={handleFileChange}
        aria-hidden="true"
      />

      {/* Mobile camera button */}
      <button
        type="button"
        disabled={disabled}
        onClick={() => !disabled && cameraInputRef.current?.click()}
        className="w-full flex items-center justify-center gap-2 py-3 px-4 rounded-2xl border-2 border-ink bg-pastel-sky text-ink text-sm font-bold shadow-[3px_3px_0px_#1A1A1A] hover:-rotate-1 transition-transform duration-150 disabled:opacity-50 disabled:cursor-not-allowed md:hidden"
      >
        <span className="text-lg">📸</span>
        {t.uploader.takePhoto}
      </button>

      {error && (
        <p role="alert" className="text-sm font-bold text-tesla-red text-center">
          {error}
        </p>
      )}
    </div>
  );
}
