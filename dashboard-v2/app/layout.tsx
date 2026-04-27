import "./globals.css";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "BUDDY Dashboard V2",
  description: "Cinematic command center for BUDDY Mark LXVII",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}

