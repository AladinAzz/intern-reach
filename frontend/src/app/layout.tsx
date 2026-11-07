import type { Metadata } from "next";
import "./globals.css";

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
    <html lang="fr">
      <body className="antialiased text-[#121212] bg-[#F8F9FA]">
        {children}
      </body>
    </html>
  );
}

