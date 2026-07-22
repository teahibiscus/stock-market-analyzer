import type { Metadata } from "next";

import "./globals.css";

export const metadata: Metadata = {
  title: "Stock Market Analyzer",
  description: "Professional stock market charting application",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
