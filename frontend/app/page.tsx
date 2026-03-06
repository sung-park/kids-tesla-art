"use client";

import { useCallback, useState } from "react";
import ModelSelector, { type TeslaModel } from "@/components/ModelSelector";
import ImageUploader from "@/components/ImageUploader";
import ProcessingStatus, {
  type ProcessingStep,
} from "@/components/ProcessingStatus";
import DownloadButton from "@/components/DownloadButton";
import { processImage, ProcessingError } from "@/lib/api";

interface ResultState {
  blobUrl: string;
  filename: string;
}

export default function HomePage() {
  const [model, setModel] = useState<TeslaModel>("model3");
  const [step, setStep] = useState<ProcessingStep>("idle");
  const [errorMessage, setErrorMessage] = useState<string | undefined>();
  const [result, setResult] = useState<ResultState | null>(null);

  const handleFileSelected = useCallback(
    async (file: File) => {
      setResult(null);
      setErrorMessage(undefined);
      setStep("uploading");

      try {
        const data = await processImage(file, model, setStep);
        setResult(data);
      } catch (err) {
        const message =
          err instanceof ProcessingError
            ? err.message
            : "Unexpected error. Please try again.";
        setErrorMessage(message);
        setStep("error");
      }
    },
    [model]
  );

  const handleReset = () => {
    if (result?.blobUrl) URL.revokeObjectURL(result.blobUrl);
    setResult(null);
    setStep("idle");
    setErrorMessage(undefined);
  };

  const isProcessing =
    step !== "idle" && step !== "done" && step !== "error";

  return (
    <div className="max-w-2xl mx-auto px-4 py-12">
      {/* Hero */}
      <div className="text-center mb-10">
        <h1 className="text-3xl font-bold text-tesla-dark dark:text-white mb-3">
          Turn Your Kid&apos;s Drawing Into a Tesla Wrap
        </h1>
        <p className="text-gray-600 dark:text-gray-400 text-lg">
          Print the template, let your child color it, take a photo, and get a
          custom Tesla wrap file in seconds.
        </p>
      </div>

      {/* Steps indicator */}
      <div className="flex items-center justify-center gap-2 mb-10 text-sm text-gray-500">
        {["Print & Color", "Upload Photo", "Download PNG", "Apply to Tesla"].map(
          (label, i) => (
            <div key={label} className="flex items-center gap-2">
              {i > 0 && <span className="text-gray-300">→</span>}
              <span className="flex items-center gap-1.5">
                <span className="w-5 h-5 rounded-full bg-tesla-red text-white text-xs flex items-center justify-center font-semibold">
                  {i + 1}
                </span>
                <span className="hidden sm:inline">{label}</span>
              </span>
            </div>
          )
        )}
      </div>

      <div className="space-y-6">
        {/* Model selection */}
        <section>
          <h2 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-2 uppercase tracking-wide">
            1. Select Your Tesla Model
          </h2>
          <ModelSelector selected={model} onChange={setModel} />
        </section>

        {/* Template download */}
        <section>
          <h2 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-2 uppercase tracking-wide">
            2. Download & Print Template
          </h2>
          <a
            href={`/templates/${model}-template.pdf`}
            download
            className="inline-flex items-center gap-2 px-4 py-2 rounded-lg border border-gray-300 dark:border-gray-600 text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5M16.5 12L12 16.5m0 0L7.5 12m4.5 4.5V3" />
            </svg>
            Download {model === "model3" ? "Model 3" : "Model Y"} Template (PDF)
          </a>
          <p className="text-xs text-gray-400 mt-1.5">
            Print on A4 or Letter paper. Have your child color the template with crayons or markers.
          </p>
        </section>

        {/* Upload */}
        <section>
          <h2 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-2 uppercase tracking-wide">
            3. Upload Your Photo
          </h2>
          {result ? (
            <div className="space-y-4">
              <DownloadButton
                blobUrl={result.blobUrl}
                filename={result.filename}
              />
              <button
                type="button"
                onClick={handleReset}
                className="w-full py-2 text-sm text-gray-500 hover:text-gray-700 dark:hover:text-gray-300 transition-colors"
              >
                Start over with a new photo
              </button>
            </div>
          ) : (
            <ImageUploader
              onFileSelected={handleFileSelected}
              disabled={isProcessing}
            />
          )}
        </section>

        {/* Status */}
        <ProcessingStatus step={step} errorMessage={errorMessage} />

        {/* Error retry helper */}
        {step === "error" && (
          <button
            type="button"
            onClick={handleReset}
            className="w-full py-2 text-sm text-gray-500 hover:text-gray-700 dark:hover:text-gray-300 transition-colors"
          >
            Try again
          </button>
        )}
      </div>

      {/* Tips */}
      <div className="mt-12 rounded-xl bg-gray-50 dark:bg-gray-800 p-5">
        <h3 className="font-semibold text-sm text-gray-700 dark:text-gray-300 mb-3">
          Tips for best results
        </h3>
        <ul className="text-sm text-gray-600 dark:text-gray-400 space-y-1.5 list-disc list-inside">
          <li>Place the template on a flat surface in good lighting</li>
          <li>Make sure all 4 corner markers are visible in the photo</li>
          <li>Avoid shadows or reflections over the markers</li>
          <li>Take the photo straight on, not at an angle</li>
        </ul>
      </div>
    </div>
  );
}
