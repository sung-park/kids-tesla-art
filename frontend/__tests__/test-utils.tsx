import { render, type RenderOptions } from "@testing-library/react";
import { LocaleProvider } from "@/contexts/LocaleContext";

function EnWrapper({ children }: { children: React.ReactNode }) {
  return <LocaleProvider>{children}</LocaleProvider>;
}

export function renderEn(ui: React.ReactElement, options?: RenderOptions) {
  localStorage.setItem("locale", "en");
  return render(ui, { wrapper: EnWrapper, ...options });
}
