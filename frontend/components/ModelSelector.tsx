"use client";

import { useT } from "@/contexts/LocaleContext";

export type TeslaModel = "model3" | "modely";

interface ModelSelectorProps {
  selected: TeslaModel;
  onChange: (model: TeslaModel) => void;
}

export default function ModelSelector({
  selected,
  onChange,
}: ModelSelectorProps) {
  const t = useT();

  const models: { id: TeslaModel; label: string; description: string; emoji: string; pastel: string }[] = [
    { id: "model3", label: "Model 3", description: t.modelSelector.sedan, emoji: "🚗", pastel: "bg-pastel-sky" },
    { id: "modely", label: "Model Y", description: t.modelSelector.suv, emoji: "🚙", pastel: "bg-pastel-pink" },
  ];

  return (
    <div role="radiogroup" aria-label="Select Tesla model" className="flex gap-3">
      {models.map((model) => {
        const isSelected = selected === model.id;
        return (
          <button
            key={model.id}
            type="button"
            role="radio"
            aria-checked={isSelected}
            onClick={() => onChange(model.id)}
            className={[
              "flex-1 rounded-2xl border-2 border-ink px-4 py-3 text-left transition-transform duration-150 hover:-rotate-1",
              isSelected
                ? `${model.pastel} shadow-[4px_4px_0px_#1A1A1A]`
                : "bg-white hover:bg-ivory shadow-[2px_2px_0px_#1A1A1A]",
            ].join(" ")}
          >
            <p className="text-xl mb-1">{model.emoji}</p>
            <p className="font-bold text-sm text-ink">{model.label}</p>
            <p className="text-xs text-ink/60 mt-0.5">{model.description}</p>
          </button>
        );
      })}
    </div>
  );
}
