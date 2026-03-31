import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        canvas: "#f5efe5",
        ink: "#1d2a38",
        accent: "#0f766e",
        coral: "#c96b43",
        sand: "#e7dac8",
      },
      fontFamily: {
        sans: ["Segoe UI", "Tahoma", "sans-serif"],
      },
      boxShadow: {
        soft: "0 18px 40px rgba(29, 42, 56, 0.12)",
      },
    },
  },
  plugins: [],
};

export default config;

