/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./src/**/*.{js,ts,jsx,tsx,mdx}"],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        surface: {
          DEFAULT: "#0a0a0a",
          50: "#111111",
          100: "#1a1a1a",
          200: "#2a2a2a",
          300: "#3a3a3a",
        },
        accent: {
          DEFAULT: "#6366f1",
          hover: "#818cf8",
        },
      },
    },
  },
  plugins: [],
};
