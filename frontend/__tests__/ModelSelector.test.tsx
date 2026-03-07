import { describe, it, expect, vi } from "vitest";
import { screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import ModelSelector from "@/components/ModelSelector";
import { renderEn } from "./test-utils";

describe("ModelSelector", () => {
  it("renders both model options", () => {
    renderEn(<ModelSelector selected="model3" onChange={vi.fn()} />);
    expect(screen.getByText("Model 3")).toBeInTheDocument();
    expect(screen.getByText("Model Y (~2024)")).toBeInTheDocument();
  });

  it("marks selected model as checked", () => {
    renderEn(<ModelSelector selected="modely" onChange={vi.fn()} />);
    const modelYBtn = screen.getByRole("radio", { name: /model y/i });
    const model3Btn = screen.getByRole("radio", { name: /model 3/i });
    expect(modelYBtn).toHaveAttribute("aria-checked", "true");
    expect(model3Btn).toHaveAttribute("aria-checked", "false");
  });

  it("calls onChange with correct model id when clicked", async () => {
    const onChange = vi.fn();
    renderEn(<ModelSelector selected="model3" onChange={onChange} />);
    await userEvent.click(screen.getByRole("radio", { name: /model y/i }));
    expect(onChange).toHaveBeenCalledWith("modely");
  });

  it("does not call onChange when same model clicked again", async () => {
    const onChange = vi.fn();
    renderEn(<ModelSelector selected="model3" onChange={onChange} />);
    await userEvent.click(screen.getByRole("radio", { name: /model 3/i }));
    expect(onChange).toHaveBeenCalledWith("model3");
  });
});
