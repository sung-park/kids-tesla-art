import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { processImage, ProcessingError } from "@/lib/api";

const mockFetch = vi.fn();
globalThis.fetch = mockFetch;
globalThis.URL.createObjectURL = vi.fn(() => "blob:mock-url");

beforeEach(() => {
  mockFetch.mockReset();
});

afterEach(() => {
  vi.restoreAllMocks();
});

function makeFile(name = "photo.jpg", type = "image/jpeg"): File {
  return new File(["data"], name, { type });
}

describe("processImage", () => {
  it("returns blobUrl and filename on success", async () => {
    const mockBlob = new Blob(["png-data"], { type: "image/png" });
    mockFetch.mockResolvedValue({
      ok: true,
      blob: () => Promise.resolve(mockBlob),
      headers: new Headers({
        "Content-Disposition": 'attachment; filename="my-wrap.png"',
      }),
    });

    const onStep = vi.fn();
    const result = await processImage(makeFile(), "model3", onStep);

    expect(result.filename).toBe("my-wrap.png");
    expect(result.blobUrl).toBe("blob:mock-url");
    expect(onStep).toHaveBeenCalledWith("uploading");
    expect(onStep).toHaveBeenCalledWith("previewing");
  });

  it("uses fallback filename when Content-Disposition is missing", async () => {
    const mockBlob = new Blob(["data"], { type: "image/png" });
    mockFetch.mockResolvedValue({
      ok: true,
      blob: () => Promise.resolve(mockBlob),
      headers: new Headers(),
    });

    const result = await processImage(makeFile(), "model3", vi.fn());
    expect(result.filename).toBe("kids-tesla-wrap.png");
  });

  it("throws ProcessingError with 422 status", async () => {
    mockFetch.mockResolvedValue({
      ok: false,
      status: 422,
      text: () => Promise.resolve(JSON.stringify({ detail: "Markers not detected" })),
    });

    await expect(processImage(makeFile(), "model3", vi.fn())).rejects.toThrow(
      ProcessingError
    );
    await expect(processImage(makeFile(), "model3", vi.fn())).rejects.toThrow(
      /markers/i
    );
  });

  it("throws ProcessingError on network failure", async () => {
    mockFetch.mockRejectedValue(new TypeError("Failed to fetch"));

    await expect(processImage(makeFile(), "model3", vi.fn())).rejects.toThrow(
      ProcessingError
    );
    await expect(processImage(makeFile(), "model3", vi.fn())).rejects.toThrow(
      /network error/i
    );
  });

  it("throws ProcessingError on 500 server error", async () => {
    mockFetch.mockResolvedValue({
      ok: false,
      status: 500,
      text: () => Promise.resolve(JSON.stringify({ detail: "Internal error" })),
    });

    await expect(processImage(makeFile(), "model3", vi.fn())).rejects.toThrow(
      ProcessingError
    );
  });

  it("sends correct model and image in form data", async () => {
    const mockBlob = new Blob(["data"], { type: "image/png" });
    mockFetch.mockResolvedValue({
      ok: true,
      blob: () => Promise.resolve(mockBlob),
      headers: new Headers(),
    });

    const file = makeFile("test.jpg");
    await processImage(file, "modely", vi.fn());

    const [url, options] = mockFetch.mock.calls[0] as [string, RequestInit];
    expect(url).toContain("/process");
    const formData = options.body as FormData;
    expect(formData.get("model")).toBe("modely");
    expect(formData.get("image")).toBe(file);
  });
});
