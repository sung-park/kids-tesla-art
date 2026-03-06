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
        tesla: {
          red: "#E31937",
          dark: "#171A20",
          gray: "#393C41",
          light: "#AAAAAA",
        },
      },
    },
  },
  plugins: [],
};

export default config;
