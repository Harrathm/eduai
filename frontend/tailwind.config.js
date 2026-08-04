export default {
  content: ["./index.html", "./src/**/*.{js,jsx,ts,tsx}"],
  theme: {
    extend: {
      colors: {
        orange: {
          DEFAULT: "#FF6B2B",
          w: "#FF8C42",
          l: "#FFB347",
          g: "#FFCF8D",
          p: "#FFF0E6",
        },
        navy: {
          DEFAULT: "#0D1B2A",
          m: "#1A2E4A",
          s: "#2C4A6E",
          50: "#E8ECF1",
          100: "#C5CDD9",
          200: "#9AABB3",
          300: "#6E898D",
          500: "#2C4A6E",
          600: "#1A2E4A",
          700: "#0D1B2A",
          800: "#08121B",
        },
        cream: {
          DEFAULT: "#FFF8F0",
          m: "#F5EDE4",
        },
        gray: {
          DEFAULT: "#8A7A6E",
          l: "#C4B5A5",
        },
      },
      fontFamily: {
        display: ["Cormorant Garamond", "serif"],
        body: ["DM Sans", "sans-serif"],
        arabic: ["Tajawal", "sans-serif"],
      },
      boxShadow: {
        or: "0 8px 40px rgba(255,107,43,.22)",
        dp: "0 20px 60px rgba(13,27,42,.18)",
        sm: "0 4px 20px rgba(13,27,42,.07)",
      },
      animation: {
        "fade-up": "fadeUp .7s ease both",
        float: "float 3s ease-in-out infinite",
        pulse: "pulse 2s ease-in-out infinite",
      },
      keyframes: {
        fadeUp: {
          from: { opacity: 0, transform: "translateY(32px)" },
          to: { opacity: 1, transform: "none" },
        },
        float: {
          "0%, 100%": { transform: "translateY(0)" },
          "50%": { transform: "translateY(-10px)" },
        },
      },
    },
  },
  plugins: [],
};