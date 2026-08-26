import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "VAT Enterprise | Multi-Vendor Network Diagnostic & Remediation",
  description:
    "Carrier-Grade Network Operations Center (NOC) Diagnostic and 4-Stage Remediation Platform",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        <link
          href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;600;700&display=swap"
          rel="stylesheet"
        />
      </head>
      <body className="h-screen w-screen bg-obsidian-950 flex flex-col">
        {children}
      </body>
    </html>
  );
}
