import { describe, it, expect, vi } from "vitest";
import { screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import ImageUploader from "@/components/ImageUploader";
import { renderEn } from "./test-utils";

describe("ImageUploader", () => {
  it("renders upload area", () => {
    renderEn(<ImageUploader onFileSelected={vi.fn()} />);
    expect(screen.getByRole("button", { name: /drop image here/i })).toBeInTheDocument();
  });

  it("shows error for oversized file", async () => {
    const onFileSelected = vi.fn();
    renderEn(<ImageUploader onFileSelected={onFileSelected} />);

    const oversizedFile = new File(["x".repeat(21 * 1024 * 1024)], "big.jpg", {
      type: "image/jpeg",
    });
    Object.defineProperty(oversizedFile, "size", { value: 21 * 1024 * 1024 });

    const input = document.querySelector(
      'input[type="file"]:not([capture])'
    ) as HTMLInputElement;
    await userEvent.upload(input, oversizedFile);

    expect(screen.getByRole("alert")).toHaveTextContent(/too large/i);
    expect(onFileSelected).not.toHaveBeenCalled();
  });

  it("shows error for unsupported file type", async () => {
    const onFileSelected = vi.fn();
    renderEn(<ImageUploader onFileSelected={onFileSelected} />);

    const badFile = new File(["data"], "doc.pdf", { type: "application/pdf" });
    const input = document.querySelector(
      'input[type="file"]:not([capture])'
    ) as HTMLInputElement;
    // applyAccept: false bypasses the input accept attribute so our custom
    // validation logic in the component gets exercised.
    await userEvent.upload(input, badFile, { applyAccept: false });

    expect(screen.getByRole("alert")).toHaveTextContent(/jpeg|png|webp|heic/i);
    expect(onFileSelected).not.toHaveBeenCalled();
  });

  it("calls onFileSelected for valid JPEG file", async () => {
    const onFileSelected = vi.fn();
    renderEn(<ImageUploader onFileSelected={onFileSelected} />);

    const validFile = new File(["image-data"], "photo.jpg", { type: "image/jpeg" });
    const input = document.querySelector(
      'input[type="file"]:not([capture])'
    ) as HTMLInputElement;
    await userEvent.upload(input, validFile);

    expect(onFileSelected).toHaveBeenCalledWith(validFile);
    expect(screen.queryByRole("alert")).not.toBeInTheDocument();
  });

  it("calls onFileSelected for valid PNG file", async () => {
    const onFileSelected = vi.fn();
    renderEn(<ImageUploader onFileSelected={onFileSelected} />);

    const pngFile = new File(["png-data"], "art.png", { type: "image/png" });
    const input = document.querySelector(
      'input[type="file"]:not([capture])'
    ) as HTMLInputElement;
    await userEvent.upload(input, pngFile);

    expect(onFileSelected).toHaveBeenCalledWith(pngFile);
  });

  it("disables interaction when disabled prop is true", () => {
    renderEn(<ImageUploader onFileSelected={vi.fn()} disabled />);
    const dropZone = screen.getByRole("button", { name: /drop image here/i });
    expect(dropZone).toHaveAttribute("tabIndex", "-1");
  });
});
