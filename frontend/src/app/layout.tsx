import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Memory Engine",
  description: "Personal multimodal image search",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className="dark">
      <body className="min-h-screen bg-surface text-white antialiased">
        {children}
      </body>
    </html>
  );
}
