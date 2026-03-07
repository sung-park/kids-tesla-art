import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        ivory: "#FDFBF7",
        ink: "#1A1A1A",
        crayon: {
          pink: "#FF8FAB",
          yellow: "#FFD60A",
          mint: "#3ECF8E",
          sky: "#4DA6FF",
        },
        pastel: {
          pink: "#FFD6E7",
          yellow: "#FFF3C4",
          mint: "#C7F2E8",
          sky: "#C9E8FF",
        },
        tesla: {
          red: "#E31937",
          dark: "#171A20",
          gray: "#393C41",
          light: "#AAAAAA",
        },
      },
      fontFamily: {
        sans: ["var(--font-jua)", "sans-serif"],
      },
    },
  },
  plugins: [],
};

export default config;
