import type { Metadata } from "next";
import { Inter, JetBrains_Mono } from "next/font/google";
import "./globals.css";

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-sans",
  display: "swap",
});

const jetbrainsMono = JetBrains_Mono({
  subsets: ["latin"],
  variable: "--font-mono",
  display: "swap",
});

export const metadata: Metadata = {
  title: "InternReach // Recherche de Stage & Lettres Personnalisées",
  description:
    "Plateforme académique et scientifique de recherche de stage et de génération de lettres de motivation pour l'embarqué, l'IA et le traitement du signal à Paris.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="fr" className={`${inter.variable} ${jetbrainsMono.variable}`}>
      <body className="antialiased text-[#121212] bg-[#F8F9FA] font-sans">
        {children}
      </body>
    </html>
  );
}

