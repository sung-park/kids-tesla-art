"use client";

export type TeslaModel = "model3" | "modely";

interface ModelSelectorProps {
  selected: TeslaModel;
  onChange: (model: TeslaModel) => void;
}

const MODELS: { id: TeslaModel; label: string; description: string }[] = [
  { id: "model3", label: "Model 3", description: "Sedan" },
  { id: "modely", label: "Model Y", description: "SUV / Crossover" },
];

export default function ModelSelector({
  selected,
  onChange,
}: ModelSelectorProps) {
  return (
    <div role="radiogroup" aria-label="Select Tesla model" className="flex gap-3">
      {MODELS.map((model) => {
        const isSelected = selected === model.id;
        return (
          <button
            key={model.id}
            type="button"
            role="radio"
            aria-checked={isSelected}
            onClick={() => onChange(model.id)}
            className={[
              "flex-1 rounded-xl border-2 px-4 py-3 text-left transition-all",
              isSelected
                ? "border-tesla-red bg-red-50 dark:bg-red-950"
                : "border-gray-200 dark:border-gray-700 hover:border-gray-400",
            ].join(" ")}
          >
            <p
              className={[
                "font-semibold text-sm",
                isSelected
                  ? "text-tesla-red"
                  : "text-tesla-dark dark:text-white",
              ].join(" ")}
            >
              {model.label}
            </p>
            <p className="text-xs text-gray-500 mt-0.5">{model.description}</p>
          </button>
        );
      })}
    </div>
  );
}
