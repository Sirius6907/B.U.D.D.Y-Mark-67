import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        surface: "#07111b",
        cyan: "#5cf6ff",
        sky: "#00d2ff",
        rose: "#ff4fd8",
        lime: "#8cff66",
      },
      fontFamily: {
        display: ["Orbitron", "sans-serif"],
        mono: ["JetBrains Mono", "monospace"],
      },
      boxShadow: {
        glow: "0 0 40px rgba(92, 246, 255, 0.18)",
      },
    },
  },
  plugins: [],
};

export default config;

