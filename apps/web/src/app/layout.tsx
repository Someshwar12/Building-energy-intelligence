import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Building Intelligence",
  description:
    "Energy intelligence and operational insights for buildings.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}