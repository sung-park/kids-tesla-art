import type { TeslaModel } from "@/components/ModelSelector";
import type { ProcessingStep } from "@/components/ProcessingStatus";

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "/api";

export interface ProcessResult {
  blobUrl: string;
  filename: string;
}

export class ProcessingError extends Error {
  constructor(
    message: string,
    public readonly step?: ProcessingStep
  ) {
    super(message);
    this.name = "ProcessingError";
  }
}

export async function processImage(
  file: File,
  model: TeslaModel,
  onStep: (step: ProcessingStep) => void
): Promise<ProcessResult> {
  onStep("uploading");

  const formData = new FormData();
  formData.append("image", file);
  formData.append("model", model);

  onStep("detecting");

  let response: Response;
  try {
    response = await fetch(`${API_BASE}/process`, {
      method: "POST",
      body: formData,
    });
  } catch {
    throw new ProcessingError(
      "Network error. Please check your connection and try again."
    );
  }

  if (!response.ok) {
    const text = await response.text().catch(() => "");
    let detail = "Processing failed. Please try again.";

    try {
      const json = JSON.parse(text) as { detail?: string };
      if (json.detail) detail = json.detail;
    } catch {
      // non-JSON error body
    }

    if (response.status === 422) {
      throw new ProcessingError(
        detail ||
          "Could not detect alignment markers. Make sure all 4 corner markers are visible in the photo.",
        "detecting"
      );
    }

    throw new ProcessingError(detail);
  }

  onStep("compositing");

  const blob = await response.blob();
  const contentDisposition = response.headers.get("Content-Disposition") ?? "";
  const filenameMatch = contentDisposition.match(/filename="?([^";\n]+)"?/);
  const filename = filenameMatch?.[1] ?? "kids-tesla-wrap.png";

  const blobUrl = URL.createObjectURL(blob);
  onStep("done");

  return { blobUrl, filename };
}
