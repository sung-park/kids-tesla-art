import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "How to Apply Your Wrap | Kids Tesla Art",
  description:
    "Step-by-step guide to transfer your custom wrap to your Tesla via USB drive.",
};

export default function GuideLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return <>{children}</>;
}
