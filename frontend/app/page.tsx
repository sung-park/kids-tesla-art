"use client";

import { useCallback, useState } from "react";
import ModelSelector, { type TeslaModel } from "@/components/ModelSelector";
import ImageUploader from "@/components/ImageUploader";
import ProcessingStatus, {
  type ProcessingStep,
} from "@/components/ProcessingStatus";
import DownloadButton from "@/components/DownloadButton";
import PreviewModal from "@/components/PreviewModal";
import { processImage, ProcessingError } from "@/lib/api";
import { useT } from "@/contexts/LocaleContext";

interface ResultState {
  blobUrl: string;
  filename: string;
}

export default function HomePage() {
  const t = useT();
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
            : t.home.unexpectedError;
        setErrorMessage(message);
        setStep("error");
      }
    },
    [model, t]
  );

  const handleReset = () => {
    if (result?.blobUrl) URL.revokeObjectURL(result.blobUrl);
    setResult(null);
    setStep("idle");
    setErrorMessage(undefined);
  };

  const isProcessing =
    step !== "idle" && step !== "done" && step !== "error" && step !== "previewing";

  const handleConfirmDownload = () => {
    setStep("done");
  };

  return (
    <>
    {step === "previewing" && result && (
      <PreviewModal
        blobUrl={result.blobUrl}
        filename={result.filename}
        onConfirm={handleConfirmDownload}
        onRedo={handleReset}
      />
    )}
    <div className="max-w-2xl mx-auto px-4 py-12">
      {/* Hero */}
      <div className="text-center mb-10">
        <h1 className="text-3xl font-bold text-tesla-dark dark:text-white mb-3">
          {t.home.heroTitle}
        </h1>
        <p className="text-gray-600 dark:text-gray-400 text-lg">
          {t.home.heroSubtitle}
        </p>
      </div>

      {/* Steps indicator */}
      <div className="flex items-center justify-center gap-2 mb-10 text-sm text-gray-500">
        {t.home.steps.map((label, i) => (
          <div key={label} className="flex items-center gap-2">
            {i > 0 && <span className="text-gray-300">→</span>}
            <span className="flex items-center gap-1.5">
              <span className="w-5 h-5 rounded-full bg-tesla-red text-white text-xs flex items-center justify-center font-semibold">
                {i + 1}
              </span>
              <span className="hidden sm:inline">{label}</span>
            </span>
          </div>
        ))}
      </div>

      <div className="space-y-6">
        {/* Model selection */}
        <section>
          <h2 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-2 uppercase tracking-wide">
            {t.home.step1Header}
          </h2>
          <ModelSelector selected={model} onChange={setModel} />
        </section>

        {/* Template download */}
        <section>
          <h2 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-2 uppercase tracking-wide">
            {t.home.step2Header}
          </h2>
          <a
            href={`/templates/${model}-template.pdf`}
            download
            className="inline-flex items-center gap-2 px-4 py-2 rounded-lg border border-gray-300 dark:border-gray-600 text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5M16.5 12L12 16.5m0 0L7.5 12m4.5 4.5V3" />
            </svg>
            {t.home.downloadTemplate(model === "model3" ? "Model 3" : "Model Y")}
          </a>
          <p className="text-xs text-gray-400 mt-1.5">
            {t.home.templateHint}
          </p>
        </section>

        {/* Upload */}
        <section>
          <h2 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-2 uppercase tracking-wide">
            {t.home.step3Header}
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
                {t.home.startOver}
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
            {t.home.tryAgain}
          </button>
        )}
      </div>

      {/* Tips */}
      <div className="mt-12 rounded-xl bg-gray-50 dark:bg-gray-800 p-5">
        <h3 className="font-semibold text-sm text-gray-700 dark:text-gray-300 mb-3">
          {t.home.tipsTitle}
        </h3>
        <ul className="text-sm text-gray-600 dark:text-gray-400 space-y-1.5 list-disc list-inside">
          {t.home.tips.map((tip) => (
            <li key={tip}>{tip}</li>
          ))}
        </ul>
      </div>
    </div>
    </>
  );
}
