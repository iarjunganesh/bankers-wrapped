import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Banker's Wrapped",
  description: "Your financial year, told as a story.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body style={{ margin: 0, padding: 0 }}>{children}</body>
    </html>
  );
}
