"use client";

export type ProcessingStep =
  | "idle"
  | "uploading"
  | "detecting"
  | "removing_bg"
  | "compositing"
  | "previewing"
  | "done"
  | "error";

const STEP_MESSAGES: Record<ProcessingStep, string> = {
  idle: "",
  uploading: "Uploading image...",
  detecting: "Detecting alignment markers...",
  removing_bg: "Removing background...",
  compositing: "Applying to Tesla template...",
  previewing: "Preview ready!",
  done: "Your wrap is ready!",
  error: "",
};

interface ProcessingStatusProps {
  step: ProcessingStep;
  errorMessage?: string;
}

export default function ProcessingStatus({
  step,
  errorMessage,
}: ProcessingStatusProps) {
  if (step === "idle") return null;

  const isError = step === "error";
  const isDone = step === "done";
  const isProcessing = !isError && !isDone;

  return (
    <div
      role="status"
      aria-live="polite"
      aria-label={isError ? "Error" : STEP_MESSAGES[step]}
      className={[
        "flex items-center gap-3 rounded-xl px-4 py-3 text-sm",
        isError
          ? "bg-red-50 dark:bg-red-950 text-red-700 dark:text-red-400"
          : isDone
          ? "bg-green-50 dark:bg-green-950 text-green-700 dark:text-green-400"
          : "bg-blue-50 dark:bg-blue-950 text-blue-700 dark:text-blue-400",
      ].join(" ")}
    >
      {isProcessing && (
        <svg
          className="w-4 h-4 animate-spin shrink-0"
          fill="none"
          viewBox="0 0 24 24"
          aria-hidden="true"
        >
          <circle
            className="opacity-25"
            cx="12"
            cy="12"
            r="10"
            stroke="currentColor"
            strokeWidth="4"
          />
          <path
            className="opacity-75"
            fill="currentColor"
            d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
          />
        </svg>
      )}
      {isDone && (
        <svg className="w-4 h-4 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
        </svg>
      )}
      {isError && (
        <svg className="w-4 h-4 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126zM12 15.75h.007v.008H12v-.008z" />
        </svg>
      )}
      <span>
        {isError ? errorMessage || "Something went wrong. Please try again." : STEP_MESSAGES[step]}
      </span>
    </div>
  );
}
