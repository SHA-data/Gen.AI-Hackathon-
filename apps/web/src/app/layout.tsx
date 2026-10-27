import React from "react";
import "./globals.css";
import { EvidenceDrawerProvider } from "@/components/evidence/EvidenceDrawer";

export const metadata = {
  title: "NeuralCFO - Unified AI Decision Engine",
  description: "Next-Generation Liquid Glassmorphism & Claymorphic Decision Cockpit for Small Business Finance & Strategy",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <body className="min-h-screen text-slate-100 flex flex-col font-sans antialiased overflow-x-hidden">
        <EvidenceDrawerProvider>
          {children}
        </EvidenceDrawerProvider>
      </body>
    </html>
  );
}
