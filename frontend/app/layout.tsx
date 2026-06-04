import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Heill — Sports Travel Agent",
  description: "AI-powered sports activity holiday planner",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
