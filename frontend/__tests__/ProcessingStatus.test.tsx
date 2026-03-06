import { describe, it, expect } from "vitest";
import { screen } from "@testing-library/react";
import ProcessingStatus from "@/components/ProcessingStatus";
import { renderEn } from "./test-utils";

describe("ProcessingStatus", () => {
  it("renders nothing when idle", () => {
    const { container } = renderEn(<ProcessingStatus step="idle" />);
    expect(container).toBeEmptyDOMElement();
  });

  it("shows spinner and message when uploading", () => {
    renderEn(<ProcessingStatus step="uploading" />);
    expect(screen.getByRole("status")).toHaveTextContent(/uploading/i);
  });

  it("shows detecting message", () => {
    renderEn(<ProcessingStatus step="detecting" />);
    expect(screen.getByRole("status")).toHaveTextContent(/detecting/i);
  });

  it("shows background removal message", () => {
    renderEn(<ProcessingStatus step="removing_bg" />);
    expect(screen.getByRole("status")).toHaveTextContent(/removing background/i);
  });

  it("shows done message", () => {
    renderEn(<ProcessingStatus step="done" />);
    expect(screen.getByRole("status")).toHaveTextContent(/ready/i);
  });

  it("shows custom error message", () => {
    renderEn(<ProcessingStatus step="error" errorMessage="Markers not found." />);
    expect(screen.getByRole("status")).toHaveTextContent("Markers not found.");
  });

  it("shows default error message when no errorMessage provided", () => {
    renderEn(<ProcessingStatus step="error" />);
    expect(screen.getByRole("status")).toHaveTextContent(/something went wrong/i);
  });
});
