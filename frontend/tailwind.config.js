/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        swiss: {
          white: "#FFFFFF",
          black: "#121212",
          dark: "#1A1A1A",
          blue: "#0047AB", // Azul Científico
          "blue-hover": "#003680",
          neutral: "#EFEFEF",
          muted: "#6C757D",
          border: "#E2E4E8",
          green: "#006400", // Verde Escuro
          red: "#8B0000",   // Vermelho Escuro
          gold: "#FFD700",  // Amarelo Ouro
        },
      },
      fontFamily: {
        sans: ["var(--font-sans)", "Inter", "-apple-system", "BlinkMacSystemFont", "Helvetica Neue", "Arial", "sans-serif"],
        mono: ["var(--font-mono)", "JetBrains Mono", "SFMono-Regular", "Menlo", "Monaco", "Consolas", "monospace"],
      },
      borderRadius: {
        swiss: "8px",
      },
      boxShadow: {
        swiss: "0 2px 12px rgba(0, 0, 0, 0.06)",
        "swiss-hover": "0 4px 16px rgba(0, 0, 0, 0.10)",
      },
    },
  },
  plugins: [],
};

