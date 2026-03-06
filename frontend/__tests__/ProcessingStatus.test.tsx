import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import ProcessingStatus from "@/components/ProcessingStatus";

describe("ProcessingStatus", () => {
  it("renders nothing when idle", () => {
    const { container } = render(<ProcessingStatus step="idle" />);
    expect(container).toBeEmptyDOMElement();
  });

  it("shows spinner and message when uploading", () => {
    render(<ProcessingStatus step="uploading" />);
    expect(screen.getByRole("status")).toHaveTextContent(/uploading/i);
  });

  it("shows detecting message", () => {
    render(<ProcessingStatus step="detecting" />);
    expect(screen.getByRole("status")).toHaveTextContent(/detecting/i);
  });

  it("shows background removal message", () => {
    render(<ProcessingStatus step="removing_bg" />);
    expect(screen.getByRole("status")).toHaveTextContent(/removing background/i);
  });

  it("shows done message", () => {
    render(<ProcessingStatus step="done" />);
    expect(screen.getByRole("status")).toHaveTextContent(/ready/i);
  });

  it("shows custom error message", () => {
    render(<ProcessingStatus step="error" errorMessage="Markers not found." />);
    expect(screen.getByRole("status")).toHaveTextContent("Markers not found.");
  });

  it("shows default error message when no errorMessage provided", () => {
    render(<ProcessingStatus step="error" />);
    expect(screen.getByRole("status")).toHaveTextContent(/something went wrong/i);
  });
});
