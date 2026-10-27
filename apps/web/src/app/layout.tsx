import React from "react";
import "./globals.css";
import { EvidenceDrawerProvider } from "@/components/evidence/EvidenceDrawer";

export const metadata = {
  title: "NeuralCFO - Unified AI Decision Engine",
  description: "Next-Generation Liquid Glass & Claymorphic Decision Cockpit for Small Business Finance & Strategy",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="min-h-screen text-slate-800 flex flex-col font-sans antialiased overflow-x-hidden selection:bg-cyan-200">
        <EvidenceDrawerProvider>
          {children}
        </EvidenceDrawerProvider>
      </body>
    </html>
  );
}
