import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        background: "#F8FAFC",
        surface: "#FFFFFF",
        border: "#E5E7EB",
        primary: "#0F172A",
        secondary: "#64748B",
        brand: "#2536D9",
        brandStrong: "#3046E8",
        brandSoft: "#EEF2FF",
        positive: "#059669",
        positiveSoft: "#ECFDF5",
        warning: "#D97706",
        warningSoft: "#FEF3C7",
        risk: "#DC2626",
        riskSoft: "#FEF2F2"
      },
      boxShadow: {
        soft: "0 10px 30px rgba(15, 23, 42, 0.06)"
      },
      borderRadius: {
        card: "1rem"
      },
      fontFamily: {
        sans: ["Inter", "Arial", "sans-serif"]
      }
    },
  },
  plugins: [],
};

export default config;
